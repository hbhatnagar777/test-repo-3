GITBIN=##Automation--GITBIN--##/git
SRCPATH=##Automation--SRCPATH--##
DEST_REPO=##Automation--DEST_REPO--##
RESTOREPATH=##Automation--RESTOREPATH--##
BARE=##Automation--BARE--##

restorefromindex() {
    cd "$RESTOREPATH" && mv "$DEST_REPO" "$DEST_REPO.git" && $GITBIN clone $BARE "$SRCPATH" "$DEST_REPO"
}

restorefromindex "$RESTOREPATH" "$DEST_REPO" "$GITBIN" "$SRCPATH"
