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
    [string]$SiteTitle
)

$template = "STS#3"  # STS#3 is for a modern team site without an Office 365 group
$storageQuota = 1024  # in MB

$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $Username, $( ConvertTo-SecureString $Password -AsPlainText -Force )
Connect-SPOService -Url $SiteAdminUrl -Cred $credential -WarningAction:SilentlyContinue

try
{
    $site = Get-SPOSite -Identity $SiteUrl -ErrorAction Stop -WarningAction:SilentlyContinue
    Write-Output 2
}
catch
{
    New-SPOSite -Url $SiteUrl -Owner $Username -StorageQuota $storageQuota -Template $template -Title $SiteTitle -WarningAction:SilentlyContinue
    try
    {
        $site = Get-SPOSite -Identity $SiteUrl -ErrorAction Stop -WarningAction:SilentlyContinue
        Write-Output 0
    }
    catch
    {
        Write-Output 1
    }
}
