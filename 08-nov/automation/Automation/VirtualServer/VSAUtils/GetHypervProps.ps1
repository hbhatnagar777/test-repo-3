Function Main()
{
#initialize general varaibles
$global:Server = "##Automation--server_name--##"
$global:vmName = "##Automation--vm_name--##"
$global:property= "##Automation--property--##"
[string]$global:ExtraArgs = "##Automation--extra_args--##"
$WarningPreference = "SilentlyContinue"
$protocol = "https"
$global:NameSpace =  "root\virtualization\v2"


$global:OsVersion = (Get-WmiObject -class Win32_OperatingSystem -computername $global:Server).caption

if($global:OsVersion -imatch "2008")
{
$global:NameSpace =  "root\virtualization"
}

$vms = Get-WmiObject -Class Msvm_ComputerSystem -Namespace $NameSpace -ComputerName $global:Server


if($vmName -ne ""){

$global:vm = $vms | where-object {$_.elementname -eq $global:vmName}

}

if($global:Property -eq "All")
{
$var1 = no_of_disks
$var2 = power_state
$var3,$var11 = nic
$var4 = memory
$var5 = no_of_cpu
$var7 = guid
$var8 = guest_os
$var9 = ip
$var12 = disk_path
$var13 = version
$var14 = GetVMFilesPath
$var15 = VMSnapshot
$var16 = Generation
$var17 = config_version

write-host "disk_count="$var1";power_state="$var2";NicName="$var3";memory="$var4";no_of_cpu="$var5";guid="$var7";guest_os="$var8";ip="$var9";nic_count="$var11";disk_path="$var12";version="$var13";VMFilesPath="$var14";VMSnapshot="$var15";Generation="$var16";config_version="$var17
}

elseif($global:Property -eq "Basic")
{
$var1 = guid
$var2 = power_state
$var3 = guest_os
$var4 = memory
$var5 = no_of_cpu
$var6 = no_of_disks
$var7,$var8 = nic
$var9 = VMSnapshot
$var10 = ip
$var11 = config_version

write-host "guid="$var1";power_state="$var2";guest_os="$var3";memory="$var4";no_of_cpu="$var5";disk_count="$var6";NicName="$var7";nic_count="$var8";VMSnapshot="$var9";ip="$var10";config_version="$var11
}
elseif($global:Property -eq "Vhdx" ){

$vhdx  = getVhdx
write-host $vhdx

}

else
{
if($global:property -ieq "DiskType")
{
$type,$num,$location = $global:ExtraArgs.Split(",")
$var10 = &$global:Property $type $num $location
}
else
{
$var10 = &$global:Property
}
write-host $global:Property"="$var10
}
}

function no_of_disks()
{

$idecount=0
$scsicount=0
$ides=get-vm $global:vmName -ComputerName $global:Server| get-vmharddiskdrive
foreach($ide in $ides)
{
if($ides.controllertype -match 'IDE')
{
$idecount=$idecount+1

}
else
{
$scsicount=$scsicount+1
}
}
#write-host "ide controller: $idecount"
#write-host "scsi controller: $scsicount"
return $scsicount + $idecount

}

function getVhdx()
{

$details = "{ "
$alldisks = Get-VMHardDiskDrive -VMName $global:vmName
Foreach($eachdisk in $alldisks)
{ $Cont = $eachdisk.ControllerType
  $number= $eachdisk.ControllerNumber
  $location= $eachdisk.ControllerLocation
  $eachdisk = Get-VHD $eachdisk.Path
  while($eachdisk.ParentPath)
    {
     $eachdisk = Get-VHD $eachdisk.ParentPath
    }
$details =$details + "'" + $Cont+$number+$location +"': ['"+$eachdisk.Path+"'"+",'"+$eachdisk.VhdType+"' ],"
}
return $details.TrimEnd(',')+" }"
}

function DiskType($type,$num,$loc)
{
$disk_path = (Get-VM -Name $global:vmName -ComputerName $global:Server | Get-VMHardDiskDrive -ControllerType $type -ControllerNumber $num -ControllerLocation $loc).Path
return $disk_path
}


