@echo off
SETLOCAL ENABLEEXTENSIONS

SET PYTHONEXE="%~dp0..\..\python\python.exe"

SET installScript= setup.py install
%PYTHONEXE%%installScript%
ENDLOCAL