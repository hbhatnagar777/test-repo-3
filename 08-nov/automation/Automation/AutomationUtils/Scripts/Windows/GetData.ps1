# POWERSHELL SCRIPT TO GET METADATA OF THE ITEMS BASED ON GIVEN INPUT PARAMETERS
# USING GetData.bash AS REFERENCE

Function GetData() 
    {
        $Path            = "##Automation--path--##"
        $name            = "##Automation--name--##"
        $meta            = "##Automation--meta--##"
        $sum             = "##Automation--sum--##"
        $acls            = "##Automation--acls--##"
        $xattr           = "##Automation--xattr--##"
        $sorted          = "##Automation--sorted--##"
        $dirtime         = "##Automation--dirtime--##"
        $attrname        = "cvattr"
        $attrvalue       = "autovalue"
        $CustomMetaList  = "##Automation--custom_meta_list--##"

        # To print sample usage, no arguments
        function printUsage()
         {
          Write-Host "Sample usage below, -path is mandatory"
          Write-Host "-path datapath -name yes -meta yes -sum yes -acls yes -xattr yes -sorted yes -dirtime yes"
         }

        # Print full path of all the items in the given directory
        function printPath($Path)
         {
          Write-Host "$Path"
          if ($sorted -eq "yes")
           { 
            $ListOfItems = (Get-ChildItem -Recurse $Path).FullName | Sort-Object 
           }
          else
           {
            $ListOfItems = (Get-ChildItem -Recurse $Path).FullName
           }
          foreach($item in $ListOfItems)
           {
            Write-Host "$item"
           }
         }

        # Print complete "dir" output of all the items in the given directory
        function printMeta($Path)
         {
          $len = $Path.Length+1
          # Not printing Mode property of items if the path is UNC, the archive bit could be different for the restored files, especially for Windows FS Network Share Clients 
          if ($Path.StartsWith("\\")) 
           {
            $items = Get-ChildItem -Recurse $Path | ForEach-Object {
              $item = $_
              if ($item.PSIsContainer -and $dirtime -eq 'no')
               {
			          return
               }
              else
               {
                ($item | Format-Table -AutoSize -HideTableHeaders -Property @{e={$_.LastWriteTime}}, @{e={$_.Length};width=50}, @{e={$_.FullName -replace '^.{'+$($len)+'}'};width=10000} | Out-String -Width 60960).Trim() + "`n"
               }
              }
           }
          else
           {
            $items = Get-ChildItem -Recurse $Path | ForEach-Object {
              $item = $_
              if ($item.PSIsContainer -and $dirtime -eq 'no')
               {
                return
               }
              else
               {
                ($item | Format-Table -AutoSize -HideTableHeaders -Property @{e={$_.Mode};width=50}, @{e={$_.LastWriteTime.ToString("MM/dd/yyyy hh:mm tt")}}, @{e={$_.Length};width=50}, @{e={$_.FullName -replace '^.{'+$($len)+'}'};width=10000} | Out-String -Width 60960).Trim()+"`n"
               }
             }
           }
	        Write-Host $items
         }

        # Print checksum of all the files in the given directory
        function printSum($Path)
         {
          $len = $path.Length+1
          if ($sorted -eq "yes")
           { 
            $ListOfItems = (Get-ChildItem -Recurse -File $Path).FullName | Sort-Object 
           }
          else
           {
            $ListOfItems = (Get-ChildItem -Recurse -File $Path).FullName
           }
          foreach($item in $ListOfItems)
           {
            Write-Host (Get-FileHash -Path $item -Algorithm MD5 | Format-Table -Property Hash, @{n='Path';e={$_.Path -replace '^.{'+$($len)+'}'}} -HideTableHeaders -AutoSize| Out-String).Trim()
           }
         }

        # Print ACLs of all the items in the given directory
        function printACL($Path)
         {
          $items =  Get-ChildItem -Recurse $Path | Select-Object -Property @{n='# file';e={$_.FullName}}, @{n='# owner';e={(Get-Acl).Owner}} | Format-List | Out-String
          Write-Host $items
         }

        # Print XATTR of all the items in the given directory THIS IS A COPY OF printACL() NEED TO IMPLEMENT IT CORRECTLY
        function printXATTR()
         {
          $items =  Get-ChildItem -Recurse $Path | Select-Object -Property @{n='# file';e={$_.FullName}}, @{n='# owner';e={(Get-Acl).Owner}} | Format-List | Out-String
          Write-Host $items
         }

        # Prints the list of item properties as per the list that's been provided.
        function printCustomMetaList($Path)
         {
          $Files = $False
          $Force = $False
          $Props = switch ($CustomMetaList -split ',')
           {
            "'FilesOnly'"        { $Files = $True; continue } # Save in Boolean var.
            "'Hidden'"           { $Force = $True; continue } # Save in Boolean var.
            "'FullName'"         { 'FullName'; continue }
            "'Size'"             { 'Length'; continue }         # Map 'Size' to 'Length'
            "'Mode'"             { 'Mode'; continue }
            "'LastWriteTimeUtc'" { @{ n=$_; e = { [int] (Get-Date -Date $_.LastWriteTimeUtc -UFormat %s)}}} #  Calculated property
            "'CreationTimeUtc'"  { @{ n=$_; e = { [int] (Get-Date -Date $_.CreationTimeUtc -UFormat %s)}}} #  Calculated property
            "'LastAccessTimeUtc'"  { @{ n=$_; e = { [int] (Get-Date -Date $_.LastAccessTimeUtc -UFormat %s)}}} #  Calculated property
            "'Attributes'"       {'Attributes'; continue}
            "'SizeOnDisk'"       { @{ n=$_; e = { (GetSizeOnDisk($_.FullName))}}}
           }

          $script:memberDefinition = @'

public struct FILE_STANDARD_INFO {
  public long AllocationSize;
  public long EndOfFile;
  public uint         NumberOfLinks;
  public bool       DeletePending;
  public bool       Directory;
}

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern IntPtr CreateFile(
        [MarshalAs(UnmanagedType.LPTStr)] string filename,
        [MarshalAs(UnmanagedType.U4)] UInt32 access,
        [MarshalAs(UnmanagedType.U4)] UInt32 share,
        IntPtr securityAttributes, // optional SECURITY_ATTRIBUTES struct or IntPtr.Zero
        [MarshalAs(UnmanagedType.U4)] UInt32 creationDisposition,
        [MarshalAs(UnmanagedType.U4)] UInt32 flagsAndAttributes,
        IntPtr templateFile);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetFileInformationByHandleEx(
        IntPtr hFile,
        int infoClass,
        out FILE_STANDARD_INFO fileInfo,
        uint dwBufferSize);

'@
            function GetSizeOnDisk($fileName){
                $fileHandle = [Kernel32.File]::CreateFile($fileName,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite,
                [System.IntPtr]::Zero,
                [System.IO.FileMode]::Open,
                [System.UInt32]0x02000000,
                [System.IntPtr]::Zero)
                $fileBasicInfo = New-Object -TypeName Kernel32.File+FILE_STANDARD_INFO
                $bRetrieved = [Kernel32.File]::GetFileInformationByHandleEx($fileHandle,1,
                [ref]$fileBasicInfo,
                [System.Runtime.InteropServices.Marshal]::SizeOf($fileBasicInfo))
                $size = $fileBasicInfo.AllocationSize
                $bClosed = [Kernel32.File]::CloseHandle($fileHandle)
                $size
            }

          Add-Type -MemberDefinition $script:memberDefinition -Name File -Namespace Kernel32

          Get-ChildItem -File:$Files $Path -Recurse -Force:$Force | Format-Table -Property $props -HideTableHeaders -AutoSize | Out-String -Width 5000
         }

         if ($name -eq "yes")
         {
          printPath $Path
         }
    
         if ($sum -eq "yes")
         {
          printSum $Path
         }
		 
		 if ($meta -eq "yes")
         {
          printMeta $Path
         }
		 
		 if ($acls -eq "yes")
         {
          printACL $Path
         }

         if ($CustomMetaList -ne "no")
         {
          printCustomMetaList $Path
         }
    }