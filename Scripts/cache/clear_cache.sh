#!/bin/bash

echo "SCRIPT TRIGGERED: $(date)" >> /var/log/squid/cron.log

/bin/systemctl stop squid
/bin/rm -rf /var/spool/squid/*
/usr/sbin/squid -z
/bin/systemctl start squid

echo "CACHE CLEARED SUCCESSFULLY: $(date)" >> /var/log/squid/cron.log