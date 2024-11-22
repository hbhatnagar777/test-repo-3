GITBIN=##Automation--GITBIN--##/git
URL=##Automation--URL--##
PULLPATH=##Automation--PULLPATH--##
DEST=##Automation--DEST--##
BARE=##Automation--BARE--##

gitpull() {
    cd $PULLPATH && $GITBIN clone $BARE $URL $DEST
}

gitpull $GITBIN $URL $PULLPATH $DEST $BARE