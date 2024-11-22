#!/bin/bash
#
#shell script to collect performance stats for the unix client
#Usage Arguments : <Output csv file path> <Counter header names> <Top command counter positions> <sleep interval>
#
#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below"
        echo "GetMachinePerformanceStats.bash <Output csv file path> <Counter header names> <Top command counter positions> <sleep interval>"
		echo "Supportted Top command Counter position values {CPU usage - 2 , Available memory - 37 , Free Memory - 23 , load Average - 355}"
}
if [ "$1"x = "-help"x ] || [ "$1"x = "-h"x ]
then
        printUsage
        exit 0
fi
csv=$1
header=$2
position=$3
sleeptime=$4
IFS=', ' read -r -a positionarray <<< $position
echo $header >> $1
while true
do
datenow=$(date +"%F %X")
finaloutput=""
value=""
topcmd=$(top -w 1024 -b -n 1 | awk 'NR>2 && NR<6' | tr -s [:space:] ,)
IFS=', ' read -r -a topoutput <<< $topcmd
for pos in "${positionarray[@]}"
	do
	out=""
	if [[ $pos -eq 23 ]]
		then
		out=$(echo ${topoutput[$pos]})
		topoutput[$pos]=$(echo ${out%.*})
		fi
	if [[ $pos -eq 37 ]]
		then
		out=$(echo ${topoutput[$pos]})
		topoutput[$pos]=$(echo ${out%.*})
		fi
	if [[ $pos -eq 355 ]]
	then
	out=$(top -w 1024 -b -n 1 | grep -w "load average" | tr -s [:space:] ,)
	IFS=', ' read -r -a loadarray <<< $out
	out=${loadarray[${#loadarray[@]} - 1]}
	else
	let "pos--"
	out=${topoutput[$pos]}
	fi	
	if [[ "$value" == "" ]]
		then
		value=$out
		else
		value="$value,$out"
		fi
	done
finaloutput="$datenow,$value"
echo $finaloutput >> $1
sleep $sleeptime
done