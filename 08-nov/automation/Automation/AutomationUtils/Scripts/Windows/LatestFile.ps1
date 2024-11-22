Function Main() {
    $FolderPath = "##Automation--folder_path--##"
    $Type = "##Automation--type--##"
    if ($Type -eq "FILE") {
        $Dir = Get-ChildItem $FolderPath | ? {! $_.PSIsContainer } | sort LastWriteTime | select -last 1 | select Name
    } elseif ($Type -eq "FOLDER") {
        $Dir = Get-ChildItem $FolderPath | ? { $_.PSIsContainer } | sort LastWriteTime | select -last 1 | select Name
    } else {
        throw "Invalid type provided"
    }
    return $Dir
}
