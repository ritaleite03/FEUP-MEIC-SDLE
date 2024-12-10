import sqlite3
import uuid


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
    cursor.execute('''SELECT item, positive, negative FROM item_list WHERE list = ?''', (list_url,))
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


def add_item(connection, cursor, list, item, value, update=True):   
    try: 
        cursor.execute('''SELECT positive FROM item_list WHERE item = ? AND list = ?''', (item,list,))
        exists_item = cursor.fetchone()
        if exists_item is [] or exists_item is None:
            cursor.execute('''INSERT INTO item_list (item, list, positive, negative) VALUES (?, ?, ?, ?)''', (item, list, value, 0,))
            connection.commit()
            return True
        if update:
            new_value = exists_item[0] + value
            cursor.execute('''UPDATE item_list SET positive = ? WHERE item = ? AND list = ?''', (new_value, item, list,)) 
            connection.commit()
        else:
            cursor.execute('''UPDATE item_list SET positive = ? WHERE item = ? AND list = ?''', (value, item, list,)) 
            connection.commit()
        return True
    except:
        return False
       
    
def del_item(connection, cursor, list, item, value, update=True):
    try:
        cursor.execute('''SELECT negative, positive FROM item_list WHERE item = ? AND list = ?''', (item,list,))
        exists_item = cursor.fetchone()        
        if exists_item is [] or exists_item is None: 
            return True        
        if update:           
            print(1)
            print(exists_item)
            old_value = exists_item[0]
            old_positive = exists_item[1]
            new_value = old_value + value
            if (old_positive - new_value) <= 0:
                new_value = old_positive
            print(new_value)
            cursor.execute('''UPDATE item_list SET negative = ? WHERE item = ? AND list = ?''', (new_value, item, list,)) 
            connection.commit()
            return True
        else:
            cursor.execute('''UPDATE item_list SET negative = ? WHERE item = ? AND list = ?''', (value, item, list,)) 
            connection.commit()
            return True
    except Exception as e:
        return False