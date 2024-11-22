
Function Main()
{

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
$ErrorActionPreference = 'SilentlyContinue'
	$mailboxExistsTest = get-user -Identity $aliasname |select RecipientType
	$ErrorActionPreference = 'Continue'
	if ($mailboxExistsTest.RecipientType -match "Mailbox")
	{
        		####Mailbox exists - Hence deleting it
		remove-mailbox -Identity $UPN -permanent $true -confirm:$false
	}
new-mailbox -alias $displayname -database $database -firstname $displayname -name $displayname -displayname $displayname -userprincipalname $UPN -password $PWord
Enable-Mailbox $aliasname -Archive

}
