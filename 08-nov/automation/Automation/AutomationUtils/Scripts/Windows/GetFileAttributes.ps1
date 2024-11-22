Function getFileAttributes() {
 $FilePath = "##Automation--FilePath--##" 
 $attrib = (Get-ItemProperty -Path $FilePath).attributes
 return $attrib
 }