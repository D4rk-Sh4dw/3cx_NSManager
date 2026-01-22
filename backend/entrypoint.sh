#!/bin/bash
set -e

# Default to localhost if not provided
HOST=${SSL_SAN_IP:-127.0.0.1}

echo "Checking SSL Certificates for HOST: $HOST"

if [ ! -f /app/certs/cert.pem ] || [ ! -f /app/certs/key.pem ]; then
    echo "Generating self-signed certificate..."
    mkdir -p /app/certs
    
    # Determine if HOST is an IP or DNS Name for the SAN field
    if [[ $HOST =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        SAN_PREFIX="IP"
    else
        SAN_PREFIX="DNS"
    fi
    
    openssl req -x509 -newkey rsa:4096 -keyout /app/certs/key.pem -out /app/certs/cert.pem -days 365 -nodes \
    -subj "/CN=$HOST" \
    -addext "subjectAltName = DNS:localhost,IP:127.0.0.1,$SAN_PREFIX:$HOST"
    
    echo "Certificate generated."
else
    echo "Certificates found. Skipping generation."
    echo "Note: If you changed the HOST/IP, delete /app/certs content and restart."
fi

# Execute the CMD passed to docker run
exec "$@"
