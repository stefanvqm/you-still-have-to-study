const sqlite3 = require('sqlite3').verbose();

// Open a database connection
let db = new sqlite3.Database('./database.sqlite3', sqlite3.OPEN_READWRITE, (err) => {
  if (err) {
    console.error('Error opening database', err.message);
  } else {
    console.log('Connected to the SQLite database.');
  }
});

/**
 * Executes an SQL query on the database and returns the results.
 * @param {string} sql - The SQL query to execute.
 * @param {Array} [params=[]] - The parameters for the SQL query.
 * @returns {Promise} A promise that resolves with the query results.
 */
function executeQuery(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) {
        console.log('Error running sql: ' + sql);
        console.log(err);
        reject(err);
      } else {
        resolve(rows);
      }
    });
  });
}

module.exports = { executeQuery };
