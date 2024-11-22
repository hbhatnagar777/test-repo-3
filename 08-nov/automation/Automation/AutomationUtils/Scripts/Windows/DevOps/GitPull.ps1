Function gitpull() {
    $GITBIN = "##Automation--GITBIN--##" + "\git"
    $URL = "##Automation--URL--##"
    $PULLPATH = "##Automation--PULLPATH--##"
	$DEST = "##Automation--DEST--##"
	$BARE = "##Automation--BARE--##"
    $curPath = (Resolve-Path .\).Path
    cd $PULLPATH
    & $GITBIN clone $BARE $URL $DEST
    cd $curPath
}