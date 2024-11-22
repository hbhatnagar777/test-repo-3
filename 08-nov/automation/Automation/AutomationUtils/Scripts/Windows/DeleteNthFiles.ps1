Function DeleteNthFiles(){
    $target_dir = "##Automation--directory--##"
    $delete_factor = ##Automation--deletefactor--##
    $keep_factor = ##Automation--keepfactor--##
    $file_counter = 0
    if($delete_factor -gt 0){
        Get-ChildItem $target_dir | SELECT FullName | ForEach-Object {
            $file_counter = $file_counter + 1
            if($file_counter%$delete_factor -eq 0){
                Remove-Item -Force $_.FullName
            }
        }
    }
    else{
        Get-ChildItem $target_dir | SELECT FullName | ForEach-Object {
            $file_counter = $file_counter + 1
            if($file_counter%$keep_factor -ne 0){
                Remove-Item -Force $_.FullName
            }
        }
    }
}