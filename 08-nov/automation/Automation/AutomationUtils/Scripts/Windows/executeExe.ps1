Function ExecuteExe() {
    $exe_path = "##Automation--exe_path--##"    
    $exe_command =  [string]::Format("& '{0}'",$exe_path)
    $result = iex $exe_command
    return $result
}