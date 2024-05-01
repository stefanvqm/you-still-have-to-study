var express = require('express');
var { executeQuery } = require('../interact-database');

var router = express.Router();


// Display the registration form
router.get('/register', function(req, res, next) {
  res.render('register', { title: 'Register' });
});

router.post('/register', async function(req, res, next) {
  const { username, password } = req.body;
  const sql = `INSERT INTO Users (username, password) VALUES ('${username}', '${password}')`;
  const result = await executeQuery(sql);
  console.log(result);
  res.redirect('/login');
});

// Display the login form
router.get('/login', function(req, res, next) {
  res.render('login', { title: 'Login' });
});

router.post('/login', async function(req, res, next) {
  const { username, password } = req.body;
  const sql = `SELECT * FROM Users WHERE username = '${username}' AND password = '${password}'`;
  const result = await executeQuery(sql);
  if (result.length > 0) {
    req.session.username = result[0].username;
    req.session.userid = result[0].id;
    res.redirect('/');
  } else {
    res.redirect('/login');
  }
});

router.get('/logout', function(req, res) {
  req.session.destroy(function(err) {
    if (err) {
      return next(err);
    } else {
      return res.redirect('/login');
    }
  });
});

module.exports = router;