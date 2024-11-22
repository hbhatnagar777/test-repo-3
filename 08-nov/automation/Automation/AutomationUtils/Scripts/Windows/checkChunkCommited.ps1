Function checkChunkCommited() {
    $JobId = "##Automation--JOBID--##"
    $Dir = "##Automation--DIR--##"
	
	cd "$Dir" #changing the working directory to automation log directory
	#cd ../../..	#changing the working directory to CS log directory	
	$JobId > gk.txt
	$Dir >> gk.txt
	

	$b="$JobId.*Closed.the.chunk.with.ID"

	#check if at-least one chunk is committed in CVD.log, if not wait for 60 seconds and check again until a chunk is committed
	#Select-String -Path CVD.log -Pattern $b -Quiet
	If (Select-String -Path CVD.log -Pattern $b -Quiet){
	return $true
	} Else {
            return $false
        }
	
	
}
