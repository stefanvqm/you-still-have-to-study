var express = require('express');
var router = express.Router();

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const multer = require('multer');

var { executeQuery } = require('../interact-database');
var { encryptText, decryptText } = require('../utils/crypto')


// Multer storage configuration
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const username = req.session.username; // Ensure username is available in session
    const uploadPath = path.join(__dirname, `../uploads/${username}`);
    ensureDirectoryExistence(uploadPath);
    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    // You can customize the filename as needed
    cb(null, file.fieldname + '-' + Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });
const uploadMiddleware = upload.single('file');

// Middleware to check if user is logged in
function checkAuthenticated(req, res, next) {
  if (req.session && req.session.userid) {
    next();
  } else {
    res.status(403).send("Unauthorized");
  }
}

// Function to ensure the directory exists
function ensureDirectoryExistence(filePath) {
  var dirname = path.dirname(filePath);
  if (fs.existsSync(dirname)) {
    return true;
  }
  ensureDirectoryExistence(dirname);
  fs.mkdirSync(dirname);
}


router.post('/create_note', async function(req, res, next) {
  // Check if the user is logged in
  if (req.session && req.session.userid) {
    const { title, content } = req.body; // Extract title and content from POST request body

    if (!title || !content) {
      return res.status(400).send("Title and content are required.");
    }

    const insertNoteSql = "INSERT INTO Notes (owner_id, title, content) VALUES (?, ?, ?)";
    try {
      // Use executeQuery to insert the new note into the database
      await executeQuery(insertNoteSql, [req.session.userid, title, content]);
      res.redirect('/'); // Redirect back to the homepage (or to another success page)
    } catch (err) {
      console.error('Error inserting note into database', err.message);
      next(err); // Pass errors to Express
    }
  } else {
    // If the user is not logged in, redirect to the login page or send an appropriate response
    res.status(403).send("You must be logged in to create a note.");
  }
});

router.post('/delete_note/:noteId', checkAuthenticated, async function(req, res) {
  const noteId = req.params.noteId;
  const userId = req.session.userid; // To ensure users can only delete their own notes

  const deleteSql = "DELETE FROM Notes WHERE id = ? AND owner_id = ?";
  try {
    await executeQuery(deleteSql, [noteId, userId]);
    res.redirect('/'); // Redirect back to the home page or a success message page
  } catch (err) {
    console.error('Error deleting note from database', err.message);
    res.status(500).send("An error occurred while deleting the note.");
  }
});

router.post('/encrypt/:noteId', checkAuthenticated, async (req, res) => {
  const noteId = req.params.noteId;
  const password = req.body.password; // Assuming the password is sent in the request body
  const userId = req.session.userid;

  // Fetch the note to encrypt
  const fetchSql = "SELECT content FROM Notes WHERE id = ? AND owner_id = ?";
  const note = await executeQuery(fetchSql, [noteId, userId]);

  if (note.length > 0) {
    // Encrypt the note content with the user's password
    const encrypted = encryptText(note[0].content, password);

    // Update the encrypted content back to the database, including the iv and salt
    const updateSql = "UPDATE Notes SET content = ?, is_encrypted = 1, iv = ?, salt = ? WHERE id = ? AND owner_id = ?";
    await executeQuery(updateSql, [encrypted.content, encrypted.iv, encrypted.salt, noteId, userId]);

    req.session.message = {
      type: 'success',
      text: 'Note encrypted successfully.'
    };
    res.redirect('/');    
  } else {
    res.render('index', {
      title: 'Error',
      message: { type: 'error', text: 'Note not found or you do not have permission to encrypt it.' }
    });
  }
});

router.post('/decrypt/:noteId', checkAuthenticated, async (req, res) => {
  const noteId = req.params.noteId;
  const userId = req.session.userid; // Assuming userId is stored in the session
  const password = req.body.password; // Assuming the password is sent in the request body

  // Fetch the encrypted note, IV, and salt from the database
  const fetchSql = "SELECT content, iv, salt FROM Notes WHERE id = ? AND owner_id = ?";
  try {
    const note = await executeQuery(fetchSql, [noteId, userId]);
    if (note.length > 0) {
      const decryptedContent = decryptText(note[0].content, password, note[0].iv, note[0].salt);

      // Update the note content back to decrypted in the database
      const updateSql = "UPDATE Notes SET content = ?, is_encrypted = 0, iv = '', salt = '' WHERE id = ? AND owner_id = ?";
      await executeQuery(updateSql, [decryptedContent, noteId, userId]);

      req.session.message = {
        type: 'success',
        text: 'Note decrypted and saved successfully.'
      };
      res.redirect('/');
    } else {
      throw new Error("Note not found or you don't have permission to decrypt it.");
    }
  } catch (err) {
    console.error('Decryption or database update error:', err.message);
    req.session.message = {
      type: 'error',
      text: err.message || "An error occurred during decryption or saving the note."
    };
    res.redirect('/');
  }
});

