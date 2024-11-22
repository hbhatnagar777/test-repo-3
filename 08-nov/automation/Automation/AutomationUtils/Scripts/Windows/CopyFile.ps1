Function CopyFolder() {
    $Source = "##Automation--source--##"
    $Destination = "##Automation--destination--##"

	$FileName = "##Automation--file_name--##"

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


    if ($temp1.IsUnc)
    {
        $Password_1 = $Password_1|ConvertTo-SecureString -AsPlainText -Force
        $Cred_1= New-Object System.Management.Automation.PsCredential($Username_1,$Password_1)
        New-PSDrive -Name $Drive_1 -PSProvider "FileSystem" -Root $NetworkPath_1 -Credential $Cred_1 | Out-Null
    }
    if ($temp2.IsUnc)
    {
        $Password_2 = $Password_2|ConvertTo-SecureString -AsPlainText -Force
        $Cred_2 = New-Object System.Management.Automation.PsCredential($Username_2,$Password_2)
        New-PSDrive -Name $Drive_2 -PSProvider "FileSystem" -Root $NetworkPath_2 -Credential $Cred_2 | Out-Null
    }

	robocopy $Source $Destination $FileName /r:10 /NP /NFL /NDL

	if ($LastExitCode -gt 1) {
    # an error occurred
    exit 1
    }

	if ($temp1.IsUnc)
	{
		$NetworkObject = New-Object -ComObject WScript.Network
		$NetworkObject.RemoveNetworkDrive($Drive)
	}

	if ($temp1.IsUnc)
	{
		$NetworkObject = New-Object -ComObject WScript.Network
		$NetworkObject.RemoveNetworkDrive($Drive)
	}

 }