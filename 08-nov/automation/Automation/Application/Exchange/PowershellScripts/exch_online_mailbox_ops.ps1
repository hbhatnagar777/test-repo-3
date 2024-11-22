Function Main()
{

	$PWD = "##Automation--LoginPassword--##"
	$LoginUser= "##Automation--LoginUser--##"
    $OpType = "##Automation--OpType--##"

    $SMTP = "##Automation--SMTP--##"
    $ExchangeServerDomain = "##Automation--ExchangeServerDomain--##"
    $aliasname = "##Automation--aliasName--##"
    $displayname = "##Automation--displayName--##"
    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
	Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false

    if ($OpType -eq "CREATE")
    {
        $UPN=$aliasname+"@"+$ExchangeServerDomain

	    $smtp = $UPN
        try{
            $ErrorActionPreference = 'SilentlyContinue'
            Get-EXOMailbox -Identity $aliasname | Remove-Mailbox -Confirm:$false
        }
        catch{
            $ErrorActionPreference = 'Continue'
        }
	    New-Mailbox -MicrosoftOnlineServicesID $UPN -Alias $aliasname -Name $displayname -PrimarySmtpAddress $smtp -FirstName $displayname -DisplayName $displayname -Password $PWord
    }

    elseif ( $OpType -eq "DELETE")
    {
        Get-EXOMailbox -Identity $SMTP | Remove-Mailbox -Confirm:$false
    }

    elseif( $OpType -eq "ModifySMTP")
    {
        $CurrSMTP = $SMTP
        $NewSMTP = "modified" + $CurrSMTP

#        $NewSMTP = "SMTP:"+$NewSMTP
#        Get-EXOMailbox -IncludeInactiveMailbox -Identity $CurrSMTP | Set-Mailbox -EmailAddresses $NewSMTP

        Connect-AzureAD -Credential $Credential

        Get-AzureADUser -ObjectId $CurrSMTP | Set-AzureADUser -UserPrincipalName $NewSMTP

    }

    elseif ($OpType -eq "CLEANUP")
    {
        $ErrorActionPreference = 'Continue'

        $ComplianceName = -join ((48..57) + (97..122) | Get-Random -Count 32 | % {[char]$_})
        # Name of the compliance Search
        $Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri https://ps.compliance.protection.outlook.com/powershell-liveid/ -Credential $Credential -Authentication Basic -AllowRedirection

        Import-PSSession $Session -AllowClobber

        New-ComplianceSearch -Name $ComplianceName -ExchangeLocation $SMTP -AllowNotFoundExchangeLocationsEnabled:$true

        Start-ComplianceSearch -Identity $ComplianceName

        $ComplianceSearchStatus = Get-ComplianceSearch -Identity $ComplianceName | Select-Object Status

        while ($ComplianceSearchStatus.Status -ne "Completed") {

            Start-Sleep -Milliseconds 5000

            $ComplianceSearchStatus = Get-ComplianceSearch -Identity $ComplianceName | Select-Object Status
        }

        $ComplianceActionName = New-ComplianceSearchAction -SearchName $ComplianceName -Purge -PurgeType HardDelete -Confirm:$false | Select-Object Name

        $ComplianceStatus = Get-ComplianceSearchAction -Identity $ComplianceActionName.Name | Select-Object Status

        while($ComplianceStatus.Status -ne "Completed")
        {
            Start-Sleep -Milliseconds 5000

            $ComplianceStatus = Get-ComplianceSearchAction -Identity $ComplianceActionName.Name | Select-Object Status
        }

        Remove-ComplianceSearchAction -Identity $ComplianceActionName.Name -Confirm:$false

        Remove-ComplianceSearch -Identity $ComplianceName -Confirm:$false

        Remove-PSSession $Session -Confirm:$false

    }
    $ErrorActionPreference = 'Continue'
}
