#Purpose:  TO Get all VMs and some properties of the vm from given HOst or vCenter

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
$global:vm_name = "##Automation--vm_name--##"
$global:property= "##Automation--property--##"
[string]$global:extra_args = "##Automation--extra_args--##"


Connect-VIServer -Server $server -User $user -Password $pwd -Protocol $protocol | Out-Null
}

catch
{
    write-host $Error[0]
    break
}

if($global:property -eq "tagsvalidation")
{
$var1 = tags_of_vm
$var2 = category_of_vms

write-host "tags_of_vm="$var1";category_of_vm="$var2
}

else
{
$var10 = &$global:property
write-host $global:property "=" $var10
}
}

function tags_of_vm()
{
$vm = Get-vm $global:vm_name
$tag = Get-TagAssignment -Entity $vm
$tagsofvm = $tag.Tag.Name -join ','
return $tagsofvm
}

function category_of_vms()
{
$vm= Get-vm $global:vm_name
$tag = Get-TagAssignment -Entity $vm
$categoryofvms = $tag.Tag.Category.Name | Get-Unique
return $categoryofvms
}

function listvms()
{
    $ListofVMs = New-Object System.Collections.Generic.List[string]
    $command = $global:extra_args.Split(':')[-1].trim()
    $pattern = $global:extra_args.replace(':'+$command,'').trim()
    $pattern = $pattern.replace('id:','')
    if ($global:extra_args.StartsWith('id')){
        $pattern = '*'+$pattern
        $list_vms = '(& $command  | where {$_.id -like $pattern} )'
        }
    else {
        $pattern = $pattern.Split(':')[1]
        $pattern = '*'+$pattern
        $list_vms = '(& $command  | where {$_.name -like $pattern} )'}
    $ListofVMs = Invoke-Expression $list_vms
    $ListofVMs = tags_n_category $ListofVMs.name $command

    return $ListofVMs
}

function tags_n_category($value1, $value2)
{
    if($value2 -eq 'get-tag')
    {
        $tags = Get-VM | Get-TagAssignment | Where-Object {$_.Tag.Name -eq $value1}
        $vms= $tags.Entity.Name -join ","
    }
    if ($value2 -eq 'get-tagcategory')
    {
        $cat = Get-TagAssignment -Category $value1
        $cat = $cat.Entity | Select-Object -unique
        $vms = $cat.name -join","
    }
    return $vms
}