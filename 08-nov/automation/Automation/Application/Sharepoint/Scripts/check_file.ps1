Function CheckFile()
{
	#read in arguments
	$webUrl = "##Automation--SiteURL--##"
	$libName = "##Automation--LibraryName--##"
	$fileName = "##Automation--FileName--##"

    #load snapins and modules
	Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue

	$ErrorActionPreference = "Stop"
	try
	{

		Start-SPAssignment -Global

		[Microsoft.SharePoint.SPSecurity]::RunWithElevatedPrivileges({
			$spWeb = Get-SPWeb -Identity $webUrl
			$List = $spWeb.Lists.TryGetList($libName)
			$folder = $List.RootFolder

			$spFile = $spWeb.GetFile($spWeb.ServerRelativeUrl + $folder.Url + "/" + $fileName)

			if ($spFile.Exists -eq $true)
			{
				Write-Host "File $fileName exists in library $libName!"
			}
			else
			{
				Write-Host "File $fileName does not exist in library $libName!"
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