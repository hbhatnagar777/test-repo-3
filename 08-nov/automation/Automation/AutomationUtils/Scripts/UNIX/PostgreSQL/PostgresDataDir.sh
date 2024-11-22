BINDIR=##Automation--BINDIR--##
PASSWORD=##Automation--PASSWORD--##
PORT=##Automation--PORT--##

get_datadir()
{
	su - postgres -c "export PGPASSWORD=$2;$1/psql -p $3 -U postgres -c 'show data_directory;'" > /postgres_datadir
	data_dir=`sed -n '3p' /postgres_datadir`
	echo $data_dir
}

get_datadir $BINDIR $PASSWORD $PORT
