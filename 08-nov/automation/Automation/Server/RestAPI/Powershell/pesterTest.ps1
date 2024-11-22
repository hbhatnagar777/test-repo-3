# Introduction to Pester testing of CommvaultPowerShell
# Pester is a testing framework for PowerShell. To install Pester, follow these steps:

# With CommvaultPowerShell and Pester installed, you can start writing and running tests to validate PowerShell scripts and functions.
# For more information on using CommvaultPowershell, refer to the documentation: https://github.com/Commvault/CVPowershellSDK
# For more information on using Pester, refer to the documentation: https://pester.dev/docs/introduction/installation

# Command to execute the pestercode:
# Run command as administrator: invoke-Pester {path}\{filename}.ps1 -Output Detailed



# If the CommvaultPowerShell module is not installed, install it
$cvpowershell = Get-Package -Name "CommvaultPowerShell" -ErrorAction SilentlyContinue
if (-not $cvpowershell) {
    Write-Host "Installing CommvaultPowerShell..."
    Install-Module -Name CommvaultPowerShell
}
Write-Host "CommvaultPowerShell is installed"

# If the Pester module is not installed, install it
if (Get-Module -Name "Pester" -ListAvailable) {
	# If the module is installed, get its version
	$moduleVersion = (Get-Module -Name "Pester" -ListAvailable).Version.ToString()
	Write-Host "Pester is installed. Version: $moduleVersion"
	if ($moduleVersion -eq "3.4.0") {
	  Write-Host "Built-in version of Pester found. Uninstalling..."
	  # Uninstall the module
	  $module = "C:\Program Files\WindowsPowerShell\Modules\Pester"
	  takeown /F $module /A /R
	  icacls $module /reset
	  icacls $module /grant "*S-1-5-32-544:F" /inheritance:d /T
	  Remove-Item -Path $module -Recurse -Force -Confirm:$false
	}
} 
$pester = Get-Package -Name "Pester" -ErrorAction SilentlyContinue
if (-not $pester) {
	Write-Host "Installing Pester"
	Install-Module -Name Pester -Force -SkipPublisherCheck
}

#Login
$host_name = Read-Host "Enter the Webconsole host name"
$credential = Get-Credential -Message " "
$username=$credential.GetNetworkCredential().UserName
$password = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes(($credential.GetNetworkCredential().Password)))
Invoke-SetupLogin -Username $username -Password $password -WebServerURL "http://$host_name/webconsole/api"


Describe "Rest API Tests" {
	Context "Company" { 
		It "Get company" {
			$companies = Get-CVCompany
			$hasCompanies = $companies.Count -gt 0
			$hasCompanies | Should -Be $true 
			$companycount = $companies.Count
			Write-Host "Number of Companies: $companycount"
		}
		It "Create Company" {
			$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
			$alias = "newpstest" + $timestamp
			$name = "newpstest" + $timestamp
			$createCompany = New-CVCompany -Alias $alias -Name $name
			$companyId = [int]$createCompany.Id
			Write-Host "Company Id: $companyId "
			$companyId -is [int] | Should -Be $true 
			$TestDrive:companyId = $companyId
		}
		It "Delete Company" {
			$cid = $TestDrive:companyId
			Invoke-CVModifyCompany -CompanyId $cid -OptionDisableBackup -OptionDisableLogin -OptionDisableRestore -StatusDeactivate
			Write-Host "Deactivating Company. id: $cid "
			$removecompany = remove-cvcompany -companyId $cid
			Write-Host "Deleting Company. id: $cid "
			$removecompanystatus = [int]$removecompany.ErrorCode
			Write-Host "error code: $removecompanystatus "
			$removecompanystatus | Should -Be 0 
		}
	}


	Context "Clients" {
		It "Get Clients" {
			$clients=Get-CVClient
			$Clients_count=$clients.Count
			Write-Host "Number of clients: $clients_count"
			$has_clients = $clients_count -gt 0
			$has_clients | Should -Be $true
			$TestDrive:client_id = $clients[0].clientId
		}
		It "Get Client Details" {
			$client_id = $TestDrive:client_id
			$client_props = Get-CVClientProps -Id $client_id
			$name = $client_props.clientName
			$id = $client_props.clientId
			$GUID = $client_props.clientIdGUID
			Write-Host "Client Details:-"
			Write-Host "Client Name: $name"
			Write-Host "Client Id: $id"
			Write-Host "Client Guid: $GUID"
			$has_id = $id -gt 0
			$has_id | Should -Be $true
		}
	}

	Context "Users" {
		It "Get Users" {
			$users=Get-CVUser
			$users_count=$users.Count
			Write-Host "Number of Users: $users_count"
			$has_users = $users_count -gt 0
			$has_users | Should -Be $true
		}
		It "Create User" {
			$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
			$data = [Commvault.Powershell.Models.ICreateUser]@{}
			$data.Email = "abc$timestamp@gmail.com"
			$data.FullName = "psuser$timestamp"
			$data.Name = "psuser$timestamp"
			$data.Password = "Q29tbXZhdWx0ITEy"
			$new_user =  new-cvuser -Users $data 
			$user_id = [int]$new_user.Id
			Write-Host "New user Id: $user_id "
			$user_id -is [int] | Should -Be $true 
			$TestDrive:user_id = $user_id
		}
		It "Delete User" {
			$user_id = $TestDrive:user_id
			$remove_user = remove-cvuser -userId $user_id
			Write-Host "Deleting user id: $user_id "
			$remove_user_status = [int]$remove_user.ErrorCode
			Write-Host "error code: $remove_user_status "
			$remove_user_status | Should -Be 0 
		}
	}


	Context "Usergroup" {
		It "Get Usergroup" {
			$usergroups=Get-CVusergroup
			$usergroups_count=$usergroups.Count
			Write-Host "Number of usergroups: $usergroups_count"
			$has_usergroups = $usergroups_count -gt 0
			$has_usergroups | Should -Be $true
			$TestDrive:usergroup_id = $usergroups[0].Id
		}
		It "Get usergroup Details" {
			$usergroup_id = $TestDrive:usergroup_id
			$usergroup_props = Get-CVusergroupdetail -UserGroupId $usergroup_id
			$name = $usergroup_props.Name
			$GUID = $usergroup_props.GUID
			$description = $usergroup_props.Description
			Write-Host "User Group Details:-"
			Write-Host "Usergroup Name: $name"
			Write-Host "Usergroup Guid: $GUID"
			Write-Host "Usergroup Description: $description"
			Write-Host "Usergroup Id: $usergroup_id"
			$name -is [string] | Should -Be $true
		}
	}

	Context "Servergroup" {
		It "Get Servergroup" {
			$Servergroups=Get-CVServergroup
			$Servergroups_count=$Servergroups.Count
			Write-Host "Number of Servergroups: $Servergroups_count"
			$has_Servergroups = $Servergroups_count -gt 0
			$has_Servergroups | Should -Be $true
			$TestDrive:Servergroup_id = $Servergroups[0].Id
		}
		It "Get Servergroup Details" {
			$Servergroup_id = $TestDrive:Servergroup_id
			$Servergroup_props = Get-CVServerGroupIdDetail -ServerGroupId $Servergroup_id
			$name = $Servergroup_props.ServerGroupName
			$id = $Servergroup_props.ServerGroupId
			$description = $Servergroup_props.Description
			Write-Host "Server Group Details:-"
			Write-Host "Servergroup Name: $name"
			Write-Host "Servergroup id: $id"
			Write-Host "Servergroup Description: $description"
			$name -is [string] | Should -Be $true
		}
	}

}




