#!/bin/bash
#
#shell script to manage the Unix automation test data for small datasets
#Refee printUsage function for the complete usage details.
#vim: set tabstop=4 expandtab shiftwidth=4 softtabstop=4
#

OPTYPE=""
DATAPATH=""
REGULAR="yes"
DIRS=3
FILES=5
SIZEINKB=20
LEVELS=1
HLINKS="no"
SLINKS="no"
HSLINKS="no"
SPARSE="no"
ACLS="no"
XATTR="no"
UNICODE="no"
LONG="no"
LONGLEVEL=1200
CUSTOMTAR=""
NONROOT="no"

RENAME="no"
MODIFY="no"
PERMISSIONS="no"

NAMELIST="no"
METALIST="no"
SUMLIST="no"
ACLLIST="no"
XATTRLIST="no"
SORTED="no"
DIRTIME="no"
SKIPLINK="no"
ISOPENVMS="no"
CUSTOMMETALIST="no"

CALLFUNCTION=""
DEFAULTFILEPERM=770
DEFAULTDIRPERM=775
DEFAULTSLINKPERM=777
DEFAULTHLINKPERM=766
DEFAULTMODPERM=555
TESTUSER="cvusr"
TESTGROUP="cvgrp"
ACLUSER="cvusr2"
ACLGROUP="cvgrp2"
HOLESIZEKB=1024
ATTRNAME="cvattr"
ATTRVALUE="autovalue"
MODATTRVALUE="modvalue"
CHINESE=$(printf "\346\227\251\344\270\212\345\245\275")
JAPANESE=$(printf "\343\201\212\343\201\257\343\202\210\343\201\206\343\201\224\343\201\226\343\201\204\343\201\276\343\201\231")
ARABIC=$(printf "\330\265\330\250\330\247\330\255 \330\247\331\204\330\256\331\212\330\261")
SPECIAL="lower UPPER\!@#*&^%(),"
SPECIAL2=$(printf "special2\tt\042\044\047\052\053\055\056")
SPECIAL3=$(printf "special3\072\073\074\075\076\077")
RUSSIAN=$(printf "\320\264\320\276\320\261\321\200\320\276\320\265 \321\203\321\202\321\200\320\276")

#find command output not processing few characters correctly on MAC terminal even if locale is set correctly
#disabling them
[ `uname -s` = "Darwin" ] && JAPANESE=$(printf "\343\201\212\343\201\257\343\202\210")

# HP-UX lacks this
PATH=$PATH:/usr/bin:/bin
export PATH
alias ls='ls '

