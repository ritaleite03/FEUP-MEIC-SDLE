import json
import random
from sys import argv
import threading
import time
from menu import *
from utils import *
import zmq
import database  
import crdt
import myCRDT


class Client:
              
                
    def __init__(self, id):      
       
        # variables
        self.lock = threading.Lock()
        self.id = id
        self.url = None
        self.list_crdts = {}
        
        # database connection
        self.connection, self.cursor = database.connect_db(f"../db/database_user_{id}.db")
        database.add_client(self.connection, self.cursor, self.id)
        for url, owner, deleted, crdt in database.get_lists(self.cursor):
            crdt_object = myCRDT.AWMap.from_dict(self.id,crdt)
            self.list_crdts[url] = (crdt_object, owner, deleted)
       
        # ZMQ sockets
        self.context = zmq.Context()
        self.socket_5555 = self.context.socket(zmq.REQ)
        self.socket_5555.connect("tcp://localhost:5555")
        self.socket_5556 = self.context.socket(zmq.REQ)
        self.socket_5556.connect("tcp://localhost:5556")
       
        # threads
        database_thread = threading.Thread(target=self.database_thread)
        database_thread.daemon = True
        database_thread.start()        
        polling_thread = threading.Thread(target=self.polling_thread)
        polling_thread.daemon = True
        polling_thread.start()
        
        
    def database_thread(self):
        while True:
            with self.lock: temp_list_crdts = self.list_crdts
            for url, tuple in temp_list_crdts.items():
                with self.lock: database.update_list(self.connection, self.cursor, url, str(tuple[0].to_dict()), tuple[1], tuple[2])
            time.sleep(10)
    
    
    def polling_thread(self): 
        while True:
            
            if self.url:
        
                # send message
                with self.lock:
                    crdt = self.list_crdts[self.url][0].to_dict()
                    owner = self.list_crdts[self.url][1]
                message = self.send_message({"neighbour": "no", "cmd": "poll", "url": self.url, "id": self.id, "owner": owner, "crdt": str(crdt)})        

                # if list deleted
                if message is not None and message["status"] == "deleted":
                    with self.lock:
                        crdt_info = self.list_crdts[self.url]
                        crdt = crdt_info[0]
                        owner = crdt_info[1]
                        self.list_crdts[self.url] = (crdt, owner, True)    
                    print("\nThis list was deleted")
                    print("\nWrite here : ")
                    self.url = None
                
                # if list updated
                if message is not None and message["status"] == "success":
                    if "crdt" in message.keys():
                        crdt = myCRDT.AWMap.from_dict(self.id, message["crdt"])
                        with self.lock:
                            crdt_info = self.list_crdts[self.url]          
                            current_crdt = crdt_info[0]
                            current_crdt.merge(crdt)
                            self.list_crdts[self.url] = (current_crdt, owner, True)  
                    print("\nThis list was sincronized")
                    print("\nWrite here : ")
                    
            time.sleep(30)
        
        
    def select_list(self):
        url = name_menu(MENU_SELECT_LIST)
        if (url.lower() == '0' or url.lower() == '1'): return
        with self.lock:
            self.url = database.get_url_list(self.cursor, url)
        if self.url == None:
            print_error("Something went wrong.")
            self.select_list()
    
        
    def create_list(self):
        with self.lock: 
            self.url = database.add_list(self.connection, self.cursor, self.id)
            self.list_crdts[self.url] = (myCRDT.AWMap(self.id), self.id, False)
        if self.url == None:
            self.create_list()

    
    def download_list(self):  
        url = menu(MENU_DOWNLOAD_LIST)
        if (url.lower() == '0' or url.lower() == '1'): return 
        message = self.send_message({"neighbour": "no", "cmd": "send", "url": url, "id": self.id})   
        if message is None:
            print_error("The list's name does not exist")
            self.download_list()     
        else :     
            with self.lock:
                self.url = url
                database.add_client(self.connection, self.cursor, message["owner"])
                crdt = myCRDT.AWMap.from_dict(self.id, message["crdt"])
                crdt.node_it = self.id
                self.list_crdts[self.url] = (crdt, message["owner"], False)            
     
       
    def update_list(self):
        while (self.url != None):
            with self.lock: 
                values = self.list_crdts[self.url][0].values()
            last_line = ""
            for key, value in values.items():
                if value == 0:
                    last_line += "\nItem : " + key + " (purchased)"
                else:
                    last_line += "\nItem : " + key + " : " + str(value)
            option = option_menu(MENU_UPDATE_LIST, 0, 7, "The URL is " + self.url + ".\nThe items are: " + last_line + ".\n")    
            if(self.url == None):
                print_error("The list was deleted by its owner")   
                return 

            if (option == 1): self.inc_item()
            if (option == 2): self.dec_item()
            if (option == 3): self.delete_item()
            if (option == 4): self.delete_list()
            if (option == 5): continue
            if (option == 6): return
        
    
    def inc_item(self):   
        try:
            quantity, item = quantity_item_menu(MENU_ADD_ITEM)  
            with self.lock: self.list_crdts[self.url][0].add_item(item, quantity)
        except:
            return
            # print_error("Something went wrong.")     
    
    
    def dec_item(self):
        try:
            quantity, item = quantity_item_menu(MENU_DEC_ITEM)
            with self.lock: self.list_crdts[self.url][0].add_item(item, -quantity)
        except:
            return
            # print_error("Something went wrong.")
   
   
    def delete_item(self):
        try:
            item = name_menu(MENU_DEL_ITEM)
            with self.lock: self.list_crdts[self.url][0].remove_item(item)
        except:
            return
            # print_error("Something went wrong.")
      
      
    def delete_list(self):
        message = self.send_message({"neighbour": "no", "cmd": "delete", "url": self.url, "id": self.id})
        if message is None:
            print_error("Something went wrong! You may not be the owner or the list is not in the servers's databases. The list will be deleted from your local database")   
        with self.lock:
            crdt = self.list_crdts[self.url][0]
            owner = self.list_crdts[self.url][1]
            self.list_crdts[self.url] = (crdt, owner, True)
            
      
    def send_message(self, message_json):
        while True:
            
            # randomly choose socket
            sockets = [self.socket_5555, self.socket_5556]
            random.shuffle(sockets)
            
            #for socket in sockets:
            socket = sockets[0]
            try:
                
                # send message to server
                socket.send(json.dumps(message_json).encode(), zmq.DONTWAIT)
                poller = zmq.Poller()
                poller.register(socket, zmq.POLLIN)
                events = dict(poller.poll(timeout=60000))
                
                # if it is alive
                if socket in events and events[socket] == zmq.POLLIN:
                    response = json.loads(socket.recv_string())
                    poller.unregister(socket)
                    if response["status"] == "error": return None
                    elif response["status"] == "deleted": return response
                    else: return response
                
                # if it is not alive
                else:
                    poller.unregister(socket)
                    if socket == self.socket_5555:
                        self.socket_5555.close()
                        self.socket_5555 = self.context.socket(zmq.REQ)
                        self.socket_5555.connect("tcp://localhost:5555")
                    else:
                        self.socket_5556.close()
                        self.socket_5556 = self.context.socket(zmq.REQ)
                        self.socket_5556.connect("tcp://localhost:5556")       
            
            except Exception as e:
                poller.unregister(socket)
                print(f"Error sending message: {e}")   
    
    
    def run(self):
        while True:
            
            # menu to input action to perform
            with self.lock: lists = self.list_crdts.keys()
            option = option_menu(MENU_LIST, 0, 5, get_lists_to_string(lists))        
            
            # perform action
            if option == 1 : self.select_list()
            if option == 2 : self.create_list()
            if option == 3 : self.download_list()
            if option == 4 : return 
            self.update_list()

      
        
if __name__ == "__main__":
    if(len(argv) < 2):
        print("Error - missing parameters")
    else:
        client = Client(int(argv[1]))
        client.run()