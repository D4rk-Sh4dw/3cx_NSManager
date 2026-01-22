#!/bin/bash
set -e

HOST=${EXTERNAL_HOST:-localhost}
echo "Ensuring SSL Certs for HOST: $HOST"

mkdir -p /etc/nginx/certs

if [ ! -f /etc/nginx/certs/cert.pem ] || [ ! -f /etc/nginx/certs/key.pem ]; then
    echo "Generating self-signed certificate..."
    
    # Determine SAN prefix
    if [[ $HOST =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        SAN_PREFIX="IP"
    else
        SAN_PREFIX="DNS"
    fi
    
    openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/certs/key.pem -out /etc/nginx/certs/cert.pem -days 365 -nodes \
    -subj "/CN=$HOST" \
    -addext "subjectAltName = DNS:localhost,IP:127.0.0.1,$SAN_PREFIX:$HOST"
    
    echo "Certificate generated."
fi

# Nginx docker image entrypoint handles template substitution automatically!
