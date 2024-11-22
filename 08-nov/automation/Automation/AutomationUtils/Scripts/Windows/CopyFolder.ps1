Function CopyFolder() {
    $Source = "##Automation--source--##"
    $Destination = "##Automation--destination--##"

	$Threads = "##Automation--threads--##"
    $Use_xcopy = "##Automation--use_xcopy--##"
    $Recurse = "##Automation--recurse--##"

    $Username_1 = "##Automation--username_1--##"
    $Password_1= "##Automation--password_1--##"
    $NetworkPath_1= "##Automation--network_path_1--##"
    $Drive_1 = "##Automation--drive_1--##"

    $Username_2 = "##Automation--username_2--##"
    $Password_2= "##Automation--password_2--##"
    $NetworkPath_2= "##Automation--network_path_2--##"
    $Drive_2 = "##Automation--drive_2--##"



    $temp1 = [System.Uri]$NetworkPath_1
    $temp2 = [System.Uri]$NetworkPath_2

    $Destination = ($Destination + "\" + ($Source | split-path -Leaf))


    if ($temp1.IsUnc)
    {
        $NetworkPath_1 = $NetworkPath_1 | split-path
        $Password_1 = $Password_1|ConvertTo-SecureString -AsPlainText -Force
        $Cred_1= New-Object System.Management.Automation.PsCredential($Username_1,$Password_1)
        New-PSDrive -Name $Drive_1 -PSProvider "FileSystem" -Root $NetworkPath_1 -Credential $Cred_1 | Out-Null
    }
    if ($temp2.IsUnc)
    {
        $NetworkPath_2 = $NetworkPath_2 | split-path
        $Password_2 = $Password_2|ConvertTo-SecureString -AsPlainText -Force
        $Cred_2 = New-Object System.Management.Automation.PsCredential($Username_2,$Password_2)
        New-PSDrive -Name $Drive_2 -PSProvider "FileSystem" -Root $NetworkPath_2 -Credential $Cred_2 | Out-Null
    }

	New-Item -Force -ItemType directory -Path $Destination
	
	if ($Use_xcopy -eq $true)
	{
	    if ($Recurse -eq $true){
	        xcopy $Source $Destination /E /H /C /I
	    }
	    else{
	        xcopy $Source $Destination /H /C /I
	    }
	}
    else
    {
        if ($Recurse -eq $true){
            robocopy $Source $Destination /e /r:10 /MT:$Threads /NP /NFL /NDL
        }
        else{
            robocopy $Source $Destination /r:10 /MT:$Threads /NP /NFL /NDL
        }
    }

	if ($LastExitCode -gt 1) {
    # an error occurred
    exit 1
    }

	if ($temp1.IsUnc)
	{
		Remove-PSDrive $Drive_1
	}

	if ($temp2.IsUnc)
	{
		Remove-PSDrive $Drive_2
	}

 }