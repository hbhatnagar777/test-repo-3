Function GenerateTestData() {
    $TestDataPath = "##Automation--path--##"
    $Level = ##Automation--level--##
    $Size = ##Automation--size--##

	function CreateRandomFile($FolderPath, $Size) {

		Try {
			$Extensions = ".avi", ".midi", ".mov", ".mp3", ".mp4", ".mpeg", ".mpeg2", ".jpeg", ".pptx",
					   ".docx", ".doc", ".xls", ".pdf", ".ppt", ".dot", ".dll", ".exe", ".bat", ".msi",
					   ".txt", ".xml", ".ini", ".rt"

			# Get Random extension from list of extensions
			$Extension = $Extensions | Get-Random

			# Get some random verb to use as file name
			$Name = (Get-Verb | Select-Object verb | Get-Random -Count 1).verb

			$FileName = $Name + $Extension

			# Get some random Text to write in file
			$word = ''
			for ($i =0; $i -lt 4; $i++) {
			   $word += (-join ((0..256) | Get-Random -Count 256 | ForEach-Object {[char]$_})) + "`r`n"
			}

			$FileSize = 0
			$FilePath = $FolderPath + "\" + $FileName

			if (Test-Path $FilePath) {
				return CreateRandomFile $FolderPath $Size
			}

			# Write content to file recursively till it satisfies the size limit
			While ($FileSize -le $Size) {
				# Add Content to this file
				$word | Add-Content $FilePath

				$FileSize = Get-Item $FilePath
				$FileSize = [Math]::Round($FileSize.Length/1KB, 0)
			}
		}
		Catch {
            Unblock-File -Path $FilePath
		}

	}

	if ([System.IO.File]::Exists($TestDataPath)){
        throw [System.IO.DirectoryNotFoundException] "$TestDataPath is not a Directory."
    }

	New-Item -Path $TestDataPath -ItemType Directory -Force | Out-Null

    # Create 1 KB File
    CreateRandomFile $TestDataPath 0

    # Create 2 KB File
    CreateRandomFile $TestDataPath 1

    $FolderSize = [Math]::Round($Size/$Level, 0)

    $FilesCount = 8

    # Generate 8 random files
    for ($i = 1; $i -le $FilesCount; $i++) {

        if ($i -eq $FilesCount) {
            $FileSize = $FolderSize
        }
        else {
            $FileSize = (Get-Random -Maximum $FolderSize -Minimum 0)
        }

        CreateRandomFile $TestDataPath $FileSize

        $FolderSize = $FolderSize - $FileSize

    }

    # Get list of files to be copied
    $FilesToCopy = Get-ChildItem $TestDataPath -File

    # Copy Test Data folder upto $Level depth
    for ($i=2; $i -le $Level; $i++) {

            $TestDataPath = $TestDataPath + "\TestData" + $i

            New-Item -Path $TestDataPath -ItemType Directory -Force | Out-Null

            foreach ($File in $FilesToCopy) {
                Copy-Item -Path $File.FullName -Destination $TestDataPath -Force
            }

    }
}