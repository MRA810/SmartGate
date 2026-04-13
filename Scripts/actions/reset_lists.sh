#!/bin/bash
sudo truncate -s 0 /home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt
sudo truncate -s 0 /home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/whitelist.txt
sudo systemctl reload squid
echo "All block/unblock lists cleared"
