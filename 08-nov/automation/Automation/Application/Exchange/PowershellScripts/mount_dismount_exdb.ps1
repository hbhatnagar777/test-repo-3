Function Main()
{

Set-ExecutionPolicy -ExecutionPolicy remotesigned -Force

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$database = "##Automation--ExchangeDatabase--##"
$server = "##Automation--ExchangeServerName--##"
$op= "##Automation--operation--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$server/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
$op=$op.ToUpper()
if($op -eq "MOUNT")
{
    mount-Database -Identity $database -Confirm:$False
}
else
{
    Dismount-Database -Identity $database -Confirm:$False
}
}