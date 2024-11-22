INFORMIX_DIR=##Automation--INFORMIX_DIR--##
SERVER_NAME=##Automation--SERVER_NAME--##
OPERATION=##Automation--OPERATION--##
DATABASE=##Automation--DATABASE--##
CLIENT_NAME=##Automation--CLIENT_NAME--##
INSTANCE=##Automation--INSTANCE--##
BASE_DIR=##Automation--BASE_DIR--##
COPY_PRECEDENCE=##Automation--COPY_PRECEDENCE--##
TOKEN_FILE_PATH=##Automation--TOKEN_FILE_PATH--##
SERVER_NUM=##Automation--SERVER_NUM--##
ARGUMENTS=##Automation--ARGUMENTS--##
OS_NAME=##Automation--OS_NAME--##
INFORMIXSQLHOSTS=##Automation--SQLHOSTS_FILE--##

server_check()
{
	cd $INFORMIX_DIR
	export INFORMIXDIR=$INFORMIX_DIR
	export INFORMIXSERVER=$SERVER_NAME
	export ONCONFIG="onconfig."$SERVER_NAME
	export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS
	export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH}
	
	export CvClientName=$CLIENT_NAME
	export CvInstanceName=$INSTANCE
	if [ $OS_NAME != "None" ]
	then
		export LD_LIBRARY_PATH=$BASE_DIR
	fi
	
	if [ $TOKEN_FILE_PATH != "None" ]
	then
		export CvQcmdTokenFile=$TOKEN_FILE_PATH
	fi
	
	if [ $OPERATION == "status" ]
	then
		echo `onstat -`
	fi
	if [ $OPERATION == "start" ]
	then
		echo `oninit -vy` 2> /tmp/123
	fi
	if [ $OPERATION == "stop" ]
	then
		echo `onmode -yuk` 2> /tmp/123
	fi
	if [ $OPERATION == "online" ]
	then
		echo `onmode -m`
	fi
	if [ $OPERATION == "dbspace_down" ]
	then
	  echo `oninit -vy` 2> /tmp/123
		echo `onmode -yO`
	fi
	if [ $OPERATION == "create_dbspace" ]
	then
		touch $INFORMIX_DIR/cvauto1
		chown informix:informix $INFORMIX_DIR/cvauto1
		chmod 660 $INFORMIX_DIR/cvauto1
		echo `onspaces -c -d cvauto1 -p $INFORMIX_DIR/cvauto1 -o 0 -s 10240000`
	fi
	if [ $OPERATION == "drop_dbspace" ]
	then
		echo `onspaces -d cvauto1 -y`
	fi
	if [ $OPERATION == "create_db" ]
	then
		query="create database $DATABASE in cvauto1 with buffered log;"
		echo "$query" | dbaccess sysmaster 2> /tmp/123
		
	fi
	if [ $OPERATION == "drop_db" ]
	then
		query="drop database if exists $DATABASE;"
		echo "$query" | dbaccess sysmaster
	fi

	if [ $OPERATION == "switch_log" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onmode -l
	fi
	
	if [ $OPERATION == "log_only_backup" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -l
	fi
	
	if [ $OPERATION == "cl_full_entire_instance" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -L 0
	fi
	
	if [ $OPERATION == "cl_incremental_entire_instance" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -L 1
	fi
	
	if [ $OPERATION == "cl_incremental_entire_instance_2" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -L 2
	fi
	
	if [ $OPERATION == "cl_restore_entire_instance" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r 2> /tmp/123
	fi
	
	if [ $OPERATION == "secondary_copy_restore" ]
	then
		export CVGX_COPYID=$COPY_PRECEDENCE
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -p 2> /tmp/123
	fi
	if [ $OPERATION == "physical_restore" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -p 2> /tmp/123
	fi
	
	if [ $OPERATION == "log_only_restore" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -l 2> /tmp/123
	fi

	if [ $OPERATION == "secondary_copy_log_only_restore" ]
	then
		export CVGX_COPYID=$COPY_PRECEDENCE
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -l 2> /tmp/123
	fi
	
	if [ $OPERATION == "cl_full_whole_system" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -w -L 0
	fi
	
	if [ $OPERATION == "cl_incremental_whole_system" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -w -L 1
	fi
	
	if [ $OPERATION == "cl_incremental_whole_system_2" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -b -w -L 2
	fi
	
	if [ $OPERATION == "cl_restore_whole_system" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -w 2> /tmp/123
	fi
	if [ $OPERATION == "secondary_copy_restore_whole_instance" ]
	then
		export CVGX_COPYID=$COPY_PRECEDENCE
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -w -p 2> /tmp/123
	fi
	if [ $OPERATION == "physical_restore_whole_system" ]
	then
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;onbar -r -w -p 2> /tmp/123
	fi
	
	if [ $OPERATION == "ENTIRE_INSTANCE_CROSS_MACHINE" ]
	then
		if [ "$ARGUMENTS" == "None" ]
			then
			su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export INFORMIXSERVER=$SERVER_NAME;export CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;onbar -r -p 2> /tmp/123
			else
			su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export INFORMIXSERVER=$SERVER_NAME;export CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;onbar -r -p $ARGUMENTS 2> /tmp/123
		fi
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export INFORMIXSERVER=$SERVER_NAME;export CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;onbar -r -l 2> /tmp/123
	fi
	if [ $OPERATION == "WHOLE_SYSTEM_CROSS_MACHINE" ]
	then
		if [ "$ARGUMENTS" == "None" ]
		then 
			su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export INFORMIXSERVER=$SERVER_NAME;export CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;onbar -r -w -p 2> /tmp/123
		else
			su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export INFORMIXSERVER=$SERVER_NAME;export CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;onbar -r -w -p $ARGUMENTS 2> /tmp/123
		fi
		su - informix;export INFORMIXDIR=$INFORMIX_DIR;export INFORMIXSERVER=$SERVER_NAME;export ONCONFIG="onconfig."$SERVER_NAME;export INFORMIXSQLHOSTS=$INFORMIXSQLHOSTS;export PATH=${INFORMIXDIR}/bin:${INFORMIXDIR}/extend/krakatoa/jre/bin:${PATH};export INFORMIXSERVER=$SERVER_NAME;export CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM;if [ $OS_NAME != "None" ]; then export LD_LIBRARY_PATH=$BASE_DIR; fi;export CvClientName=$CLIENT_NAME;export CvInstanceName=$INSTANCE;onbar -r -l 2> /tmp/123
	fi
	
	if [ $OPERATION == "table_level_restore" ]
	then
		if [ -f $INFORMIX_DIR/etc/ac_config.std.org ]
		then
			cp -f $INFORMIX_DIR/etc/ac_config.std.org $INFORMIX_DIR/etc/ac_config.std
		fi
		cp $INFORMIX_DIR/etc/ac_config.std $INFORMIX_DIR/etc/ac_config.std.org
		echo "AC_DEBUG	5" >> $INFORMIX_DIR/etc/ac_config.std
		echo "AC_SCHEMA	$INFORMIX_DIR/etc/ac_schema" >> $INFORMIX_DIR/etc/ac_config.std
		if [ -f $INFORMIX_DIR/etc/ac_schema ]
		then
			rm -f $INFORMIX_DIR/etc/ac_schema
		fi
		echo "database auto1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "create table tab1 (ANAME varchar(25),BNAME varchar(25),CNAME varchar(25),DNAME varchar(25),ENAME varchar(25),FNAME varchar(25)) in cvauto1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "create table tabTableLevelRestore (ANAME varchar(25),BNAME varchar(25),CNAME varchar(25),DNAME varchar(25),ENAME varchar(25),FNAME varchar(25)) in cvauto1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "insert into tabTableLevelRestore select * from tab1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "restore to current;" >> $INFORMIX_DIR/etc/ac_schema
		archecker -Xbvs -f $INFORMIX_DIR/etc/ac_schema
	fi
	
	if [ $OPERATION == "aux_copy_table_level_restore" ]
	then
		export CVGX_COPYID=$COPY_PRECEDENCE
		if [ -f $INFORMIX_DIR/etc/ac_config.std.org ]
		then
			cp -f $INFORMIX_DIR/etc/ac_config.std.org $INFORMIX_DIR/etc/ac_config.std
		fi
		cp $INFORMIX_DIR/etc/ac_config.std $INFORMIX_DIR/etc/ac_config.std.org
		echo "AC_DEBUG	5" >> $INFORMIX_DIR/etc/ac_config.std
		echo "AC_SCHEMA	$INFORMIX_DIR/etc/ac_schema" >> $INFORMIX_DIR/etc/ac_config.std
		if [ -f $INFORMIX_DIR/etc/ac_schema ]
		then
			rm -f $INFORMIX_DIR/etc/ac_schema
		fi
		echo "database auto1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "create table tab1 (ANAME varchar(25),BNAME varchar(25),CNAME varchar(25),DNAME varchar(25),ENAME varchar(25),FNAME varchar(25)) in cvauto1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "create table tabTableLevelRestore (ANAME varchar(25),BNAME varchar(25),CNAME varchar(25),DNAME varchar(25),ENAME varchar(25),FNAME varchar(25)) in cvauto1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "insert into tabTableLevelRestore select * from tab1;" >> $INFORMIX_DIR/etc/ac_schema
		echo "restore to current;" >> $INFORMIX_DIR/etc/ac_schema
		archecker -Xbvs -f $INFORMIX_DIR/etc/ac_schema
	fi
}

server_check $INFORMIX_DIR $SERVER_NAME
