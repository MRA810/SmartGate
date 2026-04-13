#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 domain"
    exit 1
fi

DOMAIN=$1
FILE="/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt"

# Add domain safely
grep -qx "$DOMAIN" "$FILE" || echo "$DOMAIN" >> "$FILE"

# Reload squid (NO sudo password prompt version)
sudo systemctl reload squid

echo "Blocked $DOMAIN"