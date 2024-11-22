Function BMRVerify(){

###############################################################################################################

#--------------------Execution starts here----------------------------------#

$Server_name = "##Automation--esxservername--##"  
$Server_username = "##Automation--esxusername--##"
$Server_password = "##Automation--esxpassword--##"
$vm_name = "##Automation--vmname--##" 
$Guest_username = "##Automation--mach_username--##"
$Guest_password = "##Automation--mach_password--##" 


$command1 = Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false 

$commamd2 = Set-PowerCLIConfiguration -Scope User -ParticipateInCEIP $false -Confirm:$false

$command3 = Connect-VIServer -server $Server_name -user $Server_username -Password $Server_password


$script = 'get-service -Name iphlpsvc'

try
{

$output = Invoke-VMScript -ScriptText $script -VM $vm_name -GuestUser $Guest_username -GuestPassword $Guest_password

if ($output.Status -eq "Running")
{

return $True

}

}
catch [Exception]
{
$exception = $_.Exception.GetType().FullName, $_.Exception.Message
return $exception
}

return $false
}