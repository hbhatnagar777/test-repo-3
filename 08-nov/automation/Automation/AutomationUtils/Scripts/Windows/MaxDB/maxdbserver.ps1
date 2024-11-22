param (
    [string]$DBMCLI_PATH,
    [string]$INSTANCE,
    [string]$DB_USER,
    [string]$DB_PASSWORD,
    [string]$DBA_USER,
    [string]$DBA_PASSWORD,
    [string]$OPERATION,
    [string]$FULL_MEDIUM,
    [string]$INC_MEDIUM,
    [string]$LOG_MEDIUM
)

$env:PATH="$DBMCLI_PATH;$env:PATH"

If ($OPERATION -eq "status") {
    $DB_STATE = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD db_state | Select-Object -Index 2
    Write-Output $DB_STATE
}

If ($OPERATION -eq "db_online") {
    $CHG_STATE = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c db_online
    Write-Output $CHG_STATE
}

If ($OPERATION -eq "db_admin") {
    $CHG_STATE = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c db_admin
    Write-Output $CHG_STATE
}

If ($OPERATION -eq "online_full") {
    $BKP_STATUS = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $FULL_MEDIUM recovery
    Write-Output $BKP_STATUS
}

If ($OPERATION -eq "online_inc") {
    $BKP_STATUS = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $INC_MEDIUM recovery
    Write-Output $BKP_STATUS
}

If ($OPERATION -eq "offline_full") {
    $BKP_STATUS = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $FULL_MEDIUM migration
    Write-Output $BKP_STATUS
}

If ($OPERATION -eq "offline_inc") {
    $BKP_STATUS = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $INC_MEDIUM migration
    Write-Output $BKP_STATUS
}

If ($OPERATION -eq "log_bkp") {
    $BKP_STATUS = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -uUTL -c backup_start $LOG_MEDIUM
    Write-Output $BKP_STATUS
}

If ($OPERATION -eq "get_medium") {
    $DATA = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall | Select-String -Pattern "PIPE" | Select-String -Pattern "DATA" | ForEach-Object { $_.Line -replace '\\.*', '' }
    $PAGES = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall | Select-String -Pattern "PIPE" | Select-String -Pattern "PAGES" | ForEach-Object { $_.Line -replace '\\.*', '' }
    $LOG = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c medium_getall | Select-String -Pattern "PIPE" | Select-String -Pattern "LOG" | ForEach-Object { $_.Line -replace '\\.*', '' }
    Write-Output "$DATA/$PAGES/$LOG"
}

If ($OPERATION -eq "GetBackupExtIDs") {
    $DATA = & dbmcli -d $INSTANCE -u $DB_USER,$DB_PASSWORD -c param_directget RunDirectoryPath | Select-String -Pattern "RunDirectoryPath" | ForEach-Object { $_.Line.Split()[1] }

    if ($LASTEXITCODE -ne 0) {
        Write-Output "Database state is not valid to medium $LASTEXITCODE"
    } else {
        $DATA = "$DATA/dbm.ebf"
        Write-Output $DATA
    }
}
