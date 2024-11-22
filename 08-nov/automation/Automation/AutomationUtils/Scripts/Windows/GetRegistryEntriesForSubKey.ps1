Function GetRegistryEntriesForSubKey() 
 {

  $SubKeyName = "##Automation--subkeyname--##" 
  $Recurse    = "##Automation--recurse--##"
  $FindSubKey = "##Automation--findsubkey--##"
  $FindEntry  = "##Automation--findentry--##"

  if ($SubKeyName.StartsWith('REGISTRY::HKEY_LOCAL_MACHINE'))
   {  
    $replace     = "HKEY_LOCAL_MACHINE"
    $replacement = "REGISTRY::HKEY_LOCAL_MACHINE"
   }
  elseif($SubKeyName.StartsWith('REGISTRY::HKEY_USERS'))
   {
    $replace     = "HKEY_USERS"
    $replacement = "REGISTRY::HKEY_USERS"
   }
  elseif($SubKeyName.StartsWith('REGISTRY::HKEY_CURRENT_USER'))
   {
    $replace     = "HKEY_CURRENT_USER"
    $replacement = "REGISTRY::HKEY_CURRENT_USER"
   }

  Get-ItemProperty -Path "$SubKeyName"
  $ListOfSubKeysUnderSubKey = (Get-ChildItem -Recurse $SubKeyName | Format-Table -AutoSize -HideTableHeaders -Property @{n='';e={$_.Name -replace $replace,$replacement};width=5000} | Out-String -Width 60960).Replace("`r`n","`n").Trim().Split("`n")
  if($Recurse -eq 'yes')
   {
    foreach($SubKey in $ListOfSubKeysUnderSubKey)
     {
      Get-ItemProperty -Path "$SubKey".Trim()
     } 
   }
 }
