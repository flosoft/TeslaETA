# Create the database instance. Separate file to allow the import of the same "db" object
# in the models classes
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()