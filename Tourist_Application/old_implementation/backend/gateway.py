import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException
from backend.models import LocationData, SOSData, IngestPayload, DeviceRegistration, PositionData
from config.settings import settings


class GatewayClient:
    def __init__(self):
        self.base_url = settings.gateway_url
        self.timeout = httpx.Timeout(10.0)
        
        # MoD Core client configuration
        self.mod_core_enabled = settings.mod_core_enable_forwarding
        self.mod_core_base_url = settings.mod_core_base_url.rstrip("/")
        self.mod_core_ingest_endpoint = settings.mod_core_ingest_endpoint
        self.mod_core_timeout = httpx.Timeout(settings.mod_core_timeout_seconds)
        self.mod_core_verify = settings.mod_core_verify_tls
        self.mod_core_client_cert = None
        if settings.mod_core_client_cert_path and settings.mod_core_client_key_path:
            self.mod_core_client_cert = (
                settings.mod_core_client_cert_path,
                settings.mod_core_client_key_path
            )
        self.mod_core_trust = settings.mod_core_ca_cert_path

    async def send_ingest(self, payload: IngestPayload, token: str) -> Dict[str, Any]:
        """Send ingest payload to Gateway and optionally forward to MoD Core"""
        try:
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
                    gateway_response = {"status": "success", "data": response.json()}
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Authentication failed")
                elif response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                else:
                    response.raise_for_status()
                    gateway_response = {"status": "unknown"}

            mod_core_response = None
            if self.mod_core_enabled:
                mod_core_response = await self._forward_to_mod_core(payload, token)
            
            gateway_response["mod_core"] = mod_core_response or gateway_response.get("mod_core")
            return gateway_response
                    
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gateway timeout")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Gateway unreachable")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")

    async def _forward_to_mod_core(self, payload: IngestPayload, token: str) -> Dict[str, Any]:
        """Forward telemetry payload to MoD Core ingest endpoint"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Forwarded-By": "tourist-simulator"
            }
            url = f"{self.mod_core_base_url}{self.mod_core_ingest_endpoint}"
            async with httpx.AsyncClient(
                timeout=self.mod_core_timeout,
                verify=self.mod_core_trust if self.mod_core_verify else False,
                cert=self.mod_core_client_cert
            ) as client:
                response = await client.post(
                    url,
                    json=payload.model_dump(by_alias=True, exclude_none=True),
                    headers=headers
                )
                response.raise_for_status()
                return {
                    "status": "success",
                    "data": response.json() if response.content else None
                }
        except httpx.TimeoutException:
            return {"status": "timeout", "error": "MoD Core timeout"}
        except httpx.HTTPStatusError as exc:
            return {"status": "error", "code": exc.response.status_code, "detail": exc.response.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def send_sos(self, payload: IngestPayload, token: str) -> Dict[str, Any]:
        """Send SOS alert payload"""
        return await self.send_ingest(payload, token)

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
