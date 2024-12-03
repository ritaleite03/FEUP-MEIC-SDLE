import json
import random
import sqlite3
from sys import argv
import threading
import time
import uuid
from menu import *
from utils import *
import zmq
import database  

class Client:
        
        
    def __init__(self, id):
        
        self.id = id
        self.url = None
        self.shopping_list = {}
        self.connection, self.cursor = database.connect_db(f"../db/database_user_{id}.db")
        
        # create socket
        self.context = zmq.Context()
        self.socket_5555 = self.context.socket(zmq.REQ)
        self.socket_5555.connect("tcp://localhost:5555")
        
        self.socket_5556 = self.context.socket(zmq.REQ)
        self.socket_5556.connect("tcp://localhost:5556")
        
        
    def select_list(self):
        
        # get url and check if client wants to leave / go back
        url = name_menu(MENU_SELECT_LIST)
        if (url.lower() == '0' or url.lower() == '1'): 
            return
        
        # get url of the list
        self.url = database.get_list_url(self.cursor, url)
        if self.url == None:
            print_error("Something went wrong.")
            self.select_list()
        
        # initiate shopping list
        items = database.get_list_items(self.cursor, self.url)
        for (name, quantity) in items:
            self.shopping_list[name] = quantity
    
    
    def create_list(self):
        
        # check if client wants to leave / go back
        list_name = name_menu(MENU_CREATE_LIST)
        if (list_name.lower() == '0' or list_name.lower() == '1'):
            return
        
        # get url of the list
        self.url = database.add_list(self.connection, self.cursor, list_name)
        if self.url == None:
            print_error("Something went wrong.")
            self.create_list()

    
    def download_list(self):
        
        # check if client wants to leave / go back
        url = menu(MENU_DOWNLOAD_LIST)
        if (url.lower() == '0' or url.lower() == '1'): 
            return

        message = self.send_message({"neighbour": "no", "command": "download_list", "url": url})
        
        if message is None:
            print_error("The list's name does not exist")
            self.download_list()
        
        else :     
               
            self.url = url
            database.add_list_url(self.connection, self.cursor, self.url)
            
            # initiate shopping list
            items = message["list"]
            for (name, quantity) in items:
                self.shopping_list[name] = quantity
                database.add_item(self.connection, self.cursor, name, quantity)
     
       
    def update_list(self):
        items = database.get_list_items(self.cursor, self.url)
        last_line = "The URL is " + self.url + ".\n" + get_list_items_to_string(items)
        option = option_menu(MENU_UPDATE_LIST, 0, 6, last_line)
        if (option == 1):
            self.add_items()
        if (option == 2):
            self.delete_items()
        if (option == 4):
            return
        self.update_list()
    
    
    def add_items(self):
        
        # update shopping list
        quantity, item = quantity_item_menu(MENU_ADD_ITEM)
        if item not in self.shopping_list:
            self.shopping_list[item] = 0
        self.shopping_list[item] += quantity
        
        # update database
        ok = database.add_item(self.connection, self.cursor, self.url, item, self.shopping_list[item])
        if not ok: 
            print_error("Something went wrong.")
    
    
    def delete_items(self):
        
        # update shopping list
        quantity, item = quantity_item_menu(MENU_ADD_ITEM)
        if item not in self.shopping_list:
            self.shopping_list[item] = 0
        self.shopping_list[item] -= quantity
        
        # update database
        ok = database.delete_item(self.connection, self.cursor, self.url, item, self.shopping_list[item])
        if not ok: print_error("Something went wrong.")
   
   
    def reconfigure_sockets(self):
        
        self.socket_5555.close()
        self.socket_5556.close()
        
        self.context = zmq.Context()
        self.socket_5555 = self.context.socket(zmq.REQ)
        self.socket_5555.connect("tcp://localhost:5555")
        
        self.socket_5556 = self.context.socket(zmq.REQ)
        self.socket_5556.connect("tcp://localhost:5556")
        
        
    def send_message(self, message_json):
      
        poller = zmq.Poller()
      
        while True:
          
            try:
              
                # choose random socket and register them in poller
                chosen_socket = random.choice([self.socket_5555, self.socket_5556])
                other_socket = self.socket_5556 if chosen_socket == self.socket_5555 else self.socket_5555
                poller.register(chosen_socket, zmq.POLLIN)
                poller.register(other_socket, zmq.POLLIN)

                # send to first socket
                print("Trying with first socket ...")
                chosen_socket.send(json.dumps(message_json).encode())
                events = dict(poller.poll(timeout=10000))

                if chosen_socket in events and events[chosen_socket] == zmq.POLLIN:
                    message = json.loads(chosen_socket.recv().decode())
                    if message["status"] == 'error':
                        print("Error in response from first socket.")
                        self.reconfigure_sockets()
                        return None
                    else:
                        print("Received valid response from first socket.")
                        return message

                else:
                    
                    # send to second socket
                    print("No response from first socket. Trying second socket...")
                    other_socket.send(json.dumps(message_json).encode())
                    events = dict(poller.poll(timeout=10000))

                    if other_socket in events and events[other_socket] == zmq.POLLIN:
                        message = json.loads(other_socket.recv().decode())
                        if message["status"] == 'error':
                            print("Error in response from second socket.")
                            self.reconfigure_sockets()
                            return None
                        else:
                            print("Received valid response from second socket.")
                            return message

                    else:
                        print("None of the sockets responded.")
                        self.reconfigure_sockets()

            except Exception as e:
                print(f"Error sending message: {e}")
                poller.unregister(chosen_socket)
                poller.unregister(other_socket)
                self.reconfigure_sockets()
   
    def polling(self):
        while True:
            if self.url:         
                message = self.send_message({"neighbour": "no", "command": "polling", "url": self.url, "list": self.shopping_list})        
            time.sleep(10)
    
    
    def run(self):
        lists = database.get_lists(self.cursor)
        option = option_menu(MENU_LIST, 0, 5, get_lists_to_string(lists))
        if (option == 1):
            self.select_list()
        if (option == 2):
            self.create_list()
        if (option == 3):
            self.download_list()
        if (option == 4):
            return 
        polling_thread = threading.Thread(target=self.polling)
        polling_thread.start()
        self.update_list()

        
if __name__ == "__main__":
    
    if(len(argv) < 2):
        print("Error - missing parameters")
    
    else:
        client = Client(int(argv[1]))
        client.run()