Function SetRegValue() {
    $Key = "##Automation--key--##"
    $Value = "##Automation--value--##"
    $Data = "##Automation--data--##"
    $Type = "##Automation--type--##"

    If (Test-Path $Key) {
        New-ItemProperty -Path $Key -Name $Value -Value $Data -PropertyType $Type -Force | Out-Null
    } Else {
        New-Item $Key -Force |
            New-ItemProperty -Name $Value -Value $Data -PropertyType $Type -Force |
            Out-Null
    }
}
