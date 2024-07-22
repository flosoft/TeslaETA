from enum import Enum
import importlib
from backendproviders import teslalogger, teslamate
from interfaces.backendinterface import IBackendProvider

class BackendProviderFactory:
    def _load_provider(self, name):
        if name == "teslalogger":
            return teslalogger.TeslaloggerBackendProvider()
        elif name == "teslamate":
            return teslamate.TeslamateBackendProvider()
        else:
            raise Exception(f"Unknown backend provider : {name}. Available choices are 'teslalogger' or 'teslamagte'.")
    
    
    def __init__(self, provider_name):
        self.provider_name = provider_name
        
        self.provider_instance = self._load_provider(provider_name)

    def get_instance(self) -> IBackendProvider:
        return self.provider_instance
