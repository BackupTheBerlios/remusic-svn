#!/bin/sh

case "$1" in
start)
	[ -x /usr/local/bin/remus_server ] && 
	/usr/local/bin/remus_server && 
	echo -n ' remus_server'
	;;
stop)
	[ -r /var/run/remus_server.pid ] && 
	kill $(cat /var/run/remus_server.pid && 
	echo -n ' remus_server'
	;;
*)
	echo "Usage: `basename $0` {start|stop}" >&2
	;;
esac

exit 0
