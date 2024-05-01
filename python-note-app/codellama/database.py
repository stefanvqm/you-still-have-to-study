import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def create_connection(path=DATABASE_PATH):
    conn = None
    try:
        conn = sqlite3.connect(path)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

def close_connection(conn):
    if conn:
        conn.close()

# Returns all tables from database.
def get_tables_of_db():
    data = query_database("SELECT name FROM sqlite_master WHERE type='table';")
    
    tables = [table[0] for table in data]

    return tables

# Selects all data from table. 
def get_data_of_table(table_name):
    data = query_database(f"SELECT * FROM {table_name};")
    data_list = [dict(row) for row in data]

    return data_list

def query_database(query):
    """Connect to the database and execute a SQL query."""
    conn = create_connection()
    ## FOR DEBUG
    conn.row_factory = sqlite3.Row
    if not conn:
        raise ConnectionError("Unable to connect to database.")
    cur = conn.cursor()
    try:
        cur.execute(query)
        conn.commit()
        rows = cur.fetchall()
        return rows
    except sqlite3.OperationalError as e:
        print(e)
    finally:
        close_connection(conn)

# CREATED MANUALLY
def create_db():
    print(f"Creating table at: {DATABASE_PATH}")
    conn = create_connection(DATABASE_PATH)

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

    close_connection(conn)
    print("Database and tables have been successfully created.")


if __name__ == "__main__":
    create_db()
