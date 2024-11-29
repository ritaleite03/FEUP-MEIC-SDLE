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


def list_items(cursor, list_url):
    cursor.execute('''SELECT id_item, quantity FROM item_list WHERE id_list = ?''', (list_url,))
    items = cursor.fetchall()
    return items


def list_add(connection, cursor, list_name):
    url = str(uuid.uuid4())
    cursor.execute('''INSERT INTO list (url, name) VALUES (?, ?)''', (url, list_name))
    connection.commit()
    return url

def list_get(connection, cursor, list_name):
    cursor.execute('''SELECT * FROM list WHERE url = ?''', (list_name,))
    exists_item = cursor.fetchone()
    if exists_item is [] or exists_item is None:
        return False, ''
    return True, list_name

def item_add(connection, cursor, list, item, quantity):
    # check if item name exists
    cursor.execute('''SELECT * FROM item WHERE name = ?''', (item,))
    exists_item = cursor.fetchone()
    if exists_item is [] or exists_item is None:
        cursor.execute('''INSERT INTO item (name) VALUES (?)''', (item,))
        connection.commit()
    # check if item and list relation exists
    cursor.execute('''SELECT quantity FROM item_list WHERE id_item = ? AND id_list = ?''', (item,list,))
    exists_item_list = cursor.fetchone()
    if exists_item_list is [] or exists_item_list is None:
        # add item to list
        cursor.execute('''INSERT INTO item_list (id_item, id_list, quantity) VALUES (?, ?, ?)''', (item, list, quantity))
        connection.commit()
    else: 
        # update item in list
        old_quantity = exists_item_list[0]
        new_quantity = old_quantity + quantity
        cursor.execute('''UPDATE item_list SET quantity = ? WHERE id_item = ? AND id_list = ?''', (new_quantity, item, list)) 
   
    
def item_delete(connection, cursor, list, item, quantity):
    # check if item and list relation exists
    cursor.execute('''SELECT quantity FROM item_list WHERE id_item = ? AND id_list = ?''', (item,list,))
    exists_item_list = cursor.fetchone()
    if not (exists_item_list is [] or exists_item_list is None):
        old_quantity = exists_item_list[0]
        new_quantity = old_quantity - quantity
        # check if new quantity is positive
        if new_quantity > 0:
            cursor.execute('''UPDATE item_list SET quantity = ? WHERE id_item = ? AND id_list = ?''', (new_quantity, item, list)) 
            connection.commit()
        # if not, delete relation
        else:
            cursor.execute('''DELETE FROM item_list WHERE id_item = ? AND id_list = ?''', (item, list))
            connection.commit()
        return True
    return False
    