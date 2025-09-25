#!/bin/bash
set -e

echo "🔐 Generating SSL certificates for MoD Core..."

# Create certs directory in a writable location
mkdir -p /workspace/ssl-certs
cd /workspace/ssl-certs

# Check if certificates already exist
if [ -f server.crt ] && [ -f server.key ] && [ -f ca.crt ]; then
    echo "✅ Certificates already exist. Skipping generation."
    echo "To regenerate, delete the certs directory and run this script again."
    exit 0
fi

# Generate Root CA private key
echo "📝 Generating Root CA private key..."
openssl genrsa -out ca.key 4096

# Generate Root CA certificate
echo "📝 Generating Root CA certificate..."
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/C=IN/ST=AS/L=Guwahati/O=Ministry of Tourism/OU=Core Safety/CN=MoD-Core-CA"

# Generate server private key
echo "📝 Generating server private key..."
openssl genrsa -out server.key 4096

# Generate server certificate signing request
echo "📝 Generating server certificate signing request..."
openssl req -new -key server.key -out server.csr -subj "/C=IN/ST=AS/L=Guwahati/O=Ministry of Tourism/OU=Core Safety/CN=localhost"

# Create server certificate extensions file
cat > server.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = mod-core
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate server certificate
echo "📝 Generating server certificate..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -extfile server.ext

# Generate Police SEDI client certificate
echo "📝 Generating Police SEDI client certificate..."
openssl genrsa -out police-client.key 4096
openssl req -new -key police-client.key -out police-client.csr -subj "/C=IN/ST=AS/L=Guwahati/O=Police SEDI/OU=Operations/CN=police-sedi"
openssl x509 -req -in police-client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out police-client.crt -days 365

# Generate User Gateway client certificate
echo "📝 Generating User Gateway client certificate..."
openssl genrsa -out gateway-client.key 4096
openssl req -new -key gateway-client.key -out gateway-client.csr -subj "/C=IN/ST=AS/L=Guwahati/O=User Gateway/OU=Tourism/CN=user-gateway"
openssl x509 -req -in gateway-client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out gateway-client.crt -days 365

# Generate Keycloak certificate (self-signed)
echo "📝 Generating Keycloak certificate..."
openssl genrsa -out keycloak.key 4096
openssl req -new -x509 -days 365 -key keycloak.key -out keycloak.crt -subj "/C=IN/ST=AS/L=Guwahati/O=Ministry of Tourism/OU=Identity/CN=keycloak"

# Clean up temporary files
rm -f *.csr *.ext

# Set appropriate permissions
chmod 600 *.key
chmod 644 *.crt
chown -R www-data:www-data /workspace/ssl-certs

echo "✅ Certificate generation complete!"
echo ""
echo "Generated certificates:"
echo "  📜 Root CA: ca.crt, ca.key"
echo "  🖥️  Server: server.crt, server.key"
echo "  👮 Police Client: police-client.crt, police-client.key"
echo "  🚪 Gateway Client: gateway-client.crt, gateway-client.key"
echo "  🔐 Keycloak: keycloak.crt, keycloak.key"
echo ""
echo "⚠️  Client certificates (police-client.* and gateway-client.*) should be"
echo "   distributed to respective client systems for mTLS authentication."
echo ""
