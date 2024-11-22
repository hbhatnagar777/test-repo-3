SETLOCAL ENABLEEXTENSIONS

SET PYTHONEXE="%~dp0..\python\python.exe"

cd PythonSDK
rmdir /S /Q build
rmdir /S /Q dist
rmdir /S /Q cvpysdk.egg-info
SET installScript= setup_cvinstaller.py install
%PYTHONEXE%%installScript%
cd ..
ENDLOCAL 