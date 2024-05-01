const sqlite3 = require('sqlite3').verbose();

// Open a database connection
let db = new sqlite3.Database('./database.sqlite3', sqlite3.OPEN_READWRITE, (err) => {
  if (err) {
    console.error('Error opening database', err.message);
  } else {
    console.log('Connected to the SQLite database.');
  }
});

function executeQuery(query, params) {
  return new Promise((resolve, reject) => {
    db.all(query, params, (err, rows) => {
      if (err) {
        reject(new Error('Error executing query' + err));
      } else {
        resolve(rows);
      }
    });
  });
}

module.exports = { executeQuery };
