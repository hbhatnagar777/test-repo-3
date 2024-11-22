Function UploadFile()
{
	#read in arguments
	$webUrl = "##Automation--SiteURL--##"
	$libName = "##Automation--LibraryName--##"
	$filePath = "##Automation--FilePath--##"

    #load snapins and modules
	Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue

	$ErrorActionPreference = "Stop"
	try
	{

		Start-SPAssignment -Global

		[Microsoft.SharePoint.SPSecurity]::RunWithElevatedPrivileges({
			$spWeb = Get-SPWeb -Identity $webUrl
			$spWeb.AllowUnsafeUpdates = $true;
			$List = $spWeb.Lists.TryGetList($libName)
			$folder = $List.RootFolder

			$files = Get-ChildItem -Path $filePath

			$i = 0
			foreach ($file in $files)
			{
				$i++
				$fCount = $files.Count
				$FileName = $file.Name

				$spFile = $spWeb.GetFile($spWeb.ServerRelativeUrl + $folder.Url + "/" + $FileName)

				if ($spFile.Exists -eq $true)
				{
					Write-Host "File $FileName already exists in library $libName!"

					if (!($i -eq $fCount))
					{
						Write-Host "Checking next file to copy"
					}
				}
				else
				{
					$fileStream = $file.OpenRead()

					write-host -NoNewLine "Copying file " $File.Name " to " $folder.ServerRelativeUrl "..."
					$spFile = $folder.Files.Add($spWeb.ServerRelativeUrl + $folder.Url + "/" + $FileName, $fileStream, $true)
					write-host "...Success!"

					$fileStream.Close()
				}
			}
			$spWeb.AllowUnsafeUpdates = $false;
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