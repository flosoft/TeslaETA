from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv
import sqlite3
import time
import shortuuid
from datetime import datetime

load_dotenv()
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
TESLALOGGER_BASEURL = os.getenv('TESLALOGGER_BASEURL')
app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Tesla ETA'

@app.route('/map/<shortuuid>')
def map(shortuuid):
    conn = sqlite3.connect('service.db')
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
            teslalogger = requests.get(TESLALOGGER_BASEURL + 'currentjson/1/')
            return render_template('map-lite.html',
                                   mbtoken=MAPBOX_TOKEN,
                                   start=[teslalogger.json()['longitude'],
                                          teslalogger.json()['latitude']],
                                   end=[lng, lat])
        else:
            return('Link Expired')
    else:
        return('Link Invalid')




@app.route('/carstate')
def carstate():  # put application's code here
    r = requests.get('http://10.0.0.2:5010/currentjson/1/')
    return r.json()


@app.route('/map/admin', methods = ['POST', 'GET'])
def map_admin():
    if request.method == 'POST':
        # GENERATE SHORTUUID:
        uuid = shortuuid.uuid()

        data = request.form
        print(data)
        expiry_epoch = datetime.strptime(data['expiry'], '%Y-%m-%dT%H:%M').timestamp()


        conn = sqlite3.connect('service.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO shares VALUES (?, ?, ?, ?)', [uuid, data['lat'], data['lng'], expiry_epoch])
        cursor.close()
        conn.commit()
        conn.close()


        return('Link created - UUID: ' + uuid)
    else:
        conn = sqlite3.connect('service.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT shortuuid, lat, lng, expiry FROM shares WHERE expiry > ?', [time.time()])
        result = result.fetchall()
        cursor.close()
        conn.close()

        for row in result:
            print(datetime.fromtimestamp(row[3]))

        print(result)

        return render_template('map_admin.html', result=result)

@app.template_filter('fromtimestamp')
def _jinja2_filter_datetime(date, fmt=None):
    timestamp = datetime.fromtimestamp(date)
    return timestamp

if __name__ == '__main__':
    app.run()
