import mysql.connector
import pandas as pd
import glob
import NEW.KPZfunctions as KPZfunctions
import math
# CONSTANT
DB_NAME = 'database_kpz_plume'
TABLES = {}

# DOES NOT PICK A DATABASE RIGHT AWAY
db = mysql.connector.connect(user='root', passwd='kpz2022')
mycursor = db.cursor()

# DEFINING TABLES
TABLES['networks'] = (
    "CREATE TABLE IF NOT EXISTS networks ("
    "  BSSID varchar(17) NOT NULL,"
    "  SSID text NOT NULL,"         
    "  BITRATES text NOT NULL,"     
    "  STANDARD text NOT NULL,"     
    "  SECURITY text NOT NULL,"     
    "  FINAL_GPS_POS_LAT float DEFAULT NULL," 
    "  FINAL_GPS_POS_LON float DEFAULT NULL," 
    "  PRIMARY KEY (BSSID)"
    ") ENGINE=InnoDB")

TABLES['sniff_gps'] = (
    "CREATE TABLE IF NOT EXISTS sniff_gps ("
    "   ID_SNIFF_GPS int NOT NULL AUTO_INCREMENT,"
    "   BSSID varchar(17) NOT NULL,"
    "   QUALITY text NOT NULL,"     
    "   RSSI float NOT NULL,"        
    "   FREQUENCY text NOT NULL,"    
    "   CHANNEL int NOT NULL,"      
    "   SNIFF_LATITUDE float NOT NULL,"     
    "   SNIFF_LONGITUDE float NOT NULL,"    
    "   PRIMARY KEY (ID_SNIFF_GPS),"
    "   FOREIGN KEY (BSSID)"
    "       REFERENCES networks(BSSID)"
    "       ON DELETE CASCADE)"
    "ENGINE=InnoDB")

# DEFINING INSERTS AND UPDATES
# Insert network into networks, FINAL_GPS DEFAULT NULL
def insert_network (BSSID, SSID, BITRATES, STANDARD, SECURITY): 
    # Checking if SSID isn't NaN type
    if type(SSID) == float:
        values = (BSSID, '', BITRATES, STANDARD, SECURITY)
    else:
        values = (BSSID, SSID, BITRATES, STANDARD, SECURITY)

    query = (
        "INSERT IGNORE INTO networks (BSSID, SSID, BITRATES, STANDARD, SECURITY, FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON)"                                
        "VALUES (%s, %s, %s, %s, %s, DEFAULT, DEFAULT)")
    try:
        mycursor.execute(query, values)
        db.commit()
        # print("[INSERTED INTO NETWORKS] BSSID: {}, SSID: {}".format(BSSID, SSID))
    except mysql.connector.Error as err:
        print("[ERROR] MySQL error when inserting networks: ", err)
    except Exception as err:
        print("[ERROR] Unexpected error while inserting networks: ", repr(err))

