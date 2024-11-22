# CVAutomationMask

This is a placeholder for adding new 3rd Party Python Packages to Automation Package

There are 3 files. Edit these according to your requirements:

1. ```packages/requirements.txt```: these are the common packages that will be installed on both Windows and Linux controllers
2. ```packages/requirements_win.txt```: these are the packages that are OS-specific for Windows controllers. Example: ```pywin32```
3. ```packages/requirements_lin.txt```: these are the packages that are OS-specific for Linux controllers. 

Only add packages that can install without any additional system-specific requirements. For example, on Linux, ```mariadb``` module requires
 ```mariadb_config``` to be pre-installed and will fail the install script on the machine but on Windows this can be installed without any 
 requirements. We can have this in the Windows file ```packages/requirements_win.txt``` since it cannot be part of common ```packages/requirements.txt```