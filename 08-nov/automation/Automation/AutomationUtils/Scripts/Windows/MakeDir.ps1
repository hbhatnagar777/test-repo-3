Function MakeDir() {
    $DirectoryName = "##Automation--directory_name--##"
    $Username = "##Automation--username--##"
    $Password= "##Automation--password--##"
    $NetworkPath= "##Automation--network_path--##"
    $Drive = "##Automation--drive--##"
    $ForceCreate = ##Automation--force_create--##

    $temp = [System.Uri]$NetworkPath

    if ($temp.IsUnc)
    {
        $NetworkPath = $NetworkPath | split-path
        $Password = $Password|ConvertTo-SecureString -AsPlainText -Force
        $Cred = New-Object System.Management.Automation.PsCredential($Username,$Password)
        New-PSDrive -Name $Drive -PSProvider "FileSystem" -Root $NetworkPath -Credential $Cred | Out-Null
    }

    if ($ForceCreate)
    {
        Remove-Item $DirectoryName -Force -Recurse
    }
    if ( -not (New-Item -Path $DirectoryName -ItemType Directory | out-Null))
    {
        if ($temp.IsUnc)
        {
            Remove-PSDrive $Drive
        }
        exit 1
    }
    if ($temp.IsUnc)
    {
        Remove-PSDrive $Drive
    }
}
