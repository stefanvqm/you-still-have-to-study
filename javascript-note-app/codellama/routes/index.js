var express = require('express');
var router = express.Router();

var { executeQuery } = require('../interact-database');

/* GET home page. */
router.get('/', async function(req, res, next) {
    // Check if the user is logged in
    if (req.session && req.session.username) {
      // The user is logged in
      try {
        // Adjust the SQL to select only the notes belonging to the logged-in user
        var sql = "SELECT * FROM Notes WHERE owner_id=?";
        const result = await executeQuery(sql,[req.session.userid]);
        let notes = JSON.parse(JSON.stringify(result));
  
        // Render a page with functionality to add notes and list existing notes
        res.render('index', { 
          username: req.session.username, 
          notes: notes,
          showNotes: true
        });
      } catch (err) {
        console.error('Error fetching notes from the database', err.message);
        next(err); // Pass errors to Express
      }
    } else {
      // The user is not logged in
      res.render('index', { 
        message: "You are not logged in. Please login to view your notes.",
        showNotes: false 
      });
    }
  });

module.exports = router;
