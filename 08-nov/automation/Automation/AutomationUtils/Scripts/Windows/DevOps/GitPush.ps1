Function gitpush() {
    $GITBIN = "##Automation--GITBIN--##"+"\git"
    $URL = "##Automation--URL--##"
    $PUSHPATH = "##Automation--PUSHPATH--##"
    $curPath = (Resolve-Path .\).Path
    cd $PUSHPATH
    & $GITBIN init
	& $GITBIN lfs track *
    & $GITBIN add *
    & $GITBIN -c user.name='automation' -c user.email='cv@automation.com' commit -m 'automation'
    & $GITBIN push -u $URL --all
    cd $curPath
}