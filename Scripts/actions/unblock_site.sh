#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 domain"
    exit 1
fi

DOMAIN=$1
FILE="/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt"

# Remove domain from list
if [ -f "$FILE" ]; then
    grep -v "^$DOMAIN$" "$FILE" > /tmp/blocked_tmp.txt && mv /tmp/blocked_tmp.txt "$FILE"
fi

# Reload squid (no interactive prompt if sudo is configured properly)
sudo systemctl reload squid

echo "Unblocked $DOMAIN"