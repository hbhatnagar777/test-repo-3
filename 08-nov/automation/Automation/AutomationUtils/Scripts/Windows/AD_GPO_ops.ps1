##############################
# File for AD GPO operations #
##############################


Function Main()
{

	$PWD = "##Automation--LoginPassword--##"
	$LoginUser= "##Automation--LoginUser--##"
	$GPOName= "##Automation--GPOName--##"
    $OpType = "##Automation--OpType--##"
    $servername = "##Automation--ServerName--##"
    $domain = "##Automation--Domain--##"
    $ou = "##Automation--OU--##"
    $attribute = "##Automation--Attribute--##"
	$attributevalue= "##Automation--AttributeValue--##"
    if([string]::IsNullOrWhiteSpace($attributevalue))
    {
   $attributevalue = "None"
    }

    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
    $Session = New-PSSession -ComputerName $servername -Credential $Credential

   Enter-PSSession $Session
    Import-Module ActiveDirectory
    if ($OpType -eq "CREATE_GPO")
    {
        # Create a GPO
        New-GPO -Name $GPOName
    }
    elseif ($OpType -eq "SET_PROP")
    {
        # Sets the property of a GPO
        $value = [int]$attributevalue
		Set-GPRegistryValue -Name $GPOName -Key 'HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop' -ValueName $attribute -Value $value -Type 'DWORD'
    }

    elseif ( $OpType -eq "DELETE")
    {
		# Delete the GPO
        Remove - GPO $GPOName
    }

    elseif( $OpType -eq "GET_PROP")
    {
        # Gets the property of a GPO
		$result = Get-GPRegistryValue -Name $GPOName -Key 'HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop' -ValueName $attribute | ft Value -HideTableHeaders | out-string
        return [int]$result

    }
    elseif ($OpType -eq "NEW_GPLINK")
    {
        # Sets the new link for the GPO
		New-GPLink -Name $GPOName -Target $ou -Domain $domain -Server $Server
    }

    elseif ($OpType -eq "REMOVE_GPLINK")
    {
		# Delete the GPO link
        Remove-GPLink -Name $GPOName -Target $ou -Domain $domain -Server $Server

    }

    elseif( $OpType -eq "GET_GPLINKS")
    {
        # Gets the gpo links of an OU
	$result = @(Get-GPInheritance -Target $ou | Select-Object -ExpandProperty GpoLinks).Count
        return $result

    }

    elseif($OpType -eq "GPLINKS_ATT")
    {
        # Gets the gpo links of an OU
    $result = (Get-GPInheritance -Target $ou | Select-Object -ExpandProperty GpoLinks | Where-Object { $_.DisplayName -eq "$GPOName"}|Select-Object Enabled, Enforced)
    return $result
    }

    elseif($OpType -eq "GPLINKS_PROP")
    {
        # Gets the Properties of GPO
    $result =(Get-GPO -Name $GPOName|Select-Object Id, GpoStatus)
    return $result

    }

    elseif($OpType -eq "SET_STATUS")
    {
        # Change the status of GPO
    (Get-GPO -Name $GPOName).gpostatus = $Status

    }

    elseif($OpType -eq "SET_ADLINKS")
    {
        # Change the Advance GPOLinks options
        Set-GPLink -Name $GPOName -Target $ou -LinkEnabled $GpoEnable -Enforced $GpoEnforced

    }

    elseif( $OpType -eq "GPLINK_ID")
    {
        # Gets the gpo links of an OU
	$result = (Get-GPInheritance -Target $ou | Select-Object -ExpandProperty GpoLinks).GpoId
    return $result

    }

    $ErrorActionPreference = 'Continue'
}
