Function Main()
{

#initialize general variables

$LoginUser = "##Automation--LoginUser--##"
$PWD = "##Automation--LoginPassword--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
#$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri https://outlook.office365.com/powershell-liveid/ -Credential $Credential -Authentication Basic -AllowRedirection
#
#Import-PSSession $Session

Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false
$filepath = "C:\Commvault\Automation\Application\Exchange\ExchangeMailbox\RetrievedFiles\online_users.txt"

Write-output $filepath
$mb = Get-Mailbox -ResultSize Unlimited |select alias
return $mb

}