#to print sample usage , no arguments
printUsage()
{
    cat <<EOF
Usage of script:

bash $0 -option1 value1 -option2 value2 ...

Below are the supported options
-help
    To display this help content.
-optype
    To specify one of the below operation types.
    add     - To add data
    change  - To perform different modifications on the data.
    get     - To get details about the data. 
-path
    Data path where the operation will be executed.
-regular
    To indicate whether regular files should be added. 
    Value can be yes or no and the default is yes.
-dirs
    Number of directories to be created for each level.
-files
    Number of files to be created under each directories for all types of data.
-sizeinkb
    Size of the files to be created in KB.
-levels
    Number of levels to be created in the data tree.
-hlinks
    To indicate whether hardlink files should be added. 
    Value can be yes or no and the default is no.
-slinks
    To indicate whether symbolic link files should be added. 
    Value can be yes or no and the default is no.
-hslinks
    To indicate whether hard links to symbolic link files should be added.
    Value can be yes or no and the default is no.
-sparse
    To indicate whether sparse files should be added. 
    Value can be yes or no and the default is no.
-holesizeinkb
    To specify the hole size of the sparse files in KB
-unicode
    To indicate whether Unicode files should be added. 
    Value can be yes or no and the default is no.
-long
    To indicate whether longpath files should be added. 
    Value can be yes or no and the default is no.
-longlevel
    To specify the length of longpath data.
-acls
    To specify if acls should be created/changed/listed depending on optype
    Value can be yes or no and the default is no.
-acluser
    To specify the username to be created and used for setting acls
-aclgroup
    To specify the groupname to be created and used for setting acls
-testuser
    To specify the username to be created and used for setting permissions.
-testgroup
    To specify the groupname to be created and used for setting permissions.
-xattr
    To specify if acls should be created/changed/listed depending on optype
    Value can be yes or no and the default is no.
-attrname
    To specify the attribute name to set in xattr
-attrvalue
    To specify the vallue of the attribute to set in xattr
-customtar
    To create dataset by extracting the tar file.
    Value is the path of the tar or tar.gz file.
-rename
    To perform rename operations on all files  during change optype.
    Value can be yes or no and the default is no.
-modify
    To perform modify operations on all files  during change optype.
    Value can be yes or no and the default is no.
-permissions
    To perform permissions change on all files during change optype.
    Value can be yes or no and the default is no.
-name
    To print the name of all the files during get optype.
    Value can be yes or no and the default is no.
-meta
    To print the meta data of all the files during get optype.
    Value can be yes or no and the default is no.
-dirtime
    To specify if folder timestamps should be printed while printing meta data.
    Value can be yes or no and the default is no.
-skiplink
    To specify if link count should be skipped while printing meta data.
    Value can be yes or no and the default is no.
-sum
    To print the checksum of all the files during get optype.
    Value can be yes or no and the default is no.
-execfunc
    To execute a function within this bash script. 
    Value will be funtion name and arguments for the function.
-isopenvms
    To specify if the unix flavor is OpenVMS.
    Value can be yes or no and the default is no.
-nonroot
    To specify if root operations should not be performed
    Value can be yes or no and the default is no.

Examples:

1, To add data with various parameters.
$0 -optype add -path /datapath -dirs 10 -files 25 -sizeinkb 100 -levels 1 -hlinks yes -slinks yes -sparse yes -holesizeinkb 1024 -acls no -xattr no -unicode no

2, To change data with various parameters.
$0 -optype change -path /datapath -modify yes -xattr yes -rename yes

3, To get information about data with various parameters
$0 -optype get -path /datapath -meta yes -dirtime yes -acls yes -xattr yes

4, To execute a function within this bash script.
$0 -execfunc makeHLINK /filepath /linkpath
$0 -execfunc makeFile /datapath/file
EOF
}

#function to create group on Darwin
#usage
#makeGroupDarwin cvgrp
makeGroupDarwin()
{
    if [ `dscl . -list /Groups | grep "\<$1\>"`"x" = "x" ]
    then
        `printf 'n\n' | dseditgroup -o create $1 >/dev/null 2>/dev/null`
    fi
}

#function to create user on Darwin and assign it to the specified group
#usage
#makeGroupDarwin cvusr cvgrp
makeUserDarwin()
{
    if [ `dscl . -list /Users | grep "\<$1\>"`"x" = "x" ]
    then
        GID=`dscl . -read /Groups/$2 | awk '($1 == "PrimaryGroupID:") { print $2 }'`
        MAXID=$(dscl . -list /Users UniqueID | awk '{print $2}' | sort -ug | tail -1)
        NEWID=$((MAXID+1))
        `dscl . -create /Users/$1`
        `dscl . -create /Users/$1 UniqueID $NEWID`
        `dscl . -create /Users/$1 PrimaryGroupID $GID`
    fi
}

