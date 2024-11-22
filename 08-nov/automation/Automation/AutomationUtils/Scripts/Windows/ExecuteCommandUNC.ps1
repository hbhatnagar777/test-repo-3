Function ExecuteCommandUNC()
{
$path = '##Automation--path--##'


$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($using:Credentials.Password)
$Plaintext = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
$username= $using:Credentials.username
$path1=Split-Path -Path $path
net use $path1 /user:$username $Plaintext | Out-Null

##Automation--command--##


}
