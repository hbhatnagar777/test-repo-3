Function RenameItem() {
    $OldName = "##Automation--old_name--##"
    $NewName = "##Automation--new_name--##"
    Rename-Item $OldName $NewName -Force | Out-Null
}
