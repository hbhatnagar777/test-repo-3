@echo off
>finalCleanup_output.txt (
del /Q /F C:\Windows\System32\Sysprep\sysprep.bat
wmic product where name="VMware Tools" call uninstall
)