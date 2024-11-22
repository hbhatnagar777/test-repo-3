#!/bin/bash
#
#shell script to get metadata of the items based on given input parameters
#

DATAPATH=""
NAMELIST=no
METALIST=no
SUMLIST=no
ACLLIST=no
XATTRLIST=no
SORTED=no
ATTRNAME=cvattr
ATTRVALUE=autovalue

# HP-UX lacks this
PATH=$PATH:/usr/bin:/bin
export PATH
alias ls='ls '

#to print sample usage , no arguments
printUsage()
{
        echo "Sample usage below, -path is mandatory"
        echo "$0 -path /datapath -name yes -meta yes -sum yes -acls yes -xattr yes -sorted yes"
}

#print full paths of all the items in the given directory
#usage
#printPath /dirname
printPath()
{
	if [ "$SORTED" = "yes" ]
	then
		find "$1" 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
	else
		find "$1" 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g"
	fi
}

#print complete ls ouput of all the items in the given directory
#usage
#printMeta /dirname
#for directores timestamp is ignored
printMeta()
{
	if [ "$SORTED" = "yes" ]
	then
		find "$1" -type d -exec ls -l -d {} \; 2>/dev/null | awk '{printf $1FS$2FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
		find "$1" -type l -exec ls -l -d {} \; 2>/dev/null | awk '{printf $1FS$2FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
		find "$1" \! -type d \! -type l -exec ls -l -d {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
	else
		find "$1" -type d -exec ls -l -d {} \; 2>/dev/null | awk '{printf $1FS$2FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' | sed "s/$(echo $1 | sed 's/\//\\\//g')//g"
		find "$1" -type l -exec ls -l -d {} \; 2>/dev/null | awk '{printf $1FS$2FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
		find "$1" \! -type d \! -type l -exec ls -l -d {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g"
	fi
}

#print checksum of all the files in the given directory
#usage
#printSum /dirname
printSum()
{
	if [ "$SORTED" = "yes" ]
	then
		find "$1" \! -type d -exec cksum {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
	else
		find "$1" \! -type d -exec cksum {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g"
	fi
}

#print ACL of all the items in the given directory
#usage
#printACL /dirname
#this will retrun unsorted to preserve format
printACL()
{
	if [ `uname -s` = "Linux" ]
	then
		if [ "$SORTED" = "yes" ]
		then
			getfacl -R "$1" -p 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
		else
			getfacl -R "$1" -p 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g"
		fi
	else
		echo "**Not Impletemented**"
		exit 1
	fi
}

#print XATTR of all the items in the given directory
#usage
#printXATTR /dirname
#this will retrun unsorted to preserve format
printXATTR()
{
        if [ `uname -s` = "Linux" ]
        then
                if [ "$SORTED" = "yes" ]
                then
                	find "$1" -exec attr -g $ATTRNAME {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | sort
                else
                	find "$1" -exec attr -g $ATTRNAME {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g"
                fi
        else
                echo "**Not Impletemented**"
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
        -name)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-name\" option."
                echo
                exit 1
            fi
            NAMELIST=$1
            shift
            ;;

        -meta)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-meta\" option."
                echo
                exit 1
            fi
            METALIST=$1
            shift
            ;;

        -sum)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-sum\" option."
                echo
                exit 1
            fi
            SUMLIST=$1
            shift
            ;;

        -sorted)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-sorted\" option."
                echo
                exit 1
            fi
            SORTED=$1
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
            ACLLIST=$1
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
            XATTRLIST=$1
            shift
            ;;

        -all)
            shift
            NAMELIST=yes
            METALIST=yes
            SUMLIST=yes
            ACLLIST=yes
            XATTRLIST=yes
            ;;

        *)
            echo
            echo "*** Unknown argument \"$1\" encountered."
            echo
            exit 1
            ;;
    esac
done

[ "$NAMELIST" = "yes" ] && printPath "$DATAPATH"
[ "$METALIST" = "yes" ] && printMeta "$DATAPATH"
[ "$SUMLIST" = "yes" ] && printSum "$DATAPATH"
[ "$ACLLIST" = "yes" ] && printACL "$DATAPATH"
[ "$XATTRLIST" = "yes" ] && printXATTR "$DATAPATH"
exit 0
