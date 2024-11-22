# POWERSHELL SCRIPT TO MODIFY DATA
# USING ModifyData.bash AS REFERENCE

Function ModifyData()
    {
        $path         = "##Automation--path--##"
        $encrypt_file_with_aes ="##Automation--encrypt_file_with_aes--##"
        $rename       = "##Automation--rename--##"
        $modify       = "##Automation--modify--##"
        $acls         = "##Automation--acls--##"
        $xattr        = "##Automation--xattr--##"
        $permissions  = "##Automation--permissions--##"
        $slinks       = "##Automation--slinks--##"
        $hlinks       = "##Automation--hlinks--##"
        $TESTGROUP    = "cvgroup"
        $TESTUSER     = "cvusr"
        $ACLGROUP     = "cvgroup2"
        $ACLUSER      = "cvusr2"

        # Function to create user and group to set on the test data set
        function makeUserAndGroup()
         {
          NET LOCALGROUP $TESTGROUP /ADD
          NET LOCALGROUP $ACLGROUP /ADD
          NET USER $TESTUSER "######"/ADD
          NET USER $ACLUSER "######"/ADD
          NET LOCALGROUP $TESTGROUP $TESTUSER /ADD
          NET LOCALGROUP $ACLGROUP $ACLUSER /ADD
         }

        # Function to rename all the files in a given path
        # Already renamed files won't be renamed again
        function doRename([String]$path)
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName 
          foreach ($file in $ListOfFiles) 
           {
            if($file -notmatch "cvrenamed*")
             {
              Rename-Item $file $file".cvrenamed" -ErrorAction Ignore
             }
            }
          }  

        # Function to modify all the files in a given path by adding extra data
        function doModify([String]$path)
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName
          foreach ($file in $ListOfFiles) 
           {
            echo cvmodified >> $file 
           }
         }


        function doACLS([String]$path)
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName
          # Options for icacls do not always run easily under Powershell, hence we make use of Invoke-Expression
		  $Grant       = "/GRANT"
		  $UserAccount = $ACLUSER
		  $Permission  = ":R" # Grant Read Permission 
          foreach ($File in $ListOfFiles) 
           {
            Invoke-Expression -Command('icacls $File $Grant $UserAccount$Permission') # Granting $UserAccount $Permission on $File, modifying ACLS 
           }           
         }


         # THIS IS A COPY OF doModify() NEED TO IMPLEMENT IT CORRECTLY        
         function doXATTR([String]$path)
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName
          foreach ($File in $ListOfFiles) 
           {
            echo cvmodified >> $File 
           } 
         }


        function doPermissions([String]$path) # THIS IS A COPY OF doModify() NEED TO IMPLEMENT IT CORRECTLY
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName
          foreach ($file in $ListOfFiles) 
           {
            echo cvmodified >> $file 
           } 
         }

        # Function to modify all the files in a given path by adding Symbolic links
        function doSLINKS($path)
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName
          foreach($file in $ListOfFiles)
           {
            New-Item -Path $file".cvslink" -ItemType SymbolicLink -Value $file -ErrorAction Ignore | Out-Null
           }
         }

        # Function to modify all the files in a given path by adding Hard links
        function doHLINKS()
         {
          $ListOfFiles = (Get-ChildItem -File -Recurse $path).FullName
          foreach($file in $ListOfFiles)
           {
            New-Item -Path $file".cvhlink" -ItemType HardLink -Value $file -ErrorAction Ignore | Out-Null
           }
         }

         # Function to generate a random byte array of specified size
         function Get-RandomBytes()
         {
          param(
          [int]$size
          )

          $randomBytes = New-Object byte[] $size
          [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($randomBytes)
          return $randomBytes
          }

         # Function to encrypt an existing file using AES with a randomly generated key and IV
         function doEncryptFileWithAes()
         {
         param(
          [string]$path
          )

          try {
            # Generate random key and IV
            $keySize = 32  # 32 bytes for AES-256
            $ivSize = 16    # 16 bytes for AES

            $keyBytes = Get-RandomBytes -size $keySize
            $ivBytes = Get-RandomBytes -size $ivSize

            # Create AES provider with CBC mode and PKCS7 padding
            $aes = New-Object System.Security.Cryptography.AesCryptoServiceProvider
            $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
            $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7

            # Create encryptor using the key and IV
            $encryptor = $aes.CreateEncryptor($keyBytes, $ivBytes)

            # Open file for reading and writing (overwrite)
            $fileStream = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite)

            # Create CryptoStream to encrypt the file
            $cryptoStream = New-Object System.Security.Cryptography.CryptoStream($fileStream, $encryptor, [System.Security.Cryptography.CryptoStreamMode]::Write)

            # Encrypt the file in-place
            $bufferSize = 4096
            $buffer = New-Object byte[] $bufferSize
            $readBytes = 0
            do {
                $readBytes = $fileStream.Read($buffer, 0, $bufferSize)
                $cryptoStream.Write($buffer, 0, $readBytes)
            } while ($readBytes -ne 0)

            # Clean up resources
            $cryptoStream.Close()
            $fileStream.Close()
            $aes.Dispose()

            Write-Output "File encrypted successfully."
            }
            catch {
                Write-Error "Encryption failed: $_"
            }
            }


        if ($rename -eq "yes")
         {
          doRename $path
         }


        if ($modify -eq "yes")
         {
          doModify $path
         }

 
        if ($acls -eq "yes")
         {
          doACLS $path
         }

         if ($xattr -eq "yes")
         {
          doXATTR $path
         }

         if ($permissions -eq "yes")
         {
          doPermissions $path
         }

         if ($encrypt_file_with_aes -eq "yes")
         {
          doEncryptFileWithAes $path
         }

         if ($slinks -eq "yes")
         {
          doSLINKS $path
         }

         if ($hlinks -eq "yes")
         {
          doHLINKS $path
         }
    }








