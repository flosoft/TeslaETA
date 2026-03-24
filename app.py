from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests, os, time, shortuuid, flask_login, dotenv, bcrypt
import json
import dataclasses
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from datetime import datetime
from geopy.distance import geodesic
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from apiflask import HTTPError

from dtos.state_dto import StateDTO
from dtos.user_dto import UserDTO
from dtos.share_dto import ShareDTO

# Important to have before "from helpers import init"
dotenv.load_dotenv(".env")

from interfaces.backendfactory import BackendProviderFactory

from helpers import init_helper, share_helper
from config import app, db

# Import models for automated database migration
from models.share import Share
from models.user import User


MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
BASE_URL = os.getenv('BASE_URL')
PORT = os.getenv('PORT', 5051)
DATA_DIR = os.path.abspath(os.getenv('DATA_DIR', '/data/'))

BACKEND_PROVIDER = os.getenv('BACKEND_PROVIDER', 'teslalogger')
BACKEND_PROVIDER_HOSTNAME = os.getenv('BACKEND_PROVIDER_HOSTNAME')
BACKEND_PROVIDER_CAR_ID = os.getenv('BACKEND_PROVIDER_CAR_ID', 1)
BACKEND_PROVIDER_MULTICAR = os.getenv('BACKEND_PROVIDER_MULTICAR', False)

JWT_SECRET = os.getenv('JWT_SECRET')

# Backend provider instanciation
BackendProviderFactory(BACKEND_PROVIDER, BACKEND_PROVIDER_HOSTNAME, BACKEND_PROVIDER_CAR_ID)

## Init JWT capabilities
app.config["JWT_SECRET_KEY"] = JWT_SECRET
jwt = JWTManager(app)
sock = Sock(app)

app.secret_key = os.getenv('SECRET_KEY')

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


@app.post("/api/auth/token")
@app.input(UserDTO.Schema, arg_name='request_user')
def get_token(request_user):
    user = db.session.query(User).where(User.username == request_user.username).first()
    
    if not user:
        raise HTTPError(403, "Invalid authentication.")
    
    is_password_correct = bcrypt.checkpw(request_user.password.encode('utf-8'), user.password)
    
    if not is_password_correct:
        raise HTTPError(403, "Invalid authentication.")
    
    access_token = create_access_token(identity=user.username)
    return {"token": access_token}

temp_latitude = 0
temp_longitude = 0

@app.get("/api/state/<shortuuid>")
@app.output(StateDTO.Schema)
def get_car_state(shortuuid):
    share_helper.is_share_valid(shortuuid)
    
    provider = BackendProviderFactory.get_instance()
    provider.refresh_data()
    
    
    # global temp_latitude
    # global temp_longitude
    
    # if temp_latitude == 0:
    #     provider.refresh_data()
    #     temp_latitude = provider.state.latitude 
    #     temp_longitude = provider.state.longitude
    
    # temp_latitude += 0.001
    # temp_longitude += 0.001

    # # Temporary fake data
    # provider.state.active_route_destination = "Hello"
    # provider.state.active_route_longitude = 6.617034
    # provider.state.active_route_latitude = 46.555974
    # provider.state.latitude = temp_latitude
    # provider.state.longitude = temp_longitude
    
    return provider.state

@app.get("/api/share")
@jwt_required()
def get_shares():
    shares = db.session.query(Share).where(Share.expiry > time.time()).all()
    
    return shares

@app.post("/api/share")
@app.input(ShareDTO.Schema, arg_name="share_dto")
@app.output(ShareDTO.Schema, status_code=200)
@jwt_required()
def add_share(share_dto: ShareDTO):
    uuid = shortuuid.uuid()
    
    if share_dto.expiry < time.time():
        raise HTTPError(400, "The expiry date cannot be less than the current time.")
    
    share = Share(shortuuid=uuid, lat=share_dto.lat, lng=share_dto.lng, expiry=share_dto.expiry, carid=share_dto.carid)
    db.session.add(share)
    db.session.commit()
    
    share_dto.uuid = uuid
    return share_dto

@app.delete("/api/share/<shortuuid>")
@jwt_required()
def delete_share(shortuuid: str):
    share = share_helper.is_share_valid(shortuuid)
    
    db.session.delete(share)
    db.session.commit()
    
    return {"status": "success"}

@app.get("/api/test")
@jwt_required()
def test():
    return "OK"


@sock.route('/ws/<share_uuid>')
def ws_car_state(ws, share_uuid):
    # 1. Validate share
    share = share_helper.is_share_valid(share_uuid)
    if not share:
        return

    # 3. Get provider and determine mode
    provider = BackendProviderFactory.get_instance()

    from backendproviders.teslamate_mqtt import TeslamateMQTTBackendProvider

    if isinstance(provider, TeslamateMQTTBackendProvider):
        # MQTT push mode: wait on condition variable for state updates
        condition = provider._condition
        # Send current state immediately if available
        if provider.state.latitude is not None:
            try:
                ws.send(json.dumps(dataclasses.asdict(provider.state)))
            except ConnectionClosed:
                return

        while True:
            with condition:
                condition.wait(timeout=30)
            try:
                ws.send(json.dumps(dataclasses.asdict(provider.state)))
            except ConnectionClosed:
                break
    else:
        # Fallback poll mode: poll every 1s and push
        while True:
            try:
                provider.refresh_data()
                ws.send(json.dumps(dataclasses.asdict(provider.state)))
            except ConnectionClosed:
                break
            time.sleep(1)


if __name__ == '__main__':
    init_helper.provision_admin_user()
    app.run(host='0.0.0.0', port=PORT)
