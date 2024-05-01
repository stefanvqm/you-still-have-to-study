import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zdatabase.db")

def create_connection(path=DATABASE_PATH):
    """Create a database connection to the SQLite database specified by DATABASE_PATH."""
    conn = None
    try:
        conn = sqlite3.connect(path)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

def close_connection(conn):
    """Close the database connection."""
    if conn:
        conn.close()

def query_database(conn, query, params=()):
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    cursor.execute(query, params)
    conn.commit()
    return cursor.fetchall()

# CREATED MANUALLY
def create_db():
    print(f"Creating table at: {DATABASE_PATH}")
    conn = create_connection(DATABASE_PATH)

    query_database(conn,
    """
    CREATE TABLE IF NOT EXISTS User (
        ID INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        sessionid TEXT
    )
    """
    )

    query_database(conn,
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
