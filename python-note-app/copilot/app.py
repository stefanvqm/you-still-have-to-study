from flask import Flask, request, session, redirect, url_for, render_template, flash, send_file

from base64 import urlsafe_b64encode
import os, binascii, hashlib, json

from database import query_database

# DEBUG
from database import get_data_of_table, get_tables_of_db

from cryptography.fernet import Fernet
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# DEBUG
@app.route('/debug')
def debug():
    tables = get_tables_of_db()
    content = {}

    for table in tables:
        content[table] = get_data_of_table(table)

    return render_template("debug.html", data=content)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Save the session id in the database
        query = f"INSERT INTO User (username, password) VALUES ({username}, {password})"
        query_database(query)

        return redirect(url_for('index'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        query = f"SELECT ID, password FROM User WHERE username = {username}"
        user = query_database(query)
        
        if user and user[0][1] == password:
            # Generate a new session id
            session_id = binascii.hexlify(os.urandom(12)).decode()

            # Save the session id in the user's browser
            session['session_id'] = session_id
            session['username'] = username
            session['user_id'] = user[0][0]

            # Update the session id in the database
            query = f"UPDATE User SET sessionid = {session_id} WHERE username = {username}"
            query_database(query)

            return redirect(url_for('index'))
        else:
            return redirect('/login')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove the username and session_id from the session if they are present
    session.pop('username', None)
    session.pop('session_id', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    user_id = session.get('user_id')
    
    if user_id:
        query = f"SELECT ID, title, content, is_encrypted FROM Notes WHERE owner_id = {user_id}"
        notes = query_database(query)

        return render_template('index.html', notes=notes)
    else:
        return redirect(url_for('login'))
    
@app.route('/add_note', methods=['POST'])
def add_note():
    user_id = session.get('user_id')
    if user_id:
        title = request.form.get('title')
        content = request.form.get('content')
        if not title.strip() or not content.strip():
            flash('Title and content cannot be blank', 'error')
            return redirect(url_for('index'))
        query = f"INSERT INTO Notes (owner_id, title, content) VALUES ({user_id}, {title}, {content})"
        query_database(query)
        return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))
    
@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    user_id = session.get('user_id')
    if user_id:
        query = f"SELECT * FROM Notes WHERE ID = {note_id} AND owner_id = {user_id}"
        note = query_database(query)
        if note:
            # Delete the note from the database
            query = f"DELETE FROM Notes WHERE ID = {note_id} AND owner_id = {user_id}"
            query_database(query)

            # Delete the exported file
            username = session.get('username')
            filename = f"exports/{username}/{username}_{note_id}.json"
            
            if os.path.exists(filename):
                os.remove(filename)

            return redirect(url_for('index'))
        else:
            flash('Note not found', 'error')
            return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))

@app.route('/encrypt_note/<int:note_id>', methods=['POST'])
def encrypt_note(note_id):
    user_id = session.get('user_id')
    if user_id:
        password = request.form.get('password')
        query = f"SELECT content FROM Notes WHERE ID = {note_id} AND owner_id = {user_id}"
        note = query_database(query)
        if note:
            content = note[0]['content']
            key = urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
            cipher_suite = Fernet(key)
            encrypted_content = cipher_suite.encrypt(content.encode()).decode()
            query = f"UPDATE Notes SET content = {encrypted_content}, is_encrypted = 1 WHERE ID = {note_id} AND owner_id = {user_id}"
            query_database(query)
            return redirect(url_for('index'))
        else:
            flash('Note not found', 'error')
            return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))

@app.route('/decrypt_note/<int:note_id>', methods=['POST'])
def decrypt_note(note_id):
    user_id = session.get('user_id')
    if user_id:
        password = request.form.get('password')
        query = f"SELECT content FROM Notes WHERE ID = {note_id} AND owner_id = {user_id}"
        note = query_database(query)
        if note:
            encrypted_content = note[0]['content']
            key = urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
            cipher_suite = Fernet(key)
            decrypted_content = cipher_suite.decrypt(encrypted_content.encode()).decode()
            query = f"UPDATE Notes SET content = {decrypted_content}, is_encrypted = 0 WHERE ID = {note_id} AND owner_id = {user_id}"
            query_database(query)
            return redirect(url_for('index'))
        else:
            flash('Note not found', 'error')
            return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))

@app.route('/export_note/<int:note_id>', methods=['POST'])
def export_note(note_id):
    user_id = session.get('user_id')
    if user_id:
        query = f"SELECT title, content FROM Notes WHERE ID = {note_id} AND owner_id = {user_id}"
        note = query_database(query)
        if note:
            username = session.get('username')
            filename = f"{username}_{note_id}.json"
            file_path = os.path.join("exports", username, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            print(str(note[0]))
            with open(file_path, 'w') as file:
                file.write(json.dumps({
                    'title': note[0]['title'],
                    'content': note[0]['content']
                }))
            
            return send_file(file_path, as_attachment=True)
        else:
            flash('Note not found', 'error')
            return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))
    
@app.route('/share_note/<int:note_id>', methods=['POST'])
def share_note(note_id):
    user_id = session.get('user_id')
    if user_id:
        query = f"SELECT * FROM Notes WHERE ID = {note_id} AND owner_id = {user_id}"
        note = query_database(query)
        if note:
            share_link = url_for('view_note', note_id=note_id, _external=True)
            return render_template('share.html', share_link=share_link)
        else:
            flash('Note not found', 'error')
            return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))
    
@app.route('/view_note/<int:note_id>')
def view_note(note_id):
    query = "SELECT * FROM Notes WHERE ID = {note_id}"
    note = query_database(query)
    if note:
        return render_template('view.html', note=note[0])
    else:
        return "Note not found", 404
    
@app.route('/upload_note', methods=['POST'])
def upload_note():
    user_id = session.get('user_id')
    if user_id:
        note_file = request.files['note_file']
        if note_file:
            filepath = os.path.join('uploads', note_file.filename)
            note_file.save(filepath)

            with open(filepath, 'r') as f:
                note_data = json.load(f)

            title = note_data.get('title')
            content = note_data.get('content')
            if title and content:
                query = f"INSERT INTO Notes (owner_id, title, content) VALUES ({user_id}, {title}, {content})"
                query_database(query)
                os.remove(filepath)  # delete the uploaded file after saving its content
                return redirect(url_for('index'))
            else:
                flash('Invalid note file', 'error')
                return redirect(url_for('index'))
        else:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
    else:
        flash('You are not logged in', 'error')
        return redirect(url_for('login'))
    
if __name__ == '__main__':
    app.run()
