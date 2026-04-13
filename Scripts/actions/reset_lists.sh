#!/bin/bash

FILE="/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt"

# Clear file safely
> "$FILE"

# Reload squid
sudo systemctl reload squid

echo "Blocked list cleared"