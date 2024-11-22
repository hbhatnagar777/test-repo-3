Function CreateFile() {
    $Path = "##Automation--path--##"
    $Content = "##Automation--content--##"
    
    if($path.StartsWith('\\'))
    {
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($using:Credentials.Password)
    $Plaintext = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    $username= $using:Credentials.username
    $path1=Split-Path -Path $path
    net use $path1 /user:$username $Plaintext | Out-Null
    }


    New-Item -Path $Path -ItemType 'File' -Force | Out-Null
    $Content | Set-Content $Path -Force
}