# Insert network into networks with predefined GPS positions, for testing purpouses
def insert_networks_TEST (BSSID, SSID, BITRATES, STANDARD, SECURITY, FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON): 
    if type(SSID) == float:
        values = (BSSID, '', BITRATES, STANDARD, SECURITY, FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON)
    else:
        values = (BSSID, SSID, BITRATES, STANDARD, SECURITY, FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON)
    query = (
        "INSERT IGNORE INTO networks (BSSID, SSID, BITRATES, STANDARD, SECURITY, FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON)"                                
        "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    try:
        mycursor.execute(query, values)
        db.commit()
    except mysql.connector.Error as err:
        print("[ERROR] MySQL error when inserting networks: ", err)
    except Exception as err:
        print("[ERROR] Unexpected error while inserting networks: ", repr(err))

# ID_SNIFF_GPS auto, ID_NETWORK relationship
def insert_sniff_gps (BSSID, QUALITY, RSSI, FREQUENCY, CHANNEL, SNIFF_LATITUDE, SNIFF_LONGITUDE): 
    vaules = (BSSID, QUALITY, RSSI, FREQUENCY, CHANNEL, SNIFF_LATITUDE, SNIFF_LONGITUDE)
    query = (
        "INSERT INTO sniff_gps (ID_SNIFF_GPS, BSSID, QUALITY, RSSI, FREQUENCY, CHANNEL, SNIFF_LATITUDE, SNIFF_LONGITUDE)"                     
        "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s)")
    try:
        mycursor.execute(query,vaules)
        db.commit()
    except mysql.connector.Error as err:
        print("[ERROR] MySQL error when inserting sniff_gps: ", err)
    except Exception as err:
        print("[ERROR] Unexpected error when inserting sniff_gps: ", repr(err))

# Updating the final GPS position of network (after localization alghotirm)
def update_final_gps_pos (FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON, BSSID):
    values = (FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON, BSSID)
    query = ("UPDATE networks SET FINAL_GPS_POS_LAT = %s, FINAL_GPS_POS_LON = %s WHERE BSSID = %s")
    try:
        mycursor.execute(query,values)
        db.commit()
    except mysql.connector.Error as err:
        print("[ERROR] MySQL error when updating final gps pos: ", err)
    except Exception as err:
        print("[ERROR] Unexpected error when updating final_gps_pos: ", repr(err))

# Selecting gps position for given BSSID
def select_gps_where_bssid (BSSID):
    query = ("SELECT FINAL_GPS_POS_LAT, FINAL_GPS_POS_LON WHERE BSSID = %s")
    try:
        mycursor.execute(query.format(BSSID))
        db.commit()
    except mysql.connector.Error as err:
        print("[ERROR] MySQL error when selecting gps where bssid=: ", err)
    except Exception as err:
        print("[ERROR] Unexpected error when selecting gps while bssid=... : ", repr(err))

# Reading all files from data folder into database
def read_all_data_folder():
    try:
        path = 'data'
        csv_files = glob.glob(path + "/*.csv")

        for filename in csv_files:
            KPZfunctions.change_commas_to_periods_SSIDS_sniffer(filename)

        df_list = (pd.read_csv(file) for file in csv_files)
        df = pd.concat(df_list, ignore_index = True)
        for row in df.itertuples():
            insert_network(row.Address, row.SSID, row.BitRates, row.Standard, row.Security) 
            insert_sniff_gps(row.Address, row.Quality, row.SignalLevel, row.Frequency, row.Channel, row.Latitude, row.Longitude) 
        print("[DATABASE] All sniffer data from folder data updated")
    except OSError:
        print("[ERROR] OSError occured when reading data from data folder")
    except Exception as err:
        print("[ERROR] Unexpected error when reading data from data folder: ", repr(err))

def delete_all_data():
    query1 = "DELETE FROM networks"
    query2 = "DELETE FROM sniff_gps"
    try:
        mycursor.execute(query1)
        db.commit()
        mycursor.execute(query2)
        db.commit()
    except mysql.connector.Error as err:
        print(err)
    except Exception as err:
        print("[ERROR] Unexpected error when deleting data: ", repr(err))

# Adds sniffer data to database
def add_sniffer_data(sniffer_file):
    try:
        file = pd.read_csv (sniffer_file)   
        df = pd.DataFrame(file)
        for row in df.itertuples():
            insert_network(row.Address, row.SSID, row.BitRates, row.Standard, row.Security) 
            insert_sniff_gps(row.Address, row.Quality, row.SignalLevel, row.Frequency, row.Channel, row.Latitude, row.Longitude) 
        print("[DATABASE] Sniffer data from {} file added".format(sniffer_file))
    except FileNotFoundError:
        print("[ERROR] FileNotFoundError ", sniffer_file)
    except OSError:
        print("[ERROR] OSError occured when handling files")
    except Exception as err:
        print("[ERROR] Unexpected error when adding sniffer data: ", repr(err))

# Adding sniffer data with predefined GPS values
def add_networks_TEST_serv(networks_file):
    try:
        file = pd.read_csv (networks_file)   
        df = pd.DataFrame(file)
        for row in df.itertuples():
            insert_networks_TEST(row.BSSID, row.SSID, row.BITRATES, row.STANDARD, row.SECURITY, row.FINAL_GPS_POS_LAT, row.FINAL_GPS_POS_LON) 
    except FileNotFoundError:
        print("[ERROR] FileNotFoundError ", networks_file)
    except OSError:
        print("[ERROR] OSError occured when handling files")
    except Exception as err:
        print("[ERROR] Unexpected error when adding networks: ", repr(err))

# Creating the database
def create_database():
    print("[CREATING DATABASE] {}".format(DB_NAME))
    try:                                                                        # Creating database if it doesen't alredy exist
        mycursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(DB_NAME))
        print("[DATABASE CREATED/ ALREDY EXISTS] {}".format(DB_NAME))
        db.commit()
    except mysql.connector.Error as err:                                        # Checking for errors
        print("[ERROR] Failed to create a database: {}".format(err))
        exit(1)   
    except Exception as err:
        print("[ERROR] Unexpected error when creating database: ", repr(err))                                                            

# Creating tables
def create_tables(tables):
    for table_name in tables:
        print("[CREATING TABLE] {}".format(table_name))
        try:                                                                    # Creating tables if it they don't alredy exist
            mycursor.execute(tables[table_name])  
            db.commit()                                 
            print("[TABLE CREATED/ ALREDY EXISTS] {}".format(table_name))
        except mysql.connector.Error as err:                                    # Checking for errors
            print("Failed to create {} table: {}".format(table_name, err))      
            exit(1)

create_database()
mycursor.execute("USE {}".format(DB_NAME))                                      # Using created database
create_tables(TABLES)