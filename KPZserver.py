import socket
from database import *
import selectors
import types
import multilateration 

import datetime

BUFFER_SIZE = 4096      # Bytes saved to files from transfer
PORT = 5000             # Port forwarded to TPC 5000
SERVER = "0.0.0.0"      # Server listening on all ips         
ADDR = (SERVER, PORT)   # Touple storing server adress

sel = selectors.DefaultSelector()                           # Defining selectors
serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # Defining sockets
serv.bind(ADDR)                                             # Binging the server to the socket      

# Test data for plume generator
def PLUME_TESTING(recieved_data):
    unique_filename = "scan_" + str(datetime.datetime.now().time()).replace(':', '_') +".csv"
    with open(unique_filename, "wb") as f:
        f.write(recieved_data)
        print("[FILE] Test file saved: " + unique_filename) 

# Creates a socket object and registers the socket to be selected
def accept_connection(client_socket):
    conn, addr = client_socket.accept()  
    print("==============================================")
    print(f"[NEW CONNECTION] {addr} connected")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# Handles a connection with client 
def handle_connection(key, mask):
    client_socket = key.fileobj
    data = key.data
    
    if mask & selectors.EVENT_READ:
        with open("recieved_client.csv", "wb") as f:
                bytes_read = client_socket.recv(BUFFER_SIZE)                    # Recieving a list of networks from app
                if bytes_read:
                    data.inb += bytes_read
                    PLUME_TESTING(bytes_read) # Generating separate files for each scan, for testing localiziation from home
                    f.write(bytes_read)
                    print("[FILE] Recieved")
                else:
                    sel.unregister(client_socket)
                    print(f"[CLOSING CONNECTION] to {data.addr}")
                    print("==============================================")
                    client_socket.close()

    if mask & selectors.EVENT_WRITE:
        if data.inb:
            data.outb = multilateration.calculate_user_location()               # Calculating users location 
            print(f"[SENDING] User location {data.outb!r} to {data.addr}")
            sent = client_socket.send(data.outb)                                # Sending users location to app
            print(f"[SENT] User location")
            data.outb = data.outb[sent:]
            sel.unregister(client_socket) 
            print(f"[CLOSING CONNECTION] to {data.addr}") 
            print("==============================================") 
            client_socket.close() 
            data.inb=b''

# Starts the server
def start_server():
    serv.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    serv.setblocking(False)
    sel.register(serv, selectors.EVENT_READ, data=None)

    # Accepting and handling connections
    try:
        while(True):
            try:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        accept_connection(key.fileobj)
                    else:
                        handle_connection(key, mask)
            
            # When ctrl-c OPTIONS
            except KeyboardInterrupt:
                options = "options" 
                print("===================[OPTIONS]===================")
                print("     > Input x to delete data from database")
                print("     > Input l to load all data from data folder")
                print("     > Input xl or lx to combine both options")
                print("     > Input dc to close the server")
                options = input("[OPTIONS] Input an option: ")              # Clear database 
                if options == 'x':
                    print("[SERVER] Deleting all data from database...")
                    delete_all_data()
                if options == 'l':                                          # Load new data
                    print("[SERVER] Loading data from data folder...")
                    read_all_data_folder()
                    multilateration.calculate_RP_locations()                # Recalculate all networks locations 
                if options == 'xl' or options == 'lx':                      # Clear database and load new data
                    print("[SERVER] Deleting all data from database...")
                    delete_all_data()
                    print("[SERVER] Loading data from data folder...")
                    read_all_data_folder()
                    multilateration.calculate_RP_locations()                # Recalculate all networks locations  
                if options == "dc":                                         # Close the server
                    print("[SERVER] Closing the server...")
                    exit()

    finally:
        sel.close()

if __name__=="__main__":
        print("==============================================")
        print(f"[STARTING] Server is starting...")
        print("==============================================")
        start_server()
