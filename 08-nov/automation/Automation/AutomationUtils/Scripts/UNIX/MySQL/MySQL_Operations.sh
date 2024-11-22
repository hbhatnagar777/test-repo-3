BINDIR=##Automation--BINDIR--##
USERNAME=##Automation--USERNAME--##
PASSWORD=##Automation--PASSWORD--##
SOCKFILE=##Automation--SOCKFILE--##
OPERATION=##Automation--OPERATION--##

server_check()
{	
	if [ $OPERATION != "port" ]
	then
	$BINDIR/mysqladmin -u$USERNAME -p$PASSWORD $OPERATION --socket=$SOCKFILE 2> /dev/null
	fi
	
	if [ $OPERATION == "port" ]
	then
	a=`netstat -lnp | grep LISTENING | grep $SOCKFILE | awk 'match($0,/([0-9]*\/)mysqld/) {print substr($0,RSTART,RLENGTH)}'`
	netstat -tlnp | grep LISTEN | grep $a | awk 'BEGIN{x=65536}; /mysql*/ {n=split($(NF-3),a,":")}; a[n]<x{x=a[n]}; END{print x}'
	fi
	
}

server_check $BINDIR $USERNAME $PASSWORD $SOCKFILE $OPERATION
