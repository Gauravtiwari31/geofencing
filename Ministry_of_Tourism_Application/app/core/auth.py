"""
Authentication and authorization using OIDC and mTLS
"""
import jwt
from typing import Optional, List, Annotated
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from .config import get_settings

settings = get_settings()
security = HTTPBearer()

# Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm,
    client_secret_key=settings.keycloak_client_secret
)


class User:
    """User model from token claims."""
    def __init__(self, token_claims: dict):
        self.user_id = token_claims.get("sub")
        self.username = token_claims.get("preferred_username")
        self.email = token_claims.get("email")
        self.roles = token_claims.get("realm_access", {}).get("roles", [])
        self.client_roles = token_claims.get("resource_access", {})
        self.tourist_id = token_claims.get("tourist_id")  # Custom claim


def verify_token(token: str) -> dict:
    """Verify JWT token with Keycloak."""
    try:
        # Get public key from Keycloak
        public_key = keycloak_openid.public_key()
        key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        
        # Decode and verify token
        decoded_token = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience="account",
            options={"verify_exp": True}
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def verify_client_certificate(request: Request) -> bool:
    """Verify client certificate for mTLS."""
    # In production, this would check the client certificate
    # For now, we'll check for specific headers set by the proxy
    client_cert_verified = request.headers.get("X-Client-Cert-Verified")
    client_cert_subject = request.headers.get("X-Client-Cert-Subject")
    
    if client_cert_verified != "SUCCESS":
        return False
    
    # Verify certificate subject contains expected values
    if not client_cert_subject:
        return False
    
    # Check if it's from an authorized client
    authorized_subjects = [
        "police-sedi",
        "user-gateway",
        "mod-admin"
    ]
    
    return any(subject in client_cert_subject for subject in authorized_subjects)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from JWT token."""
    token = credentials.credentials
    token_claims = verify_token(token)
    return User(token_claims)


async def get_current_user_with_mtls(
    request: Request,
    user: User = Depends(get_current_user)
) -> User:
    """Get current user with mTLS verification for police endpoints."""
    if not verify_client_certificate(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid client certificate required"
        )
    return user


def require_roles(required_roles: List[str]):
    """Decorator to require specific roles."""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        user_roles = set(user.roles)
        required_roles_set = set(required_roles)
        
        if not required_roles_set.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {required_roles}"
            )
        return user
    return role_checker


def require_police_role():
    """Require POLICE role with mTLS."""
    def police_checker(
        request: Request,
        user: User = Depends(get_current_user)
    ) -> User:
        # Check role
        if "POLICE" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="POLICE role required"
            )
        
        # Check mTLS
        if not verify_client_certificate(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Valid client certificate required for police access"
            )
        
        return user
    return police_checker


def require_tourist_role():
    """Require TOURIST role."""
    return require_roles(["TOURIST"])


def require_admin_role():
    """Require ADMIN role."""
    return require_roles(["ADMIN"])


# Type annotations for dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
TouristUser = Annotated[User, Depends(require_tourist_role())]
PoliceUser = Annotated[User, Depends(require_police_role())]
AdminUser = Annotated[User, Depends(require_admin_role())]
