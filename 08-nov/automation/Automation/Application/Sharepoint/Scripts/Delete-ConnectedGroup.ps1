# PowerShell Version: 5.1
# This script requires the following PowerShell module:
#   AzureAD version 2.0.2.182 or higher
# It can be installed with the PowerShell command: 'Install-Module -Name AzureAD -RequiredVersion 2.0.2.182 -AllowClobber -Force'

param (
    [Parameter(Position = 0, Mandatory = $true)]
    [string]$Username,
    [Parameter(Position = 1, Mandatory = $true)]
    [string]$Password,
    [Parameter(Position = 2, Mandatory = $true)]
    [string]$GroupName
)

$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $Username, $(ConvertTo-SecureString $Password -AsPlainText -Force)
$login = Connect-AzureAD -Credential $credential -WarningAction:SilentlyContinue

$GroupId = $null

try
{
    $Group = Get-AzureADGroup -Filter "DisplayName eq '$GroupName'" -WarningAction:SilentlyContinue
    $GroupId = $Group | Select-Object -ExpandProperty ObjectId
}
catch
{
    Write-Output 2
}

if ($null -ne $GroupId)
{
    try
    {
        Remove-AzureADGroup -ObjectId $GroupId -WarningAction:SilentlyContinue
        Write-Output 0
    }
    catch
    {
        Write-Output 1
    }
}
