var express = require('express');
var { executeQuery } = require('../interact-database');

var router = express.Router();

const bcrypt = require('bcrypt');
const saltRounds = 10;

// Display the registration form
router.get('/register', function(req, res, next) {
  res.render('register', { title: 'Register' });
});

router.post('/register', async function(req, res, next) {
  const { username, password } = req.body;
  try {
    let sql = "SELECT * FROM Users WHERE username = ?";
    let user = await executeQuery(sql, [username]);
    
    if (user.length > 0) {
      return res.status(409).send('Username already exists'); // Conflict
    }
    
    const passwordHash = await bcrypt.hash(password, saltRounds);
    sql = "INSERT INTO Users (username, password_hash) VALUES (?, ?)";
    await executeQuery(sql, [username, passwordHash]);
    
    res.status(201).send('User created'); // Created
  } catch (err) {
    console.error('Error registering new user', err.message);
    next(err);
  }
});

// Display the login form
router.get('/login', function(req, res, next) {
  res.render('login', { title: 'Login' });
});

router.post('/login', async function(req, res, next) {
  const { username, password } = req.body;
  try {
    const sql = "SELECT * FROM Users WHERE username = ?";
    const users = await executeQuery(sql, [username]);
    
    if (users.length === 0) {
      return res.status(404).send('User not found'); // Not Found
    }
    
    const user = users[0];
    const passwordMatch = await bcrypt.compare(password, user.password_hash);
    
    if (!passwordMatch) {
      return res.status(401).send('Password is incorrect'); // Unauthorized
    }
    
    // Here you would create a session or token
    // For example, using express-session or jsonwebtoken
    req.session.username = username; 
    req.session.userid = user.id;

    res.status(200).redirect('/');
  } catch (err) {
    console.error('Error logging in', err.message);
    next(err);
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
