# About
A small Flask Service allowing you to share your ETA on a map based on your [TeslaLogger](https://github.com/bassmaster187/TeslaLogger/) location.

## Note

This is a very rough project at the moment. You should definitely run it behind a reverse proxy like Traefik to ensure you password protect the admin page as otherwise someone could easily create a link and track your car's location.

## Current Features

- Map view with routing based on MapBox.
- Ability to create expiring links via a webpage

# Create DB
Create a SQLite DB called service.db and run `service_db_creation.sql`.

Alternatively, you can copy over the empty database (`service.db.empty`)

# Running the service

Simply run `app.py` while ensuring you have installed all requirements from `requirements.txt`. A virtualenv is recommended.

