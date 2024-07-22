from interfaces.backendinterface import IBackendProvider
import requests

class TeslamateBackendProvider(IBackendProvider):
    def refresh_data(self):

        data = requests.get(f"{self.base_url}/api/v1/cars/{self.car_id}/status").json()["data"]["status"]

        self.latitude = data["car_geodata"]["latitude"]
        self.longitude = data["car_geodata"]["longitude"]
        self.odometer = data["odometer"]
        self.is_driving = data["driving_details"]["shift_state"] is not "P"
        self.is_charging  = data["charging_details"]["time_to_full_charge"] > 0
        self.battery_level = data["battery_details"]["battery_level"]


        self.active_route_latitude = data["driving_details"]["active_route"]["location"]["latitude"]
        self.active_route_longitude = data["driving_details"]["active_route"]["location"]["longitude"]

        self.active_route_destination = data["driving_details"]["active_route"]["destination"]
        self.active_route_minutes_to_arrival = data["driving_details"]["active_route"]["minutes_to_arrival"]
        self.active_route_energy_at_arrival = data["driving_details"]["active_route"]["energy_at_arrival"]