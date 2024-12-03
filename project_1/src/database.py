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

def get_lists(cursor):
    cursor.execute('''SELECT name, url, owner FROM list''')
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

def add_item(connection, cursor, list, item, quantity):
    try:
        # check if item and list relation exists
        cursor.execute('''SELECT quantity FROM item_list WHERE item = ? AND list = ?''', (item,list,))
        exists_item_list = cursor.fetchone()
        if exists_item_list is [] or exists_item_list is None:
            # add item to list
            cursor.execute('''INSERT INTO item_list (item, list, quantity) VALUES (?, ?, ?)''', (item, list, quantity,))
            connection.commit()
        else: 
            # update item in list
            cursor.execute('''UPDATE item_list SET quantity = ? WHERE item = ? AND list = ?''', (quantity, item, list,)) 
        return True
    except:
       return False
    
def delete_item(connection, cursor, list, item, quantity):
    try:    
        # check if item and list relation exists
        cursor.execute('''SELECT quantity FROM item_list WHERE item = ? AND list = ?''', (item,list,))
        exists_item_list = cursor.fetchone()
        if not (exists_item_list is [] or exists_item_list is None):
            # check if new quantity is positive
            if quantity > 0:
                cursor.execute('''UPDATE item_list SET quantity = ? WHERE item = ? AND list = ?''', (quantity, item, list,)) 
                connection.commit()
            # if not, delete relation
            else:
                cursor.execute('''DELETE FROM item_list WHERE item = ? AND list = ?''', (item, list,))
                connection.commit()
            return True
        return False
    except:
        return False
    
def delete_list(connection, cursor, list, owner):
    try:    
        cursor.execute('''SELECT * FROM list WHERE url = ?''', (list,))
        exists_item_list = cursor.fetchone()
        if exists_item_list[2] == owner:
            cursor.execute('''DELETE FROM list WHERE url = ?''', (list,))
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
            cursor.execute('''DELETE FROM list WHERE url = ?''', (list,))
            connection.commit()
            return True
        return None
    except:
        return False
    