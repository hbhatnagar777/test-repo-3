Function Main
{

$User = "##Automation--AzureUsername--##"
$Password="##Automation--AzurePassword--##"
$UserId="##Automation--UserId--##"
$GroupId="##Automation--GroupObjectId--##"
$OpType='##Automation--OpType--##'

$PWord = ConvertTo-SecureString -String $Password -AsPlainText -Force
$Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord
$Connected=Connect-AzureAD -Credential $Credential

if ($UserId){
    $ObjectId=(Get-AzureADUser -ObjectId $UserId).ObjectId
}

    if ($OpType -eq "ADD_TO_GROUP")
    {
        # ADDS NEW USER

    Add-AzureADGroupMember -ObjectId $GroupId -RefObjectId $ObjectId
    }
    elseif ( $OpType -eq "DELETE_USER")
    {
		#Soft  Delete the User
		Remove-AzureADUser -ObjectId $ObjectId
		#Hard Delete the user
        Remove-AzureADMSDeletedDirectoryObject -id $ObjectId
    }
    elseif( $OpType -eq "RETURN_MEMBER_GROUPS")
    {
    #Returns groups associated with user
    $result=(Get-AzureADUser -SearchString $UserId | Get-AzureADUserMembership ).ObjectId
    return $result
    }
    elseif($OpType -eq "REMOVE_FROM_GROUP")
    {
    Remove-AzureADGroupMember -ObjectId $GroupId -MemberId $ObjectId
    }
    elseif( $OpType -eq "COUNT_USER")
    {
        $userCount = (Get-AzureADUser -All $true).Count
        return $userCount
    }
}