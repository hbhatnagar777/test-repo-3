Function ServerStatus() {
    $BINDIR = "##Automation--BINDIR--##"
    $DATADIR = "##Automation--DATADIR--##"
    $curPath = (Resolve-Path .\).Path
    cd $BINDIR
    ./pg_ctl -U postgres -D $DATADIR status
    cd $curPath
}