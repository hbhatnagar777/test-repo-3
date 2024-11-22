#Purpose:  to perform operations on azureRM VMs

Function Main()
{
$WarningPreference = "SilentlyContinue"
$protocol = "https"

#initialize general varaibles
$global:subscription_id = "##Automation--subscription_id--##"
$global:tenant_id = "##Automation--tenant_id--##"
$global:client_id = "##Automation--client_id--##"
$global:cred_password = "##Automation--cred_password--##"
$global:vm_name = "##Automation--vm_name--##"
$global:resource_group = "##Automation--resource_group--##"
$global:property= "##Automation--property--##"
[string]$global:extra_args = "##Automation--extra_args--##"

$global:secpasswd = ConvertTo-SecureString $global:cred_password -AsPlainText -Force

$global:sub_creds = New-Object System.Management.Automation.PSCredential ($global:client_id, $global:secpasswd)

Connect-AzureRmAccount -TenantId $global:tenant_id -ServicePrincipal -SubscriptionId $global:subscription_id -Credential $global:sub_creds

$var = &$global:property 
write-host $global:property"="$var
}

Function power_on()
{
    try
    {
        $start_instance = Get-AzureRmVM -ResourceGroupName $global:resource_group -Name $global:vm_name -Status | select -ExpandProperty Statuses | ?{ $_.Code -match "PowerState" } |select -ExpandProperty DisplayStatus
        if($start_instance -cnotcontains "running")
        {
            Start-AzureRMVM -ResourceGroupName $global:resource_group -Name $global:vm_name 
            $start_instance = Get-AzureRmVM -ResourceGroupName $global:resource_group -Name $global:vm_name -Status | select -ExpandProperty Statuses | ?{ $_.Code -match "PowerState" } |select -ExpandProperty DisplayStatus
        }
        return $start_instance

 

    }
    catch
    {
        return $false
    }
}

Function power_off()
{
    try
    {
        Stop-AzureRMVM -ResourceGroupName $global:resource_group -Name $global:vm_name -Force
        $stop_instance = Get-AzureRmVM -ResourceGroupName $global:resource_group -Name $global:vm_name -Status | select -ExpandProperty Statuses | ?{ $_.Code -match "PowerState" } |select -ExpandProperty DisplayStatus
        return $stop_instance

    }
    catch
    {
        return $false
    }
}

Function clean_up()
{
    try
       {
            Get-AzureRmVM -ResourceGroupName $global:resource_group | Where Name -Match $global:vm_name  | foreach { 
            $a=$_ 
            $DataDisks = @($a.StorageProfile.DataDisks.Name) 
            $OSDisk = @($a.StorageProfile.OSDisk.Name)  

            $_ | Remove-AzureRmVM -Force -Confirm:$false 
 
            $_.NetworkProfile.NetworkInterfaces | where {$_.ID} | ForEach-Object { 

                $NICName = Split-Path -Path $_.ID -leaf 
                Write-Warning -Message "Removing NIC: $NICName" 
                $Nic = Get-AzureRmNetworkInterface -ResourceGroupName $global:resource_group -Name $NICName 
                $Nic | Remove-AzureRmNetworkInterface -Force 

            } 

            if($a.StorageProfile.OsDisk.ManagedDisk ) 
            { 
            ($OSDisk + $DataDisks) | ForEach-Object { 
    
                Get-AzureRmDisk -ResourceGroupName $ResourceGroup -DiskName $_ | Remove-AzureRmDisk -Force 

               } 
            } 

            else 
            { 
             
                $saname = ($a.StorageProfile.OsDisk.Vhd.Uri -split '\.' | Select -First 1) -split '//' |  Select -Last 1 
                $sa = Get-AzureRmStorageAccount -ResourceGroupName $global:resource_group -Name $saname 

                $a.StorageProfile.DataDisks | foreach { 
                    $disk = $_.Vhd.Uri | Split-Path -Leaf 
                    Get-AzureStorageContainer -Name vhds -Context $Sa.Context | 
                    Get-AzureStorageBlob -Blob  $disk | 
                    Remove-AzureStorageBlob   
                } 

                $disk = $a.StorageProfile.OsDisk.Vhd.Uri | Split-Path -Leaf 
                Get-AzureStorageContainer -Name vhds -Context $Sa.Context | 
                Get-AzureStorageBlob -Blob  $disk | 
                Remove-AzureStorageBlob   
 
             } 
     
          }

        return $true
   }

    catch
    {
        return $false
    }
}