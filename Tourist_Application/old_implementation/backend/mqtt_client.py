import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt
from backend.models import LocationData, SOSData
from config.settings import settings


class MQTTClient:
    def __init__(self):
        self.host = settings.gateway_mqtt_host
        self.port = settings.gateway_mqtt_port
        self.device_id = settings.device_id
        self.client = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id=f"tourist-sim-{self.device_id}")
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to Gateway Mosquitto
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(10):  # 5 second timeout
                await asyncio.sleep(0.5)
                if self.connected:
                    return True
                    
            return False
            
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            print(f"Connected to MQTT broker at {self.host}:{self.port}")
        else:
            print(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        print("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback for received MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"Received MQTT message on {topic}: {payload}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    async def publish_telemetry(self, location: LocationData, heart_rate: Optional[int] = None, 
                               battery: Optional[float] = None) -> bool:
        """Publish ESP32-style telemetry data"""
        if not self.connected:
            return False
            
        try:
            topic = f"esp32/{self.device_id}/telemetry"
            payload = {
                "ts": datetime.utcnow().isoformat(),
                "lat": location.lat,
                "lng": location.lng,
            }
            
            if heart_rate is not None:
                payload["hr"] = heart_rate
                
            if battery is not None:
                payload["bat"] = battery
                
            # Add simulated accelerometer data
            payload["accel"] = [0.1, 0.2, 9.8]  # [x, y, z] in m/s²
            
            result = self.client.publish(topic, json.dumps(payload))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"Failed to publish telemetry: {e}")
            return False

    async def publish_sos(self, location: LocationData) -> bool:
        """Publish ESP32-style SOS alert"""
        if not self.connected:
            return False
            
        try:
            topic = f"esp32/{self.device_id}/sos"
            payload = {
                "ts": datetime.utcnow().isoformat(),
                "lat": location.lat,
                "lng": location.lng,
                "emergency": True
            }
            
            result = self.client.publish(topic, json.dumps(payload))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"Failed to publish SOS: {e}")
            return False

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False

    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self.connected


# Global MQTT client instance
mqtt_client = MQTTClient()
