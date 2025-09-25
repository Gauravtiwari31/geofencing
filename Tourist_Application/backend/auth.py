import httpx
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from config.settings import settings


security = HTTPBearer()


class KeycloakAuth:
    def __init__(self):
        self.keycloak_url = settings.keycloak_url
        self.realm = settings.keycloak_realm
        self.client_id = settings.keycloak_client_id
        self.client_secret = settings.keycloak_client_secret
        self._public_key = None
        self._token_cache = {}

    async def get_public_key(self) -> str:
        """Fetch Keycloak public key for JWT verification"""
        if self._public_key:
            return self._public_key
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
                )
                response.raise_for_status()
                jwks = response.json()
                
                # Extract first key (simplified for demo)
                if jwks.get("keys"):
                    # In production, you'd find the right key by kid
                    self._public_key = jwks["keys"][0]
                    return self._public_key
                    
        except Exception as e:
            print(f"Failed to fetch Keycloak public key: {e}")
            
        return None

    async def get_auth_url(self, redirect_uri: str) -> str:
        """Generate Keycloak authorization URL"""
        return (
            f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/auth"
            f"?client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=openid profile email"
        )

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
                
                if self.client_secret:
                    data["client_secret"] = self.client_secret
                
                response = await client.post(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "refresh_token": refresh_token,
                }
                
                if self.client_secret:
                    data["client_secret"] = self.client_secret
                
                response = await client.post(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token refresh failed: {e}")

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token (simplified for demo)"""
        try:
            # In production, you'd properly verify with public key
            # For demo, we'll do basic JWT decode without verification
            payload = jwt.get_unverified_claims(token)
            
            # Check expiration
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                raise HTTPException(status_code=401, detail="Token expired")
                
            return payload
            
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get user info from Keycloak"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Failed to get user info: {e}")


# Global auth instance
keycloak_auth = KeycloakAuth()


async def get_current_user(token: str = Depends(security)):
    """Dependency to get current authenticated user"""
    if not token.credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    
    user_info = await keycloak_auth.verify_token(token.credentials)
    return user_info


# Token storage (in production, use proper session management)
class TokenStorage:
    def __init__(self):
        self._tokens = {}
    
    def store_token(self, user_id: str, token_data: Dict[str, Any]):
        self._tokens[user_id] = {
            **token_data,
            "stored_at": datetime.utcnow()
        }
    
    def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._tokens.get(user_id)
    
    def remove_token(self, user_id: str):
        self._tokens.pop(user_id, None)


token_storage = TokenStorage()
