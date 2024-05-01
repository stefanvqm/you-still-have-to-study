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
    password_hash TEXT NOT NULL
  )`, (err) => {
  if (err) {
    console.error('Error creating table', err.message);
  } else {
    console.log('Table created or already exists.');
  }
});

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
  )`, (err) => {
  if (err) {
    console.error('Error creating table', err.message);
  } else {
    console.log('Table created or already exists.');
  }
});


let insertUser = `INSERT INTO Users (username, password_hash) VALUES (?, ?)`;
db.run(insertUser, ["testuser", "hashed_password"], function(err) {
  if (err) {
    return console.log(err.message);
  }
});

db.close((err) => {
  if (err) {
    console.error('Error closing database:', err.message);
  } else {
    console.log('Database connection closed.');
  }
});
