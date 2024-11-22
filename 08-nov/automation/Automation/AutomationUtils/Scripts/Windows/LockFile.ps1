Function GetLock() { 

##################################################################################################

#-------------------Execution starts here -------------------------------------------------------#


$Path_str = "##Automation--path--##"         #string
$time = "##Automation--timeout--##"         #string
$mode = "Open"
$access = "Read"
$share = "None"
$filepointer = New-Object System.Collections.ArrayList

$arr = $Path_str -split ','

Foreach ($file in $arr)
{

$file = [System.IO.File]::Open($file, $mode, $access, $share)
$filepointer.add($file)

}
Start-Sleep -s $time

Foreach ($ptr in $filepointer)
{

$file.close()

}

##################################################################################################

}