function guest_os()
{
filter Import-CimXml
{
	$CimXml = [Xml]$_
	$CimObj = New-Object -TypeName System.Object
	foreach ($CimProperty in $CimXml.SelectNodes("/INSTANCE/PROPERTY[@NAME='Name']"))
      {
         $CimObj | Add-Member -MemberType NoteProperty -Name $CimProperty.NAME -Value $CimProperty.VALUE
      }

   foreach ($CimProperty in $CimXml.SelectNodes("/INSTANCE/PROPERTY[@NAME='Data']"))
      {
         $CimObj | Add-Member -MemberType NoteProperty -Name $CimProperty.NAME -Value $CimProperty.VALUE
      }
        $CimObj
}
try
{
$VMConf = Get-WmiObject -ComputerName $global:Server -Namespace "root\virtualization\v2" -Query "SELECT * FROM Msvm_ComputerSystem WHERE ElementName like '$global:vmName' AND caption like 'Virtual%' "
$KVPData = Get-WmiObject -ComputerName $global:Server -Namespace "root\virtualization\v2" -Query "Associators of {$VMConf} Where AssocClass=Msvm_SystemDevice ResultClass=Msvm_KvpExchangeComponent"
$KVPExport = $KVPData.GuestIntrinsicExchangeItems
}
catch
{
$VMConf = Get-WmiObject -ComputerName $Server -Namespace "root\virtualization" -Query "SELECT * FROM Msvm_ComputerSystem WHERE ElementName like '$global:vmName' AND caption like 'Virtual%' "
$KVPData = Get-WmiObject -ComputerName $Server -Namespace "root\virtualization" -Query "Associators of {$VMConf} Where AssocClass=Msvm_SystemDevice ResultClass=Msvm_KvpExchangeComponent"
$KVPExport = $KVPData.GuestIntrinsicExchangeItems
}


if ($KVPExport)
{
	# Get KVP Data
	$KVPExport = $KVPExport | Import-CimXml

	# Get Guest Information
	$VMOSName = ($KVPExport | where {$_.Name -eq "OSName"}).Data
}
else
{
	$VMOSName = "Unknown"
}

if($VMOSName -like '*Win*' -or $VMOSName -imatch "Unknown")
{
return "Windows"
}
else
{
return "Unix"
}
}


Function DISKSIZE()
{
$disksize = ""
$disk=Get-WMIObject Win32_Logicaldisk -ComputerName $global:vmName |
Select @{Name="DriveName";Expression={$_.DeviceID}},
@{Name="FreeSpace";Expression={[math]::Round($_.Freespace/1GB,2)}}

foreach ($eachdrive in $disk)
{
$diskname = $eachdrive.DriveName+"-"+$eachdrive.FreeSpace
$disksize = $diskname+","+$disksize
$disksize = $disksize.TrimEnd(",")
}
#$disk=(Get-WmiObject -Class Win32_logicalDisk -computername $global:vmName).DeviceID
return $disksize
}

function nic()
{
$niccount = 0
$Nic = ""
$hnics =  Get-VMNetworkAdapter -VMName $global:vmName -ComputerName $global:Server
foreach($hnic in $hnics)
{
$niccount = $niccount+1
if ($niccount -gt 1)
{
$Nic = $Nic + ","
}
$Nic = $Nic + $hnic.SwitchName
}
$Nic = $Nic.TrimEnd(",")
return $Nic,$niccount
}

 function memory()
{
$tot = Get-VMMemory $global:vmName
$total = [math]::Round(($tot.Startup)/(1024*1024))
return $total
}

function HostMemory()
{
$vmHost = Get-VMHost -ComputerName $global:Server
if($vmHost)
{
$total = 0
Get-VM -ComputerName $global:Server | Where-Object { $_.State -eq "Running" } | Select-Object Name, MemoryAssigned | ForEach-Object { $total = $total + $_.MemoryAssigned }

#Get available RAM via performance counters
$Bytes = Get-Counter -ComputerName $global:Server -Counter "\Memory\Available Bytes"

# Convert values to GB
$availGB = ($Bytes[0].CounterSamples.CookedValue / 1GB)

return $availGB
}
}

function HostNetwork()
{
$vmHost = Get-VMHost -ComputerName $global:Server
if($vmHost)
{
$networkName = Get-VMSwitch -ComputerName $global:Server | Where-Object { $_.SwitchType -eq "External" } | Select-Object Name
}
return $networkName.Name
}

function no_of_cpu()
{
$no_of_cpu = (Get-VMProcessor -VMName $global:vmName -ComputerName $global:Server).count
return $no_of_cpu
}

function guid()
{
$guid=$global:vm.name
return $guid
}

function CPU()
{
$usage = Get-WmiObject win32_processor -computername $global:vmName | select LoadPercentage
return $usage.LoadPercentage
}

