Function CreateData(){
 $TargetPath = "##Automation--directory--##"
$minfilesize = ("1MB"/1GB)*1GB
 $maxfilesize = 10MB
 $totalsize = ('##Automation--totalsize--##'/1GB)*1GB
 $timerangehours = 24
 $filenameseed = "abcdefghijkl012345"
 $fixedfilesize = ##Automation--filesize--##
 $prefix = "##Automation--prefix--##"
 $suffix = "##Automation--suffix--##"
#
# convert to absolute path as required by WriteAllBytes, and check existence of the directory. 
#
if (-not (Split-Path -IsAbsolute $TargetPath))
{
    $TargetPath = Join-Path (Get-Location).Path $TargetPath
}
if (-not (Test-Path -Path $TargetPath -PathType Container ))
{
    throw "TargetPath '$TargetPath' does not exist or is not a directory"
}

$currentsize = [int64]0
$currentime = Get-Date
while ($currentsize -lt $totalsize)
{
    #
    # generate a random file size. Do the smart thing if min==max. Do not exceed the specified total size. 
    #
    if ($fixedfilesize -gt 0){
        $filesize = $fixedfilesize
    }
    elseif ($minfilesize -lt $maxfilesize) {
        $filesize = Get-Random -Minimum $minfilesize -Maximum $maxfilesize
    }
    else{
        $filesize = $maxfilesize
    }

    if ($currentsize + $filesize -gt $totalsize) {
        $filesize = $totalsize - $currentsize
    }
    $currentsize += $filesize

    #
    # use a very fast .NET random generator
    #
    $data = new-object byte[] $filesize
    (new-object Random).NextBytes($data)
    
    #
    # generate a random file name by shuffling the input filename seed. 
    #
    $filename = ($filenameseed.ToCharArray() | Get-Random -Count ($filenameseed.Length)) -join ''
    $path = Join-Path $TargetPath "$($prefix+$filename+$suffix)"

    #
    # write the binary data, and randomize the timestamps as required. 
    #
    try
    {
        [IO.File]::WriteAllBytes($path, $data)
        if ($timerangehours -gt 0)
        {
            $timestamp = $currentime.AddHours(-1 * (Get-Random -Minimum 0 -Maximum $timerangehours))
        } else {
            $timestamp = $currentime
        }
        $fileobject = Get-Item -Path $path
        $fileobject.CreationTime = $timestamp
        $fileobject.LastWriteTime = $timestamp

        # show what we did. 
        [pscustomobject] @{
            filename = $path
            timestamp = $timestamp
            datasize = $filesize
        }
    } catch {
        $message = "failed to write data to $path, error $($_.Exception.Message)"
        Throw $message
    }    
}
}