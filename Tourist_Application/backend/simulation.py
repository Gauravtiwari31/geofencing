import asyncio
from datetime import datetime
from typing import Optional, List, Tuple
from backend.models import LocationData, SimulationPath, SimulationStatus
from backend.gateway import gateway_client
from backend.mqtt_client import mqtt_client


class PathSimulator:
    def __init__(self):
        self.active = False
        self.current_path: Optional[SimulationPath] = None
        self.current_position = 0
        self.current_location: Optional[LocationData] = None
        self.task: Optional[asyncio.Task] = None
        
    async def start_simulation(self, path: SimulationPath, token: str) -> bool:
        """Start path simulation"""
        if self.active:
            await self.stop_simulation()
            
        self.current_path = path
        self.current_position = 0
        self.active = True
        
        # Start simulation task
        self.task = asyncio.create_task(self._simulate_movement(token))
        return True
        
    async def stop_simulation(self):
        """Stop path simulation"""
        self.active = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        
    async def _simulate_movement(self, token: str):
        """Simulate movement along the path"""
        try:
            while self.active and self.current_path:
                coordinates = self.current_path.coordinates
                if self.current_position >= len(coordinates):
                    # Path completed, restart from beginning
                    self.current_position = 0
                    
                # Get current coordinate
                lat, lon = coordinates[self.current_position]
                self.current_location = LocationData(
                    lat=lat,
                    lon=lon,
                    timestamp=datetime.utcnow()
                )
                
                # Send location to Gateway
                try:
                    await gateway_client.send_location(self.current_location, token)
                    print(f"Simulation: sent location {lat:.6f}, {lon:.6f}")
                except Exception as e:
                    print(f"Simulation: failed to send location: {e}")
                
                # Send telemetry via MQTT
                try:
                    await mqtt_client.publish_telemetry(
                        self.current_location,
                        heart_rate=75 + (self.current_position % 20),  # Simulate varying HR
                        battery=1.0 - (self.current_position * 0.001)  # Simulate battery drain
                    )
                except Exception as e:
                    print(f"Simulation: failed to send MQTT telemetry: {e}")
                
                # Move to next position
                self.current_position += 1
                
                # Wait based on speed setting
                await asyncio.sleep(1.0 / self.current_path.speed)
                
        except asyncio.CancelledError:
            print("Simulation cancelled")
        except Exception as e:
            print(f"Simulation error: {e}")
            self.active = False
            
    def get_status(self) -> SimulationStatus:
        """Get current simulation status"""
        progress = 0.0
        if self.current_path and len(self.current_path.coordinates) > 0:
            progress = self.current_position / len(self.current_path.coordinates)
            
        return SimulationStatus(
            active=self.active,
            current_position=self.current_location,
            path_name=self.current_path.name if self.current_path else None,
            progress=min(progress, 1.0)
        )


# Predefined simulation paths for common tourist areas
PREDEFINED_PATHS = {
    "city_center": SimulationPath(
        name="City Center Tour",
        coordinates=[
            [26.1625, 91.7794],  # Guwahati center
            [26.1635, 91.7804],
            [26.1645, 91.7814],
            [26.1655, 91.7824],
            [26.1665, 91.7834],
            [26.1625, 91.7794],  # Return to start
        ],
        speed=0.5  # 0.5 points per second
    ),
    "riverside_walk": SimulationPath(
        name="Brahmaputra Riverside",
        coordinates=[
            [26.1600, 91.7750],
            [26.1610, 91.7760],
            [26.1620, 91.7770],
            [26.1630, 91.7780],
            [26.1640, 91.7790],
            [26.1650, 91.7800],
            [26.1660, 91.7810],
        ],
        speed=0.3
    ),
    "temple_circuit": SimulationPath(
        name="Temple Circuit",
        coordinates=[
            [26.1580, 91.7720],  # Kamakhya area
            [26.1590, 91.7730],
            [26.1600, 91.7740],
            [26.1610, 91.7750],
            [26.1580, 91.7720],
        ],
        speed=0.2
    )
}


# Global simulator instance
path_simulator = PathSimulator()
