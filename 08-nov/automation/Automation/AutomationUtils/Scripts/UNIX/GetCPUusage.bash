#!/bin/bash
#set -x

#07/29/2016 16:32:57,99508,cvd,0.0,51,19M,0
#07/29/2016 16:32:57,45398,CvSyncProxy,0.0,12,109M,0

# automatic bash/ksh builtin, SECONDS. Shows how many seconds the script has been running
SECONDS=0

# top sample string ( 2 lines)
# PID   COMMAND %CPU TIME     #TH #WQ #PORTS MEM  PURG CMPRS PGRP PPID STATE    BOOSTS %CPU_ME %CPU_OTHRS UID FAULTS COW   MSGSENT MSGRECV SYSBSD SYSMACH CSW    PAGEINS IDLEW POWER USER #MREGS RPRVT VPRVT VSIZE KPRVT KSHRD
# 5756- cvd     0.0  00:07.94 38  0   89     71M  0B   0B    5756 1    sleeping *0[1]  0.00000 0.00000    0   30786  2784  1677    792     38937+ 1865    11542+ 24      6669+ 0.0   root N/A    N/A   N/A   N/A   N/A   N/A


# parameters - CS name, interval for sample, total time to run in minutes
CS=$1
typeset -i plsof
interval=$2
totaltime=$3
fileName=$5
#typeset -i pid
typeset -i npids        # numbrt of pids returned from a ps (should always be 1)
typeset -i proclen
typeset -i idx
typeset -i  mem
debug=0
idx=0                   # index to the number of precesses being checked, starts at zero, not one.

# make sure output files name specified
[[ "$fileName" == "" ]] && { echo "no output filename sepcified";exit 1; }

# remnove existing file, if there.
[[ -f $fileName ]] && rm -f $fileName>/dev/null

# who am i, used to eliminate myself from the command line when trying to get the prcesses.
mypid=$$
mynameis=$(basename -- $0)

[[ $debug == 1 ]] && echo "mypid=$mypid, mynameis=$mynameis"
#convert total time to run, to seconds from minutes
totaltime=$totaltime*60

#array of processes to check, if 4th paramter sent, set array to it, otherwise go default list
proclist=(cvd CvSyncProxy ifind clBackup)
[[ "$4" != "" ]] && proclist=($4)
[[ $debug == 1 ]] && echo "proclist -> ${proclist[*]}"

