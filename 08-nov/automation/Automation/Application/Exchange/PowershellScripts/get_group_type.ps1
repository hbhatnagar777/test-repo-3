Function Main()
{
    $PWD = "##Automation--LoginPassword--##"
    $Email = "##Automation--LoginUser--##"
    $GroupName = "##Automation--GroupName--##"

    $SecurePassword = ConvertTo-SecureString -String $PWD -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $Email, $SecurePassword

	# $Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri https://outlook.office365.com/powershell-liveid/ -Credential $Credential -Authentication Basic -AllowRedirection

    # Connect-AzureAD -Credential $Credential | Out-Null

    # Import-PSSession $Session -DisableNameChecking -AllowClobber | Out-Null

    Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false

    $group_type = Get-Group -Identity $GroupName | Select-Object RecipientTypeDetails

    return $group_type
}