#function to create user and group to set on the test data set.
makeUserAndGroup()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    if [ "$NONROOT" = "yes" ]
    then
        return 0
    fi

    if [ `uname -s` = "AIX" ]
    then
        `mkgroup $TESTGROUP 2>/dev/null`
        `mkgroup $ACLGROUP 2>/dev/null`
        `mkuser pgrp=$TESTGROUP $TESTUSER 2>/dev/null`
        `mkuser pgrp=$ACLGROUP $ACLUSER 2>/dev/null`

    elif [ `uname -s` = "Darwin" ]
    then
        makeGroupDarwin $TESTGROUP
        makeGroupDarwin $ACLGROUP
        makeUserDarwin	$TESTUSER $TESTGROUP
        makeUserDarwin	$ACLUSER $ACLGROUP

    elif [ `uname -s` = "Linux" -o `uname -s` = "HP-UX" -o `uname -s` = "SunOS" ]
    then
        `groupadd $TESTGROUP 2>/dev/null`
        `groupadd $ACLGROUP 2>/dev/null`
        `useradd -g $TESTGROUP $TESTUSER 2>/dev/null`
        `useradd -g $ACLGROUP $ACLUSER 2>/dev/null`

    else
        return 0
    fi
}


#function to set acls on the given path
#sets read permission for give user and given group
#usage
#setACL /path user group
setACL()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi
    
    if [ "$NONROOT" = "yes" ]
    then
        return 0
    fi

    if [ `uname -s` = "Linux" ]
    then
        if ! `setfacl -R -m user:$2:r,group:$3:r "$1"`
        then
            echo
            echo "*** Failed to set ACLs for $1"
            echo
            exit 1
        fi
    elif [ `uname -s` = "Darwin" ]
    then
        if ! `chmod -R +a "group:$3 allow read" "$1"`
        then
            echo
            echo "*** Failed to set ACLs for $1"
            echo
            exit 1
        fi
        if ! `chmod -R +a "user:$2 allow read" "$1"`
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
#setXattr /path attrname attrvalue
setXattr()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    if [ `uname -s` = "Linux" ]
    then
        if ! `attr -s $2 -V $3 "$1" > /dev/null`
        then
            echo
            echo "*** Failed to set xattr for $1"
            echo
            exit 1
        fi
    elif [ `uname -s` = "Darwin" ]
    then
        if ! `xattr -wr $2 $3 "$1" > /dev/null`
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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    if [ "$NONROOT" = "yes" ]
    then
        return 0
    fi

    if [ `uname -s` = "OS400" ]
    then
	return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    if [ "$NONROOT" = "yes" ]
    then
        return 0
    fi

    if [ `uname -s` = "OS400" ]
    then
	return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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

#Create symbolic links with hard links on the specified input directory
#usage
#createHSlinks /pathtocreate
createHSlinks()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    makeDirectory "$1/hslinks"
    local FILEITR=1
    while [ $FILEITR -le $FILES ]
    do
        FILENAME="$1/hslinks/file$FILEITR"
        SLINKNAME="$1/hslinks/slinkfile$FILEITR"
        HLINKNAME="$1/hslinks/hlinkfile$FILEITR"
        makeFile "$FILENAME"
        makeSLINK "file$FILEITR" "$SLINKNAME"
        makeHLINK "$SLINKNAME" "$HLINKNAME"
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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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

#Create files with ACLS set on the specified input directory
#usage
#createACLFiles /pathtocreate
createACLFiles()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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
    setACL  "$1/acls" $ACLUSER $ACLGROUP
}

