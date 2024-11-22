Function MountNetworkPath() {
    $NetworkPath = "##Automation--network_path--##"
    $Username = "##Automation--username--##"
    $Password = "##Automation--password--##"
	$Drive = 'Z'

    While (Test-Path ($Drive + ':')) {
        $Drive = [int][char]$Drive
        $Drive--
        $Drive = [char]$Drive
    }

    $Drive = ($Drive + ':')

    net use $Drive $NetworkPath /user:$Username $Password | Out-Null

    return $Drive
}
