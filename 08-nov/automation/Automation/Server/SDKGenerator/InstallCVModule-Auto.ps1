#
# Package install script for 'CommvaultPSModule'
#
# Author: Sowmya
# Company: Commvault
#
# Original Source: © 2019 Rogier Langeveld, Waternet, NL
#

Function Main {
   
    Clear-Host

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    #Initialize varibale
    $ScriptDir = "##Automation--ps_path--##"

    $WorkingDir = $PSScriptRoot

    $packageName = "CommvaultRestApi.0.1.0.nupkg"
    $packagePath = $ScriptDir + "\"+ $packageName
    if (-not (Test-Path $packagePath))
    {
    $packagePath = $ScriptDir + "\bin\"+ $packageName
    if (-not (Test-Path $packagePath))
    {
    Write-Host("Please execute the script from the same path where you nuget packages are there")
    }
    }


    try {
        #unBlocking the NUget file
         Write-Host -ForegroundColor Green 'UnBlocking the Nuget Package'
        Unblock-File -Path ($packagePath)

        #Extract the contents
         Write-Host -ForegroundColor Green 'Extracting nuget Package'
        $fileName = [io.path]::GetFileNameWithoutExtension($packageName)
        $file_name_arr = $fileName.split(".")
        $extractDir = $ScriptDir + "\"+ $file_name_arr[0]       
        Rename-Item -Path $packagePath -NewName ([io.path]::ChangeExtension($packageName, '.zip')) -Verbose
        $zippackagePath = $packagePath.Replace("nupkg", "zip")
        Expand-Archive $zippackagePath -DestinationPath $extractDir

        #remove unwanted files
        $folderList = @("package","_rels","[Content_Types].xml","CommvaultRestApi.nuspec")
        foreach ($file in $folderList) {
        $filePath = $extractDir + "\"+ $file
         if(Test-Path $filePath)
         {
            Remove-Item -Recurse -Path $filePath -force -ErrorAction Ignore
        }
       }

        #copy the Folder
        Write-Host -ForegroundColor Green 'Copy the folders to Powershell Module'
        $ModulePaths = $env:PSModulePath.Split(";")
        foreach($path in $ModulePaths){
        $path_check =$path+ '\CommvaultRestApi'
        if (-not (Test-Path $path_check))
        {
        Copy-Item -Recurse -Path $extractDir -Destination $path -Confirm:$False -Force
        }
        }

        #Import Module 
        #Import-Module CommvaultRestAPi  
        Write-Host -ForegroundColor Green 'Imported the Module Sucessfully'
                 
            
    }
    catch {
        throw $_
    }
    }      
 