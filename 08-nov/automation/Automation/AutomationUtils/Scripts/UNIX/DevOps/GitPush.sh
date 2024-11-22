GITBIN=##Automation--GITBIN--##/git
URL=##Automation--URL--##
PUSHPATH=##Automation--PUSHPATH--##

gitpush() {
    cd $PUSHPATH
    $GITBIN init
    $GITBIN lfs track "*"
    $GITBIN add "*"
    $GITBIN -c user.name='automation' -c user.email='cv@automation.com' commit -m 'automation'
    $GITBIN push -u $URL --all
}

gitpush $GITBIN $URL $PUSHPATH