#!/bin/sh
OPERATION=##Automation--OPERATION--##
DBMCLIPATH=##Automation--DBMCLIPATH--##
HS=`hostname`
cmd="$OPERATION ""$HS"
data_ops()
{
if [[ $OPERATION == sdbfill* ]];
   then
        cmd="$OPERATION ""$HS"
        $cmd
   else
        $OPERATION
   fi
}
data_ops $OPERATION $OPERATION