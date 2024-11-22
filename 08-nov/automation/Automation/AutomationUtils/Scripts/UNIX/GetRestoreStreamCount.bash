#!/bin/bash
#
#shell script to return the number of streams used for given restore job id
#Usage : /share/GetRestoreStreamCount.bash -logdir /var/log/commvault2/Log_Files -jobid 3859
#

LOGDIR=""
JOBID=0

#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below, -logdir and -jobid are mandatory"
        echo "$0 -logdir /var/log/commvault/Log_Files -jobid 3859"
}

if [ "$1"x != "-logdir"x ]
then
        echo
        echo "*** \"-logdir\" is mandatory first option."
        echo
        printUsage
        exit 1
fi

shift
LOGDIR=$1
shift

if [ "$1"x != "-jobid"x ]
then
        echo
        echo "*** \"-jobid\" is mandatory second option."
        echo
        printUsage
        exit 1
fi

shift
JOBID=$1

grep " $JOBID " $LOGDIR/clRestore*.log | grep "File Statistics" | wc -l
