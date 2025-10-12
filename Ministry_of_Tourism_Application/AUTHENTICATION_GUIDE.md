# 🔐 MoD Core - Authentication Guide

## 🎯 **Working Authentication Commands**

This guide contains the **tested and verified** authentication commands for the MoD Core system.

---

## 🏃‍♂️ **Quick Start - Get Tokens**

### **For Tourist Mobile Applications:**
```bash
curl -k -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=tourist-app" \
  -d "username=tourist-demo" \
  -d "password=tourist123"
```

**Response:**
```json
{
  "access_token": "eyJhbGci...long_jwt_token...",
  "expires_in": 3600,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGci...refresh_token...",
  "token_type": "Bearer"
}
```

### **For Police SEDI Applications:**
```bash
curl -k -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=police-sedi" \
  -d "client_secret=police-sedi-secret-2025"
```

**Response:**
```json
{
  "access_token": "eyJhbGci...police_jwt_token...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "email profile"
}
```

---

## 🔑 **Token Usage Examples**

### **Tourist API Calls:**
```bash
# Extract the access token from the response above
TOURIST_TOKEN="eyJhbGci...your_tourist_token..."

# Test geofence summary endpoint
curl -H "Authorization: Bearer $TOURIST_TOKEN" \
     "http://localhost:2030/v1/app/fences/summary?lat=26.162&lon=91.779"

# Test messages endpoint
curl -H "Authorization: Bearer $TOURIST_TOKEN" \
     "http://localhost:2030/v1/app/messages"

# Test telemetry ingest endpoint
curl -H "Authorization: Bearer $TOURIST_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST "http://localhost:2030/v1/app/ingest" \
     -d '{
       "tourist_id": "demo-tourist-uuid-123",
       "device_id": "demo-device-001",
       "position": {
         "lat": 26.162,
         "lon": 91.779,
         "ts": "2025-09-25T10:30:00Z"
       },
       "health": {
         "battery": 0.75
       },
       "sos": {
         "active": false
       },
       "app": {
         "build": "1.0.0",
         "platform": "android"
       }
     }'
```

### **Police API Calls:**
```bash
# Extract the access token from the police response
POLICE_TOKEN="eyJhbGci...your_police_token..."

# Test police stream endpoint (Server-Sent Events)
curl -H "Authorization: Bearer $POLICE_TOKEN" \
     -H "Accept: text/event-stream" \
     "http://localhost:2030/v1/police/stream"

# Test police alert acknowledgment
curl -H "Authorization: Bearer $POLICE_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST "http://localhost:2030/v1/police/ack" \
     -d '{
       "alert_id": 123,
       "tourist_id": "demo-tourist-uuid-123",
       "note": "Alert acknowledged by officer",
       "officer_id": "officer-001"
     }'
```

---

## 🔧 **Configuration Details**

### **Keycloak Configuration:**
- **Realm:** `mod-core`
- **Server:** `https://host.docker.internal:2027`
- **Token Endpoint:** `/realms/mod-core/protocol/openid-connect/token`

### **Pre-configured Clients:**
1. **tourist-app**
   - Type: Public client
   - Grant Types: `password`, `authorization_code`, `refresh_token`
   - Roles: `TOURIST`

2. **police-sedi**
   - Type: Confidential client
   - Grant Types: `client_credentials`, `authorization_code`, `refresh_token`
   - Roles: `POLICE`
   - Secret: `police-sedi-secret-2025`

3. **mod-api**
   - Type: Confidential client
   - Grant Types: `client_credentials`
   - Roles: `ADMIN`
   - Secret: `mod-api-secret-key-2025`

### **Pre-configured Users:**
- **tourist-demo** / `tourist123` (TOURIST role)
- **police-officer** / `police123` (POLICE role)
- **admin** / `admin123` (ADMIN role)

---

## 🌐 **Docker Environment Notes**

### **Important URLs:**
- **From Host:** `https://localhost:2027`
- **From Container:** `https://host.docker.internal:2027`
- **Internal:** `https://keycloak:2027` (if using docker-compose)

### **SSL Certificate:**
- Uses self-signed certificates
- Requires `-k` flag with curl
- For production, replace with valid SSL certificates

---

## 🧪 **Testing Authentication Flow**

### **Complete End-to-End Test:**
```bash
echo "=== MoD Core Authentication Test ==="

# 1. Get Tourist Token
echo "1. Getting tourist token..."
TOURIST_RESPONSE=$(curl -k -s -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=tourist-app" \
  -d "username=tourist-demo" \
  -d "password=tourist123")

TOURIST_TOKEN=$(echo $TOURIST_RESPONSE | jq -r '.access_token')
echo "Tourist token: ${TOURIST_TOKEN:0:50}..."

# 2. Get Police Token  
echo "2. Getting police token..."
POLICE_RESPONSE=$(curl -k -s -X POST "https://host.docker.internal:2027/realms/mod-core/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=police-sedi" \
  -d "client_secret=police-sedi-secret-2025")

POLICE_TOKEN=$(echo $POLICE_RESPONSE | jq -r '.access_token')
echo "Police token: ${POLICE_TOKEN:0:50}..."

# 3. Test Tourist API
echo "3. Testing tourist API..."
curl -s -H "Authorization: Bearer $TOURIST_TOKEN" \
     "http://localhost:2030/v1/app/fences/summary?lat=26.162&lon=91.779" | jq

# 4. Test Police API  
echo "4. Testing police stream (first 3 lines)..."
timeout 10 curl -s -H "Authorization: Bearer $POLICE_TOKEN" \
     "http://localhost:2030/v1/police/stream" | head -3

echo "=== Authentication Test Complete ==="
```

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. "Invalid client credentials"**
- Check client_id and client_secret are correct
- Verify the client exists in Keycloak admin console

**2. "Invalid user credentials"**  
- Check username and password
- Verify user exists and is enabled in Keycloak

**3. "SSL certificate problem"**
- Use `-k` flag with curl for self-signed certificates
- For production, use valid SSL certificates

**4. "Connection refused"**
- Check Keycloak is running on port 2027
- Use correct hostname (localhost vs host.docker.internal)

**5. "Invalid token"**
- Check token hasn't expired (3600 seconds = 1 hour)
- Verify token format and Bearer prefix

### **Debug Commands:**
```bash
# Check Keycloak health
curl -k -s "https://host.docker.internal:2027/realms/mod-core" | jq

# Check token details (decode JWT)
echo "your_token_here" | cut -d. -f2 | base64 -d | jq

# Check API health
curl -s "http://localhost:2030/health" | jq
```

---

## ✅ **Success Indicators**

When authentication is working correctly, you should see:

1. **Token Response:** Valid JWT tokens with 3600 second expiry
2. **Tourist API:** Geofence data and safety information
3. **Police API:** SSE stream with tourist monitoring data
4. **Role Validation:** Proper 403 errors when using wrong role tokens

**🎉 Your MoD Core authentication system is fully operational!**
