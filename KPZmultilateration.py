import math
from scipy.optimize import minimize
import pandas as pd
import database as database
import functions

N = 3               # Environmental factor constant range: 2-4
R = 6371000         # Averge radius of Earth in meters
RP_MIN_NUMBER = 3   # Minimum number of sniff points for one network, required for its location to be calculated
ERROR_LOCATION = "51.63827653,15.00246191"  # Error location pointing to Lupinki Luzyckie, where the famous Styrta was burning 
USER_LOCATION = "0,0"                       # Predefined user location, for safety purpouses
RECIEVED_FILE =  "recieved_client.csv"      # A file where data recieved from app is stored

# Calculating distance between two points on a sphere
# Using Haversine formula: https://en.wikipedia.org/wiki/Haversine_formula
# Returns distance in meters
def distance_on_sphere (point1, point2):
    lat1 = math.radians (point1[0])
    lon1 = math.radians (point1[1])
    lat2 = math.radians (point2[0])
    lon2 = math.radians (point2[1])
    lat_d = (lat2-lat1)/2
    lon_d = (lon2-lon1)/2
    return 2 * R * math.asin(math.sqrt(math.pow(math.sin(lat_d),2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(lon_d),2)))

# Converts RSSI value to distance from the beacon
# Using this formula: https://iotandelectronics.wordpress.com/2016/10/07/how-to-calculate-distance-from-the-rssi-value-of-the-ble-beacon/
# Returns distance from the beacon in meters
def rssi_to_distance (RSSI, measured_power):
    return math.pow(10, (measured_power-RSSI)/(10*N))

# Calculating mean squared error of predicted distance
def error_function (predicted_point, GPS_points, distances_from_beacon):
    error = 0
    n = len(distances_from_beacon)
    for point, dist in zip(GPS_points, distances_from_beacon):
        distance_predicted = distance_on_sphere(point, predicted_point)
        error += math.pow(distance_predicted - dist, 2)
    return error/n

# Minimizes error_function using scipy.optimize minimize function
# Returns predicted localization point
def calculate_location (error_function, locations, distances):
    solution = minimize (
        error_function,
        get_initial_guess(locations, distances),
        args=(locations, distances),
        options={'maxiter': 1e+3}
        )
    return solution.x               # Solution array

# Returns the location point that is closest to the final point based on RSSI
def get_initial_guess (location, distances):
    min_distance = 99999
    for i in range(len(distances)):
        if distances[i] < min_distance:
            min_distance = distances[i]
            position = i
    return location[position]

# Calculating FINAL_GPS_POS of networks (all Reference Points) based on sniff_gps table
def calculate_RP_locations ():
    bssids = []
    query = ("SELECT BSSID FROM networks")
    try:
        database.mycursor.execute(query)
        myresult = database.mycursor.fetchall()

        for x in myresult:  # List of unique BSSIDs in networks table
            bssids.append(x)

        count = 0
        for i in bssids:    # Calclulate FINAL_GPS_POS of network with given BSSID
            distances = []
            locations = []
            query = ("SELECT RSSI, SNIFF_LATITUDE, SNIFF_LONGITUDE FROM sniff_gps WHERE BSSID = %s")
            database.mycursor.execute(query, i)
            myresult = database.mycursor.fetchall()
            if len(myresult) >= RP_MIN_NUMBER:
                for row in myresult:
                    distances.append(rssi_to_distance((float)(row[0]), -20))
                    locations.append(tuple([(float)(row[1]), (float)(row[2])]))

                ap_location = calculate_location(error_function, locations, distances)                  # Calculating network(AP) location
                database.update_final_gps_pos(ap_location[0], ap_location[1], bssids[count][0])         # Updating gps pos in database
            count += 1
        print("[DATABASE] Updated {} Reference Points location".format(len(bssids)))
    except database.mysql.connector.Error as err:
        print(err)
    except Exception as err:
        print("[ERROR] Unexpected error occured when calculating RP locations:", repr(err))

# Calculates user location
# Returns location in bytes, ready to be sent to the client
def calculate_user_location():
    locations = [()]
    latitudes = []
    longitudes = []
    distances = []
    query_lat = ("SELECT FINAL_GPS_POS_LAT from networks WHERE BSSID=%s")
    query_lon = ("SELECT FINAL_GPS_POS_LON from networks WHERE BSSID=%s")

    # Changing "," in SSIDs to "." to load to dataframe
    functions.change_commas_to_periods_SSIDS(RECIEVED_FILE)

    # Loading to dataframe
    file = pd.read_csv (RECIEVED_FILE)   
    df = pd.DataFrame(file)
    
    # Calculating user location
    for row in df.itertuples():
        try:   
            database.mycursor.execute(query_lat, (row.BSSID,))
            lat = database.mycursor.fetchone()
            # SPRAWDZAM CZY NIE NONE
            if lat is not None and lat[0] is not None: 
                latitudes.append(lat)

            database.mycursor.execute(query_lon, (row.BSSID,))
            lon = database.mycursor.fetchone()
            # SPRAWDZAM CZY NIE NONE
            if lon is not None and lon[0] is not None: 
                longitudes.append(lon)
                distances.append(rssi_to_distance((int)(row.LEVEL),-20))
        except database.mysql.connector.Error as err:
            print(err)
        except Exception as err:
            print("[ERROR] Unexpected error occured when calculating user location:", repr(err))

    try:
        # If we can localize the user calculate and return localiztaion:    (If network appears in at least 3 scans)
        if len(latitudes) >= RP_MIN_NUMBER and len(longitudes) >= RP_MIN_NUMBER:
            latitudes = [i for sub in latitudes for i in sub]
            longitudes = [i for sub in longitudes for i in sub]
            locations = functions.merge(list(map(float, latitudes)), list(map(float, longitudes)))
            user_location = calculate_location(error_function, locations, distances)
            USER_LOCATION = "{:.09f}".format(user_location[0]) + ',' + "{:.09f}".format(user_location[1])
            print("[LOCALIZE] Calculated user location: ", USER_LOCATION)
            return USER_LOCATION.encode('utf-8')
        # If we cannot localize the user, return error localization         (If there are not enough scans to localize the network)
        else:   
            print("[LOCALIZE] Error location!")
            return ERROR_LOCATION.encode('utf-8')                           # Returning predefined error location to the app
    except Exception as err:
        print("[ERROR] Unexpected error occured when calculating user location:", repr(err))

if __name__=="__main__":
    # TESTS

    # Updating every network location
    calculate_RP_locations ()      

    # Simulating standing on Ul.Zakladowa and scanning with app         
    RECIEVED_FILE = "scan_16_31_30.csv"     
    calculate_user_location ()
    RECIEVED_FILE = "scan_16_22_06.csv"
    calculate_user_location ()
    RECIEVED_FILE = "scan_16_23_11.csv"
    calculate_user_location ()
    RECIEVED_FILE = "scan_16_24_34.csv"
    calculate_user_location ()
    RECIEVED_FILE = "scan_16_26_29.csv"
    calculate_user_location ()
