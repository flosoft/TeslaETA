from abc import ABC, abstractmethod

class IBackendProvider(ABC):
    @abstractmethod
    def latitude():
        pass
    
    @abstractmethod
    def longitude():
        pass
    
    @abstractmethod
    def odometer():
        pass
    
    @abstractmethod
    def is_driving():
        pass
    
    @abstractmethod
    def is_charging():
        pass
    
    @abstractmethod
    def get_battery_level():
        pass
    
    @abstractmethod
    def active_route_destination():
        pass
    
    @abstractmethod
    def active_route_latitude():
        pass
    
    @abstractmethod
    def active_route_longitude():
        pass
    
    @abstractmethod
    def active_route_minutes_to_arrival():
        pass
    
    @abstractmethod
    def active_route_energy_at_arrival():
        pass