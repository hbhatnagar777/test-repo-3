#!/bin/bash

# Assign arguments to variables
logFilePath="##Automation--log_file--##"
startTimeString="##Automation--start_time--##"
endTimeString="##Automation--end_time--##"
searchPattern='##Automation--search--##'

# Convert start time and end time to seconds since epoch (Unix timestamp)
startTime=$(date -d "$startTimeString" +"%s")

# If endTimeString is empty, set endTime to the max value (equivalent of end of time)
if [ -z "$endTimeString" ]; then
    endTime=$(date -d "9999-12-31 23:59:59" +"%s")
else
    endTime=$(date -d "$endTimeString" +"%s")
fi

# Read the entire log file into an array
mapfile -t logLines < "$logFilePath"

# Initialize an array to store the filtered logs
filteredLogs=()

# Process the log file in reverse order by iterating over the array in reverse
for (( idx=${#logLines[@]}-1 ; idx>=0 ; idx-- )); do
    line="${logLines[idx]}"

    # Extract the date and time from the log line assuming the format "08/23 07:00:41"
    if [[ $line =~ [0-9]+[[:space:]]+[[:alnum:]]+[[:space:]]+([0-9]{2}/[0-9]{2})[[:space:]]+([0-9]{2}:[0-9]{2}:[0-9]{2}) ]]; then
        logDate="${BASH_REMATCH[1]}"
        logTime="${BASH_REMATCH[2]}"
        logDateTime=$(date -d "$logDate $logTime" +"%s")
        
        # Stop processing further if the log's DateTime is earlier than the start time
        if [ "$logDateTime" -lt "$startTime" ]; then
            break
        fi

        # Check if the log's DateTime falls within the specified range
        if [ "$logDateTime" -ge "$startTime" ] && [ "$logDateTime" -le "$endTime" ]; then
            # If searchPattern is not empty or if it matches the line
            if [ -z "$searchPattern" ] || echo "$line" | grep -Pq "$searchPattern"; then
                # Add the matching log line to the filteredLogs array
                filteredLogs+=("$line")
            fi
        fi
    fi
done

# Reverse the filtered logs array to maintain the original order
for (( idx=${#filteredLogs[@]}-1 ; idx>=0 ; idx-- )); do
    echo "${filteredLogs[idx]}"
done
