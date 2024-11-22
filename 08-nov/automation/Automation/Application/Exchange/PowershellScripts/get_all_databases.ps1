##########################################################################################################################
#
# This powershell script is to get the list databases within an Exchange Server
#
###########################################################################################################################
Function Main()
{
$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$server="##Automation--ExchangeServer--##"

$ErrorActionPreference = 'SilentlyContinue'

$ErrorActionPreference = 'Continue'
$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$server/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session

#$server | out-file -filepath $output -Encoding ASCII
trap { $var = "Exception occured:";$var | out-file -filepath $output -append -Encoding ASCII; $var=$_;$var | out-file -filepath $output -append -Encoding ASCII;return $var }
$all=Get-MailboxDatabase -server $server |ft name | out-string

#$all | out-file -filepath $output -append -Encoding ASCII

return $all
}