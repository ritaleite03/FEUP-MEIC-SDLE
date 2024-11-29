import json
import sqlite3
from sys import argv
import uuid
from menu import *
from utils import *
import zmq
import database


class Client:
    
    
    def __init__(self, id):
        self.id = id
        self.url = None
        self.connection, self.cursor = database.connect_db(f"../db/database_user_{id}.db")
        # create socket
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
    
    
    def select_list(self):
        list_name = name_menu(MENU_SELECT_LIST)
        if (list_name.lower() == '0' or list_name.lower() == '1'):
            return
        ok, self.url = database.list_get(self.connection, self.cursor, list_name)
        if not ok:
            print_error("The list's url does not exists")
            self.select_list()
        return
    
    
    def create_list(self):
        list_name = name_menu(MENU_CREATE_LIST)
        if (list_name.lower() == '0' or list_name.lower() == '1'):
            return
        self.url = database.list_add(self.connection, self.cursor, list_name)
        return
    
    
    def download_list(self):
        list_name = menu(MENU_DOWNLOAD_LIST)
        if (list_name.lower() == '0' or list_name.lower() == '1'):
            return
        self.socket.send(json.dumps({"neighbour": "no", "command": "download_list", "list" : list_name}).encode())
        message = json.loads(self.socket.recv().decode())
        if(message["status"] == 'error'):
            print_error("The list's name does not exists")
    
    
    def update_list(self):
        option = option_menu(MENU_UPDATE_LIST, 0, 6)
        if (option == 1):
            self.add_items()
        if (option == 2):
            self.delete_items()
        if (option == 3):
            self.url_list()
        if (option == 4):
            self.items_list()
        if (option == 5):
            return
        self.update_list()
    
    
    def url_list(self):
        print(self.url)
        input("\nPress any key to continue.")
    
        
    def items_list(self):
        items = database.list_items(self.cursor, self.url)
        print(items)
        input("\nPress any key to continue.")
    
    
    def add_items(self):
        quantity, item = quantity_item_menu(MENU_ADD_ITEM)       
        database.item_add(self.connection, self.cursor, self.url, item, quantity)
    
    
    def delete_items(self):
        quantity, item = quantity_item_menu(MENU_ADD_ITEM)       
        ok = database.item_delete(self.connection, self.cursor, self.url, item, quantity)
        if not ok:
            print_error("The list does not have that item")
            self.select_list()
        return
    
    
    def run(self):
        option = option_menu(MENU_LIST, 0, 5)
        # perform option
        if (option == 1):
            self.select_list()
        if (option == 2):
            self.create_list()
        if (option == 3):
            self.download_list()
        if (option == 4):
            return 
        self.update_list()
    
        
if __name__ == "__main__":
    if(len(argv) < 2):
        print("Error - missing parameters")
    else:
        client = Client(int(argv[1]))
        client.run()