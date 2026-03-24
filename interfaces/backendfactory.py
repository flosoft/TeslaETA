from enum import Enum
import importlib
import os
from backendproviders.teslamate_mqtt import TeslamateMQTTBackendProvider
from interfaces.backendinterface import IBackendProvider

class BackendProviderFactory:
    # static to have a singleton-like
    provider: IBackendProvider

    def _load_provider(self, name, hostname, car_id):
        if name == "teslamate-mqtt":
            mqtt_port = int(os.getenv("MQTT_PORT", 1883))
            mqtt_username = os.getenv("MQTT_USERNAME")
            mqtt_password = os.getenv("MQTT_PASSWORD")
            
            provider = TeslamateMQTTBackendProvider(
                hostname, car_id,
                mqtt_port=mqtt_port,
                mqtt_username=mqtt_username,
                mqtt_password=mqtt_password,
            )
            provider.start()
            return provider
        else:
            raise Exception(f"Unknown backend provider : {name}. Available choices are : 'teslamate-mqtt'.")
    
    
    def __init__(self, provider_name, hostname, car_id):
        self.provider_name = provider_name
        
        BackendProviderFactory.provider = self._load_provider(provider_name, hostname, car_id)

    @staticmethod
    def get_instance() -> IBackendProvider:
        return BackendProviderFactory.provider
