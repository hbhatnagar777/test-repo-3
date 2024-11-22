Function CreateWebapp()
{
    #read in arguments
    $url = "##Automation--WebappURL--##"
    $name = "##Automation--WebappName--##"
    $appPool = "##Automation--AppPoolName--##"
    $appPoolAcct = "##Automation--AppPoolAcct--##"
    $appPoolPass = "##Automation--AppPoolPass--##"
    $dbName = "##Automation--DatabaseName--##"
    $dbServer = "##Automation--DatabaseServer--##"

    #load snapins and modules
    Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue

    $ErrorActionPreference = "Stop"
    try{

        Start-SPAssignment -Global

        [Microsoft.SharePoint.SPSecurity]::RunWithElevatedPrivileges({

            $ap = New-SPAuthenticationProvider
            $spAccts = (Get-SPManagedAccount | Select UserName)
            $exists = $FALSE

            $spAccts | ForEach-Object{
                Write-Host $_.Username
                if (($_.Username -eq $appPoolAcct) -and (!($exists))){
                    $exists = $TRUE
                }
            }

            if (!($exists)){
                Write-Host "USER DOESN'T EXIST"
                $poolAcctPass = ConvertTo-SecureString -AsPlainText $appPoolPass -force
                $cred = New-Object System.Management.Automation.PSCredential ($appPoolAcct, $poolAcctPass)
                New-SPManagedAccount -Credential $cred | Out-Null
            }

            New-SPWebApplication -URL $url -Name $name -ApplicationPool $appPool -ApplicationPoolAccount $appPoolAcct -DatabaseName $dbName -DatabaseServer $dbServer -AuthenticationProvider $ap | Out-Null

            $webApp = Get-SPWebApplication -Identity $url

            $policy = $webApp.Policies.Add($appPoolAcct, $appPoolAcct)
            $policyRole = $webApp.PolicyRoles.GetSpecialRole([Microsoft.SharePoint.Administration.SPPolicyRoleType]::FullControl)
            $policy.PolicyRoleBindings.Add($policyRole)
            $webApp.Update()
        })

        Stop-SPAssignment -Global

        Exit 0
    }
    catch {
        $ErrorMessage = $_.Exception.Message
        Write-Output $ErrorMessage
        Exit 1
    }
}