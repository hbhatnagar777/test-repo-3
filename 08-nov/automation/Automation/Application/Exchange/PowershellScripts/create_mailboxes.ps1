
Function Main()
{

Set-ExecutionPolicy -ExecutionPolicy remotesigned -Force

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$displayname = "##Automation--displayName--##"
$database = "##Automation--ExchangeDatabase--##"
$ExchangeServerDomain = "##Automation--ExchangeServerDomain--##"
$server = "##Automation--ExchangeServerName--##"
$numberofmailboxes= '##Automation--MailboxesNumber--##'
$casserver="##Automation--ExchangeCASServer--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
if ($numberofmailboxes -eq "None")
{
$UPN=$displayname+"@"+$ExchangeServerDomain	
new-mailbox -alias $displayname -database $database -firstname $displayname -name $displayname -displayname $displayname -userprincipalname $UPN -password $PWord
}
else
{
for($value=0;$value -le $numberofmailboxes-1;$value++) 
{	

	$UPN=$displayname+"@"+$ExchangeServerDomain	

	####Checking whether mailbox exists
	$ErrorActionPreference = 'SilentlyContinue'
	$mailboxExistsTest = get-user -Identity $UPN |select RecipientType
	$ErrorActionPreference = 'Continue'
	if ($mailboxExistsTest.RecipientType -match "Mailbox")
	{
		####Mailbox exists - Hence deleting it
		remove-mailbox -Identity $UPN -permanent $true -confirm:$false
	}

	####Creating new mailbox
	$ErrorActionPreference = 'Stop'
	new-mailbox -alias $displayname -database $database -firstname $displayname -name $displayname -displayname $displayname -userprincipalname $UPN -password $PWord

}
new-mailbox -alias $displayname -database $database -firstname $displayname -name $displayname -displayname $displayname -userprincipalname $UPN -password $PWord
}
}