#Create files with ACLS seton the specified input directory
#usage
#createXattrFiles /pathtocreate
createXattrFiles()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    makeDirectory "$1/xattr"
    setXattr "$1/xattr" $ATTRNAME $ATTRVALUE
    local FILEITR=1
    while [ $FILEITR -le $FILES ]
    do
        FILENAME="$1/xattr/xattrfile$FILEITR"
        makeFile "$FILENAME"
        setXattr  "$FILENAME" $ATTRNAME $ATTRVALUE
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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    makeDirectory "$1/unicode/$CHINESE"
    makeDirectory "$1/unicode/$JAPANESE"
    makeDirectory "$1/unicode/$ARABIC"
    makeDirectory "$1/unicode/$RUSSIAN"
    makeDirectory "$1/unicode/$SPECIAL"
    makeDirectory "$1/unicode/$SPECIAL2"
    makeDirectory "$1/unicode/$SPECIAL3"
    local FILEITR=1
    while [ $FILEITR -le $FILES ]
    do
        FILENAME="$1/unicode/$CHINESE/$CHINESE$FILEITR"
        makeFile "$FILENAME"
        FILENAME="$1/unicode/$JAPANESE/$JAPANESE$FILEITR"
        makeFile "$FILENAME"
        FILENAME="$1/unicode/$ARABIC/$ARABIC$FILEITR"
        makeFile "$FILENAME"
        FILENAME="$1/unicode/$RUSSIAN/$RUSSIAN$FILEITR"
        makeFile "$FILENAME"
        FILENAME="$1/unicode/$SPECIAL/$SPECIAL$FILEITR"
        makeFile "$FILENAME"
        FILENAME="$1/unicode/$SPECIAL2/$SPECIAL2$FILEITR"
        makeFile "$FILENAME"
        FILENAME="$1/unicode/$SPECIAL3/$SPECIAL3$FILEITR"
        makeFile "$FILENAME"
        ((FILEITR=FILEITR+1))
    done
    setPermission $DEFAULTDIRPERM "$1/unicode"
    setUserAndGroup $TESTUSER $TESTGROUP "$1/unicode"
}

#usage
#createLongFiles /pathtocreate pathlength
createLongFiles()
{
    LONGDIR="$1/longpath"
    ((LONGLEVELITR=LONGLEVEL/10+1))
    while [ $LONGLEVELITR -gt 0 ]
    do
        LONGDIR="$LONGDIR""/abcde67890"
        ((LONGLEVELITR=LONGLEVELITR-1))
    done
    makeDirectory "$LONGDIR"
    createRegularFiles "$LONGDIR"
}

#Usage
#extractTar /pathtoextract /file.tar.gz
#only tar and tar.gz are supported
extractTar()
{
    TARDIR="$1/tardata"
    TARFILE="$2"
    PRESENTDIR=`pwd`
    makeDirectory "$TARDIR"
    if `gunzip -t "$TARFILE" >/dev/null 2>/dev/null`
    then
        if ! `gunzip -c "$TARFILE" > "$TARDIR/custom.tar"`
        then
            echo
            echo "*** Failed to extract archivefile $2 to directory $1"
            echo
            exit 1
        fi
        TARFILE="$TARDIR/custom.tar"
    fi
    cd "$TARDIR"
    if ! `tar -xf "$TARFILE"`
    then
        echo
        echo "*** Failed to extract archivefile $2 to directory $1"
        echo
        cd "$PRESENTDIR"
        exit 1
    fi
    cd "$PRESENTDIR"
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
        [ "$REGULAR" = "yes" ] && createRegularFiles "$DIRNAME"
        [ "$HLINKS" = "yes" ] && createHlinks "$DIRNAME"
        [ "$SLINKS" = "yes" ] && createSlinks "$DIRNAME"
        [ "$HSLINKS" = "yes" ] && createHSlinks "$DIRNAME"
        [ "$SPARSE" = "yes" ] && createSparseFiles "$DIRNAME"
        [ "$ACLS" = "yes" ] && createACLFiles "$DIRNAME"
        [ "$XATTR" = "yes" ] && createXattrFiles "$DIRNAME"
        [ "$UNICODE" = "yes" ] && createUnicodeFiles "$DIRNAME"
        [ "$LONG" = "yes" ] && createLongFiles "$DIRNAME" 
        if [ $REMAININGLEVEL -gt 0 ]
        then
            createDataset "$DIRNAME" $REMAININGLEVEL
        fi
        ((DIRITR=DIRITR+1))
    done
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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    setACL  "$1" $TESTUSER $TESTGROUP
}

#function to modify all the files in a given path by adding xattr
#usage
#doXATTR /path
doXATTR()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    if [ `uname -s` = "Linux" ]
    then
        if ! `find "$1" \! -type l -exec attr -s $ATTRNAME -V $MODATTRVALUE {} >/dev/null \; 2>/dev/null`
        then
        echo
            echo "*** Failed to set xattr on items in path $1"
            echo
            exit 1
        fi
    else
        setXattr "$1" $ATTRNAME $MODATTRVALUE
    fi        
}

