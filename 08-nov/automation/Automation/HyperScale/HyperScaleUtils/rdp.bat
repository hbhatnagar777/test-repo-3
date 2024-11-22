
@echo off

set ip=%1
set username=%2
set pass=%3
reg add "HKEY_CURRENT_USER\Software\Microsoft\Terminal Server Client" /v "AuthenticationLevelOverride" /t "REG_DWORD" /d 0 /f
cmdkey /generic:"%ip%" /user:"%username%" /pass:"%pass%"
mstsc /v:%ip% /admin