router.post('/export/:noteId', checkAuthenticated, async (req, res) => {
  const { noteId } = req.params;
  const username = req.session.username; // Assuming username is stored in the session

  try {
    const note = await executeQuery("SELECT * FROM Notes WHERE id = ? AND owner_id = ?", [noteId, req.session.userid]);
    if (note.length === 0) {
      throw new Error("Note not found.");
    }

    const noteContent = JSON.stringify(note[0], null, 2);
    const exportPath = path.join(__dirname, `../exports/${username}/${noteId}.json`);

    ensureDirectoryExistence(exportPath);

    fs.writeFile(exportPath, noteContent, 'utf8', (err) => {
      if (err) {
        console.error("Error saving the file:", err);
        throw err;
      }

      // Initiate the file download
      res.download(exportPath, noteId + '.json', (downloadErr) => {
        if (downloadErr) {
          console.error("Error downloading the file:", downloadErr);
          throw downloadErr;
        }
        // Consider adding cleanup logic here if you don't want to keep the file
      });
    });
  } catch (error) {
    console.error("Export error:", error);
    req.session.message = {
      type: 'error',
      text: 'Failed to export the note.' + error
    };
    res.redirect('/');
  }
});

router.post('/upload', uploadMiddleware, async (req, res) => {
  if (!req.file) {
    req.session.message = {
      type: 'error',
      text: 'No file uploaded.'
    };
    return res.redirect('/');
  }

  const username = req.session.username; // Assuming this is correctly set in the session
  const filePath = req.file.path; // The path where the file is saved

  // Read the file content from disk
  fs.readFile(filePath, 'utf-8', async (err, fileContent) => {
    if (err) {
      console.error("Error reading the file:", err);
      req.session.message = {
        type: 'error',
        text: 'Failed to read the uploaded file.'
      };
      return res.redirect('/');
    }

    let noteDetails;
    try {
      noteDetails = JSON.parse(fileContent); // Now correctly parsing the file content read from disk
    } catch (error) {
      req.session.message = {
        type: 'error',
        text: 'Invalid file format.'
      };
      return res.redirect('/');
    }

    // Insert note content and other details into the database
    try {
      const ownerIdQuery = "SELECT id FROM Users WHERE username = ?";
      const owner = await executeQuery(ownerIdQuery, [username]);
      if (owner.length === 0) {
        throw new Error('User not found.');
      }
      const owner_id = owner[0].id;

      const insertSql = "INSERT INTO Notes (owner_id, title, content, is_encrypted, iv, salt) VALUES (?, ?, ?, ?, ?, ?)";
      await executeQuery(insertSql, [
        owner_id,
        noteDetails.title,
        noteDetails.content,
        noteDetails.is_encrypted ? 1 : 0,
        noteDetails.iv || '',
        noteDetails.salt || '',
      ]);

      req.session.message = {
        type: 'success',
        text: 'File content uploaded successfully as a note and saved to server.'
      };
    } catch (error) {
      console.error("Error handling file upload:", error);
      req.session.message = {
        type: 'error',
        text: error.message || 'Failed to upload the file content to the database.'
      };
    }
    res.redirect('/');
  });
});

router.post('/share/:noteId', checkAuthenticated, async (req, res) => {
  const { noteId } = req.params;
  const userId = req.session.userid;

  // Generate a unique share token for the note
  const shareToken = crypto.randomBytes(16).toString('hex');

  try {
    // Update the note with the share token
    const updateSql = "UPDATE Notes SET share_token = ? WHERE id = ? AND owner_id = ?";
    await executeQuery(updateSql, [shareToken, noteId, userId]);

    // Generate the shareable link
    const shareLink = `${req.protocol}://${req.get('host')}/notes/share/${shareToken}`;

    // Send the share link as a response or save it to the session and redirect
    req.session.message = { type: 'success', text: `Note shared successfully: ${shareLink}` };
    res.redirect('/');
  } catch (error) {
    console.error("Error sharing the note:", error);
    req.session.message = { type: 'error', text: 'Failed to share the note.' };
    res.redirect('/');
  }
});

router.get('/notes/share/:shareToken', async (req, res) => {
  const { shareToken } = req.params;

  try {
    const selectSql = "SELECT * FROM Notes WHERE share_token = ?";
    const note = await executeQuery(selectSql, [shareToken]);

    if (note.length > 0) {
      // Render the note for the user
      res.render('noteView', { note: note[0] });
    } else {
      res.status(404).send("Note not found or the link is invalid.");
    }
  } catch (error) {
    console.error("Error retrieving shared note:", error);
    res.status(500).send("An error occurred while trying to display the shared note.");
  }
});


module.exports = router;
