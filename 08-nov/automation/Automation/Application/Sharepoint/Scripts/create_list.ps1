Function CreateList()
{
	#read in arguments
	$url = "##Automation--SiteURL--##"
	$libName = "##Automation--LibraryName--##"
	$listType = "##Automation--ListTemplate--##"

	#load snapins and modules
	Add-PSSnapin "Microsoft.SharePoint.PowerShell" -ErrorAction SilentlyContinue

	$ErrorActionPreference = "Stop"
	try
	{
		Start-SPAssignment -Global

		switch ($listType)
		{
			"C" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::Events
			}
			"T" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::Tasks
			}
			"F" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::XMLForm
			}
			"D" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::DocumentLibrary
			}
			"P" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::PictureLibrary
			}
			"A" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::Announcements
			}
			"X" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::Contacts
			}
			"L" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::Links
			}
			"PT" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::GanttTasks
			}
			"W" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::WebPageLibrary
			}
			"I" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::IssueTracking
			}
			"DB" {
				$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::DiscussionBoard
			}
		}

		[Microsoft.SharePoint.SPSecurity]::RunWithElevatedPrivileges({
			$spWeb = Get-SPWeb -Identity $url
			$spListCollection = $spWeb.Lists
			$spLibrary = $spListCollection.TryGetList($libName)

			if ($spLibrary -ne $null)
			{
				Write-Host "Library $libName already exists in the site"
				Exit 1
			}
			else
			{
				Write-Host "Creating Library - $libName"
				$dateTime = Get-Date -format "dd-MMM HH:mm:ss"
				$spLibrary = $spListCollection.Add($libName, "Created by Automation setup: $dateTime", $listTemplate)
				$spList = $spWeb.Lists.item($spLibrary)
				$spList.OnQuickLaunch = "True"
				$spList.Update()
				Write-Host "Library created successfully!"
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