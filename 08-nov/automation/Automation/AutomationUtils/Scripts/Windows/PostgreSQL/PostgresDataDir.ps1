Function get_datadir() {
    $BINDIR = "##Automation--BINDIR--##"
    $PASSWORD = "##Automation--PASSWORD--##"
    $PORT = "##Automation--PORT--##"
    $curPath = (Resolve-Path .\).Path
    cd $BINDIR
    $env:PGPASSWORD=$PASSWORD
    ./psql -p $PORT -U postgres -c 'show data_directory;' > automation-data-dir.txt
    Get-Content automation-data-dir.txt | select -Index 2
    cd $curPath
}


