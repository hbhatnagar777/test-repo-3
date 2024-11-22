#!/bin/bash
#
#shell script to verify whether Scan Optimization was used successfully
#Output will be "success" if scan optimization was used correctly
#Usage : /share/VerifyDC.bash -logdir /var/log/commvault2/Log_Files -jobid 3859
#

STATUS="fail"
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

DCOK=`grep " $JOBID " $LOGDIR/FileScan*.log | grep "DC Scan Sucessfull"`
DCFAIL=`grep " $JOBID " $LOGDIR/FileScan*.log | grep "DataClassification cannot be used"`

if [ "$DCFAIL" = "" ]
then
	if [ "$DCOK" != "" ]
	then
		STATUS="success"
	fi
fi

echo $STATUS
