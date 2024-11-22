Function GetProcessDump(){

    $process_id = "##Automation--process_id--##"
    $dump_path = "##Automation--dump_path--##"
    $file_name = "##Automation--file_name--##"

    $params = @{
        DumpFilePath = $PWD  # Default value when dump_path is empty or false
        DumpFileName = '%process_name%_%process_id%'  # Default value when file name is empty or false
    }

    if($dump_path){
        if(-not (Test-Path -Path $dump_path)){
            New-Item -ItemType Directory -Force -Path $dump_path | Out-Null
        }
        $params.DumpFilePath = $dump_path
    }

    if($file_name){
        $params.DumpFileName = $file_name
    }

    Get-Process -id $process_id | TakeProcessDump @params | Select-Object -Property FullName

}

function TakeProcessDump{

    [CmdletBinding()]
    Param (
        [Parameter(Position = 0, Mandatory = $True, ValueFromPipeline = $True)]
        [System.Diagnostics.Process]
        $Process,

        [Parameter(Position = 1)]
        [String]
        $DumpFilePath = $PWD,

        [Parameter(Position = 2)]
        [String]
        $DumpFileName = '%process_name%_%process_id%'
    )

    PROCESS
    {
        $ProcessId = $Process.Id
        $ProcessName = $Process.Name
        $ProcessHandle = $Process.Handle
        $ProcessFileName = $DumpFileName.Replace('%process_name%', $ProcessName)
        $ProcessFileName = $ProcessFileName.Replace('%process_id%', $ProcessId)
        $ProcessFileName = "$($ProcessFileName).dmp"

        $ProcessDumpPath = Join-Path $DumpFilePath $ProcessFileName

        $SystemDir = [Environment]::SystemDirectory
        $LibPath = "$($SystemDir)\comsvcs.dll"

        if(-not (Test-Path -Path $LibPath)){
            throw 'Unable to find comsvcs.dll library'
        }

        if (Test-Path -Path $ProcessDumpPath){
            try{
                Remove-Item $ProcessDumpPath -ErrorAction Stop
            }catch{}
        }

        $TempDump = $False
        $ToDumpPath = $ProcessDumpPath

        # We cannot pass a path with space to rundll32. So we dump the process to the drive root and move it later
        if($DumpFilePath -match " "){
            $TempDump = $True
            $DrivePath = Split-path -Path $ProcessDumpPath -Qualifier
            $ToDumpPath = Join-Path -Path $DrivePath -ChildPath $ProcessFileName
        }

        Powershell -c rundll32.exe $LibPath, MiniDump $ProcessId $ToDumpPath full

        if($LASTEXITCODE -ne 0){
            throw 'Unable to execute powershell dump command successfully'
        }else{

            if($TempDump){
                Move-Item -Path $ToDumpPath -Destination $ProcessDumpPath
            }

            Write-Host $ProcessDumpPath
        }

    }

    END {}
}