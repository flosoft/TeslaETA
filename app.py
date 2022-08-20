from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv
import sqlite3
import time
import shortuuid
from datetime import datetime
import flask_login

load_dotenv()
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
TESLALOGGER_BASEURL = os.getenv('TESLALOGGER_BASEURL')
TESLALOGGER_CARID = os.getenv('TESLALOGGER_CARID', 1)
BASE_URL = os.getenv('BASE_URL')
PORT = os.getenv('PORT', 5051)
DATA_DIR = os.getenv('DATA_DIR', '/data/')
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.static_url_path(BASE_URL + '/static')


# Login Code
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# User Mapping here
users = {'admin': {'password': os.getenv('ADMIN_PASSWORD', 'password')}}


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@app.route(BASE_URL + '/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='username'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    email = request.form['email']
    if email in users and request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect(url_for('map_admin'))

    return 'Bad login'


@app.route(BASE_URL + '/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


@app.route(BASE_URL + '/')
def hello_world():
    return 'Tesla ETA'

@app.route(BASE_URL + '/<shortuuid>')
def map(shortuuid):
    conn = sqlite3.connect(DATA_DIR + 'service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT lat, lng, expiry FROM shares WHERE shortuuid = ?', [shortuuid])
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    print(result)

    if result:
        lat = result[0]
        lng = result[1]
        expiry = result[2]

        print(expiry)
        print(time.time())

        if expiry > time.time():
            teslalogger = requests.get(TESLALOGGER_BASEURL + 'currentjson/' + TESLALOGGER_CARID + '/')
            return render_template('map.html',
                                   mbtoken=MAPBOX_TOKEN,
                                   start=[teslalogger.json()['longitude'],
                                          teslalogger.json()['latitude']],
                                   end=[lng, lat],
                                   odometer_start=[teslalogger.json()['odometer']],
                                   shortuuid=shortuuid,
                                   BASE_URL=BASE_URL)
        else:
            return('Link Expired')
    else:
        return('Link Invalid')




@app.route(BASE_URL + '/carstate/<shortuuid>')
def carstate(shortuuid):
    conn = sqlite3.connect(DATA_DIR + 'service.db')
    cursor = conn.cursor()
    cursor.execute('SELECT lat, lng, expiry FROM shares WHERE shortuuid = ?', [shortuuid])
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        lat = result[0]
        lng = result[1]
        expiry = result[2]

        if expiry > time.time():
            teslalogger = requests.get(TESLALOGGER_BASEURL + 'currentjson/' + TESLALOGGER_CARID + '/')
            return teslalogger.json()
        else:
            return('Link Expired')
    else:
        return('Link Invalid')


@app.route(BASE_URL + '/admin', methods = ['POST', 'GET'])
@flask_login.login_required
def map_admin():
    if request.method == 'POST':
        # GENERATE SHORTUUID:
        uuid = shortuuid.uuid()

        data = request.form
        print(data)
        expiry_epoch = datetime.strptime(data['expiry'], '%Y-%m-%dT%H:%M').timestamp()


        conn = sqlite3.connect(DATA_DIR + 'service.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO shares VALUES (?, ?, ?, ?)', [uuid, data['lat'], data['lng'], expiry_epoch])
        cursor.close()
        conn.commit()
        conn.close()


        return('Link created - UUID: ' + uuid)
    else:
        conn = sqlite3.connect(DATA_DIR + 'service.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT shortuuid, lat, lng, expiry FROM shares WHERE expiry > ?', [time.time()])
        result = result.fetchall()
        cursor.close()
        conn.close()

        for row in result:
            print(datetime.fromtimestamp(row[3]))

        print(result)

        return render_template('map_admin.html', result=result, BASE_URL=BASE_URL)

@app.template_filter('fromtimestamp')
def _jinja2_filter_datetime(date, fmt=None):
    timestamp = datetime.fromtimestamp(date)
    return timestamp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
