import sqlite3, os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zdatabase.db")

def create_connection(path):
    conn = None
    try:
        conn = sqlite3.connect(path)
    except sqlite3.Error as e:
        print(e)
    return conn

def close_connection(conn):
    if conn:
        conn.close()

def query_database(query):
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()

    conn.commit()
    conn.close()

    return result

# CREATED MANUALLY
def create_db():
    print(f"Creating table at: {DATABASE_PATH}")

    query_database(
    """ 
    CREATE TABLE IF NOT EXISTS User (
        ID INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        sessionid TEXT
    )
    """
    )

    query_database(
    """
    CREATE TABLE IF NOT EXISTS Notes (
        ID INTEGER PRIMARY KEY,
        owner_id INTEGER,
        title TEXT,
        content TEXT,
        is_encrypted BOOLEAN,
        FOREIGN KEY (owner_id) REFERENCES User(ID)
    )
    """
    )

    print("Database and tables have been successfully created.")


# Returns all tables from database.
def get_tables_of_db():
    data = query_database("SELECT name FROM sqlite_master WHERE type='table';")
    
    tables = [table[0] for table in data]

    return tables

# Returns attributes of an given table.
def get_attributes_of_table(table_name):
    data = query_database(f"PRAGMA table_info({table_name});")

    attributes = [attribute[1] for attribute in data]

    return attributes

# Selects all data from table. 
def get_data_of_table(table_name):
    data = query_database(f"SELECT * FROM {table_name};")
    data_list = [dict(row) for row in data]

    return data_list


if __name__ == "__main__":
    create_db()

