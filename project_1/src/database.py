import sqlite3
import uuid


def connect_db(path):
    
    # connect to the database
    connection = sqlite3.connect(path, check_same_thread=False)
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


def add_client(connection, cursor, client):
    try:
        cursor.execute('''SELECT id FROM client WHERE id = ?''', (client,))
        exists_item_list = cursor.fetchone()
        if exists_item_list is [] or exists_item_list is None:
            cursor.execute('''INSERT INTO client (id) VALUES (?)''', (client,))
            connection.commit()
        return True
    except:
       return False

def get_lists_url(cursor):
    cursor.execute('''SELECT url FROM list''')
    rows = cursor.fetchall()
    urls = [row[0] for row in rows]
    return urls

def get_lists_not_deleted_url(cursor):
    cursor.execute('''SELECT url FROM list WHERE deleted = ?''', (False,))
    rows = cursor.fetchall()
    urls = [row[0] for row in rows]
    return urls

def get_lists(cursor):
    cursor.execute('''SELECT name, url, owner FROM list''')
    list = cursor.fetchall()
    return list

def get_lists_not_deleted(cursor):
    cursor.execute('''SELECT name, url, owner FROM list WHERE deleted = ?''', (False,))
    list = cursor.fetchall()
    return list

def get_list_url(cursor, list_name):
    try:
        cursor.execute('''SELECT * FROM list WHERE url = ?''', (list_name,))
        exists_item = cursor.fetchone()
        if exists_item is [] or exists_item is None:
            return None
        return list_name
    except:
        return None


def get_list_owner(cursor, url):
    try:
        cursor.execute('''SELECT * FROM list WHERE url = ?''', (url,))
        exists_item = cursor.fetchone()
        if exists_item is [] or exists_item is None:
            return None
        return exists_item[2]
    except:
        return None
  
    
def get_list_items(cursor, list_url):
    cursor.execute('''SELECT item, quantity FROM item_list WHERE list = ?''', (list_url,))
    items = cursor.fetchall()
    return items


def add_list_url(connection, cursor, url, client):
    try:
        cursor.execute('''INSERT INTO list (url, name, owner) VALUES (?, ?, ?)''', (url, url, client,))
        connection.commit()
        return url
    except:
        return None


def add_list(connection, cursor, list_name, client):
    try:
        url = str(uuid.uuid4())
        cursor.execute('''INSERT INTO list (url, name, owner) VALUES (?, ?, ?)''', (url, list_name, client,))
        connection.commit()
        return url
    except:
        return None


def add_item(connection, cursor, list, item, quantity, update=True):
    
    # check if item name exists
    cursor.execute('''SELECT * FROM item_list WHERE item = ?''', (item,))
    exists_item = cursor.fetchone()
    if exists_item is [] or exists_item is None:
        cursor.execute('''INSERT INTO item_list (item, quantity) VALUES (?, ?)''', (item, quantity,))
        connection.commit()
    
    # check if item and list relation exists
    cursor.execute('''SELECT quantity FROM item_list WHERE item = ? AND list = ?''', (item,list,))
    exists_item_list = cursor.fetchone()
    
    # add item to list
    if exists_item_list is [] or exists_item_list is None:
        cursor.execute('''INSERT INTO item_list (item, list, quantity) VALUES (?, ?, ?)''', (item, list, quantity,))
        connection.commit()
        
    # update item in list
    else: 
        if update:
            old_quantity = exists_item_list[0]
            new_quantity = old_quantity + quantity
            cursor.execute('''UPDATE item_list SET quantity = ? WHERE item = ? AND list = ?''', (new_quantity, item, list,)) 
        else:
            cursor.execute('''UPDATE item_list SET quantity = ? WHERE item = ? AND list = ?''', (quantity, item, list,)) 
        
    
def delete_item(connection, cursor, list, item, quantity):
    
    # check if item and list relation exists
    cursor.execute('''SELECT quantity FROM item_list WHERE item = ? AND list = ?''', (item,list,))
    exists_item_list = cursor.fetchone()
    
    if not (exists_item_list is [] or exists_item_list is None):
        
        old_quantity = exists_item_list[0]
        new_quantity = old_quantity - quantity
        
        # check if new quantity is positive
        if new_quantity > 0:
            cursor.execute('''UPDATE item_list SET quantity = ? WHERE item = ? AND list = ?''', (new_quantity, item, list,)) 
            connection.commit()
        
        # if not, delete relation
        else:
            cursor.execute('''DELETE FROM item_list WHERE item = ? AND list = ?''', (item, list,))
            connection.commit()
        
        return True
    
    return False
    
    
def delete_list(connection, cursor, list, owner):
    try:    
        cursor.execute('''SELECT * FROM list WHERE url = ?''', (list,))
        exists_item_list = cursor.fetchone()
        if exists_item_list[2] == owner:
            cursor.execute('''UPDATE list SET deleted = ? WHERE url = ?''', (True, list,))
            connection.commit()
            return True
        return None
    except:
        return False
    
    
def delete_list_no_owner(connection, cursor, list):
    try:    
        cursor.execute('''SELECT * FROM list WHERE url = ?''', (list,))
        exists_item_list = cursor.fetchone()
        if exists_item_list is not None:
            cursor.execute('''UPDATE list SET deleted = ? WHERE url = ?''', (True, list,))
            connection.commit()
            return True
        return None
    except:
        return False
    