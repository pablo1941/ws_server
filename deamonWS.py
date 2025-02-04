#!/bin/bash
#######
service=WSServerPablo.py

if ps -ef | grep -v grep | grep $service ; then
 echo "$service is running!!!"
 exit 0
else

 echo "$service is NOT running!!!"
 #/home/dh_v2t7h7/logger.tagger-co.com/IoT/$service & 
 sudo python /var/www/html/ServiciosWS/$service >/dev/null & 
 exit 0
fi
