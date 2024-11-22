Function AttachDisksOci() {
    $disk_ips = "##Automation--disk_ips--##"
    $disk_iqs = "##Automation--disk_iqs--##"
    $disk_ips = $disk_ips -Split ','
    $disk_iqs = $disk_iqs -Split ','
    Set-Service -Name msiscsi -StartupType Automatic
    Start-Service msiscsi
    for($i = 0; $i -lt $disk_ips.length; $i++)
    {
        New-IscsiTargetPortal -TargetPortalAddress $disk_ips[$i]
        Connect-IscsiTarget -NodeAddress $disk_iqs[$i]  -TargetPortalAddress $disk_ips[$i] -IsPersistent $True -IsMultipathEnabled $True
        $diskNumber = $i + 1
        Set-Disk -Number $diskNumber -IsOffline $False
    }
}
