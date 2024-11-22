Function checkChunkCommited() {

	$INFORMIX_DIR="##Automation--INFORMIX_DIR--##"
	$SERVER_NAME="##Automation--SERVER_NAME--##"
	$OPERATION="##Automation--OPERATION--##"
	$DATABASE="##Automation--DATABASE--##"
	$CLIENT_NAME="##Automation--CLIENT_NAME--##"
	$INSTANCE="##Automation--INSTANCE--##"
	$BASE_DIR="##Automation--BASE_DIR--##"
	$COPY_PRECEDENCE="##Automation--COPY_PRECEDENCE--##"
	$TOKEN_FILE_PATH="##Automation--TOKEN_FILE_PATH--##"
	$SERVER_NUM="##Automation--SERVER_NUM--##"
	$ARGUMENTS="##Automation--ARGUMENTS--##"
	
	$env:CvClientName=$CLIENT_NAME
	$env:CvInstanceName=$INSTANCE
	If(!$TOKEN_FILE_PATH.equals("None")){
	$env:CvQcmdTokenFile=$TOKEN_FILE_PATH
	
	}
	cd $INFORMIX_DIR
	##setting the environmental variables
	$a=Get-Content $SERVER_NAME`.cmd | %{ $_.Split(' ')[1]; } | %{ $_.Split('=')[0]; }
	$b=Get-Content $SERVER_NAME`.cmd | %{ $_.Split('=')[1]; }
	$count = $a.count
	For($i=0;$i -lt $count;$i++){
	$str1=$a[$i]
	$str2=$b[$i]
	If ( $str1.tolower() -ne "path"){
	$command = '$env'+"`:$str1=""$str2"""
	Invoke-Expression $command
	}
	}

	$old_path=$env:path
	$inf_dir=$env:informixdir
	$new_path=$old_path+';'+$inf_dir+'\bin'
	$env:path=$new_path
	
	If($OPERATION -eq "status"){
	onstat - > status.txt
	$output=(Get-Content status.txt)
	If($output -like '*On-Line*'){ return $true}
	Else{ return $false}
	}
	
	If($OPERATION -eq "stop"){
	onmode -yuk
	}
	
	If($OPERATION -eq "start"){
	Start-Service $SERVER_NAME
	}
	
	If($OPERATION -eq "online"){
	onmode -m
	}

	If($OPERATION -eq "dbspace_down"){
	Start-Service $SERVER_NAME
	onmode -yO
	}

	If($OPERATION -eq "create_dbspace"){
	if(!(Test-Path cvauto1)){
	echo $null > cvauto1
	}
	onspaces -c -d cvauto1 -p "$INFORMIX_DIR\cvauto1" -o 0 -s 10240000
	}
	
	If($OPERATION -eq "drop_dbspace"){
	onspaces -d cvauto1 -y
	}
	
	If($OPERATION -eq "create_db"){
	$query = "create database $DATABASE in cvauto1 with buffered log;"
	echo "$query" | dbaccess sysmaster
	}
	
	If($OPERATION -eq "switch_log"){
	cd $BASE_DIR
	onmode -l
	cd $INFORMIX_DIR
	}
	
	If($OPERATION -eq "log_only_backup"){
	cd $BASE_DIR
	onbar -b -l
	cd $INFORMIX_DIR
	}
	
	If($OPERATION -eq "cl_full_entire_instance"){
	cd $BASE_DIR
	onbar -b -L 0
	cd $INFORMIX_DIR
	}
	
	If($OPERATION -eq "cl_incremental_entire_instance"){
	cd $BASE_DIR
	onbar -b -L 1
	onbar -b -L 2
	cd $INFORMIX_DIR
	}
	
	If($OPERATION -eq "cl_restore_entire_instance"){
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "physical_restore"){
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -p 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}

	If($OPERATION -eq "secondary_copy_restore"){
	cd $BASE_DIR
	$env:CVGX_COPYID=$COPY_PRECEDENCE
	$env:CVGX_COPYID > C:\\aaa
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -p 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "cl_full_whole_system"){
	cd $BASE_DIR
	onbar -b -w -L 0
	cd $INFORMIX_DIR
	}
	
	If($OPERATION -eq "cl_incremental_whole_system"){
	cd $BASE_DIR
	onbar -b -w -L 1
	onbar -b -w -L 2
	cd $INFORMIX_DIR
	}
	
	If($OPERATION -eq "cl_restore_whole_system"){
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -w 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "secondary_copy_restore_whole_instance"){
	cd $BASE_DIR
	$env:CVGX_COPYID=$COPY_PRECEDENCE
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -w -p 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}

	If($OPERATION -eq "physical_restore_whole_system"){
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -w -p 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "log_only_restore"){
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -l 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}

	If($OPERATION -eq "secondary_copy_log_only_restore"){
	cd $BASE_DIR
	$env:CVGX_COPYID=$COPY_PRECEDENCE
	$ErrorActionPreference = "SilentlyContinue"
	$a = onbar -r -l 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "ENTIRE_INSTANCE_CROSS_MACHINE"){
	$env:INFORMIXSERVER=$SERVER_NAME
	$env:CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	If($ARGUMENTS -eq "None"){
	$a = onbar -r -p 2> $BASE_DIR\\Temp\\aaa
	}
	Else{
	$a = onbar -r -p "$ARGUMENTS" 2> $BASE_DIR\\Temp\\aaa
	}
	$a = onbar -r -l 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "WHOLE_SYSTEM_CROSS_MACHINE"){
	$env:INFORMIXSERVER=$SERVER_NAME
	$env:CV_IFX_SOURCE_SERVERNUM=$SERVER_NUM
	cd $BASE_DIR
	$ErrorActionPreference = "SilentlyContinue"
	If($ARGUMENTS -eq "None"){
	$a = onbar -r -w -p 2> $BASE_DIR\\Temp\\aaa
	}
	Else{
	$a = onbar -r -w -p "$ARGUMENTS" 2> $BASE_DIR\\Temp\\aaa
	}
	$a = onbar -r -l 2> $BASE_DIR\\Temp\\aaa
	cd $INFORMIX_DIR
	return $true
	}
	
	If($OPERATION -eq "table_level_restore"){
	cd $BASE_DIR
	If(Test-Path -path $INFORMIX_DIR\\etc\\ac_config.std.org){
	cp -f $INFORMIX_DIR\\etc\\ac_config.std.org $INFORMIX_DIR\\etc\\ac_config.std
	}
	cp -f $INFORMIX_DIR\\etc\\ac_config.std $INFORMIX_DIR\\etc\\ac_config.std.org
	echo "AC_MSGPATH	C:\tmp\ac_msg.log" > $INFORMIX_DIR\\etc\\ac_config.std
	echo "AC_STORAGE	C:\tmp" >> $INFORMIX_DIR\\etc\\ac_config.std
	echo "AC_VERBOSE	1" >> $INFORMIX_DIR\\etc\\ac_config.std
	echo "AC_DEBUG	5" >> $INFORMIX_DIR\\etc\\ac_config.std
	echo "AC_SCHEMA	$INFORMIX_DIR\\etc\\ac_schema" >> $INFORMIX_DIR\\etc\\ac_config.std
	If(Test-Path -path $INFORMIX_DIR\\etc\\ac_schema){
	rm -f $INFORMIX_DIR\\etc\\ac_schema
	}
	echo "database auto1;" > $INFORMIX_DIR\\etc\\ac_schema
	echo "create table tab1 (ANAME varchar(25),BNAME varchar(25),CNAME varchar(25),DNAME varchar(25),ENAME varchar(25),FNAME varchar(25)) in cvauto1;" >> $INFORMIX_DIR\\etc\\ac_schema
	echo "create table tabTableLevelRestore (ANAME varchar(25),BNAME varchar(25),CNAME varchar(25),DNAME varchar(25),ENAME varchar(25),FNAME varchar(25)) in cvauto1;" >> $INFORMIX_DIR\\etc\\ac_schema
	echo "insert into tabTableLevelRestore select * from tab1;" >> $INFORMIX_DIR\\etc\\ac_schema
	echo "restore to current;" >> $INFORMIX_DIR\\etc\\ac_schema
	archecker -Xbvs -f $1/etc/ac_schema
	cd $INFORMIX_DIR
	}
	
}
