#!/bin/bash
counter=0
directory_path=##Automation--directory--##
size=##Automation--totalsize--##
fixed_filesize_kb=##Automation--filesize--##
prefix=##Automation--prefix--##
suffix=##Automation--suffix--##

if [[ $fixed_filesize_kb -gt 0 ]]
then
    size=$((size*1024))
fi

while [ $counter -le "$size" ]
do
	f_name=$(cat /dev/urandom | base64 | head -n 1 |tr -dc '[:alnum:]' |cut -c -20)
	if [[ fixed_filesize_kb -gt 0 ]]
    then
        f_size=$((fixed_filesize_kb))
        dd if=/dev/urandom of="$directory_path"/"$prefix$f_name$suffix" bs="$f_size"KiB count=1
    else
        f_size=$(($(cat /dev/urandom | base64 | head -n 1 |tr -dc '[:digit:]' |cut -c -1) +1))
	    dd if=/dev/urandom of="$directory_path"/"$prefix$f_name$suffix" bs="$f_size"MiB count=1
  fi
	counter=$((counter+f_size))
done
