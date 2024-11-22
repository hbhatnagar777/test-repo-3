Function Main() {
    $GlobalAdmin = '##Automation--LoginUser--##'
    $GlobalAdminPassword = '##Automation--LoginPassword--##'
    $ServiceAccounts = "##Automation--ServiceAccount--##"

    $SecurePassword = $GlobalAdminPassword | convertto-securestring -AsPlainText -Force
    $Cred = new-object -typename System.Management.Automation.PSCredential -argumentlist $GlobalAdmin, $SecurePassword

    Connect-AzureAD -Credential $Cred | Out-Null

    $exmb_role = Get-AzureADDirectoryRole | Where-Object {$_.DisplayName -eq "Exchange Administrator"}

    $MBX = Get-AzureADDirectoryRoleMember -ObjectId $exmb_role.ObjectId | Where-Object {$_.UserPrincipalName -eq $ServiceAccounts}

    return [bool]$MBX
}