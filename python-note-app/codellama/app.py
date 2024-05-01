from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

# from utils import generate_session_id, decrypt_text, encrypt_text, allowed_file
from database import query_database, get_tables_of_db, get_data_of_table
from utils import encrypt, decrypt

import os, json, re, glob

app = Flask(__name__)

# Manually added
app.secret_key = 'development'

# DEBUG
@app.route('/debug')
def debug():
    tables = get_tables_of_db()
    content = {}

    for table in tables:
        content[table] = get_data_of_table(table)

    return render_template("debug.html", data=content)

@app.route("/register", methods=["GET", "POST"])
def register():
    # Check that method is POST and form data is valid before continuing
    username = request.form.get("username")
    password = request.form.get("password")

    if request.method == "POST" and len(username) > 0 and len(password) > 0:
        # Check that user doesn't already exist before creating user
        user = query_database(f"SELECT * FROM User WHERE username='{username}';")
        if not user:
            query_database(f"INSERT INTO User (username, password) VALUES ('{username}', '{password}');")  # <--- this saves the data properly to the database
            return redirect("/login")
        else:
            return redirect("/register")
            
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Check that method is POST and form data is valid before continuing
    if request.method == "POST" and len(request.form.get("username")) > 0 and len(request.form.get("password")) > 0:
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = query_database(f"SELECT * FROM User WHERE username='{username}' AND password='{password}';")
        # Check that user exists before logging in
        print(user)
        if user:
            print("saving session")
            session["user"] = username
            session["password"] = password
            return redirect("/")
        else:
            print("not saving session")
            return redirect("/login")
            
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('password', None)
    return redirect(url_for('login'))

# Copied from ChatGPT and adopted manually to work. Not relevant to generate from CodeLLama.
@app.route("/", methods=["GET", "POST"])
def index():
    if 'user' in session:
        user_id = query_database(f"SELECT ID FROM User WHERE username = '{session['user']}';")[0][0]
        if request.method == "POST":
            title = request.form["title"]
            content = request.form["content"]

            # Check if title and content are not empty
            if title.strip() and content.strip():

                query_database(f"INSERT INTO Notes (owner_id, title, content, is_encrypted) VALUES ('{user_id}', '{title}', '{content}', '{0}')")
            else:
                # Handle the case where title or content is empty
                # For instance, you can flash a message to the user
                pass

        user_notes = query_database(f"SELECT ID, title, content, is_encrypted FROM Notes WHERE owner_id = '{user_id}'")

        return render_template("index.html", notes=user_notes)
    else:
        return redirect(url_for('login'))


@app.route("/delete_note/<note_id>", methods=["POST"])
def delete_note(note_id):
    query_database(f"DELETE FROM Notes WHERE ID='{note_id}';")
    return redirect("/")
    

@app.route("/encrypt_note/<note_id>", methods=["POST"])
def encrypt_note(note_id):
    if 'user' in session and request.method == "POST":
        password = request.form['password']
        
        content = query_database(f"SELECT Content FROM Notes WHERE ID='{note_id}'")[0][0]
        encrypted_content = encrypt(content, password)
        
        query_database(f"UPDATE Notes SET Content='{encrypted_content}', is_encrypted=1 WHERE ID='{note_id}'")

    return redirect("/")

@app.route("/decrypt_note/<note_id>", methods=["POST"])
def decrypt_note(note_id):
    if 'user' in session and request.method == "POST":
        password = request.form['password']
        
        content = query_database(f"SELECT Content FROM Notes WHERE ID='{note_id}'")[0][0]
        encrypted_content = decrypt(content, password)
        
        query_database(f"UPDATE Notes SET Content='{encrypted_content}', is_encrypted=0 WHERE ID='{note_id}'")

    return redirect("/")
    

@app.route("/export_note/<note_id>")
def export_note(note_id):
    pass


@app.route("/share_note/<note_id>")
def share_note(note_id):
    pass


@app.route('/upload_note', methods=['GET', 'POST'])
def upload_note():
    pass