#function to modify all the files in a given path by changing permissions
#usage
#doPermissions /path
doPermissions()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    setUserAndGroup $TESTUSER $TESTGROUP "$1"
    setPermission   $DEFAULTMODPERM "$1"
}

#function to modify all the files in a given path by adding Hard links
#usage
#doHLINKS /path
doHLINKS()
{
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

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
    if [ "$ISOPENVMS" = "yes" ]
    then
        return 0
    fi

    if ! `find "$1" -type f \! -exec sh -c 'file="$0"; ln -s "$file" "$file.cvslink"' {} \;`
    then
        echo
        echo "*** Failed to create symbolic links on items in path $1"
        echo
        exit 1
    fi
}

#print full paths of all the items in the given directory
#usage
#printPath /dirname
printPath()
{
    find "$1" 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
}

#print complete ls ouput of all the items in the given directory
#usage
#printMeta /dirname
printMeta()
{
    #For symbolic links don't print time stamps as they are not preseved during restores.
    #if skiplink is yes don't print link information
    find "$1" -type l -exec ls -l -d {} \; 2>/dev/null \
    | sed 's/%/%%/g' \
    | if [ "$SKIPLINK" != "yes" ]; then awk '{printf $1FS$2FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' 2>/dev/null;
      else awk '{printf $1FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' 2>/dev/null; fi \
    | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" \
    | if [ "$SORTED" = "yes" ]; then sort; else cat; fi

    #For directories print time stamps if fodler time stamps are enabled.
    find "$1" -type d -exec ls -l -d {} \; 2>/dev/null \
    | sed 's/%/%%/g' \
    | if [ "$DIRTIME" != "yes" ]; then awk '{printf $1FS$2FS$3FS$4; for (i=9; i <= NF; i++) printf FS$i; print NL }' 2>/dev/null; 
      else awk '{printf $1FS$2FS$3FS$4; for (i=6; i <= NF; i++) printf FS$i; print NL }' 2>/dev/null; fi \
    | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" \
    | if [ "$SORTED" = "yes" ]; then sort; else cat; fi

    #For regular files and hard links always print time stamps.
    #if skiplink is yes don't print link information
    find "$1" \! -type d \! -type l -exec ls -l -d {} \; 2>/dev/null \
    | if [ "$SKIPLINK" = "yes" ]; then sed 's/%/%%/g' ; else cat; fi \
    | if [ "$SKIPLINK" = "yes" ]; then awk '{printf $1FS$3FS$4; for (i=5; i <= NF; i++) printf FS$i; print NL }' 2>/dev/null; else cat; fi \
    | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" \
    | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
}

