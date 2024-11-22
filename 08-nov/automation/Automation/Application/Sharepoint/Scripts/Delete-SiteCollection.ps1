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
    [string]$Password,
    [Parameter(Position = 3, Mandatory = $true)]
    [string]$SiteUrl,
    [Parameter(Position = 4, Mandatory = $true)]
    [string]$DeletionType
)

$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $Username, $( ConvertTo-SecureString $Password -AsPlainText -Force )
Connect-SPOService -Url $SiteAdminUrl -Cred $credential -WarningAction:SilentlyContinue

try
{
    $site = Get-SPOSite -Identity $siteUrl -ErrorAction Stop -WarningAction:SilentlyContinue
}
catch
{
    Write-Output 2
    exit 0
}

try
{
    if ("full" -eq $DeletionType)
    {
        Remove-SPOSite -Identity $SiteUrl -Confirm:$false -WarningAction:SilentlyContinue
    }
    Remove-SPODeletedSite -identity $SiteUrl -Confirm:$false -WarningAction:SilentlyContinue
}
catch
{
    Write-Output 1
    exit 0
}

try
{
    $deletedSite = Get-SPODeletedSite -Identity $SiteUrl -Confirm:$false -WarningAction:SilentlyContinue
    Write-Output 1
}
catch
{
    try
    {
        $site = Get-SPOSite -Identity $SiteUrl -Confirm:$false -WarningAction:SilentlyContinue
        Write-Output 1
    }
    catch
    {
        Write-Output 0
    }
}
