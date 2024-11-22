#!/bin/bash
#
#shell script to verify whether Scan Optimization was used successfully
#Output will be "success" if scan optimization was used correctly
#Usage : /share/VerifyDC.bash -logdir /var/log/commvault2/Log_Files -jobid 3859
#

STATUS="NOT_LISTED"
BASEDIR=""
VOLUME=""

#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below, -basedir and -volume are mandatory"
        echo "$0 -basedir /opt/commvault/Base -volume /netapp1"
}

if [ "$1"x != "-basedir"x ]
then
        echo
        echo "*** \"-basedir\" is mandatory first option."
        echo
        printUsage
        exit 1
fi

shift
BASEDIR=$1
shift

if [ "$1"x != "-volume"x ]
then
        echo
        echo "*** \"-volume\" is mandatory second option."
        echo
        printUsage
        exit 1
fi

shift
VOLUME=$1

VOLUMESTATE=`$BASEDIR/DcClient -getinfo|grep DATACLASS|grep $VOLUME| awk '{ if($1=="'"$VOLUME"'"){print $2}}'`

if [ "$VOLUMESTATE" = "" ]
then
	$BASEDIR/DcClient -edit REFRESH_PERIOD 60
	VOLUMESTATE=`$BASEDIR/DcClient -getinfo|grep DATACLASS|grep $VOLUME| awk '{ if($1=="'"$VOLUME"'"){print $2}}'`
fi

if [ "$VOLUMESTATE" != "" ]
then
	if [ "$VOLUMESTATE" = "UNMONITORED" ] || [ "$VOLUMESTATE" = "NOT_MONITORING" ]
	then
		STATUS="Some issue with volume monitoring please check your setup"
	else
		STATUS=$VOLUMESTATE
	fi
	
fi

echo $STATUS