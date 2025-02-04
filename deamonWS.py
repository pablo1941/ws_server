#!/bin/bash
#######
service=WSServerPablo.py

if ps -ef | grep -v grep | grep $service ; then
 echo "$service is running!!!"
 exit 0
else

 echo "$service is NOT running!!!"
 sudo python /var/www/html/$service >/dev/null & 
 exit 0
fi
