#####################################
# File for AD Attributes operations #
#####################################


Function Main()
{

	$PWD = "##Automation--LoginPassword--##"
	$LoginUser= "##Automation--LoginUser--##"
    $OpType = "##Automation--OpType--##"
    $servername = "##Automation--ServerName--##"
    $attribute = "##Automation--Attribute--##"
	$attributevalue= "##Automation--Value--##"
    $entity= "##Automation--EntityName--##"

    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
    $Session = New-PSSession -ComputerName $servername -Credential $Credential

   Enter-PSSession $Session
    Import-Module ActiveDirectory
    if ($attributevalue -eq "None"){
        # Sets the attribute value to null
        $attributevalue = $null
    }
    if ($OpType -eq "SET_ATTRIBUTE")
    {
        # Sets the attribute value of an entity
        $attr = @{$attribute=$attributevalue}
	    Set-ADUser -Identity $entity @attr

    }
    elseif( $OpType -eq "GET_ATTRIBUTE")
    {
        # Gets the attribute value of an entity
	    $result = Get-ADUser -Identity $entity -Properties * | select $attribute | Format-Table -HideTableHeaders | Out-String
        return $result

    }
    elseif( $OpType -eq "CREATE_USER")
    {
    # Creates the new user
    New-ADUser -Name $entity
    }
    elseif( $OpType -eq "DELETE_USER")
    {
    # Deletes the user
    Remove-ADUser -Identity $entity
    }
    
    $ErrorActionPreference = 'Continue'
}
