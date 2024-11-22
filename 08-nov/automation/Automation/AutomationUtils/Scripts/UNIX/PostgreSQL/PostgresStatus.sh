BINDIR=##Automation--BINDIR--##
DATADIR=##Automation--DATADIR--##
OPERATION=##Automation--OPERATION--##

server_check()
{
	echo `su postgres -c "$1/pg_ctl -D $2 status"`
}

server_check $BINDIR $DATADIR $OPERATION
