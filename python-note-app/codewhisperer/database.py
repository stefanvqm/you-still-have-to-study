# Write functions that interact with an sqlite database. 
# create_connection() should connect to the given path. 
# close_connection() should close the connection and query_database() 
# should execute the given query. 

import sqlite3
from sqlite3 import Error


# create a database connection to a SQLite database
def create_connection(path):
    connection = sqlite3.connect(path)
    return connection


# close database connection
def close_connection(connection):
    if connection:
        connection.close()

# execute a database query
def query_database(connection, query):
    ## FOR DEBUG
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        connection.commit()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")

# Write a function that executes queries by opening and closing a connection.
def execute_query(query):
    connection = create_connection("database.sqlite")
    result = query_database(connection, query)
    close_connection(connection)
    return result

# Returns all tables from database.
def get_tables_of_db():
    data = execute_query("SELECT name FROM sqlite_master WHERE type='table';")
    
    tables = [table[0] for table in data]

    return tables

# Returns attributes of an given table.
def get_attributes_of_table(table_name):
    data = execute_query(f"PRAGMA table_info({table_name});")

    attributes = [attribute[1] for attribute in data]

    return attributes

# Selects all data from table. 
def get_data_of_table(table_name):
    data = execute_query(f"SELECT * FROM {table_name};")
    data_list = [dict(row) for row in data]

    return data_list

def create_database():
    connection = create_connection("database.sqlite")

    query_database(connection, """
        CREATE TABLE IF NOT EXISTS User (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            sessionid TEXT
        );
    """)
    query_database(connection, """
        CREATE TABLE IF NOT EXISTS Notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT,
            title TEXT,
            content TEXT,
            is_encrypted BOOLEAN DEFAULT 0,
            salt TEXT,
            identifier TEXT,
            FOREIGN KEY (owner_id) REFERENCES User(username)
        );
    """)

    print("Database created successfully")

    close_connection(connection)

if __name__ == "__main__":
    create_database()
