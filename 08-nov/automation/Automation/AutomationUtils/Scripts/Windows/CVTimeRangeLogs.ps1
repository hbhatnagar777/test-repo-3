Function GetTimeRangeLogs() {
    $logFilePath = "##Automation--log_file--##"
    $startTimeString = "##Automation--start_time--##"
    $endTimeString = "##Automation--end_time--##"
    $searchPattern = '##Automation--search--##'

    $ErrorActionPreference = "Stop"
    try {
        # Convert the start time string to a DateTime object using a default year (e.g., 1900)
        $startTime = [datetime]::ParseExact($startTimeString, "MM/dd HH:mm:ss", $null)

        # If end time is provided, convert it to a DateTime object; otherwise, set it to max value
        if ($endTimeString) {
            $endTime = [datetime]::ParseExact($endTimeString, "MM/dd HH:mm:ss", $null)
        } else {
            $endTime = [datetime]::MaxValue
        }

        # Initialize an array to store the filtered logs
        $filteredLogs = @()

        $logLines = Get-Content $logFilePath

        if ($logLines) {
            [Array]::Reverse($logLines)

            # Process the log file in reverse order
            foreach ($line in $logLines) {
                # Assuming each log line starts with a timestamp like "08/23 07:00:41"
                if ($line -match " \d{2}/\d{2} \d{2}:\d{2}:\d{2} ") {
                    # Combine the date (MM/DD) and time, and parse it as a DateTime object using a default year
                    $logDateTime = [datetime]::ParseExact($matches[0].Trim(), "MM/dd HH:mm:ss", $null)

                    # Stop processing further if the log's DateTime is earlier than the start time
                    if ($logDateTime -lt $startTime) {
                        break
                    }

                    # Check if the log's DateTime falls within the specified range
                    if ($logDateTime -ge $startTime -and $logDateTime -le $endTime) {
                        # Add the matching log line to the filteredLogs array if it matches the search pattern (if provided)
                        if ([string]::IsNullOrEmpty($searchPattern) -or $line -match $searchPattern) {
                            $filteredLogs += $line
                        }
                    }
                }
            }
        }
        # Reverse the filtered logs to maintain original order
        if ($filteredLogs) {
            [Array]::Reverse($filteredLogs)
        }
        # Return the filtered logs
        return $filteredLogs
    }
    catch {
        Write-Host "ERROR: $_"
        exit 1
    }
    exit 0
}