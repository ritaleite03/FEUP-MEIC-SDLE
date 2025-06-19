import sqlite3
import time
import uuid
import myCRDT

def connect_db(path):
    connection = sqlite3.connect(path, check_same_thread=False)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
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


def get_lists(cursor):
    cursor.execute('''SELECT * FROM list''')
    lists = cursor.fetchall()
    return lists


def get_lists_not_deleted_url(cursor):
    cursor.execute('''SELECT url FROM list WHERE deleted = ?''', (False,))
    rows = cursor.fetchall()
    urls = [row[0] for row in rows]
    return urls


def get_lists_not_deleted(cursor):
    cursor.execute('''SELECT * FROM list WHERE deleted = ?''', (False,))
    lists = cursor.fetchall()
    return lists


def get_url_list(cursor, url):
    try:
        cursor.execute('''SELECT url FROM list WHERE url = ?''', (url,))
        exists = cursor.fetchone()
        if exists is [] or exists is None: return None
        return exists[0]
    except: 
        return None
    

def get_owner_list(cursor, url):
    try:
        cursor.execute('''SELECT owner FROM list WHERE url = ?''', (url,))
        exists = cursor.fetchone()
        if exists is [] or exists is None: return None
        return exists[0]
    except: 
        return None

 
def get_crdt_list(cursor, url):
    try:
        cursor.execute('''SELECT crdt FROM list WHERE url = ?''', (url,))
        exists = cursor.fetchone()
        if exists is [] or exists is None: return None
        return exists[0]
    except: 
        return None


def add_list(connection, cursor, client):
    try:
        url = str(uuid.uuid4())
        crdt = str(myCRDT.AWMap(client).to_dict())
        cursor.execute('''INSERT INTO list (url, owner, crdt, deleted) VALUES (?, ?, ?, ?)''', (url, client, crdt,False,))
        connection.commit()
        return url
    except Exception as e:
        return None


def delete_list(connection, cursor, list, owner):
    try:    
        cursor.execute('''SELECT owner FROM list WHERE url = ?''', (list,))
        exists = cursor.fetchone()
        if exists[0] == owner:
            cursor.execute('''UPDATE list SET deleted = ? WHERE url = ?''', (True, list,))
            connection.commit()
            return True
        return None
    except:
        return False


def update_list(connection, cursor, url, crdt, owner=None, deleted=False):
    try:
        cursor.execute('''SELECT url FROM list WHERE url = ?''', (url,))
        exists = cursor.fetchone()
        if exists is [] or exists is None:
            cursor.execute('''INSERT INTO list (url, crdt, owner) VALUES (?, ?, ?)''', (url, crdt, owner,))
            connection.commit()
        else:
            cursor.execute('''UPDATE list SET crdt = ? , deleted = ? WHERE url = ?''', (crdt, deleted, url,)) 
            connection.commit()            
        return True
    except Exception as e:
        return False