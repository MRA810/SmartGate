#!/bin/bash
# Usage: ./unblock_site.sh example.com

if [ -z "$1" ]; then
    echo "Usage: $0 domain"
    exit 1
fi

DOMAIN=$1

# Remove domain from blocked list
sudo sed -i "/^$DOMAIN$/d" /home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt

# Reload Squid
sudo systemctl reload squid

echo "Unblocked $DOMAIN"
