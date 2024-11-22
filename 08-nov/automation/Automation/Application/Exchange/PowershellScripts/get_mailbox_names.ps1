Function Main()
{

Set-ExecutionPolicy -ExecutionPolicy remotesigned -Force

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$database = "##Automation--ExchangeDatabase--##"
$server = "##Automation--ExchangeServerName--##"
$outputpath ="##Automation--output--##"
$casserver="##Automation--ExchangeCASServer--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
Get-MailboxStatistics -Database $database | ft displayname  | out-file -filepath $outputpath -Encoding ASCII
}