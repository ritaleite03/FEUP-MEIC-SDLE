import uuid
import sqlite3

class ShoppingList:
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.name = name

def create_shopping_list(name, user_id):
    new_list = ShoppingList(name)

    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()

    cursor.execute('''
    INSERT INTO list (url, name, owner)
    VALUES (?, ?, ?)
    ''', (new_list.id, name, user_id))

    connection.commit()
    connection.close()
    
    return str(new_list.id)


def check_list_existence(id):
    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()

    cursor.execute('''
    SELECT *
    FROM list
    WHERE url = ?
    ''', (id,))

    list = cursor.fetchone()
    connection.close()

    if list:
        return True
    return False


def get_list_items(id):
    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()
    print(id)
    cursor.execute('''
    SELECT item.name, quantity
    FROM item
    JOIN item_list ON item.id = id_item
    JOIN list ON id_list = list.id
    WHERE url = ?
    ''', (str(id),))

    items = cursor.fetchall()
    connection.close()

    return items


def print_list_items(items):
    if items != []:
        for item in items:
            print(item[0] + " | " + str(item[1]))
    else:
        print("List is empty!")


def add_item_to_list(list_id, name, quantity):
    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()

    cursor.execute('''
    SELECT *
    FROM item
    WHERE name = ?
    ''', (name,))

    item = cursor.fetchone()

    if item is []:
        cursor.execute('''
        INSERT INTO item (name)
        VALUES (?)
        ''', (name,))
        connection.commit()

    cursor.execute('''
    SELECT id
    FROM item
    WHERE name = ?
    ''', (name,))
    item_id = cursor.fetchone()
    item_id = item_id[0]

    cursor.execute('''
    SELECT id
    FROM list
    WHERE url = ?
    ''', (str(list_id),))
    list_db_id = cursor.fetchone()
    list_db_id = list_db_id[0]

    cursor.execute('''
    INSERT INTO item_list (id_item, id_list, quantity)
    VALUES (?, ?, ?)
    ''', (item_id, list_db_id, quantity))

    connection.commit()
    connection.close()

    
def remove_item_from_list(list_id, name, to_remove):
    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()

    cursor.execute('''
    SELECT id
    FROM item
    WHERE name = ?
    ''', (name,))
    item_id = cursor.fetchone()
    item_id = item_id[0]

    cursor.execute('''
    SELECT id
    FROM list
    WHERE url = ?
    ''', (list_id,))
    list_db_id = cursor.fetchone()
    list_db_id = list_db_id[0]

    cursor.execute('''
    SELECT quantity
    FROM item_list
    JOIN list ON id_list = id
    WHERE url = ? AND id_item = ?
    ''', (list_id, item_id))
    quantity = cursor.fetchone()
    quantity = quantity[0]
    quantity -= to_remove

    cursor.execute('''
    DELETE FROM item_list
    WHERE id_item = ? AND id_list = ?
    ''', (item_id, list_db_id))
    connection.commit()

    if quantity > 0:
        cursor.execute('''
        INSERT INTO item_list (id_item, id_list, quantity)
        VALUES (?, ?, ?)
        ''', (item_id, list_db_id, quantity))
        

    connection.commit()
    connection.close()