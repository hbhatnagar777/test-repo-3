cd "C:\temp\DownloadPackageLocation\WinX64"
>install_output.txt (
start /wait Setup.exe /silent /play install.xml /decoupledfailoverinstance
)
exit /b 0