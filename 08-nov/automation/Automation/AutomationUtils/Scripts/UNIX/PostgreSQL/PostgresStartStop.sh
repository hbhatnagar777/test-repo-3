BINDIR=##Automation--BINDIR--##
DATADIR=##Automation--DATADIR--##
OPERATION=##Automation--OPERATION--##

server_check()
{
	su postgres -c "$1/pg_ctl -D $2 -m fast $3 > $2/start_server_log"
}

server_check $BINDIR $DATADIR $OPERATION
