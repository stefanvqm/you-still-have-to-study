import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
from os import urandom

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json'}

def generate_session_id():
    return str(uuid.uuid4())

def derive_key(password: str, salt: bytes = None) -> bytes:
    """Derive a key from the password using PBKDF2."""
    if salt is None:
        salt = urandom(16)  # Generate a new salt if not provided

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet key length
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return urlsafe_b64encode(key), salt

def encrypt_text(plain_text: str, password: str) -> str:
    key, salt = derive_key(password)
    fernet = Fernet(key)
    encrypted_text = fernet.encrypt(plain_text.encode())
    return urlsafe_b64encode(salt + encrypted_text).decode()

def decrypt_text(encrypted_data: str, password: str) -> str:
    data = urlsafe_b64decode(encrypted_data)
    salt, encrypted_text = data[:16], data[16:]  # Extract salt and encrypted text
    key, _ = derive_key(password, salt)
    fernet = Fernet(key)
    decrypted_text = fernet.decrypt(encrypted_text)
    return decrypted_text.decode()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
