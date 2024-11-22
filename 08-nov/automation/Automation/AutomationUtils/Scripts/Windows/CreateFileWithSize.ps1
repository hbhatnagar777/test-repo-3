Function CreateFilewithSize() {
    $FilePath = "##Automation--FilePath--##"
    $Size = ##Automation--Size--##
    $enc = [system.Text.Encoding]::UTF8
    $FilePathHandle = New-object System.io.fileStream  $FilePath, create, ReadWrite
    $Str1 = "this is test data created by script"
    $Data1 = $enc.Getbytes($Str1)
	$FilePathHandle.write($Data1,0,$Data1.Length)
	$FilePathHandle.setLength($Size)
	$FilePathHandle.Close()
}
