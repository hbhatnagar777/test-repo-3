##pre-req - Azuread ps module
Function Main(){
        $commandCenterUrl = "##Automation--HostName--##"

        $PWD = "##Automation--LoginPassword--##"
        $LoginUser= "##Automation--LoginUser--##"
        $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force


        $replyUrl = 'https://' + $commandCenterUrl + '/commandcenter/processAzureAuthToken.do'

        $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord

        $accountInfo = Connect-AzureAD -Credential $Credential

        $directoryId = $accountInfo.TenantId

    #Assigning permission explitcitly
    $MsGraphOnlyPermissionList = New-Object Microsoft.Open.AzureAD.Model.RequiredResourceAccess
    $MsGraphOnlyPermissionList.ResourceAppId = "00000003-0000-0000-c000-000000000000" #ResourceName = MS Graph API


    $DynamicsCRMPermissionList = New-Object Microsoft.Open.AzureAD.Model.RequiredResourceAccess
    $DynamicsCRMPermissionList.ResourceAppId = "00000007-0000-0000-c000-000000000000" #ResourceName = Dynamics CRM

    $MsGraphReadDirectoryData = New-Object Microsoft.Open.AzureAD.Model.ResourceAccess -ArgumentList "7ab1d382-f21e-4acd-a863-ba3e13f7da61","Role"

    $MsGraphDirectoryAccessAsUser = New-Object Microsoft.Open.AzureAD.Model.ResourceAccess -ArgumentList "0e263e50-5827-48a4-b97c-d940288653c7","Scope"

    $MsGraphApplicationReadWriteAll = New-Object Microsoft.Open.AzureAD.Model.ResourceAccess -ArgumentList "1bfefb4e-e0b5-418b-a88f-73c46d2cc8e9","Role"

    $MsGraphOrganizationReadAll= New-Object Microsoft.Open.AzureAD.Model.ResourceAccess -ArgumentList "498476ce-e0fe-48b0-b801-37ba7e2685c6","Role"
    $MsGraphReportsReadAll= New-Object Microsoft.Open.AzureAD.Model.ResourceAccess -ArgumentList "b0afded3-3588-46d8-8b3d-9842eff778da","Role"


    $DynamicsCRMUserImpersonation = New-Object Microsoft.Open.AzureAD.Model.ResourceAccess -ArgumentList "78ce3f0f-a1ce-49c2-8cde-64b5c0896db4","Scope"


    $displayname = ''

    $MsGraphOnlyPermissionList.ResourceAccess += $MsGraphApplicationReadWriteAll
    $MsGraphOnlyPermissionList.ResourceAccess += $MsGraphReportsReadAll
    $MsGraphOnlyPermissionList.ResourceAccess += $MsGraphDirectoryAccessAsUser


    $DynamicsCRMPermissionList.ResourceAccess += $DynamicsCRMUserImpersonation
    $MsGraphOnlyPermissionList.ResourceAccess += $MsGraphOrganizationReadAll
    $MsGraphOnlyPermissionList.ResourceAccess += $MsGraphReadDirectoryData

    $displayname = 'CVDynamicsMetallicAutomationApp'


    $AllResourceList = New-Object System.Collections.Generic.List[Microsoft.Open.AzureAD.Model.RequiredResourceAccess]
    if($MsGraphOnlyPermissionList.ResourceAccess.Count -gt 0){$AllResourceList.Add($MsGraphOnlyPermissionList)}
    if($DynamicsCRMPermissionList.ResourceAccess.Count -gt 0){$AllResourceList.Add($DynamicsCRMPermissionList)}

#    Connect-AzAccount -Credential $Credential
    Connect-AzAccount -Credential $Credential > $null 3>$null 2>$null
    #Creating App
    $unixTimeStamp = [int][double]::Parse((Get-Date -date (Get-Date).ToUniversalTime()-uformat %s))
    $DisplayName += $($unixTimeStamp + $i)

    $newAzureApp = New-AzureADApplication -DisplayName $DisplayName -RequiredResourceAccess $AllResourceList -Oauth2AllowImplicitFlow:$true

    Update-AzADApplication -ApplicationId $newAzureApp.AppId -isFallbackPublicClient:$true

    Disconnect-AzAccount > $null 3>$null 2>$null
    Start-sleep -seconds 5

    #Generate Secret key
    $secretkey = New-AzureADApplicationPasswordCredential -ObjectId $newAzureApp.ObjectId  -EndDate (Get-Date).AddYears(100)

    ##Set replyUrl
    if(-not [string]::IsNullOrEmpty($replyUrl))
    {
        Set-AzureADApplication -ObjectId $newAzureApp.ObjectId -ReplyUrls $replyUrl
    }


    try
    {
        [byte[]]$logoBytes = [System.Convert]::FromBase64String("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")

        $filestream = New-Object -TypeName 'System.IO.MemoryStream' -ArgumentList (,$logoBytes)
        Set-AzureADApplicationLogo -ObjectId $newAzureApp.ObjectId -FileStream $filestream -ErrorAction SilentlyContinue
    }
    catch
        {
            ##Do Nothing. This is to suppress any failure while setting up app details
        }


#        Commenting below lines, keeping note of attributes, in case their use might come up later
#        $azureAppCred ="

#            Azure Application ID -                " + $newAzureApp.AppId + "
#            Azure Application Secret -            " + $secretkey.value + "
#            Azure Directory ID -                  " + $directoryId.Guid + "
#
#            Azure Application Name -              " + $newAzureApp.DisplayName + "
#            Azure Application Object ID -         " + $newAzureApp.ObjectId + "
#        "
            return $newAzureApp.AppId , $secretkey.value, $directoryId.Guid

}
