#!/bin/bash
#
#shell script to return the number of nodes and streams used for a given distributed job on master node
#Sample Usage : GetNodeAndStreamCount.bash -logdir /var/log/commvault2/Log_Files -jobid 3859 -pkg Hadoop
#Sample Output: 3:6 (Where Nodes=3 and Streams=6)
#

LOGDIR=""
JOBID=0
PKG=""

#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below, -logdir, -jobid and -pkg are mandatory"
        echo "$0 -logdir /var/log/commvault/Log_Files -jobid 3859 -pkg Hadoop"
}

if [ "$1"x != "-logdir"x ]
then
        echo
        echo "*** \"-logdir\" is mandatory first argument."
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
        echo "*** \"-jobid\" is mandatory second argument."
        echo
        printUsage
        exit 1
fi

shift
JOBID=$1
shift

if [ "$1"x != "-pkg"x ]
then
        echo
        echo "*** \"-pkg\" is mandatory third argument."
        echo
        printUsage
        exit 1
fi

shift
PKG=$1

#Get the details from the last distributed report printed in the log
LOG_LINE=`grep -h " $JOBID " $LOGDIR/$PKG*.log | grep printReport | tail -1`
NODE_COUNT=`grep -h -A 100 "$LOG_LINE" $LOGDIR/$PKG*.log | grep "REPORT:  Node" | wc -l`
STREAM_COUNT=`grep -h -A 100 "$LOG_LINE" $LOGDIR/$PKG*.log | grep "REPORT:Stream" | wc -l`

#For TrueUp job, last report stream count will be zero for post-ops phase
#So get the details from the penultimate report if stream count is 0
if [ "$STREAM_COUNT"x == "0"x ]
then
        LOG_LINE=`grep -h " $JOBID " $LOGDIR/$PKG*.log | grep printReport | tail -2 | head -1`
        NODE_COUNT=`grep -h -A 100 "$LOG_LINE" $LOGDIR/$PKG*.log | grep "REPORT:  Node" | wc -l`
        STREAM_COUNT=`grep -h -A 100 "$LOG_LINE" $LOGDIR/$PKG*.log | grep "REPORT:Stream" | wc -l`
fi
echo $NODE_COUNT:$STREAM_COUNT