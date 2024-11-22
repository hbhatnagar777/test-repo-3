Function AddData()
    {
        <#
        $Path           - The path under which the dataset will be created.                                          (accepts any valid string as value)
        $Dirs           - The number of directories created at each level.                                           (accepts positive integers for value)
        $Files          - The number of files (of all types) created at each level.                                  (accepts positive integers for value)
        $SizeInKb       - The size of files in KB.                                                                   (accepted values are 'yes' or 'no')
        $Levels         - The number of levels i.e. level of nesting.                                                (accepts positive integers as value)
        $HLinks         - Specifies whether hard links need to be created or not.                                    (accepted values are 'yes' and 'no')
        $SLinks         - Specifies whether soft links need to be created or not.                                    (accepted values are 'yes' and 'no')
        $Sparse         - Specifies whether sparse files need to be created or not.                                  (accepted values are 'yes' and 'no')
        $HoleSizeInKb   - Specifies the size of the hole, applicable only if value of $Sparse is 'yes'.              (accepts positive integers for value)
        $HoleOffset     - Specifies the offset in the file in KB from where the sparse range begins.                 (accepted values are 'yes' or 'no')
        $Acls           - Specifies whether files for ACL modifications need to be created or not.                   (accepted values are 'yes' and 'no')
        $ZeroSizeFile   - Specifies whether the file of zero kb should be created or not.                            (accepted values are 'yes' and 'no')
        $ASCIIDataFile  - Specifies whether the file content should be a valid ASCII data[0-9a-zA-z] or not                     (accepted values are 'yes' and 'no')
        $XAttr          - Specifies whether files for XATTR modifications need to be created or not, N/A to Windows.
        $Unicode        - Specifies whether files with unicode characters in their names need to be created or not.  (accepted values are 'yes' and 'no')
        $ZipFilePath    - The path where the problematic dataset resides.                                            (accepts any valid string as value)
        $ZipExePath     - The path where the cv7z.exe binary resides.                                                (accepts any valid string as value)
        $ExtrFilePath   - The path to which the file will be extracted.                                              (accepts any valid string as value)
        $CreateOnly     - Only create files of the specified type. It will take effect only if $Dirs is 0.           (accepts 'sparse', 'hlinks', 'slinks' or 'attributefile' as value)
        $AttributeFiles - Create files with the specified attributes.                                                (accepts a PS array with one or more of the following values R,H,RH)
        $FileName       - Create files with the specific name.
        $ServerHostName - Name of the server hosting the share if the value of $Path happens to be one.
        $Username       - Username of the account that needs to be impersonated when the dataset needs to be created on a share.
        $Password       - Password of the account that needs to be impersonated when the dataset needs to be created on a share.
        #>

        $Path           = "##Automation--path--##"
        $Dirs           = ##Automation--dirs--##
        $Files          = ##Automation--files--##
        $SizeInKb       = ##Automation--size_in_kb--##
        $Levels         = ##Automation--levels--##
        $HLinks         = "##Automation--hlinks--##"
        $SLinks         = "##Automation--slinks--##"
        $Sparse         = "##Automation--sparse--##"
        $HoleSizeInKb   = ##Automation--hole_size_in_kb--##
        $HoleOffset     = ##Automation--hole_offset--##
        $Acls           = "##Automation--acls--##"
        $XAttr          = "##Automation--xattr--##"
        $ZeroSizeFile   = "##Automation--zero_size_file--##"
        $ASCIIDataFile   = "##Automation--ascii_data_file--##"
        $Unicode        = "##Automation--unicode--##"
        $ThreadCnt      =  ##Automation--thread_cnt--##
        $Chinese        = [char[]]@(24555,36895,30340,26837,33394,29392,29432,36339,36807,20102,25042,29399)
        $Japanese       = [char[]]@(36895,12356,33590,33394,12398,12461,12484,12493,12399,24608,24816,12394,29356,12398,19978,12395,39131,12403,20055,12387,12383)
        $Arabic         = [char[]]@(1602,1601,1586,32,1575,1604,1579,1593,1604,1576,32,1575,1604,1576,1606,1610,32,1575,1604,1587,1585,1610,1593,32,1593,1604,1609,1575,1604,1603,1604,1576,32,1575,1604,1603,1587,1608,1604)
        $Special        = [char[]]@(37,36,35,64)
        $Russian        = [char[]]@(1073,1099,1089,1090,1088,1099,1081,32,1082,1086,1088,1080,1095,1085,1077,1074,1099,1081,32,1083,1080,1089,32,1087,1077,1088,1077,1087,1088,1099,1075,1085,1091,1083,32,1095,1077,1088,1077,1079,32,1083,1077,1085,1080,1074,1091,1102,32,1089,1086,1073,1072,1082,1091)
        $TestGroup      = "cvgroup"
        $TestUser       = "cvusr"
        $AclGroup       = "cvgroup2"
        $AclUser        = "cvusr2"
        $ZipFilePath    = "##Automation--zip_file_path--##"
        $ZipExePath     = "##Automation--zip_exe_path--##"
        $ExtrFilePath   = "##Automation--extr_file_path--##"
		$CreateOnly     = "##Automation--create_only--##"
        $AttributeFiles = "##Automation--attribute_files--##"
        $CustomFileName = "##Automation--custom_file_name--##"
        $ServerHostName = "##Automation--server_host_name--##"
        $Username       = "##Automation--username--##"
        $Password       = "##Automation--password--##"

        # Function returns True if Search is NOT in List
        function NotPresentIn($Search,$List)
         {
          return $Search -notin $List
         }

        # Function to check and create user and group to set on the test data set.
        function makeUserAndGroup()
         {
          $UserList  = $(NET USER).split(" ")
          $GroupList = $(NET LOCALGROUP).split(" ")
          if (NotPresentIn $TestUser $UserList)
           {
              NET USER $TestUser "######"/ADD
           }
          if (NotPresentIn $AclUser $UserList)
           {
              NET USER $AclUser "######"/ADD
           }
          if (NotPresentIn *$TestGroup $GroupList)
           {
              NET LOCALGROUP $TestGroup /ADD
              NET LOCALGROUP $TestGroup $TestUser /ADD
           }
          if (NotPresentIn *$AclGroup $GroupList)
           {
              NET LOCALGROUP $AclGroup /ADD
              NET LOCALGROUP $AclGroup $AclUser /ADD
           }
         }





        function createAllFiles
         {
          param($Path_p,$DirName_p,$Levels_p,$HLinks_p,$SLinks_p,$Sparse_p,$Acls_p,$XAttr_p,$ZeroSizeFile_p,$ASCIIDataFile_p,$Unicode_p,$Dirs_p,$Files_p,$SizeInKb_p,$HoleSizeInKb_p,$HoleOffset_p,$Chinese_p,$Japanese_p,$Arabic_p,$Special_p,$Russian_p,$CreateOnly_p,$AttributeFiles_p,$CustomFileName_p)

          $Path             = $Path_p
          $DirName          = $DirName_p
          $Levels           = $Levels_p
          $HLinks           = $HLinks_p
          $SLinks           = $SLinks_p
          $Sparse           = $Sparse_p
          $Acls             = $Acls_p
          $XAttr            = $XAttr_p
          $ZeroSizeFile     = $ZeroSizeFile_p
          $ASCIIDataFile    = $ASCIIDataFile_p
          $Unicode          = $Unicode_p
          $Dirs             = $Dirs_p
          $Files            = $Files_p
          $SizeInKb         = $SizeInKb_p
          $HoleSizeInKb     = $HoleSizeInKb_p
          $HoleOffset       = $HoleOffset_p
          $Chinese          = $Chinese_p
          $Japanese         = $Japanese_p
          $Arabic           = $Arabic_p
          $Special          = $Special_p
          $Russian          = $Russian_p
		  $CreateOnly       = $CreateOnly_p
          $AttributeFiles   = $AttributeFiles_p
          $CustomFileName   = $CustomFileName_p

          $1KB_Content = Invoke-Expression "(@((, (48..57) + (32) + (65..90) + (97..122) ) * 18) | Get-Random -Count  1024 | % {[char]`$_}) -join ''"

          if ($SizeInKb -ge 1024)
           {
                if($ASCIIDataFile -eq 'yes')
                {
                $FileContent = Invoke-Expression "(@((, (48..57) + (32) + (65..90) + (97..122) ) * 18000) | Get-Random -Count  1048576 | % {[char]`$_}) -join ''"
                }
                else
                {
                $FileContent = Invoke-Expression "(@((, (33..254) ) * 4750) | Get-Random -Count  1048576 | % {[char]`$_}) -join ''"
                }
            $Size = $SizeInKb/1024
           }
          else
           {
                if($ASCIIDataFile -eq 'yes')
                {
                $FileContent = Invoke-Expression "(@((, (48..57) + (32) + (65..90) + (97..122) ) * 18) | Get-Random -Count  1024 | % {[char]`$_}) -join ''"
                }
                else
                {
                $FileContent = Invoke-Expression "(@((, (33..254) ) * 5) | Get-Random -Count  1024 | % {[char]`$_}) -join ''"
                }
            $Size = $SizeInKb
           }

          function createAllFiles_2([String]$DirName)
           {
            # Function yet to be implemented
            function setACL()
             {
             }

            # Function yet to be implemented
            function setXattr()
             {
             }

            # Function to set permissions on a given path recursively
            function setPermission()
             {
             }

            # Function to set user and group recursively on a given path
            function setUserAndGroup()
             {
             }

            # Function to create directory
            function makeDirectory([String]$DirectoryName)
             {
              if ( -not ( Test-Path $DirectoryName ) )
               {
                New-Item $DirectoryName -ItemType Directory | Out-Null
               }
             }

            # Function to create file with random data
            function makeFile([String]$FileName,$NumOfFiles=$null,$Attribute=$null,$Extn=$null)
             {
              if ($NumOfFiles -eq $null)
               {
                for($i=1;$i -le $Size;$i++)
                 {
                  $FileContent | Add-Content "$FileName$Extn"
                 }

                if ($Attribute -ne $null)
                 {
                  ATTRIB "$FileName" $Attribute
                 }
               }
              else # CREATE MORE THAN ONE FILE
               {
                for($i=1;$i -le $NumOfFiles; $i++)
                 {
                  for($j=1;$j -le $Size;$j++)
                   {
                    $FileContent | Add-Content "$FileName$i$Extn"
                   }
                  if ($Attribute -ne $null)
                   {
                    ATTRIB "$FileName$i" $Attribute
                   }
                 }
               }
             }

            # Function to create hard link for a file
            function makeHLink([String]$FileName,[String]$HLinkName)
             {
              if ( (Test-Path $FileName) -and (-not (Test-Path $HLinkName)) )
               {
                New-Item $HLinkName -ItemType HardLink -Value $FileName | Out-Null
               }
             }

            # Function to create symbolic link for file
            function makeSLINK([String]$FileName,[String]$SLinkName)
             {
              if ( (Test-Path $FileName) -and (-not (Test-Path $SLinkName)) )
               {
                New-Item $SLinkName -ItemType SymbolicLink -Value $FileName | Out-Null
               }
             }

            function makeSparseFile([String]$FileName,$NumOfFiles=$null,$HoleOffset=$null)
             {
              if ($HoleOffset -eq $null)
               {
                $HoleOffset = 0
               }

              if ($NumOfFiles -eq $null)
               {
                $FileContent | Set-Content $FileName
                fsutil Sparse setflag $FileName
                fsutil Sparse setrange $FileName $HoleOffset $(1024*$HoleSizeInKb)
               }
              else
               {
                for($i=1;$i -le $NumOfFiles;$i++)
                 {
                  $FileContent | Set-Content "$FileName$i"
                  fsutil Sparse setflag "$FileName$i"
                  fsutil Sparse setrange "$FileName$i" $HoleOffset $(1024*$HoleSizeInKb)
                 }
               }
              # Setting sparse flag

             }

            function createRegularFiles([String]$Path)
             {
              makeDirectory "$DirName\regular"
              $FileName = "$DirName\regular\regularfile"
              makeFile $FileName $Files
             }

            # Function to create a single file of 0KB, 1KB, 2KB and 3KB. Reusing code from makeFile(). Need to modify makeFile() to support an additional parameter for size
            function createSmallFiles([String]$Path)
             {
              makeDirectory "$DirName\small"
              Out-File "$DirName\small\0_KB" -Encoding ascii # CREATING A 0KB FILE
              $1KB_Content * 1 | Set-Content "$DirName\small\2_KB"
              $1KB_Content * 2 | Set-Content "$DirName\small\3_KB"
              $1KB_Content * 3 | Set-Content "$DirName\small\4_KB"
             }

            function  createFilesWithCustomFileName([String]$CustomFileName)
             {
              # If the file  name provided is a.txt and number of files to create is 5, then files will be created as a1.txt, a2.txt,.....,a5.txt.
              makeDirectory "$DirName\files_with_custom_name"
              $FileName = "$DirName\files_with_custom_name" # name will be added later by in function  makeFile()
              $Parts = "$CustomFileName".Split(".")
              $FN = $Parts[0]
              $FE = $Parts[1]
              makeFile $DirName\files_with_custom_name\$FN $Files $AttributeFiles ".$FE"
             }

            function createHLinks([String]$DirName)
             {
              makeDirectory "$DirName\hlinks"
              $FileItr = 1
              while ($FileItr -le $Files)
               {
                $FileName = "$DirName\hlinks\file$FileItr"
                $HLinkName = "$DirName\hlinks\hlinksfile$FileItr"
                makeFile $FileName
                makeHLink $FileName $HLinkName
                $FileItr += 1
               }
             }

            function createSLinks([String]$DirName)
             {
              makeDirectory "$DirName\slinks"
              $FileItr = 1
              while ($FileItr -le $files)
               {
                $FileName = "$DirName\slinks\file$FileItr"
                $slinkname = "$DirName\slinks\slinkfile$FileItr"
                makeFile $FileName
                makeSLink $FileName $SLinkName
                $FileItr += 1
               }
             }

            function createSparseFiles()
             {
              makeDirectory "$DirName\sparse"
              $FileName = "$DirName\sparse\sparsefile"
              makeSparseFile $FileName $Files $HoleOffset
             }

            function createACLFiles()
             {
              makeDirectory "$dirname\acls"
              $fileitr = 1
              while ($fileitr -le $files)
              {
               $filename = "$dirname\acls\aclfile$fileitr"
               makeFile $filename
               $fileitr += 1
              }
             }

            function createXattrFiles()
             {
             }

            function createAttributeFiles()
             {
              makeDirectory "$DirName\attribute_files"
              foreach ($attribute in $AttributeFiles)
               {
                if ($attribute -eq 'R')
                 {
                  $FileName = "$DirName\attribute_files\read_only_file"
                  makeFile $FileName $Files "+R"
                 }
                if ($attribute -eq 'H')
                 {
                  $FileName = "$DirName\attribute_files\hidden_file"
                  makeFile $FileName $Files "+H"
                 }
                if ($attribute -eq 'RH' -or $attribute -eq 'HR')
                 {
                  $FileName = "$DirName\attribute_files\read_only_+_hidden_file"
                  makeFile $FileName $Files "+R +H"
                 }
               }

             }

            function createUnicodeFiles([String]$dirname)
             {
              makeDirectory "$dirname\unicode"
              $fileitr = 1
              while ($fileitr -le $files)
               {
                $filename = "$dirname\unicode\$($Chinese -join '')$fileitr"
                makeFile $filename
                $filename = "$dirname\unicode\$($Japanese -join '')$fileitr"
                makeFile $filename
                $filename = "$dirname\unicode\$($Arabic -join '')$fileitr"
                makeFile $filename
                $filename = "$dirname\unicode\$($Russian -join '')$fileitr"
                makeFile $filename
                $filename = "$dirname\unicode\$($Special -join '')$fileitr"
                makeFile $filename
                $fileitr += 1
               }
             }

             makeDirectory $DirName
             if ($CreateOnly -eq 'no')
              {
			   if ($Dirs -eq 0 -and $CustomFileName -eq '')
			    {
			     $FileName = "$DirName\file"
			     makeFile $FileName $Files
			    }
               elseif ($CustomFileName -ne '')
                {
                 createFilesWithCustomFileName $CustomFileName
                }
			   else
			    {
                 createRegularFiles $DirName
			     if ($ZeroSizeFile -eq "yes")
                  {
                  createSmallFiles $DirName
                  }
                }
              }
             if ($HLinks -eq "yes")
              {
               createHLinks $DirName
              }
             if ($SLinks -eq "yes")
              {
               createSLinks $DirName
              }
             if ($Sparse -eq "yes")
              {
               createSparseFiles $DirName
              }
             if ($Acls -eq "yes")
              {
               createACLFiles $DirName
              }
             if ($XAttr -eq "yes")
              {
               createXattrFiles $DirName
              }
             if ($Unicode -eq "yes")
              {
               createUnicodeFiles $DirName
              }
			 if ($AttributeFiles -ne "")
              {
               createAttributeFiles $DirName
              }
           } # END OF FUNCTION createAllFiles_2

          function createAllFiles_1()
           {
             # Queue object $Q will store list of directories.
             $Q  =  New-Object System.Collections.Queue

             # STEP 1 - Seed queue object $Q with first directory to create.
             $Q.Enqueue(@($DirName,1))

             # STEP 2 - Continue processing till queue object $Q is empty.
             while($Q.Count -gt 0)
              {

               # STEP 2.01 - Fetch item from queue object $Q and store current depth in variable $CurLev.
               $CurrentVar = $Q.Dequeue()
               $CurLev = $CurrentVar[1]

                # STEP 2.02 - Create files under the directory
               createAllFiles_2 $CurrentVar[0]

               # STEP 2.03 - If current depth is not the deepest level.
               if($CurLev+1 -le $Levels)
                {
                 # STEP 2.04 - Then as many items as number of directories $Dirs to queue object $Q and increment the item's current level/depth value by 1.
                 for($i=1;$i -le $Dirs;$i++)
                  {
                   $Q.Enqueue(@($($CurrentVar[0]+"\dir$i"),[int]$($CurrentVar[1]+1)))
                  }
                }
              }
            } # END OF FUNCTION createAllFiles_1
          createAllFiles_1
         }

       function UnzipProblemData([String]$Path,[String]$ZipFilePath)
         {
          $ProblematicDataPath = "$Path\ProblematicData"
          if ( -not ( Test-Path $ProblematicDataPath ) )
           {
            New-Item $ProblematicDataPath -ItemType Directory | Out-Null
           }
          $x = "x" # eXtract files with full paths
          $Dest = "-o$ExtrFilePath" # -o denotes output directory
          $overwrite = "-aoa" # Overwrite all existing files without prompt
          # STEP 1 - EXTRACT THE FILE
          # -------------------------
          Start-Process $ZipExePath -ArgumentList $x, $ZipFilePath, $Dest, $overwrite -Wait -NoNewWindow

          # STEP 2 - RUN setup.bat
          # ----------------------
          $SetupBatPath = "$ExtrFilePath\setup.bat"
          Start-Process $SetupBatPath -WorkingDirectory "$ExtrFilePath" -ArgumentList $ProblematicDataPath, "forcepath", $ExtrFilePath -Wait -ErrorAction Ignore
         }

        # STEP 3 - IMPERSONATE USER ACCOUNT IF SPECIFIED
        # ----------------------------------------------
        if ($Username -ne '' -and $Password -ne '')
         {
          NET USE "$ServerHostName" /U:$Username $Password
         }

        # STEP 4 - CREATE THE DATASET
        # ---------------------------
        function createDataset($Path,$Levels)
         {
		  if($Dirs -eq 0)
		   {
		    $DirName = $Path
		    Start-Job -ScriptBlock ${function:createAllFiles} -ArgumentList @($Path,$DirName,$Levels,$HLinks,$SLinks,$Sparse,$Acls,$XAttr,$ZeroSizeFile,$ASCIIDataFile,$Unicode,$Dirs,$Files,$SizeInKb,$HoleSizeInKb,$HoleOffset,$Chinese,$Japanese,$Arabic,$Special,$Russian,$CreateOnly,$AttributeFiles,$CustomFileName) | Out-Null
		   }
		  else
		   {
		    $DirItr = 1
            while ($DirItr -le $Dirs)
             {
              $DirName = "$Path\dir$DirItr"
              while ($(Get-Job -State Running).count -ge $ThreadCnt)
               {
                sleep -Seconds 5 # Check back every 5 seconds if we have less than 4 instances of jobs running. IF yes we will create more ELSE wait
               }
              Start-Job -ScriptBlock ${function:createAllFiles} -ArgumentList @($Path,$DirName,$Levels,$HLinks,$SLinks,$Sparse,$Acls,$XAttr,$ZeroSizeFile,$ASCIIDataFile,$Unicode,$Dirs,$Files,$SizeInKb,$HoleSizeInKb,$HoleOffset,$Chinese,$Japanese,$Arabic,$Special,$Russian,$CreateOnly,$AttributeFiles,$CustomFileName) | Out-Null
              $DirItr += 1
             }
           }
		  # Wait for all running jobs to finish
          Get-Job | Wait-Job | Receive-Job 
		 }

		createDataset $Path $Levels

        # CHECKING IF PROBLEMATIC DATA NEEDS TO BE CREATED
        if ($ZipFilePath -ne 'no')
         {
          UnzipProblemData $Path $ZipFilePath
         }
    }
