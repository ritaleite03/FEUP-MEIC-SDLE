import hashlib
import json
import sqlite3
from sys import argv
import threading
import time
import zmq
import database
import myCRDT


class Server:   
    
    
    def __init__(self, port, number_servers, number_neighbours):
        
        self.lock = threading.Lock()
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
                
        self.list_crdts = {}
        for url, owner, deleted, crdt in database.get_lists(self.cursor):
            server_id = str(-self.port)
            crdt_object = myCRDT.AWMap.from_dict(server_id, crdt)
            self.list_crdts[url] = (crdt_object, owner, deleted)
          
        # threads
        database_thread = threading.Thread(target=self.database_thread)
        database_thread.daemon = True
        database_thread.start()  


    def database_thread(self):
        while True:
            temp_list_crdts = self.list_crdts.copy()
            for url, tuple in temp_list_crdts.items():
                database.update_list(self.connection, self.cursor, url, str(tuple[0].to_dict()), tuple[1], tuple[2])
            time.sleep(10)
            
            
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
        servers_tried = set()
        neighbours, next_index = self.get_neighbours(message["server_index"])
        if self.port in neighbours: neighbours.remove(self.port)
        
        # update original servers' neighbours
        neighbours_missing = neighbours.copy()
        for neighbour in neighbours:
            servers_tried.add(neighbour)
            neighbour_message = message
            neighbour_message["neighbour"] = "yes"
            neighbour_socket = self.server_port_socket[neighbour]
            try:
                with self.lock:
                    response = self.send_message(neighbour_message, neighbour_socket)

                if response is not None:
                    neighbours_missing.remove(neighbour)

                else:
                    self.server_port_socket[neighbour].close()
                    self.server_port_socket[neighbour] = self.context.socket(zmq.REQ)
                    self.server_port_socket[neighbour].connect(f"tcp://localhost:{neighbour}")
            except:
                self.server_port_socket[neighbour].close()
                self.server_port_socket[neighbour] = self.context.socket(zmq.REQ)
                self.server_port_socket[neighbour].connect(f"tcp://localhost:{neighbour}")    
        
        # try other neighbours
        if len(neighbours_missing) > 0:
            true_neighbour = neighbours_missing.pop()            
            while True:                
                neighbour = self.servers_hash_port[self.servers_hash[(next_index) % len(self.servers_hash)]]
                next_index += 1
                if neighbour in servers_tried: continue
                if neighbour == self.port or neighbour in neighbours: continue 
                servers_tried.add(neighbour)
                neighbour_message = message
                neighbour_message["neighbour"] = "yes"
                neighbour_message["to_server"] = true_neighbour
                neighbour_socket = self.server_port_socket[neighbour]
                try:
                    with self.lock:
                        response = self.send_message(neighbour_message, neighbour_socket)

                    if response is not None:
                        print(f"Server {neighbour} will try to update {true_neighbour}")
                        if len(neighbours_missing) > 0:
                            true_neighbour = neighbours_missing.pop()
                        else:
                            break
                        
                    else:
                        self.server_port_socket[neighbour].close()
                        self.server_port_socket[neighbour] = self.context.socket(zmq.REQ)
                        self.server_port_socket[neighbour].connect(f"tcp://localhost:{neighbour}")
                except:
                    self.server_port_socket[neighbour].close()
                    self.server_port_socket[neighbour] = self.context.socket(zmq.REQ)
                    self.server_port_socket[neighbour].connect(f"tcp://localhost:{neighbour}")
                
                if len(servers_tried) == self.number_servers - 1: break                  
    
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
            if port == self.port: continue
            
            try:
                server_socket = self.server_port_socket[port]
                with self.lock:
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
        print("Start trying to update neighboring server")
        
        while True:
            
            try:
                server_socket = self.server_port_socket[server]
                with self.lock:
                    response = self.send_message(message, server_socket)
                if response is not None: break
                else:
                    self.server_port_socket[server].close()
                    self.server_port_socket[server] = self.context.socket(zmq.REQ)
                    self.server_port_socket[server].connect(f"tcp://localhost:{server}")
            
            except Exception as e:
                # print(f"Exception in update_neighbours_thread - {e}")
                self.server_port_socket[server].close()
                self.server_port_socket[server] = self.context.socket(zmq.REQ)
                self.server_port_socket[server].connect(f"tcp://localhost:{server}")
            time.sleep(10)
            
        print("Stop trying to update neighboring server")


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
                self.add_list(message["id"], message["owner"], message["url"], message["crdt"])
                self.update_neighbours(message)
            
            elif message["url"] not in database.get_lists_not_deleted_url(self.cursor):
                self.socket.send(json.dumps({"status": "deleted"}).encode())
                self.update_neighbours({"neighbour": "no", "cmd": "delete", "url": message["url"], "id": message["id"]})
            
            else:
                self.update_list(message['neighbour'] , message["crdt"], message["url"], message["owner"])
                self.update_neighbours(message)
        
        except Exception as e:
            print(f"Exception in poll - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
     
      
    def get_position_ring(self, url):
        hash_message_word = hashlib.sha256(url).hexdigest()
        for i in range(len(self.servers_hash)):
            if hash_message_word <= self.servers_hash[i]:
                return i
    
    
    def send_message(self, message, socket):
        try:
            socket.send_string(json.dumps(message), zmq.DONTWAIT)
            poller = zmq.Poller()
            poller.register(socket, zmq.POLLIN)
            events = dict(poller.poll(timeout=1000))                
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
            if message["url"] in self.list_crdts.keys():
                crdt = self.list_crdts[message["url"]][0]
                self.socket.send(json.dumps({"status": "success", "crdt": str(crdt.to_dict())}).encode())
            else:
                self.socket.send(json.dumps({"status": "error"}).encode())
        except Exception as e:
            print(f"Exception in function send_list_server - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
    
    
    def send_list_client(self, message):
        try:
            for url, owner, _, _ in database.get_lists_not_deleted(self.cursor):
                if url == message["url"]:
                    server_crdt = self.list_crdts[url][0]
                    # create neighbour's crdt
                    rec_response = self.read_neighbours(url)
                    for response in rec_response:
                        if "crdt" in response and len(response["crdt"]) != 0:
                            neighbour_crdt = myCRDT.AWMap.from_dict(None,response["crdt"])
                            server_crdt.merge(neighbour_crdt)                    
                    self.socket.send(json.dumps({"status": "success", "url": message["url"], "crdt": str(server_crdt.to_dict()), "owner": owner}).encode())
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
            self.update_neighbours(message)   
        except Exception as e:
            print(f"Exception in delete_list - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
    
        
    def add_list(self, client, owner, url, crdt):
        try:
            server_id = str(-self.port)
            self.list_crdts[url] = (myCRDT.AWMap.from_dict(server_id,crdt), owner, False)
            self.socket.send(json.dumps({"status": "success", "url": url}).encode())
        except Exception as e:
            print(f"Exception in add_list - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
        
       
    def update_list(self, neighbour, crdt, url, owner):
        try:
            if neighbour == "no":  
                print("Updating as original server")
                # create client's crdt
                client_crdt = myCRDT.AWMap.from_dict(None,crdt)

                # create server's crdt
                if url in self.list_crdts.keys():
                    server_crdt = self.list_crdts[url][0]          
                    server_crdt.merge(client_crdt)
                else:
                    server_id = str(-self.port)
                    server_crdt = myCRDT.AWMap.from_dict(server_id, crdt)
                    
                # create neighbour's crdt
                rec_response = self.read_neighbours(url)
                for response in rec_response:
                    if "crdt" in response and len(response["crdt"]) != 0:
                        neighbour_crdt = myCRDT.AWMap.from_dict(None,response["crdt"])
                        server_crdt.merge(neighbour_crdt)
                self.list_crdts[url] = (server_crdt, owner, False)
                self.socket.send(json.dumps({"status": "success", "url": url, "crdt": str(server_crdt.to_dict())}).encode())
           
            else:
                print("Updating as neighboring server")
                server_id = str(-self.port)
                self.list_crdts[url] = (myCRDT.AWMap.from_dict(server_id ,crdt), owner, False)
                self.socket.send(json.dumps({"status": "success", "url": url, "crdt": crdt}).encode())
        
        except Exception as e:
            print(f"Exception in update_list - {e}")
            self.socket.send(json.dumps({"status": "error"}).encode())
       
            
    def run(self):
        while True:    
            # check the responsible server
            message = json.loads(self.socket.recv().decode())
            hash_message_word = hashlib.sha256(message["url"].encode()).hexdigest()
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
        server = Server(int(argv[1]), int(argv[2]), int(argv[3]))
        thread = threading.Thread(target=server.run)
        thread.start()