from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

from utils import generate_session_id, decrypt_text, encrypt_text, allowed_file
from database import query_database, close_connection, create_connection

import os, json, re, glob

app = Flask(__name__)
app.secret_key = 'your_secret_key1'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = create_connection()
        
        query_database(conn, "INSERT INTO User (username, password) VALUES (?, ?)", (username, password))

        session_id = generate_session_id()
        session['session_id'] = session_id
        session['user'] = username

        query_database(conn, "UPDATE User SET sessionid = ? WHERE username = ?", (session_id , username))

        close_connection(conn)

        return redirect(url_for('index'))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = create_connection()

        user = query_database(conn, "SELECT password, id FROM User WHERE username = ?", (username))
        print(user)
        if user and user[0][0] == password:
            # Correct password, log the user in
            session_id = generate_session_id()
            session['session_id'] = session_id
            session['user'] = username
            session['user_id'] = user[0][1]

            # Update session ID in the database
            query_database(conn, "UPDATE User SET sessionid = ? WHERE username = ?", (session_id , username))

            close_connection(conn)

            return redirect(url_for('index'))
        else:
            # Wrong credentials
            close_connection(conn)
            return "Invalid username or password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Remove user information from the session
    session.pop('user', None)
    session.pop('session_id', None)
    return redirect(url_for('login'))


@app.route("/", methods=["GET", "POST"])
def index():
    if 'user' in session:
        conn = create_connection()

        if request.method == "POST":
            title = request.form["title"]
            content = request.form["content"]

            # Check if title and content are not empty
            if title.strip() and content.strip():
                owner_id = query_database(conn, "SELECT ID FROM User WHERE username = ?", (session['user'],))[0][0]
                query_database(conn, "INSERT INTO Notes (owner_id, title, content, is_encrypted) VALUES (?, ?, ?, ?)", (owner_id, title, content, False))
            else:
                # Handle the case where title or content is empty
                # For instance, you can flash a message to the user
                pass

        user_id = query_database(conn, "SELECT ID FROM User WHERE username = ?", (session['user']))[0][0]
        user_notes = query_database(conn, "SELECT ID, title, content, is_encrypted FROM Notes WHERE owner_id = ?", (user_id))

        close_connection(conn)

        return render_template("index.html", notes=user_notes)
    else:
        return redirect(url_for('login'))


@app.route("/delete_note/<note_id>", methods=["POST"])
def delete_note(note_id):
    if 'user' in session:
        conn = create_connection()

        # Fetch the title of the note to be deleted
        note = query_database(conn, "SELECT title FROM Notes WHERE ID = ?", (note_id))

        if note:
            title = note[0][0]
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

            # Delete the note from the database
            query_database(conn, "DELETE FROM Notes WHERE ID = ?", (note_id))

            # Define the path to the user's export folder
            user_folder = os.path.join('exports', session['user'])

            # Define the pattern for the exported file name
            file_pattern = os.path.join(user_folder, f"{session['user']}_{safe_title}_{note_id}.json")

            # Find and delete the exported file
            for file in glob.glob(file_pattern):
                os.remove(file)

            close_connection(conn)
            return redirect(url_for('index'))
        else:
            close_connection(conn)
            return "Note not found", 404
    else:
        return redirect(url_for('login'))
    

@app.route("/encrypt_note/<note_id>", methods=["POST"])
def encrypt_note(note_id):
    if 'user' in session:
        password = request.form["password"]
        conn = create_connection()

        # Verify user's password
        stored_password = query_database(conn, "SELECT password FROM User WHERE username = ?", (session['user']))[0][0]
        if stored_password == password:
            close_connection(conn)
            return "Incorrect password"

        # Retrieve the note and encrypt its content
        owner_id = query_database(conn, "SELECT ID FROM User WHERE username = ?", (session['user']))[0][0]
        note = query_database(conn, "SELECT content FROM Notes WHERE ID = ? AND owner_id = ?", (note_id, owner_id))[0]
        
        if note:
            encrypted_content = encrypt_text(note[0], password)  # Implement your encryption logic here
            query_database(conn, "UPDATE Notes SET content = ?, is_encrypted = ? WHERE ID = ?", (encrypted_content, True, note_id))
        
        close_connection(conn)
        
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))  


@app.route("/decrypt_note/<note_id>", methods=["POST"])
def decrypt_note(note_id):
    if 'user' in session:
        password = request.form["password"]
        conn = create_connection()

        # Verify user's password
        stored_password = query_database(conn, "SELECT password FROM User WHERE username = ?", (session['user']))[0][0]
        if stored_password == password:
            close_connection(conn)
            return "Incorrect password"
        
        # Retrieve the note and decrypt its content
        owner_id = query_database(conn, "SELECT ID FROM User WHERE username = ?", (session['user']))[0][0]
        note = query_database(conn, "SELECT content FROM Notes WHERE ID = ? AND owner_id = ?", (note_id, owner_id))[0]

        if note:
            decrypted_content = decrypt_text(note[0], password)  # Use your decryption function here
            query_database(conn, "UPDATE Notes SET content = ?, is_encrypted = ? WHERE ID = ?", (decrypted_content, False, note_id))

        close_connection(conn)

        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
    

@app.route("/export_note/<note_id>")
def export_note(note_id):
    if 'user' in session:
        conn = create_connection()

        owner_id = query_database(conn, "SELECT ID FROM User WHERE username = ?", (session['user']))[0][0]
        note = query_database(conn, "SELECT title, content FROM Notes WHERE ID = ? AND owner_id = ?", (note_id, owner_id))

        if note:
            title, content = note[0]
            note_data = {"title": title, "content": content}
            
            # Sanitize the title to be safe for file names
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

            # Create a subfolder for the user within the exports directory
            user_folder = os.path.join('exports', session['user'])
            os.makedirs(user_folder, exist_ok=True)

            # Define the file path including the subfolder and sanitized title
            file_path = os.path.join(user_folder, f"{session['user']}_{safe_title}_{note_id}.json")

            # Write the note data to the file
            with open(file_path, 'w') as file:
                json.dump(note_data, file)

            close_connection(conn)

            return send_file(file_path, as_attachment=True)
        else:
            close_connection(conn)
            return "Note not found", 404
    else:
        return redirect(url_for('login'))


@app.route("/share_note/<note_id>")
def share_note(note_id):
    conn = create_connection()

    # Fetch the note by its ID
    note = query_database(conn, "SELECT User.username, Notes.title, Notes.content FROM Notes JOIN User ON Notes.owner_id = User.ID WHERE Notes.ID = ?", (note_id))

    if note:
        note_details = {"owner": note[0][0], "title": note[0][1], "content": note[0][2]}
        close_connection(conn)
        return render_template("shared_note.html", note=note_details)
    else:
        close_connection(conn)
        return "Note not found", 404


@app.route('/upload_note', methods=['GET', 'POST'])
def upload_note():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Read the contents of the uploaded file
            with open(file_path, 'r') as file:
                note_data = json.load(file)

            # Save note data into the user's notes
            conn = create_connection()
            query_database(conn, "INSERT INTO Notes (owner_id, title, content, is_encrypted) VALUES (?, ?, ?, ?)", (session['user_id'], note_data['title'], note_data['content'], False))
            close_connection(conn)

            # Remove the uploaded file after processing
            os.remove(file_path)

            return redirect(url_for('index'))

    return render_template('upload_note.html')
