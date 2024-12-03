import hashlib
import json
import sqlite3
from sys import argv
import threading
import zmq
import database  


class Server:
    
    
    def __init__(self, port, number_servers, number_neighbours):
        
        self.port = port
        self.number_servers = number_servers
        self.number_neighbours = number_neighbours
        self.servers_hash_port = {}
        self.servers_hash = []
        self.socket = None
        self.server_port_socket = {}
        self.connection, self.cursor = database.connect_db(f"../db/database{port}.db")       
        self.setup_ring()
        self.setup_socket()


    def setup_ring(self):
        
        # create ring
        for i in range(self.number_servers):
            port = 5556 + i
            for j in range(3):
                server_partion = "server_" + str(port) + "_" + str(j)
                hash = hashlib.sha256(server_partion.encode()).hexdigest()
                self.servers_hash.append(hash)
                self.servers_hash_port[hash] = port
        
        # sort hash
        self.servers_hash.sort()
        print(f"Port : {self.port} hashs : {len(self.servers_hash)}")


    def setup_socket(self):
        
        # Create sockets to send replies to servers and clients
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"tcp://localhost:{self.port}")
        
        # Create sockets to send requests to other servers
        for i in range(self.number_servers):
            port_server = 5556 + i
            if port_server != self.port:
                socket_server = context.socket(zmq.REQ)
                socket_server.connect(f"tcp://localhost:{port_server}")
                self.server_port_socket[port_server] = socket_server


    def connect_db(self):
         
        # connect to the database
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # if database has no tables, create them
        if not tables:
            with open('../db/schema.sql', 'r') as f:
                schema_sql = f.read()            
            with connection:
                connection.executescript(schema_sql)
           
        return connection, cursor

        
    def action_delete_list(self, message):
        try:

            # check for errors in message
            if len(list(message.keys())) != 4:
                self.socket.send(json.dumps({"status": "error"}).encode())
                return       

            url = message["url"]           
            client = message["id"]
            ok = database.delete_list(self.connection, self.cursor, url, client)
            if ok:
                self.socket.send(json.dumps({"status": "success"}).encode())
            else:
                self.socket.send(json.dumps({"status": "error"}).encode())
            
        except:
            print("Exception")
            self.socket.send(json.dumps({"status": "error"}).encode())
            
    def action_send_list(self, message):
        try:
        
            # check for errors in message
            if len(list(message.keys())) != 4:
                self.socket.send(json.dumps({"status": "error"}).encode())
                return       

            # perform action
            url = message["url"]
            for server_url, server_name, owner in database.get_lists(self.cursor):
                # check if url exists in server's database
                if server_url == url:
                    shopping_list_dict = {}
                    for item, value in  database.get_list_items(self.cursor, url):
                        shopping_list_dict[item] = value
                    self.socket.send(json.dumps({"status": "success", "url": url, "list": shopping_list_dict, "owner": owner}).encode())
                    return
            # it does not exist, send error        
            self.socket.send(json.dumps({"status": "error"}).encode())
            
        except:
            self.socket.send(json.dumps({"status": "error"}).encode())

        
    def action_polling(self, message):
       
        try:
       
            url = message["url"]
            client = message["id"]
            shopping_list = message["list"]
            owner = message["owner"]

            # create list if it does not exist and add items
            if url not in database.get_lists(self.cursor):
                if client == owner:
                    database.add_list_url(self.connection, self.cursor, url, client)       
                else:     
                    self.socket.send(json.dumps({"status": "error"}).encode())
                    return
                    
            for key, value in shopping_list.items():
                database.add_item(self.connection, self.cursor, url, key, value)
            
            self.socket.send(json.dumps({"status": "success", "url": url, "list": shopping_list}).encode())
       
        except:
            self.socket.send(json.dumps({"status": "error"}).encode())
                          
            
    def update_neighbours(self, message):
        
        # check position in ring
        message["neighbour"] = "yes"
        hash_message_word =hashlib.sha1(message["url"].encode()).hexdigest()
        position = self.servers_hash[0]
        for i in range(len(self.servers_hash)):
            if hash_message_word <= self.servers_hash[i]:
                position = i
                break  
        
        position += 1
        neighbours_send = [self.port]
        
        while len(neighbours_send) < self.number_neighbours + 1:

            neighbour_hash = self.servers_hash[(position + i) % len(self.servers_hash)]
            neighbour_port = self.servers_hash_port[neighbour_hash]
            position += 1
            
            # send update to {number_neighbours} different servers
            if(neighbour_port not in neighbours_send):
                neighbours_socket = self.server_port_socket[neighbour_port]
                neighbours_socket.send(json.dumps(message).encode())
                neighbours_send.append(neighbour_port)
                response = json.loads(neighbours_socket.recv().decode())
                if(response["status"] == 'error'):
                    print(f"Error in update of neighbour {neighbour_port}")
                else:
                    print(f"Success in update of neighbour {neighbour_port}")
             
             
    def run(self):
        while True:    
            message = json.loads(self.socket.recv().decode())
            if message["command"] == "polling": 
                self.action_polling(message)
                #if(message["neighbour"] != "yes"):
                #    self.update_neighbours(message)
            elif message["command"] == "delete_list":
                self.action_delete_list(message)
            elif message["command"] == "download_list":
                self.action_send_list(message)
            else:
                self.socket.send(json.dumps({"status": "error"}).encode())


if __name__ == "__main__":
    
    if(len(argv) < 3):
        print("Error - missing parameters")
    
    else:
        number_servers = int(argv[1])
        number_neighbours = int(argv[2])
        for i in range(int(argv[1])):    
            port = 5557 + i
            # Start each server in a new thread
            server = Server(port, number_servers, number_neighbours)
            thread = threading.Thread(target=server.run)
            thread.start()
