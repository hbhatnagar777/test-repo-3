Function get_commvault_process() {
  
	$INSTANCE_NAME="##Automation--INSTANCE_NAME--##"
	$JOB_ID="##Automation--JOB_ID--##"
	$CVD_PATH="##Automation--CVD_PATH--##"
	
	
	$JOB_ID > gk.txt
	$CVD_PATH >> gk.txt
	
	$INSTALL_DIR=($CVD_PATH -split "Log Files")[0]
	
	Get-Content $CVD_PATH | findstr "Launched Process:" | findstr -i $JOB_ID | Out-File $INSTALL_DIR\Base\Temp\temp_file
	$count =0
	Get-Content $INSTALL_DIR\Base\Temp\temp_file |%{ $count++ }
	$lines = Get-Content $INSTALL_DIR\Base\Temp\temp_file
	$json_ob="{"
	foreach ($l in $lines){
	$a=($l -split "Launched Process: ")[1]
	$x = ($a -split ' ')[0]
	$proc=($x -split '<')[1]
	$pids=($l -split "Pid=")[1]
	$json_ob=$json_ob+""""+$proc+""":"+$pids
	$count--
	If($count -ne 0){
	$json_ob=$json_ob+","
	}
	}
	$json_ob=$json_ob+"}"
	$json_ob | Out-File $INSTALL_DIR\Base\Temp\temp_file
	echo $json_ob
	
	
}
