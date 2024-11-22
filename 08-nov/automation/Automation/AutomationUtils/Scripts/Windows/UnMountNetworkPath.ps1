Function UnMountNetworkPath() {
    $Drive = "##Automation--drive--##"
    $NetworkObject = New-Object -ComObject WScript.Network
	$NetworkObject.RemoveNetworkDrive($Drive)
}
