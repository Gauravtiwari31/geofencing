import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException
from backend.models import LocationData, SOSData, IngestPayload, DeviceRegistration
from config.settings import settings


class GatewayClient:
    def __init__(self):
        self.base_url = settings.gateway_url
        self.timeout = httpx.Timeout(10.0)
        
    async def send_location(self, location: LocationData, token: str, sos: Optional[SOSData] = None) -> Dict[str, Any]:
        """Send location data to Gateway /gw/ingest endpoint"""
        try:
            payload = IngestPayload(
                location=location,
                timestamp=datetime.utcnow().isoformat(),
                sos=sos
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Client-Type": "tourist-simulator"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/gw/ingest",
                    json=payload.model_dump(exclude_none=True),
                    headers=headers
                )
                
                if response.status_code == 200:
                    return {"status": "success", "data": response.json()}
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Authentication failed")
                elif response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                else:
                    response.raise_for_status()
                    
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gateway timeout")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Gateway unreachable")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")

    async def send_sos(self, location: LocationData, token: str) -> Dict[str, Any]:
        """Send SOS alert to Gateway"""
        sos_data = SOSData(
            active=True,
            lat=location.lat,
            lng=location.lng,
            timestamp=datetime.utcnow()
        )
        
        return await self.send_location(location, token, sos_data)

    async def get_messages(self, token: str) -> Dict[str, Any]:
        """Get messages from Gateway"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Client-Type": "tourist-simulator"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/gw/messages",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

    async def register_device(self, registration: DeviceRegistration, token: str) -> Dict[str, Any]:
        """Register device with Gateway"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Client-Type": "tourist-simulator"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/gw/register-device",
                    json=registration.model_dump(),
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Device registration failed: {str(e)}")

    async def check_connectivity(self) -> bool:
        """Check if Gateway is reachable"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                return response.status_code == 200
        except:
            # If no health endpoint, try a simple GET to base URL
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                    response = await client.get(self.base_url, timeout=5.0)
                    return response.status_code in [200, 404, 405]  # Any response means it's up
            except:
                return False


# Global gateway client instance
gateway_client = GatewayClient()
