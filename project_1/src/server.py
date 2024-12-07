import hashlib
import json
import sqlite3
from sys import argv
import threading
import time
import zmq
from crdt import PNCounter, ShoppingList
import database


class Server:
    
    
    def __init__(self, port, number_servers, number_neighbours):
        self.context = zmq.Context()
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
        for i in range(self.number_servers):
            port = 5557 + i
            for j in range(3):
                server_partion = "server_" + str(port) + "_" + str(j)
                hash = hashlib.sha256(server_partion.encode()).hexdigest()
                self.servers_hash.append(hash)
                self.servers_hash_port[hash] = port
        self.servers_hash.sort()


    def setup_socket(self):
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://localhost:{self.port}")
        for i in range(self.number_servers):
            port_server = 5557 + i
            if port_server != self.port:
                socket_server = self.context.socket(zmq.REQ)
                socket_server.connect(f"tcp://localhost:{port_server}")
                self.server_port_socket[port_server] = socket_server


    def connect_db(self):
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            with open('../db/schema.sql', 'r') as f:
                schema_sql = f.read()            
            with connection:
                connection.executescript(schema_sql)
        return connection, cursor
    
    
    def get_neighbours(self, index):
        neighbours = set()
        neighbours.add(self.servers_hash_port[self.servers_hash[index]])
        i = 0
        while len(neighbours) < self.number_neighbours + 1:
            neighbour_index = (index + i) % len(self.servers_hash)
            neighbours.add(self.servers_hash_port[self.servers_hash[neighbour_index]])
            i+=1
        return neighbours , i
    
    
    def write_neighbours(self, message):
        # define original message destination and neighbours of that server
        neighbours, next_index = self.get_neighbours(message["server_index"])
        if self.port in neighbours: neighbours.remove(self.port)
        # update original servers' neighbours
        neighbours_missing = neighbours.copy()
        for neighbour in neighbours:
            neighbour_message = message
            neighbour_message["neighbour"] = "yes"
            neighbour_socket = self.server_port_socket[neighbour]
            response = self.send_message(neighbour_message, neighbour_socket)
            if response is not None:
                neighbours_missing.remove(neighbour)
            else:
                self.server_port_socket[neighbour].close()
                self.server_port_socket[neighbour] = self.context.socket(zmq.REQ)
                self.server_port_socket[neighbour].connect(f"tcp://localhost:{neighbour}")         
        # try other neighbours
        if len(neighbours_missing) > 0:
            true_neighbour = neighbours_missing.pop()
            while len(neighbours_missing) != 0:
                neighbour = self.servers_hash_port[self.servers_hash[(next_index) % len(self.servers_hash)]]
                if neighbour == self.port or neighbour in neighbours: continue 
                neighbour_message = message
                neighbour_message["neighbour"] = "yes"
                neighbour_message["to_server"] = true_neighbour
                neighbour_socket = self.server_port_socket[neighbour]
                response = self.send_message(neighbour_message, neighbour_socket)
                if response is not None:
                    if len(neighbours_missing) > 0:
                        true_neighbour = neighbours_missing.pop()
                else:
                    self.server_port_socket[neighbour].close()
                    self.server_port_socket[neighbour] = self.context.socket(zmq.REQ)
                    self.server_port_socket[neighbour].connect(f"tcp://localhost:{neighbour}")
                next_index += 1
                
    
    def read_neighbours(self, url):
        # define neighbours to read from
        position = self.get_position_ring(url.encode())
        neighbours_ports = set()
        i = 1
        while len(neighbours_ports) < self.number_neighbours:
            neighbour_hash = self.servers_hash[(position + i) % len(self.servers_hash)]
            neighbours_ports.add(self.servers_hash_port[neighbour_hash])
            i+=1
        # read from neighbours
        send_message = {"cmd": "read", "url": url, "neighbour": "yes"}
        rec_response = []  
        for port in neighbours_ports:
            try:
                server_socket = self.server_port_socket[port]
                response = self.send_message(send_message, server_socket)
                if response is not None:
                    rec_response.append(response)     
                else:
                    self.server_port_socket[port].close()
                    self.server_port_socket[port] = self.context.socket(zmq.REQ)
                    self.server_port_socket[port].connect(f"tcp://localhost:{port}")
                    continue
            except Exception as e:
                print(f"Exception in read_neighbours - {e}")
                self.server_port_socket[port].close()
                self.server_port_socket[port] = self.context.socket(zmq.REQ)
                self.server_port_socket[port].connect(f"tcp://localhost:{port}")
                continue
        return rec_response
    
    
    def update_neighbours_thread(self, message, server):
        while True:
            try:
                server_socket = self.server_port_socket[server]
                response = self.send_message(message, server_socket)
                if response is not None:
                    break
            except Exception as e:
                print(f"Exception in update_neighbours_thread - {e}")
                self.server_port_socket[server].close()
                self.server_port_socket[server] = self.context.socket(zmq.REQ)
                self.server_port_socket[server].connect(f"tcp://localhost:{server}")
            time.sleep(10)


    def update_neighbours(self, message):
        if message['neighbour'] == "no": 
            self.write_neighbours(message)           
        elif message['neighbour'] == "yes" and "to_server" in message:
            server = message.pop("to_server")            
            thread = threading.Thread(target=self.update_neighbours_thread, args=(message, server))
            thread.daemon = True
            thread.start()
             
              
    def poll(self, message):
        try:
            if message["url"] not in database.get_lists_url(self.cursor): 
                self.add_list(message["id"], message["owner"], message["url"])
            else: 
                self.update_list(message['neighbour'] , message["crdt"], message["url"])
            self.update_neighbours(message)
        except Exception as e:
            print(f"Exception in poll - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
     
     
    def get_position_ring(self, url):
        hash_message_word = hashlib.sha1(url).hexdigest()
        for i in range(len(self.servers_hash)):
            if hash_message_word <= self.servers_hash[i]:
                return i
    
    
    def send_message(self, message, socket):
        try:
            socket.send_string(json.dumps(message), zmq.DONTWAIT)
            poller = zmq.Poller()
            poller.register(socket, zmq.POLLIN)
            events = dict(poller.poll(timeout=5000))                
            if socket in events and events[socket] == zmq.POLLIN:
                response = json.loads(socket.recv_string())
                return response
            else:                   
                return None
        except Exception as e:
            print(f"Exception in function send_message - {e}")
            return None
        
   
    def send_list_server(self, message):
        try:
            if message["url"] not in database.get_lists_url(self.cursor):
                self.socket.send(json.dumps({"status": "error"}).encode())
                return
            server_list = ShoppingList()
            for item, value in  database.get_list_items(self.cursor, message["url"]):
                server_list.add_item(item, value)
            self.socket.send(json.dumps({"status": "success", "crdt": server_list.to_dict()}).encode())
        except Exception as e:
            print(f"Exception in function send_list_server - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
    
    
    def send_list_client(self, message):
        try:
            for url, _, owner in database.get_lists(self.cursor):
                if url == message["url"]:
                    list = {}
                    for item, value in  database.get_list_items(self.cursor, message["url"]): list[item] = value
                    self.socket.send(json.dumps({"status": "success", "url": message["url"], "list": list, "owner": owner}).encode())
                    return
            self.socket.send(json.dumps({"status": "error"}).encode())  
        except Exception as e:
            print(f"Exception in send_list_client - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())


    def delete_list(self, message):
        try:
            ok = database.delete_list(self.connection, self.cursor, message["url"], message["id"])
            if ok: self.socket.send(json.dumps({"status": "success"}).encode())
            else: self.socket.send(json.dumps({"status": "error"}).encode())      
        except Exception as e:
            print(f"Exception in delete_list {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
     
     
    def add_list(self, client, owner, url):
        if client == owner:
            database.add_list_url(self.connection, self.cursor, url, client)
            for key, value in database.get_list_items(self.cursor, url):
                database.add_item(self.connection, self.cursor, url, key, value)
            self.socket.send(json.dumps({"status": "success", "url": url}).encode())
        else:     
            self.socket.send(json.dumps({"status": "deleted"}).encode())
    
    
    def update_list(self, neighbour, crdt, url):
        try:
            if neighbour == "no":
                # create client's crdt
                client_list = ShoppingList()
                for key, value in crdt.items():
                    client_list.items[key] = PNCounter(**value) 
                # create server's crdt           
                server_list = ShoppingList()
                for item, value in  database.get_list_items(self.cursor, url):
                    server_list.add_item(item, value)
                server_list.merge(client_list)
                # create neighbour's crdt
                rec_response = self.read_neighbours(url)
                for response in rec_response:
                    if "crdt" in response:
                        if len(response["crdt"]) != 0:
                            neighbour_list = ShoppingList().from_dict(response["crdt"])
                            server_list.merge(neighbour_list)
                for key, value in server_list.items.items():
                    database.add_item(self.connection, self.cursor, url, key, value.value(), False)
                self.socket.send(json.dumps({"status": "success", "url": url, "crdt": server_list.to_dict()}).encode())
            else:
                list = ShoppingList()
                for key, value in crdt.items(): list.items[key] = PNCounter(**value) 
                self.socket.send(json.dumps({"status": "success", "url": url, "crdt": list.to_dict()}).encode())
        except Exception as e:
            print(f"Exception in update_list - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
             
    def run(self):
        while True:    
            # check the responsible server
            message = json.loads(self.socket.recv().decode())
            hash_message_word = hashlib.sha1(message["url"].encode()).hexdigest()
            for i in range(len(self.servers_hash)):
                if hash_message_word <= self.servers_hash[i]:
                    message["server_index"] = i   
                    break      
            # perform action
            if message["cmd"] == "poll": self.poll(message)
            elif message["cmd"] == "read": self.send_list_server(message)
            elif message["cmd"] == "send": self.send_list_client(message)
            elif message["cmd"] == "delete": self.delete_list(message)
            else: self.socket.send(json.dumps({"status": "error"}).encode())


if __name__ == "__main__":
    if(len(argv) < 3): print("Error - missing parameters")
    else:
        for i in range(int(argv[1])):    
            port = 5557 + i
            server = Server(port, int(argv[1]), int(argv[2]))
            thread = threading.Thread(target=server.run)
            thread.start()