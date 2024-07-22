from interfaces.backendinterface import IBackendProvider
import requests

class TeslaloggerBackendProvider(IBackendProvider):
    def refresh_data(self):
        data = requests.get(f"{self.base_url}/currentjson/{self.car_id}/").json()

        self.latitude = data["latitude"]
        self.longitude = data["longitude"]
        self.odometer = data["odometer"]
        self.is_driving = data["driving"]
        self.is_charging  = data["charging"]
        self.battery_level = data["battery_level"]

        self.active_route_latitude = data["active_route_latitude"]
        self.active_route_longitude = data["active_route_longitude"]

        self.active_route_destination = data["active_route_destination"]
        self.active_route_minutes_to_arrival = data["active_route_minutes_to_arrival"]
        self.active_route_energy_at_arrival = data["active_route_energy_at_arrival"]