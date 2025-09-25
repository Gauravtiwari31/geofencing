# Keycloak Token Retrieval Guide

> **Redirect Fix**: Set `APP_EXTERNAL_BASE_URL=http://localhost:2040` (or rely on `X-Forwarded-Proto`/`X-Forwarded-Host` headers if using a reverse proxy) so the login button doesn’t redirect to `0.0.0.0`.

The Tourist Mobile Simulator and the MoD Core integration rely on Keycloak for issuing OAuth2 access tokens. Use the following curl command to obtain a token for the `tourist-app` client in the `mod-core` realm.

> **Prerequisites**
> - Keycloak accessible at `https://localhost:2027`
> - The `tourist-app` client configured to allow password grant
> - Test credentials: `username=tourist-demo`, `password=tourist123`

## Command

```bash
curl -k -X POST "https://localhost:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=tourist-app" \
  -d "username=tourist-demo" \
  -d "password=tourist123"
```

### Flags Explained
- `-k` : Allows insecure TLS (self-signed certificates in dev)
- `grant_type=password` : Uses Resource Owner Password Credentials flow
- `client_id=tourist-app` : Keycloak client configured for the simulator
- `username/password` : Demo credentials provisioned in Keycloak

### Sample Response
```json
{
  "access_token": "<JWT>",
  "expires_in": 3600,
  "refresh_expires_in": 1800,
  "refresh_token": "<JWT>",
  "token_type": "Bearer",
  "scope": "email profile"
}
```

Use the value of `access_token` as the Bearer token for calls to the Gateway and MoD Core APIs.
