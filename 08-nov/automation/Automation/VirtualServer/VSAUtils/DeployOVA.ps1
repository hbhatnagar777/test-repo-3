Function Main()
{

try{
import-Module VMware.VimAutomation.Core
$WarningPreference = "SilentlyContinue"
$protocol = "https"

#initialize general varaibles
$global:server = "##Automation--server_name--##"
$global:user = "##Automation--user--##"
$global:pwd = "##Automation--pwd--##"
$global:ovaPath = "##Automation--ova_path--##"
$global:vm_name = "##Automation--vm_name--##"
$global:vm_host = "##Automation--esx_host--##"
$global:datastore = "##Automation--datastore--##"
$global:vm_network = "##Automation--vm_network--##"
$global:vm_pwd = "##Automation--vm_pwd--##"


Connect-VIServer -Server $server -User $user -Password $pwd -Protocol $protocol | Out-Null
}

catch
{ 
    write-host $Error[0]
    break
}

Deploy
}

Function Deploy()
{


$ovfConfig = Get-OvfConfiguration -Ovf $global:ovaPath

$ovfConfig.'001_HostName'.Host_Name.Value = $global:vm_name
$ovfConfig.'001_HostName'.Password.Value = $global:vm_pwd
$ovfConfig.NetworkMapping.VM_Network.Value = $global:vm_network

$VMhost = Get-VMHost -Name $global:vm_host

try{
    Import-VApp -Source $global:ovaPath -OvfConfiguration $ovfConfig -Location $VMHost -VMHost $VMhost -Datastore $global:datastore -Name $global:vm_name -DiskStorageFormat Thin -ErrorAction Stop
}
catch{
    Write-host "Exception deploying OVA. Please check host logs."
    break
}

$vm = Get-VM -Name $global:vm_name
Start-VM -VM $vm

}