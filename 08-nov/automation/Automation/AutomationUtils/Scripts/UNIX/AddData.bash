#!/bin/bash
#
#shell script to automatically populate the test data
#

DATAPATH=""
DIRS=3
FILES=5
SIZEINKB=20
LEVELS=1
HLINKS=yes
SLINKS=yes
SPARSE=yes
ACLS=no
XATTR=no
UNICODE=no
DEFAULTFILEPERM=770
DEFAULTDIRPERM=775
DEFAULTSLINKPERM=777
DEFAULTHLINKPERM=766
TESTUSER=cvusr
TESTGROUP=cvgrp
ACLUSER=cvusr2
ACLGROUP=cvgrp2
HOLESIZEKB=1024
ATTRNAME=cvattr
ATTRVALUE=autovalue
CHINESE=$(printf "\346\227\251\344\270\212\345\245\275")
JAPANESE=$(printf "\343\201\212\343\201\257\343\202\210\343\201\206\343\201\224\343\201\226\343\201\204\343\201\276\343\201\231")
ARABIC=$(printf "\330\265\330\250\330\247\330\255 \330\247\331\204\330\256\331\212\330\261")
SPECIAL="name space\!@#*&^%(),"
RUSSIAN=$(printf "\320\264\320\276\320\261\321\200\320\276\320\265 \321\203\321\202\321\200\320\276")

# HP-UX lacks this
PATH=$PATH:/usr/bin:/bin
export PATH
alias ls='ls '

#to print sample usage , no arguments
printUsage()
{
	echo "Sample usage below, -path is mandatory"
	echo "$0 -path /datapath -dirs 10 -files 25 -sizeinkb 100 -levels 1 -hlinks yes -slinks yes -sparse yes -holesizeinkb 1024 -acls no -xattr no -unicode no"	
}

