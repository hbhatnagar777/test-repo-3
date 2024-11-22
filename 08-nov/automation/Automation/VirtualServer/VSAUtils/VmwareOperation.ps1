
#Purpose:  TO Get all VMs and some properties of the vm from given HOst or vCenter

Function Main()
{
import-Module VMware.VimAutomation.Core
$WarningPreference = "SilentlyContinue"
$protocol = "https"

#initialize general varaibles
$global:server = "##Automation--server_name--##"
$global:user = "##Automation--user--##"
$global:pwd = "##Automation--pwd--##"
$global:vm_name = "##Automation--vm_name--##"
$global:vm_user = "##Automation--vm_user--##"
$global:vm_pass = "##Automation--vm_pass--##"
$global:property= "##Automation--property--##"
[string]$global:extra_args = "##Automation--extra_args--##"

Connect-VIServer -Server $server -User $user -Password $pwd -Protocol $protocol | Out-Null

$var = &$global:property 
write-host $global:property"="$var
}

function copy_data()
{
  try {
        $_path=$global:extra_args -split "@"
        Copy-VMGuestFile -LocalToGuest -Force -VM $global:vm_name -Source $_path[0] -Destination $_path[1] -GuestUser $global:vm_user -GuestPassword $global:vm_pass
        return "Sucess"
    }
    catch
    {
        return "Error"

}}

function vm_exists()
{
    $vm = get-view -viewtype VirtualMachine -filter @{"name" = "^($global:vm_name)$"}
    if ($vm -ne $Null)
    {
        return $true
        }
    else
        {
        return $false
        }

}

function ds_info()
{
    $vm = get-view -viewtype VirtualMachine -filter @{"name" = "^($global:vm_name)$"}
    $ds=$vmConfig.DatastoreUrl|Select Name
    return $ds.Name
}

function ds_exists()
{
    $ds =Get-DataStore $global:vm_name
    if ($ds -ne $Null)
    {
        return $true
    }
    else
    {
        return $false
    }
}


function convert_vm_to_template()
{
        $template = Get-VM $global:vm_name | Set-VM -ToTemplate -Name $global:vm_name -Confirm:$false
        return $template
}

function convert_template_to_vm()
{
        $vm = Set-Template -Template $global:vm_name -ToVM
        return $vm
}

function power_on()
{
    try
    {
        Start-VM -VM (Get-VM -Name $global:vm_name)
        return $true
        }
    catch
    {
        return $false
    }
}

function power_off()
{
    try
    {
        $vm_present = vm_exists
        if ($vm_present -eq $true){
            Stop-VM -VM (Get-VM -Name $global:vm_name) -Confirm:$false
        }
        else{
            return "vm is not present"
        }
        return $true
        }
    catch
    {
        return $false
    }
}

function delete()
{
    try
        {
        $vm = Get-VM -Name $global:vm_name
        if ($vm.PowerState -eq "PoweredOn")
        {
            power_off
            Start-Sleep -s 10
            }
        Remove-vm $vm.name -DeletePermanently -Confirm:$false | Out-Null
        Start-Sleep -s 10
        return $true
        }
    catch
    {
        return $false
        }

    }

function attach_network_adapter()
{
    try
    {
        Get-VM $global:vm_name | Get-NetworkAdapter| Set-NetworkAdapter -Connected:$true -Confirm:$false | Out-Null
        return $true
    }
    catch
    {
         return $false
    }
}

function delete_disks()
{
    $disks = Get-HardDisk -VM $global:vm_name | Select-Object name,filename  | Where-object {$_.filename -like $global:extra_args} | sort-object -Property Name -descending
    foreach($disk in $disks){
        Get-HardDisk -VM $vm_name -Name $disk.name | Remove-HardDisk -DeletePermanently -Confirm:$false
    }
    return $disks.Filename
}

function change_num_cpu()
{
    $num_cpu = $global:extra_args -as [int]
    Set-VM $global:vm_name -NumCPU $num_cpu -Confirm:$false
    return $true
}

function change_memory()
{
    $ram_val = $global:extra_args -as [int]
    Set-VM $global:vm_name -MemoryGB $ram_val -Confirm:$false
    return $true
}
