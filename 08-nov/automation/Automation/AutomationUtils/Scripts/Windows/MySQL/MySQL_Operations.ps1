Function ServerStatus() {
    $BINDIR = "##Automation--BINDIR--##"
    $USERNAME = "##Automation--USERNAME--##"
    $PASSWORD = "##Automation--PASSWORD--##"
    $SOCKFILE = "##Automation--SOCKFILE--##"
	$OPERATION = "##Automation--OPERATION--##"
    cd $BINDIR
    .\mysqladmin.exe -u $USERNAME --password=$PASSWORD $OPERATION -P $SOCKFILE 2> temp
}