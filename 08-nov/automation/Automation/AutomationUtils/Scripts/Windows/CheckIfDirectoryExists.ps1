Function CheckIfDirectoryExists() {
    $DirectoryPath = "##Automation--directory_path--##"

    $Username = "##Automation--username--##"
    $Password= "##Automation--password--##"
    $NetworkPath= "##Automation--network_path--##"
    $Drive = "##Automation--drive--##"

    $temp = [System.Uri]$NetworkPath

    if ($temp.IsUnc)
    {
        $Password = $Password|ConvertTo-SecureString -AsPlainText -Force
        $Cred = New-Object System.Management.Automation.PsCredential($Username,$Password)
        New-PSDrive -Name $Drive -PSProvider "FileSystem" -Root $NetworkPath -Credential $Cred | Out-Null
    }
    Test-Path $DirectoryPath
}
