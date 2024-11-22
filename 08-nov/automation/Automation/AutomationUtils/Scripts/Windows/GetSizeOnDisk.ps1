
Function GetSizeOnDisk() {

    $Username = "##Automation--username--##"
    $Password = "##Automation--password--##"
    $NetworkPath = "##Automation--network_path--##"
    $Drive = "##Automation--drive--##"
    $Path = "##Automation--path--##"
    $Type = "##Automation--type--##"


    $temp = [System.Uri]$NetworkPath

    if ($temp.IsUnc)
    {
        $Password = $Password|ConvertTo-SecureString -AsPlainText -Force
        $Cred = New-Object System.Management.Automation.PsCredential($Username,$Password)
        New-PSDrive -Name $Drive -PSProvider "FileSystem" -Root $NetworkPath -Credential $Cred | Out-Null
    }

   
$source = @"
 using System;
 using System.Runtime.InteropServices;
 using System.ComponentModel;
 using System.IO;

 namespace Win32
  {
    
    public class Disk {
	
    [DllImport("kernel32.dll")]
    static extern uint GetCompressedFileSizeW([In, MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
    [Out, MarshalAs(UnmanagedType.U4)] out uint lpFileSizeHigh);	
        
    public static ulong GetSizeOnDisk(string filename)
    {
      uint HighOrderSize;
      uint LowOrderSize;
      ulong size;

      FileInfo file = new FileInfo(filename);
      LowOrderSize = GetCompressedFileSizeW(file.FullName, out HighOrderSize);

      if (HighOrderSize == 0 && LowOrderSize == 0xffffffff)
      {
	    throw new Win32Exception(Marshal.GetLastWin32Error());
      }
      else 
      { 
	    size = ((ulong)HighOrderSize << 32) + LowOrderSize;
	    return size;
      }
    }
  }
}

"@

Add-Type -TypeDefinition $source

$total_size_on_disk = 0

If ($Type -eq "Folder") 
{


    Get-ChildItem -Recurse $Path | Where-Object { ! $_.PSIsContainer} | Foreach-Object { 
  
            $size = [Win32.Disk]::GetSizeOnDisk($_.FullName)
            $total_size_on_disk += $size    
        }
        return $total_size_on_disk
}
ElseIf ($Type -eq "File") 
{

    $fileobj = Get-ChildItem $Path
    $total_size_on_disk = [Win32.Disk]::GetSizeOnDisk($fileobj.FullName)
    return $total_size_on_disk
}


Else 
{
    return "Type Not Supported"
}

}
