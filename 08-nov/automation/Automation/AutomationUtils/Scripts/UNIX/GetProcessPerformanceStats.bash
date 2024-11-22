#!/bin/bash
#
#shell script to collect performance stats for the unix process
#Usage Arguments : <PID list> <Output csv file path> <Counter header names> <Top command counter positions> <sleep interval>
#
#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below"
        echo "GetProcessPerformanceStats.bash <comma separated process ID list> <Output csv file path> <Counter header names> <Top command counter positions> <sleep interval>"
		echo "Supported Top command Counter position {Handle - 255 , Thread - 256 , Virtual bytes - 5 , working set Private - 6 , Working set - 7 , CPU usage- 9}"
}
if [ "$1"x = "-help"x ] || [ "$1"x = "-h"x ]
then
        printUsage
        exit 0
fi
pids=$1
csv=$2
header=$3
headercount=0
position=$4
sleeptime=$5
IFS=', ' read -r -a headerarray <<< $header
finalheader=""
for heading in "${headerarray[@]}"
do
if [[ $heading != "Time" ]]
then
IFS=', ' read -r -a processarray <<< $pids
for pid in "${processarray[@]}"
do
finalheader="${finalheader},${heading}_$pid"
done
fi
let "headercount++"
done
IFS=', ' read -r -a positionarray <<< $position
let "headercount--"
echo "Time$finalheader" >> $2
while true
do
datenow=$(date +"%F %I:%M:%S")
finaloutput=""
value=""
IFS=', ' read -r -a processarray <<< $pids
i=0
for pid in "${processarray[@]}"
do
	handle=0
	threads=0
	topcmd=$(top -w 1024 -b -n 1 -p $pid | awk 'NR>7 && NR<13' | tr -s [:space:] , | rev | cut -c 2- | rev)
	IFS=', ' read -r -a topoutput <<< $topcmd
	for pos in "${positionarray[@]}"
	do
		if [[ $pos -eq 255 ]]
		then
		handle=$(lsof -p $pid | wc -l)
		if [[ "$value" == "" ]]
		then
		value="$handle"
		else
		value="$value,$handle"
		fi
		continue
		fi
		if [[ $pos -eq 256 ]]
		then
		threads=$(ps -T -p $pid | wc -l)
		if [[ "$value" == "" ]]
		then
		value="$threads"
		else
		value="$value,$threads"
		fi
		continue
		fi
		let "pos--"
		out=${topoutput[$pos]}
		if [[ "$out" == *g ]]
		then
		out=$(echo $out | rev | cut -c 2- | rev)
		out=$(echo $out 1073741824 | awk '{printf "%4f\n", $1*$2}')
		out=$(echo ${out%.*})
		elif [[ "$out" == *m ]]
		then
		out=$(echo $out | rev | cut -c 2- | rev)
		out=$(echo $out 1048576 | awk '{printf "%4f\n", $1*$2}')
		out=$(echo ${out%.*})
		else
		if [[ $pos -eq 4 || $pos -eq 5 ||  $pos -eq 6 ]]
		then
		out=$(echo $out 1024 | awk '{printf "%4f\n", $1*$2}')
		out=$(echo ${out%.*})
		fi
		fi
		if [[ "$value" == "" ]]
		then
		value="$out"
		else
		value="$value,$out"
		fi
	done
let "i++"
done
if [ $i -gt 1 ]
then	
	IFS=', ' read -r -a output <<< $value
	for ((j=0;j<$headercount;j++))
	do
	finaloutput="$finaloutput,${output[$j]}"
		for ((p=1;p<$i;p++))
		do
		pindex=$headercount*$p
		jj=$j+$pindex
		finaloutput="$finaloutput,${output[$jj]}"
		done
	done
	finaloutput="$datenow$finaloutput"
else
finaloutput="$datenow,$value"
fi
echo $finaloutput >> $2
sleep $sleeptime
done