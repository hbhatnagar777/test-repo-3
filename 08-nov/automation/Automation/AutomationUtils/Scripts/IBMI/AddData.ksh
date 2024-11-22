
DATAPATH=""
NUMEMPTYFILE=0
NUMPHYSICALFILE=0
NUMMEMBER=1
NUMSAVFFILE=0
NUMDELETE=0
NUMATTRIBUTES=0
SIZEINKB=5000
NUMDATAAREA=1
testcaseID=""


createDataArea()
{
	local FILEITR=1
	while [ $FILEITR -le $NUMDATAAREA ]
	do
		if [ -e /QSYS.LIB/$DATAPATH.LIB/DA$testcaseID$FILEITR.DTAARA ]
		then
			command="CHGDTAARA DTAARA($DATAPATH/DA$testcaseID$FILEITR (130 15)) VALUE(INCREMENTAL)"
			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't modify data area in library $DATAPATH"
				exit 1
			fi
		else
			command="CRTDTAARA DTAARA($DATAPATH/DA$testcaseID$FILEITR) TYPE(*CHAR) LEN(150) VALUE('FULL')"
			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't add data area in library $DATAPATH"
				exit 1
			fi
		fi
		((FILEITR=FILEITR+1))
	done
}

changeAttributes()
{
	local FILEITR=1
	while [ $FILEITR -le $NUMATTRIBUTES ]
	do
		if [ -e /QSYS.LIB/$DATAPATH.LIB/SA$testcaseID$FILEITR.FILE ]
		then
			command="GRTOBJAUT OBJ($DATAPATH/SA$testcaseID$FILEITR) OBJTYPE(*ALL) USER(*PUBLIC) AUT(*ALL)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't change file in library $DATAPATH"
				exit 1
			fi
		fi

		if [ -e /QSYS.LIB/$DATAPATH.LIB/EM$testcaseID$FILEITR.FILE ]
		then
			command="GRTOBJAUT OBJ($DATAPATH/EM$testcaseID$FILEITR) OBJTYPE(*ALL) USER(*PUBLIC) AUT(*ALL)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't change file in library $DATAPATH"
				exit 1
			fi
		fi

		if [ -e /QSYS.LIB/$DATAPATH.LIB/PH$testcaseID$FILEITR.FILE ]
		then
			command="GRTOBJAUT OBJ($DATAPATH/PH$testcaseID$FILEITR) OBJTYPE(*ALL) USER(*PUBLIC) AUT(*ALL)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't change file in library $DATAPATH"
				exit 1
			fi
		fi

		((FILEITR=FILEITR+1))
	done
}

deleteFiles()
{
	local FILEITR=1
	while [ $FILEITR -le $NUMDELETE ]
	do
		if [ -e /QSYS.LIB/$DATAPATH.LIB/SA$testcaseID$FILEITR.FILE ]
		then
			command="DLTF FILE($DATAPATH/SA$testcaseID$FILEITR)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't delete file in library $DATAPATH"
				exit 1
			fi
		fi

		if [ -e /QSYS.LIB/$DATAPATH.LIB/EM$testcaseID$FILEITR.FILE ]
		then
			command="DLTF FILE($DATAPATH/EM$testcaseID$FILEITR)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't delete file in library $DATAPATH"
				exit 1
			fi
		fi

		if [ -e /QSYS.LIB/$DATAPATH.LIB/PH$testcaseID$FILEITR.FILE ]
		then
			command="DLTF FILE($DATAPATH/PH$testcaseID$FILEITR)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't delete file in library $DATAPATH"
				exit 1
			fi
		fi

		((FILEITR=FILEITR+1))
	done
}

createSavfFiles()
{
	local FILEITR=1
	savcommand[0]="SAVLIB LIB($DATAPATH) DEV(*SAVF) OUTPUT(*OUTFILE) "
	savcommand[1]="SAV OBJ(('/tmp/$DATAPATH_file.txt')) "
	local commandItr=0
	devicefile=""

	if [ -e /dev/urandom ]
	then
	    devicefile="/dev/urandom"
	else
	    devicefile="/dev/zero"
	fi

	if ! `dd if=$devicefile of=/tmp/$DATAPATH_file.txt bs=1k count=$SIZEINKB 2>/dev/null`
	then
	    echo
	    echo "*** Failed to create /tmp file"
	    echo
	    exit 1
	fi

	while [ $FILEITR -le $NUMSAVFFILE ]
	do
		if ! [ -e /QSYS.LIB/$DATAPATH.LIB/SA$testcaseID$FILEITR.FILE ]
		then
			command="CRTSAVF FILE($DATAPATH/SA$testcaseID$FILEITR)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't create SAVF files in library $DATAPATH"
				exit 1
			fi
		else
			command="CLRSAVF FILE($DATAPATH/SA$testcaseID$FILEITR)"

			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't clear SAVF files in library $DATAPATH"
				exit 1
			fi
		fi

		if [ $commandItr -eq 0 ]
		then
			command="${savcommand[0]} OMITOBJ((SA*) (DBLIB*)) SAVF($DATAPATH/SA$testcaseID$FILEITR) OUTFILE($DATAPATH/DBLIB$FILEITR)"
			commandItr=1
		else
			command="${savcommand[1]} DEV('/QSYS.LIB/$DATAPATH.LIB/SA$testcaseID$FILEITR.FILE')"
			commandItr=0
		fi

		if ! `system "$command" > /dev/null`
		then
			echo "Couldn't add SAV data in library $DATAPATH"
			exit 1
		fi

		((FILEITR=FILEITR+1))
	done

}

