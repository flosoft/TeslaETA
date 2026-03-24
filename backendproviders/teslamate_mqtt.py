import json
import threading
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from dtos.state_dto import StateDTO
from interfaces.backendinterface import IBackendProvider

class TeslamateMQTTBackendProvider(IBackendProvider):
    def __init__(self, hostname, car_id, mqtt_port=1883, mqtt_username=None, mqtt_password=None):
        super().__init__(hostname, car_id)
        self.hostname = hostname
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password

        self.state = StateDTO()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self.is_connected = False

        # Use default clean_session=True (stateless session).
        # Retained messages from Teslamate are delivered immediately on subscribe
        # regardless of session type — clean_session=False is not needed.
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        if mqtt_username:
            self._client.username_pw_set(mqtt_username, mqtt_password)

        # Exponential reconnect delay: 1s initial, 64s maximum
        self._client.reconnect_delay_set(min_delay=1, max_delay=64)

    def start(self):
        self._client.connect(self.hostname, self.mqtt_port, keepalive=60)
        self._client.loop_start()

    def refresh_data(self):
        # No-op: MQTT pushes updates continuously
        pass

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"TeslamateMQTT: failed to connect, reason_code={reason_code}")
            self.is_connected = False
        else:
            self.is_connected = True
            topic = f"teslamate/cars/{self.car_id}/#"
            client.subscribe(topic, qos=1)
            print(f"TeslamateMQTT: connected and subscribed to {topic} (QoS 1)")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.is_connected = False
        print(f"TeslamateMQTT: disconnected, reason_code={reason_code}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload_str = msg.payload.decode("utf-8")
        except Exception:
            return

        prefix = f"teslamate/cars/{self.car_id}/"
        if not topic.startswith(prefix):
            return

        subtopic = topic[len(prefix):]

        with self._condition:
            self._handle_subtopic(subtopic, payload_str)
            self._condition.notify_all()

    def _handle_subtopic(self, subtopic, payload_str):
        if subtopic == "location":
            try:
                data = json.loads(payload_str)
                self.state.latitude = data["latitude"]
                self.state.longitude = data["longitude"]
            except Exception as e:
                print(f"TeslamateMQTT: error parsing location: {e}")

        elif subtopic == "shift_state":
            self.state.shift_state = payload_str if payload_str else None
            self.state.is_driving = payload_str in ("D", "R", "N")

        elif subtopic == "battery_level":
            try:
                self.state.battery_level = int(payload_str)
            except ValueError:
                pass

        elif subtopic == "heading":
            try:
                self.state.heading = float(payload_str)
            except ValueError:
                pass

        elif subtopic == "odometer":
            try:
                self.state.odometer = float(payload_str)
            except ValueError:
                pass

        elif subtopic == "charging_state":
            self.state.is_charging = payload_str == "Charging"

        elif subtopic == "speed":
            try:
                self.state.speed = int(payload_str)
            except ValueError:
                pass

        elif subtopic == "active_route":
            try:
                data = json.loads(payload_str)
                if data.get("error") is not None:
                    self.state.active_route_destination = None
                    self.state.active_route_latitude = None
                    self.state.active_route_longitude = None
                    self.state.active_route_minutes_to_arrival = None
                    self.state.active_route_energy_at_arrival = None
                else:
                    self.state.active_route_destination = data.get("destination")
                    location = data.get("location", {})
                    self.state.active_route_latitude = location.get("latitude")
                    self.state.active_route_longitude = location.get("longitude")
                    self.state.active_route_minutes_to_arrival = data.get("minutes_to_arrival")
                    self.state.active_route_energy_at_arrival = data.get("energy_at_arrival")
            except Exception as e:
                print(f"TeslamateMQTT: error parsing active_route: {e}")
