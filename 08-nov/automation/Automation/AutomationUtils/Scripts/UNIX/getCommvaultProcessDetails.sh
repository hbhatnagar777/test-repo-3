INSTANCE_NAME=##Automation--INSTANCE_NAME--##
JOB_ID=##Automation--JOB_ID--##
CVD_PATH=##Automation--CVD_PATH--##
get_datadir()
{
	#!/bin/bash
	/usr/bin/commvault list -instance $INSTANCE_NAME > /tmp/1234
	nu=`awk 'END {print NR}' /tmp/1234`
	#echo $nu > /tmp/12345
	json_op=`awk -v x=$nu 'BEGIN {print "{" } {if(NR>=6 && NR%2==0 && NR!=x)print "\""$2"\"" ":" $4(NR!=(x-2)?",":"")} END {print "}"} ' /tmp/1234`
	cat $CVD_PATH | grep -i "Launched process:" | grep -i "Pid=" | grep -i $JOB_ID > /tmp/1234
	rm -rf /tmp/123
	strindex() {    x="${1%%$2*}";   [[ "$x" = "$1" ]] && echo -1 || echo "${#x}"; }
	cat /tmp/1234 | while read LINE; do str1=`strindex "$LINE" "Process:"`; str2=`strindex "$LINE" "-j"`; str3=`echo $((str1+11))`; proc=`echo $LINE | cut -c$str3-$str2`; proc=`echo $proc | sed -e 's/^[ \t]*//'`;str4=`strindex "$LINE" "Pid="`; str4=`echo $((str4+4))`; pid=`echo ${LINE:$str4}`; echo \"$proc\":$pid >> /tmp/123; done
	x=`echo ${json_op::-1}`
	nu=`awk 'END {print NR}' /tmp/123`
	p=`awk -v x=$nu '{print $0}{if(NR!=x)print ","} END {print "}"} ' /tmp/123`
	echo "{" $p
}
get_datadir
