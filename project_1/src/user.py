import sqlite3

def create_user(name):
    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()

    cursor.execute('''
    INSERT INTO user (name)
    VALUES (?)
    ''', (name,))

    connection.commit()

    cursor.execute('''
    SELECT id
    FROM user
    WHERE name = ?
    ''', (name,))
    id = cursor.fetchone()

    connection.close()

    return str(id)


def check_user_existence(name):
    connection = sqlite3.connect('../db/database5556.db')
    cursor = connection.cursor()

    cursor.execute('''
    SELECT *
    FROM user
    WHERE name = ?
    ''', (name,))

    user = cursor.fetchone()
    connection.close()

    if user:
        return True
    return False