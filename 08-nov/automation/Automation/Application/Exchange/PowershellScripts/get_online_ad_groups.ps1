Function Main()
{

    #initialize general variables
    $LoginUser = "##Automation--LoginUser--##"
    $LoginPassword = "##Automation--LoginPassword--##"
    $filepath = "##Automation--filepath--##"

    $PWord = ConvertTo-SecureString -String $LoginPassword -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord

    # $Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri https://outlook.office365.com/powershell-liveid/ -Credential $Credential -Authentication Basic -AllowRedirection

    # Import-PSSession $Session

	Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false
    
    $mbs = Get-DistributionGroup -ResultSize unlimited | Format-List Alias, DistinguishedName, SamAccountName

    $mbs | Out-File $filepath -Encoding utf8  -Width 300
}
