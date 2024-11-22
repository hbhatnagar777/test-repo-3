GITBIN=##Automation--GITBIN--##/git

gitstatus() {
    $GITBIN version
    $GITBIN lfs version
}

gitstatus $GITBIN