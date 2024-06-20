# Geolocalization based on wifi networks using multilateration

Firstly, this relies on the data from a sniffer of wifi networks, with the localization of the scan being made (in form of longitude and latitude) and networks with corresponding names and RSSI signals. 
Then converts RSSI signals to the distance from localization of the scan. Based on that - we are able to estimate the longitude and latitude of the network location.
Then when a user using an app (the app is not in this repo) scans the networks near them, and gets their RSSI, passes it to the server - the server is able to calculate the location of a user based on RSSI signals of WiFi networks near him.
