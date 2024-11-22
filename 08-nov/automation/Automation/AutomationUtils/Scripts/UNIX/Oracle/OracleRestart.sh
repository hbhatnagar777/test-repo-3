DB_UNIQUE_NAME=##Automation--db_unique_name--##
STARTUP_OPTION=##Automation--startup_option--##

create_script()
{
    srvctl stop database -d $1
    srvctl start database -d $1 -o $2
}

create_script $DB_UNIQUE_NAME $STARTUP_OPTION

