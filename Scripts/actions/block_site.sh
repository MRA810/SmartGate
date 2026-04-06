#!/bin/bash
# Usage: ./block_site.sh example.com

if [ -z "$1" ]; then
    echo "Usage: $0 domain"
    exit 1
fi

DOMAIN=$1

# Add to blocked list if not already present
grep -qx "$DOMAIN" /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/blocked_sites.txt || echo "$DOMAIN" | sudo tee -a /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/blocked_sites.txt

# Reload Squid
sudo systemctl reload squid

echo "Blocked $DOMAIN"
