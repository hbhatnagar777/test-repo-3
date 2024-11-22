Function Main()
{

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$casserver="##Automation--ExchangeCASServer--##"
$aliasname = "##Automation--aliasName--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
$return_val = $true
$mailboxExistsTest = Get-Mailbox -Identity $aliasname -ErrorAction SilentlyContinue |? {$_.RecipientType -eq "UserMailbox"}
if (!$mailboxExistsTest)
{
    $return_val = $false
}

Search-Mailbox -Identity $aliasname -DeleteContent -Force
Remove-PSSession $Session
return "Result: $return_val"
}