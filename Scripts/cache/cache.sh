sudo awk '{print $4}' /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/Scripts/cache/log/readable.log | sort -u > urls.txt
wget -i urls.txt
