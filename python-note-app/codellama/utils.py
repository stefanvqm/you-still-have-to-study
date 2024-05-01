from cryptography.fernet import Fernet
from hashlib import sha256
from base64 import urlsafe_b64encode, urlsafe_b64decode

def generate_key(password):
    key = sha256(password.encode()).digest()
    return key

def encrypt(content, password):
    key = generate_key(password)
    fernet = Fernet(urlsafe_b64encode(key))
    encrypted_text = fernet.encrypt(content.encode())
    return encrypted_text.decode()

def decrypt(encrypted_content, password):
    key = generate_key(password)
    fernet = Fernet(urlsafe_b64encode(key))
    decrypted_text = fernet.decrypt(encrypted_content.encode())
    return decrypted_text.decode()
