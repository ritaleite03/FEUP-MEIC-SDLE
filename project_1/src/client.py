import json
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
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        
        
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
        
        # send request
        self.socket.send(json.dumps({"neighbour": "no", "command": "download_list", "url" : url}).encode())
        message = json.loads(self.socket.recv().decode())
        if(message["status"] == 'error'):
            print_error("The list's name does not exists")
            self.download_list()
        self.url = url
        database.add_list_url(self.connection, self.cursor, self.url)
        
        # initiate shopping list
        items = message["list"]
        for (name, quantity) in items:
            self.shopping_list[name] = quantity
            database.add_item(self.connection, self.cursor, name, quantity)
     
       
    def update_list(self):
        last_line = "The URL is " + self.url + ".\n" + self.get_list_items_to_string()
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
   
    def polling(self):
        while True:
            if self.url:                
                self.socket.send(json.dumps({"neighbour": "no", "command": "polling", "url": self.url, "list": self.shopping_list}).encode())
                response = self.socket.recv().decode()
                #print(f"Sent URL: {self.url}, received: {response}")            
            time.sleep(10)
    
    def run(self):
        option = option_menu(MENU_LIST, 0, 5, self.get_lists_to_string())
        # perform option
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
       
    def get_lists_to_string(self):
        lists = database.get_lists(self.cursor)
        lists_string = "You hava already this lists saved:"
        if(len(lists) == 0):
            return "There is no list saved.\n"
        for (name, url) in lists:
            lists_string += "URL : " + url + " , " + "Name : " + name + "\n"
        return lists_string
    
    def get_list_items_to_string(self):
        items = database.get_list_items(self.cursor, self.url)
        items_string = "Here is the content of this list:"
        if(len(items) == 0):
            return "This list is empty.\n"
        for (name, quantity) in items:
            items_string += "Item : " + name + " , " + "Quantity : " + str(quantity) + "\n"
        return str(items_string)
        
if __name__ == "__main__":
    if(len(argv) < 2):
        print("Error - missing parameters")
    else:
        client = Client(int(argv[1]))
        client.run()