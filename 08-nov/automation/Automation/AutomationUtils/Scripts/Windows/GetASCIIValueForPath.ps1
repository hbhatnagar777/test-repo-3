Function GetItemsList()
    {
	 $data_path = "##Automation--data_path--##"
	 $search_term   = "##Automation--search_term--##"
     (Get-ChildItem -Recurse -Path "$data_path" | where {$_.FullName -match $search_term}).FullName | ForEach-Object { [int[]]@("$_").ToCharArray() -join ',' } | Out-String
	}