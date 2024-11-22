#!/bin/sh
OPERATION=##Automation--OPERATION--##
INSTANCE=##Automation--INSTANCE--##
DB_USER=##Automation--USERNAME--##
DB_PASSWORD=##Automation--PASSWORD--##
DBA_USER=##Automation--DBA_USER--##
DBA_PASSWORD=##Automation--DBA_PASSWORD--##
DBMCLI_PATH=##Automation--DBMCLIPATH--##
FULL_MEDIUM=##Automation--FULL_MEDIUM--##
INC_MEDIUM=##Automation--INC_MEDIUM--##
LOG_MEDIUM=##Automation--LOG_MEDIUM--##

HS=`hostname`

server_check()
{
    export PATH=$DBMCLI_PATH:$PATH
    if [ $OPERATION == "status" ]
    then
        DB_STATE=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD db_state | sed -n -e 3p`
        if [ ${PIPESTATUS[0]} -ne 0 ] && [ ${PIPESTATUS[1]} -ne 0 ]
        then
                echo "Database state is not valid to run backups ${PIPESTATUS[0]} ${PIPESTATUS[1]}"
        else
                echo $DB_STATE
        fi
    fi
    if [ $OPERATION == "db_online" ]
    then
        CHG_STATE=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c db_online`

        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Unable to change Database state to online Out put: ${PIPESTATUS[0]} "
        else
                echo $CHG_STATE
        fi
    fi
    if [ $OPERATION == "db_admin" ]
    then
        CHG_STATE=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c db_admin`

        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Unable to change Database state to admin Out put: ${PIPESTATUS[0]} "
        else
                echo $CHG_STATE
        fi
    fi
    if [ $OPERATION == "online_full" ]
    then
        BKP_STATUS=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $FULL_MEDIUM recovery`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Database state is not valid to run backups "${PIPESTATUS[0]}""
        else
                echo $BKP_STATUS
        fi
    fi
    if [ $OPERATION == "online_inc" ]
    then
        BKP_STATUS=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $INC_MEDIUM recovery`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Database state is not valid to run backups ${PIPESTATUS[0]}"
        else
                echo $BKP_STATUS
        fi
    fi
    if [ "$OPERATION" == "offline_full" ]
    then
        BKP_STATUS=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $FULL_MEDIUM migration`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Database state is not valid to run backups ${PIPESTATUS[0]}"
        else
                echo $BKP_STATUS
        fi
    fi
    if [ "$OPERATION" == "offline_inc" ]
    then
        BKP_STATUS=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $INC_MEDIUM migration`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Database state is not valid to run backups ${PIPESTATUS[0]}"
        else
                echo $BKP_STATUS
        fi
    fi
    if [ $OPERATION == "log_bkp" ]
    then
        BKP_STATUS=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $LOG_MEDIUM`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
                echo "Database state is not valid to run backups ${PIPESTATUS[0]}"
        else
                echo $BKP_STATUS
        fi
    fi
    if [ $OPERATION == "get_medium" ]
    then
        GET_MEDIUM=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
               echo "Database state is not valid to medium ${PIPESTATUS[0]}"
        else
                DATA=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall | grep PIPE | grep DATA | sed 's/\\\\.*//' | head -n 1`
                PAGES=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall | grep PIPE | grep PAGES | sed 's/\\\\.*//' | head -n 1`
                LOG=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall | grep PIPE | grep LOG | sed 's/\\\\.*//' | head -n 1`
                echo $DATA/$PAGES/$LOG
        fi
	  fi
	  if [ $OPERATION == "GetBackupExtIDs" ]
    then
        DATA=`dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c param_directget RunDirectoryPath | grep RunDirectoryPath | awk '{print $2}'`
        if [ ${PIPESTATUS[0]} -ne 0 ]
        then
               echo "Database state is not valid to medium ${PIPESTATUS[0]}"
        else
                DATA="$DATA""/dbm.ebf"
                echo $DATA
        fi
   fi


}

server_check $OPERATION $INSTANCE $DB_USER $DB_PASSWORD

