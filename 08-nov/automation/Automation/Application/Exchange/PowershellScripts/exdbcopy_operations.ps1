Function Main()
{

Set-ExecutionPolicy -ExecutionPolicy remotesigned -Force

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$database = "##Automation--ExchangeDatabase--##"
$server = "##Automation--ExchangeServerName--##"
$op= "##Automation--operation--##"
$casserver="##Automation--ExchangeCASServer--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
$op=$op.ToUpper()
if($op -eq "SUSPEND")
{
Suspend-MailboxDatabaseCopy "$database" -Confirm:$False
}
Elseif ($op -eq "RESUME")
{
Resume-MailboxDatabaseCopy "$database" -Confirm:$False
}
Elseif($op -eq "REMOVE")
{
$db= $database+"\"+$server
Remove-MailboxDatabaseCopy "$db" -Confirm:$False
}
else
{
Add-MailboxDatabaseCopy "$database" -MailboxServer "$server"
}
}