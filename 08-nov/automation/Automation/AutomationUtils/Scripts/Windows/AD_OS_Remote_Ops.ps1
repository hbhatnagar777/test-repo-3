######################################
# File for OS COMMANDLINE operations # 
######################################


Function Main()
{

    $PWD = "##Automation--LoginPassword--##"
    $LoginUser= "##Automation--LoginUser--##"
    $OpType = "##Automation--OpType--##"
    $servername = "##Automation--ServerName--##"
    $path =  "##Automation--Path--##"


    $PWord = ConvertTo-SecureString -String $PWD -AsPlainText -Force
    $Credential = New-Object -TypeName "System.Management.Automation.PSCredential" -ArgumentList $LoginUser, $PWord
    $Session = New-PSSession -ComputerName $servername -Credential $Credential

   Enter-PSSession $Session
    if ($OpType -eq "DELETE_DIR")
    {
        # delete directory
        rmdir $path -r
    }

    $ErrorActionPreference = 'Continue'
}