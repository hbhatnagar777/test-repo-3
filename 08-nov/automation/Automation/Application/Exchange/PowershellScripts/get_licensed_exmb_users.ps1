Function Main()
{
    $Passwd = "##Automation--LoginPassword--##"

    $LoginUser = "##Automation--LoginUser--##"

    $PWord = ConvertTo-SecureString -String $Passwd -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord

    Connect-MsolService -Credential $credential

    Get-MsolUser -All | Where-Object { $_.Licenses.ServiceStatus | Where-Object { $_.ServicePlan.ServiceName -like "*exchange*" -and $_.ProvisioningStatus -eq "Success" } } | Format-List UserPrincipalName
}