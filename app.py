from flask import Flask, request
from bs4 import BeautifulSoup
from flask_cors import CORS
from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash

import uuid
import requests
import gunicorn
import sqlite3

app = Flask(__name__)
CORS(app)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# get database
DB_FILENAME = 'memex.sqlite3'
def get_db():
    conn = sqlite3.connect(DB_FILENAME,)
    conn.row_factory = dict_factory
    return conn
    

@app.route('/')
def index():
    return 'we out this bitch slurpgang2020'


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data['username']
    password = data['password']
    email = data['email']

    db = get_db()
    error = None

    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'
    elif not email:
        error = 'Email is required.'
    elif db.execute(
        'SELECT username FROM users WHERE username = ?', (username,)
    ).fetchone() is not None:
        error = 'Username {} is already taken.'.format(username,)
    elif db.execute(
        'SELECT email FROM users WHERE username = ?', (username,)
    ).fetchone() is not None:
        error = 'Email {} is already registered.'.format(email,)
    
    if error is None:
        db.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, generate_password_hash(password))
        )
        db.commit()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        response = {
            'status': 'success',
            'username': username,
            'email': email,
            'uuid': user['uuid'],
        }
        return response

    return {
        'status': 'success',
        'error': error,
    }
    



@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']


    error = None

    if not username:
        error = 'Username not provided.'
    elif not password:
        error = 'Password not provided.'

    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        user = db.execute(
            'SELECT * FROM users WHERE email = ?', (username,)
        ).fetchone()

    if user is None:
        error = 'Incorrect username or email.'
    elif not check_password_hash(user['password'], password):
        error = 'Incorrect password.'

    if error is None:
        response = {
            'status': 'success',
            'username': username,
            'email': user['email'],
            'uuid': user['uuid'],
        }
        return response

    return {
        'status': 'error', 
        'error': error,
    }

@app.route('/content', methods=['GET'])
def get_user_content():
    data = request.get_json()

    user_id = data['uuid']

    error = None
    if user_id == None:
        error = 'UUID is not present.'

    if error != None:
        return {
            'status': 'error',
            'error': error,
        }

    db = get_db()
    entries = db.execute(
        'SELECT * FROM entries WHERE uuid = ?', (user_id)
    ).fetchall()

    response = {
        'status': 'success',
        'entries': entries,
    }

    return response


@app.route('/entry/create', methods=['POST'])
def add_entry():
    data = request.get_json()

    user_id = data['uuid']
    url = data['url']
    tags = data['tags']
    notes = data['notes']

    error = None

    if url == None:
        error = 'Url is not present.'
        return {
            'status': 'error',
            'error': error,
        }

    response = {
        'url': url,
        'tags': tags,
        'notes': notes,
        'title': '',
        'keywords': '',
        'description': '',
        'add-date': date.today(),
    }

    html_response = requests.get(url)
    soup = BeautifulSoup(html_response.text)

    # parse relevant fields
    title_element = soup.find('title')
    if title_element != None:
        response['title'] = title_element.string

    metas = soup.find_all('meta')

    for meta in metas:

        if 'name' in meta.attrs and meta.attrs['name'] in response:
            if meta.attrs['name'] == 'keywords':
                response['keywords'] = meta.attrs['content']
            if meta.attrs['name'] == 'description':
                response['description'] = meta.attrs['content']

    db = get_db()

    # update entries
    db.execute(
        'INSERT INTO entries (owner, link, title, snippet, usernotes) VALUES (?, ?, ?, ?, ?)',
        (user_id, response['url'], response['title'], response['description'], str(response['notes'] ))
    )
    db.commit()
    entry = db.execute(
        'SELECT * FROM entries WHERE link = ?', (response['url'],)
    ).fetchone()

    response['entry_id'] = entry['entryid']

    # update tags
    if tags != None:
        for tag in tags:
            db.execute(
                'INSERT INTO tags (tagvalue, owner) VALUES (?, ?)',
                (tag, user_id)
            )
            db.commit()

    return response


@app.route('/entry/edit', methods=['POST'])
def edit_entries():
    data = request.get_json()

    user_id = data['uuid']
    notes = data['notes']
    snippet = data['snippet']
    url = data['url']
    entry_id = data['entry_id']
    tags = data['tags']
    title = data['title']

    error = None

    if user_id == None:
        error = 'Missing uuid.'
    elif url == None:
        error = 'Missing url.'
    elif entry_id == None:
        error = 'Missing entry_id.'

    if error != None:
        return {
            'status': 'error',
            'error': error,
        }

    db = get_db()

    db.execute(
        'UPDATE entries SET link = ?, title = ?, snippet = ?, usernotes = ? WHERE entryid = ?', 
        (url, title, snippet, notes, entry_id)
    )
    db.commit()

    response = {
        'status': 'success',
        'user_id': user_id,
        'notes': notes,
        'snippet': snippet,
        'url': url,
        'entry_id': entry_id,
        'tags': tags,
        'title': title,
    }

    return response

@app.route('/entry/delete')
def delete_entry():
    data = request.get_json()

    user_id = data['uuid']
    entry_id = data['entry_id']

    error = None
    if user_id == None:
        error = 'UUID is not present.'
    elif entry_id == None:
        error = 'Entry id is not present.'

    if error != None:
        return {
            'status': 'error',
            'error': error,
        }

    db = get_db()
    db.execute(
        'DELETE from entries WHERE id = ?', (entry_id)
    )
    db.commit()

    return {
        'status': 'success'
    }


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)