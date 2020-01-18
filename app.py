from flask import Flask
from bs4 import BeautifulSoup
from flask_cors import CORS
import requests
import gunicorn
import sqlite3

app = Flask(__name__)
CORS(app)

# get database
DB_FILENAME = 'memex.sqlite3'
def get_db():
    conn = sqlite3.connect(DB_FILENAME)
    return conn

# get all users & associated metadata in DB
def get_users(conn):
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    rows = cur.fetchall()

    users = []
    for row in rows:
        users.append(row)

    return 
    
# get all user entries
def get_user_entries(uuid, conn):
    cur = conn.cursor()
    cur.execute('SELECT * FROM entries WHERE owner=?', (uuid,))
    rows = cur.fetchall()

    return rows

@app.route('/')
def index():
    return 'we out this bitch slurpgang2020'

@app.route('/available-endpoints')
def available_endpoints():
    return {
        'index:' '/'
    }

@app.route('/user/<uuid>')
def show_user_entries():
    return {
        'dummy': 'hello'
    }

@app.route('/user/<uuid>/add', methods=['POST'])
def add_entry_for_user():
    return 'very nice'
    # return 'success + {uuid}'

    # add to SQL schema


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)