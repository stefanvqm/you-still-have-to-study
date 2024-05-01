var express = require('express');
var router = express.Router();

var aesjs = require('aes-js');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid')

var { executeQuery } = require('../interact-database');
var { encryptText, decryptText } = require('../utils/crypto')



router.post('/create_note', async function(req, res, next) {
    let sql = "INSERT INTO Notes (title, content, owner_id) VALUES(?,?,?)";
    let result = await executeQuery(sql, [req.body.title, req.body.content, req.session.userid]);
    if (result != undefined) {
        res.redirect('/');
    } else {
        res.send('Error creating note.');
    }
});

router.post('/delete_note/:noteId', async function(req, res, next) {
    let noteId = req.params.noteId;
    let sql = "DELETE FROM Notes WHERE id=? AND owner_id=?"
    await executeQuery(sql, [noteId, req.session.userid]);
    // Delete note from database and redirect to homepage (/)
    res.redirect('/');
});

router.post('/encrypt/:noteId', async (req, res) => {
    let sql = "SELECT content FROM Notes WHERE id=?"
    let noteContent = await executeQuery(sql, [req.params.noteId]);
    // Encrypt noteContent with aesjs library and req.body.password
    const textBytes = aesjs.utils.utf8.toBytes(noteContent[0].content);
    const password = req.body.password + "1234567890123456";
    const encoder = new TextEncoder();
    const encodedPassword = encoder.encode(password);
    const key = new Uint8Array(encodedPassword.subarray(0, 16));
    //added 1234567890123456 to req.body.password if its shorter than 16 bytes
    const aesCtr = new aesjs.ModeOfOperation.ctr(key, 256); 
    const encryptedNoteContent = aesjs.utils.hex.fromBytes(aesCtr.encrypt(textBytes));
    let sqlUpdate = "UPDATE Notes SET content=?,is_encrypted=1 WHERE id=?"
    await executeQuery(sqlUpdate, [encryptedNoteContent, req.params.noteId]);
    // Update note in database and redirect to homepage (/)
    res.redirect('/');
});

router.post('/decrypt/:noteId', async (req, res) => {
    let sql = "SELECT content FROM Notes WHERE id=?"
    let encryptedNoteContent = await executeQuery(sql, [req.params.noteId]);
    const password = req.body.password + "1234567890123456";
    const encoder = new TextEncoder();
    const encodedPassword = encoder.encode(password);
    const key = new Uint8Array(encodedPassword.subarray(0, 16));
    const aesCtr = new aesjs.ModeOfOperation.ctr(key, 256);
    const encryptedBytes = aesjs.utils.hex.toBytes(encryptedNoteContent[0].content);
    const decryptedBytes = aesCtr.decrypt(encryptedBytes);
    const decryptedNoteContent = aesjs.utils.utf8.fromBytes(decryptedBytes);
    // Update note in database with decrypted content
    let sqlUpdate = "UPDATE Notes SET content=?, is_encrypted=0 WHERE id=?";
    await executeQuery(sqlUpdate, [decryptedNoteContent, req.params.noteId]);
    // Redirect to homepage
    res.redirect('/');
});

router.post('/export/:noteId', async (req, res) => {  
    let sql = "SELECT * FROM Notes WHERE id=?"
    let noteContent = await executeQuery(sql, [req.params.noteId]); // select all attributes from a given note
    const jsonObject = JSON.stringify(noteContent[0]) // create a json object out of the selected attributes
    res.setHeader('Content-disposition', 'attachment; filename=notedownload.json') // set response header to attachment and specify filename
    const exportPath = path.join(__dirname, `../exports/${req.session.username}/${req.params.noteId}.json`);
    var dirname = path.dirname(exportPath);
    if (!fs.existsSync(dirname)) {
        fs.mkdirSync(dirname);
    }
    fs.writeFileSync(exportPath, jsonObject) // write the exported file into exports folder with a name composed by username and note id
    res.send(jsonObject) // send the json object in the response body
});

router.post('/upload', async (req, res) => {  
    res.send("CodeLLama is not able to code this. We want to test this to see if any file can be uploaded. This critical part would have to be coded by human.")
});

router.post('/share/:noteId', async (req, res) => {  
    let sql = "UPDATE Notes SET share_token=? WHERE id=?" // update the note with a unique share token and mark it as public
    const shareToken = uuidv4(); // generate a new unique share token using the uuid library
    await executeQuery(sql, [shareToken, req.params.noteId]);
    res.redirect(`/notes/share/${shareToken}`); // redirect to /notes/share/<share_token>
});

router.get('/notes/share/:shareToken', async (req, res) => {
    const shareToken = req.params.shareToken;

    const selectSql = "SELECT * FROM Notes WHERE share_token = ?";
    const note = await executeQuery(selectSql, [shareToken]);

    if (note.length > 0) {
        res.render('noteView', { note: note[0] });
    } else {
        req.session.message = { type: 'success', text: `Share token unknown: ${shareToken}` };
        res.redirect("/");
    }
});


module.exports = router;
