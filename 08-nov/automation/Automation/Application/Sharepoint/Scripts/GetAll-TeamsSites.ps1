# PowerShell Version: 5.1
# This script requires the following PowerShell module:
#   'Sharepoint Online Management Shell' version 16.0.25012.12000 or higher
# It can be installed using this link: https://www.microsoft.com/en-us/download/details.aspx?id=35588

param (
    [Parameter(Position = 0, Mandatory = $true)]
    [string]$SiteAdminUrl,
    [Parameter(Position = 1, Mandatory = $true)]
    [string]$Username,
    [Parameter(Position = 2, Mandatory = $true)]
    [string]$Password
)

$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $Username, $( ConvertTo-SecureString $Password -AsPlainText -Force )
Connect-SPOService -Url $SiteAdminUrl -Cred $credential -WarningAction:SilentlyContinue

try
{
    $allSites = Get-SPOSite -Limit All -WarningAction:SilentlyContinue
    $teamsSites = $allSites | Where-Object { $_.IsTeamsConnected -eq $True } | Select-Object -ExpandProperty Url
    $teamsConnectedSites = $allSites | Where-Object { $_. IsTeamsChannelConnected -eq $True } | Select-Object -ExpandProperty Url

    $fileName = "TeamsSites_$([System.Guid]::NewGuid()).txt"
    $allTeamsSites = ($teamsSites + $teamsConnectedSites) | Sort-Object -Unique
    Set-Content -Path $fileName -Value $allTeamsSites

    Write-Output $fileName
}
catch
{
}
