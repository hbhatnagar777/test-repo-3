Function ServerStatus() {
    $BINDIR = "##Automation--BINDIR--##"
    $DATADIR = "##Automation--DATADIR--##"
    $OPERATION = "##Automation--OPERATION--##"
    $curPath = (Resolve-Path .\).Path
    cd $BINDIR
    ./pg_ctl -U postgres -D $DATADIR $OPERATION
}