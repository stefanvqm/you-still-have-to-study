var express = require('express');
var router = express.Router();

var fs = require('fs');
var path = require('path');

const multer  = require('multer');


var { executeQuery } = require('../interact-database');
var { encryptText, decryptText } = require('../utils/crypto')

function generateShareToken() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const tokenLength = 10;
    let token = '';
    for (let i = 0; i < tokenLength; i++) {
        const randomIndex = Math.floor(Math.random() * characters.length);
        token += characters.charAt(randomIndex);
    }
    return token;
}

function ensureFilePathExists(filePath) {
    var dirname = path.dirname(filePath);
    if (fs.existsSync(dirname)) {
      return true;
    }
    ensureDirectoryExistence(dirname);
    fs.mkdirSync(dirname);
}

// Multer storage configuration
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
      const username = req.session.username; // Ensure username is available in session
      const uploadPath = path.join(__dirname, `../uploads/${username}`);
      ensureFilePathExists(uploadPath);
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
    try {
        const { title, content } = req.body;
        owner_id = req.session.userid
        const query = `INSERT INTO Notes (title, content, owner_id) VALUES ('${title}', '${content}', '${owner_id}')`;
        await executeQuery(query);
        res.status(200).redirect('/')
    } catch (error) {
        res.status(500).redirect('/')
    }
});

router.post('/delete_note/:noteId', async function(req, res) {
    const noteId = req.params.noteId;
    const query = `DELETE FROM Notes WHERE id = '${noteId}'`;
    await executeQuery(query);
    res.status(200).redirect('/');
});

router.post('/encrypt/:noteId', async (req, res) => {
    try {
        const noteId = req.params.noteId;
        const password = req.body.password;

        const query = `SELECT * FROM Notes WHERE id = '${noteId}'`;
        const note = await executeQuery(query);

        if (note.length > 0) {
            const { encryptedContent, iv } = encryptText(note[0].content, password);
            const updateQuery = `UPDATE Notes SET content = '${encryptedContent}', iv = '${iv}', is_encrypted = 1 WHERE id = '${noteId}'`;
            await executeQuery(updateQuery);
            res.status(200).redirect('/');
        } else {
            res.status(404).redirect('/');
        }
    } catch (error) {
        res.status(500).redirect('/');
    }
});

router.post('/decrypt/:noteId', async (req, res) => {
    try {
        const noteId = req.params.noteId;
        const password = req.body.password;

        const query = `SELECT * FROM Notes WHERE id = '${noteId}'`;
        const note = await executeQuery(query);

        if (note.length > 0) {
            const decryptedContent = decryptText(note[0].content, password, note[0].iv);
            const updateQuery = `UPDATE Notes SET content = '${decryptedContent}', iv = '', is_encrypted = 0 WHERE id = '${noteId}'`;
            await executeQuery(updateQuery);
            res.status(200).redirect('/');
        } else {
            res.status(404).redirect('/');
        }
    } catch (error) {
        res.status(500).send('/');
    }
});

router.post('/export/:noteId', async (req, res) => {
    const noteId = req.params.noteId;
    const query = `SELECT * FROM Notes WHERE id = '${noteId}'`;
    const note = await executeQuery(query);

    if (note.length > 0) {
        const { title, content, is_encrypted, iv, salt, share_token } = note[0];
        const username = req.session.username;
        const filePath = `./exports/${username}/${noteId}.json`;

        ensureFilePathExists(filePath)

        const jsonData = JSON.stringify({ title, content, is_encrypted, iv, salt, share_token });

        // Save JSON file
        fs.writeFileSync(filePath, jsonData);

        // Download JSON file
        res.download(filePath, `${noteId}.json`);
    } else {
        res.status(404).redirect('/');
    }
});

router.post('/upload', uploadMiddleware, async (req, res) => {
    const filePath = req.file.path;

    const jsonData = fs.readFileSync(filePath, 'utf8');
    const parsedData = JSON.parse(jsonData);

    const title = parsedData.title || "";
    const content = parsedData.content || ""; 
    const is_encrypted = parsedData.is_encrypted || "";
    const iv = parsedData.iv || "";
    const salt = parsedData.salt || ""; 
    const share_token = parsedData.share_token || "";
    const ownerId = req.session.userid;

    const insertQuery = `INSERT INTO Notes (title, content, is_encrypted, iv, salt, share_token, owner_id) VALUES ('${title}', '${content}', '${is_encrypted}', '${iv}', '${salt}', '${share_token}', '${ownerId}')`;
    await executeQuery(insertQuery);
    
    res.status(200).redirect('/');
});

router.post('/share/:noteId', async (req, res) => {
    const noteId = req.params.noteId;
    const shareToken = generateShareToken(); 
    const updateQuery = `UPDATE Notes SET share_token = '${shareToken}' WHERE id = '${noteId}'`;
    await executeQuery(updateQuery);
    
    res.status(200).redirect(`/notes/share/${shareToken}`);
});

router.get('/notes/share/:shareToken', async (req, res) => {
    const { shareToken } = req.params;

    const selectSql = `SELECT * FROM Notes WHERE share_token = '${shareToken}'`;
    const note = await executeQuery(selectSql);
  
    if (note.length > 0) {
        res.render('noteView', { note: note[0] });
    } else {
        res.status(404).send("Note not found or the link is invalid.");
    }
});


module.exports = router;
