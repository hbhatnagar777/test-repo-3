Function WindowsOperation()
    {
    $user  =      "##Automation--user--##"
    $action=      "##Automation--action--##"
    $permission = "##Automation--permission--##"
    $path  =      "##Automation--path--##"
    $getacl=      "##Automation--getacl--##"
    $modifyacl=      "##Automation--modifyacl--##"
    $folder=      "##Automation--folder--##"
    $remove   =      "##Automation--remove--##"
    $targetfolder= "##Automation--targetfolder--##"	
    
    if($path.StartsWith('\\'))
    {
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($using:Credentials.Password)
    $Plaintext = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    $username= $using:Credentials.username
    $path1=Split-Path -Path $path
    net use $path1 /user:$username $Plaintext | Out-Null
    }		
    		

    Function getACL_path()
    {
    if($getacl -eq 'yes')
    {
        $item = Get-ACl $path |Select-Object -ExpandProperty Access|Where-Object IdentityReference -eq $user|Select @{n="Action";e={$_.AccessControlType}},@{n="Permission";e={$_.FileSystemRights}}
	Write-Host "$item"
    }
    else
    {
        $item = Get-ACl $path
	return $item
    }
    
    }

    Function addACE_path()
    {
    $acl=getACL_path
    if(($folder -eq "yes") -and ($targetfolder -eq "2"))
    {$ace = New-object Security.AccessControl.FileSystemAccessRule($user,$permission,'ContainerInherit,ObjectInherit',"None",$action)}
    elseif(($folder -eq "yes") -and ($targetfolder -eq "1"))
    {$ace = New-object Security.AccessControl.FileSystemAccessRule($user,$permission,'ContainerInherit',"NoPropagateInherit",$action)}
    elseif((($folder -eq "yes") -and ($targetfolder -eq "0")) -or ($folder -eq "no"))
    {$ace = New-object Security.AccessControl.FileSystemAccessRule($user,$permission,'None',"None",$action)}
    $acl.AddAccessRule($ace)
    Set-Acl $path $acl
    }
    
    Function removeACE_path()
    {
    $acl=getACL_path
    if($folder -eq "yes")
    {$ace = New-object Security.AccessControl.FileSystemAccessRule($user,$permission,'ContainerInherit,ObjectInherit',"None",$action)}
    else
    {$ace = New-object Security.AccessControl.FileSystemAccessRule($user,$permission,'None',"None",$action)}
    $acl.RemoveAccessRule($ace)
    Set-Acl $path $acl
    }

    if($getacl -eq "yes")
    {
    getACL_path

    }

    if($modifyacl -eq "yes")
    {
        if($remove -eq "yes")
        {
        removeACE_path
        }
        else
        {
        addACE_path
        }
    }

}