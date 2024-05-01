var express = require('express');
var { executeQuery } = require('../interact-database');

var router = express.Router();


// Display the registration form
router.get('/register', function(req, res, next) {
  res.render('register', { title: 'Register' });
});

router.post('/register', async function (req, res, next) {
  let sql = "INSERT INTO Users (username, password) VALUES(?,?)";
  let result = await executeQuery(sql, [req.body.username, req.body.password]);
  res.redirect('/login');
});

// Display the login form
router.get('/login', function(req, res, next) {
  res.render('login', { title: 'Login' });
});

router.post('/login', async function (req, res, next) {
  let sql = "SELECT * FROM Users WHERE username=? AND password=?";
  const [result] = await executeQuery(sql, [req.body.username, req.body.password]);

  if (result != undefined) {
    req.session.userid = result.id;
    req.session.username = result.username;
    res.redirect('/');
  } else {
    // Inform user about wrong credentials
    res.render('login', { error: "Invalid username or password" });
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
