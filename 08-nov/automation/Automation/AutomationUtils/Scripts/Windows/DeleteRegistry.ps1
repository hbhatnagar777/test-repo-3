Function DeleteRegistry() {
    $Key = "##Automation--key--##"
    $Value = "##Automation--value--##"

    If ($Value -eq "None") {
        Remove-Item -Path $Key -Force
    } Else {
        Remove-ItemProperty -Path $Key -Name $Value -Force
    }
}
