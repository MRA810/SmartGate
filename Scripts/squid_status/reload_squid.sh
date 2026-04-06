#!/bin/bash
# Usage: ./reload_squid.sh

sudo systemctl reload squid
echo "Squid reloaded"
