#!/bin/sh

##################################################################################################
# checks the membership of an element in an array
#	Arguments
#		-arg1 (str)   -The element to be checked for membership
#		-arg2 (str[]) -The Array
#	Return
#		1(equivalent to False)  if it is a member     ie., present in the Array 
#		0(equivalent to True )  if it is not a member ie., NOT present in Array
containsElement ()
{
	
	local e match="$1"
	shift
	for e; do [[ "$e" == "$match" ]] && return "1"; done
	return "0"
}
##################################################################################################

##################################################################################################
# Recurse folders and sub folder and computes hash for all the files except the files present in
# folders which are listed under IgnoreArray
#
#	Arguments
#		-arg1 (str)	-The path of the directory
#	Return
#		NONE
GetHash() {
	Path="$1"
	find "$Path" -maxdepth "1" ! -name '*~' ! -name '.*' 2>&1 | grep -v 'system loop' | #Returns the path of files and folders #System loop warnings are ignored
	while IFS= read -r line				  #For each path returned above
	do
		if [ "$line" = "$Path" ]; then	  #We ignore the first Path since its already the Path
			continue					  #what we passed as an argument
		elif [[ -f "$line" ]]; then 	 	 #If file compute hash
			result="$(eval $Algorithm \"$line\")"
			IFS=" " read -r hash path <<< "$result"
			    echo "$hash" "${path// /}"
		elif [[ -d "$line" ]] &&  (( !("$IgnoreCase") && containsElement $(basename "${line}") \
		"${IgnoreArray[@]}" ) || ( "$IgnoreCase" && containsElement $(basename "${line}" | tr\
		'[:upper:]' '[:lower:]')  "${IgnoreArray[@]}" ));then	 #if it is a folder and if not
			GetHash "$line" 										 #present in the IgnoreArray then
		fi									                     #recurse to get files in the
	done	  												 #subfolder
}
##################################################################################################

#-------------------------------------- Execution starts here -----------------------------------#

#variables
Path="$1"
Ignore="$2"
IgnoreCase="$3"
Algorithm="$4"
IgnoreArray=()

#constant
declare -r Delimiter="&^&^&"

#Delimits the string into an array of string
temp="$Ignore$Delimiter"
while [[ "$temp" ]]
	do
    		IgnoreArray+=( "${temp%%"$Delimiter"*}" );
    		temp="${temp#*"$Delimiter"}";
	done

#Converts the array elements to lowercase
if  "$IgnoreCase" ;then
	IgnoreArray=( "${IgnoreArray[@],,}" )
fi

#Function call
GetHash "$Path"
##################################################################################################
