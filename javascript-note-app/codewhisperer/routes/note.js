var express = require('express');
var router = express.Router();

const fs = require('fs');
const path = require('path');
const multer = require('multer');

var { executeQuery } = require('../interact-database');
var { encryptText, decryptText } = require('../utils/crypto')

// Multer storage configuration
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
      const username = req.session.username; // Ensure username is available in session
      const uploadsPath = path.join(__dirname, '../uploads/');
      
      // ensure directory exists
      if (!fs.existsSync(uploadsPath)) {
        fs.mkdirSync(uploadsPath);
      }
      const usersUploadPath = path.join(uploadsPath, username);
      // ensure directory exists
      if (!fs.existsSync(usersUploadPath)) {
        fs.mkdirSync(usersUploadPath);
      }
      const uploadPath = usersUploadPath;

      cb(null, uploadPath);
    },
    filename: function (req, file, cb) {
      // You can customize the filename as needed
      cb(null, file.fieldname + '-' + Date.now() + path.extname(file.originalname));
    }
  });
  
const upload = multer({ storage: storage });
const uploadMiddleware = upload.single('file');


router.post('/create_note', async function(req, res, next) {
  const { title, content } = req.body;
  // Save ownerid from session (userid), title and content
  const query = `INSERT INTO Notes (owner_id, title, content) VALUES (${req.session.userid}, '${title}', '${content}')`;
  const result = await executeQuery(query);
  // redirect to /
  res.redirect(`/`);
});

router.post('/delete_note/:noteId', async function(req, res) {
  const query = `DELETE FROM Notes WHERE id = ${req.params.noteId}`;
  const result = await executeQuery(query);
  res.redirect(`/`);
});

router.post('/encrypt/:noteId', async (req, res) => {
    const { password } = req.body;
    const query = `SELECT content FROM Notes WHERE id = ${req.params.noteId}`;
    const result = await executeQuery(query);
    const content = result[0].content;
    // encryptText returns { encryptedContent, iv, salt }
    const { encryptedContent, iv, salt } = encryptText(content, password);
    // Set is_encrypted to true
    const updateQuery = `UPDATE Notes SET is_encrypted = true, content = '${encryptedContent}', iv = '${iv}', salt = '${salt}' WHERE id = ${req.params.noteId}`;
    await executeQuery(updateQuery);
    // redirect to /
    res.redirect(`/`);
});

router.post('/decrypt/:noteId', async (req, res) => {
    const { password } = req.body;
    const query = `SELECT content, iv, salt FROM Notes WHERE id = ${req.params.noteId}`;
    const result = await executeQuery(query);
    const content = result[0].content;
    const iv = result[0].iv;
    const salt = result[0].salt;
    const decryptedContent = decryptText(content, password, iv, salt);
    const updateQuery = `UPDATE Notes SET is_encrypted = false, content = '${decryptedContent}' WHERE id = ${req.params.noteId}`;
    await executeQuery(updateQuery);
    res.redirect(`/`);
});

router.post('/export/:noteId', async (req, res) => {
    const query = `SELECT * FROM Notes WHERE id = ${req.params.noteId}`;
    const result = await executeQuery(query);

    const title = result[0].title;
    const content = result[0].content;
    const is_encrypted = result[0].is_encrypted;
    const iv = result[0].iv;
    const salt = result[0].salt;

    // Create a json file out of the note attributes and save it to /exports/username/noteid.json
    const dir = path.join(__dirname, '../exports');
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
    }
    const dir2 = path.join(dir, req.session.username);
    if (!fs.existsSync(dir2)) {
        fs.mkdirSync(dir2);
    }

    const filename = path.join(dir2, `${req.params.noteId}.json`);
    const data = { title, content, is_encrypted, iv, salt };
    fs.writeFileSync(filename, JSON.stringify(data));

    // Download file to user
    res.download(filename);
});

router.post('/upload', uploadMiddleware, async (req, res) => {
    const username = req.session.username; 
    const filePath = req.file.path; 
    
    // Read file and insert into database
    const data = JSON.parse(fs.readFileSync(filePath));
    const { title, content, is_encrypted, iv, salt } = data;
    const query = `INSERT INTO Notes (owner_id, title, content, is_encrypted, iv, salt) VALUES (${req.session.userid}, '${title}', '${content}', ${is_encrypted}, '${iv}', '${salt}')`;
    await executeQuery(query);

    // redirect to /
    res.redirect(`/`);
});

router.post('/share/:noteId', async (req, res) => {
    // create identifier for note and save this
    const query = `SELECT * FROM Notes WHERE id = ${req.params.noteId}`;
    const result = await executeQuery(query);
    const { title, content, is_encrypted, iv, salt } = result[0];
    const shareToken = encryptText(JSON.stringify({ title, content, is_encrypted, iv, salt }), 'secret').encryptedContent;
    const updateQuery = `UPDATE Notes SET share_token = '${shareToken}' WHERE id = ${req.params.noteId}`;
    await executeQuery(updateQuery);

    // redirect to /notes/share/:shareToken
    res.redirect(`/notes/share/${shareToken}`); 
});

router.get('/notes/share/:shareToken', async (req, res) => {
    const shareToken = req.params.shareToken;
    const query = `SELECT * FROM Notes WHERE share_token = '${shareToken}'`;
    const result = await executeQuery(query);
    res.render('noteView', { note: result[0] });
});


module.exports = router;
