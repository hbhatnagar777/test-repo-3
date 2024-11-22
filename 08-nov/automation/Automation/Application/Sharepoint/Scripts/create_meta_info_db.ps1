Function CreateMetaInfoDB()
{
	#read in arguments
	$metaFile = "##Automation--MetaFile--##"
	$url = "##Automation--WebappURL--##"

	#load snapins and modules
	Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue
	Import-Module "WebAdministration"

	$ErrorActionPreference = "Stop"
	try
	{
		$Username = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

		Start-SPAssignment -Global

		$w = Get-SPWebApplication -Identity $url
		$w.GrantAccessToProcessIdentity($Username)

		#gather necessary items
		$url = $url.Substring(0, $url.Length - 1)

		$webAppName = (Get-SPWebApplication $url).DisplayName
		$port = (Get-WebBinding $webAppName).bindingInformation
		$port = $port.Replace(":", "")
		$siteCount = (Get-SPSite ($url + "*")).WebApplication.Sites.Count
		$poolAcct = (Get-SPManagedAccount -WebApplication $url).UserName
		$contentDb = (Get-SPContentDatabase -webapplication $url).Name

		Stop-SPAssignment -Global

		#write to file
		$fileStream = [System.IO.StreamWriter]$metaFile
		$fileStream.WriteLine($webAppName)
		$fileStream.WriteLine($port)
		$fileStream.WriteLine($siteCount)
		$fileStream.WriteLine($poolAcct)
		$fileStream.WriteLine($contentDb)

		$fileStream.close()

	}
	catch
	{
		$ErrorMessage = $_.Exception.Message
		Write-Output $ErrorMessage
		Exit 1
	}

}