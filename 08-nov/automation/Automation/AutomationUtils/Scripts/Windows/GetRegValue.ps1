Function GetRegValue() {
    $Key = "##Automation--key--##"
    $Value = "##Automation--value--##"

    If (Test-Path $Key) {
        (Get-ItemProperty -Path $Key).$Value
    }
}
