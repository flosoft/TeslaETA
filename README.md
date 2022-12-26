![TeslaETA](https://github.com/flosoft/TeslaETA/blob/master/TeslaETA-map.png?raw=true)
# About
A small Flask Service allowing you to share your ETA on a map based on your [TeslaLogger](https://github.com/bassmaster187/TeslaLogger/) location.

## Note

This is a very rough project at the moment. Currently there is only one user, "admin" with the password set via .env.

## Current Features

- Map view with routing based on MapBox.
- Ability to create expiring links via a webpage
- ETA, Distance and Chargestate update based on car state every 5 seconds

# Create DB
Create a SQLite DB called service.db and run `service_db_creation.sql`.

Alternatively, you can copy over the empty database (`service.db.empty`)

# Running the service
## Docker
### docker-compose
```
version: '3'
services:
  teslaeta:
    container_name: teslaeta
    image: ghcr.io/flosoft/teslaeta:latest
    volumes:
    - ./data/:/data/
    env_file:
    - .env
    ports:
    - "5051:5051"
```
You will be able to access the Admin Interface on /admin in your serving directory to create your links to share.

A more in depth guide on how to run it behind Traefik alongside TeslaLogger, can be found [here](https://florianjensen.com/2022/08/20/sharing-your-eta-with-teslaeta/).

## Manual
Simply run `app.py` while ensuring you have installed all requirements from `requirements.txt` and the `.env` file has been configured. A virtualenv is recommended.