createEmptyFiles()
{
	local FILEITR=1
	while [ $FILEITR -le $NUMEMPTYFILE ]
	do
		if [ -e /QSYS.LIB/$DATAPATH.LIB/EM$testcaseID$FILEITR.FILE ]
		then
			((FILEITR=FILEITR+1))
			continue
		fi

		command="CRTSRCPF FILE($DATAPATH/EM$testcaseID$FILEITR) MBR(*NONE)"

		if ! `system "$command" > /dev/null`
		then
			echo "Couldn't create empty file in library $DATAPATH"
			exit 1
		fi

		((FILEITR=FILEITR+1))
	done
}

createDataFiles()
{
	local FILEITR=1
	while [ $FILEITR -le $NUMPHYSICALFILE ]
	do
		if ! [ -e /QSYS.LIB/$DATAPATH.LIB/PH$testcaseID$FILEITR.FILE ]
		then
			command="CRTSRCPF FILE($DATAPATH/PH$testcaseID$FILEITR) MBR(*NONE)"
			if ! `system "$command" > /dev/null`
			then
				echo "Couldn't create file in library $DATAPATH"
				exit 1
			fi
		fi

		local MEMITR=1
		while [ $MEMITR -le $NUMMEMBER ]
		do
			if ! [ -e /QSYS.LIB/$DATAPATH.LIB/PH$testcaseID$FILEITR.FILE/MEMBER$MEMITR.MBR ]
			then
				command="ADDPFM FILE($DATAPATH/PH$testcaseID$FILEITR) MBR(MEMBER$MEMITR)"

				if ! `system "$command" > /dev/null`
				then
					echo "Couldn't create member in library $DATAPATH"
					exit 1
				fi
			fi

			((MEMITR=MEMITR+1))
		done

		((FILEITR=FILEITR+1))
	done
}

createLibrary()
{
	if [ -e /QSYS.LIB/$DATAPATH.LIB ]
	then
		return 0
	fi

	command="CRTLIB LIB($DATAPATH)"

	if ! `system "$command" > /dev/null`
	then
		echo "Couldn't create library $DATAPATH"
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

testcaseID=`echo $DATAPATH | cut -c 5-`

createLibrary "$DATAPATH"

while [ $# -gt 0 ]
do
    case $1 in
        -numSavfFile)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of savf files expected after \"-numSavfFile\" option."
                echo
                exit 1
            fi
            NUMSAVFFILE=$1
            shift
            ;;
        -numEmptyFile)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of empty files expected after \"-numEmptyFile\" option."
                echo
                exit 1
            fi
            NUMEMPTYFILE=$1
            shift
            ;;
        -numDataFile)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of physical files expected after \"-numDataFile\" option."
                echo
                exit 1
            fi
            NUMPHYSICALFILE=$1
            shift
            ;;
        -numDeletes)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of files to delete expected after \"-numDeletes\" option."
                echo
                exit 1
            fi
            NUMDELETE=$1
            shift
            ;;
        -numAttribute)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of attribute changes expected after \"-numAttribute\" option."
                echo
                exit 1
            fi
            NUMATTRIBUTES=$1
            shift
            ;;
        -numMember)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of members expected after \"-numMember\" option."
                echo
                exit 1
            fi
            NUMMEMBER=$1
            shift
            ;;
        -sizeSavf)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Size in KB expected after \"-sizeSavf\" option."
                echo
                exit 1
            fi
            SIZEINKB=$1
            shift
            ;;
		-numDataArea)
            shift
            if [ $# -eq 0 ]
            then
                echo
                echo "*** Number of data area objects expected after \"-numDataArea\" option."
                echo
                exit 1
            fi
            NUMDATAAREA=$1
            shift
            ;;

	esac
done
	
createDataArea
createEmptyFiles
createDataFiles
createSavfFiles
deleteFiles
changeAttributes
