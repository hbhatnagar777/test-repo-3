"""Main file for performing Local Simpana Detection Operation """

import os
import re
import platform
import subprocess
import logger
try:
    import winreg
except ImportError:
    pass


class Simpanadefaults():
    """
    Class Simpana Defaults is responsible for Local Commvault detection
    Methods :
    local_cs_detection : Method to detect local Commvault  installation and fetch CS name
    local_client_detection : Method to detect local Commvault  installation and fetch Clientname
    """
    @staticmethod
    def _winregistry_reading(path, keyname):
        """
        Method to read Windows Registry
        """
        key_value = None
        status = False
        try:
            key2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                  path, 0, winreg.KEY_ALL_ACCESS)
            key_list = winreg.QueryValueEx(key2, keyname)
            key_value = key_list[0]
            status = True
        except Exception:
            status = False
        finally:
            return status, key_value

    def local_cs_detection(self, instance_name):
        """
        Method to detect local commvault  installation and
        returns the local  CS name  to the calling function
        Args :
        instance_name:Commvault Instance
        Returns :
        status = True | False depending on Commvault Detection on Local Machine
        csName= Commvault CS for the currently detected Local client
        """
        loglines = []
        is_interface_list = False
        try:
            csname = ""
            flag = False
            keyvalue2 = ""
            INSTANCE_PATH = 'SOFTWARE\\CommVault Systems\\Galaxy\\' + instance_name
            if platform.system() == 'Windows':
                comm_path = INSTANCE_PATH + '\\CommServe'
                keyname = 'sCSINTERFACELIST'
                (status, cs_interface_list) = Simpanadefaults()._winregistry_reading(comm_path, keyname)
                if status is True:
                    loglines.append(["i", f"CS Interface List is :{cs_interface_list}"])
                    csname = cs_interface_list
                    flag = True
                    is_interface_list = True
                else:
                    comm_path = INSTANCE_PATH + '\\CommServe'
                    keyname = 'sCSHOSTNAME' 
                    (status, cs_hostname) = Simpanadefaults()._winregistry_reading(comm_path, keyname)
                    if status is True:
                        loglines.append(["i", f"CS Hostname is :{cs_hostname}"])
                        csname = cs_hostname
                        flag = True
                    else:
                        loglines.append(["e", "Issue in reading from Windows registry"])
            elif platform.system() == 'Linux':
                try:
                    cmd = subprocess.Popen(
                        "id -u", stdout=subprocess.PIPE, shell=True)
                    i, error = cmd.communicate()
                    i = int(i)
                    reg_path = "/etc/CommVaultRegistry/Galaxy/"
                    if i != 0:
                        user_cmd = subprocess.Popen(
                            "id -u -n", stdout=subprocess.PIPE, shell=True)
                        user, error = user_cmd.communicate()
                        home_cmd = subprocess.Popen(
                            "echo $HOME", stdout=subprocess.PIPE, shell=True)
                        home, error = home_cmd.communicate()
                        home_string = home.decode().rstrip('\n')
                        cv_reg_path = "CommVaultRegistry/Galaxy/"
                        cv_reg_path = os.path.join(home_string, cv_reg_path)
                        if os.path.exists(cv_reg_path):
                            reg_path = cv_reg_path
                    linux_path1 = reg_path + instance_name
                    if os.path.exists(linux_path1):
                        linux_path2 = reg_path + instance_name + "/CommServe"
                        if os.path.exists(linux_path2):
                            filename2 = linux_path2 + "/.properties"
                            file2 = open(filename2, 'r')
                            lines = file2.readlines()

                            for item in lines:
                                item = str(item)
                                if item.startswith("sCSINTERFACELIST"):
                                    reg_detail2 = item
                                    is_interface_list = True
                                    break
                                elif item.startswith("sCSHOSTNAME"):
                                    cs_hostname = item
                                else:
                                    continue
                            
                            if not is_interface_list:
                                reg_detail2 = cs_hostname
                            
                            cs_node_name = reg_detail2.split()
                            keyvalue2 = str(cs_node_name[1])
                            csname = keyvalue2
                            file2.close()
                            flag = True
                        else:
                            loglines.append(["e",
                                             "Commvault Registry Path does not exist : " + str(linux_path2)])
                            # sys.exit(0)
                    else:
                        loglines.append(["e",
                                         "Commvault Registry Path does not exist : " + str(linux_path1)])

                except (IOError, SystemError) as linux_registry_exception:
                    loglines.append(["e", "Error in Opening Linux Commvault Registry"])
                    loglines.append(["e", "Exception is %s" % linux_registry_exception])
                    flag = False
            elif platform.system() == 'OS400':
                loglines.append(["i", 'IBMi machine, skipping...'])
            else:
                loglines.append(["e", "Unsupported OS"])
                # sys.exit(0)
        except Exception as simpana_detect_exception:
            loglines.append(["e", "Exception in local CS detection : %s" %
                             simpana_detect_exception])

        finally:
            return (flag, csname, loglines, is_interface_list)

    def local_client_detection(self, instance_name):
        """
        Method to detect local commvault installation  and
        returns the local client name to the calling function
        Args :
        instance_name:Commvault Instance
        Returns :
        status = True | False depending on Commvault Detection on Local Machine
        clientName=Local client name
        """
        loglines = []
        try:
            clientname = ""
            flag = False
            INSTANCE_PATH = 'SOFTWARE\\CommVault Systems\\Galaxy\\' + instance_name
            if platform.system() == 'Windows':
                keyname = 'sPhysicalNodeName'
                (status, clientname) = Simpanadefaults(
                )._winregistry_reading(INSTANCE_PATH, keyname)
                if status is True:
                    flag = True
                else:
                    loglines.append(["e", "Issue in reading from Windows registry"])

            elif platform.system() == 'Linux':
                try:
                    cmd = subprocess.Popen(
                        "id -u", stdout=subprocess.PIPE, shell=True)
                    i, error = cmd.communicate()
                    i = int(i)
                    reg_path = "/etc/CommVaultRegistry/Galaxy/"
                    if i != 0:
                        user_cmd = subprocess.Popen(
                            "id -u -n", stdout=subprocess.PIPE, shell=True)
                        user, error = user_cmd.communicate()
                        home_cmd = subprocess.Popen(
                            "echo $HOME", stdout=subprocess.PIPE, shell=True)
                        home, error = home_cmd.communicate()
                        home_string = home.decode().rstrip('\n')
                        cv_reg_path = "CommVaultRegistry/Galaxy/"
                        cv_reg_path = os.path.join(home_string, cv_reg_path)
                        if os.path.exists(cv_reg_path):
                            reg_path = cv_reg_path
                    linux_path1 = reg_path + instance_name
                    if os.path.exists(linux_path1):
                        filename1 = linux_path1 + "/.properties"
                        file1 = open(filename1, 'r')
                        lines = file1.readlines()
                        for item in lines:
                            item = str(item)
                            if item.startswith("sPhysicalNodeName"):
                                reg_detail1 = item
                                break
                            else:
                                continue
                        physical_node_name = reg_detail1.split()
                        keyvalue1 = str(physical_node_name[1])
                        clientname = keyvalue1
                        flag = True
                        file1.close()
                    else:
                        loglines.append(["e",
                                         "Commvault Registry Path does not exist : %s" % (linux_path1)])

                except (IOError, SystemError) as linux_registry_exception:
                    loglines.append(["e", "Exception is :%s" % linux_registry_exception])
                    flag = False
            elif platform.system() == 'OS400':
                loglines.append(["i", 'IBMi machine, skipping...'])
            else:
                loglines.append(["e", "Unsupported OS"])
                # sys.exit(0)
        except Exception as simpana_detect_exception:
            loglines.append(["e", "Exception in client detection : %s" %
                             simpana_detect_exception])

        finally:
            return (flag, clientname, loglines)

    def check_for_local_instance(self, client_name):
        """
        Method to detect if client passed belongs to local instance
        Args :
        client_name:Client Name
        Returns :
        status = True | False depending on whether client is local
        """
        loglines = []
        try:
            flag = False

            if platform.system() == 'Windows':
                instances_list = []
                win_path = 'SOFTWARE\\CommVault Systems\\Galaxy'
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                         win_path, 0, winreg.KEY_ALL_ACCESS)
                    i = 0
                    while True:
                        try:
                            subkey = winreg.EnumKey(key, i)
                            instances_list.append(subkey)
                            i = i + 1
                        except WindowsError:
                            break
                    for path in instances_list:
                        if path.startswith("Instance"):
                            instance_path = 'SOFTWARE\\CommVault Systems\\Galaxy' + "\\" + path
                            keyname = 'sPhysicalNodeName'
                            (status, clientname) = Simpanadefaults(
                            )._winregistry_reading(instance_path, keyname)
                            if status is True:
                                if clientname == client_name:
                                    flag = True
                                    break
                except Exception as windows_registry_exception:
                    windows_registry_exception = str(
                        windows_registry_exception)
                    flag = False
                    loglines.append(["e", "Exception in accessing Windows Commvault Registry :%s" %
                                     windows_registry_exception])

            elif platform.system() == 'Linux':
                try:
                    cmd = subprocess.Popen(
                        "id -u", stdout=subprocess.PIPE, shell=True)
                    i, error = cmd.communicate()
                    i = int(i)
                    reg_path = "/etc/CommVaultRegistry/Galaxy/"
                    if i != 0:
                        user_cmd = subprocess.Popen(
                            "id -u -n", stdout=subprocess.PIPE, shell=True)
                        user, error = user_cmd.communicate()
                        home_cmd = subprocess.Popen(
                            "echo $HOME", stdout=subprocess.PIPE, shell=True)
                        home, error = home_cmd.communicate()
                        home_string = home.decode().rstrip('\n')
                        cv_reg_path = "CommVaultRegistry/Galaxy/"
                        cv_reg_path = os.path.join(home_string, cv_reg_path)
                        if os.path.exists(cv_reg_path):
                            reg_path = cv_reg_path
                    if os.path.exists(reg_path):
                        instances_list = None
                        instances_list = os.listdir(reg_path)
                        if instances_list:
                            for i in instances_list:
                                if i.startswith("Instance"):
                                    filename1 = reg_path + i + "/.properties"
                                    file1 = open(filename1, 'r')
                                    lines = file1.readlines()
                                    for item in lines:
                                        item = str(item)
                                        if item.startswith("sPhysicalNodeName"):
                                            reg_detail1 = item
                                            break
                                        else:
                                            continue
                                    physical_node_name = reg_detail1.split()
                                    keyvalue1 = str(physical_node_name[1])
                                    clientname = keyvalue1
                                    if clientname == client_name:
                                        flag = True
                                        file1.close()
                                        break
                    else:
                        loglines.append(["e",
                                         "Commvault Registry Path does not exist : %s" % (reg_path)])

                except (IOError, SystemError) as linux_registry_exception:
                    loglines.append(["e", "Exception is :%s" % linux_registry_exception])
                    flag = False
            elif platform.system() == 'OS400':
                loglines.append(["i", 'IBMi machine, skipping...'])
            else:
                loglines.append(["e", "Unsupported OS"])
                # sys.exit(0)
        except Exception as simpana_detect_exception:
            loglines.append(["e", "Exception in checking for local instance : %s" %
                             simpana_detect_exception])

        finally:
            return (flag, loglines)

    def simpana_installation_path(self, instance_name):
        loglines = []

        try:
            installation_path = ""
            flag = False
            keyvalue1 = ""
            if platform.system() == 'Windows':
                base_path = 'SOFTWARE\\CommVault Systems\\Galaxy' + \
                    '\\' + instance_name + '\\' + 'Base'
                base_path = str(base_path)
                try:
                    key1 = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, base_path, 0, winreg.KEY_READ)
                    galaxy_home = winreg.QueryValueEx(
                        key1, "dGALAXYHOME")
                    keyvalue1 = galaxy_home[0]
                    installation_path = keyvalue1
                    flag = True
                except Exception as windows_registry_exception:
                    windows_registry_exception = str(
                        windows_registry_exception)
                    flag = False
                    loglines.append(["e", "Exception in accessing Windows Commvault Registry :%s" %
                                     windows_registry_exception])

            elif platform.system() == 'Linux':
                try:
                    cmd = subprocess.Popen(
                        "id -u", stdout=subprocess.PIPE, shell=True)
                    i, error = cmd.communicate()
                    i = int(i)
                    reg_path = "/etc/CommVaultRegistry/Galaxy/"
                    if i != 0:
                        user_cmd = subprocess.Popen(
                            "id -u -n", stdout=subprocess.PIPE, shell=True)
                        user, error = user_cmd.communicate()
                        home_cmd = subprocess.Popen(
                            "echo $HOME", stdout=subprocess.PIPE, shell=True)
                        home, error = home_cmd.communicate()
                        home_string = home.decode().rstrip('\n')
                        cv_reg_path = "CommVaultRegistry/Galaxy/"
                        cv_reg_path = os.path.join(home_string, cv_reg_path)
                        if os.path.exists(cv_reg_path):
                            reg_path = cv_reg_path
                    linux_path1 = reg_path + instance_name + "/Base"
                    if os.path.exists(linux_path1):
                        filename1 = linux_path1 + "/.properties"
                        file1 = open(filename1, 'r')
                        lines = file1.readlines()
                        for item in lines:
                            item = str(item)
                            if item.startswith("dGALAXYHOME"):
                                reg_detail1 = item
                                break
                            else:
                                continue
                        galaxy_home = reg_detail1.split()
                        keyvalue1 = str(galaxy_home[1])
                        installation_path = keyvalue1
                        file1.close()
                        flag = True
                        # sys.exit(0)
                    else:
                        loglines.append(["e",
                                         "Commvault Registry Path does not exist : %s" % (linux_path1)])

                except (IOError, SystemError) as linux_registry_exception:
                    loglines.append(["e", "Exception is :%s" % linux_registry_exception])
                    flag = False
            elif platform.system() == 'OS400':
                loglines.append(["i", 'IBMi machine, skipping...'])
            else:
                loglines.append(["e", "Unsupported OS"])
                # sys.exit(0)
        except Exception as simpana_detect_exception:
            loglines.append(["e", "Exception in Commvault installation path detection : %s" %
                             simpana_detect_exception])

        finally:
            return (flag, installation_path, loglines)

    def simpana_logging_path(self, instance_name):
        loglines = []

        try:
            logging_path = ""
            flag = False
            keyvalue1 = ""
            if platform.system() == 'Windows':
                base_path = 'SOFTWARE\\CommVault Systems\\Galaxy' + '\\' + instance_name + '\\' + 'EventManager'
                base_path = str(base_path)
                try:
                    key1 = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, base_path, 0, winreg.KEY_READ)
                    galaxy_home = winreg.QueryValueEx(
                        key1, "dEVLOGDIR")
                    keyvalue1 = galaxy_home[0]
                    logging_path = keyvalue1
                    flag = True
                except Exception as windows_registry_exception:
                    windows_registry_exception = str(
                        windows_registry_exception)
                    flag = False
                    loglines.append(["e", "Exception in accessing Windows Commvault Registry :%s" %
                                     windows_registry_exception])

            elif platform.system() == 'Linux':
                try:
                    cmd = subprocess.Popen(
                        "id -u", stdout=subprocess.PIPE, shell=True)
                    i, error = cmd.communicate()
                    i = int(i)
                    reg_path = "/etc/CommVaultRegistry/Galaxy/"
                    if i != 0:
                        user_cmd = subprocess.Popen(
                            "id -u -n", stdout=subprocess.PIPE, shell=True)
                        user, error = user_cmd.communicate()
                        home_cmd = subprocess.Popen(
                            "echo $HOME", stdout=subprocess.PIPE, shell=True)
                        home, error = home_cmd.communicate()
                        home_string = home.decode().rstrip('\n')
                        cv_reg_path = "CommVaultRegistry/Galaxy/"
                        cv_reg_path = os.path.join(home_string, cv_reg_path)
                        if os.path.exists(cv_reg_path):
                            reg_path = cv_reg_path
                    linux_path1 = reg_path + instance_name + "/EventManager"
                    if os.path.exists(linux_path1):
                        filename1 = linux_path1 + "/.properties"
                        file1 = open(filename1, 'r')
                        lines = file1.readlines()
                        for item in lines:
                            item = str(item)
                            if item.startswith("dEVLOGDIR"):
                                reg_detail1 = item
                                break
                            else:
                                continue
                        galaxy_home = reg_detail1.split()
                        keyvalue1 = str(galaxy_home[1])
                        logging_path = keyvalue1
                        file1.close()
                        flag = True
                        # sys.exit(0)
                    else:
                        loglines.append(["e",
                                         "Commvault Registry Path does not exist : %s" % (linux_path1)])

                except (IOError, SystemError) as linux_registry_exception:
                    loglines.append(["e", "Exception is :%s" % linux_registry_exception])
                    flag = False
            elif platform.system() == 'OS400':
                loglines.append(["i", 'IBMi machine, skipping...'])
            else:
                loglines.append(["e", "Unsupported OS"])
                # sys.exit(0)
        except Exception as simpana_detect_exception:
            loglines.append(["e", "Exception in Commvault logging path detection : %s" %
                             simpana_detect_exception])

        finally:
            return (flag, logging_path, loglines)

    def check_valid_instance(self, instance_name):
        """
        Method to detect if instance passed is a valid instance
        Args :
        instance_name:instance Name
        Returns :
        status = True | False depending on whether instance is valid
        """
        loglines = []
        loglines.append(["i", "Checking validity of instance name"])
        try:
            flag = False
            if platform.system() == 'Windows':
                instances_list = []
                win_path = 'SOFTWARE\\CommVault Systems\\Galaxy'
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                         win_path, 0, winreg.KEY_ALL_ACCESS)
                    i = 0
                    while True:
                        try:
                            subkey = winreg.EnumKey(key, i)
                            instances_list.append(subkey)
                            i = i + 1
                        except WindowsError:
                            break
                    for p in instances_list:
                        if p.startswith("Instance"):
                            if p == instance_name:
                                flag = True
                                loglines.append(["i", "Instance name found to be valid"])
                                break
                except Exception as windows_registry_exception:
                    windows_registry_exception = str(
                        windows_registry_exception)
                    flag = False
                    loglines.append(["e", "Exception in accessing Windows Commvault Registry :%s" %
                                     windows_registry_exception])

            elif platform.system() == 'Linux':
                try:
                    cmd = subprocess.Popen(
                        "id -u", stdout=subprocess.PIPE, shell=True)
                    i, error = cmd.communicate()
                    i = int(i)
                    reg_path = "/etc/CommVaultRegistry/Galaxy/"
                    if i != 0:
                        user_cmd = subprocess.Popen(
                            "id -u -n", stdout=subprocess.PIPE, shell=True)
                        user, error = user_cmd.communicate()
                        home_cmd = subprocess.Popen(
                            "echo $HOME", stdout=subprocess.PIPE, shell=True)
                        home, error = home_cmd.communicate()
                        home_string = home.decode().rstrip('\n')
                        cv_reg_path = "CommVaultRegistry/Galaxy/"
                        cv_reg_path = os.path.join(home_string, cv_reg_path)
                        if os.path.exists(cv_reg_path):
                            reg_path = cv_reg_path
                    if os.path.exists(reg_path):
                        instances_list = None
                        instances_list = os.listdir(reg_path)
                        if instances_list:
                            for i in instances_list:
                                if i.startswith("Instance"):
                                    if i == instance_name:
                                        flag = True
                                        loglines.append(["i", "Instance name found to be valid"])
                                        break
                    else:
                        loglines.append(["e",
                                         "Commvault Registry Path does not exist : %s" % (reg_path)])

                except (IOError, SystemError) as linux_registry_exception:
                    loglines.append(["e", "Exception is :%s" % linux_registry_exception])
                    flag = False
            elif platform.system() == 'OS400':
                flag = True
                loglines.append(["i", 'IBMi machine, skipping instance validation'])
            else:
                loglines.append(["e", "Unsupported OS"])
                # sys.exit(0)
        except Exception as simpana_detect_exception:
            loglines.append(["e", "Exception in checking for valid instance : %s" %
                             simpana_detect_exception])

        finally:
            return (flag, loglines)

    def get_local_instance_name(self, install_directory):
        """To get the local instance name based on install directory provided

        Args:
            install_directory	(str)	-- Commvault install directory

        Returns:
            (str)	-- Instance name

        """
        os_type = platform.system()
        if os_type == 'Linux':
            with open('{0}/galaxy_vm'.format(install_directory), 'r') as file:
                content = file.read()
            temp = re.findall('GALAXY_INST="(.+?)";', content)
            if temp:
                return temp[0]
        elif os_type == 'Windows':
            with open(r'{0}\Base\QinetixVM'.format(install_directory), 'r') as file:
                content = file.read()
            if content:
                return content.strip()

        return "Instance001"
    
    def force_https(self, instance, log):
        """
        Checks for registry key value of bCVC_USE_HTTPS

        Args:

            instance    (str)   --  Instance name like Instance001

            log         (obj)   --  Logger class object

        Returns:

            (bool)  -   True if bCVC_USE_HTTPS is set True else false

        """
        log.info("Checking registry value for key bCVC_USE_HTTPS")
        value = None
        try:
            if platform.system() == 'Windows':
                reg_path = rf'SOFTWARE\CommVault Systems\Galaxy\{instance}\CommvaultSDKForPython'
                _, value = self._winregistry_reading(reg_path, 'bCVC_USE_HTTPS')

            elif platform.system() == 'Linux':
                value = self._get_unix_registry(instance, 'CommvaultSDKForPython', 'bCVC_USE_HTTPS')

        except Exception:
            log.info("Unable to fetch registry value for bCVC_USE_HTTPS")

        finally:
            if value is not None and value != '' and value == 0:
                return False
            return True

    def allow_http(self, instance, log):
        """
        Checks for registry key value of bAllowCVCHttpFallback

        Args:

            instance    (str)   --  Instance name like Instance001

            log         (obj)   --  Logger class object

        Returns:

            (bool)  -   True if bAllowCVCHttpFallback is set True else false

        """
        log.info("Checking registry value for key bAllowCVCHttpFallback")
        value = None
        try:
            if platform.system() == 'Windows':
                reg_path = rf'SOFTWARE\CommVault Systems\Galaxy\{instance}\EventManager'
                _, value = self._winregistry_reading(reg_path, 'bAllowCVCHttpFallback')

            elif platform.system() == 'Linux':
                value = self._get_unix_registry(instance, 'EventManager', 'bAllowCVCHttpFallback')

        except Exception:
            log.info("Unable to fetch registry value for bAllowCVCHttpFallback")

        finally:
            if value:
                return True
            return False
        
    def web_service_url(self, instance, log):
        """
        Checks for registry key value of sCVCWebServiceUrl

        Args:

            instance    (str)   --  Instance name like Instance001

            log         (obj)   --  Logger class object

        Returns:

            (string)  -   web_service_url to be used by cvc for rest api calls

        """
        log.info("Checking registry value for key sCVCWebServiceUrl")
        value = None
        try:
            if platform.system() == 'Windows':
                reg_path = rf'SOFTWARE\CommVault Systems\Galaxy\{instance}\CommvaultSDKForPython'
                _, value = self._winregistry_reading(reg_path, 'sCVCWebServiceUrl')

            elif platform.system() == 'Linux':
                value = self._get_unix_registry(instance, 'CommvaultSDKForPython', 'sCVCWebServiceUrl')

        except Exception:
            log.info("Unable to fetch registry value for sCVCWebServiceUrl")

        finally:
            if value is not None and value != '':
                return value.strip()
            return None

    def _get_unix_registry(self, instance, category, key_name):
        """
        Reads the registry value from the given path

        Args:
            instance    (str)   --  Instance name like Instance001

            category    (str)   -- Category the key belongs to
                                    Example: EventManager

            key_name    (str)   -- Registry key name

        """
        value = None
        cmd = subprocess.Popen("id -u", stdout=subprocess.PIPE, shell=True)
        user_id, _ = cmd.communicate()
        user_id = int(user_id)
        reg_path = "/etc/CommVaultRegistry/Galaxy"
        if user_id != 0:
            home_cmd = subprocess.Popen("echo $HOME", stdout=subprocess.PIPE, shell=True)
            home_path, _ = home_cmd.communicate()
            home_path = home_path.decode().rstrip('\n')
            temp_reg_path = f"{home_path}/CommVaultRegistry/Galaxy"

            if os.path.exists(temp_reg_path):
                reg_path = temp_reg_path

        reg_path = f"{reg_path}/{instance}/{category}/.properties"

        if not os.access(reg_path, 4):
            return ''
        if os.path.exists(reg_path):
            with open(reg_path, 'r') as rfile:
                content = rfile.readlines()

            for line in content:
                if line.startswith(key_name):
                    value = line.split(' ')[1]
                    try:
                        value = int(value)
                    except Exception:
                        pass

                    break

        return value
