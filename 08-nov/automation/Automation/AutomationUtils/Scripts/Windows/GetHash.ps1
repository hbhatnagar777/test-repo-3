Function GetHash() { 

##################################################################################################
# Recurses folders and subfolders and computes hash for all the files except the files present in
# the folders which are listed under Ignore.
#
#	Arguments
#		-arg1 (str)	-The path of the directory
#	Return
#		Hash value of all files along with their path except the ignored
Function Recurse($Path) {

		$Hash = (Get-ChildItem -Path $Path -force | ForEach-Object {

		If(! $_.PsIsContainer){    # If it is a file
			    Get-FileHash -Path $_.FullName -Algorithm $Algorithm | Select Hash, Path 
		}

		ElseIf($_.PsIsContainer -and ( (!$IgnoreCase -and !$Ignore.Contains($_.BaseName)) `
		-or ($IgnoreCase -and !$Ignore.Contains($_.BaseName.ToLower()) ))) {
		#If it is a folder and not in the ignore list
			Recurse $_.FullName  
        }
		
	}
	)
    return $Hash
    }
##################################################################################################

#-------------------Execution starts here -------------------------------------------------------#

#Variables
$Username =    "##Automation--username--##"
$Password =    "##Automation--password--##"
$NetworkPath =  "##Automation--network_path--##"
$Drive =        "##Automation--drive--##"
$Path =   	    "##Automation--path--##"					#string
$Type =   		"##Automation--type--##"					#string
$Ignore = 		"##Automation--ignore--##"					#string
$Algorithm =    "##Automation--algorithm--##"				#string
$IgnoreCase =   ##Automation--ignore_case--##				#boolean


$temp = [System.Uri]$NetworkPath

if ($temp.IsUnc)
{
	$Password = $Password|ConvertTo-SecureString -AsPlainText -Force
	$Cred = New-Object System.Management.Automation.PsCredential($Username,$Password)
	New-PSDrive -Name $Drive -PSProvider "FileSystem" -Root $NetworkPath -Credential $Cred | Out-Null
}

#Constants				
Set-Variable Delimiter -option Constant -value "!@##@!"     #string constant

#Splits the string of folders using delimiters into an array of strings	
$Ignore = $Ignore -split $Delimiter 	

#Converts the Case of the Ignore array elements to lowerCase	
If($IgnoreCase) {						
	$Ignore=$Ignore.ToLower()
}
 

$Hash = If ($Type -eq "Folder") {
			Recurse $Path				#calls GetHash function
		} ElseIf ($Type -eq "File") {
			(Get-FileHash $Path -Algorithm $Algorithm).Hash    #returns hash if it is a single file   
		} Else {
			"Type Not Supported"
		}
$Hash = $Hash -replace '\s+',''

return $Hash
##################################################################################################
}

