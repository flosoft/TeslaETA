from enum import Enum
import importlib
from backendproviders import teslalogger, teslamate
from interfaces.backendinterface import IBackendProvider

class BackendProviderFactory:
    # static to have a singleton-like
    provider: IBackendProvider

    def _load_provider(self, name, base_url, car_id):
        if name == "teslalogger":
            return teslalogger.TeslaloggerBackendProvider(base_url, car_id)
        elif name == "teslamate":
            return teslamate.TeslamateBackendProvider(base_url, car_id)
        else:
            raise Exception(f"Unknown backend provider : {name}. Available choices are 'teslalogger' or 'teslamagte'.")
    
    
    def __init__(self, provider_name, base_url, car_id):
        self.provider_name = provider_name
        
        BackendProviderFactory.provider = self._load_provider(provider_name, base_url, car_id)

    @staticmethod
    def get_instance() -> IBackendProvider:
        return BackendProviderFactory.provider
