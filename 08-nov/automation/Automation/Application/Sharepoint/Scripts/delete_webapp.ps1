Function DeleteWebapp()
{
	#read in arguments
	$url = "##Automation--WebappURL--##"

	#load snapins and modules
	Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue

	$ErrorActionPreference = "Stop"

	try
	{
		Remove-SPWebApplication $url -DeleteIISSite -RemoveContentDatabases -Confirm:$false

		Exit 0
	}
	catch
	{
		$ErrorMessage = $_.Exception.Message
		Write-Output $ErrorMessage
		Exit 1
	}
}
