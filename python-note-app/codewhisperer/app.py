
from flask import Flask, redirect, request, url_for, session, render_template, send_file

from database import execute_query, get_data_of_table, get_tables_of_db
from utils import encrypt, decrypt

import uuid, hashlib
import json, os

app = Flask(__name__)

# Add app secret
app.secret_key = 'secret'

# DEBUG
@app.route('/debug')
def debug():
    tables = get_tables_of_db()
    content = {}

    for table in tables:
        content[table] = get_data_of_table(table)

    return render_template("debug.html", data=content)


# Route to register
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        name = request.form['username']
        password = request.form['password']

        execute_query(f"INSERT INTO User (username, password) VALUES ('{name}', '{password}')")

        # redirect to login route
        return redirect(url_for('login'))
    else:
        # render login.html
        return render_template('register.html')

# Route to login.
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        name = request.form['username']
        password = request.form['password']

        result = execute_query(f"SELECT * FROM User WHERE username='{name}' AND password='{password}'")

        # Create and session id. Store this into the users localstorage
        session_id = uuid.uuid4().hex
        # Store the session id in the database
        execute_query(f"UPDATE User SET sessionid='{session_id}' WHERE username='{name}'")
        # Store the session id in the localstorage
        session['session_id'] = session_id
    else:
        # render login.html
        return render_template('login.html')

    return redirect(url_for('index'))

# Write an /logout route to log out the user
@app.route('/logout')
def logout():
    execute_query(f"UPDATE User SET sessionid=NULL WHERE sessionid='{session['session_id']}'")
    session.pop('session_id', None)
    return redirect(url_for('login'))

# Write /delete_note route that deletes the users note from the database
@app.route('/delete_note', methods=['POST'])
def delete_note():
    note_id = request.form['note_id']
    execute_query(f"DELETE FROM Notes WHERE id='{note_id}'")
    return redirect(url_for('index'))


@app.route('/encrypt_note', methods=['POST'])
def encrypt_note():
    # Take the post parameter named password
    password = request.form['password']
    # Take the post parameter named note_id
    note_id = request.form['note_id']
    # Query for the note in the database
    note = execute_query(f"SELECT * FROM Notes WHERE id='{note_id}'")
    # If the note exists
    if note != None:
        # Encrypt the note
        encrypted_note, salt = encrypt(note[0][2], hashlib.md5(password.encode()).hexdigest())
        # Update conent, salt and is_encrypted of note in the database
        execute_query(f"UPDATE Notes SET content='{encrypted_note}', salt='{salt}', is_encrypted=1 WHERE id='{note_id}'")

    return redirect(url_for('index'))


# Write /decrypt_note route that decrypts the users note from the database
@app.route('/decrypt_note', methods=['POST'])
def decrypt_note():
    password = request.form['password']
    note_id = request.form['note_id']
    # Query for the note, and salt in the database
    note = execute_query(f"SELECT content, salt FROM Notes WHERE id='{note_id}'")
    
    if note != None:
        decrypted_note = decrypt(note[0][0], note[0][1], hashlib.md5(password.encode()).hexdigest())
        execute_query(f"UPDATE Notes SET content='{decrypted_note}', is_encrypted=0 WHERE id='{note_id}'")

    return redirect(url_for('index'))

@app.route('/upload_note', methods=['POST', 'GET'])
def upload_note():
    if request.method == 'GET':
        return render_template('upload_note.html')
    else:
        # Take the post parameter json object uploaded by user
        note_json = request.files['file']

        # Save the data from the json object to the database
        filename = note_json.filename
        
        # Create folder if it not exists /uploads/<username>
        try:
            os.system(f"mkdir uploads/{session['user']}")
            os.system(f"mkdir uploads\{session['user']}")
        except FileExistsError:
            pass

        # Build filepath: /uploads/<username>/<filename>
        file_path = f"uploads/{session['user']}/{filename}"
        # Save file to filepath
        note_json.save(file_path)

        # Read the json object from the file
        with open(file_path, 'r') as file:
            note = json.load(file)
        
        # Save the data from the json object to the database
        user = session['user']
        title = note['title']
        content = note['content']
        is_encrypted = note['is_encrypted']
        salt = note['salt']
        identifier = note['identifier']
        execute_query(f"INSERT INTO Notes (owner_id, title, content, is_encrypted, salt, identifier) VALUES ('{user}', '{title}', '{content}', '{is_encrypted}', '{salt}', '{identifier}')")

        # Delete the file
        os.remove(file_path)
        
        return redirect(url_for('index'))

# Query for the note in the database. Create Json Object of note information.
# Save Json Object to 'exports' folder and send it to the user.
@app.route('/export_note', methods=['GET'])
def export_note():
    note_id = request.args.get('note_id')
    note = execute_query(f"SELECT * FROM Notes WHERE id='{note_id}'")
    if note != None:
        note = note[0]
        note_json = {
            "owner": note[1],
            "title": note[2],
            "content": note[3],
            "is_encrypted": note[4],
            "salt": note[5],
            "identifier": note[6]
        }
        
        # Create folder /exports/<username>
        try:
            os.system(f"mkdir exports/{session['user']}")
            os.system(f"mkdir exports\{session['user']}")
        except FileExistsError:
            pass

        # Build filepath: /exports/<username>/<note_id>.json
        file_path = f"exports/{session['user']}/{note_id}.json"

        # Write json object to file: /exports/<username>/<note_id>.json
        with open(file_path, 'w') as file:
            json.dump(note_json, file)

        # CodeWhisperer couldn't do this: Return file as attachment
        return send_file(file_path, as_attachment=True)
    else:
        return redirect(url_for('index'))


@app.route('/share_note', methods=['POST', 'GET'])
def share_note():
    if request.method == "POST":
        if request.form.get('identifier') == None:
            return redirect(url_for('index'))
        
        # Check identifier can be found in database
        result = execute_query(f"SELECT * FROM Notes WHERE identifier='{request.form['identifier']}'")
        identifier = None if result != None or len(result) == 0 else result[0]
        if identifier == None:
            # Creating an identifier for the note and store in database
            note_id = request.form['note_id']
            identifier = hashlib.md5(note_id.encode()).hexdigest()
            # Update the identifier of the note in the database
            execute_query(f"UPDATE Notes SET identifier='{identifier}' WHERE id='{note_id}'")

        return redirect(url_for('share_note', identifier=identifier))
    else:
        # Query note
        note = execute_query(f"SELECT * FROM Notes WHERE identifier='{request.args.get('identifier')}'")
        if note == None or len(note) == 0:
            return redirect(url_for('index'))
        
        return render_template('share_note.html', note=note[0])

# Route to Index. If not logged in, redirect to login route.
@app.route('/', methods=['POST', 'GET'])
def index():
    if 'session_id' not in session:
        return redirect(url_for('login'))
    
    # Load username and store in session
    result = execute_query(f"SELECT username FROM User WHERE sessionid='{session['session_id']}'")
    if len(result) != 0:
        session['user'] = result[0][0]
    else: 
        return redirect(url_for('logout'))
    
    # Save notes title and content. Only save them if they are not empty.
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']

        if title != '' and content != '':
            execute_query(f"INSERT INTO Notes (title, content, owner_id) VALUES ('{title}', '{content}', '{session['user']}')")

        return redirect(url_for('index'))
    else:
        # Query every note from user saved in db
        notes = execute_query(f"SELECT * FROM Notes WHERE owner_id='{session['user']}'")

        if notes == None:
            notes = []

        return render_template('index.html', notes=notes)

if __name__ == '__main__':
    app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
