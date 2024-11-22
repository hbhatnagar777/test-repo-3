ORACLE_HOME=##Automation--oracle_home--##
ORACLE_SID=##Automation--oracle_sid--##
REMOTE_FILE=##Automation--remote_file--##

create_script()
{
    export ORACLE_HOME=$1
    export ORACLE_SID=$2
    $1/bin/rman target / @$3
}

create_script $ORACLE_HOME $ORACLE_SID $REMOTE_FILE

