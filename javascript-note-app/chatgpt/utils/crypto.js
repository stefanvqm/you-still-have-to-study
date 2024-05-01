const crypto = require('crypto');

// Function to derive an encryption key from the user's password
function getKeyFromPassword(password, salt) {
  const keyLength = 32;
  const iterations = 100000;
  const digest = 'sha256';
  return crypto.pbkdf2Sync(password, salt, iterations, keyLength, digest);
}

// Function to encrypt text
function encryptText(text, password) {
  const algorithm = 'aes-256-cbc';
  const salt = crypto.randomBytes(16); // Generate a new salt for each encryption
  const key = getKeyFromPassword(password, salt);

  const iv = crypto.randomBytes(16); // Generate a new IV for each encryption
  const cipher = crypto.createCipheriv(algorithm, key, iv);

  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  return {
    iv: iv.toString('hex'),
    content: encrypted,
    salt: salt.toString('hex')
  };
}

// Function to decrypt text
function decryptText(encryptedContent, password, iv, salt) {
    const algorithm = 'aes-256-cbc';
    const key = getKeyFromPassword(password, Buffer.from(salt, 'hex'));
    const decipher = crypto.createDecipheriv(algorithm, key, Buffer.from(iv, 'hex'));
  
    let decrypted = decipher.update(encryptedContent, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
  
    return decrypted;
}


module.exports = { encryptText, decryptText };
