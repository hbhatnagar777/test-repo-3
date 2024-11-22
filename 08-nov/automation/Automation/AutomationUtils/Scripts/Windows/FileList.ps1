Function Main() {
    $FolderPath = "##Automation--folder_path--##"
    $Type = "##Automation--type--##"
    $Recurse = "##Automation--Recurse--##"
    $OnlyHidden = "##Automation--OnlyHidden--##"
    $DaysOld = "##Automation--DaysOld--##"

    $parameters = @{
        Path = $FolderPath
        Recurse = [bool]::Parse($Recurse)
        Hidden = [bool]::Parse($OnlyHidden)
    }

    $CutoffDate = (Get-Date).AddDays(-[int]$DaysOld)

    if ($Type -eq "FILE") {
        $Dir = Get-ChildItem @parameters | Where-Object {
            $_.PSIsContainer -eq $false -and $_.LastWriteTime -lt $CutoffDate
        } | Select FullName
    } elseif ($Type -eq "FOLDER") {
        $Dir = Get-ChildItem @parameters | Where-Object {
            $_.PSIsContainer -eq $true -and $_.LastWriteTime -lt $CutoffDate
        } | Select FullName
    } else {
        throw "Invalid type provided"
    }
    
    return $Dir -replace '\s+', ' '
}
