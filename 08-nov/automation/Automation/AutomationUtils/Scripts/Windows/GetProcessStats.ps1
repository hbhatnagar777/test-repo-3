Function GetProcessStats(){

    $process_id = "##Automation--process_id--##"

    $cpu_cores = (Get-WMIObject Win32_ComputerSystem).NumberOfLogicalProcessors

    Get-WmiObject Win32_PerfFormattedData_PerfProc_Process -filter "idprocess=$process_id" | ForEach-Object{
        $data = "handle_count=" + $_.HandleCount
        $data += ",memory=" + $_.WorkingSetPrivate
        $data += ",thread_count=" + $_.ThreadCount
        $data += ",cpu_usage=" + ($_.PercentProcessorTime/$cpu_cores)
        return $data
    }

}