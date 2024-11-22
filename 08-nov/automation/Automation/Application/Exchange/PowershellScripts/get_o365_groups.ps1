Function Main()
{

    #initialize general variables
    $LoginUser = "##Automation--LoginUser--##"
    $PWD = "##Automation--LoginPassword--##"
    $WarningPreference  = 'SilentlyContinue'
    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
    # $Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri https://outlook.office365.com/powershell-liveid/ -Credential $Credential -Authentication Basic -AllowRedirection
    $groups = "Result is: 0"

    try{
        # Import-PSSession $Session
        Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false
        $group_obj = Get-UnifiedGroup
        if(($group_obj | Measure-Object).Count -gt 0){

            $groups = $group_obj | Format-List Alias, DisplayName, PrimarySmtpAddress, ExternalDirectoryObjectId
        }
        # Remove-PSSession $Session
    }
    catch{
        $groups = "Result is: -1"
    }
    return $groups
}


