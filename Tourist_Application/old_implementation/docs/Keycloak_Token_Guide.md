# Keycloak Token Retrieval Guide

> **Redirect Fix**: Set `APP_EXTERNAL_BASE_URL=http://localhost:2040` (or rely on `X-Forwarded-Proto`/`X-Forwarded-Host` headers if using a reverse proxy) so the login button doesn’t redirect to `0.0.0.0`.

The Tourist Mobile Simulator now uses the **proper OIDC Authorization Code Flow with PKCE** for enhanced security. This is the recommended approach for user-facing applications.

## Interactive Login Flow (Recommended)

### 1. Authorization Code Flow with PKCE
The Tourist Mobile Simulator now uses the proper OIDC Authorization Code Flow with PKCE (Proof Key for Code Exchange) for enhanced security.

**Step 1: Get Authorization URL**
```bash
# The login button now generates a URL with PKCE parameters:
https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/auth
  ?client_id=tourist-app
  &response_type=code
  &scope=openid profile email
  &redirect_uri=http://localhost:2040/auth/callback
  &state=<random_state>
  &code_challenge=<pkce_challenge>
  &code_challenge_method=S256
```

**Step 2: User Authentication**
- Browser redirects to Keycloak login page
- User enters credentials: `tourist-demo` / `tourist123`
- Keycloak redirects back to `/auth/callback` with code and state

**Step 3: Token Exchange**
The callback endpoint automatically exchanges the authorization code for tokens using PKCE verification.

## Direct Token Retrieval (Alternative)

For testing or scripting, you can still use the password grant:

```bash
curl -k -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=tourist-app" \
  -d "username=tourist-demo" \
  -d "password=tourist123"
```

### Prerequisites
- Keycloak accessible at `https://host.docker.internal:2027`
- The `tourist-app` client configured to allow password grant
- Test credentials: `username=tourist-demo`, `password=tourist123`

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

## Security Features

- ✅ **PKCE (Proof Key for Code Exchange)** - Prevents authorization code interception
- ✅ **State Parameter** - CSRF protection for the authorization flow
- ✅ **Code Verifier** - Ensures the authorization code was issued to this client
- ✅ **Secure Random Generation** - Cryptographically secure state and PKCE parameters