# get the number of elements in the array -1, since it starts at zero
proclen=${#proclist[@]}-1

#get pids of processes that are running or set pid to zero for that process, launch "top" in backgound for running processes

while (($SECONDS <= totaltime))
do
        idx=0
        pid="0"
        while (( $idx <= $proclen ))
        do

# debug if needed
                [[ $debug == 1 ]] && {
                        echo "proclist -> |${proclist[$idx]}|"
                        echo "pid= ps -fea | grep -v $mynameis 2>/dev/null | grep -v grep 2>/dev/null | grep -iw ${proclist[$idx]} 2>/dev/null | awk '{print $2}'"
                }
# we have to make a caveat between clBackupParent and clBackupChild, we only want the child process.
                [[ "${proclist[$idx]}" == "clBackup" ]] && {
                        pid=$(ps -fea | grep -v $mynameis 2>/dev/null | grep -v grep 2>/dev/null | grep -iw ${proclist[$idx]} 2>/dev/null | grep -i child | awk '{print $2}')

                } ||    #normal, eg not clBackup
                {
                        pid=$(ps -fea | grep -v $mynameis 2>/dev/null | grep -v grep 2>/dev/null | grep -iw ${proclist[$idx]} 2>/dev/null | awk '{print $2}')
                }
                npids=$(echo $pid | wc -w)

# if we have more than one pid returned, then we have an issue
# should be a single instance, single stream
# write the error, then assume nothing returned for this iteration for this process, by setting pid to zero.

                (( $npids > 1 )) &&  {

                        echo "$npids pids returned for ${proclist[$idx]}" >> /tmp/performanceCheckMultiPS.$mypid.log
                        echo "$pid" >> /tmp/performanceCheckMultiPS.$mypid.log
                        for e in $pid
                        do
                                ps -fp $e >> /tmp/performanceCheckMultiPS.$myplid.log
                        done
                        pid="0"
                }

# if zero pids are returned, then we can assume that processe is not running.

                (( $npids == 0 )) && pid="0"

# if pid !=0, then we can save and assume the process is running
# double check pid, if non-zero, get "top command" output, otheriwse zero out as zero pid means no process.

                [[ "$pid" != "0" ]] && {
                        pidlist[$idx]=$pid
                        ptop[$idx]=$(top -l 2 -s $interval -pid $pid | tail -1 | grep ${proclist[$idx]} &)
                } || pidlist[$idx]="0"
                [[ $debug == 1 ]] && echo ${proclist[$idx]},${pidlist[$idx]}
                idx=$idx+1
        done

# wait for any child process to finish, since "top" runs in the background
        wait

#07/29/2016 16:32:57,99508,cvd,0.0,51,19M,0
#07/29/2016 16:32:57,45398,CvSyncProxy,0.0,12,109M,0

# t1 - process name (example cvd)
# t2 - CPU time
# t3 - num threads
# t4 - memory usage
# plsof - number of open handles
# prefix - determine if value is in Bytes, MBytes, KBytes, Gbytes and adjust value

# construct and output the line for this interval.
        idx=0
        outline=""
        while (( $idx <= $proclen ))

        do
                [[ ${ptop[$idx]} != "" ]] && {
                        #echo ${ptop[$idx]}
                        t1=$(echo ${ptop[$idx]} | awk '{print($2)}')
                        tstamp=$(date "+%m/%d/%Y %H:%M:%S")
                        tmpt2=$(echo ${ptop[$idx]} | awk '{print($3)}')
                        t2=$(echo $tmpt2 | cut -f1 -d"/")
                        t3=$(echo ${ptop[$idx]} | awk '{print($5)}' | cut -d"/" -f1)    # only want left of "/" if value has "/" appended
                        t4=$(echo ${ptop[$idx]} | awk '{print($8)}')
                        prefix=${t4//[0-9]/}                    # get bytes/mb/kb/gb indicator (B/K/M/G)
                        prefix=$(echo $prefix | cut -c1)        # just get 1st char in case something appended
                        value=${t4//[!0-9]/}                    # get numeric portion
                        mem=value
                        [[ "$prefix" == "G" ]] && mem=$mem*10240000
                        [[ "$prefix" == "M" ]] && mem=$mem*1024000
                        [[ "$prefix" == "K" ]] && mem=$mem*102400
                        # get number of open files, approximate
                        plsof=$(lsof -p ${pidlist[$idx]} 2>/dev/null | wc -l)

                        [[ $debug == 2 ]] && {
                                echo "tstamp,idx,pidlist[idx],t1,t2,t4"
                                echo "$tstamp,$idx,${pidlist[$idx]},$t1,$t2,$t4"
                                #echo "$tstamp,$idx,${pidlist[$idx]},$t1,$t2,$t3,$t4,$mem,$prefix,$vaule,$plsof"
                        }

                        # construct output line
                        [[ "$idx" == "0" ]] && outline="$outline${tstamp},$t2" ||    # beggining of line (1st entry)
                                outline="$outline,$t2,$mem"                               # 2nd through "n" entries
                                #outline="$outline,${pidlist[$idx]},$t1,$t2,$t3,$mem,$plsof"                               # 2nd through "n" entries
                }  ||  outline="$(date "+%m/%d/%Y %H:%M:%S"),0"   # this means, the process in the array was not running, so default output
                ptop[$idx]=""
                idx=$idx+1
        done
        #echo $outline
        echo $outline>>$fileName

done

