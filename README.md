![TeslaETA](https://github.com/flosoft/TeslaETA/blob/master/docs/teslaeta-header.png?raw=true)
# About
A small Flask Service allowing you to share your ETA on a map based on your [TeslaLogger](https://github.com/bassmaster187/TeslaLogger/) or [TeslaMateApi](https://github.com/tobiasehlert/teslamateapi) location.

## Note

This is a very rough project at the moment. Currently there is only one user, "admin" with the password set via .env.

## Current Features
- all mobile responsive

### Map View
- Map view with routing based on MapBox.
- Ability to create expiring links via a webpage
- ETA, Distance and Chargestate update based on car state every 5 seconds

### Admin Interface
- Viewing active links
- Ability to create new links by searching location on map or manual coordinate entry

# Screenshots
![Map UI](https://github.com/flosoft/TeslaETA/blob/master/docs/ui-map.png?raw=true)
![Admin UI](https://github.com/flosoft/TeslaETA/blob/master/docs/ui-admin.png?raw=true)


# Setup & running it
A more in depth guide on how to run it behind Traefik alongside TeslaLogger, can be found [here](https://florianjensen.com/2022/08/20/sharing-your-eta-with-teslaeta/).

## .env file
> [!WARNING]
> Please note that the .env file changed between versions 0.3.7 and 0.5.0!

Copy the `.env_sample` to `.env` and configure the variables. This file will need to be in the folder of your `docker-compose.yml` or in the folder where you will run the script in.

| Variable                  | Example                                                                                  | Required |
|---------------------------|------------------------------------------------------------------------------------------|----------|
| PORT                      | `5051`                                                                                   | Y        |
| DATA_DIR                  | `/data/`                                                                                 | Y        |
| SECRET_KEY                | `RANDOMLY_GENERATED_HERE`                                                                | Y        |
| ADMIN_PASSWORD            | `PASSWORD_FOR_ADMIN_PAGE`                                                                | Y        |
| BASE_URL                  | `/map`                                                                                   | Y        |
| MAPBOX_TOKEN              | `pk.BLA`                                                                                 | Y        |
| BACKEND_PROVIDER          | `teslalogger` OR `teslamate`                                                             | Y        |
| BACKEND_PROVIDER_BASE_URL | `http://insert-base-api-here:withport/`<br>TeslaLogger Example: `http://raspberry:5010/` | Y        |
| BACKEND_PROVIDER_CAR_ID   | `1`                                                                                      | Y        |
| BACKEND_PROVIDER_MULTICAR | `False` OR `True`                                                                        | N        |
| TZ                        | `Europe/Berlin`                                                                          | Y        |

- `ADMIN_PASSWORD` variable is the password in plaintext for the user "admin"
- `MAPBOX_TOKEN` will need to be generated [here](https://account.mapbox.com/access-tokens/). A free Mapbox account is required.

## Option 1 - Docker
### docker-compose
The following `docker-compose.yml` file will store the database in `./data/`. Make sure you created the folder or you've adjusted the file below.
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

## Option 2 - Runnig manually
You will need to install the python requirements, `pip install -r requirements.txt`
Then you can simply run `docker_init.sh`.

## Initial Login
Once the service is up and running, you'll be able to access it on `BASEURL + /admin`, for example `/map/admin`. Just log in with the username `admin` and the password which you sent in `.env`.
