@echo off
start /wait /b sc start cloudbase-init
start /wait /b sc config cloudbase-init start=delayed-auto

for /F "usebackq tokens=1,2 delims==" %%i in (`wmic os get LocalDateTime /VALUE 2^>NUL`) do if '.%%i.'=='.LocalDateTime.' set ldt=%%j
set ldt=%ldt:~0,4%-%ldt:~4,2%-%ldt:~6,2% %ldt:~8,2%:%ldt:~10,2%:%ldt:~12,6%

cd "C:\Windows\System32\Sysprep"
echo Local date is [%ldt%] >> timeAndSid.txt
PsGetsid.exe /accepteula >> timeAndSid.txt 2>nul

rmdir "C:\temp" /q /s
del /S /F /Q %temp%
NetSh Advfirewall set privateprofile state on
NetSh Advfirewall set publicprofile state on
NetSh Advfirewall set domainprofile state off
Netsh advfirewall firewall add rule name=custom_cvlt_private profile=private dir=in action=allow enable=yes protocol=tcp localport=80,81,443
Netsh advfirewall firewall add rule name=custom_cvlt_public profile=public dir=in action=allow enable=yes protocol=tcp localport=80,81,443
netsh advfirewall firewall add rule name="ICMP Allow incoming V4 echo request" protocol=icmpv4:8,any dir=in action=allow
netsh advfirewall firewall add rule name="ICMP Allow incoming V6 echo request" protocol=icmpv6:8,any dir=in action=allow
del /Q /F C:\Windows\System32\Sysprep\uninstall_vmwaretools.ps1
del /Q /F C:\Windows\System32\Sysprep\uninstall_vmtools.bat
del /Q /F C:\Windows\System32\Sysprep\PsGetsid.exe
echo Sysprep is working...
cd "C:\Windows\System32\Sysprep"

sysprep.exe /oobe /generalize /shutdown /quiet /unattend:ForSysprep.xml

del /Q /F C:\Windows\System32\Sysprep\ForSysprep.xml

(goto) 2>nul & del "%~f0"