#print checksum of all the files in the given directory
#usage
#printSum /dirname
printSum()
{
    find "$1" \! -type d -exec cksum {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
}

#print ACL of all the items in the given directory
#usage
#printACL /dirname
printACL()
{
    if [ `uname -s` = "Linux" ]
    then
        getfacl -R "$1" -p 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
    elif [ `uname -s` = "Darwin" ]
    then
        find "$1" -exec ls -aled {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi 
    else
        echo "**Not Impletemented**"
        exit 1
    fi
}

#print XATTR of all the items in the given directory
#usage
#printXATTR /dirname
printXATTR()
{
    if [ `uname -s` = "Linux" ]
    then
        find "$1" -exec attr -g $ATTRNAME {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
    elif [ `uname -s` = "Darwin" ]
    then
        xattr -lr "$1" 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
    else
        echo "**Not Impletemented**"
        exit 1
    fi
}

printCustomMetaList()
{
        if [ `uname -s` = "Linux" ]
        then
            if [[ "$CUSTOMMETALIST" == *"LastWriteTime"* ]]
            then
              find "$1" -exec stat -c %y {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
            fi
            if [[ "$CUSTOMMETALIST" == *"LastAccessTime"* ]]
            then
              find "$1" -exec stat -c %x {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
            fi
            if [[ "$CUSTOMMETALIST" == *"CreationTime"* ]]
            then
              find "$1" -exec stat -c %w {} \; 2>/dev/null | sed "s/$(echo $1 | sed 's/\//\\\//g')//g" | if [ "$SORTED" = "yes" ]; then sort; else cat; fi
            fi

        else
                echo "**Not Impletemented**"
                exit 1
        fi
}

#Check if running as non root user
[ `id | sed "s/[^=]*=\([^)]*\)(.*/\1/"` != "0" ] && NONROOT="yes"

#Parse command-line arguments
while [ $# -gt 0 ]
do
    case $1 in
        -help)
            printUsage
            exit 0
            ;;
        -optype)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Valid operation type expected after \"-optype\" option."
                echo
                printUsage
                exit 1
            fi
            if [ $1"x" = "addx" ]
            then
                OPTYPE="add"
            elif [ $1"x" = "changex" ]
            then
                OPTYPE="change"
            elif [ $1"x" = "getx" ]
            then
                OPTYPE="get"
            else
                echo
                echo "*** Valid operation type expected after \"-optype\" option."
                echo
                printUsage
                exit 1
            fi
            shift
            ;;
        -path)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Valid path expected after \"-path\" option."
                echo
                printUsage
                exit 1
            fi
            DATAPATH=$1
            shift
            ;;
        -regular)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-regular\" option."
                echo
                printUsage
                exit 1
            fi
            REGULAR=$1
            shift
            ;;
        -dirs)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of dirs expected after \"-dirs\" option."
                echo
                printUsage
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
                printUsage
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
                printUsage
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
                printUsage
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
                printUsage
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
                printUsage
                exit 1
            fi
            SLINKS=$1
            shift
            ;;
        -hslinks)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-hslinks\" option."
                echo
                printUsage
                exit 1
            fi
            HSLINKS=$1
            shift
            ;;
        -sparse)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-sparse\" option."
                echo
                printUsage
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
                printUsage
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
                printUsage
                exit 1
            fi
            ACLS=$1
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
                printUsage
                exit 1
            fi
            XATTR=$1
            XATTRLIST=$1
            shift
            ;;
        -unicode)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-unicode\" option."
                echo
                printUsage
                exit 1
            fi
            UNICODE=$1
            shift
            ;;
        -long)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-long\" option."
                printUsage
                exit 1
            fi
            LONG=$1
            shift
            ;;
        -longlevel)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** valid input expected after \"-longlevel\" option."
                printUsage
                exit 1
            fi
            LONGLEVEL=$1
            shift
            ;;
        -customtar)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** valid tar file path expected after \"-customtar\" option."
                printUsage
                exit 1
            fi
            CUSTOMTAR=$1
            shift
            ;;
        -acluser)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** User name expected after \"-acluser\" option."
                echo
                printUsage
                exit 1
            fi
            ACLUSER=$1
            shift
            ;;
        -aclgroup)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Group name expected after \"-aclgroup\" option."
                echo
                printUsage
                exit 1
            fi
            ACLGROUP=$1
            shift
            ;;
        -testuser)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** User name expected after \"-testuser\" option."
                echo
                printUsage
                exit 1
            fi
            TESTUSER=$1
            shift
            ;;
        -testgroup)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Group name expected after \"-testgroup\" option."
                echo
                printUsage
                exit 1
            fi
            TESTGROUP=$1
            shift
            ;;
        -attrname)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Attribute name expected after \"-attrname\" option."
                echo
                printUsage
                exit 1
            fi
            ATTRNAME=$1
            shift
            ;;
        -attrvalue)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Attribute value expected after \"-attrvalue\" option."
                echo
                printUsage
                exit 1
            fi
            ATTRVALUE=$1
            shift
            ;;
        -rename)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no expected after \"-rename\" option."
                echo
                printUsage
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
                printUsage
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
                printUsage
                exit 1
            fi
            PERMISSIONS=$1
            shift
            ;;
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
        -dirtime)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-dirtime\" option."
                echo
                exit 1
            fi
            DIRTIME=$1
            shift
            ;;
        -skiplink)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-skiplink\" option."
                echo
                exit 1
            fi
            SKIPLINK=$1
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
        -isopenvms)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-isopenvms\" option."
                echo
                exit 1
            fi
            ISOPENVMS=$1
            shift
            ;;
        -nonroot)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** yes or no  expected after \"-nonroot\" option."
                echo
                exit 1
            fi
            NONROOT=$1
            shift
            ;;
        -custom_meta_list)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** csv string expected after \"-custom_meta_list\" option."
                echo
                exit 1
            fi
            CUSTOMMETALIST=$1
            shift
            ;;
        -all)
            shift
            UNICODE="yes"
            HLINKS="yes"
            SLINKS="yes"
            SPARSE="yes"
            ACLS="yes"
            XATTR="yes"
            RENAME="yes"
            MODIFY="yes"
            PERMISSIONS="yes"
            NAMELIST="yes"
            METALIST="yes"
            SUMLIST="yes"
            ACLLIST="yes"
            XATTRLIST="yes"
            CUSTOMMETALIST="LastWriteTime,LastAccessTime"
            ;;
        -execfunc)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Function name and arguments expected after \"-execfunc\" option."
                echo
                printUsage
                exit 1
            fi
            CALLFUNCTION=$@
            break
            ;;
        *)
            echo
            echo "*** Unknown argument \"$1\" encountered."
            echo
            printUsage
            exit 1
            ;;
    esac
