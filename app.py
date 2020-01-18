from flask import Flask, request
from bs4 import BeautifulSoup
from flask_cors import CORS
from datetime import date

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
def add_entry_for_user(uuid):

    # get url 
    # get title
    # get keywords & descriptions if they exist
    data = request.get_json()

    url = data['url']
    tags = data['tags']
    notes = data['notes']

    response = {
        'uuid': uuid,
        'url': url,
        'tags': tags,
        'notes': notes,
        'title': '',
        'keywords': '',
        'description': '',
        'add-date': date.today(),
    }

    response = requests.get(url)
    soup = BeautifulSoup(response.text)

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

    # return 'success + {uuid}'

    return response

    # add to SQL schema


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)