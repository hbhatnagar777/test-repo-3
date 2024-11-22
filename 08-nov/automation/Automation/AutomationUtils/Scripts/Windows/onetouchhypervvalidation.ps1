Function BMRVerifyhyperv(){

###############################################################################################################

#--------------------Execution starts here----------------------------------#

$vm_name = "##Automation--vmname--##" 
$Guest_username = "##Automation--mach_username--##"
$Guest_password = "##Automation--mach_password--##"

$pass = ConvertTo-SecureString -AsPlainText $Guest_password -Force
$Cred = New-Object System.Management.Automation.PSCredential -ArgumentList $Guest_username,$pass



try
{

$output = Invoke-Command -VMName $vm_name -ScriptBlock {get-service -Name iphlpsvc} -Credential $cred

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

return $False
}