done

if [ "$CALLFUNCTION"x != ""x ]
then
    eval $CALLFUNCTION
    exit 0
fi

if [ "$DATAPATH"x = ""x ]
then
    echo
    echo "*** \"-path\" argument is not provided."
    printUsage
    echo
    exit 1
fi

if [ $OPTYPE"x" = "addx" ]
then
    makeDirectory "$DATAPATH"
    makeUserAndGroup
    setPermission $DEFAULTDIRPERM "$DATAPATH"
    setUserAndGroup $TESTUSER $TESTGROUP "$DATAPATH"
    createDataset "$DATAPATH" $LEVELS
    [ "$CUSTOMTAR" != "" ] && extractTar "$DATAPATH" "$CUSTOMTAR"
elif [ $OPTYPE"x" = "changex" ]
then
    makeUserAndGroup
    [ "$RENAME" = "yes" ] && doRename "$DATAPATH"
    [ "$MODIFY" = "yes" ] && doModify "$DATAPATH"
    [ "$PERMISSIONS" = "yes" ] && doPermissions "$DATAPATH"
    [ "$ACLS" = "yes" ] && doACLS "$DATAPATH"
    [ "$XATTR" = "yes" ] && doXATTR "$DATAPATH"
    [ "$HLINKS" = "yes" ] && doHLINKS "$DATAPATH"
    [ "$SLINKS" = "yes" ] && doSLINKS "$DATAPATH"
elif [ $OPTYPE"x" = "getx" ]
then
    [ "$NAMELIST" = "yes" ] && printPath "$DATAPATH"
    [ "$METALIST" = "yes" ] && printMeta "$DATAPATH"
    [ "$SUMLIST" = "yes" ] && printSum "$DATAPATH"
    [ "$ACLLIST" = "yes" ] && printACL "$DATAPATH"
    [ "$XATTRLIST" = "yes" ] && printXATTR "$DATAPATH"
    [ "$CUSTOMMETALIST" != "no" ] && printCustomMetaList "$DATAPATH"
else
    echo
    echo "*** Valid operation type not provided using \"-optype\" option."
    echo
    printUsage
    exit 1
fi
exit 0
