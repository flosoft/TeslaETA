from interfaces.backendinterface import IBackendProvider
import requests

class TeslamateBackendProvider(IBackendProvider):
    def refresh_data(self):

        req_result = requests.get(f"{self.base_url}/api/v1/cars/{self.car_id}/status").json()
        data = req_result["data"]["status"]

        self.state.latitude = data["car_geodata"]["latitude"]
        self.state.longitude = data["car_geodata"]["longitude"]
        self.state.odometer = data["odometer"]
        self.state.is_driving = data["driving_details"]["shift_state"] != "P"
        self.state.is_charging  = data["charging_details"]["time_to_full_charge"] > 0
        self.state.battery_level = data["battery_details"]["battery_level"]


        self.state.active_route_latitude = data["driving_details"]["active_route"]["location"]["latitude"]
        self.state.active_route_longitude = data["driving_details"]["active_route"]["location"]["longitude"]

        self.state.active_route_destination = data["driving_details"]["active_route"]["destination"]
        self.state.active_route_minutes_to_arrival = data["driving_details"]["active_route"]["minutes_to_arrival"]
        self.state.active_route_energy_at_arrival = data["driving_details"]["active_route"]["energy_at_arrival"]