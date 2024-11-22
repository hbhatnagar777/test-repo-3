##########################################################################################################################
#
# This powershell script is to create specified number of journal mailboxes within the given database
# under the specified Exchange Server
# If journal mailbox already exists it will be deleted and recreated
#
###########################################################################################################################
Function Main()
{

trap {$var = "Exception occured:";$var=$var + $_;return $var}
$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$aliasname = "##Automation--aliasName--##"
$displayname = "##Automation--displayName--##"
$smtp= "##Automation--SMTP--##"
$database = "##Automation--ExchangeDatabase--##"
$ExchangeServerDomain = "##Automation--ExchangeServerDomain--##"
$ExchangeCASServer = "##Automation--ExchangeCAServer--##"


$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
$UPN=$aliasname+"@"+$ExchangeServerDomain

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$ExchangeCASServer/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session

$UPN=$displayname+"@"+$ExchangeServerDomain

$ErrorActionPreference = 'Continue'
$mb=@()
$temp=@()



	####Checking whether journal mailbox exists
	$ErrorActionPreference = 'SilentlyContinue'
	$mailboxExistsTest = get-user -Identity $UPN |select RecipientType
	$ErrorActionPreference = 'Continue'
	if ($mailboxExistsTest.RecipientType -match "Mailbox")
	{
		####Mailbox exists - Hence deleting it
		remove-mailbox -Identity $UPN -permanent $true -confirm:$false
	}


$ErrorActionPreference = 'Stop'
$temp = new-mailbox -alias $displayname -database $database -firstname $displayname -name $displayname -displayname $displayname -userprincipalname $UPN -password $PWord
set-MailboxDatabase $database -journalrecipient $displayname -WarningAction SilentlyContinue


#	$temp = new-mailbox -alias $name -database $database -firstname $name -name $name -displayname $name -userprincipalname $UPN -password $password
#	set-mailboxdatabase $database -journalrecipient $name
	#$temp | select userprincipalname | foreach {$_.UserPrincipalName}
	$temp =  $temp.UserPrincipalName
	$mb += $temp

return $mb
}







