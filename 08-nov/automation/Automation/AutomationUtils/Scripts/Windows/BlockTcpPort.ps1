Function BlockTcpPort()
{$Port = "##Automation--port--##"
 $Time = "##Automation--time--##"
 $IsSql = "##Automation--issql--##"
 $Port = [int]$Port
 $Time = [int]$Time
 $Listener = [System.Net.Sockets.TcpListener]$Port
    Try
    {
     if($IsSql -eq 'yes')
    {
        Stop-Process -Name sql* -Force
        Start-Sleep -Seconds 10
     }
    $Listener.Start()
     Write-Host "Connected to Port - " $Port
     if($IsSql -eq 'yes')
     {
        Start-Service -Name 'MSSQL$COMMVAULT'
        Start-Sleep -Seconds 10
        Start-Service -Name 'SQLAgent$COMMVAULT'
        Start-Sleep -Seconds 10
        Start-Service -Name 'SQLBrowser'
        Start-Sleep -Seconds 10
        Start-Service -Name 'SQLTELEMETRY$COMMVAULT'
        Start-Sleep -Seconds 10
     }
     Start-Sleep -Seconds $Time
 }
    Catch {
     "Port binding failed with: `n" + $Error[0]
 }

 }
