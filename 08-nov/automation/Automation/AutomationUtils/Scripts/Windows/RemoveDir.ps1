Function RemoveDir() {
    $DirectoryName = "##Automation--directory_name--##"
    $isUnc = ##Automation--isUnc--##
    if($isUnc){
        $Username = "##Automation--username--##"
        $Password= "##Automation--password--##"
        $NetworkPath= "##Automation--network_path--##"
        $Drive = "##Automation--drive--##"

        $NetworkPath = $NetworkPath | split-path
        $Password = $Password|ConvertTo-SecureString -AsPlainText -Force
        $Cred = New-Object System.Management.Automation.PsCredential($Username,$Password)
        New-PSDrive -Name $Drive -PSProvider "FileSystem" -Root $NetworkPath -Credential $Cred | Out-Null

        Remove-Item $DirectoryName -Force -Recurse
        Remove-PSDrive $Drive
    }
    else{
        $NoOfDays = ##Automation--days--##
        $CleanUpDate = (Get-Date).AddDays(-$NoOfDays)

        # Need to check why Get-ChildItem -Path does not remove -Path
        Get-ChildItem -Path $DirectoryName -Recurse -Directory  | Where-Object {$_.CreationTime -le $CleanUpDate -or $_.LastWriteTime -le $CleanUpDate} | Remove-Item -Recurse -Force | Out-Null
        if( -not(Get-Item -Path $DirectoryName | Where-Object {$_.CreationTime -le $CleanUpDate -or $_.LastWriteTime -le $CleanUpDate} | Remove-Item -Recurse -Force | Out-Null ))
        {exit 1}
    }
}
