Function gitstatus() {
    $GITBIN = "##Automation--GITBIN--##"+"\git"
    $curPath = (Resolve-Path .\).Path
    & $GITBIN version
    & $GITBIN lfs version
    cd $curPath
}