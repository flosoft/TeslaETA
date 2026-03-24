from dataclasses import field
from typing import Optional
from marshmallow_dataclass import dataclass

@dataclass
class StateDTO():
    latitude: float = None
    longitude: float = None
    heading: float = None
    odometer: float = None
    is_driving: bool = False
    is_charging: bool = False
    battery_level: int = 0

    active_route_destination: str = None
    active_route_latitude: float = None
    active_route_longitude: float = None
    active_route_minutes_to_arrival: float = None
    active_route_energy_at_arrival: int = None
