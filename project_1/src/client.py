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

class Client:
                
                
    def __init__(self, id):      
        # variables
        self.lock = threading.Lock()
        self.id = id
        self.url = None
        self.crdt = None
        # database connection
        self.connection, self.cursor = database.connect_db(f"../db/database_user_{id}.db")
        database.add_client(self.connection, self.cursor, self.id)
        # ZMQ sockets
        self.context = zmq.Context()
        self.socket_5555 = self.context.socket(zmq.REQ)
        self.socket_5555.connect("tcp://localhost:5555")
        self.socket_5556 = self.context.socket(zmq.REQ)
        self.socket_5556.connect("tcp://localhost:5556")
        # polling thread
        polling_thread = threading.Thread(target=self.polling)
        polling_thread.start()
        
        
    def select_list(self):
        # menu to input list's url
        url = name_menu(MENU_SELECT_LIST)
        if (url.lower() == '0' or url.lower() == '1'): return    
        # select list if no error
        with self.lock:
            self.url = database.get_list_url(self.cursor, url)
            self.crdt = crdt.ShoppingList()
            for item, value in  database.get_list_items(self.cursor, url):
                self.crdt.add_item(item, value) 
        if self.url == None:
            print_error("Something went wrong.")
            self.select_list()
    
    
    def create_list(self):
        # menu to input list's name
        name = name_menu(MENU_CREATE_LIST)
        if (name.lower() == '0' or name.lower() == '1'): return  
        # create list if no error
        with self.lock: 
            self.url = database.add_list(self.connection, self.cursor, name, self.id)
            self.crdt = crdt.ShoppingList()
        if self.url == None:
            print_error("Something went wrong.")
            self.create_list()

    
    def download_list(self):  
        # menu to input list's url
        url = menu(MENU_DOWNLOAD_LIST)
        if (url.lower() == '0' or url.lower() == '1'): return 
        # send message to server
        message = self.send_message({"neighbour": "no", "cmd": "send", "url": url, "id": self.id})   
        # no message, then error
        if message is None:
            print_error("The list's name does not exist")
            self.download_list()     
        # add list and items to database
        else :     
            with self.lock:
                self.url = url
                self.crdt = crdt.ShoppingList()
                database.add_client(self.connection, self.cursor, message["owner"])
                database.add_list_url(self.connection, self.cursor, self.url, message["owner"])
                for name, quantity in message["list"].items(): 
                    database.add_item(self.connection, self.cursor, self.url, name, int(quantity))
                    self.crdt.add_item(name, quantity)
     
     
    def delete_list(self):
        # send message to server
        message = self.send_message({"neighbour": "no", "cmd": "delete", "url": self.url, "id": self.id})
        # no message, then error
        if message is None:
            print_error("Something went wrong! You may not be the owner or the list is not in the servers's databases. The list will be deleted from your local database")   
        # delete list from database
        with self.lock:
            ok = database.delete_list(self.connection, self.cursor, self.url, self.id)
            self.url = None
       
       
    def update_list(self):
        while (self.url != None):
            # menu to input action to perform
            with self.lock: items = database.get_list_items(self.cursor, self.url)
            last_line = "The URL is " + self.url + ".\n" + get_list_items_to_string(items)
            option = option_menu(MENU_UPDATE_LIST, 0, 6, last_line)    
            # check url (list may have been deleted)
            if(self.url == None):
                print_error("The list was deleted by its owner")   
                return 
            # perform action
            if (option == 1): self.add_items()
            if (option == 2): self.delete_items()
            if (option == 3): self.delete_list()
            if (option == 4): return
    
    
    def add_items(self):   
        # menu to input quantity and item  
        quantity, item = quantity_item_menu(MENU_ADD_ITEM)  
        # update database
        with self.lock:
            ok = database.add_item(self.connection, self.cursor, self.url, item, int(quantity))
            self.crdt.add_item(item, quantity)
        if not ok: print_error("Something went wrong.")
    
    
    def delete_items(self):       
        # menu to input quantity and item    
        quantity, item = quantity_item_menu(MENU_ADD_ITEM)
        # update database
        with self.lock:
            ok = database.delete_item(self.connection, self.cursor, self.url, item, quantity)
            self.crdt.del_item(item, quantity)
        if not ok: print_error("Something went wrong.")
   
      
    def send_message(self, message_json):
        while True:
            # randomly choose socket
            sockets = [self.socket_5555, self.socket_5556]
            random.shuffle(sockets)
            #for socket in sockets:
            socket = sockets[0]
            try:
                # send message to server
                socket.send_string(json.dumps(message_json), zmq.DONTWAIT)
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
    
    
    def polling(self): 
        while True:
            # if some list is selected
            if self.url:             
                # get owner of the list and its items
                with self.lock:    
                    owner = database.get_list_owner(self.cursor, self.url)
                    items = database.get_list_items(self.cursor, self.url)
                # convert format of list of items to dict
                shopping_list = {}
                for (name, quantity) in items: shopping_list[name] = quantity
                # send message to server
                message = self.send_message({"neighbour": "no", "cmd": "poll", "url": self.url, "list": shopping_list, "id": self.id, "owner": owner, "crdt": self.crdt.to_dict()})        
                if message is not None and message["status"] == "deleted":
                    with self.lock:
                        database.delete_list_no_owner(self.connection, self.cursor, self.url)
                    print("\nThis list was deleted")
                    print("\nWrite here : ")
                    self.url = None
                if message is not None and message["status"] == "success":
                    with self.lock:
                        self.crdt = crdt.ShoppingList()
                        for name, quantity in message["crdt"].items(): 
                            database.add_item(self.connection, self.cursor, self.url, name, int(quantity['positive'] + quantity['negative']), False)
                            self.crdt.add_item(name, quantity['positive'])
                            self.crdt.del_item(name, quantity['negative'])
                        print("\nThis list was sincronized")
                        print("\nWrite here : ")
                        
            time.sleep(10)
    
    
    def run(self):
        while True:
            # menu to input action to perform
            with self.lock: lists = database.get_lists_not_deleted(self.cursor)
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