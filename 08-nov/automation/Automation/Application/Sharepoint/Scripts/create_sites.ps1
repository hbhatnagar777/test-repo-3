Function CreateSiteCollection()
{
    #read in arguments
    $siteUrl = "##Automation--SiteURL--##"
    $siteOwner = "##Automation--SiteOwner--##"
    $template = "##Automation--SiteTemplate--##"
    $siteTitle = "##Automation--SiteTitle--##"
    $siteCount = "##Automation--SiteCount--##"

	if (!($siteCount -ge 1))
	{
		Write-Output "Error: Site Count must be 1 or greater"
		Exit 1
	}

	Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue

	$ErrorActionPreference = "Stop"
	try
	{

		Start-SPAssignment -Global

		[Microsoft.SharePoint.SPSecurity]::RunWithElevatedPrivileges({
			if ($siteCount -eq 1)
			{
				New-SPSite ($siteUrl) -OwnerAlias $siteOwner -Name $siteTitle -Template $template
			}
			else
			{
				for ($i = 0; $i -le $siteCount - 1; $i++){
					if ($i -eq 0)
					{
						New-SPSite ($siteUrl) -OwnerAlias $siteOwner -Name $siteTitle -Template $template
					}
					else
					{
						New-SPSite ($siteUrl + $i) -OwnerAlias $siteOwner -Name ($siteTitle + "-" + $i) -Template $template
					}
				}
			}
		})

		Stop-SPAssignment -Global
		Exit 0
	}
	catch
	{
		$ErrorMessage = $_.Exception.Message
		Write-Output $ErrorMessage
		Exit 1
	}
}