function disk_path()
{
$VMInfo = Get-VM -ComputerName $global:Server -Name $global:vmName

 $VHDs = ($VMInfo).harddrives.path

 $VHDString = ""
 $CheckChain = $true

 foreach ($VHD in $VHDs)
{
$ListDisk = New-Object System.Collections.Generic.List[string]
$CheckChain = $true
$VhdChain = $VHD
$dict = @{}

while($CheckChain)
{
$VHDInfo = $VhdChain | Get-VHD -ComputerName $global:Server

if([string]::IsNullOrEmpty($VHDInfo.ParentPath))
{
if([string]::IsNullOrEmpty($ListDisk))
{
$dict.Add($VHD,"None")
}
else
{
$dict.Add($VHD,$ListDisk)
}
$CheckChain = $false
}
else
{

$VhdChain = $VHDInfo.ParentPath
$ListDisk.Add($VHDInfo.ParentPath)
}
}
$str = $dict.GetEnumerator()  | % { "$($_.Name)::$($_.Value)" }
$str = $str +","
$VHDString = $VHDString + $str
}
$VHDString = $VHDString.TrimEnd(",")
return $VHDString
}


function power_state()
{
if($global:vm.EnabledState -eq 2 )
{
return "running"
}
else
{
return "off"
}
}

function ON()
{
Start-VM $global:vmName
sleep(20)
$op = Get-VM $global:vm -ComputerName $global:Server
return $op.State
}

function OFF()
{
Start-VM $global:vmName -ComputerName $global:Server
sleep(20)
$op = Get-VM $global:vm
return $op.State
}

function DeleteVM()
{
Get-VM $global:vmName -ComputerName $global:Server | %{ Stop-VM -VM $_ -Force; Remove-VM -vm $_ -Force ; Remove-Item -Path $_.Path -Recurse -Force}
}

function version()
{
$version = (Get-VM -Name $global:vmName -ComputerName $global:Server).IntegrationServicesVersion.major
return $version
}

function ip()
{
$ip = (Get-VM -Name $global:vmName | Select -ExpandProperty NetworkAdapters).IPAddresses | where {$_ -match "^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"}
return $ip
}

function GetVMFilesPath()
{
if($global:OsVersion -imatch "2008")
{
$GlobalValue = Get-WMIObject -class Msvm_VirtualSystemGlobalSettingData -namespace "root/virtualization" | where {$_.ElementName -eq $global:vmName}
return $GlobalValue.ExternalDataRoot
}
else
{
return (Get-VM $global:vmName -ComputerName $global:Server).Path
}
}

function GetAllVM()
{
$allVMs = gwmi -query "SELECT * FROM Msvm_ComputerSystem" -namespace $global:NameSpace -ComputerName $global:Server | where {$_.Caption -eq "Virtual Machine"}
$ListofVMs = New-Object System.Collections.Generic.List[string]
Foreach($eachVM in $allVMs){
    $ListofVMs.Add($eachVM.ElementName+",")
}
return $ListofVMs
}

function VMSnapshot()
{
$ListofSnap = ""
$Snapshots = Get-VMSnapshot $global:vmName
Foreach($eachSnap in $Snapshots){
    $ListofSnap = $eachSnap.Name+ ","+ $ListofSnap
}
$ListofSnap = $ListofSnap.TrimEnd(",")
return $ListofSnap
}
function Generation()
{
return (Get-VM $global:vmName).Generation
}

function GetHostName()
{
return [System.Net.Dns]::GetHostName()
}

function GetCSVRootPath()
{
    $rootPath =  (Get-Cluster).SharedVolumesRoot
    return $rootPath
}

function GetCSVOwner()
{
$output = Get-ClusterSharedVolume
$List = New-Object System.Collections.Generic.List[string]
$eachCSV = ""
Foreach($op in $output){
    $eachCSV = $op.Name + "+" + $op.OwnerNode.Name
    $List.Add($eachCSV + "," )
}
return $List
}
function GetVolumeFriendlyName()
{
$output = (Get-ClusterSharedVolumeState | Select-Object Name,VolumeFriendlyName) | sort-object -Property Name -Unique
$List = New-Object System.Collections.Generic.List[string]
$eachCSV = ""
Foreach($op in $output){
    $eachCSV = $op.Name + "+" + $op.VolumeFriendlyName
    $List.Add($eachCSV + "," )
}
return $List
}
function config_version(){
$ver = (Get-VM -Name $global:vmName -ComputerName $global:Server).Version
return $ver
}
function GetHyperVDefaultFolder()
{
$output = Get-VMHost | Select-object VirtualHardDiskPath
return $output.VirtualHardDiskPath
}