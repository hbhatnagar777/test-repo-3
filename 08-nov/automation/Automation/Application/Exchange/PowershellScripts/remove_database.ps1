Function Main()
{
Set-ExecutionPolicy -ExecutionPolicy remotesigned -Force
$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$server="##Automation--ExchangeServerName--##"
$databasename="##Automation--ExchangeDatabase--##"
$casserver='##Automation--ExchangeCASServer--##'
$edbfolder='##Automation--DatabaseEDBFolderPath--##'
$logfolder='##Automation--DatabaselogFolderPath--##'

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session
if($databasename -ne "None")
{
	##DB is present,delete all the mailboxes and delete the db
	#$DBname = $server+"\"+$name
    	
	$databases=Get-MailboxDatabase -Server $server
	$len=$databases.Length
	$loop=0
	$found=0
	while($loop -lt $len)
    {
        $db = [string]($databases[$loop])
        $loop = $loop + 1
        
        if ($databasename -eq $db)
        {
            $stri = "Found the database.. " + $db
            $found = $found + 1
            $loop = $len
        } 
    }
}
if($found -eq 1)
{
		$mailboxes = get-mailbox -database $db
                $len = $mailboxes.Length
                $flag2 = 1
                if ($mailboxes.Length)
                {
                    $flag2 = 0
                }
                if ($flag2 -eq 1)
                {
                    $len = 1
                }
                for ($m=0;$m -lt $len;$m++)
                {
                    if ($len -eq 1)
                    {
                        $mb = [string]($mailboxes)
                    }
                    else
                    {
                        $mb = [string]($mailboxes[$m])
                    }
                    if ($mb)
                    {
                        $stri = "Removing the mailbox.. "+$mb
                        $op=[string](remove-mailbox -Identity $mb -Confirm:$false)
                    }
                }               
                $stri = "Removing the database.. "+$db
                $op=[string](remove-mailboxdatabase -Identity $db -Confirm:$false)
                Remove-item -Force -Recurse -Path $edbfolder
                Remove-item -Force -Recurse -Path $logfolder
}
}
           