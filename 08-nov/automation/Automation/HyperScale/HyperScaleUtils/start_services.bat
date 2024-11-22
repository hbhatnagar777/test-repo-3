start /wait /b sc start SQLAgent$COMMVAULT
start /wait /b sc config SQLAgent$COMMVAULT start=auto
timeout /t 15
start /wait /b sc start MSSQL$COMMVAULT
start /wait /b sc config MSSQL$COMMVAULT start=auto
timeout /t 15
start /wait /b sc start GxCVD(Instance001)
start /wait /b sc config GxCVD(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxClMgrS(Instance001)
start /wait /b sc config GxClMgrS(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxApM(Instance001)
start /wait /b sc config GxApM(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxBlr(Instance001)
start /wait /b sc config GxBlr(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxQSDK(Instance001)
start /wait /b sc config GxQSDK(Instance001) start=auto
timeout /t 5
start /wait /b sc start CVContentPreview(Instance001)
start /wait /b sc config CVContentPreview(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxJobMgr(Instance001)
start /wait /b sc config GxJobMgr(Instance001) start=auto
timeout /t 5
start /wait /b sc start GXMLM(Instance001)
start /wait /b sc config GXMLM(Instance001) start=auto
timeout /t 5
start /wait /b sc start GXMMM(Instance001)
start /wait /b sc config GXMMM(Instance001) start=auto
timeout /t 5
start /wait /b sc start CvMessageQueue(Instance001)
start /wait /b sc config CvMessageQueue(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxMONGO(Instance001)
start /wait /b sc config GxMONGO(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxFWD(Instance001)
start /wait /b sc config GxFWD(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxSearchServerInstance001
start /wait /b sc config GxSearchServerInstance001 start=auto
timeout /t 5
start /wait /b sc start GxEvMgrS(Instance001)
start /wait /b sc config GxEvMgrS(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxTomcatInstance001
start /wait /b sc config GxTomcatInstance001 start=auto
timeout /t 5
start /wait /b sc start GxVssHWProv(Instance001)
start /wait /b sc config GxVssHWProv(Instance001) start=auto
timeout /t 5
start /wait /b sc start GxVssProv(Instance001)
start /wait /b sc config GxVssProv(Instance001) start=auto
timeout /t 5
start /wait /b sc start cloudbase-init
start /wait /b sc config cloudbase-init start=delayed-auto

timeout /t 600
"c:\Program Files\Commvault\ContentStore\Base\gxadmin.exe" -consoleMode -setsvcstartmode Automatic || "e:\Program Files\Commvault\ContentStore\Base\gxadmin.exe" -consoleMode -setsvcstartmode Automatic

"C:\Program Files\Commvault\ContentStore\Base\GxAdmin.exe" -consoleMode -startsvcgrp All || "E:\Program Files\Commvault\ContentStore\Base\GxAdmin.exe" -consoleMode -startsvcgrp All