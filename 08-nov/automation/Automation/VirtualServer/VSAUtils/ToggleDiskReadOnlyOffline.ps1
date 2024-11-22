Function Main() {
    try {
        #initialize general varaibles
        $global:skip_os     = "##Automation--skip_os--##"
        $global:read_only   = "##Automation--read_only--##"
        $global:offline     = "##Automation--offline--##"
    }

    catch {
        write-host $Error[0]
        break
    }

    if ($global:read_only -eq "true"){
        $var1 = $true
    }
    else {
        $var1 = $false
    }

    if ($global:offline -eq "true"){
        $var2 = $true
    }
    else {
        $var2 = $false
    }

    if ($global:skip_os -eq "true") {
		# Properties will not be set for disk in which OS is installed
        $os_disk = Get-WmiObject -query "Select * from Win32_DiskPartition WHERE Bootable = True" | Select-Object DiskIndex
        $non_os_disks = Get-Disk | Where-Object {$_.Number -ne $os_disk.DiskIndex}
        $non_os_disks | ForEach-Object {
            Set-Disk $_.Number -IsReadOnly $var1
            Set-Disk $_.Number -IsOffline $var2
        }
    }

    else {
        $disks = Get-Disk
        $disks | ForEach-Object {
            Set-Disk $_.Number -IsReadOnly $var1
            Set-Disk $_.Number -IsOffline $var2
        }
    }
}