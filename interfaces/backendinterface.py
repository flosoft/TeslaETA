from abc import ABC, abstractmethod

class IBackendProvider(ABC):
    base_url: str = None
    car_id: int = None

    latitude: float = None
    longitude: float = None
    odometer: float = None
    is_driving: bool = False
    is_charging: bool = False
    battery_level: int = 0

    active_route_destination: str = None
    active_route_latitude: float = None
    active_route_longitude: float = None
    active_route_minutes_to_arrival: float = None
    active_route_energy_at_arrival: int = None


    def __init__(self, base_url, car_id):
        self.base_url = base_url
        self.car_id = car_id

        print(f"Starting provider. BASE_URL : {base_url}, CAR_ID : {car_id}")

    @abstractmethod
    def refresh_data(self):
        pass

    @property
    def active_route_seconds_to_arrival(self) -> float:
        return self.active_route_minutes_to_arrival * 60