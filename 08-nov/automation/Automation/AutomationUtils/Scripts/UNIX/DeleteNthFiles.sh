target_dir=##Automation--directory--##
delete_factor=##Automation--deletefactor--##
keep_factor=##Automation--keepfactor--##
file_counter=0
if [[ delete_factor -gt 0 ]]
	then
		for file_sample in "$target_dir"*
		do
			if [[ $((file_counter%delete_factor)) -eq 0 ]]
			then
				rm "$file_sample"
			fi
			file_counter=$((file_counter + 1))
		done
	else
		for file_sample in "$target_dir"*
		do
			if [[ $((file_counter%keep_factor)) -ne 0 ]]
			then
				rm "$file_sample"
			fi
			file_counter=$((file_counter + 1))
		done
fi
