const sqlite3 = require('sqlite3').verbose();

let db = new sqlite3.Database('./database.sqlite3', (err) => {
  if (err) {
    console.error('Error opening database', err.message);
  } else {
    console.log('Connected to the SQLite database.');
  }
});

// Create Users Table
db.run(`
  CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
  )`
);

// Create Notes Table
db.run(`
  CREATE TABLE IF NOT EXISTS Notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_encrypted BOOLEAN DEFAULT 0,
    iv TEXT DEFAULT NULL,
    salt TEXT DEFAULT NULL,
    share_token TEXT DEFAUL NULL,
    FOREIGN KEY (owner_id) REFERENCES Users(id) ON DELETE CASCADE
  )`
);

// Create a test user
db.run(`
  INSERT INTO Users (username, password)
  VALUES ('test', 'test')
`);

db.close();
