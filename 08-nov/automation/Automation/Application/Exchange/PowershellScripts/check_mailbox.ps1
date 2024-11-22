Function Main()
{

Set-ExecutionPolicy -ExecutionPolicy remotesigned -Force

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$mailbox = "##Automation--MailboxName--##"
$casserver="##Automation--ExchangeCASServer--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
$name=Get-Mailbox -Identity $mailbox | ft name | out-string
return $name
}