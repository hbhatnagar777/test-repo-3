Function Main
{

	$PWD = "##Automation--LoginPassword--##"
	$LoginUser= "##Automation--LoginUser--##"
	$UserName= "##Automation--UserName--##"
    $OpType = "##Automation--OpType--##"
    $servername = "##Automation--ServerName--##"
    $attribute= "##Automation--attribute--##"
	$attributevalue= "##Automation--AttributeValue--##"
	$CompName="##Automation--CompName--##"
	$UserPrinicpalName="##Automation--UserPrincipalName--##"
    $attr = @{$attribute=$attributevalue}


    if([string]::IsNullOrWhiteSpace($attributevalue))
    {
   $attributevalue = "None"
    }

    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
    $Session = New-PSSession -ComputerName $CompName -Credential $Credential

   Enter-PSSession $Session
    Import-Module ActiveDirectory
    if ($OpType -eq "NEW_USER")
    {
        # ADDS NEW USER

       New-ADUser -Name $UserName -UserPrincipalName $UserPrincipalName

	Write-Output $UserName
    }
    elseif ( $OpType -eq "DELETE_USER")
    {
		# Delete the User
        Remove-ADUser -Identity $UserName -Confirm:$false -Verbose
    }
    elseif ($OpType -eq "MODIFY_USER")
	{
	Set-ADUser -Identity $UserName @attr

	}
    elseif ($OpType -eq "RETURN_PROPERTY")
    {
        return (Get-AdUser -Identity $UserName -Properties * | Select $attribute)
    }

    $ErrorActionPreference = 'Continue'
}