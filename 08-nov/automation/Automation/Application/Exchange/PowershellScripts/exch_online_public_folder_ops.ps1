Function Main()
{

    $PWD = "##Automation--LoginPassword--##"
    $Email = "##Automation--LoginUser--##"
    $Attribute = '##Automation--Attribute--##'
    $OpType = "##Automation--OpType--##"
        # Which attribute to fetch from Exchang
    $HashAlgo = '##Automation--HashAlgo--##'
        # Hash Algo <optional> that needs to be applied
    $PublicFolderName = "##Automation--PublicFolderName--##"

    $MailEnabledStatus = "##Automation--MailEnabledStatus--##"
        # Attribute for Delete Operation

    $SecurePassword = ConvertTo-SecureString -String $PWD -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $Email, $SecurePassword

	Connect-ExchangeOnline -Credential $Credential -ShowBanner:$false

    if ($OpType -eq "GetFolderIDs")
    {

        $folder_IDs = Get-PublicFolder \ -GetChildren | Select-Object $Attribute

        if ($HashAlgo)
        {
            $hasher = [System.Security.Cryptography.HashAlgorithm]::Create($HashAlgo)

            $res = New-Object System.Collections.Generic.List[System.Object]

            For($i=0; $i -lt $folder_IDs.length; $i++){
            $hash = $hasher.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($folder_IDs[$i].$Attribute))
            $hashString = [System.BitConverter]::ToString($hash)

            $hashValue = $hashString.Replace('-','')
            $res.Add($hashValue)

            }
            return $res.ToArray()
        }
        else
        {
            return $folder_IDs
        }
    }

    elseif ( $OpType -eq "ItemCount")
    {
        $Folder_Id = Get-PublicFolder -Recurse | Select Name, EntryId | Where-Object { $_.Name -eq $PublicFolderName} | Select-Object EntryId

        $items = Get-PublicFolderItemStatistics -Identity $Folder_Id.EntryId

        return $items.count
    }

    elseif( $OpType -eq "MailEnable")
    {
        Enable-MailPublicFolder \$PublicFolderName

        $smtp_address = Get-MailPublicFolder | Where-Object {$_.Identity -eq $PublicFolderName} | Select-Object PrimarySmtpAddress

        return $smtp_address
    }

    elseif( $OpType -eq "CreatePF")
    {
        New-PublicFolder $PublicFolderName
    }

    elseif( $OpType -eq "Delete")
    {
        if($MailEnabledStatus -eq $true)
        {
            Disable-MailPublicFolder -Identity \$PublicFolderName -Confirm:$false
        }
        Remove-PublicFolder -Identity \$PublicFolderName -Confirm:$false
    }


    $ErrorActionPreference = 'Continue'
}
