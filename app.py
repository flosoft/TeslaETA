from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv
import sqlite3
import time
import shortuuid
from datetime import datetime
import flask_login
from geopy.distance import geodesic
from flask_migrate import Migrate
from models.database import db
import flask_sqlalchemy

from interfaces.backendfactory import BackendProviderFactory

# Import models for automated database migration
from models.share import Share

load_dotenv()
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
BASE_URL = os.getenv('BASE_URL')
PORT = os.getenv('PORT', 5051)
DATA_DIR = os.path.abspath(os.getenv('DATA_DIR', '/data/'))

BACKEND_PROVIDER = os.getenv('BACKEND_PROVIDER', 'teslalogger')
BACKEND_PROVIDER_BASE_URL = os.getenv('BACKEND_PROVIDER_BASE_URL')
BACKEND_PROVIDER_CAR_ID = os.getenv('BACKEND_PROVIDER_CAR_ID', 1)
BACKEND_PROVIDER_MULTICAR = os.getenv('BACKEND_PROVIDER_MULTICAR', False)

# Backend provider instanciation
BackendProviderFactory(BACKEND_PROVIDER, BACKEND_PROVIDER_BASE_URL, BACKEND_PROVIDER_CAR_ID)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATA_DIR}/service.db"
# Use the global db object
db.init_app(app)
migrate = Migrate(app,db)

with app.app_context():
    db.create_all()

# Fix static folder BASE_URL
app.view_functions["static"] = None
a_new_static_path = BASE_URL + '/static'

# Set the static_url_path property.
app.static_url_path = a_new_static_path

# Remove the old rule from Map._rules.
for rule in app.url_map.iter_rules('static'):
    app.url_map._rules.remove(rule)  # There is probably only one.

# Remove the old rule from Map._rules_by_endpoint. In this case we can just 
# start fresh.
app.url_map._rules_by_endpoint['static'] = []  

# Add the updated rule.
app.add_url_rule(f'{a_new_static_path}/<path:filename>',
                 endpoint='static',
                 view_func=app.send_static_file)


# Login Code
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# User Mapping here
users = {'admin': {'password': os.getenv('ADMIN_PASSWORD', 'password')}}

# Initiate singleton
BackendProviderFactory(BACKEND_PROVIDER, BACKEND_PROVIDER_BASE_URL, BACKEND_PROVIDER_CAR_ID)


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
        return render_template('login.html.j2')
    else:
        email = request.form['email']
        if email in users and request.form['password'] == users[email]['password']:
            if 'remember-me' in request.form:
                remember_me = True
            else:
                remember_me = False
            user = User()
            user.id = email
            flask_login.login_user(user, remember=remember_me)
            return redirect(url_for('map_admin'))
        else:
            return render_template('login.html.j2', success=False)


@app.route(BASE_URL + '/logout')
def logout():
    flask_login.logout_user()
    return render_template('login.html.j2', logout=True)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


@app.route(BASE_URL + '/')
def homepage():
    return render_template('index.html.j2')

@app.route(BASE_URL + '/<shortuuid>')
def map(shortuuid):
    result = db.session.query(Share).where(Share.shortuuid == shortuuid).first()

    if result:
        if result.expiry > time.time():
            teslalogger = carstate(shortuuid)
            return render_template('map.html.j2',
                                   mbtoken=MAPBOX_TOKEN,
                                   eta_data=teslalogger,
                                   shortuuid=shortuuid,
                                   BASE_URL=BASE_URL)
        else:
            return('Link Expired')
    else:
        return('Link Invalid')

@app.route(BASE_URL + '/carstate/<shortuuid>')
def carstate(shortuuid):
    result = db.session.query(Share).where(Share.shortuuid == shortuuid).first()

    if result:
        if result.expiry > time.time():
            # Update Attribute for car_id if in DB result else use ENV variable - only if MultiCar is enabled
            if BACKEND_PROVIDER_MULTICAR == 'True':
                if result.carid:
                    new_car_id = result.carid
                else:
                    new_car_id = BACKEND_PROVIDER_CAR_ID
            BackendProviderFactory.provider.car_id = new_car_id

            provider = BackendProviderFactory.get_instance()
            provider.refresh_data()

            temp_carstate = vars(provider)

            # Check if ETA destination is similar and use Tesla provided destination if it's within 250m
            # destination_db = (lat, lng)
            if provider.active_route_destination:
                if not result.lat or not result.lng:
                    # If the lat/lon for the destination was not set on the shared link stored in DB, use the destination set in Tesla
                    temp_carstate['eta_destination_lat'] = provider.active_route_latitude
                    temp_carstate['eta_destination_lng'] = provider.active_route_longitude
                    temp_carstate['eta_destination_tesla_seconds'] = provider.active_route_seconds_to_arrival
                    temp_carstate['eta_destination_tesla_battery_level'] = provider.active_route_energy_at_arrival
                else:
                    temp_carstate['eta_destination_lat'] = result.lat
                    temp_carstate['eta_destination_lng'] = result.lng
                    temp_carstate['eta_waypoint_lat'] = provider.active_route_latitude
                    temp_carstate['eta_waypoint_lng'] = provider.active_route_longitude

            else:
                temp_carstate['eta_destination_lat'] = result.lat
                temp_carstate['eta_destination_lng'] = result.lng
            
            return temp_carstate
        else:
            return('Link Expired'), 410
    else:
        return('Link Invalid'), 404


@app.route(BASE_URL + '/admin', methods = ['POST', 'GET'])
@flask_login.login_required
def map_admin():
    if request.method == 'POST':
        # GENERATE SHORTUUID:
        uuid = shortuuid.uuid()

        data = request.form
        lat = data['lat']
        lng = data['lng']

        lat_to_insert = float(lat) if lat else None
        lng_to_insert = float(lng) if lng else None
        expiry_epoch = datetime.strptime(data['expiry'], '%Y-%m-%dT%H:%M').timestamp()

        new_share = Share(shortuuid=uuid, lat=lat_to_insert , lng=lng_to_insert, expiry=expiry_epoch)
        db.session.add(new_share)
        db.session.commit()

    result = db.session.query(Share).where(Share.expiry > time.time()).all()
    
    # Update Attribute for car_id if in DB result else use ENV variable
    if BACKEND_PROVIDER_MULTICAR == 'True':
        if request.args.get('carid'):
            new_car_id = request.args.get('carid')
        else:
            new_car_id = BACKEND_PROVIDER_CAR_ID
        BackendProviderFactory.provider.car_id = new_car_id
    else:
        new_car_id = BACKEND_PROVIDER_CAR_ID

    provider = BackendProviderFactory.get_instance()
    provider.refresh_data()

    if 'uuid' in locals():
        return render_template('map_admin.html.j2', result=result, BASE_URL=BASE_URL, uuid=uuid, mbtoken=MAPBOX_TOKEN, car_location=[provider.longitude, provider.latitude], multicar=BACKEND_PROVIDER_MULTICAR, carid=new_car_id)
    else:
        return render_template('map_admin.html.j2', result=result, BASE_URL=BASE_URL, mbtoken=MAPBOX_TOKEN, car_location=[provider.longitude, provider.latitude], multicar=BACKEND_PROVIDER_MULTICAR, carid=new_car_id)

@app.template_filter('fromtimestamp')
def _jinja2_filter_datetime(date, fmt=None):
    timestamp = datetime.fromtimestamp(date)
    return timestamp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
