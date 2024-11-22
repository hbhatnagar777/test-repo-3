Function GetSize() {
    $Username = "##Automation--username--##"
    $Password = "##Automation--password--##"
    $NetworkPath = "##Automation--network_path--##"
    $Drive = "##Automation--drive--##"
    $Path = "##Automation--path--##"
    $Type = "##Automation--type--##"

    $temp = [System.Uri]$NetworkPath

    if ($temp.IsUnc)
    {
        $Password = $Password|ConvertTo-SecureString -AsPlainText -Force
        $Cred = New-Object System.Management.Automation.PsCredential($Username,$Password)
        New-PSDrive -Name $Drive -PSProvider "FileSystem" -Root $NetworkPath -Credential $Cred | Out-Null
    }

    $FSobject = New-Object -ComObject Scripting.FileSystemObject

    If ($Type -eq "Folder") {
        $Size = $FSobject.GetFolder($Path).Size
        return $Size
    } ElseIf ($Type -eq "File") {
        $Size = $FSobject.GetFile($Path).Size
        return $Size
    } Else {
        return "Type Not Supported"
    }
}
