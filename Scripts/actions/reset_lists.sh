#!/bin/bash
sudo truncate -s 0 /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/blocked_sites.txt
sudo truncate -s 0 /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/whitelist.txt
sudo systemctl reload squid
echo "All block/unblock lists cleared"
