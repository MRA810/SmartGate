sudo awk '{print $4}' /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/readable.log | sort -u > /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/urls.txt
wget -i /home/mra/Desktop/Coding_Nerdy_Stuff/SmartGate/proxy/urls.txt
