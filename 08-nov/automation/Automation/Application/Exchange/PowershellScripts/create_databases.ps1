##########################################################################################################################
#
# This powershell script is to create n a new database
# Names of  database should be given as input
# If & database already exists they will be deleted and recreated
# If mailboxes already exists within the database, first they will be removed before deleting and recreating the database
#
###########################################################################################################################

Function Main()
{

$PWD = "##Automation--LoginPassword--##"
$LoginUser= "##Automation--LoginUser--##"
$server="##Automation--ExchangeServer--##"
$name="##Automation--ExchangeDatabase--##"
$edb_folder="##Automation--DatabaseEDBFolderPath--##"
$outputfilepath="C:\test.txt"
$logfolderpath="##Automation--DatabaselogFolderPath--##"
$casserver="##Automation--ExchangeCASServer--##"

$PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force

$Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://$casserver/PowerShell/ -Authentication Kerberos -Credential $Credential

Import-PSSession $Session

$edb_filepath=$edb_folder+"\"+$name
$edb_filepath1=$edb_filepath+"."+"edb"

$ErrorActionPreference = 'SilentlyContinue'
Add-PSSnapin Microsoft.Exchange.Management.PowerShell.Admin
Add-PSSnapin Microsoft.Exchange.Management.PowerShell.E2010
$ErrorActionPreference = 'Continue'

$outputfilepath|Out-File -FilePath $outputfilepath -Encoding Ascii
$logfolderpath|out-file -filepath $outputfilepath -Append -Encoding Ascii
trap { $var = "Exception occured:";$var | out-file -filepath $outputfilepath -append -Encoding Ascii; $var=$_;$var | out-file -filepath $outputfilepath -append -Encoding Ascii;return $var }
if($name -ne "None")
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

        if ($name -eq $db)
        {
            $stri = "Found the database.. " + $db
            $stri |out-file -filepath $outputfilepath -Append -Encoding Ascii
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
                        $stri|out-file -filepath $outputfilepath -Append -Encoding Ascii
                        $op=[string](remove-mailbox -Identity $mb -Confirm:$false)
                        $op|out-file -filepath $outputfilepath -Append -Encoding Ascii
                    }
                }
                $stri = "Removing the database.. "+$db
                $stri|out-file -filepath $outputfilepath -Append -Encoding Ascii

                $op=[string](remove-mailboxdatabase -Identity $db -Confirm:$false)
                $op|out-file -filepath $outputfilepath -Append -Encoding Ascii
if (Test-Path -path $edb_folder)
{
    $stri = "Deleting existing edb folder.."+$edb_folder
    $stri|out-file -filepath $outputfilepath -Append -Encoding Ascii
    Remove-Item "$edb_folder" -recurse -force -Confirm:$false
    New-Item "$edb_folder" -type directory -force
}
if (Test-Path -path $logfolderpath)
{
    $stri = "Deleting existing log folder.."+$logfolderpath
    $stri|out-file -filepath $outputfilepath -Append -Encoding Ascii
    Remove-Item "$logfolderpath" -recurse -force -Confirm:$false
    New-Item "$logfolderpath" -type directory -force
}
$ErrorActionPreference = 'Stop'
New-MailboxDatabase -Name $name -Server $server -EdbFilePath $edb_filepath1 -LogFolderPath $logfolderpath
$temp="new-mailboxdatabase -Name '"+$name+"' -Server '"+$server+"' -EdbFilePath '"+$edb_filepath1+"' -LogFolderPath '"+$logfolderpath
$temp|out-file -filepath $outputfilepath -append -Encoding Ascii
######mount the newly created database
Start-Sleep -s 60
mount-database -Identity $name -Confirm:$False
}
else
{
$ErrorActionPreference = 'Stop'
New-MailboxDatabase -Name $name -Server $server -EdbFilePath $edb_filepath1 -LogFolderPath $logfolderpath
$temp="new-mailboxdatabase -Name '"+$name+"' -Server '"+$server+"' -EdbFilePath '"+$edb_filepath1+"' -LogFolderPath '"+$logfolderpath
$temp|out-file -filepath $outputfilepath -append -Encoding Ascii
######mount the newly created database
Start-Sleep -s 60
mount-database -Identity $name -Confirm:$False
}
}