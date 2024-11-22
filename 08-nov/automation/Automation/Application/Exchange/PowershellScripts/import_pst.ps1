##########################################################################################################################
#
# This powershell script is to import a PST File to a Mailbox
#
###########################################################################################################################
Function Main()
{

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$aliasname = "##Automation--aliasName--##"
$ExchangeCASServer = "##Automation--ExchangeCAServer--##"
$path = "##Automation--PstPath--##"
$ErrorActionPreference = 'Stop'
$global:ErrorCode = 0

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
$UPN=$aliasname+"@"+$ExchangeServerDomain

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$ExchangeCASServer/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session

Try{
        $importPST = New-MailboxImportRequest -Mailbox $aliasname -FilePath $path  -TargetRootFolder /|fw requestguid | Out-String
            #use polling
            $completed = $false

            # Set timeout for pst import request
            $timeout = New-TimeSpan -Minutes 20
            $sw = [diagnostics.stopwatch]::StartNew()

            # Poll for every 30 seconds
            while($sw.elapsed -lt $timeout)
            {
                if(-not $completed)
                {
                    $ImportStatus=Get-MailboxImportRequest -Identity $importPST | Where-Object { $_.Status -notmatch "Completed"}
                    if(-not $ImportStatus)
                    {
                        $completed = $true
                        EXIT 0
                    }

                }

                # sleep for 30 seconds
                write-host "waiting for 30 sec"
                Start-Sleep -Seconds 30
            }

            # Throw exception if import request is not completed in 20 min
            if (-not $completed)
            {
                write-host "Failed to import pst"
                EXIT 1
            }

  }
Catch{

  $global:ErrorCode = 1
}



}