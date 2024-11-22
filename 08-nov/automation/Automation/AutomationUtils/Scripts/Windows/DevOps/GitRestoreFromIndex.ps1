Function restorefromindex {
    $GITBIN = "##Automation--GITBIN--##" + "\git"
    $SRCPATH = "##Automation--SRCPATH--##"
    $RESTOREPATH = "##Automation--RESTOREPATH--##"
    $DEST_REPO = "##Automation--DEST_REPO--##"
    $BARE = "##Automation--BARE--##"

    # Save the current path
    $curPath = (Get-Location).Path

    # Change to the restore path
    Set-Location -Path $RESTOREPATH

    # Rename the destination repository
    Move-Item -Path "$DEST_REPO" -Destination "$DEST_REPO.git" -Force

    # Clone the repository
    if ($BARE -eq '--bare') {
    	& "$GITBIN" clone --bare $SRCPATH $DEST_REPO
    } else {
    	& "$GITBIN" clone $SRCPATH $DEST_REPO
    }

    # Return to the original path
    Set-Location -Path $curPath
}

restorefromindex
