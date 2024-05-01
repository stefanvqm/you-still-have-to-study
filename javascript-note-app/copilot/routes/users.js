

var express = require('express');
var { executeQuery } = require('../interact-database');

var router = express.Router();

// Display the registration form
router.get('/register', function(req, res, next) {
  res.render('register', { title: 'Register' });
});

router.post('/register', async function(req, res, next) {
  const { username, password } = req.body;
  // Check if the username already exists in the database
  const existingUser = await executeQuery('SELECT * FROM Users WHERE username = ?', [username]);
  if (existingUser.length > 0) {
    res.render('index', { 
      message: "Username already exists",
    });
  }
  // Insert the new user into the database
  await executeQuery('INSERT INTO Users (username, password) VALUES (?, ?)', [username, password]);

  res.render('login', { 
    message: "User registered successfully",
  });
});

// Display the login form
router.get('/login', function(req, res, next) {
  res.render('login', { title: 'Login' });
});

router.post('/login', async function(req, res, next) {
  const { username, password } = req.body;
  // Check if the username and password match a user in the database
  const user = await executeQuery('SELECT * FROM Users WHERE username = ? AND password = ?', [username, password]);
  if (user.length > 0) {
    // Set the user's session
    req.session.username = user[0].username;
    req.session.userid = user[0].id;
    
    res.status(200).redirect('/');
  } else {
    res.status(200).redirect('/login');
  }
});

router.get('/logout', function(req, res) {
  req.session.destroy(); 
  res.redirect('/login');
});


module.exports = router;
