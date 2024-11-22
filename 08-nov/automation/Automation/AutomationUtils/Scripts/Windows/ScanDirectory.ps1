Function ScanDirectory(){

    $recursive = "##Automation--recursive--##"
    $recursive_flag = $recursive -eq "yes"
    $path ='##Automation--path--##'

    $items = Get-ChildItem $path -recurse:$recursive_flag | foreach-object{
        $type = 'file'
        $attrs = [string] $_.Attributes
        if($attrs.contains('Directory')){
            $type = 'directory'
        }
        $modified_time = [Int] (New-TimeSpan -Start (Get-Date -Date '01/01/1970') -End $_.LastWriteTime).TotalSeconds
        return "{0}`t{1}`t{2}`t{3}" -f $_.FullName, $type, $_.Length, $modified_time
    }

    return $items
}