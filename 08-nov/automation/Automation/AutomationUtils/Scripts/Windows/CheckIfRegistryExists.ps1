Function CheckIfRegistryExists() {
    $Key = "##Automation--key--##"
    $Value = "##Automation--value--##"

    If ($Value -eq "None") {
        Test-Path $Key
    } Else {
        If (Test-Path $Key) {
            $temp = (Get-ItemProperty -Path $Key).$Value
            If ($temp -eq $null) {
                return $false
            } Else {
                return $true
            }
        } Else {
            return $false
        }
    }
}
