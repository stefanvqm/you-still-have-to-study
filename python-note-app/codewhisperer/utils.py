
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.padding import PKCS7

import os, base64

# Write a function that encrypts a string with a given password
def encrypt(string, password):
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    key = kdf.derive(password.encode())

    cipher = Cipher(algorithms.AES(key), modes.CBC(salt), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = PKCS7(128).padder()
    padded_data = padder.update(string.encode()) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Encode the ciphertext with Base64
    b64_encoded_ciphertext = base64.b64encode(ciphertext)
    b64_encoded_salt = base64.b64encode(salt)

    return b64_encoded_ciphertext.decode('utf-8'), b64_encoded_salt.decode('utf-8')

def decrypt(encrypted_string, salt_string, password):
    # Decode the Base64 encoded values
    ciphertext = base64.b64decode(encrypted_string)
    salt = base64.b64decode(salt_string)

    # Recreate the key from the password and salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())

    # Initialize the cipher for decryption
    cipher = Cipher(algorithms.AES(key), modes.CBC(salt), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the ciphertext
    decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Unpad the decrypted data
    unpadder = PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

    return decrypted_data.decode()


