Function Main()
{

	$PWD = "##Automation--LoginPassword--##"
	$LoginUser= "##Automation--LoginUser--##"
    $OpType = "##Automation--OpType--##"
    $GroupName = "##Automation--GroupName--##"
    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
	Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false

    if ($OpType -eq "CREATE")
    {

        try {
            $ErrorActionPreference = 'SilentlyContinue'
            Get-UnifiedGroup | Where-Object{ $_.DisplayName -eq $GroupName} | Remove-UnifiedGroup -Confirm:$false
        }
        catch{
            $ErrorActionPreference = 'Continue'
        }
        finally {
            New-UnifiedGroup -DisplayName $GroupName
        }
    }

    elseif ($OpType -eq "MemberCount") {
        $GroupType = Get-Group -Identity $GroupName | Select-Object RecipientTypeDetails 3>$null -WarningAction: SilentlyContinue

        if($GroupType.RecipientTypeDetails -eq "MailUniversalDistributionGroup")
        {
            $member = Get-DistributionGroupMember -Identity $GroupName |  Where-Object { $_.Name -NotLike "CVEXBackupAccount*" -And $_.Name -NotLike "CommvaultAutoGenerated*"}

            $count = $member.count
            return $count
        }

        elseif($GroupType.RecipientTypeDetails -eq "GroupMailbox") {

            $users = Get-UnifiedGroup -Identity $GroupName | Get-UnifiedGroupLinks -LinkType Member | Where-Object {$_.RecipientType -eq "UserMailbox"} | Select-Object Name |  Where-Object { $_.Name -NotLike "CVEXBackupAccount*" -And $_.Name -NotLike "CommvaultAutoGenerated*"}

            $User_Count = $users.count

            return $User_Count

        }

    }

    elseif ( $OpType -eq "AddGroupMembers")
    {
        $GroupMembers = "##Automation--GroupMembers--##"

        $Members = $GroupMembers

        Add-UnifiedGroupLinks -Identity $GroupName -LinkType Members -Links $Members -Confirm:$false
    }

    $ErrorActionPreference = 'Continue'
}
