#!/bin/bash
#
#shell script to modify the items based on given input parameters
#

DATAPATH=""
RENAME=no
MODIFY=no
ACLS=no
XATTR=no
ATTRNAME=cvattr
ATTRVALUE=modvalue
PERMISSIONS=no
SLINKS=no
HLINKS=no
TESTUSER=cvusr2
TESTGROUP=cvgrp2
ACLUSER=cvusr
ACLGROUP=cvusr
DEFAULTMODPERM=555

# HP-UX lacks this
PATH=$PATH:/usr/bin:/bin
export PATH
alias ls='ls '

#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below, -path is mandatory"
        echo "$0 -path /datapath -rename yes -modify yes -acls yes -xattr yes -permissions yes -slinks yes -hlinks yes"
}

#function to create user and group to set on the test data set.
makeUserAndGroup()
{
        if [ `uname -s` = "AIX" ]
        then
                `mkgroup $TESTGROUP 2>/dev/null`
                `mkgroup $ACLGROUP 2>/dev/null`
                `mkuser pgrp=$ACLGROUP $ACLUSER 2>/dev/null`
                `mkuser pgrp=$TESTGROUP $TESTUSER 2>/dev/null`
        else
                `groupadd $TESTGROUP 2>/dev/null`
                `groupadd $ACLGROUP 2>/dev/null`
                `useradd -g $ACLGROUP $ACLUSER 2>/dev/null`
                `useradd -g $TESTGROUP $TESTUSER 2>/dev/null`
        fi
}

#function to set permissions on a given path recursively
#usage
#setPermission permission /path
setPermission()
{
        if ! `chmod -R "$1" "$2"`
        then
                echo
                echo "*** Failed to set permissions $1 for $2"
                echo
                exit 1
        fi
}

#function to set user and group recursively on a given path
#usage
#setUserAndGroup user group /path
setUserAndGroup()
{
        if ! `chown -R $1:$2 "$3"`
        then
                echo
                echo "*** Failed to set permissions $1 for $2"
                echo
                exit 1
        fi
}

#function to set acls on the given path
#sets read permission for root user and root group
#usage
#setACL /path
setACL()
{
        if [ `uname -s` = "Linux" ]
        then
                if ! `setfacl -R -m user:$ACLUSER:r,group:$ACLGROUP:r "$1"`
                then
                        echo
                        echo "*** Failed to set ACLs for $1"
                        echo
                        exit 1
                fi

        else
                echo "Not implemented"
                exit 1
        fi

}

#function to rename all the files in a given path
#usage
#doRename /path
#already renamed files won't be renamed again
doRename()
{
	if ! `find "$1" \! -type d \! -name '*.cvrenamed' -exec sh -c 'file="$0"; mv "$file" "$file.cvrenamed"' {} \;`
	then
                echo
                echo "*** Failed to rename files on path $1"
                echo
                exit 1
	fi
}

#function to modify all the files in a given path by adding extra data
#usage
#doModify /path
doModify()
{
        if ! `find "$1" -type f \! -exec sh -c 'file="$0"; echo cvmodified >> "$file"' {} \;`
        then
                echo
                echo "*** Failed to modify files on path $1"
                echo
                exit 1
        fi
}

#function to modify all the files in a given path by adding acls
#usage
#doACLS /path
doACLS()
{
	setACL  "$1"
}

#function to modify all the files in a given path by adding xattr
#usage
#doXATTR /path
doXATTR()
{
        if ! `find "$1" \! -type l -exec attr -s $ATTRNAME -V $ATTRVALUE {} >/dev/null \; 2>/dev/null` 
        then
                echo
                echo "*** Failed to set xattr on items in path $1"
                echo
                exit 1
        fi
}

#function to modify all the files in a given path by changing permissions
#usage
#doPermissions /path
doPermissions()
{
	setUserAndGroup $TESTUSER $TESTGROUP "$1"
	setPermission	$DEFAULTMODPERM "$1"
}

#function to modify all the files in a given path by adding Hard links
#usage
#doHLINKS /path
doHLINKS()
{
        if ! `find "$1" -type f \! -exec sh -c 'file="$0"; ln "$file" "$file.cvhlink"' {} \;`
        then
                echo
                echo "*** Failed to create hardlinks on items in path $1"
                echo
                exit 1
        fi
}

#function to modify all the files in a given path by adding Symbolic links
#usage
#doHLINKS /path
doSLINKS()
{
        if ! `find "$1" -type f \! -exec sh -c 'file="$0"; ln -s "$file" "$file.cvslink"' {} \;`
        then
                echo
                echo "*** Failed to create symbolic links on items in path $1"
                echo
                exit 1
        fi
}

#Parse command-line arguments

if [ "$1"x = "-help"x ] || [ "$1"x = "-h"x ]
then
        printUsage
        exit 0
fi


if [ "$1"x != "-path"x ]
then
        echo
        echo "*** \"-path\" is mandatory first option."
        echo
        exit 1
fi

shift
DATAPATH=$1
shift

while [ $# -gt 0 ]
do
    case $1 in
       -rename)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-rename\" option."
                echo
                exit 1
            fi
            RENAME=$1
            shift
            ;;

       -modify)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-modify\" option."
                echo
                exit 1
            fi
            MODIFY=$1
            shift
            ;;

       -permissions)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-permissions\" option."
                echo
                exit 1
            fi
            PERMISSIONS=$1
            shift
            ;;

       -hlinks)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-hlinks\" option."
                echo
                exit 1
            fi
            HLINKS=$1
            shift
            ;;

       -slinks)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-slinks\" option."
                echo
                exit 1
            fi
            SLINKS=$1
            shift
            ;;

        -acls)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-acls\" option."
                echo
                exit 1
            fi
            ACLS=$1
            shift
            ;;

        -xattr)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-xattr\" option."
                echo
                exit 1
            fi
            XATTR=$1
            shift
            ;;

        -all)
            shift
            UNICODE=yes
            HLINKS=yes
            SLINKS=yes
            SPARSE=yes
            ACLS=yes
            XATTR=yes
            ;;
        *)
            echo
            echo "*** Unknown argument \"$1\" encountered."
            echo
            exit 1
            ;;
    esac
done

#main execution starts from here
makeUserAndGroup


[ "$RENAME" = "yes" ] && doRename "$DATAPATH"
[ "$MODIFY" = "yes" ] && doModify "$DATAPATH"
[ "$PERMISSIONS" = "yes" ] && doPermissions "$DATAPATH"
[ "$ACLS" = "yes" ] && doACLS "$DATAPATH"
[ "$XATTR" = "yes" ] && doXATTR "$DATAPATH"
[ "$HLINKS" = "yes" ] && doHLINKS "$DATAPATH"
[ "$SLINKS" = "yes" ] && doSLINKS "$DATAPATH"
exit 0
