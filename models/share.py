
# from flask_sqlalchemy import SQLAlchemy
# import sqlalchemy.orm
from models.database import db
# import sqlalchemy

class Share(db.Model):
    shortuuid = db.Column(db.Text(22), unique=True, nullable=False, primary_key=True)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    expiry = db.Column(db.Integer, nullable=False)
    carid = db.Column(db.Integer, nullable=True)