
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
import time
import shutil
import os
import win32wnet
import threading
import subprocess
from HyperScale.HyperScaleUtils import esxManagement
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.database_helper import DBResponse
import winreg
from AutomationUtils.config import get_config

class TestCase(CVTestCase):

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "TEST_CASE_NAME"
        self.config = get_config()
        self.show_to_user = True
        self.esx_object = None
        self.machine_obj = None
        self.status = constants.PASSED
        self.result_string = constants.NO_REASON
        self.automation_dir = os.getcwd()
        self.machine_obj = None
        self.small_timeout = 600
        self.medium_timeout = 6000
        self.sp_level = ''
        self.version_level = '11'
        self.large_timeout = 12000
        self.dynamic_install = False
        self.error_count = 0
        self.xlarge_timeout = 28800
        self.hyperscale_utils_path = self.automation_dir + "\\HyperScale\\HyperScaleUtils"
        self.hyperscale_preova_path = self.automation_dir + \
                                      "\\HyperScale\\HyperScaleUtils\\pre_ova_generation"
        self.hyperscale_binaries_path= None
        self.remote_utils_location = None
        self.remote_custom_package_location = None
        self.remote_local_utils_location = None
        self.remote_local_custom_package_path = None
        self.remote_sysprep_path = None
        self.remote_local_sysprep_path = "C:\\Windows\\System32\\Sysprep"
        self.remote_driver_path1 = None
        self.remote_local_driver_path = None
        self.remote_local_scripts_path = None
        self.remote_local_base_path = None
        self.md5_checksum_file = "c:\\temp\\md5.txt"
        self.remote_base_path = None
        self.remote_system32_path = None
        self.remote_local_system32_path = "C:\\Windows\\System32"
        self.created_ova_path = "C:\\temp\\cvhcics.ova"
        self.vm_tools_states = ['toolsNotInstalled','toolsNotRunning','toolsOk','toolsOld']
        self.cs_bootstrap_path =''
        self.tcinputs = {
            "run_export_ova": None,
            "snapshot_name": None,
            "manage_via_snapshots": None,
            "run_deploy": None,
            "prepare_ova": None,
            "install_win_updates": None,
            "export_updated_snapshot": None,
            "run_configure": None,
            "partition_count": None,
            "clientMachineHostname": None,
            "clientMachineUser": None,
            "clientMachinePassword": None,
            "sp_value": None,
            "mount_username": None,
            "mount_password": None,
            "customPackageCreation_URL": None,
            "customPackageLocation": None,
            "cs_bootstrap_path": None,
            "esxHostIP": None,
            "esxHostUser": None,
            "esxHostPassword": None,
            "esxDatacenterName": None,
            "esxDataStorename": None,
            "vm_name": None,
            "vm_vmdkPath": None,
            "vm_ovfPath": None,
            "run_delete_vm": None,
            "final_machine_name": None,
            "final_loc_path": None,
            "final_loc_user": None,
            "final_loc_pass": None,
            "hyperscale_version": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.esx_object = esxManagement.EsxManagement(self.tcinputs["esxHostIP"],
                                                      self.tcinputs["esxHostUser"],
                                                      self.tcinputs["esxHostPassword"])

    def reinitialize_esx(self):
        """
        This method is to just re-initialize the object for esx server.
        Seems like when performing time consuming operations,
        the object times out in the backend and needs to be reinitialized
        :return:
        """
        self.setup()

    def reinitialize_machine_object(self):
        """
        This method is to just re-initialize the object for remote machine.
        Seems like when performing time consuming operations,
        the object times out in the backend and needs to be reinitialized
        :return:
        """

        self.machine_obj = Machine(machine_name=self.tcinputs["clientMachineHostname"],
                                   username=self.tcinputs["clientMachineUser"],
                                   password=self.tcinputs["clientMachinePassword"])

    def generate_paths(self):
        """
        This method basically generates all the destination paths where all the files
        need to be copied for the CS install and post install processes

        :return: nothing
        """
        self.log.info('Generating paths')
        self.remote_utils_location = "\\\\" + self.tcinputs["clientMachineHostname"] + "\\c$\\temp\\utils"
        self.remote_local_utils_location = "C:\\temp\\utils"
        self.remote_custom_package_location = "\\\\" + self.tcinputs["clientMachineHostname"] + "\\c$\\temp\\"
        self.remote_local_custom_package_path = "C:\\temp\\"
        self.remote_sysprep_path = "\\\\" + self.tcinputs["clientMachineHostname"] + "\\c$\\Windows\\System32\\Sysprep"
        self.remote_system32_path = "\\\\" + self.tcinputs["clientMachineHostname"] + "\\c$\\Windows\\System32"
        self.remote_local_driver_path = "C:\\ApplianceInstall\\Driver\\Scripts"
        self.remote_driver_path1 = "\\\\" + self.tcinputs["clientMachineHostname"] + \
                                   "\\c$\\ApplianceInstall\\Driver\\Scripts"

        if int(self.tcinputs["partition_count"]) == 1:
            self.remote_base_path = "\\\\" + self.tcinputs["clientMachineHostname"] + \
                "\\c$\\Program Files\\Commvault\\ContentStore\\Base"
            self.remote_local_base_path = "C:\\Program Files\\Commvault\\ContentStore\\Base"
            self.remote_local_scripts_path = "C:\\Program Files\\Commvault\\ContentStore\\Scripts"
        else:
            self.remote_base_path = "\\\\" + self.tcinputs["clientMachineHostname"] + \
                "\\e$\\Program Files\\Commvault\\ContentStore\\Base"
            self.remote_local_base_path = "E:\\Program Files\\Commvault\\ContentStore\\Base"
            self.remote_local_scripts_path = "E:\\Program Files\\Commvault\\ContentStore\\Scripts"

    def create_batch_files(self):
        """
        This is a wip method
        :return: nothing
        """
        install_windows_updates_cmd = r"powershell PS_WinUpdate > C:\temp\utils\op.log"
        install_win_updates_director_cmd = r"START /wait install_windows_update.bat"
        mount_disk_cmd1 = r"net use * /D /Y "
        mount_disk_cmd1 = \
            r'net use X: "\\%s\" ' \
            r'%s /USER:%s' % (self.config.Hyperscale.engweb_path,
                              self.tcinputs["mount_password"], self.tcinputs["mount_username"])
        return

    def manage_cv_services(self,operation = 'start'):
        """
        Method to manage CV services using gxadmin.
        :param operation: Start | Stop | Restart
        :return: returns error sting if error encountered
        """
        control_map = {'start': 'startsvcgrp', 'stop': 'stopsvcgrp', 'restart': 'restartsvcgrp'}
        self.log.info('Will now %s Commvault Services' %operation)
        if int(self.tcinputs["partition_count"]) == 1:
            drive_letter = r'C:'
        else:
            drive_letter = r'E:'
        svc_cmd = '"'+drive_letter + r'\Program Files\Commvault\ContentStore\Base\GxAdmin.exe" -consoleMode -' + \
            control_map[operation]+' All'
        ps_svc_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + \
                    ' -u ' + self.tcinputs["clientMachineUser"] + \
                    ' -p ' + self.tcinputs["clientMachinePassword"] + \
                    ' ' + svc_cmd + ' -accepteula'
        op = self.run_clean_subprocess(ps_svc_cmd, self.xlarge_timeout)
        self.log.info(op)
        if "Successfully" in str(op):
            self.log.info('Service %s operation successful')
        else:
            self.log.error('Could not perform operation on cv services.')
            raise op

    def manage_services(self, operation='start'):
        """
        Method to manage CV services via machine object and sc command
        :param operation: Start | Stop | Restart
        :return:
        """
        service_list = ["SQLAgent$COMMVAULT", "MSSQL$COMMVAULT", "SQLBrowser","GxCVD(Instance001)",
                        "GxClMgrS(Instance001)", "GxApM(Instance001)", "GxBlr(Instance001)",
                        "GxQSDK(Instance001)", "CVContentPreview(Instance001)",
                        "GxJobMgr(Instance001)", "GXMLM(Instance001)", "GXMMM(Instance001)",
                        "CvMessageQueue(Instance001)", "GxMONGO(Instance001)",
                        "GxFWD(Instance001)", "GxSearchServerInstance001", "GxEvMgrS(Instance001)",
                        "GxTomcatInstance001", "GxVssHWProv(Instance001)",
                        "GxVssProv(Instance001)", "CVJavaWorkflow(Instance001)"]
        ret_value = True
        for service_name in service_list:
            try:
                cmd = "sc %s %s" % (operation, service_name)
                self.log.info('Attempting to start %s service' % service_name)
                op = self.machine_obj.execute_command(cmd)
                self.log.info(op.output)
                if operation == 'query':
                    if 'running' in str(op.output).lower():
                        self.log.info('Service %s running ' % service_name)
                    else:
                        self.log.warning('Service %s NOT running ' % service_name)
                        ret_value = False
                time.sleep(5)
            except Exception as err:
                self.log.error(str(err))
        return ret_value

    def open_connection(self, retry=True):
        """
        This method will be moved to a different file.
        I am keeping it here since we have yet to create a utils for hyperscale.
        This will open a windows connection to the remote machine
        so that packages can be transferred.

        Note:
        Common methods in the Machine class are not working.
        I tried several of the methods of the class and none of them seem to be working.
        Will use them once those are in working state

        :return: Either just returns or raises exception. NO return value as such
        """
        try:
            win32wnet.WNetAddConnection2(0, None, r'\\' + self.tcinputs["clientMachineHostname"],
                                         None, self.tcinputs["clientMachineUser"],
                                         self.tcinputs["clientMachinePassword"])
            return
        except Exception as err:
            self.log.info(str(err))
            self.log.error('Hostname %s. Username %s, pass %s'
                           % (self.tcinputs["clientMachineHostname"],
                              self.tcinputs["clientMachineUser"],
                              self.tcinputs["clientMachinePassword"]))

            if '64' in str(err) and retry:
                time.sleep(5)
                self.log.warning('Open Connection failed. Will now retry one more time')
                self.open_connection(False)
            else:
                raise Exception

    def modify_reg_key(self, key, sub_key, value, key_type):
        """
        This method is used to add needed registry keys on the deployed windowns VM before
        the CS can be installed
        Cannot use machine object method since it only writes under Commvault/galaxy
        :param key: registry key name
        :param sub_key: subkey name
        :param value: value of  the sub key
        :param key_type: type of the key

        :return: True if successful | False if failed
        """

        try:
            rr = winreg.ConnectRegistry(self.tcinputs["clientMachineHostname"], winreg.HKEY_LOCAL_MACHINE)
            try:
                hKey = winreg.OpenKey(rr, key, 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_ALL_ACCESS))
            except FileNotFoundError:
                winreg.CreateKey(rr, "SOFTWARE\CommVault Systems\Galaxy\Installer\Data")
                hKey = winreg.OpenKey(rr, key, 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_ALL_ACCESS))
            try:
                if key_type == 'dword':
                    winreg.SetValueEx(hKey, sub_key, 0, winreg.REG_DWORD, value)
                elif key_type == 'string':
                    winreg.SetValueEx(hKey, sub_key, 0, winreg.REG_SZ, value)
                self.log.info('Reg key value modified-- cs,key:' + self.tcinputs["clientMachineHostname"]
                                  + ',' + sub_key + ' to:' + str(value))
            except:
                if key_type == 'dword':
                    winreg.CreateKey(key, sub_key)
                    winreg.SetValueEx(hKey, sub_key, 0, winreg.REG_DWORD, value)
                elif key_type == 'string':
                    winreg.CreateKey(key, sub_key)
                    winreg.SetValueEx(hKey, sub_key, 0, winreg.REG_SZ, value)
                self.log.info('Reg key value not found. Created new -- cs,key:' +
                              self.tcinputs["clientMachineHostname"] + ',' + sub_key + ' to:' + str(value))
            return True
        except WindowsError as e:
            self.log.error(e)
            self.error_count += 1
            return False

    def read_reg_value(self, key, sub_key):
        """
        Custom method to read reg value of remote machine.
        Cannot use machine object method since it only reads under Commvault/galaxy
        :param key: (str) Key path
        :param sub_key: (str) sub key name
        :return: returns the value of the subkey
        """
        try:
            rr = winreg.ConnectRegistry(self.tcinputs["clientMachineHostname"], winreg.HKEY_LOCAL_MACHINE)
            hKey = winreg.OpenKey(rr, key, 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_ALL_ACCESS))
            try:
                return winreg.QueryValueEx(hKey, sub_key)[0]
            except:
                self.log.info('Reg key value not found.')
                return ''

        except WindowsError as e:
            self.log.error(e)
            return ''

    def commit_cache(self):
        """
        Does a commit cache on the remote CS machine
        uses machine obj
        :return: Nothing
        """
        commit_location = self.remote_local_base_path + "\\SetupCacheCmdLine.exe"
        commit_cmd = 'cmd.exe /k "'+commit_location + r'" /instance Instance001 /copytype sync'
        self.log.info('Commiting cache now')
        self.log.info(commit_cmd)
        commit_op = self.machine_obj.execute_command(commit_cmd)
        self.log.info(commit_op.output)
        if "Failed to commit the cache" in commit_op.output:
            raise Exception
        if commit_op.exception not in (None, '', ' '):
            self.log.info(commit_op.exception)
            self.log.info(commit_op.exception_message)
            raise commit_op.exception

    def transfer_files(self):
        """
        This will transfer the necessary packages to the remote machine for
        custom package installation. I am using shutil for the transfer

        Note:
        Common methods in the Machine class are not working.
        I tried several of the methods of the class and none of them seem to be working.
        Will use them once those are in working state
        :return: Nothing.
        """

        self.open_connection()
        '''
        WIP - This did not work when it was first implemented. This needs to be debugged fursther. 
        workaround already implemented
        
        machine_obj = Machine(machine_name=self.tcinputs["clientMachineHostname"],
                              commcell_object=None, username=self.tcinputs["clientMachineUser"],
                              password=self.tcinputs["clientMachinePassword"])
        machine_obj.create_registry("HKEY_LOCAL_MACHINE\SOFTWARE\CommVault Systems\Galaxy\Installer\Data",
                                    "szFTPCacheDir", "c:\ApplianceInstall\ContentStore")
        '''
        self.modify_reg_key("SOFTWARE\CommVault Systems\Galaxy\GalaxyInstaller\Data",
                            "szFTPCacheDir", "c:\ApplianceInstall\ContentStore", "string")

        # copying the batch files needed for unzip and install
        if os.path.exists(self.remote_custom_package_location):
            shutil.rmtree(self.remote_custom_package_location)

        os.makedirs(self.remote_utils_location, exist_ok=True)
        self.log.info('Successfully created remote directory %s' % self.remote_utils_location)

        os.makedirs(self.remote_custom_package_location, exist_ok=True)
        self.log.info('Successfully created remote directory %s' % self.remote_custom_package_location)

        ignore_patterns = shutil.ignore_patterns('CVS*', '*cache*', '*.py')
        if (self.cs_bootstrap_path not in ('', None, 'None')) and ("\\" not in self.cs_bootstrap_path):
            self.clean_copy2(self.hyperscale_utils_path,
                             self.remote_local_utils_location, self.cs_bootstrap_path)

        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'installPackage.bat')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'installPackageHS2.bat')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'postDeploy.bat')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'preExport.bat')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'install.xml')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, '450install.xml')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, '450installHS2.xml')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'install4.xml')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'mount_disk.bat')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'mount.exe')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'start_services.bat')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'HyperScale-HardwareAlerts.xml')
        
        self.log.info('Utilities copied')

        time.sleep(5)
        if self.tcinputs["customPackageLocation"] == '':
            self.dynamic_install = True
        else:
            # copying the custom package
            self.log.info('Will now copy custom package to the target location: <%s>'
                          % self.remote_custom_package_location)
            self.log.info('This might take a while depending on the network speed/transfer size')
            package_location = self.tcinputs["customPackageLocation"].split("\\")
            file_name = str(package_location[-1])
            package_path = self.tcinputs["customPackageLocation"].rstrip("\\"+file_name)
            self.log.info('Location of custom package: %s. Custom PAckage file name: %s' % (package_path, file_name))
            self.clean_copy2(package_path,
                             self.remote_local_custom_package_path, file_name)
            self.log.info('Custom package copied')
        time.sleep(5)
        return

    def clean_copy(self, source, destination, file_name):
        """
        method to delete file on remote machine before copying it
        Uses python os abd shutil module
        :param source: (str) Source path
        :param destination: (str) Destination path
        :param file_name: (str) File name
        :return: Nothing
        """
        try:
            if os.path.exists(destination + "\\"+file_name):
                try:
                    os.remove(destination + "\\"+file_name)
                    self.log.info('Successfully removed file %s from location %s' % (file_name, destination))
                except Exception as err:
                    #self.machine_obj.delete_file()
                    self.log.warning('Unable to remove file %s from location %s' % (file_name, destination))
                    self.log.warning(str(err))
            shutil.copy(source+"\\"+file_name, destination)
            self.log.info('Successfully copied file %s to location %s' % (file_name, destination))
        except Exception as err:
            self.log.warning(str(err))
            self.log.error('Unable to copy file %s to location %s' % (file_name, destination))
            raise err

    def clean_copy2(self, source, destination, file_name):
        """
        method to delete file on remote machine before copying it
        Uses machine object
        :param source: (str) Source path
        :param destination: (str) Destination path
        :param file_name: (str) File name
        :return: Nothing
        """
        try:
            if os.path.exists(destination + "\\"+file_name):
                try:
                    self.machine_obj.delete_file(destination + "\\"+file_name)
                    self.log.info('Successfully removed file %s from location %s' % (file_name, destination))
                except Exception as err:
                    self.log.warning('Unable to remove file %s from location %s' % (file_name, destination))
                    self.log.warning(str(err))
            try:
                self.machine_obj.copy_from_local(source+"\\"+file_name, destination)
            except Exception as err:
                self.log.info('Could not copy via machine object. Will retry via shutil')
                self.log.warning(str(err))
                raise Exception
                # shutil.copy(source + "\\" + file_name, destination)
            self.log.info('Successfully copied file %s to location %s' % (file_name, destination))
        except Exception as err:
            self.log.warning(str(err))
            self.log.error('Unable to copy file %s to location %s' % (file_name, destination))
            raise err

    def configure_machine(self):
        """
        This methods basically invokes the transferred batch files to
        1. Disable firewall, Windows defender
        2. Unzip the custom package transferred
        3. Install the CS package silently

        :return:
        """
        self.open_connection()
        time.sleep(15)

        if not self.dynamic_install:
            cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + \
                  r' -u ' + self.tcinputs["clientMachineUser"] + \
                  ' -p ' + self.tcinputs["clientMachinePassword"] + \
                  ' ' + self.remote_local_utils_location+'\\postDeploy.bat -accepteula'
            # above command was used whe npsexec was used. it was later removed
            # and machine object was used and it worked. Keeping the cmd value for any future workaround
            self.log.info('Wil now unzip the custom package')
            unzip_op = self.machine_obj.execute_command(self.remote_local_utils_location + '\\postDeploy.bat')
            self.log.info(unzip_op.output, unzip_op.exception)
            time.sleep(30)
            self.log.info('Unzipped Custom Package')
            self.reinitialize_esx()

            # Install Custom package
            self.log.info('Will now install the Custom package')
            start_install_time = time.time()
            install_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + ' -u ' \
                          + self.tcinputs["clientMachineUser"] + ' -p ' \
                          + self.tcinputs["clientMachinePassword"] + ' ' \
                          + self.remote_local_utils_location + '\\installPackage.bat -accepteula'
            if '1.' in self.tcinputs["hyperscale_version"]:
                install_op = self.machine_obj.execute_command(self.remote_local_utils_location + '\\installPackage.bat')
            elif '2.' in self.tcinputs["hyperscale_version"]:
                install_op = self.machine_obj.execute_command(self.remote_local_utils_location + '\\installPackageHS2.bat')
            else:
                self.log.error('Hyperscale version not provided in input file. Exiting')
                raise Exception
            self.log.info(install_op.output, install_op.exception)
            end_install_time = time.time()
        else:
            start_install_time = time.time()
            if int(self.tcinputs["partition_count"]) == 1:
                self.log.info('Installing single partition')
                install_file = "C:\\temp\\utils\\450install.xml"
            else:
                self.log.info('Installing 4 partition')
                install_file = "C:\\temp\\utils\\install4.xml"
            self.install_cs_package(self.tcinputs["sp_value"], install_file)
            end_install_time = time.time()

        self.log.info('CS package installed in %d minutes '
                      % (int(end_install_time - start_install_time) / 60))
        self.reinitialize_esx()
        self.reinitialize_machine_object()
        self.open_connection()
        self.modify_reg_key("SOFTWARE\CommVault Systems\Galaxy\Installer\Data",
                            "szFTPCacheDir", "c:\ApplianceInstall\ContentStore", "string")
        try:
            if self.read_reg_value(r"SOFTWARE\CommVault Systems\Galaxy\Instance001\Base",
                                "sVERSION") == '':
                self.log.error('CS not installed correctly')
                raise Exception
            self.log.info('Verified CS install via reg')
        except Exception as err:
            self.log.error(str(err))
            self.log.error('Unable to find install. exiting now')
            raise err

        #Create target directories
        os.makedirs(self.remote_driver_path1, exist_ok=True)

        # copying the driver
        self.clean_copy2(self.hyperscale_preova_path+"\\"+self.tcinputs["sp_value"],
                         self.remote_local_driver_path, 'EvalLicSeal.exe')
        self.clean_copy2(self.hyperscale_preova_path+"\\"+self.tcinputs["sp_value"],
                         self.remote_local_driver_path, 'EvalLicUnSeal.exe')
        self.clean_copy2(self.hyperscale_preova_path, self.remote_local_driver_path,
                         'UpdateCSGUID.sqle')

        self.clean_copy2(self.hyperscale_preova_path, self.remote_local_scripts_path,
                         'UpdateCSGUID.sqle')

        self.clean_copy2(self.hyperscale_preova_path+"\\"+self.tcinputs["sp_value"],
                         self.remote_local_base_path, 'EvalLicSeal.exe')
        self.clean_copy2(self.hyperscale_preova_path+"\\"+self.tcinputs["sp_value"],
                         self.remote_local_base_path, 'EvalLicUnSeal.exe')
        self.clean_copy2(self.hyperscale_preova_path, self.remote_local_base_path,
                         'UpdateCSGUID.sqle')
        self.clean_copy2(self.hyperscale_utils_path, self.remote_local_utils_location,
                         'temp_db_query.sql')

        self.log.info('Successfully copied driver data to %s and %s'
                      % (self.remote_driver_path1, self.remote_base_path))
        self.manage_services()
        self.machine_obj.execute_command(self.remote_local_utils_location + '\\start_services.bat')
        time.sleep(600)
        self.commit_cache()
        time.sleep(5)

        if int(self.tcinputs["partition_count"]) == 4:
            self.clean_copy2(self.hyperscale_utils_path, self.remote_local_utils_location,
                             'temp_db_query.sql')
            self.run_db_maintenance()
            time.sleep(10)
            self.run_tempdb_query()
            time.sleep(10)
            self.manage_cv_services('start')
            time.sleep(10)


    def seal_license(self):
        """
        This method seals the license on the CS
        :return: nothing
        """
        self.log.info('Sealing the license')
        eval_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + \
                   ' -u ' + self.tcinputs["clientMachineUser"] + \
                   ' -p ' + self.tcinputs["clientMachinePassword"] + \
                   ' "' + self.remote_local_base_path + '\\EvalLicSeal.exe" -accepteula'
        try:
            op = self.run_clean_subprocess(eval_cmd, self.medium_timeout)
            self.log.info(op)
            if "completed successfully" in str(op):
                self.log.info('Sealing license successful')
            else:
                self.log.error('Could not seal license. will try using machine class')
                raise op
        except Exception as err:
            self.log.error(str(err))
            raise Exception

    def install_cert(self):
        """
        This method installs the redhat drivers.
        :return: Error string if install fails
        """
        self.log.info('Installing cert')
        try:
            pub = r'cmd.exe /c certutil.exe -addstore "trustedPublisher" C:\ApplianceInstall\Driver\RedHat.cer'
            pub_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + \
                       ' -u ' + self.tcinputs["clientMachineUser"] + \
                       ' -p ' + self.tcinputs["clientMachinePassword"] + \
                       ' '+pub+' -accepteula'
            op = self.run_clean_subprocess(pub_cmd, self.medium_timeout)
            self.log.info(op)
            if "CertUtil: -addstore command completed successfully." in str(op):
                self.log.info('Cert installed successful')
            else:
                self.log.error('Could not install cert. ')
                raise op
            self.log.info(op)
        except Exception as err:
            self.log.error('Unable to install certificate')
            self.log.error(str(err))

    def install_network_driver(self):
        """
        This method installs redhat network driver
        :return: Error string if install fails
        """
        self.log.info('Installing redhat driver')
        try:
            netw = r'cmd.exe /c pnputil.exe -i -a C:\ApplianceInstall\Driver\amd64\netkvm.inf'
            netw_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + \
                      ' -u ' + self.tcinputs["clientMachineUser"] + \
                      ' -p ' + self.tcinputs["clientMachinePassword"] + \
                      ' ' + netw + ' -accepteula'
            op = self.run_clean_subprocess(netw_cmd, self.medium_timeout)
            self.log.info(op)
            if "Driver package added successfully." in str(op):
                self.log.info('redhat driver installed successful')
            else:
                self.log.error('Could not install redhat drivers.')
                raise op
            self.log.info(op)
        except Exception as err:
            self.log.error('Unable to install network driver')
            self.log.error(str(err))

    def run_db_maintenance(self):
        """
        This method is used to run DB maintainance on the CS
        :return: error string if it fails
        """
        try:
            self.manage_cv_services('stop')
            db_cmd = r'DBMaintenance.exe -startwiatracer -wiatracercfg 1000 –wiarefresh'
            ps_db_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + \
                      ' -u ' + self.tcinputs["clientMachineUser"] + \
                      ' -p ' + self.tcinputs["clientMachinePassword"] + \
                      ' ' + db_cmd + ' -accepteula'
            op = self.run_clean_subprocess(ps_db_cmd, self.xlarge_timeout)
            self.log.info(op)
            if op == b'\r\n' or "Database Maintenance complete" in str(op):
                self.log.info('DB maintenance successful')
            else:
                self.log.error('Could not run db maintenance.')
                raise op
            self.log.info(op)
        except Exception as err:
            self.log.error('Unable to run db maintenance')
            self.log.error(str(err))

    def run_tempdb_query(self):
        """
        This method changes the temp DB location for HS3300 configurations
        :return: nothing
        """
        remote_hostname = str(self.machine_obj.execute_command('hostname').output).strip()
        sql_cmd = r"sqlcmd -E -S %s\Commvault -i C:\temp\utils\temp_db_query.sql" % remote_hostname

        sql_batch = open(r'C:\temp\utils\run_temp_cmd.bat', 'w')
        sql_batch.write('echo off \n')
        sql_batch.write('mkdir G:\TempDB \n')
        sql_batch.write(sql_cmd + '\n')
        sql_batch.close()
        self.clean_copy2("C:\\temp\\utils", "C:\\temp\\utils", "run_temp_cmd.bat")
        time.sleep(10)
        bat_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + ' -u ' \
                      + self.tcinputs["clientMachineUser"] + ' -p ' \
                      + self.tcinputs["clientMachinePassword"] + \
                      ' "C:\\temp\\utils\\run_temp_cmd.bat" -accepteula'
        tempdb_bat_res = self.run_clean_subprocess(bat_cmd, timeout=self.xlarge_timeout)
        self.log.info(tempdb_bat_res)
        self.log.info('done running tempdb query')

    def rdp(self):
        """
        This method basically will be moved to a common utils or replaced by any existing util.
        As of now it is a batch file. Will be converted to a threaded function.

        What it does is basically initiates an RDP connection using the hostname,user and password.
        This is needed for a brand new machine or a rebooted because it needs a login in order
        to start a few windows services which are needed by the test
        :return:
        """

        try:
            subprocess.check_output(r'%s %s %s %s ' % (self.hyperscale_utils_path+"\\rdp.bat",
                                                       self.tcinputs["clientMachineHostname"],
                                                       self.tcinputs["clientMachineUser"],
                                                       self.tcinputs["clientMachinePassword"]))

            return
        except Exception as err:
            self.log.error(str(err))
            self.log.info('rdp batch file path: %s' % str(self.hyperscale_utils_path+"\\rdp.bat"))
            raise Exception

    def run_clean_subprocess(self, command, timeout, call=False, retry=True):
        """
        cleans up psexec on remote machine and runs the new command
        :param command: command to run
        :param timeout: timeout for command
        :param call: call when true makes subprocess.call else names check_output
        :return:
        """
        self.open_connection()
        retry_count = 1
        try:
            kill_psexesvc_cmd = 'pskill \\\\' + self.tcinputs["clientMachineHostname"] + ' -u ' \
                                + self.tcinputs["clientMachineUser"] + ' -p ' \
                                + self.tcinputs["clientMachinePassword"] + ' PSEXESVC.exe'
            if str(subprocess.call(kill_psexesvc_cmd)) == '4294967295':
                subprocess.call(kill_psexesvc_cmd)
            self.machine_obj.execute_command(r"taskkill /IM PSEXESVC.exe /F")
            time.sleep(5)
        except Exception as err:
            self.log.error('Unable to kill psexesvc on remote machine')
            self.log.error(str(err))
        if retry:
            retry_count = 2
        while retry_count > 0:
            try:
                if call:
                    return subprocess.call(command, timeout=timeout)
                else:
                    return subprocess.check_output(command, timeout=timeout)
            except Exception as err:
                retry_count -= 1
                if retry_count == 0:
                    self.log.error('Unable to launch remote command <%s>' % str(command))
                    self.log.error(str(err))
                    raise err
                time.sleep(5)

    def get_process_id(self, process_name):
        """
        This method basicall gets the process ID of a process.
        Since the Machine class is not working.
        I had to write my own for being able to get process ID of mstsc
        :param process_name:
        :return:
        """
        if '.exe' not in process_name:
            process_name = process_name + ".exe"
        try:
            cm = r'tasklist /FI "imagename eq %s"' % process_name
            tasklist_output = subprocess.check_output(cm)
            if 'No tasks are running which match' in str(tasklist_output):
                # means that no rdp sessions are running
                return []
            final_list = []
            t1 = str(tasklist_output).split(' ')
            for item in t1:
                if 'RDP' in item:
                    final_list.append(t1[t1.index(item) - 1])
                    t1.remove(item)
                elif 'Console' in item:
                    final_list.append(t1[t1.index(item) - 1])
                    t1.remove(item)
            return final_list
        except Exception as err:
            self.log.error(str(err))

    def install_windows_update(self):
        """
        This method basically contains the invoking of the batc file which runs
        the powershell update command.
        Once initiated, code then waits for the output of the batch file and
        reads the windows update report from system32 folder.
        Based on that we check if updates were installed or not. Also if it needs a reboot

        :return: True (if updates were installed) | False (if no updates)
        """
        try:
            self.open_connection()
            self.clean_copy2(self.hyperscale_utils_path, self.remote_local_utils_location, 'install_windows_update.bat')
            self.clean_copy2(self.hyperscale_utils_path, self.remote_local_utils_location, 'install_updates.bat')
            self.clean_copy2(self.hyperscale_utils_path, self.remote_local_system32_path, 'PS_WinUpdate.ps1')

            remote_hostname = str(self.machine_obj.execute_command('hostname').output).strip()
            self.log.info('Will attempt to remove old windows update log file')
            self.log.info(self.remote_system32_path + '\\' + remote_hostname + "_Report.txt")
            try:
                if os.path.exists(self.remote_system32_path+'\\'+remote_hostname+"_Report.txt"):
                    os.remove(self.remote_system32_path+'\\'+remote_hostname+"_Report.txt")
            except Exception as err:
                self.log.error(str(err))
                self.log.error('Unable to remove remote file %s' %
                               str(self.remote_system32_path+'\\'+remote_hostname+"_Report.txt"))
            self.log.info('Initiating install updates now...')
            stime = time.time()
            '''
            For some reason it is not launching the batch file correctly
            Will have to debug more. For now will use the psexec for it
            update_install_op = self.machine_obj.execute_command(
                self.remote_local_utils_location + '\\install_updates.bat')
            self.log.info(update_install_op.output, update_install_op.exception)
            '''
            update_install_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + ' -u ' \
                          + self.tcinputs["clientMachineUser"] + ' -p ' \
                          + self.tcinputs["clientMachinePassword"] + ' ' \
                          + self.remote_local_utils_location + \
                          '\\install_windows_update.bat -accepteula'
            self.log.info(update_install_cmd)
            try:
                update_install_op = self.run_clean_subprocess(update_install_cmd, timeout=self.xlarge_timeout)
                self.log.info(update_install_op)
            except Exception as err:
                self.log.info('Could not launch install updates via psexec. will retry using the machine object')

            etime = time.time()
            time.sleep(5)
            batch_op_obj = open(self.remote_utils_location+"\\op.log", 'r')
            batch_op = batch_op_obj.readlines()
            batch_op_obj.close()
            new_updates = True
            reboot_required = False
            downloaded_updates = 0
            installed_updates = 0
            for line in batch_op:
                if "There are no applicable updates for this computer." in \
                        str(line).strip("\\n").strip("\\t"):
                    self.log.info('No new updates to be installed')
                    new_updates = False
            if new_updates:
                update_output = ''
                for item in os.listdir(self.remote_utils_location):
                    if item.endswith("_Report.txt"):
                        update_output_obj= open(self.remote_utils_location+"\\"+item, 'r')
                        update_output = update_output_obj.readlines()
                        update_output_obj.close()
                        break
                if update_output == '':
                    for item in os.listdir(self.remote_system32_path):
                        if item.endswith("_Report.txt"):
                            update_output_obj = open(self.remote_system32_path + "\\" + item, 'r')
                            update_output = update_output_obj.readlines()
                            update_output_obj.close()
                            break
                if update_output != '':
                    for item in update_output:
                        if "Download Status: SUCCESS" in str(item).strip("\\n").strip("\\t"):
                            self.log.info('Latest updates downloaded successfully')
                            downloaded_updates += 1
                        if "Update Installation Status: SUCCESS" in \
                                str(item).strip("\\n").strip("\\t"):
                            self.log.info('Latest updates installed successfully')
                            installed_updates += 1
                        if "reboot" in str(item).strip("\\n").strip("\\t"):
                            self.log.info('Update Requires reboot. Will reboot now')
                            reboot_required = True
                        if "Exception from HRESULT: 0x80248007" in \
                                str(item).strip("\\n").strip("\\t"):
                            update_cmd_fix = 'psexec \\\\' + \
                                             self.tcinputs["clientMachineHostname"] + ' -u ' \
                                                 + self.tcinputs["clientMachineUser"] + ' -p ' \
                                                 + self.tcinputs["clientMachinePassword"] + \
                                             ' net start msiserver -accepteula'
                            # removing call via psexec in attempt to move to machine object. keeping for workaround
                            # update_install_fix_op =
                            # self.run_clean_subprocess(update_cmd_fix, timeout=self.small_timeout)
                            update_install_fix_op = self.machine_obj.execute_command('net start msiserver')
                            self.log.info(update_install_fix_op.output, update_install_fix_op.exception)
                            #update_install_fix_op = subprocess.check_output(update_cmd_fix, timeout=self.small_timeout)
                            self.log.info(update_install_fix_op)
                    if downloaded_updates != installed_updates:
                        self.log.warning('Not all updates were installed. Please check the logs ')
                        self.log.warning(update_output)
                else:
                    self.log.warning('Unable to check if updates were installed or not.report missing')
            else:
                etime = time.time()
                self.log.info('Took %d minutes to process install updates process'
                              % int((etime - stime) / 60))
                self.reinitialize_esx()
                return False

            self.reinitialize_esx()
            if reboot_required:
                self.shutdown_gracefully()
                time.sleep(10)
                self.esx_object.vm_power_control(self.tcinputs["vm_name"], "on")
                self.let_windows_finish_update()

            self.log.info('Took %d minutes to process install updates process' % int((etime-stime)/60))
            self.machine_obj.delete_file(self.remote_local_system32_path+'\\PS_WinUpdate.ps1')
            return True
        except Exception as err:
            self.log.error('Could not install windows update. Please check')
            self.log.error(str(err))
            self.machine_obj.delete_file(self.remote_local_system32_path + '\\PS_WinUpdate.ps1')
            return False

    def disable_defender(self):
        """
        Method disables the defender on the remote machine
        :return: Nothing
        """
        try:
            self.machine_obj.execute_command('powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"')
            self.modify_reg_key("SOFTWARE\Microsoft\Windows Defender",
                            "DisableAntiSpyware", "00000001", "DWord")
        except Exception as err:
            self.log.warning('Unable to disable defender. It may not be installed on the system')
            self.log.warning(str(err))

    def get_mac_address(self):
        """
        This method is to get the mac address of the remote machine via arp
        :return: IP of the client machine from arpcache if available
        """
        op = str(subprocess.check_output("arp -a"))
        op = op.replace("static", "dynamic")
        op = op.split("dynamic")
        for line in op:
            if self.tcinputs["clientMachineHostname"] in line:
                return line.strip()
        return ''

    def initialize_machine(self):
        """
        This method basically just gets the IP of the VM from the host by using hte vm name
        Then it initializes a rdp connection so as all windows modules are launched
        before we continue

        :return: nothing
        """

        # get IP
        machine_ip = self.esx_object.get_vm_ip(self.tcinputs["vm_name"])
        if self.tcinputs["clientMachineHostname"] == '' or self.tcinputs["clientMachineHostname"] != machine_ip:
            self.tcinputs["clientMachineHostname"] = machine_ip

        if self.tcinputs["clientMachineHostname"] in ('', None):
            self.log.error('Could not get the IP of machine. Exiting')
            raise Exception
        self.log.info('IP of the deployed machine is: %s'
                      % str(self.tcinputs["clientMachineHostname"]))

        try:
            if self.machine_obj is None:
                raise Exception
            if not self.machine_obj.check_directory_exists("C:\\windows"):
                raise Exception
            self.log.info('Old machine object still valid')
        except Exception as err:
            self.log.info('Creating new machine object')
            self.log.info(str(err))
            self.reinitialize_machine_object()

        self.log.info('Disabling firewall on %s ' % self.tcinputs["clientMachineHostname"])
        self.machine_obj.stop_firewall()
        self.disable_defender()
        # rdp into it
        current_rdp_list = self.get_process_id('mstsc.exe')
        th = threading.Thread(target=self.rdp, )
        th.start()
        time.sleep(5)
        end_rdp_list = self.get_process_id('mstsc.exe')
        self.log.info('Initiated RDP connection')
        rdp_id = list(set(end_rdp_list) - set(current_rdp_list))
        try:
            self.log.info('MSTSC process id is %s' % rdp_id)
            time.sleep(25)
            subprocess.call(r'taskkill /pid ' + rdp_id[0] + ' /f')
            self.log.info('Killed RDP session')
        except Exception as err:
            self.log.error(str(err))

    def copy_iso_to_target(self):
        """
        This method is used to push the generated ova/iso file to the destination as requested
        sftp / paramiko is used to upload

        :return: True (if successful) | False (if not)
        """

        import paramiko
        try:
            if self.tcinputs["final_machine_name"] not in (None, "None", "", " "):
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.tcinputs["final_machine_name"],
                            username=self.tcinputs["final_loc_user"],
                            password=self.tcinputs["final_loc_pass"])
                sftp = ssh.open_sftp()
                sftp.get_channel().settimeout(self.xlarge_timeout)
                if int(self.tcinputs["partition_count"]) == 1:
                    machine_type = 'HS2300'
                else:
                    machine_type = 'HS4300'
                temp_folder = machine_type + '_' + \
                              self.version_level + '_' + \
                              self.tcinputs["sp_value"] + '_' + \
                              time.strftime("%d-%b-%Y_%H_%M_%S")

                remote_path = self.tcinputs["final_loc_path"] + temp_folder
                try:
                    sftp.chdir(remote_path)
                except IOError:
                    self.log.info('Created target directory %s' % remote_path)
                    sftp.mkdir(remote_path)
                    time.sleep(2)
                self.log.info('Uploading ova file now...')
                sftp.put(self.created_ova_path,
                         remote_path + '/cvhcics.ova')
                self.log.info('Uploading checksum file now ')
                sftp.put(self.md5_checksum_file, self.tcinputs["final_loc_path"] +
                         temp_folder + '/md5.txt')
                sftp.close()
                ssh.close()
                self.result_string = 'OVA uploaded to: %s' % str(remote_path)
                self.log.info('Deleting local ova file and md5 checksum since copy complete')
                os.remove(self.created_ova_path)
                os.remove(self.md5_checksum_file)
            else:
                self.log.info('Skipping ova copy since no machine path provided')
                return 'NA'
            return str(remote_path)
        except Exception as err:
            self.log.error('Unable to copy the ova to final directory. Please do so manually')
            self.log.error(str(err))
            return 'Unable to copy OVA to target location. %s' %str(err)

    def let_windows_finish_update(self):
        """
        This method basically helps to figure out when the windows is done
        configuring windows after windows install updates has been completed.
        If it cannot figure out it ends the task after about 30 minutes

        :return: nothing
        """

        counter = 0
        while counter <= 1800:

            cmd = "tasklist -S "+self.tcinputs["clientMachineHostname"] + " -U " + \
                  self.tcinputs["clientMachineUser"] + " -P " + \
                  self.tcinputs["clientMachinePassword"]
            try:
                call_op = subprocess.check_output(cmd)
                self.log.info('Waiting for login page to be up..')
                if 'winlogon' in str(call_op):
                    self.log.info('Machine is on its login page now.')
                    break
                if "explorer" in str(call_op):
                    self.log.info('Machine explorer process is running.')
                    break
            except Exception as err:
                self.log.warning(str(err))
                self.log.info('Will keep looking for the logon or exinstall_cs_packageplorer process '
                              'on target machine')
            time.sleep(5)
            counter += 5

    def md5_hash(self, file_name):
        """
        This module basically calculates the MD5 hash value of the provided file
        :param file_name: File name whose checksum need to be calculated

        :return: MD5 checksum | empty string (if failure)
        """

        import hashlib
        try:
            f = open(file_name, 'rb')
            m = hashlib.md5()
            while True:
                data = f.read(10240)
                if len(data) == 0:
                    break
                m.update(data)
            return m.hexdigest()
        except Exception as err:
            self.log.error(err)
            return ''

    def power_on_ops(self, initialize=False, force_vmtools=False):
        """
        does a power on of the VM, gets its IP and waits for windows updates to finish (if any)
        :param initialize:
                True means run the ip query and initiate rdp to launch
                            windows profile service
        :return: Nothing
        """
        self.reinitialize_esx()
        if not self.esx_object.vm_power_control(self.tcinputs["vm_name"], "on"):
            vmtools_cmd = "sc start VMTools"
            self.log.info('Attempting to start vmtools service' )
            try:
                op = self.machine_obj.execute_command(vmtools_cmd)
                self.esx_object.vm_power_control(self.tcinputs["vm_name"], "on", True)
            except Exception as err:
                self.log.error(str(err))
                self.log.info('Could not bring up vmwaretools and existing IP did not work')
                self.esx_object.vm_power_control(self.tcinputs["vm_name"], "on", False)
        if initialize:
            time.sleep(60)
            self.initialize_machine()
        self.let_windows_finish_update()
        self.reinitialize_esx()

    def shutdown_gracefully(self):
        """
        Gracefully shuts down via machien object and if it can't, it will try to do a shutdown
        via esx livrary
        :return: nothing
        """
        try:
            if self.machine_obj is not None:
                self.log.info('Will attempt to shutdown gracefully')
                self.machine_obj.shutdown_client()
                self.reinitialize_esx()
                wait_count = 0
                while self.esx_object.get_vm_power_state(self.tcinputs["vm_name"]) != 'off':
                    self.log.info('Waiting for machine to be shutdown')
                    time.sleep(30)
                    wait_count += 30
                    if wait_count >= 7200:
                        self.log.error('Machine not properly shutdown in 2 hours')
                        self.log.error('will just shutdown now')
                        raise Exception
            else:
                raise Exception
        except Exception as err:
            self.log.info('Could not shutdown gracefully')
            self.log.info('Attempting to shutdown from esx')
            self.esx_object.vm_power_control(self.tcinputs["vm_name"], "off")

    def wait_for_reboot(self):
        self.reinitialize_esx()
        while self.esx_object.get_vm_power_state(self.tcinputs["vm_name"])!= 'off':
            pass

    def install_cs_package(self, sp_value, xml_path):
        """
        This is a method which installs CS package using an xml directly from engweb
        :param sp_value: (str) value of the SP
        :param xml_path: (str) path to the xml to be used
        :return: Nothing
        """
        self.open_connection()

        mount_clear = "cmd.exe /c net use * /D /Y "
        self.log.info(str(self.machine_obj.execute_command(mount_clear).output))



        self.log.info(self.machine_obj.mount_network_path(
            r"\\"+self.tcinputs["eng_path"],
            self.tcinputs["mount_username"], self.tcinputs["mount_password"]))

        self.log.info('Now building install batch')
        pre_install_cmd = r'net use \\%s %s /USER:%s' % \
                          (self.tcinputs["eng_path"], self.tcinputs["mount_password"], self.tcinputs["mount_username"])

        if self.cs_bootstrap_path in ('',None,'None'):
            install_exe = str(self.get_install_exe(sp_value))
            self.log.info(install_exe)
            install_cmd = \
                r'start /wait cmd.exe /c \\%s\%s\BootStrapper\Commvault-1\%s' \
                r' /wait /silent /install /silent /play "%s"' % (self.config.Hyperscale.engweb_path,
                                                                 sp_value, install_exe, xml_path)
        else:
            self.log.info(' Using custom cs bootstrap path')
            install_cmd = r'start /wait cmd.exe /c %s' \
                r' /wait /silent /install /silent /play "%s"' % (str(self.cs_bootstrap_path), xml_path)

        if '2.' in self.tcinputs["hyperscale_version"]:
            install_cmd = install_cmd + ' /decoupledfailoverinstance'

        post_install_cmd = r'net use * /D /Y'
        self.log.info(str(install_cmd))
        install_batch = open('c:\\install_CS_direct.bat', 'w')
        install_batch.write(pre_install_cmd + '\n')
        install_batch.write(install_cmd + '\n')
        install_batch.write(post_install_cmd + '\n')
        install_batch.close()
        self.log.info("Install batch file built")
        self.clean_copy2("C:\\", "C:\\temp\\utils","install_CS_direct.bat")
        time.sleep(10)
        install_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + ' -u ' \
                      + self.tcinputs["clientMachineUser"] + ' -p ' \
                      + self.tcinputs["clientMachinePassword"] + \
                      ' "C:\\temp\\utils\\install_CS_direct.bat" -accepteula'
        # self.log.info(str(sysprep_cmd))
        self.log.info('Starting CS install now...')
        install_result = self.run_clean_subprocess(install_cmd, timeout=self.xlarge_timeout)
        # Will keep using run via psexec because for some reason machine object execute fails to run this batch EVERY
        #  time
        # install_result = self.machine_obj.execute_command("C:\\temp\\utils\\install_CS_direct.bat")
        self.log.info(install_result)

        time.sleep(10)
        self.open_connection()

        if not self.machine_obj.wait_for_process_to_exit("Setup.exe",
                                                         time_out=self.xlarge_timeout, poll_interval=300):
            self.log.error('Install not finished in 8 hours')
            raise Exception
        self.log.info('CS install finished')
        time.sleep(30)
        return

    def sys_prep(self):
        """
        Does all operations needed to be done at sysprep
        1. copy all data to remote machine
        2. run fw exclusions
        3. seal license
        4. uninstall vmtools
        5. run sysprep batch
        :return:
        """
        self.log.info('Will copy sysprep related files')
        # copying the sysprep data
        self.clean_copy2(self.hyperscale_preova_path,
                         self.remote_local_sysprep_path,
                         'ForSysprep.xml')
        self.clean_copy2(self.hyperscale_preova_path,
                         self.remote_local_sysprep_path,
                         'sysprep.bat')
        self.clean_copy2(self.hyperscale_preova_path,
                         self.remote_local_sysprep_path,
                         'PsGetsid.exe')
        self.clean_copy2(self.hyperscale_preova_path,
                         self.remote_local_sysprep_path,
                         'uninstall_vmtools.bat')
        self.clean_copy2(self.hyperscale_preova_path,
                         self.remote_local_sysprep_path,
                         'uninstall_vmwaretools.ps1')
        self.clean_copy2(self.hyperscale_utils_path,
                         self.remote_local_utils_location, 'start_services.bat')

        self.log.info('Successfully copied sysprep data to %s' % self.remote_sysprep_path)
        time.sleep(5)
        self.machine_obj.execute_command(self.remote_local_utils_location + '\\start_services.bat')

        self.seal_license()
        
        time.sleep(15)

        self.log.info('Initiating uninstall of vmtools')
        self.machine_obj.execute_command("C:\\Windows\\System32\\Sysprep\\uninstall_vmtools.bat")
        time.sleep(1800)
        self.power_on_ops()

        self.machine_obj.execute_command(self.remote_local_utils_location + '\\start_services.bat')
        self.log.info('Executing sysprep batch file now')
        sysprep_output = self.machine_obj.execute_command("C:\\Windows\\System32\\Sysprep\\sysprep.bat")
        self.log.info(sysprep_output)
        time.sleep(600)

    def get_install_exe(self, sp_value):
        """
        This method basically does a mount of the eng web path for the req'd
         SP and checks the latest exe name since it changes with every recut

        :param sp_value: (str) SP value (example SP16)
        :return: Nothing
        """
        remount = False
        if self.cs_bootstrap_path in (None,'','None'):
            eng_path = r"\\%s\%s\BootStrapper\Commvault-1" % (self.config.Hyperscale.engweb_path, sp_value)
            machine = r"\\%s\%s\BootStrapper\Commvault-1" % (self.config.Hyperscale.engweb_path, sp_value)
        else:
            return ''
        try:

            op = os.listdir(eng_path)
            if len(op) > 0:
                return op[0]
            else:
                self.log.info('Could not get latest exe name. will exit')
                raise Exception

        except Exception as err:
            self.log.error(str(err))
            raise Exception

    def setup_fw_exclusions(self):

        self.log.info('Running Firewall exclusions')
        fw_cmd = r"start /wait AddFWExclusions.bat"
        self.log.info(fw_cmd)
        fw_batch = open(r'C:\temp\utils\run_fw.bat', 'w')
        if int(self.tcinputs["partition_count"]) == 4:
            fw_batch.write('E: \n')
        fw_batch.write('cd "%s"\n' % self.remote_local_base_path)
        fw_batch.write(fw_cmd + '\n')
        fw_batch.close()
        self.clean_copy2("C:\\temp\\utils", "C:\\temp\\utils", "run_fw.bat")
        time.sleep(10)
        fw_bat_cmd = 'psexec \\\\' + self.tcinputs["clientMachineHostname"] + ' -u ' \
                 + self.tcinputs["clientMachineUser"] + ' -p ' \
                 + self.tcinputs["clientMachinePassword"] + \
                 ' "C:\\temp\\utils\\run_fw.bat" -accepteula'
        fw_bat_res = self.run_clean_subprocess(fw_bat_cmd, timeout=self.xlarge_timeout)
        self.log.info(fw_bat_cmd)
        self.log.info(fw_bat_res)

        time.sleep(180)
        self.log.info('Finished running Firewall exclusion')

    def run(self):

        """Run function of this test case"""

        try:
            self.cs_bootstrap_path = self.tcinputs["cs_bootstrap_path"]
            if self.tcinputs["run_deploy"] in (True, "True"):
                # destroy vm --> Removing this since a bad input can delete the base VM
                # self.log.info('Will delete if there is any vm by the name already')
                # self.esx_object.destroy_vm(self.tcinputs["vm_name"])

                # deploy ovf
                self.esx_object.deploy_ovf(self.tcinputs["esxDatacenterName"],
                                           self.tcinputs["esxDataStorename"],
                                           self.tcinputs["esx_cluster_name"],
                                           self.tcinputs["vm_vmdkPath"],
                                           self.tcinputs["vm_ovfPath"])
            else:
                self.log.info('Skipping Deployment step as instructed')
                if self.tcinputs["snapshot_name"] not in (None, "None",""):
                    self.log.info('Will use the suggested snapshot now')
                    if self.tcinputs["snapshot_name"].lower() == "auto_choose":
                        op = self.esx_object.get_snapshots(self.tcinputs["vm_name"])
                        for item in op:
                            if "Windows_Updates_installed" not in item["snapshot_name"]:
                                op.remove(item)
                        latest = 0
                        if len(op) == 0:
                            self.log.error('Please provide valid snapshot name.Exiting')
                            return False
                        self.log.info(op)
                        for item in op:
                            if 'Windows_Updates_installed_' in item["snapshot_name"]:
                                if latest == 0:
                                    latest = int(item["snapshot_name"].
                                                 lstrip("Windows_Updates_installed_"))
                                    latest_snap = item["snapshot_name"]
                                else:
                                    if latest < int(item["snapshot_name"].
                                                            lstrip("Windows_Updates_installed_")):
                                        latest = int(item["snapshot_name"].
                                                     lstrip("Windows_Updates_installed_"))
                                        latest_snap = item["snapshot_name"]
                        if latest != 0:
                            if not self.esx_object.revert_snapshot(self.tcinputs["vm_name"],
                                                                   latest_snap):
                                self.log.error('Error selecting snapshot %s'
                                               % str(latest_snap))
                            else:
                                self.log.info('Reverted to snapshot: %s' %str(latest_snap))
                        else:
                            self.log.info('Could not find any code created snapshot to revert to. '
                                          'Please provide a valid snapshot name'
                                          ' to select it or pass "None"')
                    else:
                        if not self.esx_object.revert_snapshot(self.tcinputs["vm_name"],
                                                               self.tcinputs["snapshot_name"]):
                            self.log.error('Error selecting snapshot %s'
                                           % self.tcinputs["snapshot_name"])
                else:
                    self.log.info('Using current machine state as instructed')
            if self.tcinputs["install_win_updates"] in ("True", True) or \
                    self.tcinputs["run_configure"] in ("True", True):
                self.shutdown_gracefully()
                time.sleep(60)
                self.power_on_ops(initialize=True)
                time.sleep(120)
                self.generate_paths()
            elif self.tcinputs["prepare_ova"] in ('True', True):
                if self.esx_object.get_vm_power_state(self.tcinputs["vm_name"])== 'off':
                    self.power_on_ops(initialize=True)

                else:
                    self.initialize_machine()
                time.sleep(120)
                # -----------------------------------------------------------
                # Will now generate paths since we now have the machine IP
                self.generate_paths()
                # Done generating paths
                # -----------------------------------------------------------
            # install windows update (conditional)
            if self.tcinputs["install_win_updates"] in ("True", True):
                self.open_connection()
                time.sleep(60)
                self.log.info('Will now install latest windows updates. This can take a while')
                if self.install_windows_update():
                    self.log.info('New updates were installed. '
                                  'We will take a snapshot of the machine for future use')
                    self.log.info('We will reset the machine once before taking '
                                  'a snapshot of it')
                    self.reinitialize_esx()
                    self.shutdown_gracefully()
                    time.sleep(5)
                    self.power_on_ops()

                    if self.tcinputs["manage_via_snapshots"] in ("True", True):
                        snapshot_name = 'Windows_Updates_installed_' + str(int(time.time()))
                        self.shutdown_gracefully()
                        time.sleep(5)
                        self.esx_object.save_snapshot(self.tcinputs["vm_name"], snapshot_name)
                        self.log.info('Snapshot saved as: %s' % snapshot_name)
                        self.power_on_ops()
                    if self.tcinputs["export_updated_snapshot"] in ("True", True):
                        try:
                            # export updated blank windows to ovf
                            output_path = '\\'.join(self.tcinputs["vm_vmdkPath"].split('\\')[0:-1])
                            exported_updates_ovf_dir = self.esx_object.export_vm(self.tcinputs["vm_name"],
                                                                                 output_path +
                                                                                 "\\updated_Windows_" +
                                                                                 str(int(time.time())))
                            self.log.info(exported_updates_ovf_dir)
                            self.log.info('Exported updated windows machine as ovf')
                        except Exception as err:
                            self.log.warning(str(err))
                            self.log.warning('Issues while exporting updated windows vm. '
                                             'will continue anyway')
                        finally:
                            self.power_on_ops()
                else:
                    self.initialize_machine()
                time.sleep(120)
                # -----------------------------------------------------------
                # Will now generate paths since we now have the machine IP
                self.generate_paths()
                # Done generating paths
                # -----------------------------------------------------------

            if self.tcinputs["test_code"] in ("True", True):
                self.initialize_machine()
                self.open_connection()
                time.sleep(60)
                self.run_tempdb_query()

            if self.tcinputs["run_configure"] in ("True", True):
                # open connection
                self.open_connection()
                time.sleep(60)

                # transfer packages
                self.transfer_files()
                time.sleep(60)
                # configure machine and unzip package, install CS package
                self.configure_machine()
                time.sleep(60)
                self.open_connection()
                # We will take a snapshot of the created machine.
                sp_val = self.read_reg_value("SOFTWARE\\CommVault Systems\\Galaxy\\Instance001\\UpdateFlags",
                                        "LastInstalledUpdateName")
                if sp_val == '':
                    sp_val = self.read_reg_value("SOFTWARE\\CommVault Systems\\Galaxy\\Instance001\\UpdateBinTran",
                                        "SP_Transaction")

                    desc = 'Latest SP transaction: %s' % str(sp_val)
                else:
                    desc = 'Latest installed update: %s' % str(sp_val)

                if sp_val != '':
                    sp_val = sp_val.split("_")[0]
                    self.sp_level = sp_val

                version_val = self.read_reg_value(r"SOFTWARE\CommVault Systems\Galaxy\Instance001\Base",
                                        "sVERSION")
                if version_val != '':
                    version_val = version_val.split(".")[0]
                    self.version_level = version_val



                snapshot_name = 'CV_' + str(version_val) +'_'+str(sp_val) + '_' + \
                                str(time.strftime("%d-%b-%Y_%H_%M_%S"))
                self.reinitialize_esx()
                self.shutdown_gracefully()
                time.sleep(5)
                self.esx_object.save_snapshot(self.tcinputs["vm_name"],
                                              snapshot_name, description=desc)
                self.log.info('Snapshot saved as: %s' % snapshot_name)
                self.power_on_ops()
                time.sleep(120)
                if sp_val != '':
                    sp_val = sp_val.split("_")[0]
                    self.sp_level = sp_val

                version_val = self.read_reg_value(r"SOFTWARE\CommVault Systems\Galaxy\Instance001\Base",
                                        "sVERSION")
                if version_val != '':
                    version_val = version_val.split(".")[0]
                    self.version_level = version_val

                snapshot_name = 'CV_' + str(version_val) +'_'+str(sp_val) + '_' + \
                                str(time.strftime("%d-%b-%Y_%H_%M_%S"))
                self.reinitialize_esx()
                self.shutdown_gracefully()
                time.sleep(5)
                self.esx_object.save_snapshot(self.tcinputs["vm_name"],
                                              snapshot_name, description=desc)
                self.log.info('Snapshot saved as: %s' % snapshot_name)
                self.power_on_ops()
                time.sleep(120)
            else:
                    self.log.info('Skipping Configuration step as instructed')

            # -----------------------------------------------------------
            # -----------------------------------------------------------
            if self.tcinputs["prepare_ova"] in ('True', True):
                self.open_connection()
                # copying the driver
                self.clean_copy2(self.hyperscale_preova_path + "\\" + self.tcinputs["sp_value"],
                                 self.remote_local_driver_path, 'EvalLicSeal.exe')
                self.clean_copy2(self.hyperscale_preova_path + "\\" + self.tcinputs["sp_value"],
                                 self.remote_local_driver_path, 'EvalLicUnSeal.exe')
                self.clean_copy2(self.hyperscale_preova_path, self.remote_local_driver_path,
                                 'UpdateCSGUID.sqle')

                self.clean_copy2(self.hyperscale_preova_path, self.remote_local_scripts_path,
                                 'UpdateCSGUID.sqle')

                self.clean_copy2(self.hyperscale_preova_path + "\\" + self.tcinputs["sp_value"],
                                 self.remote_local_base_path, 'EvalLicSeal.exe')
                self.clean_copy2(self.hyperscale_preova_path + "\\" + self.tcinputs["sp_value"],
                                 self.remote_local_base_path, 'EvalLicUnSeal.exe')
                self.clean_copy2(self.hyperscale_preova_path, self.remote_local_base_path,
                                 'UpdateCSGUID.sqle')

                self.log.info('Successfully copied driver data to %s and %s'
                              % (self.remote_driver_path1, self.remote_base_path))
                self.manage_services()
                self.machine_obj.execute_command(self.remote_local_utils_location + '\\start_services.bat')
                time.sleep(600)
                self.commit_cache()
                self.reinitialize_esx()
                # enable firewall, run FW exclusions, run eval license ,
                # run sysprep, delete sysprep data
                # remove temp directory, remove sysprep batfile, remove vmware tools
                self.setup_fw_exclusions()
                self.setup_fw_exclusions() # Needs to be executed again. batch file sometimes takes effect on 2nd run

                snapshot_name = 'Before_sysprep__'+str(int(time.time()))
                self.shutdown_gracefully()
                time.sleep(5)
                self.esx_object.save_snapshot(self.tcinputs["vm_name"],
                                             snapshot_name, description='Image before sysprep')
                self.log.info('Snapshot saved as: %s' % snapshot_name)
                self.power_on_ops(initialize=True)
                time.sleep(120)
                self.open_connection()
                self.reinitialize_esx()

                self.sys_prep()
                self.log.info('sysprep operation finished. Waiting upto 10 mins')
                # off VM
                time.sleep(900)
                self.reinitialize_esx()
                vm_state = self.esx_object.get_vm_power_state(self.tcinputs["vm_name"])
                if vm_state == 'on':

                    self.log.error('VM is still turned ON. will not take ova now. exiting')
                    self.log.info(vm_state)
                    raise Exception
                elif vm_state == 'off':
                    self.log.info('VM is already turned OFF. Will continue')
                    self.log.info(vm_state)
                else:
                    self.log.warning('VM is in a non expected state: %s' % str(vm_state))
                    raise Exception


            else:
                self.log.info('Skipping OVA preparation step as instructed')
            # -----------------------------------------------------------
            # -----------------------------------------------------------
            if self.tcinputs["run_export_ova"] in ('True', True):

                # remove adapter
                self.reinitialize_esx()
                self.esx_object.delete_all_nics(self.tcinputs["vm_name"])
                exported_ovf_dir = self.esx_object.export_vm(self.tcinputs["vm_name"], "C:\\temp")
                self.log.info('Exported CS machine as ovf')
                self.reinitialize_esx()

                # convert to ova
                self.esx_object.create_ova(self.created_ova_path, exported_ovf_dir)
                self.log.info(r'Created OVA: %s' % str(self.created_ova_path))

                # calculate md5
                md5_value = self.md5_hash(self.created_ova_path)
                if md5_value == '':
                    self.log.error('Could not calculate md5 checksum of ova')
                else:
                    self.log.info('md5 checksum of ova is: %s' % str(md5_value))
                op = open(self.md5_checksum_file, "w")
                op.write(md5_value)
                op.close()

                # Copy ova to final loc
                op = self.copy_iso_to_target()
                if op == 'NA':
                    pass
                elif 'Unable to copy OVA to target location' in op:
                    self.status = constants.PASSED
                    self.result_string = str(op) + ' . Please copy the  OVA manually from the machine location: %s '\
                        % self.created_ova_path
                else:
                    self.status = constants.PASSED
                    self.result_string = 'OVA Generated at %s:%s .Creds: %s,%s' % (self.tcinputs["final_machine_name"],
                                                                  op,
                                                                  'guest',
                                                                  'cvadmin')
                    self.log.info(self.result_string)
                if self.tcinputs["run_delete_vm"] in ('True', True):
                    # destroy VM
                    self.log.info('Will now destroy the VM')
                    self.esx_object.destroy_vm(self.tcinputs["vm_name"])
                else:
                    self.log.info('Skipping VM delete as instructed')
            else:
                self.log.info('Skipping OVA EXPORT step as instructed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.log.info(self.status)
            self.log.info(self.result_string)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info('End of test case')
