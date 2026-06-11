#!/bin/bash
# Generate a self-signed TLS certificate for the ristomele server.
# Run once on the Raspberry Pi before starting the service with HTTPS.
#
# Usage: ./generate_cert.sh
#   Writes ssl_cert.pem and ssl_key.pem in the current directory.

set -e

CERT=ssl_cert.pem
KEY=ssl_key.pem

if [ -f "$CERT" ] && [ -f "$KEY" ]; then
    echo "Certificate already exists, skipping generation."
    echo "  $CERT"
    echo "  $KEY"
    exit 0
fi

openssl req -x509 -newkey rsa:2048 \
    -keyout "$KEY" \
    -out    "$CERT" \
    -days   3650 \
    -nodes \
    -subj   '/CN=ristomele'

echo "Done. Certificate written:"
echo "  $CERT"
echo "  $KEY"
