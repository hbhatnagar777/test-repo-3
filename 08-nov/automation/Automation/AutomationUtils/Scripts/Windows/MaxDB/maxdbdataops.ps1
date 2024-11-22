param (
    [string]$DBMCLI_PATH = ##Automation--DBMCLIPATH--##,
    [string]$OPERATION = ##Automation--OPERATION--##

)
$HS = (hostname)
$env:PATH="$DBMCLI_PATH;$env:PATH"

cd $DBMCLI_PATH
    if ($OPERATION -like "sdbfill*") {
        $cmd =  $OPERATION + " " + $HS
        Invoke-Expression $cmd

    }
    else {
        Invoke-Expression $OPERATION
   }
