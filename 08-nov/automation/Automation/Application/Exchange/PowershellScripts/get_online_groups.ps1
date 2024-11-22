Function Main()
{
    #initialize general variables
    $LoginUser = "##Automation--LoginUser--##"
    $PWD = "##Automation--LoginPassword--##"
    $GroupType  = "##Automation--GroupType--##"
    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
    Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false
    if($GroupType -eq "Microsoft 365")
    {
        $output=Get-EXORecipient | select Alias,RecipientTypeDetails | where RecipientTypeDetails -eq "GroupMailbox"

        return $output.Alias
    }

    if($GroupType -eq "Distribution List")
    {
        $output=Get-EXORecipient | select Alias,RecipientTypeDetails | where RecipientTypeDetails -eq "MailUniversalDistributionGroup"

        return $output.Alias
    }

    if($GroupType -eq "Mail Enabled Security Group")
    {
        $output=Get-EXORecipient | select Alias,RecipientTypeDetails | where RecipientTypeDetails -eq "MailUniversalSecurityGroup"

        return $output.Alias
    }

    if($GroupType -eq "Dynamic Distribution Group")
    {
        $output=Get-EXORecipient | select Alias,RecipientTypeDetails | where RecipientTypeDetails -eq "DynamicDistributionGroup"

        return $output.Alias
    }

    Get-PSSession | Remove-PSSession
}