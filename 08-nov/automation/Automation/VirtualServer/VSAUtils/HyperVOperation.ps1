Function Main()
{

function CreateSnap($snap)
{
$Error.Clear()
$status = -1
$create = CheckPoint-VM -ComputerName $global:Server -VMName $global:VMName -Snapshotname $snap
if(!$Error)
{
sleep(10)
$status = 0
}
return $status
} 

function DeleteSnap($snap)
{
$Error.Clear()
$status = -1
$delete = Remove-VMSnapshot -ComputerName $global:Server -VMName $global:VMName -Name $snap
if(!$Error)
{
sleep(10)
while($count -lt 3)
{
$ip = (get-vm -Name $global:VMName -ComputerName $global:Server | select -ExpandProperty networkadapters).ipaddresses
if($ip)
{
$status = 0
break
}
else
{
$count = $count+1
write-host "retrying for IP"
$status = -1
}
}
}
else
{
Write-Host "Cannot Delete snapshot with error $reterr"
$status = -1
}
return $status
}

function RevertSnap($snap)
{
$count = 0
$error.clear()
$revert = Restore-VMSnapshot -Name $snap -VMName $global:VMName -ComputerName $global:Server -Confirm:$false
if(!$error)
{
sleep(10)
while($count -lt 3)
{
$ip = (get-vm -Name $global:VMName -ComputerName $global:Server | select -ExpandProperty networkadapters).ipaddresses
if($ip)
{
$status = 0
break
}
else
{
$count = $count+1
write-host "retrying for IP"
$status = -1
}
}
}
else
{
Write-Host "Cannot revert snapshot with error $reterr"
$status = -1
}
return $status
}

function PowerOn($OsVersion)
{
if(($global:VM).EnabledState -ne 2 )
{
try
{
Start-VM -Name ($global:VMName)
Write-host "Success"
sleep(120)
return 0
}
catch
{
Write-Warning "Error occured: $_"
return 1
}}
else
{
Write-host "Success"
return 0
}}

function PowerOff($OsVersion)
{
if(($global:VM).EnabledState -eq 3){
Write-host "Success"
return 0
}
if(($global:VM).EnabledState -eq 2 )
{
try
{
Stop-VM -Name ($global:VMName)
Write-host "Success"
return 0
}
catch
{
Write-Warning "Error occured: $_"
return 1
}}}

function MigrateVM()
{
Move-ClusterVirtualMachineRole $global:VMName
}

function Merge($OsVersion,$BaseVHDName)
{
try
{
Merge-VHD -path $global:VHDName -DestinationPath $BaseVHDName
return 0
}
catch
{
return -1
}
}

function delvm()
{
	
	if($global:VM -ne $null)
	{
		$VSMgtService = get-wmiobject -class "Msvm_VirtualSystemManagementService" -namespace "root\virtualization"  
		$result = $VSMgtService.DestroyVirtualSystem($global:VM) 
        $job=[WMI]$result.job
	 
		if($result.ReturnValue -eq 4096)
		{
           $errcode =  WaitforJobtoFinish $job
		}
		
		return $errcode
	}
}

function WaitforJobtoFinish($job)
{
while($job.jobstate -lt 7){$job.get()} 
return $job.ErrorCode 
}

function newstate($newState)
{
	
	if($global:VM-ne $null)
	{

		$result = $vm.RequestStateChange($newState) 
	 
	  	$job=[WMI]$result.job

		while ($job.JobState -eq 3 -or $job.JobState -eq 4)
		{
			write-host $job.PercentComplete "% complete"
			start-sleep 1
			$job=[WMI]$result.job
		}
	 
		if($result.ReturnValue -eq 4096)
		{
           $errcode =  WaitforJobtoFinish $job
		}
		
		return $errcode
	}
}

function DeleteOldHostVM
{

newstate 3
sleep 7
if($global:VM -ne $null -and $global:VM.EnabledState -eq 2)
{
	newstate 3
	sleep 7
	delvm
	return 0
}

if($global:VM -ne $null -and $global:VM.EnabledState -eq 3)
{	
	$flag = newstate 2
	
	if($flag -eq 0)
	{	
		newstate 3
		
		sleep 7
		delvm
		return 0
	}
	else
	{
		sleep  7
		delvm
		return 1
	}
}
 
#Unknown state
if($global:VM -eq $null -or ($global:VM.EnabledState -ne 2 -and $global:VM.EnabledState -ne 3))
{
	return 1
}
}
function Delete($OsVersion)
{
if($OsVersion -imatch "2008")
{
$result = DeleteOldHostVM
return $result
}
else
{
Stop-VM -VMName $global:VMName -TurnOff:$True -Force
sleep(1)
GET-VM -VMName $global:VMName | GET-VMHardDiskDrive | Foreach { Remove-Item -path $_.Path -Recurse -Force -Confirm:$False}
sleep(1)
Remove-VM -VMName $global:VMName -force
Write-Host "Success"
return 0
}
}

function SetVmProcessor($processorcount)
{

Stop-VM -VMName $global:VMName -TurnOff:$True -Force
sleep(1)
Set-VMProcessor -VmName $global:VMName -Count $processorcount
Write-Host "Success"
return $processorcount


}

function SetVmMemory($memory)
{

Stop-VM -VMName $global:VMName -TurnOff:$True -Force
sleep(1)
Set-VMMemory $global:VMName -DynamicMemoryEnabled $true -StartupBytes ($memory*1024*1024)
Write-Host "Success"
return $memory


}

function Checkdriveletter()
{
try
{
$regex = ".*[a-zA-Z]+.*"
$Result = Mount-VHD $global:VHDName -passthru
$drive = (Get-DiskImage -ImagePath $global:VHDName | Get-Disk | Get-Partition).DriveLetter
if($drive -match $regex)
{
Write-Host "Driveletter got assigned"
$arr = $drive -split ' '
foreach ($drivelet in $arr) {
$driveletter = $drivelet +","+$driveletter
}
$driveletter = $driveletter.TrimEnd(",")
Write-Host "DriveLetter="$driveletter
Write-Host "Success"
return 0
}
else
{
write-Host "Checking if disk is online"
SetDiskOnline
write-Host "Assigning Driveletter"

$driveletter = ""
$num = (Get-Disk |Where-Object {$_.FriendlyName -Eq "Microsoft Virtual Disk"}).Number
$partiionlist = (Get-Partition -DiskNumber $num).PartitionNumber
foreach($eachpartition in $partiionlist)
{
$partitionDriveletter = (Get-Partition -DiskNumber $num -PartitionNumber $eachpartition).DriveLetter
if($partitionDriveletter -match $regex)
{
$driveletter = $partitionDriveletter +","+$driveletter
}
else
{
$drive = AssignDriveletter $num $eachpartition
$driveletter = $drive +","+$driveletter
}
}
$driveletter = $driveletter.TrimEnd(",")
Write-Host "DriveLetter="$driveletter
Write-Host "Success"
return 0
}
}
catch
{
$ErrorMessage = $_.Exception.Message
$FailedItem = $_.Exception.ItemName
write-Host $ErrorMessage
write-Host $FailedItem
}
}

function AssignDriveletter($DiskNumber,$partitionnum)
{
$AllLetters = 65..90 | ForEach-Object {[char]$_ + ":"}
$UsedLetters = get-wmiobject win32_logicaldisk | select -expand deviceid
$FreeLetters = $AllLetters | Where-Object {$UsedLetters -notcontains $_}
$driveletter = ($FreeLetters | select-object -last 1).split(":")[0]
Get-Partition -DiskNumber $DiskNumber -PartitionNumber $partitionnum | Set-Partition -NewDriveLetter $driveletter
return $driveletter
}

function SetDiskOnline()
{
$num = $null

$num = (Get-Disk | where-object IsOffline -ieq $True | Where-Object {$_.FriendlyName -Eq "Microsoft Virtual Disk"}).Number
if (-Not([string]::IsNullOrWhiteSpace($num)))
{
       Set-Disk -Number $num -IsOffline $False
}
}

function ChangeExtension()
{

$Extn = [IO.Path]::GetExtension($global:VHDName)
$fileBaseName = (Get-Item $global:VHDName).Basename
$fileDirectoryName = (Get-Item $global:VHDName).DirectoryName
$Filewithoutextn = join-path $fileDirectoryName  $fileBaseName

if($Extn -ieq ".avhd")
{
$Newfilename = $Filewithoutextn+".vhd"
Rename-Item $global:VHDName $Newfilename
$global:VHDName = $Newfilename
}
elseif($Extn -ieq ".avhdx")
{
$Newfilename = $Filewithoutextn+".vhdx"
Rename-Item $global:VHDName $Newfilename
$global:VHDName = $Newfilename
}
return $OldFileName
}

function DriveSize
{
$size = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='$global:ExtraArgs'" | Select @{Name="Size";Expression={[math]::Round($_.Size/1MB,2)}}
$size = $size.Size
Write-Host "DriveSize="$size
}

function MountVHD($OsVersion)
{

$OldFileName = ChangeExtension

if($OsVersion -imatch "2008")
{

$Result = $global:VHDService.Mount($global:VHDName)
return 0
}
else
{

$Vhdmount = Checkdriveletter $global:VHDName
}


if($Vhdmount -eq 0)
{
write-Host "Success"
return 0
}

else
{
Write-Host "issue in bringing Device online"
}
}

function UnMountVHD
{
[CmdletBinding()]
param (
[string]$OsVersion,
[string]$rename = "true"
)

$OldFileName = ''
if($rename -imatch "true")
{
$BaseName = $global:VHDName.Substring(0, $global:VHDName.LastIndexOf('.'))
$Extn = $global:VHDName.Split(".")[1]

if($Extn -ieq "avhd")
{
$Newfilename = $BaseName+".vhd"
$OldFileName = $global:VHDName
$global:VHDName = $Newfilename
}
elseif($Extn -ieq "avhdx")
{
$Newfilename = $BaseName+".vhdx"
$OldFileName = $global:VHDName
$global:VHDName = $Newfilename
}
}

if($OsVersion -imatch "2008")
{

$Result = $global:VHDService.Unmount($global:VHDName)
Write-host "Success"
if (-Not([string]::IsNullOrWhiteSpace($OldFileName)))
{
Rename-Item $global:VHDName $OldFileName
}
return 0
}
elseif($OsVersion -imatch "2012 Standard")
{
Dismount-VHD -Path $global:VHDName
Write-host $Result
Write-host "Success"
if (-Not([string]::IsNullOrWhiteSpace($OldFileName)))
{
Rename-Item $global:VHDName $OldFileName
}
return 0
}
else
{
$testmount = Get-DiskImage -ImagePath $global:VHDName | Get-Disk | Get-Partition
if (-Not([string]::IsNullOrWhiteSpace($testmount)))
{
Dismount-VHD -Path $global:VHDName
Write-host $Result
Write-host "Success"
if (-Not([string]::IsNullOrWhiteSpace($OldFileName)))
{
Rename-Item $global:VHDName $OldFileName
}
return 0
}
else
{
return 0
}}}


#Initialize
$global:Server = "##Automation--server_name--##"
$global:VMName = "##Automation--vm_name--##"
$global:operation= "##Automation--operation--##"
[string]$global:VHDName = "##Automation--vhd_name--##"
[string]$global:ExtraArgs = "##Automation--extra_args--##"
$ErrorActionPreference = "Stop"
$VerbosePreference = "SilentlyContinue"
$NameSpace =  "root\virtualization\v2"
$OsVersion = (Get-WmiObject -class Win32_OperatingSystem -computername $global:Server).caption
write-host $global:VHDName

if($OsVersion -imatch "2008")
{
$NameSpace =  "root\virtualization"
}

$VMs = Get-WmiObject -Class Msvm_ComputerSystem -Namespace $NameSpace -ComputerName $global:Server

$global:VM = $VMs | where-object {$_.elementname -eq $global:VMName}

$global:VHDService = get-wmiobject -class "Msvm_ImageManagementService" -namespace $NameSpace -computername "."

if($operation -ieq "Merge")
{
$BaseVHDName = $global:ExtraArgs
$var1 = &$global:operation $OsVersion $BaseVHDName
}
elseif($operation -ieq "DeleteSnap")
{
$snapname = $global:ExtraArgs
$var1 = &$global:operation $snapname 
return $var1
}

elseif($operation -ieq "RevertSnap")
{
$snapname = $global:ExtraArgs
$var1 = &$global:operation $snapname 
return $var1
}

elseif($operation -ieq "CreateSnap")
{
$snapname = $global:ExtraArgs
$var1 = &$global:operation $snapname 
return $var1
}

elseif($operation -ieq "DeleteSnap")
{
$snapname = $global:ExtraArgs
$var1 = &$global:operation $snapname
return $var1
}

elseif($operation -ieq "SetVmProcessor"){

[Int]$processorcount = $global:ExtraArgs
$var1 = &$global:operation $processorcount
return $var1

}

elseif($operation -ieq "SetVmMemory"){

[Int]$memory = $global:ExtraArgs
$var1 = &$global:operation $memory
return $var1
}

else
{
$var1 = &$global:operation $OsVersion 
return $var1
}
}