#function to create user and group to set on the test data set.
makeUserAndGroup()
{
	if [ `uname -s` = "AIX" ]
	then
		`mkgroup $TESTGROUP 2>/dev/null`
		`mkgroup $ACLGROUP 2>/dev/null`
		`mkuser pgrp=$TESTGROUP $TESTUSER 2>/dev/null`
		`mkuser pgrp=$ACLGROUP $ACLUSER 2>/dev/null`

	else
		`groupadd $TESTGROUP 2>/dev/null`
		`groupadd $ACLGROUP 2>/dev/null`
		`useradd -g $TESTGROUP $TESTUSER 2>/dev/null`
		`useradd -g $ACLGROUP $ACLUSER 2>/dev/null`
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

#function to set xattrs on the given path
#usage
#setXattr /path
setXattr()
{
        if [ `uname -s` = "Linux" ]
        then
                if ! `attr -s $ATTRNAME -V $ATTRVALUE "$1" > /dev/null`
                then
                        echo
                        echo "*** Failed to set xattr for $1"
                        echo
                        exit 1
                fi

        else
                echo "Not implemented"
                exit 1
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

#to create directory using mkdir -p
#usage
#makeDirectory /dirname
makeDirectory()
{
        if ! `mkdir -p "$1"`
        then
                echo
                echo "*** Failed to create $1"
                echo
                exit 1
        fi
}


#to create file with random data using dd
#usage
#makeFile /filepath
makeFile()
{
        if ! `dd if=/dev/urandom of="$1" bs=1k count=$SIZEINKB 2>/dev/null`
        then
                echo
                echo "*** Failed to create $1"
                echo
                exit 1
        fi
}

#function to create hardlink to given file
#usage
#makeHLINK /filepath /linkpath
makeHLINK()
{
        if ! `ln "$1" "$2"`
        then
                echo
                echo "*** Failed to create hardlink $2 for $1"
                echo
                exit 1
        fi

}

#function to create symbolic link to given file
#usage
#makeSLINK /filepath /linkpath
makeSLINK()
{
        if ! `ln -s "$1" "$2"`
        then
                echo
                echo "*** Failed to create symbolic link $2 for $1"
                echo
                exit 1
        fi

}

#to create sparse files
#usage
#makeSparseFile /filepath
makeSparseFile()
{
        if ! `echo "Sparse" >"$1"`
        then
                echo
                echo "*** Failed to create $1"
                echo
                exit 1
        fi
        if ! `dd if=/dev/urandom of="$1" bs=1k count=$SIZEINKB seek=$HOLESIZEKB 2>/dev/null`
        then
                echo
                echo "*** Failed to create $1"
                echo
                exit 1
        fi

}

#Create regular files on the specified input firectory
#usage 
#createRegularFiles /pathtocreate
createRegularFiles()
{
	makeDirectory "$1/regular"
	local FILEITR=1
	while [ $FILEITR -le $FILES ]
	do
		FILENAME="$1/regular/regularfile$FILEITR"
		makeFile "$FILENAME"
		((FILEITR=FILEITR+1))
	done
	setPermission $DEFAULTFILEPERM "$1/regular"
	setUserAndGroup $TESTUSER $TESTGROUP "$1/regular"
}

#Create Hardlinks on the specified input directory
#usage
#createHlinks /pathtocreate
createHlinks()
{
	makeDirectory "$1/hlinks"
	local FILEITR=1
	while [ $FILEITR -le $FILES ]
	do
		FILENAME="$1/hlinks/file$FILEITR"
		LINKNAME="$1/hlinks/hlinkfile$FILEITR"
		makeFile "$FILENAME"
		makeHLINK "$FILENAME" "$LINKNAME"
		((FILEITR=FILEITR+1))
	done
	setPermission $DEFAULTHLINKPERM "$1/hlinks"
	setUserAndGroup $TESTUSER $TESTGROUP "$1/hlinks"
}

#Create symbolic links on the specified input directory
#usage
#createSlinks /pathtocreate
createSlinks()
{
        makeDirectory "$1/slinks"
        local FILEITR=1
        while [ $FILEITR -le $FILES ]
        do
                FILENAME="$1/slinks/file$FILEITR"
                LINKNAME="$1/slinks/slinkfile$FILEITR"
                makeFile "$FILENAME"
                makeSLINK "file$FILEITR" "$LINKNAME"
                ((FILEITR=FILEITR+1))
        done
	#DC does not process this
	#setPermission $DEFAULTDIRPERM "$1/slinks"
	#setUserAndGroup $TESTUSER $TESTGROUP "$1/slinks"
}

#Create sparse files on the specified input directory
#usage
#createSparseFiles /pathtocreate
createSparseFiles()
{
        makeDirectory "$1/sparse"
        local FILEITR=1
        while [ $FILEITR -le $FILES ]
        do
                FILENAME="$1/sparse/sparsefile$FILEITR"
                makeSparseFile "$FILENAME"
                ((FILEITR=FILEITR+1))
        done
        setPermission $DEFAULTDIRPERM "$1/sparse"
        setUserAndGroup $TESTUSER $TESTGROUP "$1/sparse"
}

#Create files with ACLS seton the specified input directory
#usage
#createACLFiles /pathtocreate
createACLFiles()
{
        makeDirectory "$1/acls"
        local FILEITR=1
        while [ $FILEITR -le $FILES ]
        do
                FILENAME="$1/acls/aclfile$FILEITR"
                makeFile "$FILENAME"
                ((FILEITR=FILEITR+1))
        done
        setPermission $DEFAULTDIRPERM "$1/acls"
        setUserAndGroup $TESTUSER $TESTGROUP "$1/acls"
        setACL  "$1/acls"
}

#Create files with ACLS seton the specified input directory
#usage
#createACLFiles /pathtocreate
createXattrFiles()
{
        makeDirectory "$1/xattr"
        setXattr "$1/xattr"
        local FILEITR=1
        while [ $FILEITR -le $FILES ]
        do
                FILENAME="$1/xattr/xattrfile$FILEITR"
                makeFile "$FILENAME"
                setXattr  "$FILENAME"
                ((FILEITR=FILEITR+1))
        done
        setPermission $DEFAULTDIRPERM "$1/xattr"
        setUserAndGroup $TESTUSER $TESTGROUP "$1/xattr"
}

#Function to create files with unicode names.
#usage
#createUnicodeFiles /pathtocreate
createUnicodeFiles()
{
        makeDirectory "$1/unicode"
        local FILEITR=1
        while [ $FILEITR -le $FILES ]
        do
                FILENAME="$1/unicode/$CHINESE$FILEITR"
                makeFile "$FILENAME"
                FILENAME="$1/unicode/$JAPANESE$FILEITR"
                makeFile "$FILENAME"
                FILENAME="$1/unicode/$ARABIC$FILEITR"
                makeFile "$FILENAME"
                FILENAME="$1/unicode/$RUSSIAN$FILEITR"
                makeFile "$FILENAME"
                FILENAME="$1/unicode/$SPECIAL$FILEITR"
                makeFile "$FILENAME"
                ((FILEITR=FILEITR+1))
        done
        setPermission $DEFAULTDIRPERM "$1/unicode"
        setUserAndGroup $TESTUSER $TESTGROUP "$1/unicode"
}

#Create dataset on the specified input firectory
#usage
#createDataset /pathtocreate levels
createDataset()
{
        local DIRITR=1
        local REMAININGLEVEL=$2
        ((REMAININGLEVEL=REMAININGLEVEL-1))
        while [ $DIRITR -le $DIRS ]
        do
                DIRNAME="$1/dir$DIRITR"
                makeDirectory "$DIRNAME"
                setPermission $DEFAULTDIRPERM "$DIRNAME"
                setUserAndGroup $TESTUSER $TESTGROUP "$DIRNAME"
                createRegularFiles "$DIRNAME"
                [ "$HLINKS" = "yes" ] && createHlinks "$DIRNAME"
                [ "$SLINKS" = "yes" ] && createSlinks "$DIRNAME"
                [ "$SPARSE" = "yes" ] && createSparseFiles "$DIRNAME"
                [ "$ACLS" = "yes" ] && createACLFiles "$DIRNAME"
                [ "$XATTR" = "yes" ] && createXattrFiles "$DIRNAME"
                [ "$UNICODE" = "yes" ] && createUnicodeFiles "$DIRNAME"
                if [ $REMAININGLEVEL -gt 0 ]
                then
                        createDataset "$DIRNAME" $REMAININGLEVEL
                fi
                ((DIRITR=DIRITR+1))
        done

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

#Create the path if it does not exist and set permissions.
makeDirectory "$DATAPATH"
makeUserAndGroup
setPermission $DEFAULTDIRPERM "$DATAPATH"
setUserAndGroup $TESTUSER $TESTGROUP "$DATAPATH"

while [ $# -gt 0 ]
do
    case $1 in
        -dirs)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of dirs expected after \"-dirs\" option."
                echo
                exit 1
            fi
            DIRS=$1
            shift
            ;;
	
	-files)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of files expected after \"-files\" option."
                echo
                exit 1
            fi
            FILES=$1
            shift
            ;;
	
	-sizeinkb)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Size in KB expected after \"-sizeinkb\" option."
                echo
                exit 1
            fi
            SIZEINKB=$1
            shift
            ;;

	-levels)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of levels expected after \"-levels\" option."
                echo
                exit 1
            fi
            LEVELS=$1
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

	-sparse)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-sparse\" option."
                echo
                exit 1
            fi
            SPARSE=$1
            shift
            ;;

        -holesizeinkb)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Size of hole in KB expected after \"-holesizeinkb\" option."
                echo
                exit 1
            fi
            HOLESIZEKB=$1
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

	
	-unicode)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-unicode\" option."
                echo
                exit 1
            fi
            UNICODE=$1
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


#echo $DATAPATH $DIRS $FILES $SIZEINKB $LEVELS $HLINKS $SLINKS $SPARSE $HOLESIZEKB $ACLS $UNICODE
#main execution starts from here
createDataset "$DATAPATH" $LEVELS
exit 0
