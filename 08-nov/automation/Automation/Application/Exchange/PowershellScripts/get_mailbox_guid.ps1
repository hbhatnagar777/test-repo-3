
Function Main()
{

    $Passwd = "##Automation--LoginPassword--##"
    $LoginUser= "##Automation--LoginUser--##"
    $Mailbox = "##Automation--Mailbox--##"
    $Environment = "##Automation--Environment--##"

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    $PWord = ConvertTo-SecureString -String $Passwd -AsPlainText -Force

    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord

    If ( $Environment -eq "AzureAD")
    {
        Connect-AzureAD -Credential $Credential | Out-Null

        $ObjId = Get-AzureADUser -ObjectId $Mailbox;

        $ObjectId = $ObjId.ObjectId;

        return $ObjectId
    }

    elseif ($Environment -eq "OnPrem")
    {

        $GUID = Get-ADUser -Identity $Mailbox | Select-Object ObjectGUID

        return $GUID.ObjectGUID.Guid

    }


}