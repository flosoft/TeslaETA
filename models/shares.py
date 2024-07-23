
from flask_sqlalchemy import SQLAlchemy
from app import db

class Shares(db.Model):
    shortuuid = db.Column(db.Text(22), unique=True, nullable=False, primary_key=True)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    expiry = db.Column(db.Integer, nullable=False)