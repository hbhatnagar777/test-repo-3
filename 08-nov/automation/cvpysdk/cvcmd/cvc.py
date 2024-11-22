"""
Main File for performing Commandline parsing provide a CMDLINE structure COMMCELL Operations
"""

import os
import os.path
import re
import argparse
from cmd import Cmd
import getpass
import pickle
import platform
import shlex
import socket
import sys
import warnings
import subprocess
import backup
import browse
from cvpysdk import commcell
from cvpysdk.exception import SDKException
import jobs
import logger
import subclient
import restore
import SimpanaDefaults
import datetime
from entity import Entity
import urllib3


def get_version():
    """Gets the version of the cvcmd python package from __init__.py file."""
    root = os.path.dirname(__file__)
    version = re.compile(r'''__version__ = ['"]([0-9.]+)['"]''')
    init = open(os.path.join(root, '__init__.py')).read()
    return version.search(init).group(1)


def process_env_variables():
    """
    Function to return configure, backup, recover and restore overwrite flags after reading environment variables.
    By default, configure, backup and recover flags are set to 1 and overwrite flag is set to 0.

    Returns:
            Configure, backup, recover and restore overwrite flags where each flag is 0 or 1
    """
    env_variables = os.environ

    configure_flag = bool(int(env_variables.get('CVC_CONFIGURE', '1')))
    backup_flag = bool(int(env_variables.get('CVC_BACKUP', '1')))
    recover_flag = bool(int(env_variables.get('CVC_RECOVER', '1')))
    overwrite_flag = bool(int(env_variables.get(
        'CVC_RESTORE_DEFAULT_OVERWRITE', '0')))
    show_deleted_flag = bool(int(env_variables.get(
        'CVC_DEFAULT_SHOW_DELETED', '0')))
    https_flag = bool(int(env_variables.get('CVC_HTTPS', '0')))
    restrict_alt_client_flag = bool(
        int(env_variables.get('CVC_RESTRICT_ALT_CLIENT', '0')))
    cvc_ca_bundle = env_variables.get("CVC_CA_BUNDLE")

    return (
        configure_flag,
        backup_flag,
        recover_flag,
        overwrite_flag,
        show_deleted_flag,
        https_flag,
        restrict_alt_client_flag,
        cvc_ca_bundle
    )


# Retrevie configure, backup, recover, restore overwrite and https flags
try:
    (cvc_configure, cvc_backup, cvc_recover, cvc_restore_default_overwrite,
     cvc_default_show_deleted, cvc_https, cvc_restrict_alt_client, cvc_ca_bundle) = process_env_variables()
except Exception as e:
    print("Error while process environment variables: %s" % str(e))
    exit(2)


def print_env_variables():
    LOG.info('Environment variables flags : ')
    LOG.info('\t CVC_CONFIGURE : ' + str(cvc_configure))
    LOG.info('\t CVC_BACKUP : ' + str(cvc_backup))
    LOG.info('\t CVC_RECOVER : ' + str(cvc_recover))
    LOG.info('\t CVC_RESTORE_DEFAULT_OVERWRITE : ' +
             str(cvc_restore_default_overwrite))
    LOG.info('\t CVC_DEFAULT_SHOW_DELETED : ' +
             str(cvc_default_show_deleted))
    LOG.info('\t CVC_HTTPS : ' + str(cvc_https))
    LOG.info('\t CVC_RESTRICT_ALT_CLIENT : ' + str(cvc_restrict_alt_client))


def get_object(tokenpath, encKey):
    '''
    Given tokenpath and key,the function returns commcell_object
    Args:
            Tokenpath
            Encryption key
    Returns:
            Commcell object
    '''
    pickledData = None
    cipherData = None
    commcell_object = None
    if os.path.isfile(tokenpath):
        try:
            encKey = bytes(encKey, 'utf-8')
            cipherObject = AES.new(encKey, AES.MODE_EAX, b'This is an IV456')
            infoFile = open(tokenpath, "rb")
            cipherData = infoFile.read()
            pickledData = cipherObject.decrypt(cipherData)
            commcell_object = pickle.loads(pickledData)
            infoFile.close()
        except pickle.UnpicklingError:
            LOG.error("Login info cannot be loaded. Exiting")
            print("Operation failed. Login info cannot be loaded. Exiting")
            exit(2)
        except Exception as tokenfile_exception:
            LOG.error(
                "Error while loading the login info. Exception: " +
                str(tokenfile_exception))
            print(
                "Operation failed. Error while loading the login info.Exception: " +
                str(tokenfile_exception))
            exit(2)
    else:
        LOG.error("Session not found. Please login.")
        print("Session not found. Please login.")
        exit(2)
        
    if not commcell_object._cvpysdk_object._verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
    return commcell_object


def print_log_lines(loglines):
    '''Prints loglines
    Args:
            Log lines
    '''
    for i in loglines:
        if i[0] == "i":
            LOG.info(i[1])
        else:
            LOG.error(i[1])


def check_instance(instance_name):
    '''Method to check if instance provided by user is a valid instance
    Args :
            Instance name
    Returns :
            Flag :
                    True indicates instance is valid
                    False indicates instance is invalid
    '''
    simpana_default_obj = SimpanaDefaults.Simpanadefaults()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        (flag, loglines) = simpana_default_obj.check_valid_instance(instance_name)
    return (flag, loglines)

def check_vsa_instance(agent_name, instance_name):	
    '''Method to check whether Virtual Server is used or not
    1.) Check if flag is passed for agent_name
    2.) Check if Virtual server registry is present
    Returns :	
            True when nAgentType = 2	
            False when nAgentType != 2	
    '''	
    if agent_name == 'vsa':
        print("Using Virtual Server agent operations based on flag {0}".format(agent_name))
        return True
    elif agent_name == 'fs':
        print("Using File System Agent operations based on flag {0}".format(agent_name))
        return False
    
    try:
        LOG.info('Checking nAgentType registry in CommvaultSDKForPython')	
    except:
        pass
    vsa_guid = ""	
    if platform.system() == 'Linux':
        simpana_default_obj = SimpanaDefaults.Simpanadefaults()	
        value = simpana_default_obj._get_unix_registry(instance_name, 'CommvaultSDKForPython', 'nAgentType')
        return True if value == 2 else False
    return False

def check_copy_precedence_registry(instance_name):
    '''Method to check whether regkey for copy precedence is set or not
    Args :
            Instance name
    Returns :
            value indicates which copy precedence be used during browse
            None indicates copy precedence not be used during browse
    '''	
    LOG.info('Checking nCopyPrecedence registry in CommvaultSDKForPython')	
    simpana_default_obj = SimpanaDefaults.Simpanadefaults()	
    value = simpana_default_obj._get_unix_registry(instance_name, 'CommvaultSDKForPython', 'nCopyPrecedence')
    if value:
        return value
    return None

def dest_inplace_restore(path):
    '''Method to get destination path from source path for inplace restore conversion to out-of-place restores
    Args :
            Source Path(list)
    Returns:
            destination path(str)
    '''
    if len(path) > 1:
        return ''
    dest_path_from_source = path[0]
    dest_path_from_source = dest_path_from_source.strip('/').rsplit('/',1)
    if len(dest_path_from_source) == 1:
        dest_path_from_source1 = '/'
    else:
        dest_path_from_source1 = f"/{dest_path_from_source[0]}"
    return dest_path_from_source1

def is_subpath(dir1, dir2):
    '''Method to check if dir1 is subpath of dir2
    Args :
            dir1(str)
            dir2(str)
    Returns:
            true if dir1 is subpath of dir2
            false if dir1 is not subpath of dir2
    '''
    if dir1.startswith(dir2):
        return True
    return False

def get_token_path(instanceName):
    '''If token file path is not passed, simpana installation directory path is considered as tokenpath.
    If no local commvault installation exists, ask the user to provide path in the command and exit the program.
    '''
    tokenpath = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        (status1, csName, loglines, is_interface_list) = simpana_default_obj.local_cs_detection(instanceName)
        print_log_lines(loglines)
        if status1 is True:
            (status2, installation_path,
             loglines) = simpana_default_obj.simpana_installation_path(instanceName)
            print_log_lines(loglines)
            if status2 is True:
                if platform.system() == 'Linux':
                    if os.access(installation_path, os.W_OK):
                        tokenpath = installation_path + \
                            "/.cvcsession." + str(os.getuid())
                    else:
                        from pathlib import Path
                        tokenpath = str(Path.home()) + \
                            "/.cvcsession." + str(os.getuid())
                elif platform.system() == 'Windows':
                    tokenpath = installation_path + '\\' + "cvcsession." + getpass.getuser()
                else:
                    print("Operation failed. Unsupported OS. Exiting")
                    LOG.error("Unsupported OS. Exiting")
                    exit(2)
            else:
                print("Operation failed. Error in assigning token file path ")
                LOG.error("Error in assigning token file path ")
                exit(2)
        else:
            LOG.error("No Local Commvault Installation. Its mandatory "
                      "to pass the token file path as commandline argument.")
            print("Operation failed. No Local Commvault Installation. Its mandatory "
                  "to pass the token file path as commandline argument.")
            exit(2)
    if tokenpath:
        return tokenpath
    else:
        exit(2)


def get_logging_path(instanceName, log_file_path):
    status = False
    log_path = ''
    response = None
    response_2 = None

    try:
        if log_file_path:
            if not os.access(log_file_path, os.W_OK):
                print("User does not have permission to write logs on {0}".format(log_file_path))
                exit(1)
            else:
                if os.path.isfile(log_file_path):
                    log_path = os.path.dirname(log_file_path)
                else:
                    log_path = log_file_path
                status = True

        else:
            if platform.system() == 'Linux' or platform.system() == 'OS400':
                userHomeDir = os.path.expanduser('~')
                log_path = userHomeDir
                log_file = os.path.join(log_path, 'cvc', 'cvc.log')
                if (os.path.exists(log_file) and not os.access(log_file, os.W_OK)) or (
                        not os.access(log_path, os.W_OK)):
                    log_path = os.getcwd()
                    log_file = os.path.join(log_path, 'cvc.log')
                    if (os.path.exists(log_file) and not os.access(log_file, os.W_OK)) or (
                            not os.access(log_path, os.W_OK)):
                        if not userHomeDir or userHomeDir =='/':
                            print("User home directory not found & User does not have permission for writing logs on current working directory, please specify a path for logging")
                            exit(1)
                        print('User does not have permission for writing logs on {} or on current working directory, '
                              'please pass a valid log file path'.format(userHomeDir))
                        exit(1)
                else:
                    if not userHomeDir or userHomeDir =='/':
                        print("User home directory not found, please specify a path for logging")
                        exit(1)
                    log_path = '{}/cvc'.format(userHomeDir)
                    if not os.path.exists(log_path):
                        os.makedirs(log_path)
                        os.chmod(log_path, 0o700)
                status = True
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    output, _, response = simpana_default_obj.local_cs_detection(instanceName)
                    if output:
                        output, logging_path, response_2 = simpana_default_obj.simpana_logging_path(instanceName)
                        if output:
                            log_path = logging_path
                            status = True

        if platform.system() == 'Linux' or platform.system() == 'OS400':
            if log_file_path:
                os.environ['CV_CVC_LOG_FILE'] = '{}/qcommand'.format(log_path)
            else:
                output, logging_path, response_2 = simpana_default_obj.simpana_logging_path(instanceName)
                if output:
                    if(os.path.exists(logging_path) and os.access(logging_path, os.W_OK)):
                        os.environ['CV_CVC_LOG_FILE'] = '{}/qcommand'.format(logging_path)
                    else:
                        os.environ['CV_CVC_LOG_FILE'] = '{}/qcommand'.format(log_path)
                else:
                    os.environ['CV_CVC_LOG_FILE'] = '{}/qcommand'.format(log_path)
            lock_folder = '{}/locks'.format(log_path)
            if not os.path.exists(lock_folder):
                os.makedirs(lock_folder)
                os.chmod(lock_folder, 0o700)
    except Exception as exp:
        print("Failed to set logging path\nError: {0}".format(exp))
        exit(1)

    if status:
        return status, log_path, response, response_2
    else:
        print("Failed to set logging path")
        exit(1)


def check_qlogin_localadmin_chosen(self, commcell_clientName):

    return_flag = True

    # Check if qlogin localadmin is chosen
    if self._qlogin_local_client:
        if commcell_clientName is None:
            commcell_clientName = self._qlogin_local_client
            self._LOG.info(
                "Setting Client Name as the Local Client %s" %
                commcell_clientName)
        elif commcell_clientName == self._qlogin_local_client:
            self._LOG.info(
                "Proceeding with Operation on Local Client %s" %
                commcell_clientName)
        else:
            self._LOG.error(
                "Access denied. Local admin user can operate only on the local client.")
            print("Access denied. Local user can operate only on the local client.")
            return_flag = False

    return (return_flag, commcell_clientName)


def check_csname_and_creds(
        commcell_name,
        commcell_instanceName,
        commcell_username,
        commcell_password,
        is_interactive=False):

    return_flag = True
    local_cs_detected = False
    local_client = None
    is_interface_list = False 

    # If the comcell name is empty, we run local CS detection
    if not commcell_name:
        LOG.info(
            "Since CS name is empty , proceeding to check local commvault detection")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            status, cs_name, log_lines, is_interface_list = simpana_default_obj.local_cs_detection(
                commcell_instanceName)
            print_log_lines(log_lines)
        if status:
            commcell_name = cs_name
            local_cs_detected = True
            if is_interface_list:
                LOG.info("Interface List is detected.")
                LOG.info(f"Interface List : {commcell_name}")
            else:
                LOG.info("Local Commvault Instance is detected.")
                LOG.info(f"WebConsole HostName : {commcell_name}")
        else:
            print("Operation failed. No Local Commvault Instance detected. Please provide a commcell name to proceed further")
            LOG.error(
                "No Local Commvault Instance detected. It is now mandatory to pass the commcell name as commandline argument to proceed further")
            return (
                False,
                commcell_name,
                commcell_username,
                commcell_password,
                local_client,
                is_interface_list)

    # If the username and password are not provided, we try for localadmin
    # login (if applicable)
    if not commcell_username and not commcell_password:

        # if commcell name was provided, we check if it is same as the local cs
        # name
        if not local_cs_detected:
            # fetching the local cs name
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                (status, local_cs_name, log_lines, is_interface_list) = simpana_default_obj.local_cs_detection(
                    commcell_instanceName)
                print_log_lines(log_lines)
            if status:
                LOG.info("Local Commvault Instance is detected.")
                LOG.info(
                    "Checking if the webconsole name provided is same as the local webconsole name.")
                
                if is_interface_list:
                    commcell_name_in_list = False
                    interface_list = local_cs_name.split(',')
                    for interface in interface_list:
                        if socket.getfqdn(commcell_name) == socket.getfqdn(interface):
                            commcell_name_in_list = True
                            break
                    
                    if not commcell_name_in_list:
                        LOG.info(
                            "Local CS Interface List does not contain the webconsole name passed as cmdline argument. \
                                Hence, we cannot proceed with OS authentication.")
                        print(
                            "Operation failed. Please provide the credentials to proceed further.")
                        return (
                            False,
                            commcell_name,
                            commcell_username,
                            commcell_password,
                            local_client,
                            is_interface_list)

                else:
                    if socket.getfqdn(commcell_name) == socket.getfqdn(local_cs_name):
                        LOG.info(
                            "Local commvault webconsole name matches with passed cmdline argument.")
                    else:
                        LOG.info(
                            "Local commvault webconsole name does not match with webconsole name passed as cmdline \
                            argument. Hence, we cannot proceed with OS authentication.")
                        print(
                            "Operation failed. Please provide the credentials to proceed further.")
                        return (
                            False,
                            commcell_name,
                            commcell_username,
                            commcell_password,
                            local_client,
                            is_interface_list)
            else:
                print(
                    "Operation failed. No Local Commvault Instance detected. Please provide the credentials to proceed further.")
                LOG.error(
                    "No Local Commvault Instance detected. It is now mandatory to pass the credentials as argument to proceed further")
                return (
                    False,
                    commcell_name,
                    commcell_username,
                    commcell_password,
                    local_client,
                    is_interface_list)

        # Now, since we have detected local Commvault instance, we now proceed
        # to obtain localadmin credentials
        LOG.info("Proceeding with localadmin authentication.")
        try:
            status, installation_path, log_lines = simpana_default_obj.simpana_installation_path(
                commcell_instanceName)
            if status:
                print_log_lines(log_lines)
                if platform.system() == 'Linux':
                    localadmin_qcommand = subprocess.check_output(
                        str(installation_path) + "/Base/" + "qlogin -localadmin -gt", shell=True)
                elif platform.system() == 'Windows':
                    localadmin_qcommand = subprocess.check_output(
                        '"' + str(installation_path) + r'\Base\qlogin" -localadmin -gt', shell=True)
                else:
                    raise Exception("Unsupported OS")
        except Exception as qlogin_error:
            print("Error while attempting to login with qlogin -localadmin token. Pass username/password as cmdline argument")
            print("Error is %s" % str(qlogin_error))
            return (
                False,
                commcell_name,
                commcell_username,
                commcell_password,
                local_client,
                is_interface_list)

        # Qlogin was successful and now we set all the requied parameters
        print("Logging in as local user.")
        LOG.info("Operation will use localadmin authentication.")
        token = localadmin_qcommand.decode()
        commcell_username = 'admin'
        commcell_password = {'Authtoken': token}
        status, local_client, loglines = simpana_default_obj.local_client_detection(
            commcell_instanceName)
        print_log_lines(loglines)

    # If only the password is missing
    # For interactive : ask the user to provide the password
    # For non-interactive : throw an error
    elif commcell_username and not commcell_password:
        if is_interactive:
            print("Please enter the password : ")
            commcell_password = getpass.getpass()
        else:
            print("Operation failed. Password not provided.")
            LOG.error("Operation failed. Password not provided.")
            return (
                False,
                commcell_name,
                commcell_username,
                commcell_password,
                local_client,
                is_interface_list)

    # If only the user name is missing - throw an error
    elif not commcell_username and commcell_password:
        print("Operation failed. Username not provided.")
        LOG.error("Operation failed. Username not provided.")
        return (
            False,
            commcell_name,
            commcell_username,
            commcell_password,
            local_client,
            is_interface_list)

    return (
        True,
        commcell_name,
        commcell_username,
        commcell_password,
        local_client,
        is_interface_list)


def _login_using_cvpysdk(
        webconsole_hostname,
        commcell_username=None,
        commcell_password=None,
        force_https=False,
        allow_http=False,
        certificate_path=None,
        log=None,
        is_interface_list=False,
        **kwargs):
        """Initialize the Commcell object with the values required for doing the API operations.

            Args:
                webconsole_hostname     (str)   --  webconsole host Name / IP address

                    e.g.:

                        -   webclient.company.com

                        -   xxx.xxx.xxx.xxx


                commcell_username       (str)   --  username for log in to the commcell console

                    default: None


                commcell_password       (str)   --  plain-text password for log in to the console

                    default: None

                force_https             (bool)  --  boolean flag to specify whether to force the
                connection to the commcell only via HTTPS

                if the flag is set to **False**, SDK first tries to connect to the commcell via
                HTTPS, but if that fails, it tries to connect via HTTP

                if flag is set to **True**, it'll only try via HTTPS, and exit if it fails

                    default: False


                certificate_path        (str)   --  path of the CA_BUNDLE or directory with
                certificates of trusted CAs (including trusted self-signed certificates)

                    default: None

                    **Note** If certificate path is provided, force_https is set to True

                log     (obj)   -- Object of logger class

                is_interface_list         (bool)  --  boolean flag to specify whether webconsole_hostname
                has a single CS-hostname or a comma seperated list of Interfaces of the CS. 

                if the flag is set to **False** webconsole_hostname has a single hostname. 
                Login fails if we are unable to connect to it

                If flag is set to **True** webconsole_hostname is a comma seperated list of interfaces of a CS. 
                We try connecting to each one of these interfaces untill a connection is successful 
                or login fails if we are not able to connect to any interface in the list.
                
                **kwargs:
                    web_service_url      (str)   --  url of webservice for the api requests
                
            Returns:
                object  -   instance of this class

            Raises:
                SDKException:
                    if the web service is down or not reachable

                    if no token is received upon log in

        """
        commcell_obj = None
        web_service_url = kwargs.get("web_service_url", None)
        if not is_interface_list:
            try:
                if certificate_path or force_https:
                    try:
                        commcell_obj = commcell.Commcell(
                            webconsole_hostname=webconsole_hostname,
                            commcell_username=commcell_username,
                            commcell_password=commcell_password,
                            force_https=force_https,
                            certificate_path=certificate_path,
                            web_service_url=web_service_url
                        )
                    except Exception:
                        if force_https and not allow_http:
                            raise

                if not commcell_obj:
                    commcell_obj = commcell.Commcell(
                        webconsole_hostname=webconsole_hostname,
                        commcell_username=commcell_username,
                        commcell_password=commcell_password,
                        verify_ssl=False,
                        web_service_url=web_service_url
                    )

            except Exception as login_exception:
                log.error("Error Encountered during Login : %s", login_exception)
                log.error("Login failed for user %s", commcell_username)
                print(f"Error in login : {login_exception}")
                exit(2)
        else:
            interface_list = webconsole_hostname.split(',')
            exception_count = 0

            try:
                if certificate_path or force_https:
                    for interface in interface_list:
                        try:
                            commcell_obj = commcell.Commcell(
                                webconsole_hostname=interface,
                                commcell_username=commcell_username,
                                commcell_password=commcell_password,
                                force_https=force_https,
                                certificate_path=certificate_path,
                                web_service_url=web_service_url
                            )
                            
                            if commcell_obj:
                                break
                            
                        except Exception as login_exception:
                            exception_count += 1
                            if force_https and exception_count == len(interface_list) and not allow_http:
                                raise                        
                            else:
                                if isinstance(login_exception, SDKException) and login_exception.exception_module == 'CVPySDK' and login_exception.exception_id == '101':
                                    raise
                                log.error("Error Encountered during Login: %s", login_exception)
                                log.error("Login failed for user: %s Commcell Interface: %s", commcell_username, interface)
                                log.error("Continuing with next interface")
                exception_count = 0
                if not commcell_obj:
                    for interface in interface_list:
                        try:
                            commcell_obj = commcell.Commcell(
                                webconsole_hostname=interface,
                                commcell_username=commcell_username,
                                commcell_password=commcell_password,
                                verify_ssl=False,
                                web_service_url=web_service_url
                            )
                            
                            if commcell_obj:
                                break
                            
                        except Exception as login_exception:
                            exception_count += 1
                            if exception_count == len(interface_list):
                                raise
                            else:
                                
                                if isinstance(login_exception, SDKException) and login_exception.exception_module == 'CVPySDK' and login_exception.exception_id == '101':
                                    raise
                                log.error("Error Encountered during Login : %s", login_exception)
                                log.error("Login failed for user %s Commcell Interface %s", commcell_username, interface)
                                log.error("Continuing with next interface")
            
            except Exception as login_exception:
                log.error("Error Encountered during Login : %s", login_exception)
                log.error("Login failed for user %s", commcell_username)
                print(f"Error in login: {login_exception}")
                exit(2)

        log.info(commcell_obj)
        log.info("Login Successful")
        print("Login Successful")
        return commcell_obj


class Noninteractive():
    """
    Class is responsible for parsing the commandline arguments and running operations for non-interactive approach
    Methods  :
    login_ni : Method to login to webconsole server
    backup_ni : Method to do backup on mentioned subclient
    restore_ni : Method to perform in-place, out-of-place and PIT restore at subclient Level
    job_status_ni : Method to obtain job status for a given Job ID
    logout_ni : Method to logout of webconsole server
    subclient_create_ni : Method to create a subclient
    subclient_update_ni : Method to update the content or filter list of subclient
    subclient_delete_ni : Method to delete a subclient
    browse_ni : Method to browse backed up files
    """

    def __init__(self):
        """
        Initialize Noninteractive Class Object
        """
        self._commcell_obj = None
        self._commcell_username = ""
        self._commcell_clientName = ""
        self._commcell_instanceName = ""
        self._commcell_agent = ""
        self.VSA_AGENT = "virtual server"

    def login_ni(
            self,
            tokenpath,
            commcell_username,
            commcell_password,
            commcell_name,
            commcell_instanceName,
            commcell_key,
            force_https,
            allow_http,
            certificate_path,
            agent_type,
            **kwargs):
        """
        usage: PROG login [-h] -u USERNAME -p PASSWORD [-cs COMMCELLNAME]
                          [-i INSTANCENAME] [-k KEY] [-f TOKENFILEPATH]
                          [-lf LOGFILEPATH] [-at AGENTTYPE]
        optional arguments:
        -h, --help        show this help message and exit
        -u USERNAME       Username
        -p PASSWORD       Password
        -cs COMMCELLNAME  Commcell Name
        -i INSTANCENAME   Instance Name
        -k KEY            key-16 characters
        -f TOKENFILEPATH  Token File Path
        -lf LOGFILEPATH   Log File Path
        -at AGENTTYPE      Commcell agent type
        """
        global cvc_https
        self._commcell_username = commcell_username
        simpana_default_obj = SimpanaDefaults.Simpanadefaults()
        web_service_url = kwargs.get("web_service_url", None)

        # check if the instance passed by user is valid
        instance_log_lines = []
        if commcell_instanceName:
            flag, instance_log_lines = check_instance(commcell_instanceName)
            print_log_lines(instance_log_lines)
            if not flag:
                print("Operation failed. Instance with the provided name does not exist")
                return
        else:
            commcell_instanceName = 'Instance001'
        self._commcell_instanceName = commcell_instanceName

        flag, commcell_name_list, commcell_username, commcell_password, local_client, is_interface_list = check_csname_and_creds(
            commcell_name,
            commcell_instanceName,
            commcell_username,
            commcell_password)
        if not flag:
            return

        self._commcell_obj = _login_using_cvpysdk(
            webconsole_hostname=commcell_name_list,
            commcell_username=commcell_username,
            commcell_password=commcell_password,
            force_https=force_https,
            allow_http=allow_http,
            certificate_path=certificate_path,
            log=LOG,
            is_interface_list=is_interface_list,
            web_service_url=web_service_url
        )

        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        if is_VSA:
            LOG.info("Using VSA related ops")
            Entity.client = self._commcell_obj.clients.get(local_client)
            vsa_guid = Entity.client.vm_guid
            if vsa_guid is None:
                print("Operation failed. Could not find GUID for VM ", local_client)
                exit(2)

        pickledData = None
        cipherData = None
        try:
            encKey = bytes(commcell_key, 'utf-8')
            cipherObject = AES.new(encKey, AES.MODE_EAX, b'This is an IV456')
            pickledData = pickle.dumps(self._commcell_obj)
            cipherData = cipherObject.encrypt(pickledData)
            infoFile = open(tokenpath, "wb")
            infoFile.write(cipherData)
            infoFile.close()
            if platform.system() == 'Linux' or platform.system() == 'OS400':
                os.chmod(tokenpath, 0o600)
        except pickle.PicklingError:
            print("Operation failed. Error while logging in.")
            LOG.error("Login info cannot be stored. Exiting")
            exit(2)
        except Exception as tokenfile_exception:
            print(
                "Operation failed. Error while logging in." +
                str(tokenfile_exception))
            LOG.error("Error while saving the login info. Exiting")
            exit(2)
        return

    def logout_ni(self, tokenpath, commcell_key):
        """
        usage: PROG logout [-h] [-i INSTANCENAME] [-k KEY] [-tf TOKENFILEPATH]
        optional arguments:
        -h, --help         show this help message and exit
        -i INSTANCENAME    Instance Name
        -k KEY             key-16 characters
        -tf TOKENFILEPATH  Token File Path
        """
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Error while logging out.")
            exit(2)
        self._commcell_obj = commcell_object
        try:
            self._commcell_obj.logout()
            if os.path.isfile(tokenpath):
                os.remove(tokenpath)
            LOG.info("SuccessFully Logged out of the commserve")
            print("Logout Successful")
        except NameError as name_error:
            name_error = str(name_error)
            LOG.error("NameError Raised :" + name_error)
            print("Operation failed. Logout Unsuccessful: " + name_error)
            exit(2)

    def backup_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            commcell_subclientId,
            backup_type,
            contentPath,
            directiveFilePath,
            commcell_instanceName,
            commcell_agentName,
            commcell_key,
            outputFilePath,
            loggingPath,
            agent_type):
        """
        usage: cvc.py backup [-h] [-c CLIENTNAME]
                                 [-scid SUBCLIENTID | -sc SUBCLIENTNAME]
                                 [-bk BACKUPSETNAME]
                                 [-l {full,incremental,synthetic_full,differential}]
                                 [-path [CONTENTPATH [CONTENTPATH ...]] | -df
                                 DIRECTIVEFILEPATH] [-i INSTANCENAME] [-a AGENTNAME]
                                 [-k KEY] [-tf TOKENFILEPATH] [-of OUTPUTFILEPATH]
                                 [-lf LOGFILEPATH] [-at AGENTTYPE]
                                 [path]
        positional arguments:
        path                  File or folder to backup with default options. 
                              Other user provided options will be ignored and default values will be used.                              
                                        
        optional arguments:
        -h, --help            show this help message and exit
        -c CLIENTNAME         Client Name
        -scid SUBCLIENTID     Subclient ID
        -sc SUBCLIENTNAME     Subclient Name
        -bk BACKUPSETNAME     Backupset Name
        -l {full,incremental,synthetic_full,differential}
                                        Backup Level
        -path [CONTENTPATH [CONTENTPATH ...]]
                                        Adhoc Backup Path
        -df DIRECTIVEFILEPATH
                                        Directive File Path
        -i INSTANCENAME       Instance Name
        -a AGENTNAME          Agent Name
        -k KEY                key-16 characters
        -tf TOKENFILEPATH     Token File Path
        -of OUTPUTFILEPATH    Output File Path
        -lf LOGFILEPATH       Log File Path
        -at AGENTTYPE      Commcell agent type
        """
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        if is_VSA:
            print("VSA Backup operations are not allowed in CVC")
            exit(2)
        adhoc = 0
        if contentPath is not None or directiveFilePath is not None:
            LOG.info("Adhoc Backup Operation")
            adhoc = 1
        else:
            LOG.info("Backup Operation")

        if cvc_restrict_alt_client and commcell_clientName:
            print("Access denied. Local user can operate only on the local client.")
            LOG.error(
                "Operation failed. Passing client name / destination client is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
            exit(2)

        self._commcell_agent = commcell_agentName
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object
        common_object = CsCommon(self._commcell_obj)
        checkAdhocClient = 0
        if adhoc:
            if commcell_clientName:
                checkAdhocClient = 1
        if checkAdhocClient:
            adhocFlag1 = common_object.check_client_exists_in_cs(
                commcell_clientName)
            if adhocFlag1:
                adhocFlag2 = common_object.check_adhoc_client(
                    commcell_clientName)
                if not adhocFlag2:
                    LOG.error(
                        "Operation failed. Client passed is not a local instance. Adhoc operation cannot be performed")
                    print(
                        "Operation failed. Client passed is not a local instance. Adhoc operation cannot be performed")
                    exit(2)
                else:
                    self._commcell_clientName = commcell_clientName
            else:
                print("Operation failed. Client passed is not part of logged in CS.")
                exit(2)
        else:
            LOG.info("Deciding client for the operation")
            clientName = None
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                LOG.info("Clientname is decided : %s" % clientName)
                self._commcell_clientName = clientName
            else:
                LOG.error("Pass correct Clientname as argument")
                print("Operation failed. Pass correct Clientname as argument")
                exit(2)
        adHocDict = None
        if adhoc:
            backup_type = 'Incremental'
            if contentPath is not None:
                LOG.info(
                    "Adhoc Backup to be run on the following content :" +
                    str(contentPath))
                adHocDict = {
                    "adhoc_backup": True,
                    "adhoc_backup_contents": contentPath}
            elif directiveFilePath is not None:
                adHocDict = {
                    "adhoc_backup": True,
                    "directive_file": directiveFilePath}
        flag = 0
        backup_error = ''
        try:
            backup_obj = backup.Backup(
                loggingPath,
                self._commcell_obj,
                backup_type,
                self._commcell_clientName,
                self._commcell_agent,
                commcell_backupSetName,
                commcell_subClientName,
                commcell_subclientId)
            if adhoc:
                (flag, jobid) = backup_obj.adHocBackup(
                    adHocDict, outputFilePath)
            else:
                (flag, jobid) = backup_obj.backup(outputFilePath)
        except NameError as name_error:
            name_error = str(name_error)
            LOG.error("NameError Raised :" + name_error)
            backup_error = name_error
            flag = 1
            exit(2)
        except Exception as backup_exception:
            flag = 1
            backup_exception = str(backup_exception)
            LOG.error("Exception Raised in Backup Class : %s" %
                      backup_exception)
            backup_error = backup_exception
            exit(2)
        finally:
            if flag == 0:
                LOG.info(
                    "{0}Backup Initiated Successfully. Job ID:{1} ".format(
                        'Adhoc ' if adhoc else '', str(jobid)))
            else:
                print(
                    "{0}Backup Initiation encountered Error. {1}".format(
                        'Adhoc ' if adhoc else '',
                        backup_error))
                exit(2)

    def restore_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            sourcepath,
            restorefilelist,
            commcell_destclient,
            commcell_destpath,
            commcell_fromTime,
            commcell_toTime,
            versions,
            unconditional_overwrite,
            commcell_instanceName,
            commcell_agentName,
            commcell_key,
            outputFilePath,
            loggingPath,
            browse_filter,
            copy_precedence,
            agent_type,
            **kwargs):
        """
        usage: cvc.py restore [-h] [-c CLIENTNAME] [-sc SUBCLIENTNAME]
                              [-bk BACKUPSETNAME] [-path SOURCEPATH [SOURCEPATH ...] |
                              -l RESTOREFILELIST] [-dc DESTCLIENT] [-dp DESTPATH]
                              [-ftime FROMTIME] [-ttime TOTIME] [-versions VERSIONS]
                              [-uo {True,False}] [-i INSTANCENAME] [-a AGENTNAME]
                              [-k KEY] [-tf TOKENFILEPATH] [-of OUTPUTFILEPATH]
                              [-lf LOGFILEPATH]
                              [-filter BROWSE_FILTER [BROWSE_FILTER ...]] [-at AGENTTYPE]
                              [path] [-sd {True,False}]

        positional arguments:
          path                  File or folder to restore with default options. 
                                Other user provided options will be ignored and default values will be used.
                                
        optional arguments:
          -h, --help            show this help message and exit
          -c CLIENTNAME         Client Name
          -sc SUBCLIENTNAME     Subclient Name. Name to be passed even in case of
                                default subclient
          -bk BACKUPSETNAME     Backupset Name
          -path SOURCEPATH [SOURCEPATH ...]
                                Source Paths
          -l RESTOREFILELIST    Restore File List. The file should be present on the
                                machine from where command is run.
          -dc DESTCLIENT        Destination Client
          -dp DESTPATH          Destination Path
          -ftime FROMTIME       The start time of the backup window that you specify for a point-in-time restore operation. The format is yyyy-mm-dd hh:mm:ss.
          -ttime TOTIME         The end time of the backup window that you specify for a point-in-time restore operation. The format is yyyy-mm-dd hh:mm:ss.
          -versions VERSIONS    Versions to be restored. "All" or "all" or list of
                                version numbers such as "1,2,5"
          -uo {True,False}      Unconditional Overwrite {True,False}. False by default
          -i INSTANCENAME       Instance Name
          -a AGENTNAME          Agent Name
          -k KEY                key-16 characters
          -tf TOKENFILEPATH     Token File Path
          -of OUTPUTFILEPATH    Output File Path
          -lf LOGFILEPATH       Log File Path
          -filter BROWSE_FILTER [BROWSE_FILTER ...], --browseFilter BROWSE_FILTER [BROWSE_FILTER ...]
                                Browse Filters
          -at AGENTTYPE         Commcell agent type
          -sd {True,False}      Show deleted items {True,False}. Set this to True to restore deleted items. False by default.
        """
        LOG.info("Restore Operation")
        show_deleted = kwargs.get("show_deleted", False)
        self._commcell_agent = commcell_agentName
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object

        if cvc_restrict_alt_client and (
                commcell_clientName is not None or commcell_destclient is not None):
            print("Access denied. Local user can operate only on the local client.")
            LOG.error(
                "Operation failed. Passing client name / destination client is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
            exit(2)

        LOG.info("Deciding client for the operation")
        common_object = CsCommon(self._commcell_obj)
        clientName = None
        (status, clientName) = common_object.check_client_name(
            commcell_clientName, commcell_instanceName)
        if status == 0:
            LOG.info("Clientname is decided : %s" % clientName)
            self._commcell_clientName = clientName
        else:
            LOG.error("Pass correct Clientname as argument")
            print("Operation failed. Pass correct Clientname as argument")
            exit(2)
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        vsa_guid = ''
        if is_VSA:
            self._commcell_agent = self.VSA_AGENT
            Entity.client = self._commcell_obj.clients.get(self._commcell_clientName)
            vsa_guid = Entity.client.vm_guid
            if vsa_guid is None:
                print("Operation failed. Could not find GUID for VM ", self._commcell_clientName)
                exit(2)
        if sourcepath:
            commcell_sourcepath = sourcepath
            restore_paths = commcell_sourcepath
        elif restorefilelist:
            LOG.info("File List Option Chosen")
            filename = str(restorefilelist)
            (status, restore_paths) = common_object.read_file_list(filename)
            if status is True:
                LOG.info("Backup paths fetched successfully from file")
            else:
                LOG.error("Backup paths could not be fetched from file")
                print("Operation failed. Error while reading filelist")
                exit(2)
        else:
            print("Insufficient Parameters for Performing restore Operation : either specify the directory path or RestoreFile which contains the list of items to be restored")
            LOG.error("Operation failed. Insufficient Parameters for Performing restore Operation : either specify the directory path or RestoreFile which contains the list of items to be restored")
            exit(1)

        options = {}
        options['no_image'] = show_deleted
        # Find out the versions to be restored. By default, latest version is
        # restored.
        try:
            if versions is not None:
                if versions.lower() == "all":
                    options = {'all_versions': True}
                else:
                    versionList = versions.split(',')
                    for item in versionList:
                        if item.isdigit() is False:
                            LOG.error("Version numbers must be digits only")
                            print(
                                "Operation failed. Incorrect format of version numbers")
                            exit(2)
                    versionList1 = list(map(int, versionList))
                    options = {'versions': versionList1}
        except Exception as version_fetch_exception:
            version_fetch_exception = str(version_fetch_exception)
            LOG.error(
                "Error in fetching version information" +
                version_fetch_exception)
            print("Operation failed. Error in fetching version information. Exiting")
            exit(2)

        if browse_filter:
            xml_string = "<?xml version='1.0' encoding='UTF-8'?><databrowse_Query type=\"0\" queryId=\"0\"><whereClause connector=\"0\"><criteria field=\"0\"><values val=\"{0}\"/></criteria></whereClause><dataParam><sortParam ascending=\"1\"><sortBy val=\"38\" /><sortBy val=\"0\" /></sortParam><paging firstNode=\"0\" pageSize=\"1000\" skipNode=\"0\" /></dataParam></databrowse_Query>"
            browse_filter_string = ""
            for browse_filter_element in browse_filter:
                browse_filter_string = "{0}{1}{2}".format(
                    browse_filter_string,
                    " OR " if browse_filter_string != "" else "",
                    browse_filter_element)
            xml_string = xml_string.format(browse_filter_string)
            options["browse_filters"] = [xml_string]

        options['cvcBrowse'] = True

        flag = 1
        restore_error = ''

        if copy_precedence:
            LOG.info("Copy precedence set to " + str(copy_precedence))

        if platform.system() == "Linux":
            if os.geteuid() != 0:
                if is_VSA:
                    paths = []
                    for path in restore_paths:
                        path = '\\{0}{1}'.format(vsa_guid.rstrip("\n"), path.replace('/', '\\'))
                        paths.append(path)
                    restore_paths = paths
                rcode = common_object.restore_non_root_user(
                    restore_paths,
                    self._commcell_clientName,
                    self._commcell_agent,
                    commcell_instanceName,
                    commcell_backupSetName,
                    commcell_subClientName,
                    commcell_destclient,
                    commcell_destpath,
                    commcell_fromTime,
                    commcell_toTime,
                    outputFilePath,
                    options,
                    unconditional_overwrite,
                    copy_precedence,
                    is_vsa=is_VSA,
                    tempPath=loggingPath)
                if rcode:
                    LOG.error("Restore job encountered error")
                    print("Restore job encountered error")
                    exit(2)
                else:
                    exit(0)
        try:
            LOG.info("while creating main object for restore")
            restore_obj = restore.Restore(
                package_instance=commcell_instanceName,
                commcell_object=self._commcell_obj,
                client_name=self._commcell_clientName,
                agent_name=self._commcell_agent,
                backupset_name=commcell_backupSetName,
                subclient_name=commcell_subClientName,
                logger_object=LOG
            )
            LOG.info("created main object for restore")
            # Checks if it is In-Place or Out-of-Place Restore , accordingly
            # invokes the method
            if (commcell_destclient is not None):
                if commcell_destpath is None:
                    LOG.error(
                        "Destination Path is mandatory for Out of place restore.Pass it in CMDLINE")
                    print(
                        "Operation failed. Destination Path is mandatory for Out of place restore.Pass it in CMDLINE")
                    exit(2)
                else:
                    LOG.info("Out of place restore ")
                    flag, jobid = restore_obj.restore_out_of_place(
                        paths=restore_paths,
                        destination_client=commcell_destclient,
                        destination_path=commcell_destpath,
                        from_time=commcell_fromTime,
                        to_time=commcell_toTime,
                        output_file_path=outputFilePath,
                        fs_options=options,
                        unconditional_overwrite=unconditional_overwrite,
                        copy_precedence=copy_precedence,
                        vsa_guid=vsa_guid)
            else:
                if commcell_destpath is None:
                    if is_VSA:
                        dest_path = dest_inplace_restore(restore_paths)
                        if dest_path == '':
                            print("In-Place restore is not supported with multiple source paths. Please provide destination path manually.")
                            exit(2)
                        else:
                            LOG.info(
                                "Proceeding with restore on source client with destination path : "+ str(dest_path))
                            LOG.info("Out of place restore ")
                            flag, jobid = restore_obj.restore_out_of_place(
                                paths=restore_paths,
                                destination_client=self._commcell_clientName,
                                destination_path=dest_path,
                                from_time=commcell_fromTime,
                                to_time=commcell_toTime,
                                output_file_path=outputFilePath,
                                fs_options=options,
                                unconditional_overwrite=unconditional_overwrite,
                                copy_precedence=copy_precedence,
                                vsa_guid=vsa_guid)
                    else:
                        LOG.info(
                            "Destination client and Destination path is empty . So proceeding with in-place restore")
                        flag, jobid = restore_obj.restore(
                            paths=restore_paths,
                            from_time=commcell_fromTime,
                            to_time=commcell_toTime,
                            output_file_path=outputFilePath,
                            fs_options=options,
                            unconditional_overwrite=unconditional_overwrite,
                            copy_precedence=copy_precedence,
                            vsa_guid=vsa_guid)
                else:
                    LOG.info(
                        "Proceeding with restore on source client with provided destination path")
                    LOG.info("Out of place restore ")
                    flag, jobid = restore_obj.restore_out_of_place(
                        paths=restore_paths,
                        destination_client=self._commcell_clientName,
                        destination_path=commcell_destpath,
                        from_time=commcell_fromTime,
                        to_time=commcell_toTime,
                        output_file_path=outputFilePath,
                        fs_options=options,
                        unconditional_overwrite=unconditional_overwrite,
                        copy_precedence=copy_precedence,
                        vsa_guid=vsa_guid)
        except NameError as name_error:
            name_error = str(name_error)
            LOG.error("NameError Raised :" + (name_error))
            restore_error = name_error
            flag = 1
            exit(2)
        except Exception as restore_exception:
            restore_exception = str(restore_exception)
            LOG.error(
                "Exception occurred during restore operation : " +
                restore_exception)
            restore_error = restore_exception
            flag = 1
            exit(2)
        finally:
            if flag == 0:
                LOG.info(
                    "Restore Job Initiated successfully. Job ID : " +
                    str(jobid))
            else:
                print("Restore job encountered error. " + restore_error)
                exit(2)

    def job_status_ni(self, tokenpath, commcell_jobId, commcell_key,
                      outputFilePath, loggingPath):
        """
        usage: PROG job_status [-h] -jid JOBID [-i INSTANCENAME] [-k KEY]
                                   [-tf TOKENFILEPATH] [-of OUTPUTFILEPATH]
        optional arguments:
        -h, --help          show this help message and exit
        -jid JOBID          Job ID
        -i INSTANCENAME     Instance Name
        -k KEY              key-16 characters
        -tf TOKENFILEPATH   Token File Path
        -of OUTPUTFILEPATH  Output File Path
        """
        LOG.info("Getting Job Status")
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object
        flag = 1
        try:
            job_obj = jobs.Jobs(
                loggingPath,
                self._commcell_obj,
                commcell_jobId)
            (flag, job_finish_status, job_current_status) = job_obj.get_job_status(
                outputFilePath)
        except Exception as job_status_exception:
            job_status_exception = str(job_status_exception)
            LOG.error(
                "Exception occurred while gettign job status:" +
                job_status_exception)
            print("Operation failed. " + job_status_exception)
            flag = 1
            exit(2)
        finally:
            if flag == 1:
                print("Getting job status failed")
                exit(2)
            else:
                return

    def subclient_create_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            subclient_content,
            subclient_filters,
            subclient_dsp,
            commcell_instanceName,
            commcell_agentName,
            commcell_key,
            loggingPath,
            agent_type):
        """
        Usage for subclient operations
        usage: PROG subclient [-h] (-create | -update | -delete) -c CLIENTNAME
                                  [-a AGENTNAME] [-bk BACKUPSETNAME] -sc SUBCLIENTNAME
                                  [-path PATH] [-excludepath EXCLUDE_PATH] [-dsp DSP]
                                  [-overwrite {True,False}] [-i INSTANCENAME] [-k KEY]
                                  [-tf TOKENFILEPATH] [-at AGENTTYPE]
        optional arguments:
        -h, --help            show this help message and exit
        -create               Create Subclient
        -update               Update Subclient
        -delete               Delete Subclient
        -c CLIENTNAME         Client Name
        -a AGENTNAME          Agent Name
        -bk BACKUPSETNAME     Backupset Name
        -sc SUBCLIENTNAME     Subclient Name
        -path PATH            path
        -excludepath EXCLUDE_PATH
                                        Filter Path(s)
        -dsp DSP              Default Storage Policy
        -overwrite {True,False}
                                        Overwrite {True,False}
        -i INSTANCENAME       Instance Name
        -k KEY                key-16 characters
        -tf TOKENFILEPATH     Token File Path
        -at AGENTTYPE         Commcell agent type
        """
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        if is_VSA:
            print("Subclient creation not allowed for VSA in CVC")
            exit(2)
        self._commcell_agent = commcell_agentName
        LOG.info("Subclient Creation")
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object
        LOG.info("Deciding client for the operation")
        common_object = CsCommon(self._commcell_obj)
        clientName = None
        (status, clientName) = common_object.check_client_name(
            commcell_clientName, commcell_instanceName)
        if status == 0:
            LOG.info("Clientname is decided : %s" % clientName)
            self._commcell_clientName = clientName
        else:
            LOG.error("Pass correct Clientname as argument")
            print("Operation failed. Pass correct Clientname as argument")
            exit(2)

        # check for mandatory arguments
        if subclient_content is None:
            LOG.error("Content was not passed for subclient creation. Exiting")
            print(
                "Operation failed. Content is mandatory for subclient creation. Try again")
            exit(2)
        if subclient_dsp is None:
            LOG.error(
                "Default storage policy was not passed for subclient creation. Exiting")
            print(
                "Operation failed. Default storage policy is mandatory for subclient creation. Try again")
            exit(2)
        LOG.info("Subclient  will be created on below defined contents : ")
        LOG.info(subclient_content)
        flag = 1
        try:
            LOG.info("creation of subclient_operation instance ")
            subc_obj = subclient.SubClient(
                loggingPath,
                self._commcell_obj,
                self._commcell_clientName,
                self._commcell_agent,
                commcell_backupSetName)
            flag = subc_obj.subclient_add(
                commcell_subClientName,
                subclient_dsp,
                subclient_content,
                subclient_filters)
        except Exception as subclient_exception:
            LOG.error("Issue in creating subclient with given content")
            flag = 1
            subclient_exception = str(subclient_exception)
            LOG.error("Exception Raised : %s" % subclient_exception)
            print("Operation failed. " + subclient_exception)
            exit(2)
        finally:
            if flag == 0:
                print("Subclient creation completed")
            else:
                print("Subclient creation encountered error")
                exit(2)

    def subclient_update_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            subclient_content,
            subclient_filters,
            overwrite,
            commcell_instanceName,
            commcell_agentName,
            commcell_key,
            loggingPath,
            agent_type):
        """
        Function for updating subclient
        """
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        if is_VSA:
            print("Operation not allowed for VSA in CVC")
            exit(2)
        LOG.info("Subclient Updation")
        self._commcell_agent = commcell_agentName
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object
        LOG.info("Deciding client for the operation")
        common_object = CsCommon(self._commcell_obj)
        clientName = None
        (status, clientName) = common_object.check_client_name(
            commcell_clientName, commcell_instanceName)
        if status == 0:
            LOG.info("Clientname is decided : %s" % clientName)
            self._commcell_clientName = clientName
        else:
            LOG.error("Pass correct Clientname as argument")
            print("Operation failed. Pass correct Clientname as argument")
            exit(2)
        if subclient_content is None and subclient_filters is None:
            LOG.error(
                "No information provided for update. Provide content or filter path")
            print(
                "Operation failed. No information provided for update. Provide content or filter path")
            exit(2)
        backup_paths = subclient_content
        filter_paths = subclient_filters
        # Creation Subclient Instance to initiate the Subclient Update
        # Operation
        flag = 1
        try:
            LOG.info("creation of subclient_operation instance ")
            subc_obj = subclient.SubClient(
                loggingPath,
                self._commcell_obj,
                self._commcell_clientName,
                self._commcell_agent,
                commcell_backupSetName)
            flag = subc_obj.subclient_update(
                commcell_subClientName, backup_paths, filter_paths, overwrite)
        except Exception as subclient_update_error:
            LOG.error("Issue in Subclient Update Operation")
            flag = 1
            subclient_update_error = str(subclient_update_error)
            LOG.error("Exception Raised : %s" % subclient_update_error)
            print("Operation failed. " + subclient_update_error)
            exit(2)
        finally:
            if flag == 0:
                print("Subclient update completed")
            else:
                print("Subclient Update encountered error")
                exit(2)

    def subclient_delete_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            commcell_instanceName,
            commcell_agentName,
            commcell_key,
            loggingPath,
            agent_type):
        """
        Function for deleting subclient
        """
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        if is_VSA:
            print("Operation not allowed for VSA in CVC")
            exit(2)
        LOG.info("Subclient Deletion")
        self._commcell_agent = commcell_agentName
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object
        LOG.info("Deciding client for the operation")
        common_object = CsCommon(self._commcell_obj)
        clientName = None
        (status, clientName) = common_object.check_client_name(
            commcell_clientName, commcell_instanceName)
        if status == 0:
            LOG.info("Clientname is decided : %s" % clientName)
            self._commcell_clientName = clientName
        else:
            LOG.error("Pass correct Clientname as argument")
            print("Operation failed. Pass correct Clientname as argument")
            exit(2)

        flag = 1
        try:
            LOG.info("creation of subclient_operation instance ")
            subc_obj = subclient.SubClient(
                loggingPath,
                self._commcell_obj,
                self._commcell_clientName,
                self._commcell_agent,
                commcell_backupSetName)
            flag = subc_obj.subclient_delete(commcell_subClientName)
        except Exception as subclient_delete_exception:
            LOG.error("Issue in deleting the subclient ")
            flag = 1
            subclient_delete_exception = str(subclient_delete_exception)
            LOG.error("Exception Raised : %s" % subclient_delete_exception)
            print("Operation failed. " + subclient_delete_exception)
            exit(2)
        finally:
            if flag == 0:
                print("Subclient deletion completed")
            else:
                print("SubClient deletion encountered error")
                exit(2)

    def browse_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            browsepath,
            commcell_fromTime,
            commcell_toTime,
            allVersions,
            commcell_instanceName,
            commcell_agentName,
            browse_filter,
            commcell_key,
            loggingPath,
            agent_type,
            copy_precedence,
            **kwargs):
        """
        usage: PROG browse [-h] -c CLIENTNAME [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME]
                           [-p BROWSEPATH] [-ftime FROMTIME] [-ttime TOTIME]
                           [-allVersions] [-i INSTANCENAME] [-a AGENTNAME] [-k KEY]
                           [-tf TOKENFILEPATH] [-of OUTPUTFILEPATH] [-at AGENTTYPE]
                           [-sd {True,False}]
        optional arguments:
        -h, --help          show this help message and exit
        -c CLIENTNAME       Client Name
        -bk BACKUPSETNAME   Backupset Name
        -sc SUBCLIENTNAME   Subclient Name
        -p BROWSEPATH       Browse Path
        -ftime FROMTIME     The start time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.
        -ttime TOTIME       The end time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.
        -allVersions        Show all versions. For VSA, Index files after backup option must be enabled on VM group.
        -i INSTANCENAME     Instance Name
        -a AGENTNAME        Agent Name
        -k KEY              key-16 characters
        -tf TOKENFILEPATH   Token File Path
        -at AGENTTYPE       Commcell agent type
        -cp COPYPRECEDNECE  Copy Precedence
        -sd {True,False}    Show deleted items {True,False}. False by default
        """
        LOG.info("Browse Operation")
        show_deleted=kwargs.get('show_deleted',False)
        self._commcell_agent = commcell_agentName
        commcell_object = None
        commcell_object = get_object(tokenpath, commcell_key)
        if commcell_object is None:
            LOG.error("Login info could not be loaded.Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object

        if cvc_restrict_alt_client and commcell_clientName is not None:
            print("Access denied. Local user can operate only on the local client.")
            LOG.error(
                "Operation failed. Passing client name is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
            exit(2)

        LOG.info("Deciding client for the operation")
        common_object = CsCommon(self._commcell_obj)
        clientName = None
        (status, clientName) = common_object.check_client_name(
            commcell_clientName, commcell_instanceName)
        if status == 0:
            LOG.info("Clientname is decided : %s" % clientName)
            self._commcell_clientName = clientName
        else:
            LOG.error("Pass correct Clientname as argument")
            print("Operation failed. Pass correct Clientname as argument")
            exit(2)
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        vsa_guid = ''
        if is_VSA:
            self._commcell_agent = self.VSA_AGENT
            Entity.client = self._commcell_obj.clients.get(self._commcell_clientName)
            vsa_guid = Entity.client.vm_guid
            if vsa_guid is None:
                print("Operation failed. Could not find GUID for VM ", self._commcell_clientName)
                exit(2)
        filters = []
        if browse_filter:
            browse_filter_string = ""
            for browse_filter_element in browse_filter:
                browse_filter_string = "{0}{1}{2}".format(
                    browse_filter_string,
                    " OR " if browse_filter_string != "" else "",
                    browse_filter_element)
            filters = [('FileName', browse_filter_string)]
        
        if not copy_precedence:
            copy_precedence = check_copy_precedence_registry(commcell_instanceName)

        # Creation of Instance for Browse class to initiate browse operation
        flag = 1
        try:
            browse_obj = browse.Browse(
                package_instance=commcell_instanceName,
                commcell_object=self._commcell_obj,
                client_name=self._commcell_clientName,
                agent_name=self._commcell_agent,
                backupset_name=commcell_backupSetName,
                logger_object=LOG,
                tempFolder=loggingPath 
            )

            flag = browse_obj.qlist_browse(
                operation='All versions' if allVersions else 'Browse',
                subclient_name=commcell_subClientName,
                path=browsepath,
                from_time=commcell_fromTime,
                to_time=commcell_toTime,
                filters=filters,
                vsa_guid=vsa_guid,
                copy_precedence=copy_precedence,
                show_deleted=show_deleted)

        except NameError as name_error:
            name_error = str(name_error)
            LOG.error("NameError Raised :%s" % name_error)
            print("Operation failed. " + name_error)
            flag = 1
            exit(2)
        except Exception as browse_exception:
            browse_exception = str(browse_exception)
            LOG.error(
                "Exception occurred while initiating  browse operation :%s " %
                browse_exception)
            print("Operation failed. " + browse_exception)
            flag = 1
            exit(2)
        finally:
            if flag == 0:
                return
            else:
                print("Browse encountered error")
                exit(2)

    def find_ni(
            self,
            tokenpath,
            commcell_clientName,
            commcell_backupSetName,
            commcell_subClientName,
            find_path,
            commcell_fromTime,
            commcell_toTime,
            commcell_instanceName,
            commcell_agentName,
            file_name,
            commcell_key,
            agent_type,
            copy_precedence,
            loggingPath,
            **kwargs):
        """
        usage: FIND [-h]   [-c CLIENTNAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME]
                           [-path FINDPATH] [-ftime FROMTIME] [-ttime TOTIME] [-i INSTANCENAME] 
                           [-a AGENTNAME] [-k KEY] [-tf TOKENFILEPATH] [-at AGENTTYPE] [-sd {True,False}]

        Args:

        -h, --help          show this help message and exit

        -c CLIENTNAME       Client Name

        -bk BACKUPSETNAME   Backupset Name

        -sc SUBCLIENTNAME   Subclient Name

        -p FINDPATH         Find Path

        -ftime FROMTIME     The start time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.

        -ttime TOTIME       The end time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.

        -i INSTANCENAME     Instance Name

        -a AGENTNAME        Agent Name

        -k KEY              key-16 characters

        -tf TOKENFILEPATH   Token File Path

        -at AGENTTYPE       Commcell agent type

        -cp COPYPRECEDNECE  Copy Precedence
        
        -sd {True,False}    Show deleted items {True,False}. False by default
        """
        is_VSA = check_vsa_instance(agent_type, commcell_instanceName)
        show_deleted = kwargs.get('show_deleted', False)
        if is_VSA:
            print("Operation not allowed for VSA in CVC")
            exit(2)
        LOG.info("Find Operation")
        commcell_object = get_object(tokenpath, commcell_key)

        if not commcell_object:
            LOG.error("Login information could not be loaded. Exiting")
            print("Operation failed. Login info could not be loaded.")
            exit(2)
        self._commcell_obj = commcell_object
        self._commcell_agent = commcell_agentName

        if cvc_restrict_alt_client and commcell_clientName is not None:
            print("Access denied. Local user can operate only on the local client.")
            LOG.error(
                "Operation failed. Passing client name is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
            exit(2)

        LOG.info("Deciding client for the operation")
        common_object = CsCommon(self._commcell_obj)
        status, client_name = common_object.check_client_name(commcell_clientName, commcell_instanceName)

        if status == 0:
            LOG.info("Clientname is decided : %s" % client_name)
            self._commcell_clientName = client_name
        else:
            LOG.error("Pass correct Clientname as argument")
            print("Operation failed. Pass correct Clientname as argument")
            exit(2)

        filters = []
        if file_name:
            filters = [('FileName', file_name)]

        if not find_path:
            LOG.info("Path is not passed. Using current working directory of local machine as find path")
            find_path = os.getcwd()
        
        if not copy_precedence:
            copy_precedence = check_copy_precedence_registry(commcell_instanceName)

        # Creation of Instance for Browse class to initiate Find operation
        flag = 1
        try:
            browse_obj = browse.Browse(
                package_instance=commcell_instanceName,
                commcell_object=self._commcell_obj,
                client_name=client_name,
                agent_name=self._commcell_agent,
                backupset_name=commcell_backupSetName,
                logger_object=LOG,
                tempFolder=loggingPath
            )

            flag = browse_obj.qlist_browse(
                operation='Find',
                subclient_name=commcell_subClientName,
                path=find_path,
                from_time=commcell_fromTime,
                to_time=commcell_toTime,
                filters=filters,
                copy_precedence=copy_precedence,
                show_deleted=show_deleted)

        except NameError as name_error:
            LOG.error("NameError Raised :%s", name_error)
            print("Operation failed. " + name_error)
            flag = 1
            exit(2)
        except Exception as browse_exception:
            LOG.error("Exception occurred while initiating find operation :%s ", browse_exception)
            print("Operation failed. " + browse_exception)
            flag = 1
            exit(2)
        finally:
            if flag == 0:
                return
            else:
                print("Find encountered error")
                exit(2)


class CsCommon():
    """
    Class for performing common functions and checks on logged in CS
    """

    def __init__(self, commcell_object):
        """
        Initialize CsCommon Class Parameter with Cs object
        """
        self._cs_obj = commcell_object

    def read_file_list(self, filename):
        """
        Method to read from file and retruns list of paths
        """
        path_list = []
        status = False
        try:
            if os.path.exists(filename):
                filehandler = open(filename, 'r')
                old_list = filehandler.readlines()
                filehandler.close()
                new_list = []
                for item in old_list:
                    new_list.append(item.strip("\n"))
                path_list = new_list
                LOG.info("List of individual paths in file")
                LOG.info(path_list)
                status = True
            else:
                LOG.error("Invalid File path to fetch content List")
        except IOError as ioerror:
            LOG.error("Error Occurred While processing  file")
            ioerror = str(ioerror)
            LOG.error(
                "Exception raised while opening the  File  : %s " %
                ioerror)
        finally:
            return(status, path_list)

    def check_adhoc_client(self, clientName):
        '''Method to check if client provided by user for adhoc backup is associated with a local instance
        Args :
                Client name
        Returns :
                Flag :
                        True indicates client is local
                        False indicates client is not lcoal
        '''
        simpana_default_obj = SimpanaDefaults.Simpanadefaults()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            (flag, loglines) = simpana_default_obj.check_for_local_instance(clientName)
            print_log_lines(loglines)
        return flag

    def check_client_exists_in_cs(self, clientName):
        """
        Method to check if passsed client name exists in currently logged in CS
        Args :
                Client name
        Returns :
                Flag :
                        True indicates client exists in logged in CS
                        False indicates client does not exist in logged in CS
        """
        if self._cs_obj is None:
            LOG.error("Login to CS before initiating any operation")
            print("Login to CS before initiating any operation")
            return
        cs_object = self._cs_obj
        status = cs_object.clients.has_client(str(clientName))
        if status is True:
            LOG.info("Client exists in Logged in CS")
        else:
            LOG.error(
                "Client %s does not exist in Logged in CS" %
                str(clientName))
        return status

    def check_client_name(self, clientName, instanceName):
        """
        Method to validate if passed client name exists and return clientname
        Args :
                clientname
                instancename
        Returns :
        Flag
                0 = Clientname decided
                1 = Need to pass clientname correctly from argument
        Client name
        """
        flag1 = 1
        commcell_clientName = ""
        csname = self._cs_obj.commserv_name
        # Creating Object of SimpanaDefaults Class   for Local Commvault
        # detection
        simpana_default_obj = SimpanaDefaults.Simpanadefaults()
        LOG.info("Checking client name")
        if clientName is None:
            LOG.info(
                "ClientName Parameter is empty. Proceeding to check for Local Commvault Installation")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                (status, localclientname, loglines) = simpana_default_obj.local_client_detection(
                    instanceName)
                print_log_lines(loglines)
            if status is True:
                LOG.info("Proceeding with local CV detection")
                LOG.info(
                    "Local Commvault Installation is detected . Lets compare if local client exists in currently logged in CS")
                flag = self.check_client_exists_in_cs(localclientname)
                if flag is True:
                    LOG.info(
                        "Local Client name is found in currently logged in CS ")
                    LOG.info(
                        "Proceeding with given operation on client %s" %
                        localclientname)
                    commcell_clientName = localclientname
                    flag1 = 0
                else:
                    LOG.error(
                        "Local Client name %s is not  found in currently logged in CS %s" %
                        (localclientname, csname))
                    LOG.info("Enter clientname existing in logged in CS")
                    flag1 = 1
            else:
                LOG.error("No Local commvault installation detected.")
                flag1 = 1
        else:
            LOG.info("Reading clientname from cmdline argument")
            LOG.info(
                "Lets check if clientname passed exists in currently logged in CS")
            flag = self.check_client_exists_in_cs(clientName)
            if flag is True:
                LOG.info(
                    "CMDLINE argument Client name is found in currently logged in CS ")
                LOG.info(
                    "Proceeding with given operation on client %s" %
                    clientName)
                commcell_clientName = clientName
                flag1 = 0
            else:
                LOG.error(
                    "CMDLINE argument Client name is not  found in currently logged in CS : " +
                    str(csname))
                LOG.info("Enter clientname existing in logged in CS")
                flag1 = 1
        return (flag1, commcell_clientName)

    def restore_non_root_user(
            self,
            restore_paths,
            commcell_clientName,
            commcell_agent,
            commcell_instanceName,
            commcell_backupSetName,
            commcell_subClientName,
            commcell_destclient,
            commcell_destpath,
            commcell_fromTime,
            commcell_toTime,
            outputFilePath,
            versionOptions,
            unconditional_overwrite,
            copy_precedence,
            **kwargs):
        # performing qexecute operation
        is_vsa = kwargs.get("is_vsa", False)
        loggingPath = kwargs.get("tempPath", '')
        exit_code = 1
        istatus = False
        dest_client_obj = None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                (istatus, installation_path, loglines) = simpana_default_obj.simpana_installation_path(
                    commcell_instanceName)
            if not istatus:
                raise Exception(
                    "No local installaiton present with the specified instance name. Cannot perform restore")
            if commcell_destclient:
                if not commcell_destpath:
                    raise Exception("Destination Path is mandatory for out of place restore. Pass it in CMDLINE")
                if self._cs_obj.clients.has_client(commcell_destclient):
                    dest_client_obj = self._cs_obj.clients.get(commcell_destclient)
                else:
                    raise Exception(f"Invalid destination client: [{commcell_destclient}]")

            print_log_lines(loglines)
            # form input XML
            import xml.etree.cElementTree as etree
            from xml.dom import minidom
            root = etree.Element('TMMsg_CreateTaskReq')
            taskInfo = etree.Element('taskInfo')
            associations = etree.Element('associations')
            appName = etree.Element('appName')
            appName.text = commcell_agent
            backupsetName = etree.Element('backupsetName')
            clientobj = self._cs_obj.clients.get(str(commcell_clientName))
            LOG.info("Client Name : %s" % (commcell_clientName))
            LOG.info("client object created successfully")

            # For In-place restores using same client
            if not dest_client_obj:
                dest_client_obj = clientobj
            agentobj = clientobj.agents.get(str(commcell_agent))
            LOG.info("Agent Name  : %s " % (commcell_agent))
            LOG.info("agent object created successfully")
            if not commcell_backupSetName and not is_vsa:
                commcell_backupSetName = agentobj.backupsets.default_backup_set
            
            backupsetobj = None
            if commcell_backupSetName:
                backupsetobj = agentobj.backupsets.get(str(commcell_backupSetName))
                LOG.info("backupset object created successfully")
            
            LOG.info("BackupSet Name : %s" % (commcell_backupSetName))
            
            backupsetName.text = commcell_backupSetName
            clientName = etree.Element('clientName')
            clientName.text = commcell_clientName
            instanceName = etree.Element('instanceName')
            instanceId = etree.Element('instanceId')
            if is_vsa and not commcell_backupSetName and not commcell_subClientName:
                instanceName.text = 'vminstance'
                instanceId.text = agentobj.instances.get(str('vminstance')).instance_id
                
            subclientName = etree.Element('subclientName')
            if not commcell_subClientName and backupsetobj:
                commcell_subClientName = backupsetobj.subclients.default_subclient
            subclientName.text = commcell_subClientName
            subTasks = etree.Element('subTasks')
            options = etree.Element('options')
            restoreOptions = etree.Element('restoreOptions')

            # Setting advanced option <jobDescription> for restore job
            commonOpts = etree.Element('commonOpts')
            jobDescription = etree.Element('jobDescription')
            description = f"Submitted by user: [{getpass.getuser()}] uid: [{os.geteuid()}]"
            jobDescription.text = description
            commonOpts.append(jobDescription)
            LOG.info(description)

            browseOption = etree.Element('browseOption')
            backupset = etree.Element('backupset')
            commCellId = etree.Element('commCellId')
            commCellId.text = '2'
            listMedia = etree.Element('listMedia')
            listMedia.text = 'false'
            cvcBrowse = etree.Element('cvcBrowse')
            cvcBrowse.text = 'true'

            mediaOption = etree.Element('mediaOption')

            copyPrecedence = etree.Element('copyPrecedence')
            copyPrecedenceApplicable = etree.Element(
                'copyPrecedenceApplicable')
            if copy_precedence:
                copyPrecedenceApplicable.text = 'true'
                copyPrecedence.append(copyPrecedenceApplicable)
                copyPrecedenceInner = etree.Element(
                    'copyPrecedence')
                copyPrecedenceInner.text = str(copy_precedence)
                copyPrecedence.append(copyPrecedenceInner)
            else:
                copyPrecedenceApplicable.text = 'false'
                copyPrecedence.append(copyPrecedenceApplicable)

            drivePool = etree.Element('drivePool')
            library = etree.Element('library')
            mediaAgent = etree.Element('mediaAgent')

            mediaOption.append(copyPrecedence)
            mediaOption.append(drivePool)
            mediaOption.append(library)
            mediaOption.append(mediaAgent)

            noImage = etree.Element('noImage')
            noImage.text = str(versionOptions.get('no_image',False))
            timeRange = etree.Element('timeRange')
            if commcell_fromTime:
                fromTimeValue = etree.Element('fromTimeValue')
                fromTimeValue.text = commcell_fromTime
                timeRange.append(fromTimeValue)
            if commcell_toTime:
                toTimeValue = etree.Element('toTimeValue')
                toTimeValue.text = commcell_toTime
                timeRange.append(toTimeValue)
            timeZone = etree.Element('timeZone')
            TimeZoneName = etree.Element('TimeZoneName')

            # Setting client timezone for restore
            TimeZoneName.text = clientobj.timezone
            LOG.info(f"Client timezone: {clientobj.timezone}")

            timeZone.append(TimeZoneName)
            useExactIndex = etree.Element('useExactIndex')
            useExactIndex.text = 'false'
            browseOption.append(backupset)
            browseOption.append(commCellId)
            browseOption.append(listMedia)
            browseOption.append(mediaOption)
            browseOption.append(noImage)
            browseOption.append(timeRange)
            browseOption.append(timeZone)
            browseOption.append(useExactIndex)
            browseOption.append(cvcBrowse)
            commonOptions = etree.Element('commonOptions')
            clusterDBBackedup = etree.Element('clusterDBBackedup')
            clusterDBBackedup.text = 'false'
            detectRegularExpression = etree.Element('detectRegularExpression')
            detectRegularExpression.text = 'true'
            offlineMiningRestore = etree.Element('offlineMiningRestore')
            offlineMiningRestore.text = 'false'
            onePassRestore = etree.Element('onePassRestore')
            onePassRestore.text = 'false'
            powerRestore = etree.Element('powerRestore')
            powerRestore.text = 'false'
            preserveLevel = etree.Element('preserveLevel')
            preserveLevel.text = '1'
            restoreACLs = etree.Element('restoreACLs')
            restoreACLs.text = 'true'
            restoreToDisk = etree.Element('restoreToDisk')
            restoreToDisk.text = 'false'
            stripLevel = etree.Element('stripLevel')
            stripLevel.text = '0'
            stripLevelType = etree.Element('stripLevelType')
            stripLevelType.text = 'PRESERVE_LEVEL'
            systemStateBackup = etree.Element('systemStateBackup')
            systemStateBackup.text = 'false'
            unconditionalOverwrite = etree.Element('unconditionalOverwrite')
            unconditionalOverwrite.text = str(unconditional_overwrite).lower()
            wildCard = etree.Element('wildCard')
            wildCard.text = 'false'
            commonOptions.append(clusterDBBackedup)
            commonOptions.append(detectRegularExpression)
            commonOptions.append(offlineMiningRestore)
            commonOptions.append(onePassRestore)
            commonOptions.append(powerRestore)
            commonOptions.append(preserveLevel)
            commonOptions.append(restoreACLs)
            commonOptions.append(restoreToDisk)
            commonOptions.append(stripLevel)
            commonOptions.append(stripLevelType)
            commonOptions.append(systemStateBackup)
            commonOptions.append(unconditionalOverwrite)
            if versionOptions:
                if next(iter(versionOptions)) == 'all_versions':
                    allVersion = etree.Element('allVersion')
                    allVersion.text = 'true'
                    commonOptions.append(allVersion)
            commonOptions.append(wildCard)
            destination = etree.Element('destination')
            destClient = etree.Element('destClient')
            destClientName = etree.Element('clientName')
            inPlace = etree.Element('inPlace')
            isLegalHold = etree.Element('isLegalHold')
            isLegalHold.text = 'false'
            no_of_streams = etree.Element('noOfStreams')
            no_of_streams.text = '2'
            qrOption = etree.Element('qrOption')
            destAppTypeId = etree.Element('destAppTypeId')

            # To retrieve destination app Id based on agent
            all_agents = dest_client_obj.agents.all_agents
            app_id = all_agents.get('file system', all_agents.get(
                'windows file system', all_agents.get('linux file system')))
            if not app_id:
                raise Exception("Failed to retrieve application ID of the destination machine")
            destAppTypeId.text = app_id
            qrOption.append(destAppTypeId)

            # out of place restore
            if commcell_destpath:
                if commcell_destclient:
                    destClientName.text = commcell_destclient
                else:
                    destClientName.text = commcell_clientName
                inPlace.text = 'false'
                destPath = etree.Element("destPath")
                destPath.text = commcell_destpath
                destination.append(destPath)
            else:
                userHomeDir = os.path.expanduser('~')
                destClientName.text = commcell_clientName
                if commcell_agent == 'virtual server':
                    if len(restore_paths) > 1:
                        print("In-Place restore is not supported with multiple source paths. Please provide destination path manually.")
                        return 1
                    inPlace.text = 'false'
                    destPath = etree.Element("destPath")
                    destPathFromSource = restore_paths[0]
                    destPathFromSource = destPathFromSource.strip('\\').split('\\', 1)[-1].replace('\\', '/').rsplit('/',1)
                    if len(destPathFromSource) == 1:
                        destPathFromSource1 = '/'
                    else:
                        destPathFromSource1 = f"/{destPathFromSource[0]}"
                    isInstallDirSubPath = is_subpath(destPathFromSource1, installation_path)
                    if isInstallDirSubPath:
                        LOG.info("Install Directory Sub-paths cannot be used as dest path for restore unless specified explicitly.")
                        LOG.info("Setting dest path to user home directory : %s" % userHomeDir)
                        if not userHomeDir or userHomeDir=='/':
                            print("User home directory not found, please specify destination path for restore")
                            raise Exception("User home directory not found, please specify destination path for restore")
                        destPath.text = userHomeDir
                    else:
                        destPath.text = destPathFromSource1
                    destination.append(destPath)
                else:
                    isInstallDirSubPath = is_subpath(restore_paths[0], installation_path)
                    if isInstallDirSubPath:
                        LOG.info("Install Directory Sub-paths cannot be used as dest path for restore unless specified explicitly.")
                        LOG.info("Setting dest path to user home directory : %s and coverting to out-of-place restore" % userHomeDir)
                        if not userHomeDir or userHomeDir=='/':
                            print("User home directory not found, please specify destination path for restore")
                            raise Exception("User home directory not found, please specify destination path for restore")
                        inPlace.text = 'false'
                        destPath = etree.Element("destPath")
                        destPath.text = userHomeDir
                        destination.append(destPath)
                    else:
                        inPlace.text = 'true'
            destClient.append(destClientName)
            destination.append(destClient)
            destination.append(inPlace)
            destination.append(isLegalHold)
            destination.append(no_of_streams)
            fileOption = etree.Element('fileOption')
            for path in restore_paths:
                sourceItem = etree.Element('sourceItem')
                sourceItem.text = path
                fileOption.append(sourceItem)
            if versionOptions:
                if next(iter(versionOptions)) == 'versions':
                    for versionNum in versionOptions['versions']:
                        sourceItem = etree.Element('sourceItem')
                        if is_vsa or commcell_agent == 'virtual server':
                            sourceItem.text = '|\\|#15!vErSiOnS|#15!\\' + str(versionNum)
                        else:
                            sourceItem.text = '|/|#15!vErSiOnS|#15!/' + str(versionNum)
                        fileOption.append(sourceItem)
            virtualServerRstOption = etree.Element('virtualServerRstOption')
            if commcell_agent == 'virtual server':
                isFileBrowse = etree.Element('isFileBrowse')
                isFileBrowse.text = 'true'
                virtualServerRstOption.append(isFileBrowse)
            volumeRstOption = etree.Element('volumeRstOption')
            volumeLeveRestore = etree.Element('volumeLeveRestore')
            volumeLeveRestore.text = 'false'
            volumeRstOption.append(volumeLeveRestore)
            associations.append(appName)
            associations.append(backupsetName)
            associations.append(clientName)
            
            if is_vsa and not commcell_backupSetName and not commcell_subClientName:
                associations.append(instanceName)
                associations.append(instanceId)
            associations.append(subclientName)
            subTasks.append(options)
            options.append(restoreOptions)
            options.append(commonOpts)
            restoreOptions.append(browseOption)
            restoreOptions.append(commonOptions)
            restoreOptions.append(destination)

            # Needed when no of streams is greater than 1
            if commcell_agent != 'virtual server':
                restoreOptions.append(qrOption)

            restoreOptions.append(fileOption)
            restoreOptions.append(virtualServerRstOption)
            restoreOptions.append(volumeRstOption)
            subTask = etree.Element('subTask')
            operationType = etree.Element('operationType')
            operationType.text = 'RESTORE'
            subTaskType = etree.Element('subTaskType')
            subTaskType.text = 'RESTORE'
            subTask.append(operationType)
            subTask.append(subTaskType)
            subTasks.append(subTask)
            task = etree.Element('task')
            initiatedFrom = etree.Element('initiatedFrom')
            initiatedFrom.text = 'COMMANDLINE'
            policyType = etree.Element('policyType')
            policyType.text = 'DATA_PROTECTION'
            taskFlags = etree.Element('taskFlags')
            disabled = etree.Element('disabled')
            disabled.text = 'false'
            taskFlags.append(disabled)
            taskType = etree.Element('taskType')
            taskType.text = 'IMMEDIATE'
            task.append(initiatedFrom)
            task.append(policyType)
            task.append(taskFlags)
            task.append(taskType)
            taskInfo.append(associations)
            taskInfo.append(subTasks)
            taskInfo.append(task)
            root.append(taskInfo)
            treeString = etree.tostring(root, 'utf-8')
            reparsed = minidom.parseString(treeString)
            userHomeDir = os.path.expanduser('~')
            temp_folder = '{}/cvc'.format(userHomeDir)
            if loggingPath: 
                temp_folder = loggingPath
            elif not userHomeDir or userHomeDir =='/':
                print("User home directory not found, please specify a path for logging")
                exit(1)

            try:
                if not os.path.exists(temp_folder):
                    os.makedirs(temp_folder)
                    os.chmod(temp_folder, 0o700)
            except OSError:
                temp_folder = os.getcwd()
                if not os.access(temp_folder, os.W_OK):
                    print('User does not have permission for writing tmp files on {}/cvc or on current working directory, please provide a valid log file path'.format(userHomeDir))
                    exit(1)
                
            _time = '{date:%m-%d-%Y_%H_%M_%S}'.format(date=datetime.datetime.now())
            _time = '{}_{}'.format(_time, os.getpid())	
            restore_xml_file_name = temp_folder + \
                '/cvcRestoreArguments' + str(os.getuid()) + '.xml'
            token_file = '{}/token_{}.dat'.format(temp_folder, _time)
            inputXMLFile = open(restore_xml_file_name, "w")
            inputXMLFile.write(reparsed.toprettyxml(indent="    "))
            inputXMLFile.close()
            os.chmod(restore_xml_file_name, 0o600)
            qcommand_path = str(installation_path) + "/Base/./qoperation"
            tokenString = self._cs_obj._headers['Authtoken']
            tokenString = str((tokenString.split(" "))[1])
            with open(token_file, 'w') as _tfile:
                _tfile.write(tokenString)
            
            os.chmod(token_file, 0o600)
            command_string = (
                str(installation_path) +
                "/Base/./qoperation execute -af " +
                restore_xml_file_name +
                " -tfPlain " + token_file)
            LOG.info("qcommand being executed :" + (command_string))
            restore_qcommand = subprocess.run(
                [
                    qcommand_path,
                    'execute',
                    '-af',
                    restore_xml_file_name,
                    '-tfPlain',
                    token_file],
                stdout=subprocess.PIPE)
            exit_code = restore_qcommand.returncode
        except Exception as qoperation_error:
            LOG.error("Operation failed. %s" % str(qoperation_error))
            
        if token_file and os.path.exists(token_file):
                os.remove(token_file)
                
        if not exit_code:
            command_output = restore_qcommand.stdout.decode().rstrip('\n')
            if outputFilePath:
                outputFile = open(outputFilePath, "w")
                outputFile.write(command_output)
                outputFile.close()
                os.chmod(outputFilePath, 0o600)
            else:
                print(command_output)
            LOG.info("Restore initiated successfully. Job ID: " +
                     command_output[command_output.index('val="') +
                                    4:command_output.index('/')])
        return exit_code


class MyPrompt(Cmd, object):
    """
    Class is responsible for Parsing the commandline arguments based on user inputs
    Methods  :
    do_login : Method to login to webconsole server
    do_version : Method to display the version of cvc tool
    do_logpath : Method to display the log file path
    do_add_subclient : Method to add Subclient with given content
    do_subclient_update : Method to add contents to existing subclient
    do_subclient_delete :  Method to delete contents
    do_backup : Method to do backup on mentioned subclient
    do_browse : Method to perform browse at subclient Level with given path
    do_restore : Method to perform in-place and out-of-place restore at subclient Level
    do_ondemand : Method to perform ondemand backup of given dataset
    do_find : Method to find details of a file given filename
    do_get_job_status: Method to get job status
    do_get_job_summary: Method to get job summary
    do_job: Method to kill, pause or resume a job
    do_backup_list: Method to set backup_list as current list
    do_restore_list: Method to set restore_list as current list
    do_add: Method to add path to list
    do_remove: Method to remove path from list
    do_list: Method to display list
    do_reset: Method to reset list
    do_setBrowseOptions: Method to set options for browse
    do_toTime: Method to set 'to time' for browse
    do_resetToDefaults: Method to reset browse options
    do_cd: Method to change directory in backup content
    do_ls: Method to list information about backup content
    do_pwd: Method to print the full path of the current working directory within backup content
    do_logout: Method to logout of commcell
    do_quit: Method to quit interactive mode
    emptyline: Method to handle emptyline entry
    """

    def __init__(self, stdin=None):
        """
        Initialize MyPrompt Class Object
        """
        if stdin is None:
            super(MyPrompt, self).__init__()
        else:
            Cmd.__init__(self, stdin=stdin)

        self._version = None
        self._commcell_obj = None
        self._commcell_agent = "file system"
        self._qlogin_local_client = None
        self._loggingPath = None
        # for dynamic list population
        self._current_list_operation = -1
        self._restore_list = set()
        self._backup_list = set()
        # for browse
        self.browse_obj = None
        self._live_browse_path = None
        self._previous_wd = None
        self._dir_stack = []
        self._lb_clientName = None
        self._lb_instanceName = None
        self._lb_backupSetName = None
        self._lb_subClientName = None
        self._lb_fromtime = 0
        self._lb_totime = 0
        self._lb_initialized = False
        self._liveBrowseOptions = None

    def do_login(self, args):
        """
        usage: login  [-h] [-wch WEBCONSOLE_HOSTNAME]  [-u USERNAME] [ -p PASSWORD] [-i INSTANCENAME] [-lf LOGFILEPATH] [-a AGENTTYPE]

        Login to Commserve

        optional arguments:
                -h, --help            show this help message and exit
                -wch WEBCONSOLE_HOSTNAME, --webconsole_hostname WEBCONSOLE_HOSTNAME
                                        Commcell name
                -u USERNAME           Commcell username
                -p PASSWORD           Commcell password
                -i INSTANCENAME       Instance name
                -lf LOGFILEPATH       Log File Path
                -a AGENTTYPE          Commcell agent type
        """
        global LOG, cvc_https
        #LOG.info("Login Started")
        k = shlex.split(args)
        # Defining Parser Command Structure for Login Operation
        p = argparse.ArgumentParser(
            description='Login to Commserve',
            usage="login [-h] [-wch WEBCONSOLE_HOSTNAME]  [-u USERNAME] [ -p PASSWORD] [-i INSTANCENAME] [-lf LOGFILEPATH] [-a AGENTTYPE]")
        p.add_argument(
            "-wch",
            "--webconsole_hostname",
            dest="webconsole_hostname",
            type=str,
            default=None,
            help="Commcell name")
        p.add_argument(
            "-u",
            dest="username",
            type=str,
            required=False,
            help="Commcell username",
            default=None)
        p.add_argument(
            "-p",
            dest="password",
            type=str,
            required=False,
            help="Commcell password",
            default=None)
        p.add_argument(
            "-i",
            dest="instanceName",
            type=str,
            required=False,
            help="Instance name",
            default=None)
        p.add_argument(
            '-lf',
            dest="logFilePath",
            help='Log File Path',
            type=str,
            default=None)
        p.add_argument(
            '-a',
            dest="agentType",
            help='Agent type(fs/vsa)',
            type=str,
            default='')
        p.add_argument(
            '-https',
            dest="force_https",
            help='Login is forced to use https protocol',
            choices=[
                'true',
                'false'],
            type=str.lower,
            default=None,
            required=False)
        p.add_argument(
            '-cert',
            dest="certificate_path",
            help='Certificate Path',
            type=str,
            default=None)
        # Creating Object of SimpanaDefaults Class   for Local Commvault
        # detection
        simpana_default_obj = SimpanaDefaults.Simpanadefaults()
        # Parsing the Command received from CMDLINE
        try:
            pargs = p.parse_args(k)
        except SystemExit:
            return
        commcell_instanceName = pargs.instanceName
        commcell_name = pargs.webconsole_hostname
        commcell_username = pargs.username
        commcell_password = pargs.password
        certificate_path = pargs.certificate_path
        self.commcell_agentType = pargs.agentType.lower()

        if len(self.commcell_agentType) != 0:
            if self.commcell_agentType != 'fs' and self.commcell_agentType != 'vsa':
                print("Operation failed. Agent Type can only be 'fs' or 'vsa'")
                return

        # check if the instance passed by user is valid
        instanceLoglines = []
        if commcell_instanceName:
            (flag, instanceLoglines) = check_instance(commcell_instanceName)
            if not flag:
                print("Operation failed. Instance with the provided name does not exist")
                return
        else:
            commcell_instanceName = 'Instance001'
        loggingPath = None
        lines1 = None
        lines2 = None
        (lflag, loggingPath, lines1, lines2) = get_logging_path(
            commcell_instanceName, pargs.logFilePath)

        if lflag:
            LOG = logger.CVCLogger()
            LOG.initializelogger('cvc.log', loggingPath)
            LOG = LOG.log
            LOG.info("CVC Shell Started ")
            LOG.info("Running in Interactive Mode ")

            # Set Force HTTPS to False, if reg key is set to 0 else true
            force_https = simpana_default_obj.force_https(commcell_instanceName, LOG)
            allow_http = simpana_default_obj.allow_http(commcell_instanceName, LOG)
            web_service_url = simpana_default_obj.web_service_url(commcell_instanceName, LOG)
            
			# User input takes first preference
            if pargs.force_https:
                cvc_https = force_https = True if pargs.force_https.lower() == 'true' else False             
                # if user is forcing https through parameter, http shouldnt be allowed
                if force_https:
                    allow_http = False
            
            
            if force_https and not certificate_path:
                certificate_path = cvc_ca_bundle

            print_env_variables()
            if instanceLoglines:
                print_log_lines(instanceLoglines)
            if lines1:
                print_log_lines(lines1)
            if lines2:
                print_log_lines(lines2)
        else:
            return
        self._loggingPath = loggingPath
        self._LOG = LOG
        print('Log path: {0}'.format(loggingPath))

        flag, commcell_name, commcell_username, commcell_password, local_client, is_interface_list = check_csname_and_creds(
            commcell_name,
            commcell_instanceName,
            commcell_username,
            commcell_password,
            True)
        if not flag:
            return
        self._qlogin_local_client = local_client

        self._commcell_obj = _login_using_cvpysdk(
            webconsole_hostname=commcell_name,
            commcell_username=commcell_username,
            commcell_password=commcell_password,
            force_https=force_https,
            allow_http=allow_http,
            certificate_path=certificate_path,
            log=LOG,
            is_interface_list=is_interface_list,
            web_service_url=web_service_url
        )

        self._vsa_guid = ''
        self._is_VSA = False
        self._is_VSA = check_vsa_instance(self.commcell_agentType, commcell_instanceName)
        if self._is_VSA:
            self._commcell_agent = "virtual server"
            self._LOG.info("Using VSA related ops")
            if self._qlogin_local_client == None:
                _, localClient, _ = simpana_default_obj.local_client_detection(commcell_instanceName)
                Entity.client = self._commcell_obj.clients.get(localClient)
                Entity.client_name = localClient
            else: 
                Entity.client = self._commcell_obj.clients.get(self._qlogin_local_client)
                Entity.client_name = self._qlogin_local_client
            self._vsa_guid = Entity.client.vm_guid
            # if self._vsa_guid is None:
            #     print("Operation failed. Could not find GUID for VM ", self._qlogin_local_client)
            #     return
        print("Current working directory : %s" % os.getcwd())

    def do_version(self, args):
        """ Prints the version of CVC tool
        usage: version

        """
        k = shlex.split(args)
        version_parser = argparse.ArgumentParser(
            description='version', usage="version [-h]")
        try:
            margs = version_parser.parse_args(k)
        except SystemExit:
            return

        if not self._version:
            self._version = get_version()
        print(self._version)

    def do_logpath(self, args):
        """ Prints the Log file path
        usage: logpath

        """
        k = shlex.split(args)
        logpath_parser = argparse.ArgumentParser(
            description='logpath', usage="logpath [-h]")
        try:
            margs = logpath_parser.parse_args(k)
        except SystemExit:
            return

        print("Log path: {0}".format(self._loggingPath))

    # CONFIGURE-RELATED COMMANDS
    if cvc_configure:
        def do_add_subclient(self, args):
            """
            usage: add_subclient [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] -sc SUBCLIENT (-d DIRPATH [DIRPATH ...] | -f DIRECTIVEFILE) [-ep EXCLUDEPATHS] -dsp DSP

            subclient creation

            optional arguments:
                    -h, --help            show this help message and exit
                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
                    -sc SUBCLIENT, --subclient SUBCLIENT
                                            Subclient Name
                    -d DIRPATH [DIRPATH ...], --dir DIRPATH [DIRPATH ...]
                                            Paths to be added to subclient content
                    -f DIRECTIVEFILE, --file DIRECTIVEFILE
                                            Directive file-it should be in current machine from
                                            which the command is executed
                    -ep EXCLUDEPATHS [EXCLUDEPATHS ...], --excludepaths EXCLUDEPATHS [EXCLUDEPATHS ...]
                                            Filter Paths
                    -dsp DSP, --defaultstoragepolicy DSP
                                            Default Storage Policy
            NOTE: This operation is not allowed for VSA
            """
            # Create subclient with provided content in given backupset
            flag = 1
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Subclient_Add Operation
            sp = argparse.ArgumentParser(
                description='subclient creation',
                usage="add_subclient [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] -sc SUBCLIENT (-d DIRPATH [DIRPATH ...] | -f DIRECTIVEFILE) [-ep EXCLUDEPATHS] -dsp DSP", epilog="NOTE: This operation is not allowed for VSA")
            sp.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name")
            sp.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            sp.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            sp.add_argument(
                "-sc",
                "--subclient",
                type=str,
                default="subclient",
                dest="subclient",
                required=True,
                help="Subclient Name")
            backup_group_path = sp.add_mutually_exclusive_group(required=True)
            backup_group_path.add_argument(
                "-d",
                "--dir",
                nargs='+',
                dest="dirpath",
                default=None,
                type=str,
                help="Paths to be added to subclient content")
            backup_group_path.add_argument(
                "-f",
                "--file",
                dest="directivefile",
                default=None,
                type=str,
                help="Directive file-it should be in current machine from which the command is executed")
            sp.add_argument(
                "-ep",
                "--excludepaths",
                nargs='+',
                dest="excludepaths",
                default=None,
                type=str,
                help="Filter Paths")
            sp.add_argument(
                "-dsp",
                "--defaultstoragepolicy",
                type=str,
                default=None,
                dest="dsp",
                required=True,
                help="Default Storage Policy")
            # Parsing the CMDLINE Input based on above defined structure
            try:
                sargs = sp.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast once  before proceeding with
            # subclient_Add
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._is_VSA:
                print("Subclient creation not allowed for VSA in CVC")
                return
            # Reading the values passed as Argument
            self._LOG.info("Subclient Creation")
            commcell_clientName = sargs.clientName
            commcell_instanceName = sargs.instanceName
            commcell_subClientName = sargs.subclient
            commcell_backupSetName = sargs.backupSetName
            # check if the instance passed by user is valid
            instanceLoglines = []
            if commcell_instanceName:
                (flag, instanceLoglines) = check_instance(commcell_instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
            else:
                commcell_instanceName = 'Instance001'

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            else:
                print("Pass correct Clientname as argument")
                return
            # Parsing other parameters
            excludepaths = sargs.excludepaths
            if sargs.dsp is None:
                print("Its mandatory to pass storage policy for subclient creation")
                self._LOG.warn(
                    "Its mandatory to pass storage policy for subclient creation")
                return
            else:
                self._LOG.info("Storage Policy Set")
                dsp = sargs.dsp
            if sargs.dirpath:
                backup_dirpath = sargs.dirpath
                backup_paths = backup_dirpath
            elif sargs.directivefile:
                backup_directivefile = sargs.directivefile
                self._LOG.info("File List Option Chosen")
                filename = str(backup_directivefile)
                self._LOG.info("Filename is :%s" % filename)
                (status, backup_paths) = common_object.read_file_list(filename)
                if status is True:
                    self._LOG.info(
                        "Backup paths fetched successfully from file")
                else:
                    print("Error while reading filelist")
                    return
            else:
                print("Any one of the  parameter : file or Directorypath is mandatory for subclient creation  .since both are not passed, exiting the process")
                return
            self._LOG.info(
                "Subclient  will be created on below defined contents : ")
            self._LOG.info(backup_paths)
            subclient_content = backup_paths
            # Creation of Instance for Subclient class to initiate the
            # Subclient Addition Operation
            try:
                self._LOG.info("creation of subclient_operation instance ")
                subc_obj = subclient.SubClient(
                    self._loggingPath,
                    self._commcell_obj,
                    commcell_clientName,
                    self._commcell_agent,
                    commcell_backupSetName)
                flag = subc_obj.subclient_add(
                    commcell_subClientName, dsp, subclient_content, excludepaths)
            except Exception as subclient_exception:
                self._LOG.error(
                    "Issue in creating subclient with given content")
                flag = 1
                subclient_exception = str(subclient_exception)
                self._LOG.error("Exception Raised : %s" % subclient_exception)
            finally:
                if flag == 0:
                    self._LOG.info("Subclient Creation Completed")
                    print("Subclient Creation Completed")
                else:
                    self._LOG.error("Subclient Creation Failed ")
                    print("Subclient Creation Failed ")

        def do_subclient_update(self, args):
            """
            usage: subclient_update [-h] [-c CLIENTNAME]  [-i INSTANCENAME]  [-bk BACKUPSETNAME] -sc SUBCLIENT (-d DIRPATH [DIRPATH ...] | -f DIRECTIVEFILE) [-ep EXCLUDEPATHS] [-overwrite  {True,False}]

            subclient update

            optional arguments:
                    -h, --help            show this help message and exit
                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
                    -sc SUBCLIENT, --subclient SUBCLIENT
                                            Subclient Name
                    -d DIRPATH [DIRPATH ...], --dir DIRPATH [DIRPATH ...]
                                            Directive file-it should be in current machine from
                                            which the command is executed
                    -f DIRECTIVEFILE, --file DIRECTIVEFILE
                                            Content is mandatory parameter
                    -ep EXCLUDEPATHS [EXCLUDEPATHS ...], --excludepaths EXCLUDEPATHS [EXCLUDEPATHS ...]
                                            Filter Paths
                    -overwrite {True,False}, --overwrite {True,False}
            NOTE: This operation is not allowed for VSA
            """
            # Add contents to given subclient
            flag = 1
            #  Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Subclient_Content_Add
            # Operation
            sp = argparse.ArgumentParser(
                description='subclient update',
                usage="subclient_update [-h] [-c CLIENTNAME]  [-i INSTANCENAME]  [-bk BACKUPSETNAME] -sc SUBCLIENT (-d DIRPATH [DIRPATH ...] | -f DIRECTIVEFILE) [-ep EXCLUDEPATHS] [-overwrite  {True,False}] ", 
                epilog="NOTE: This operation is not allowed for VSA")
            sp.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name")
            sp.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            sp.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            sp.add_argument(
                "-sc",
                "--subclient",
                type=str,
                default="subclient",
                dest="subclient",
                required=True,
                help="Subclient Name")
            backup_group_path = sp.add_mutually_exclusive_group(required=True)
            backup_group_path.add_argument(
                "-d",
                "--dir",
                nargs='+',
                dest="dirpath",
                default=None,
                type=str,
                help="Directive file-it should be in current machine from which the command is executed")
            backup_group_path.add_argument(
                "-f",
                "--file",
                dest="directivefile",
                default=None,
                type=str,
                help="Content is mandatory parameter ")
            sp.add_argument(
                "-ep",
                "--excludepaths",
                nargs='+',
                dest="excludepaths",
                default=None,
                type=str,
                help="Filter Paths")
            sp.add_argument(
                "-overwrite",
                "--overwrite",
                default='False',
                choices=[
                    'True',
                    'False'])
            # Parsing the CMDLINE Input based on above defined structure
            try:
                sargs = sp.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast once before proceeding with
            # subclient_content_add
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._is_VSA:
                print("Operation not allowed for VSA in CVC")
                return
            # Reading the values passed as Argument
            self._LOG.info("Subclient Content Addition")
            commcell_clientName = sargs.clientName
            commcell_instanceName = sargs.instanceName
            commcell_subClientName = sargs.subclient
            commcell_backupSetName = sargs.backupSetName
            # check if the instance passed by user is valid
            instanceLoglines = []
            if commcell_instanceName:
                (flag, instanceLoglines) = check_instance(commcell_instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
            else:
                commcell_instanceName = 'Instance001'

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            elif sargs.clientName is None:
                print("Need to pass clientname as parameter in cmdline")
                return
            else:
                print('Please verify the provided client name and check '
                      'whether the user has access on client: {0}'.format(commcell_clientName))
                return

            # Parsing other parameters
            excludepaths = sargs.excludepaths
            content_overwrite = sargs.overwrite
            if sargs.dirpath:
                backup_dirpath = sargs.dirpath
                backup_paths = backup_dirpath
            elif sargs.directivefile:
                backup_directivefile = sargs.directivefile
                self._LOG.info(" File List Option Chosen")
                filename = str(backup_directivefile)
                (status, backup_paths) = common_object.read_file_list(filename)
                if status is True:
                    self._LOG.info(
                        "Backup paths fetched successfully from file")
                else:
                    print("Error while reading filelist")
                    return
            else:
                print(
                    "Any one of the parameter:file or Directorypath is mandatory for Subclient Content Addition")
                return
            self._LOG.info(
                "Subclient Content Addition on below defined contents : ")
            self._LOG.info(backup_paths)
            subclient_content = backup_paths
            # Creation Subclient Instance to initiate the Subclient Content
            # Addition Operation
            try:
                self._LOG.info("creation of subclient_operation instance ")
                subc_obj = subclient.SubClient(
                    self._loggingPath,
                    self._commcell_obj,
                    commcell_clientName,
                    self._commcell_agent,
                    commcell_backupSetName)
                flag = subc_obj.subclient_update(
                    commcell_subClientName,
                    subclient_content,
                    excludepaths,
                    content_overwrite)
            except Exception as subclient_content_add_error:
                self._LOG.error("Issue in Subclient Content Addition")
                flag = 1
                subclient_content_add_error = str(subclient_content_add_error)
                self._LOG.error(
                    "Exception Raised : %s" %
                    subclient_content_add_error)
            finally:
                if flag == 0:
                    self._LOG.info("Subclient Update Completed")
                    print("Subclient Update Completed")
                else:
                    self._LOG.error("Subclient Update Failed ")
                    print("Subclient Update Failed")

        def do_subclient_delete(self, args):
            """
            usage: subclient_delete [-h] [-c CLIENTNAME]  [-i INSTANCENAME][-bk BACKUPSETNAME] -sc SUBCLIENT

            subclient deletion

            optional arguments:
                    -h, --help            show this help message and exit
                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
                    -sc SUBCLIENT, --subclient SUBCLIENT
                                            Subclient Name
            NOTE: This operation is not allowed for VSA
            """
            # To delete given  subclient  in given backupset
            flag = 1
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Subclient_Delete Operation
            sp = argparse.ArgumentParser(
                description='subclient deletion',
                usage="subclient_delete [-h] [-c CLIENTNAME]  [-i INSTANCENAME][-bk BACKUPSETNAME] -sc SUBCLIENT ", epilog="NOTE: This operation is not allowed for VSA")
            sp.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name")
            sp.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            sp.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            sp.add_argument(
                "-sc",
                "--subclient",
                type=str,
                default="subclient",
                dest="subclient",
                required=True,
                help="Subclient Name")
            # Parsing the CMDLINE Input based on above defined structure
            try:
                sargs = sp.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast once  before proceeding
            # Subclient_Deletion
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._is_VSA:
                print("Operation not allowed for VSA in CVC")
                return
            self._LOG.info("Subclient Deletion")
            commcell_subClientName = sargs.subclient
            commcell_backupSetName = sargs.backupSetName
            commcell_clientName = sargs.clientName
            commcell_instanceName = sargs.instanceName
            # check if the instance passed by user is valid
            instanceLoglines = []
            if commcell_instanceName:
                (flag, instanceLoglines) = check_instance(commcell_instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
            else:
                commcell_instanceName = 'Instance001'

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            elif sargs.clientName is None:
                print("Need to pass clientname as parameter in cmdline")
                return
            else:
                print('Please verify the provided client name and check '
                      'whether the user has access on client: {0}'.format(commcell_clientName))
                return
            
            # Creation of Instance for Subclient class to initiate the
            # Subclient Deletion
            try:
                self._LOG.info("creation of subclient_operation instance ")
                subc_obj = subclient.SubClient(
                    self._loggingPath,
                    self._commcell_obj,
                    commcell_clientName,
                    self._commcell_agent,
                    commcell_backupSetName)
                flag = subc_obj.subclient_delete(commcell_subClientName)
            except Exception as subclient_delete_exception:
                self._LOG.error("Issue in deleting the subclient ")
                flag = 1
                subclient_delete_exception = str(subclient_delete_exception)
                self._LOG.error(
                    "Exception Raised : %s" %
                    subclient_delete_exception)
            finally:
                if flag == 0:
                    self._LOG.info("Subclient deletion Completed")
                    print("Subclient deletion Completed")
                else:
                    self._LOG.error("Subclient deletion Failed ")
                    print("Subclient deletion Failed ")

        def do_help(self, arg):
            'List available commands with "help" or detailed help with "help cmd".'
            is_vsa = False

            if(self._lb_instanceName != None): 
                is_vsa = check_vsa_instance("", self._lb_instanceName)
            else:
                is_vsa = check_vsa_instance("", "Instance001")
            vsa_unsupported_command = ["do_subclient_delete", "do_backup", "do_add_subclient", "do_subclient_update", "do_backup_list", "do_ondemand"]
            #filter te items in names list which are present in vsa unsupported command

            if arg:
                # XXX check arg syntax
                try:
                    func = getattr(self, 'help_' + arg)
                except AttributeError:
                    try:
                        doc=getattr(self, 'do_' + arg).__doc__
                        if doc:
                            self.stdout.write("%s\n"%str(doc))
                            return
                    except AttributeError:
                        pass
                    self.stdout.write("%s\n"%str(self.nohelp % (arg,)))
                    return
                func()
            else:
                names = self.get_names()
                if(is_vsa):
                    filtered_names = [name for name in names if(name not in vsa_unsupported_command)]
                    names = filtered_names
                cmds_doc = []
                cmds_undoc = []
                help = {}
                for name in names:
                    if name[:5] == 'help_':
                        help[name[5:]]=1
                names.sort()
                # There can be duplicates if routines overridden
                prevname = ''
                for name in names:
                    if name[:3] == 'do_':
                        if name == prevname:
                            continue
                        prevname = name
                        cmd=name[3:]
                        if cmd in help:
                            cmds_doc.append(cmd)
                            del help[cmd]
                        elif getattr(self, name).__doc__:
                            cmds_doc.append(cmd)
                        else:
                            cmds_undoc.append(cmd)
                self.stdout.write("%s\n"%str(self.doc_leader))
                self.print_topics(self.doc_header,   cmds_doc,   15,80)
                self.print_topics(self.misc_header,  list(help.keys()),15,80)
                self.print_topics(self.undoc_header, cmds_undoc, 15,80)
 
    # BACKUP-RELATED COMMANDS
    if cvc_backup:
        def do_backup(self, args):
            """
            usage: backup [-h] [-l {full,incremental,synthetic_full,differential}] [-c CLIENTNAME] [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME | -scid SUBCLIENTID] [-path CONTENTPATH [CONTENTPATH ...] | -df DIRECTIVEFILEPATH | -list] [path]

            Backup

            positional arguments:
                    path        File or folder to backup with default options. 
                                Other user provided options will be ignored and default values will be used.
                                    
            optional arguments:
                    -h, --help            show this help message and exit
                    -l {full,incremental,synthetic_full,differential}, --level {full,incremental,synthetic_full,differential}
                                            Backup Level
                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
                    -path CONTENTPATH [CONTENTPATH ...]
                                            Path for adhoc backup
                    -df DIRECTIVEFILEPATH
                                            Directive File Path for adhoc backup
                    -list                 Dynamic list for backup
                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
                    -scid SUBCLIENTID     Subclient ID
                    -sc SUBCLIENTNAME     Subclient Name

            NOTE: VSA Backup operations are not allowed in CVC
            """
            flag = 1
            # print("Backup")
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Backup Operation
            backup_parser = argparse.ArgumentParser(
                description='Backup',
                usage="backup [-h] [-l {full,incremental,synthetic_full,differential}] [-c CLIENTNAME] [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME | -scid SUBCLIENTID] [-path CONTENTPATH [CONTENTPATH ...] | -df DIRECTIVEFILEPATH | -list] [path]",
                epilog="NOTE: VSA Backup operations are not allowed in CVC")
            backup_parser.add_argument(
                dest='path',
                type=str,
                nargs='?',
                help='File or folder to backup with default options. Other user provided options will be ignored and default values will be used.',
                default=None)
            backup_parser.add_argument(
                "-l",
                "--level",
                dest="backuplevel",
                choices=[
                    'full',
                    'incremental',
                    'synthetic_full',
                    'differential'],
                default='incremental',
                type=str,
                help="Backup Level")
            backup_parser.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""))
            backup_parser.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            adhoc_content_group = backup_parser.add_mutually_exclusive_group()
            adhoc_content_group.add_argument(
                '-path',
                dest="contentPath",
                help="Path for adhoc backup",
                nargs='+',
                type=str,
                default=None)
            adhoc_content_group.add_argument(
                '-df',
                dest="directiveFilePath",
                help="Directive File Path for adhoc backup",
                type=str,
                default=None)
            adhoc_content_group.add_argument(
                '-list',
                dest="dynamicList",
                help='Dynamic list for backup',
                action='store_true')
            backup_parser.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            sc_group = backup_parser.add_mutually_exclusive_group()
            sc_group.add_argument(
                '-scid',
                dest="subclientId",
                help="Subclient ID",
                type=str,
                default=None)
            sc_group.add_argument(
                '-sc',
                dest="subClientName",
                help='Subclient Name',
                type=str,
                default=None)

            # Parsing the CMDLINE Input based on above defined structure
            try:
                bargs = backup_parser.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast once  before proceeding with
            # backup
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._is_VSA:
                print("VSA Backup operations are not allowed in CVC")
                return
            self._LOG.info("Backup")
            self._LOG.info(bargs)
            if cvc_restrict_alt_client and bargs.clientName:
                print("Access denied. Local user can operate only on the local client.")
                self._LOG.error(
                    "Operation failed. Passing client name is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
                return
            # check if the instance passed by user is valid
            instanceLoglines = []
            if bargs.instanceName and not bargs.path:
                (flag, instanceLoglines) = check_instance(bargs.instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
                backup_instance = bargs.instanceName
            else:
                backup_instance = 'Instance001'
            commcell_instanceName = backup_instance
            adhoc = 0
            if bargs.path or bargs.contentPath or bargs.directiveFilePath or bargs.dynamicList:
                adhoc = 1
                adHocBackupContent = None
                if bargs.path:
                    adHocBackupContent = [bargs.path]
                elif bargs.contentPath:
                    adHocBackupContent = bargs.contentPath
                elif bargs.dynamicList:
                    self._LOG.info("Adhoc backup with dynamic list")
                    if not self._backup_list:
                        self._LOG.error("Dynamic backup list is empty, cannot perform adhoc backup")
                        print("Dynamic backup list is empty, cannot perform adhoc backup")
                        return
                    else:
                        adHocBackupContent = list(self._backup_list)
                if adHocBackupContent:
                    self._LOG.info(
                        "Adhoc Backup to be run on the following content :" +
                        str(adHocBackupContent))
                    adHocDict = {
                        "adhoc_backup": True,
                        "adhoc_backup_contents": adHocBackupContent}
                else:
                    adHocDict = {
                        "adhoc_backup": True,
                        "directive_file": bargs.directiveFilePath}
            if bargs.path:
                commcell_clientName = None
                commcell_backupSetName = None
                commcell_subClientName = None
                commcell_subclientId = None
                backup_level = 'Incremental'
            else:
                commcell_clientName = bargs.clientName
                commcell_backupSetName = bargs.backupSetName
                commcell_subClientName = bargs.subClientName
                commcell_subclientId = bargs.subclientId
                backup_level = bargs.backuplevel
            common_object = CsCommon(self._commcell_obj)
            checkAdhocClient = 0
            if adhoc:
                if commcell_clientName:
                    checkAdhocClient = 1
            if checkAdhocClient:
                adhocFlag1 = common_object.check_client_exists_in_cs(
                    commcell_clientName)
                if adhocFlag1:
                    adhocFlag2 = common_object.check_adhoc_client(
                        commcell_clientName)
                    if not adhocFlag2:
                        self._LOG.error(
                            "Operation failed. Client passed is not a local instance. Adhoc operation cannot be performed")
                        print(
                            "Operation failed. Client passed is not a local instance. Adhoc operation cannot be performed")
                        return
                else:
                    print(
                        "Operation failed. Client passed is not part of logged in CS.")
                    return
            else:

                # In case of localadmin user, client name should match the name
                # of the local client
                (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                    self, commcell_clientName)
                if status is False:
                    return

                self._LOG.info("Deciding client for the operation")
                clientName = None
                (status, clientName) = common_object.check_client_name(
                    commcell_clientName, commcell_instanceName)
                if status == 0:
                    self._LOG.info("Clientname is decided : %s" % clientName)
                    commcell_clientName = clientName
                else:
                    self._LOG.error("Pass correct Clientname as argument")
                    print("Operation failed. Pass correct Clientname as argument")
                    return
            self._LOG.info("Backup Initiated ")

            # Creation of Instance for Backup class to initiate backup
            # operation
            try:
                backup_obj = backup.Backup(
                    self._loggingPath,
                    self._commcell_obj,
                    backup_level,
                    commcell_clientName,
                    self._commcell_agent,
                    commcell_backupSetName,
                    commcell_subClientName,
                    commcell_subclientId)
                if adhoc:
                    (flag, jobid) = backup_obj.adHocBackup(adHocDict)
                else:
                    (flag, jobid) = backup_obj.backup()
            except NameError as name_error:
                name_error = str(name_error)
                self._LOG.error("NameError Raised :%s" % name_error)
                print(name_error)
                flag = 1
            except Exception as backup_exception:
                flag = 1
                backup_exception = str(backup_exception)
                self._LOG.error(
                    "Exception Raised in Backup Class : %s" %
                    backup_exception)
            finally:
                if flag == 0:
                    self._LOG.info(
                        "{0}Backup Initiated Successfully. Job ID:{1} ".format(
                            'Adhoc ' if adhoc else '', str(jobid)))
                else:
                    print(
                        "{0}Backup Initiation encountered Error".format(
                            'Adhoc ' if adhoc else ''))

        def do_ondemand(self, args):
            """
            usage: ondemand [-h] [-l {full,incremental,synthetic_full,differential}] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME](-d DIRPATH [DIRPATH ...] | -df DIRECTIVEFILE) [-dsp DSP]

            Ondemand Backup

            optional arguments:
                    -h, --help            show this help message and exit
                    -l {full,incremental,synthetic_full,differential}, --level {full,incremental,synthetic_full,differential}
                                            Backup Level
                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
                    -d DIRPATH [DIRPATH ...], --dir DIRPATH [DIRPATH ...]
                                            Paths for ondemand backup
                    -df DIRECTIVEFILE, --directivefile DIRECTIVEFILE
                                            Directive file-it should be in current machine from
                                            which the command is executed
                    -dsp DSP, --defaultstoragepolicy DSP
                                            content parameter and storage policy parameters are
                                            mandatory for Ondemand backup
            NOTE: VSA Backup operations are not allowed in CVC
            """
            flag = 1
            # print("OnDemand Backup")
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Ondemand Backup Operation
            ondemand_parser = argparse.ArgumentParser(
                description='Ondemand Backup',
                usage="ondemand [-h] [-l {full,incremental,synthetic_full,differential}] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME](-d DIRPATH [DIRPATH ...] | -df DIRECTIVEFILE) [-dsp DSP]", epilog="NOTE: VSA Backup operations are not allowed in CVC")
            ondemand_parser.add_argument(
                "-l",
                "--level",
                dest="backuplevel",
                choices=[
                    'full',
                    'incremental',
                    'synthetic_full',
                    'differential'],
                default='full',
                type=str,
                help="Backup Level")
            ondemand_parser.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name")
            ondemand_parser.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            ondemand_parser.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            backup_group_path = ondemand_parser.add_mutually_exclusive_group(
                required=True)
            backup_group_path.add_argument(
                "-d",
                "--dir",
                nargs='+',
                dest="dirpath",
                default=None,
                type=str,
                help="Paths for ondemand backup")
            backup_group_path.add_argument(
                "-df",
                "--directivefile",
                dest="directivefile",
                default=None,
                type=str,
                help="Directive file-it should be in current machine from which the command is executed")
            ondemand_parser.add_argument(
                "-dsp",
                "--defaultstoragepolicy",
                type=str,
                default=None,
                dest="dsp",
                required=True,
                help="content parameter and storage policy parameters\
									are mandatory for Ondemand backup")
            # Parsing the CMDLINE Input based on above defined structure
            try:
                oargs = ondemand_parser.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast once  before proceeding with
            # ondemand backup
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._is_VSA:
                print("Operation not allowed for VSA in CVC")
                return
            self._LOG.info("OnDemand Backup")
            # Reading the values passed as arguments
            commcell_clientName = oargs.clientName
            commcell_instanceName = oargs.instanceName
            commcell_subClientName = 'ondemand'
            commcell_backupSetName = oargs.backupSetName
            backup_level = oargs.backuplevel
            # check if the instance passed by user is valid
            instanceLoglines = []
            if commcell_instanceName:
                (flag, instanceLoglines) = check_instance(commcell_instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
            else:
                commcell_instanceName = 'Instance001'

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            elif oargs.clientName is None:
                print("Need to pass clientname as parameter in cmdline")
                return
            else:
                print('Please verify the provided client name and check '
                      'whether the user has access on client: {0}'.format(commcell_clientName))
                return
            if oargs.dsp is None:
                print("Missing Mandatory argument ")
                self._LOG.warn(
                    "Its mandatory to pass storage policy for ondemand backup")
                return
            else:
                self._LOG.info("Storage Policy Set")
                backup_sp = oargs.dsp
            if oargs.dirpath:
                backup_dirpath = oargs.dirpath
                backup_paths = backup_dirpath
            elif oargs.directivefile:
                backup_directivefile = oargs.directivefile
                self._LOG.info("Directive File List Option Chosen")
                filename = str(backup_directivefile)
                (status, backup_paths) = common_object.read_file_list(filename)
                if status is True:
                    self._LOG.info(
                        "Backup paths fetched successfully from file")
                else:
                    print("Error while reading filelist")
                    return
            else:
                print("Any one of the  parameter : Directivefile or Directorypath is mandatory for ondemand backup.exiting the process")
                return
            self._LOG.info(
                "Backup will be initiated on below defined contents : On Demand Backup ")
            self._LOG.info(backup_paths)
            # Creation of Instance for Backup class to initiate ondemand backup
            # operation
            try:
                backup_on_obj = backup.Backup(
                    self._loggingPath,
                    self._commcell_obj,
                    backup_level,
                    commcell_clientName,
                    self._commcell_agent,
                    commcell_backupSetName,
                    commcell_subClientName)
                (flag, jobid) = backup_on_obj.ondemand_backup(
                    backup_paths, backup_sp)
            except NameError as name_error:
                name_error = str(name_error)
                self._LOG.error("NameError Raised :%s" % name_error)
                print(name_error)
                flag = 1
            except Exception as backup_exception:
                flag = 1
                self._LOG.error("Exception Raised in Backup Class : ")
                self._LOG.error(backup_exception)
            finally:
                if flag == 0:
                    self._LOG.info("Ondemand Backup Initiated Succesfully")
                    print("Job ID : %s" % str(jobid))
                else:
                    self._LOG.error(
                        "Ondemand Backup Operation encountered Error")
                    print("Ondemand Backup Operation encountered Error")

        def do_backup_list(self, args):
            """
            usage: backup_list [-h]

            backup list

            optional arguments:
                    -h, --help  show this help message and exit
            
            NOTE: VSA Backup operations are not allowed in CVC
            """
            k = shlex.split(args)
            backup_list_parser = argparse.ArgumentParser(
                description='backup list', usage="backup_list [-h]", epilog="NOTE: VSA Backup operations are not allowed in CVC")
            try:
                margs = backup_list_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._is_VSA:
                print("VSA Backup operations are not allowed in CVC")
                return
            self._LOG.info("Setting backup list as current list")
            # indicating that list operations are to be done on backup list
            self._current_list_operation = 0
            self._LOG.info(
                "Any subsequent list operation will be specific to backup list")

    # RECOVER-RELATED COMMANDS
    if cvc_recover:
        def do_browse(self, args):
            """
            usage: browse [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME] [-p BROWSEPATH] [-ftime FROMTIME]  [-ttime TOTIME] [-allVersions] [path] [-sd SHOWDELETEDITEMS {True,False}]

            Browse

            positional arguments:
                    path        Path for browse with default options. This overrides
                                            the user provided values and instead default values
                                            are chosen

            optional arguments:
                    -h, --help            show this help message and exit
                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
                    -sc SUBCLIENTNAME, --subclient SUBCLIENTNAME
                                            Name to be passed even in case of default subclient
                    -p BROWSEPATH, -path BROWSEPATH, --path BROWSEPATH
                                            Browse Path
                    -ftime FROMTIME, --fromtime FROMTIME
                                            The start time of the backup window that you specify 
                                            for a point-in-time browse operation. 
                                            The format is yyyy-mm-dd hh:mm:ss.
                    -ttime TOTIME, --totime TOTIME
                                            The end time of the backup window that you specify 
                                            for a point-in-time browse operation. 
                                            The format is yyyy-mm-dd hh:mm:ss.
                    -allVersions          Show all versions. For VSA, Index files after backup option must be enabled on VM group.
                    -filter BROWSE_FILTER [BROWSE_FILTER ...], --browseFilter BROWSE_FILTER [BROWSE_FILTER ...]
                                    File name filters for the browse
                    -cp COPY_PRECEDENCE, --copyPrecedence COPY_PRECEDENCE
                                    Copy Precedence
                    -sd {True,False}      Show deleted items {True,False}. False by default
            
            """
            flag = 1
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Browse
            bp = argparse.ArgumentParser(
                description='Browse',
                usage="browse [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME] [-p BROWSEPATH] [-ftime FROMTIME]  [-ttime TOTIME] [-allVersions] [path] [-sd SHOWDELETEDITEMS {True,False}]")
            bp.add_argument(
                dest='path',
                type=str,
                nargs='?',
                help='Path for browse with default options. This overrides the user provided values and instead default values are chosen',
                default=None)
            bp.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""))
            bp.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            bp.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            bp.add_argument(
                "-sc",
                "--subclient",
                type=str,
                help="Name to be passed even in case of default subclient",
                default=None,
                dest="subClientName")
            bp.add_argument(
                "-p",
                "-path",
                "--path",
                dest="browsepath",
                default=None,
                type=str,
                help="Browse Path")
            bp.add_argument(
                "-ftime",
                "--fromtime",
                dest="fromtime",
                default=0,
                help="The start time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.")
            bp.add_argument(
                "-ttime",
                "--totime",
                dest="totime",
                default=0,
                help="The end time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.")
            bp.add_argument(
                '-allVersions',
                dest="allVersions",
                help='Option to browse all versions. For VSA, Index files after backup option must be enabled on VM group.',
                action='store_true')
            bp.add_argument(
                "-filter",
                "--browseFilter",
                dest="browse_filter",
                nargs='+',
                type=str,
                default=None,
                help="File name filters for the browse")
            bp.add_argument(
                "-cp",
                "--copyPrecedence",
                dest="copy_precedence",
                type=int,
                default=None,
                help="Copy Precedence")
            sd = cvc_default_show_deleted
            bp.add_argument(
                '-sd',
                dest="show_deleted",
                help='Show deleted items {True,False}. %s by default' %
                str(sd),
                default=str(sd),
                choices=[
                    'True',
                    'False'])
            # Parsing the CMDLINE Input based on above defined structure
            try:
                sargs = bp.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast before proceeding with browse
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            if cvc_restrict_alt_client and sargs.clientName is not None:
                print("Access denied. Local user can operate only on the local client.")
                self._LOG.error(
                    "Operation failed. Passing client name is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
                return

            # Reading the values passed as arguments
            self._LOG.info("Browse")
            # check if the instance passed by user is valid
            instanceLoglines = []
            if sargs.instanceName and not sargs.path:
                (flag, instanceLoglines) = check_instance(sargs.instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
                browse_instance = sargs.instanceName
            elif not sargs.instanceName and not sargs.path and self._lb_initialized and self._lb_instanceName:
                browse_instance = self._lb_instanceName
                self._LOG.info("Using browse options")
                self._LOG.info("Updated instance: " + browse_instance)
            else:
                browse_instance = 'Instance001'
            commcell_instanceName = browse_instance

            if sargs.path:
                browse_path = sargs.path
                commcell_clientName = None
                commcell_backupSetName = None
                commcell_subClientName = None
                fromtime = 0
                totime = 0
                allVersions = False
                browse_filter = None
                copy_precedence = None
                show_deleted = sd
            else:
                if sargs.browsepath:
                    browse_path = sargs.browsepath
                elif self._lb_initialized and self._live_browse_path and self._live_browse_path != '':
                    browse_path = self._live_browse_path
                    self._LOG.info(
                        "Updated path after using browse options: " +
                        browse_path)
                else:
                    self._LOG.info(
                        "Path not passed in the browse command and browse options are not initialized")
                    self._LOG.info(
                        "Current working directory of local machine to be considered as browse path.")
                    browse_path = os.getcwd()
                commcell_clientName = sargs.clientName
                commcell_backupSetName = sargs.backupSetName
                commcell_subClientName = sargs.subClientName
                fromtime = sargs.fromtime
                totime = sargs.totime
                allVersions = sargs.allVersions
                browse_filter = sargs.browse_filter
                copy_precedence = sargs.copy_precedence
                if sargs.show_deleted == 'True':
                    show_deleted = True
                else:
                    show_deleted = False
                
                if not copy_precedence:
                    copy_precedence = check_copy_precedence_registry(commcell_instanceName)
                if self._lb_initialized:
                    if not commcell_clientName and self._lb_clientName:
                        commcell_clientName = self._lb_clientName
                        self._LOG.info(
                            "Updated client after using browse options: " +
                            commcell_clientName)
                    if not commcell_backupSetName and self._lb_backupSetName:
                        commcell_backupSetName = self._lb_backupSetName
                        self._LOG.info(
                            "Updated backupset after using browse options: " +
                            commcell_backupSetName)
                    if not commcell_subClientName and self._lb_subClientName:
                        commcell_subClientName = self._lb_subClientName
                        self._LOG.info(
                            "Updated subclient after using browse options: " +
                            commcell_subClientName)
                    if fromtime == 0 and self._lb_fromtime != 0:
                        fromtime = self._lb_fromtime
                        self._LOG.info(
                            "Updated fromtime after using browse options: " +
                            str(fromtime))
                    if totime == 0 and self._lb_totime != 0:
                        totime = self._lb_totime
                        self._LOG.info(
                            "Updated totime after using browse options: " + str(totime))

            filters = []
            if browse_filter:
                browse_filter_string = ""
                for browse_filter_element in browse_filter:
                    browse_filter_string = "{0}{1}{2}".format(
                        browse_filter_string,
                        " OR " if browse_filter_string != "" else "",
                        browse_filter_element)
                filters = [('FileName', browse_filter_string)]

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            elif sargs.clientName is None:
                print("Need to pass clientname as parameter in cmdline")
                return
            else:
                print('Please verify the provided client name and check '
                      'whether the user has access on client: {0}'.format(commcell_clientName))
                return
            # Creation of Instance for Browse class to initiate browse
            # operation
            try:
                if self._is_VSA:	        
                    if Entity.client_name != commcell_clientName:
                        Entity.client = self._commcell_obj.clients.get(commcell_clientName)
                        self._vsa_guid = Entity.client.vm_guid
                        if not self._vsa_guid:
                            print("Operation failed. Could not find GUID for VM ", commcell_clientName)
                            return

                self.browse_obj = browse.Browse(
                    package_instance=commcell_instanceName,
                    commcell_object=self._commcell_obj,
                    client_name=commcell_clientName,
                    agent_name=self._commcell_agent,
                    backupset_name=commcell_backupSetName,
                    logger_object=self._LOG,
                    tempFolder=self._loggingPath
                )

                self.browse_obj.live_browse_path = self._live_browse_path
                flag = self.browse_obj.qlist_browse(
                    operation='All versions' if allVersions else 'Browse',
                    subclient_name=commcell_subClientName,
                    path=browse_path,
                    from_time=fromtime,
                    to_time=totime,
                    filters=filters,	
                    vsa_guid=self._vsa_guid,
                    copy_precedence=copy_precedence,
                    show_deleted=show_deleted)

            except NameError as name_error:
                name_error = str(name_error)
                self._LOG.error("NameError Raised :%s" % name_error)
                print(name_error)
                flag = 1
            except Exception as browse_exception:
                print("Error Occurred During Browse : Refer Logs for details ")
                browse_exception = str(browse_exception)
                self._LOG.error(
                    "Exception occurred while initiating  browse operation :%s " %
                    browse_exception)
            finally:
                if flag == 0:
                    return
                else:
                    print("Browse Operation encountered Error")

        def do_find(self, args):
            """
            usage: find [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME] -f FILENAME
            [-path FINDPATH] [-ftime FROMTIME]  [-ttime TOTIME] [-sd SHOWDELETEDITEMS {True,False}]

            Find

            optional arguments:
                    -h, --help            show this help message and exit

                    -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name

                    -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name

                    -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name

                    -sc SUBCLIENTNAME, --subclient SUBCLIENTNAME
                                            Name to be passed even in case of default subclient

                    -path FINDPATH, --path FINDPATH
                                            Path to perform find operation on

                    -f FILENAME, --filename FILENAME
                                            File or Folder Name

                    -ftime FROMTIME, --fromtime FROMTIME
                                            The start time of the backup window that you specify 
                                            for a point-in-time find operation. 
                                            The format is yyyy-mm-dd hh:mm:ss.

                    -ttime TOTIME, --totime TOTIME
                                            The end time of the backup window that you specify 
                                            for a point-in-time find operation. 
                                            The format is yyyy-mm-dd hh:mm:ss.
                    
                    -cp COPY_PRECEDENCE, --copyPrecedence COPY_PRECEDENCE
                                            Copy Precedence
                                            
                    -sd {True,False}        Show deleted items {True,False}. False by default
            """
            # print("Find")
            flag = 1
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Find Operation
            fp = argparse.ArgumentParser(
                description='Find',
                usage="find [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME] -f FILENAME"
                      " [-path FINDPATH] [-ftime FROMTIME]  [-ttime TOTIME] [-sd SHOWDELETEDITEMS {True,False}]")
            fp.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""))
            fp.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            fp.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            fp.add_argument(
                "-sc",
                "--subclient",
                type=str,
                help="Name to be passed even in case of default subclient",
                default=None,
                dest="subClientName")
            fp.add_argument(
                "-f",
                "--filename",
                dest="filename",
                default=None,
                required=True,
                type=str,
                help="File or Folder Name")
            fp.add_argument(
                "-path",
                "--path",
                dest="findpath",
                default=None,
                type=str,
                help="Path to perform find on")
            fp.add_argument(
                "-ftime",
                "--fromtime",
                dest="fromtime",
                default=0,
                help="The start time of the backup window that you specify for a point-in-time find operation. The format is yyyy-mm-dd hh:mm:ss.")
            fp.add_argument(
                "-ttime",
                "--totime",
                dest="totime",
                default=0,
                help="The end time of the backup window that you specify for a point-in-time find operation. The format is yyyy-mm-dd hh:mm:ss.")
            fp.add_argument(
                "-cp",
                "--copyPrecedence",
                dest="copy_precedence",
                type=int,
                default=None,
                help="Copy Precedence")
            sd = cvc_default_show_deleted
            fp.add_argument(
                '-sd',
                dest="show_deleted",
                help='Show deleted items {True,False}. %s by default' %
                str(sd),
                default=str(sd),
                choices=[
                    'True',
                    'False'])
            # Parsing the CMDLINE Input based on above defined structure
            try:
                fargs = fp.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast before proceeding with Find
            # operation
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            if cvc_restrict_alt_client and fargs.clientName is not None:
                print("Access denied. Local user can operate only on the local client.")
                self._LOG.error(
                    "Operation failed. Passing client name is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
                return

            self._LOG.info("Find")
            # Reading the values passed as arguments
            commcell_clientName = fargs.clientName
            commcell_instanceName = fargs.instanceName
            filename = fargs.filename
            commcell_backupSetName = fargs.backupSetName
            commcell_subClientName = fargs.subClientName
            fromtime = fargs.fromtime
            totime = fargs.totime
            find_path = fargs.findpath
            copy_precedence = fargs.copy_precedence
            if fargs.show_deleted == 'True':
                show_deleted = True
            else:
                show_deleted = False
            # check if the instance passed by user is valid
            instanceLoglines = []
            if commcell_instanceName:
                (flag, instanceLoglines) = check_instance(commcell_instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
            else:
                commcell_instanceName = 'Instance001'

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            elif fargs.clientName is None:
                print("Need to pass clientname as parameter in cmdline")
                return
            else:
                print('Please verify the provided client name and check '
                      'whether the user has access on client: {0}'.format(commcell_clientName))
                return
            
            filters = []
            if filename:
                filters = [('FileName', filename)]

            if not copy_precedence:
                copy_precedence = check_copy_precedence_registry(commcell_instanceName)

            # Creation of Instance for Browse class to initiate find operation
            try:
                if self._is_VSA:                                               
                    if Entity.client_name != commcell_clientName:
                        Entity.client = self._commcell_obj.clients.get(commcell_clientName)
                        self._vsa_guid = Entity.client.vm_guid
                        if not self._vsa_guid:
                            print("Operation failed. Could not find GUID for VM ", commcell_clientName)
                            return

                self.browse_obj = browse.Browse(
                    package_instance=commcell_instanceName,
                    commcell_object=self._commcell_obj,
                    client_name=commcell_clientName,
                    agent_name=self._commcell_agent,
                    backupset_name=commcell_backupSetName,
                    logger_object=self._LOG,
                    tempFolder=self._loggingPath
                )

                self.browse_obj.live_browse_path = self._live_browse_path
                flag = self.browse_obj.qlist_browse(
                    operation='Find',
                    subclient_name=commcell_subClientName,
                    path=find_path,
                    from_time=fromtime,
                    to_time=totime,
                    filters=filters,
                    vsa_guid=self._vsa_guid,
                    copy_precedence=copy_precedence,
                    show_deleted=show_deleted
                )

            except NameError as name_error:
                name_error = str(name_error)
                self._LOG.error("NameError Raised :%s" % name_error)
                print(name_error)
                flag = 1
            except Exception as find_exception:
                print("Error Occurred During Find : Refer Logs for details ")
                find_exception = str(find_exception)
                self._LOG.error(
                    "Exception occurred while initiating  find operation :%s " %
                    find_exception)
            finally:
                if flag == 0:
                    return
                else:
                    self._LOG.error("Find Operation encountered Error")
                    print("Find Operation encountered Error")

        def do_restore(self, args):
            """
            usage: restore [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME]
            [-sc SUBCLIENTNAME][-path SOURCEPATH [SOURCEPATH ...] | -l RESTOREFILELIST | -list])
            [-dc DESTCLIENT] [-dp DESTPATH] [-ftime FROMTIME] [-ttime TOTIME] [-versions VERSIONS]
            [-uo UNCONDITIONALOVERWRITE {True,False}] [-filter BROWSE_FILTER [BROWSE_FILTER ...]]
            [path] [-sd SHOWDELETEDITEMS {True,False}]

            Restore

            positional arguments:
              path                  File or folder to restore with default options. 
                                    Other user provided options will be ignored and default values will be used.

            optional arguments:
              -h, --help            show this help message and exit
              -c CLIENTNAME, --clientname CLIENTNAME
                                    Client Name
              -i INSTANCENAME, --instancename INSTANCENAME
                                    Instance Name
              -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                    Backupset Name
              -sc SUBCLIENTNAME, --subclient SUBCLIENTNAME
                                    Name to be passed even in case of default subclient
              -path SOURCEPATH [SOURCEPATH ...], --path SOURCEPATH [SOURCEPATH ...]
                                    Path for restore
              -l RESTOREFILELIST, --filelist RESTOREFILELIST
                                    restorelist file should be present in the machine from
                                    which the command is executed
              -list                 Dynamic list for restore
              -dc DESTCLIENT, --destinationClient DESTCLIENT
                                    Destination Client
              -dp DESTPATH, --destinationPath DESTPATH
                                    Destination Path
              -ftime FROMTIME, --fromtime FROMTIME
                                    The start time of the backup window that you specify 
                                    for a point-in-time restore operation. 
                                    The format is yyyy-mm-dd hh:mm:ss.
              -ttime TOTIME, --totime TOTIME
                                    The end time of the backup window that you specify 
                                    for a point-in-time restore operation. 
                                    The format is yyyy-mm-dd hh:mm:ss.
              -versions VERSIONS, --versions VERSIONS
                                    Versions to be restored. "All" or "all" or list of
                                    version numbers such as "1,2,5"

              -uo {True,False}      Unconditional Overwrite {True,False}. False by default
              -filter BROWSE_FILTER [BROWSE_FILTER ...], --browseFilter BROWSE_FILTER [BROWSE_FILTER ...]
                                    Browse Filters
              -cp COPY_PRECEDENCE, --copyPrecedence COPY_PRECEDENCE
                                    Copy Precedence
              -sd {True,False}      Show deleted items {True,False}. Set this to True to restore deleted items. False by default.
            """
            flag = 1
            # print("Restore")
            # Reading the Cmdline Argument
            k = shlex.split(args)
            # Defining Parser Command Structure for Restore Operation
            rp = argparse.ArgumentParser(
                description='Restore',
                usage="restore [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME]"
                "[-path SOURCEPATH [SOURCEPATH ...] | -l RESTOREFILELIST | -list])"
                "[-dc DESTCLIENT] [-dp DESTPATH] [-ftime FROMTIME] [-ttime TOTIME] [-versions VERSIONS]"
                "[-uo UNCONDITIONALOVERWRITE {True,False}] [-filter BROWSE_FILTER [BROWSE_FILTER ...]] [path]"
                "[-sd SHOWDELETEDITEMS {True,False}]")
            rp.add_argument(
                dest='path',
                type=str,
                nargs='?',
                help='File or folder to restore with default options. Other user provided options will be ignored and default values will be used.',
                default=None)
            rp.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""))
            rp.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            rp.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            rp.add_argument(
                "-sc",
                "--subclient",
                type=str,
                help="Name to be passed even in case of default subclient",
                default=None,
                dest="subClientName")
            restore_group_path = rp.add_mutually_exclusive_group()
            restore_group_path.add_argument(
                "-path",
                "--path",
                nargs='+',
                dest="sourcepath",
                default=None,
                type=str,
                help="Path for restore")
            restore_group_path.add_argument(
                "-l",
                "--filelist",
                dest="restorefilelist",
                default=None,
                type=str,
                help="restorelist file should be present in the machine from which the command is executed")
            restore_group_path.add_argument(
                '-list',
                dest="dynamicList",
                help='Dynamic list for restore',
                action='store_true')
            rp.add_argument(
                "-dc",
                "--destinationClient",
                dest="destclient",
                default=None,
                type=str,
                help="Destination Client {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""))
            rp.add_argument(
                "-dp",
                "--destinationPath",
                dest="destpath",
                default=None,
                type=str,
                help="Destination Path")
            rp.add_argument(
                "-ftime",
                "--fromtime",
                dest="fromtime",
                default=0,
                help="The start time of the backup window that you specify for a point-in-time restore operation. The format is yyyy-mm-dd hh:mm:ss.")
            rp.add_argument(
                "-ttime",
                "--totime",
                dest="totime",
                default=0,
                help="The end time of the backup window that you specify for a point-in-time restore operation. The format is yyyy-mm-dd hh:mm:ss.")
            rp.add_argument(
                "-versions",
                "--versions",
                dest="versions",
                help='Versions to be restored. "All" or "all" or list of version numbers such as "1,2,5".',
                type=str,
                default=None)
            uo = cvc_restore_default_overwrite
            rp.add_argument(
                '-uo',
                dest="unconditional_overwrite",
                help='Unconditional Overwrite {True,False}. %s by default' %
                str(uo),
                default=str(uo),
                choices=[
                    'True',
                    'False'])
            rp.add_argument(
                "-filter",
                "--browseFilter",
                dest="browse_filter",
                nargs='+',
                type=str,
                default=None,
                help="Browse Filters")
            rp.add_argument(
                "-cp",
                "--copyPrecedence",
                dest="copy_precedence",
                type=int,
                default=None,
                help="Copy Precedence")
            sd = cvc_default_show_deleted
            rp.add_argument(
                '-sd',
                dest="show_deleted",
                help='Show deleted items {True,False}. Set this to True to restore deleted items. %s by default.' %
                str(sd),
                default=str(sd),
                choices=[
                    'True',
                    'False'])

            # Parsing the CMDLINE Input based on above defined structure
            try:
                margs = rp.parse_args(k)
            except SystemExit:
                return
            # Verify if login is executed atleast before proceeding with
            # Restore
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            if cvc_restrict_alt_client and (
                    margs.clientName is not None or margs.destclient is not None):
                print("Access denied. Local user can operate only on the local client.")
                self._LOG.error(
                    "Operation failed. Passing client name / destination client is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
                return

            self._LOG.info("Restore")
            instanceLoglines = []
            if margs.instanceName and not margs.path:
                (flag, instanceLoglines) = check_instance(margs.instanceName)
                print_log_lines(instanceLoglines)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    return
                restore_instance = margs.instanceName
            elif not margs.instanceName and not margs.path and self._lb_initialized and self._lb_instanceName:
                restore_instance = self._lb_instanceName
                self._LOG.info("Using browse options")
                self._LOG.info("Updated instance: " + restore_instance)
            else:
                restore_instance = 'Instance001'
            commcell_instanceName = restore_instance
            # Reading the values passed as arguments
            if margs.path:
                self._LOG.info("Restore with default options")
                restore_sourcepath = [margs.path]
                restore_filelist = None
                restore_dynamicList = False
                commcell_clientName = None
                commcell_backupSetName = None
                commcell_subClientName = None
                commcell_destclient = None
                commcell_destpath = None
                commcell_fromTime = None
                commcell_toTime = None
                restore_versions = None
                browse_filter = None
                restore_unconditionalOverwrite = uo
                show_deleted = sd
                copy_precedence = None
            else:
                restore_sourcepath = margs.sourcepath
                restore_filelist = margs.restorefilelist
                restore_dynamicList = margs.dynamicList
                commcell_clientName = margs.clientName
                commcell_backupSetName = margs.backupSetName
                commcell_subClientName = margs.subClientName
                commcell_destclient = margs.destclient
                commcell_destpath = margs.destpath
                commcell_fromTime = margs.fromtime
                commcell_toTime = margs.totime
                restore_versions = margs.versions
                browse_filter = margs.browse_filter
                copy_precedence = margs.copy_precedence
                if margs.show_deleted == 'True':
                    show_deleted = True
                else:
                    show_deleted = False
                if margs.unconditional_overwrite == 'True':
                    restore_unconditionalOverwrite = True
                else:
                    restore_unconditionalOverwrite = False
                if self._lb_initialized:
                    if not commcell_clientName and self._lb_clientName:
                        commcell_clientName = self._lb_clientName
                        self._LOG.info(
                            "Updated client after using browse options: " +
                            commcell_clientName)
                    if not commcell_backupSetName and self._lb_backupSetName:
                        commcell_backupSetName = self._lb_backupSetName
                        self._LOG.info(
                            "Updated backupset after using browse options: " +
                            commcell_backupSetName)
                    if not commcell_subClientName and self._lb_subClientName:
                        commcell_subClientName = self._lb_subClientName
                        self._LOG.info(
                            "Updated subclient after using browse options: " +
                            commcell_subClientName)
                    if commcell_fromTime == 0 and self._lb_fromtime != 0:
                        commcell_fromTime = self._lb_fromtime
                        self._LOG.info(
                            "Updated fromtime after using browse options: " +
                            str(commcell_fromTime))
                    if commcell_toTime == 0 and self._lb_totime != 0:
                        commcell_toTime = self._lb_totime
                        self._LOG.info(
                            "Updated totime after using browse options: " +
                            str(commcell_toTime))

            # In case of localadmin user, client name should match the name of
            # the local client
            (status, commcell_clientName) = check_qlogin_localadmin_chosen(
                self, commcell_clientName)
            if status is False:
                return

            # Check if client name is passed or not
            common_object = CsCommon(self._commcell_obj)
            (status, clientName) = common_object.check_client_name(
                commcell_clientName, commcell_instanceName)
            if status == 0:
                self._LOG.info("Clientname is decided : %s" % clientName)
                commcell_clientName = clientName
            elif margs.clientName is None:
                print("Need to pass clientname as parameter in cmdline")
                return
            else:
                print('Please verify the provided client name and check '
                      'whether the user has access on client: {0}'.format(commcell_clientName))
                return
            if restore_sourcepath:
                restore_paths = restore_sourcepath
            elif restore_filelist:
                self._LOG.info(" File List Option Chosen")
                filename = str(restore_filelist)
                (status, restore_paths) = common_object.read_file_list(filename)
                if status is True:
                    self._LOG.info(
                        "Backup paths fetched successfully from file")
                else:
                    print("Error while reading filelist")
                    return
            elif restore_dynamicList:
                self._LOG.info("Restore with dynamic list")
                if self._restore_list:
                    self._LOG.info(f"Dynamic list content: {self._restore_list}")
                    restore_paths = list(self._restore_list)
                else:
                    self._LOG.error("Dynamic restore list is empty. Cannot perform restore")
                    print("Dynamic restore list is empty. Cannot perform restore")
                    return
            elif self._lb_initialized and self._live_browse_path and self._live_browse_path != '':
                restore_paths = [self._live_browse_path]
                self._LOG.info(
                    "Updated restore paths after using browse options: " +
                    str(restore_paths))
            elif commcell_clientName == self._qlogin_local_client:
                self._LOG.info(
                    "Setting current directory as the directory for restore")
                restore_paths = [os.getcwd()]
            else:
                print("Insufficient Parameters for Performing restore Operation : either specify the directory path or RestoreFile which contains the list of items to be restored")
                self._LOG.error(
                    "Insufficient Parameters for Performing restore Operation : either specify the directory path or RestoreFile which contains the list of items to be restored")
                return
            # Find out the versions to be restored. By default, latest version
            # is restored.
            options = {}
            options['no_image'] = show_deleted
            try:
                if restore_versions is not None:
                    if restore_versions.lower() == "all":
                        options = {'all_versions': True}
                    else:
                        versionList = restore_versions.split(',')
                        # print(versionList)
                        for item in versionList:
                            if item.isdigit() is False:
                                self._LOG.error(
                                    "Version numbers must be digits only")
                                print("Incorrect format of version numbers")
                                print("Restore  Initiation  encountered Error")
                                return
                        versionList1 = list(map(int, versionList))
                        options = {'versions': versionList1}
            except Exception as version_fetch_exception:
                version_fetch_exception = str(version_fetch_exception)
                self._LOG.error(
                    "Error while fetching version information" +
                    version_fetch_exception)
                print("Error while fetching version information")
                return
            if browse_filter:
                xml_string = "<?xml version='1.0' encoding='UTF-8'?><databrowse_Query type=\"0\" queryId=\"0\"><whereClause connector=\"0\"><criteria field=\"0\"><values val=\"{0}\"/></criteria></whereClause><dataParam><sortParam ascending=\"1\"><sortBy val=\"38\" /><sortBy val=\"0\" /></sortParam><paging firstNode=\"0\" pageSize=\"1000\" skipNode=\"0\" /></dataParam></databrowse_Query>"
                browse_filter_string = ""
                for browse_filter_element in browse_filter:
                    browse_filter_string = "{0}{1}{2}".format(
                        browse_filter_string,
                        " OR " if browse_filter_string != "" else "",
                        browse_filter_element)
                xml_string = xml_string.format(browse_filter_string)
                options["browse_filters"] = [xml_string]

            options['cvcBrowse'] = True

            if commcell_destclient is not None:
                # In case of localadmin user, destination client name should
                # match the name of the local client
                (status, commcell_destclient) = check_qlogin_localadmin_chosen(
                    self, commcell_destclient)
                if status is False:
                    return

            if copy_precedence:
                self._LOG.info("Copy precedence set to " + str(copy_precedence))

            if platform.system() == "Linux":
                if os.geteuid() != 0:

                    if Entity.client_name != commcell_clientName:
                        Entity.client = self._commcell_obj.clients.get(commcell_clientName)
                        Entity.separator = '\\' if 'windows' in Entity.client.os_info.lower() else '/'
                        Entity.client_name = commcell_clientName
                        self._vsa_guid = Entity.client.vm_guid

                    paths = []
                    for path in restore_paths:
                        if self._is_VSA:
                            if not self._vsa_guid:
                                print("Operation failed. Could not find GUID for VM ", commcell_clientName)
                                return
                            path = '\\' + self._vsa_guid.rstrip("\n") + Entity._get_absolute_path(path, self._live_browse_path).replace('/', '\\')
                            paths.append(path)
                        else:
                            paths.append(Entity._get_absolute_path(path, self._live_browse_path))

                    rcode = common_object.restore_non_root_user(
                        paths,
                        commcell_clientName,
                        self._commcell_agent,
                        commcell_instanceName,
                        commcell_backupSetName,
                        commcell_subClientName,
                        commcell_destclient,
                        commcell_destpath,
                        commcell_fromTime,
                        commcell_toTime,
                        None,
                        options,
                        restore_unconditionalOverwrite,
                        copy_precedence,
                        is_vsa=self._is_VSA,
                        tempPath=self._loggingPath)
                    if rcode:
                        self._LOG.error("Restore job encountered error")
                        print("Restore job encountered error")
                    return
            # Creation of Instance for Restore class to initiate restore
            # operation
            try:
                if self._is_VSA:
                    if Entity.client_name != commcell_clientName:
                        Entity.client = self._commcell_obj.clients.get(commcell_clientName)
                        self._vsa_guid = Entity.client.vm_guid
                        if not self._vsa_guid:
                            print("Operation failed. Could not find GUID for VM ", commcell_clientName)
                            return
                self._LOG.info("Creating object for Restore class")
                restore_obj = restore.Restore(
                    package_instance=commcell_instanceName,
                    commcell_object=self._commcell_obj,
                    client_name=commcell_clientName,
                    agent_name=self._commcell_agent,
                    backupset_name=commcell_backupSetName,
                    subclient_name=commcell_subClientName,
                    logger_object=self._LOG
                )
                self._LOG.info("Successfully created")

                restore_obj.live_restore_path = self._live_browse_path
                # Checks if it is In-Place or Out-of-Place Restore , accordingly
                # invokes the method
                if commcell_destclient:
                    self._LOG.info("Restore out of place")
                    if commcell_destpath is None:
                        print(
                            "Destination Path is mandatory for Out of place restore.Pass it in CMDLINE")
                        return
                    else:
                        restore_destpath = commcell_destpath
                        restore_destclient = commcell_destclient
                        flag, jobid = restore_obj.restore_out_of_place(
                            paths=restore_paths,
                            destination_client=restore_destclient,
                            destination_path=restore_destpath,
                            from_time=commcell_fromTime,
                            to_time=commcell_toTime,
                            fs_options=options,
                            unconditional_overwrite=restore_unconditionalOverwrite,
                            copy_precedence=copy_precedence,
                            vsa_guid=self._vsa_guid)
                else:
                    if commcell_destpath is None:
                        if self._is_VSA:
                            dest_path = dest_inplace_restore(restore_paths)
                            if dest_path == '':
                                print("In-Place restore is not supported with multiple source paths. Please provide destination path manually.")
                                return
                            else:
                                self._LOG.info(
                                    "Proceeding with restore on source client with destination path : "+ str(dest_path))
                                flag, jobid = restore_obj.restore_out_of_place(
                                    paths=restore_paths,
                                    destination_client=commcell_clientName,
                                    destination_path=dest_path,
                                    from_time=commcell_fromTime,
                                    to_time=commcell_toTime,
                                    fs_options=options,
                                    unconditional_overwrite=restore_unconditionalOverwrite,
                                    copy_precedence=copy_precedence,
                                    vsa_guid=self._vsa_guid)
                        else:
                            self._LOG.info(
                                "Destination client and Destination path is empty . so proceeding with in-place restore")
                            self._LOG.info("Restore in-place")
                            flag, jobid = restore_obj.restore(
                                paths=restore_paths,
                                from_time=commcell_fromTime,
                                to_time=commcell_toTime,
                                fs_options=options,
                                unconditional_overwrite=restore_unconditionalOverwrite,
                                copy_precedence=copy_precedence,
                                vsa_guid=self._vsa_guid)
                    else:
                        restore_destclient = commcell_clientName
                        restore_destpath = commcell_destpath
                        self._LOG.info(
                            "Proceeding with restore on source client with provided destination path")
                        flag, jobid = restore_obj.restore_out_of_place(
                            paths=restore_paths,
                            destination_client=restore_destclient,
                            destination_path=restore_destpath,
                            from_time=commcell_fromTime,
                            to_time=commcell_toTime,
                            fs_options=options,
                            unconditional_overwrite=restore_unconditionalOverwrite,
                            copy_precedence=copy_precedence,
                            vsa_guid=self._vsa_guid
                        )
            except NameError as name_error:
                name_error = str(name_error)
                self._LOG.error("NameError Raised :%s" % (name_error))
                print(name_error)
                flag = 1
            except Exception as restore_exception:
                print("Error Occurred During Restore : Refer Logs for details ")
                restore_exception = str(restore_exception)
                self._LOG.error(
                    "Exception occurred during restore operation :%s " %
                    restore_exception)
                flag = 1
            finally:
                if flag == 0:
                    self._LOG.info(
                        "Restore Job Initiated successfully. Job ID : " + str(jobid))
                else:
                    print("Restore  Initiation  encountered Error")

        def do_restore_list(self, args):
            """
            usage: restore_list [-h]

            restore list

            optional arguments:
                    -h, --help  show this help message and exit

            """
            k = shlex.split(args)
            restore_list_parser = argparse.ArgumentParser(
                description='restore list', usage="restore_list [-h]")
            try:
                margs = restore_list_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            self._LOG.info("Setting restore list as current list")
            # indicating that list operations are to be done on restore list
            self._current_list_operation = 1
            self._LOG.info(
                "Any subsequent list operation will be specific to restore list")

        def do_setBrowseOptions(self, args):
            """
            usage: setBrowseOptions [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME] [-ftime FROMTIME]  [-ttime TOTIME]

            Set options for browse. Use command 'resetToDefaults' to reset the options

            optional arguments:
            -h, --help            show this help message and exit
            -c CLIENTNAME, --clientname CLIENTNAME
                                            Client Name
            -i INSTANCENAME, --instancename INSTANCENAME
                                            Instance Name
            -bk BACKUPSETNAME, --backupset BACKUPSETNAME
                                            Backupset Name
            -sc SUBCLIENTNAME, --subclient SUBCLIENTNAME
                                            Name to be passed even in case of default subclient
            -ftime FROMTIME, --fromtime FROMTIME
                                            The start time of the backup window that you specify 
                                            for a point-in-time browse operation. 
                                            The format is yyyy-mm-dd hh:mm:ss.
            -ttime TOTIME, --totime TOTIME
                                            The end time of the backup window that you specify 
                                            for a point-in-time browse operation. 
                                            The format is yyyy-mm-dd hh:mm:ss.
            """
            k = shlex.split(args)
            lb_parser = argparse.ArgumentParser(
                description="Set options for browse. Use command 'resetToDefaults' to reset the options",
                usage="setBrowseOptions [-h] [-c CLIENTNAME]  [-i INSTANCENAME] [-bk BACKUPSETNAME] [-sc SUBCLIENTNAME] [-ftime FROMTIME]  [-ttime TOTIME]")
            lb_parser.add_argument(
                "-c",
                "--clientname",
                dest="clientName",
                type=str,
                default=None,
                help="Client Name {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""))
            lb_parser.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                type=str,
                default=None,
                help="Instance Name")
            lb_parser.add_argument(
                "-bk",
                "--backupset",
                type=str,
                default=None,
                dest="backupSetName",
                help="Backupset Name")
            lb_parser.add_argument(
                "-sc",
                "--subclient",
                type=str,
                help="Name to be passed even in case of default subclient",
                default=None,
                dest="subClientName")
            lb_parser.add_argument(
                "-ftime",
                "--fromtime",
                dest="fromtime",
                default=0,
                help="The start time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.")
            lb_parser.add_argument(
                "-ttime",
                "--totime",
                dest="totime",
                default=0,
                help="The end time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.")
            try:
                margs = lb_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            if cvc_restrict_alt_client and margs.clientName is not None:
                print("Access denied. Local user can operate only on the local client.")
                self._LOG.error(
                    "Operation failed. Passing client name is currently disabled. [CVC_RESTRICT_ALT_CLIENT is set to True]")
                return

            try:
                self._LOG.info("Setting browse options")
                self._lb_backupSetName = margs.backupSetName
                self._lb_subClientName = margs.subClientName
                self._lb_fromtime = margs.fromtime
                self._lb_totime = margs.totime
                instanceLoglines = []
                if margs.instanceName:
                    (flag, instanceLoglines) = check_instance(margs.instanceName)
                    print_log_lines(instanceLoglines)
                    if not flag:
                        self._LOG.error(
                            "Operation failed. Instance with the provided name does not exist")
                        print(
                            "Operation failed. Instance with the provided name does not exist")
                        return
                    browse_instance = margs.instanceName
                else:
                    if margs.clientName is None:
                        # if client name is not passed, client name associated
                        # with Instance001 is fetched from registry by default
                        browse_instance = 'Instance001'
                    else:
                        # if client name is passed, instance name is not
                        # required and hence can be set to None
                        browse_instance = None
                self._lb_instanceName = browse_instance
                self._lb_clientName = margs.clientName

                # In case of localadmin user, client name should match the name
                # of the local client
                (status, self._lb_clientName) = check_qlogin_localadmin_chosen(
                    self, self._lb_clientName)
                if status is False:
                    return

                # Check if client name is passed or not
                common_object = CsCommon(self._commcell_obj)
                (status, clientName) = common_object.check_client_name(
                    self._lb_clientName, self._lb_instanceName)
                if status == 0:
                    self._LOG.info("Client name set to : %s" % clientName)
                    self._lb_clientName = clientName
                else:
                    print(
                        "Operation failed. Client name could not be set. Provide correct clientname as parameter in cmdline")
                    return

                if self._lb_clientName is None:
                    self._lb_initialized = False
                    raise Exception("Client name not set")
                self._lb_initialized = True
                self._live_browse_path = None  # set the current path and previous path to None
                self._previous_wd = None
                self._dir_stack = []
            except Exception as lb_exception:
                self._LOG.error(
                    "Error in setting browse options. " +
                    str(lb_exception))
                print("Error in setting browse options. " + str(lb_exception))
                return
            self._liveBrowseOptions = {
                "Instance": self._lb_instanceName if self._lb_instanceName else '---',
                "Client": self._lb_clientName,
                "Backupset": self._lb_backupSetName if self._lb_backupSetName else "(Default Backupset)",
                "Subclient": self._lb_subClientName if self._lb_subClientName else "---",
                "FromTime": self._lb_fromtime,
                "ToTime": self._lb_totime}
            if self._lb_subClientName is None:
                self._LOG.info(
                    "Browse will occur at backupset level as subclient is not provided")
            self._LOG.info("Browse Options are:")
            self._LOG.info(self._liveBrowseOptions)
            print(self._liveBrowseOptions)

        def do_toTime(self, args):
            """
            usage: toTime [-h] TOTIME

            Command to directly set/update "To Time" option for browsing

            positional arguments:
            totime      'To Time' for browse. Format : 'yyyy-mm-dd hh:mm:ss'

            optional arguments:
            -h, --help  show this help message and exit
            """
            k = shlex.split(args)
            tt_parser = argparse.ArgumentParser(
                description='Command to directly set/update "To Time" option for browsing',
                usage="toTime [-h] TOTIME")
            tt_parser.add_argument(
                dest='totime',
                help="'To Time' for browse. Format : 'yyyy-mm-dd hh:mm:ss'")
            try:
                margs = tt_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._lb_initialized:
                self._lb_totime = margs.totime
                if self._liveBrowseOptions:
                    self._liveBrowseOptions['ToTime'] = margs.totime
                    self._LOG.info("Browse Options are:")
                    self._LOG.info(self._liveBrowseOptions)
                    print(self._liveBrowseOptions)
                self._LOG.info(
                    "'totime' has been updated to '%s'" % str(
                        margs.totime))
            else:
                self.do_setBrowseOptions('-ttime "' + str(margs.totime) + '"')
                self._LOG.info(
                    "'totime' set for browsing. Default values chosen for all other options")

        def do_resetToDefaults(self, args):
            """
            usage: resetToDefaults [-h]

            Reset the browse options

            optional arguments:
                    -h, --help  show this help message and exit
            """
            k = shlex.split(args)
            r_parser = argparse.ArgumentParser(
                description='Reset the browse options',
                usage="resetToDefaults [-h]")
            try:
                margs = r_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            self._lb_clientName = None
            self._lb_instanceName = None
            self._lb_backupSetName = None
            self._lb_subClientName = None
            self._lb_fromtime = 0
            self._lb_totime = 0
            self._lb_initialized = False
            self._LOG.info("Browse options are reset")

        def do_cd(self, args):
            """
            usage: cd path

            Change directory in backup content

            positional arguments:
                    path        Directory path

            optional arguments:
            -h, --help  show this help message and exit
            """
            try:
                k = shlex.split(args)
                cd_parser = argparse.ArgumentParser(
                    description='Change directory in backup content', usage="cd path")
                cd_parser.add_argument(dest='path', help='Directory path')
                try:
                    margs = cd_parser.parse_args(k)
                except SystemExit:
                    return
                if self._commcell_obj is None:
                    print("Login to CS before initiating any operation")
                    return

                if self._lb_clientName is None:
                    self._LOG.info("Setting default values for browse options")
                    import sys
                    sys.stdout = open(os.devnull, "w")
                    # This function call is to set the default values for
                    # browse options
                    self.do_setBrowseOptions("")
                    sys.stdout = sys.__stdout__
                if self._lb_clientName is None:
                    self._LOG.error("Error in setting the browse options")
                    print("Error in setting the browse options")
                    return
                else:
                    clientName = self._lb_clientName
                path = margs.path
                clientobj = self._commcell_obj.clients.get(clientName)
                if 'windows' in clientobj.os_info.lower():
                    separator = '\\'
                    import ntpath
                    win = 1
                else:
                    separator = '/'
                    import posixpath
                    win = 0
                if path == '-':
                    if self._previous_wd is None:
                        self._LOG.error("Previous working directory not set")
                        print("Previous working directory not set")
                    else:
                        temp = self._live_browse_path
                        self._live_browse_path = self._previous_wd
                        self._previous_wd = temp
                        self._dir_stack.clear()
                        for x in self._live_browse_path.split(separator):
                            if x != '.':
                                if x != '..':
                                    if x != '':
                                        self._dir_stack.append(x)
                                else:
                                    self._dir_stack.pop()
                        self._LOG.info(
                            "Current working directory changed to " +
                            self._live_browse_path)
                    return
                if path is not None:
                    oldLiveBrowsePath = self._live_browse_path
                    if (win and ntpath.isabs(path)) or (
                            not(win) and posixpath.isabs(path)):
                        self._dir_stack.clear()  # clear stack if path is absolute
                    else:
                        if oldLiveBrowsePath is None:
                            self._LOG.error(
                                "Please use an absolute path to begin with")
                            # if path is not absolute, previous path sould not
                            # be None
                            print("Please use an absolute path to begin with")
                            return

                    for y in path.split(separator):
                        if y != '.':
                            if y != '..':
                                if y != '':
                                    self._dir_stack.append(y)
                            else:
                                if self._dir_stack:
                                    self._dir_stack.pop()

                    self._live_browse_path = (
                        '/' if not win else '') + separator.join(self._dir_stack)
                    self._previous_wd = oldLiveBrowsePath
                    self._LOG.info(
                        "Current working directory changed to " +
                        self._live_browse_path)
            except Exception as cd_exception:
                self._LOG.error(
                    "Error encountered while changing directory. " +
                    str(cd_exception))
                print(
                    "Error encountered while changing directory. " +
                    str(cd_exception))

        def do_ls(self, args):
            """
            usage: ls [-l long listing format]

            List information about backup content

            optional arguments:
            -h, --help  show this help message and exit
            -l          Long listing format
            """

            flag = 1

            # Reading and parsing the arguments
            k = shlex.split(args)
            ls_parser = argparse.ArgumentParser(
                description='List information about backup content',
                usage="ls [-l long listing format]")
            ls_parser.add_argument(
                'browse_filter',
                help='filters to be used during ls',
                nargs='*')
            ls_parser.add_argument(
                '-l',
                dest='long_listing',
                help='Long listing format',
                action='store_true',
                default=True)
            try:
                margs = ls_parser.parse_args(k)
            except SystemExit:
                return
            browse_filter = margs.browse_filter

            # Checking if the user is logged in to the CS.
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            # If the browse option is not set, we set the default values for browse option
            # Note : Default values will be set only in case of local
            # installaion
            if self._lb_initialized is False:
                self._LOG.info("Setting default values for browse options")
                import sys
                sys.stdout = open(os.devnull, "w")
                # This function call is to set the default values for browse
                # options
                self.do_setBrowseOptions("")
                sys.stdout = sys.__stdout__
                if self._lb_initialized is False:
                    self._LOG.error("Error in setting the browse options")
                    self._LOG.error(
                        "Cannot perform browse as browse options are not set.")
                    self._LOG.info(
                        "Set the browse options using 'setBrowseOptions' command")
                    print("Error encountered during browse. Browse options not set")
                    return

            # If the browse path is not set, we check if the client is the local client.
            # If the client is a local client, we set current directory as directory for browse
            # Otherwise, we throw an error.
            if (self._live_browse_path is None or self._live_browse_path ==
                    '') and self._lb_clientName == self._qlogin_local_client:
                self._LOG.info(
                    "Setting current directory as the directory for browse")
                self._live_browse_path = os.getcwd()
                self._LOG.info(
                    "Directory for browse set to : " +
                    self._live_browse_path)
            elif self._live_browse_path is None or self._live_browse_path == '':
                self._LOG.error(
                    "Cannot send browse request. Browse path not set")
                self._LOG.info(
                    "Try again and set the browse path with 'cd' command.")
                print("Error encountered during browse. Path not set")
                return

            # Initializing filter to be used during browse
            filters = []
            if browse_filter:
                browse_filter_string = ""
                for browse_filter_element in browse_filter:
                    browse_filter_string = "{0}{1}{2}".format(
                        browse_filter_string,
                        " OR " if browse_filter_string != "" else "",
                        browse_filter_element)
                filters = [('FileName', browse_filter_string)]

            if margs.long_listing is not None:
                if self._is_VSA:	
                        if not self._vsa_guid:
                            print("Operation failed. Could not find GUID for VM ", self._lb_clientName)
                            return

                # Run the browse operation
                try:
                    self.browse_obj = browse.Browse(
                        package_instance=None,
                        commcell_object=self._commcell_obj,
                        client_name=self._lb_clientName,
                        agent_name=self._commcell_agent,
                        backupset_name=self._lb_backupSetName,
                        logger_object=self._LOG,
                        tempFolder=self._loggingPath
                    )

                    flag = self.browse_obj.qlist_browse(
                        operation='Browse',
                        subclient_name=self._lb_subClientName,
                        path=self._live_browse_path,
                        from_time=self._lb_fromtime,
                        to_time=self._lb_totime,
                        filters=filters,	
                        vsa_guid=self._vsa_guid)

                except NameError as name_error:
                    name_error = str(name_error)
                    self._LOG.error("NameError Raised :%s" % name_error)
                    print(name_error)
                    flag = 1
                except Exception as browse_exception:
                    print("Error Occurred During Browse : Refer Logs for details ")
                    browse_exception = str(browse_exception)
                    self._LOG.error(
                        "Exception occurred while initiating  browse operation :%s " %
                        browse_exception)
                    flag = 1
                finally:
                    if flag == 0:
                        # Browse operation was successful.
                        return
                    else:
                        print("Browse Operation encountered Error")

        def do_pwd(self, args):
            """
            usage: pwd [-h]

            Print the full path of the current working directory within backup content

            optional arguments:
            -h, --help  show this help message and exit
            """

            # Reading and parsing the arguments
            k = shlex.split(args)
            pwd_parser = argparse.ArgumentParser(
                description='Print the full path of the current working directory within backup content',
                usage="pwd [-h]")
            try:
                margs = pwd_parser.parse_args(k)
            except SystemExit:
                return

            # Checking if the user is logged in to the CS.
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            # Printing the current working directory
            if self._live_browse_path is not None and self._live_browse_path != '':
                self._LOG.info(
                    "Current working directory of backup content: " +
                    self._live_browse_path)
                print(self._live_browse_path)
            else:
                # If the browse path (current working directory) is not set, we check if the client is a local client.
                # If the client is a local client, we set current directory as directory for browse
                # Otherwise, we throw an error.
                self._LOG.error(
                    "Current working directory of backup content not set")
                if not self._lb_initialized and self._qlogin_local_client:
                    self._LOG.info("Setting default values for browse options")
                    import sys
                    sys.stdout = open(os.devnull, "w")
                    # This function call is to set the default values for
                    # browse options
                    self.do_setBrowseOptions("")
                    sys.stdout = sys.__stdout__
                    if self._lb_initialized is False:
                        self._LOG.error(
                            "Error in setting the default browse options")
                if self._lb_initialized is True and self._lb_clientName == self._qlogin_local_client:
                    self._LOG.info(
                        "Setting current directory as the directory for browse")
                    self._live_browse_path = os.getcwd()
                    self._LOG.info(
                        "Current working directory : " +
                        self._live_browse_path)
                    print(self._live_browse_path)
                    return
                print("Current working directory not set")

    def do_get_job_status(self, args):
        """
        usage: get_job_status [-h] -j [jobid]

        get_job_status

        optional arguments:
                -h, --help            show this help message and exit
                -j JOBID, --jobid JOBID
                                        Job ID
        """
        # Reading the Cmdline Argument
        k = shlex.split(args)
        # Defining Parser Command Structure for Restore Operation
        job_parser = argparse.ArgumentParser(
            description='get_job_status',
            usage="get_job_status [-h] -j [jobid]")
        job_parser.add_argument(
            "-j",
            "--jobid",
            type=str,
            required=True,
            dest="jobid",
            help="Job ID")
        # Parsing the CMDLINE Input based on above defined structure
        try:
            margs = job_parser.parse_args(k)
        except SystemExit:
            return
        # Verify if login is executed atleast before proceeding with Restore
        if self._commcell_obj is None:
            print("Login to CS before initiating any operation")
            return
        self._LOG.info("Get Job Status ")
        # Reading the values passed as arguments
        jobid = margs.jobid
        # creating object of jobid
        job_obj = jobs.Jobs(self._loggingPath, self._commcell_obj, jobid)
        (flag, job_finish_status, job_current_status) = job_obj.get_job_status()
        if flag == 1:
            print("Failed to Fetch Job Details")
        else:
            print("Job Finish Status : %s" % job_finish_status)
            print("Job Current Status : %s" % job_current_status)

    def do_get_job_summary(self, args):
        """
        usage: get_job_summary [-h] -j [jobid]

        get_job_summary

        optional arguments:
                -h, --help            show this help message and exit
                -j JOBID, --jobid JOBID
                                        Job ID
        """
        # Reading the Cmdline Argument
        k = shlex.split(args)
        # Defining Parser Command Structure for Restore Operation
        job_parser = argparse.ArgumentParser(
            description='get_job_summary',
            usage="get_job_summary [-h] -j [jobid]")
        job_parser.add_argument(
            "-j",
            "--jobid",
            type=str,
            required=True,
            dest="jobid",
            help="Job ID")
        # Parsing the CMDLINE Input based on above defined structure
        try:
            margs = job_parser.parse_args(k)
        except SystemExit:
            return
        # Verify if login is executed atleast before proceeding with Restore
        if self._commcell_obj is None:
            print("Login to CS before initiating any operation")
            return
        self._LOG.info("Get Job Summary ")
        # Reading the values passed as arguments
        jobid = margs.jobid
        # creating object of jobid
        job_obj = jobs.Jobs(self._loggingPath, self._commcell_obj, jobid)
        flag = job_obj.get_job_summary()
        if flag == 1:
            self._LOG.error("Failed to print Job summary")
        else:
            self._LOG.info("Job summary displayed Successfully")

    def do_job(self, args):
        """
        usage: job [-h] -j [jobid] -t[operation type]

        job

        optional arguments:
                -h, --help            show this help message and exit
                -j JOBID, --jobid JOBID
                                        Job ID
                -t {kill,pause,resume}, --type {kill,pause,resume}
                                        Operation type
        """
        # Reading the Cmdline Argument
        k = shlex.split(args)
        # Defining Parser Command Structure for Restore Operation
        job_parser = argparse.ArgumentParser(
            description='job', usage="job [-h] -j [jobid] -t[operation type]")
        job_parser.add_argument(
            "-j",
            "--jobid",
            type=str,
            required=True,
            dest="jobid",
            help="Job ID")
        job_parser.add_argument(
            "-t",
            "--type",
            dest="operationtype",
            choices=[
                'kill',
                'pause',
                'resume'],
            required=True,
            type=str,
            help="Operation type")
        # Parsing the CMDLINE Input based on above defined structure
        try:
            margs = job_parser.parse_args(k)
        except SystemExit:
            return
        # Verify if login is executed atleast before proceeding with Restore
        if self._commcell_obj is None:
            print("Login to CS before initiating any operation")
            return
        self._LOG.info("Job Action Method")
        # Reading the values passed as arguments
        jobid = margs.jobid
        operation = margs.operationtype
        # creating object of jobid
        job_obj = jobs.Jobs(self._loggingPath, self._commcell_obj, jobid)
        job_obj.action_on_job(operation)

    # DYNAMIC LIST MANIPULATION COMMANDS
    if cvc_backup or cvc_recover:
        def do_add(self, args):
            """
            usage: add [-h] paths

            Add item(s) to the backup/restore list

            positional arguments:
                    path        Comma-separated paths to be added to the backup/restore list

            optional arguments:
                    -h, --help  show this help message and exit
            """
            k = shlex.split(args)
            list_parser = argparse.ArgumentParser(
                description='add item(s) to backup/restore list',
                usage="add [-h] path")
            list_parser.add_argument(
                dest='path',
                type=str,
                help='Comma-separated paths to be added to the backup/restore list.',
                default=None)
            try:
                margs = list_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return

            path = margs.path.split(",")
            if self._current_list_operation == -1:
                self._LOG.error("No list initialized. Please indicate the list to be modified")
                print("No list initialized. Please indicate the list to be modified")
                return
            elif self._current_list_operation == 0:
                self._LOG.info("Adding path(s) to the backup list")
                self._backup_list.update(path)
            else:
                self._LOG.info("Adding path(s) to the restore list")
                self._restore_list.update(path)


        def do_remove(self, args):
            """
            usage: remove [-h] path

            remove item from backup/restore list

            positional arguments:
                    path        Path to be removed from backup/restore list

            optional arguments:
                    -h, --help  show this help message and exit
            """
            k = shlex.split(args)
            list_parser = argparse.ArgumentParser(
                description='remove item from backup/restore list',
                usage="remove [-h] path")
            list_parser.add_argument(
                dest='path',
                type=str,
                nargs=1,
                help='Path to be removed from backup/restore list',
                default=None)
            try:
                margs = list_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            path = margs.path
            if self._current_list_operation == -1:
                self._LOG.error("No list initialized. Please indicate the list to be modified")
                print("No list initialized. Please indicate the list to be modified")
                return
            elif self._current_list_operation == 0:
                if path[0] in self._backup_list:
                    self._LOG.info("Removing file from the backup list")
                    self._backup_list.remove(path[0])
                else:
                    print("'%s' not present in backup list" % path[0])
            else:
                if path[0] in self._restore_list:
                    self._LOG.info("Removing file from the restore list")
                    self._restore_list.remove(path[0])
                else:
                    print("'%s' not present in restore list" % path[0])

        def do_list(self, args):
            """
            usage: list [-h]

            display backup/restore list

            optional arguments:
                    -h, --help  show this help message and exit
            """
            k = shlex.split(args)
            list_parser = argparse.ArgumentParser(
                description='display backup/restore list', usage="list [-h]")
            try:
                margs = list_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._current_list_operation == -1:
                self._LOG.error("No list initialized. Please indicate the list to be modified")
                print("No list initialized. Please indicate the list to be modified")
                return
            elif self._current_list_operation == 0:
                self._LOG.info("Displaying the backup list")
                print(f"Backup list: {self._backup_list or ''}")
            else:
                self._LOG.info("Displaying the restore list")
                print(f"Restore list: {self._restore_list or ''}")

        def do_reset(self, args):
            """
            usage: reset [-h]

            reset backup/restore list

            optional arguments:
                    -h, --help  show this help message and exit
            """
            k = shlex.split(args)
            reset_parser = argparse.ArgumentParser(
                description='reset backup/restore list', usage="reset [-h]")
            try:
                margs = reset_parser.parse_args(k)
            except SystemExit:
                return
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            if self._current_list_operation == -1:
                self._LOG.error("No list initialized. Please indicate the list to be modified")
                print("No list initialized. Please indicate the list to be modified")
                return
            elif self._current_list_operation == 0:
                self._LOG.info("Resetting the backup list")
                self._backup_list.clear()
            else:
                self._LOG.info("Resetting the restore list")
                self._restore_list.clear()

    def do_logout(self, args):
        """
        usage: logout [-h]

        Logout

        optional arguments:
                -h, --help         show this help message and exit
        """
        k = shlex.split(args)
        logout_parser = argparse.ArgumentParser(
            description='Logout', usage="logout [-h]")
        try:
            margs = logout_parser.parse_args(k)
        except SystemExit:
            return
        try:
            if self._commcell_obj is None:
                print("Login to CS before initiating any operation")
                return
            self._commcell_obj.logout()
            self._commcell_obj = None
            self._LOG.info("SuccessFully Logged out of the commserve")
            print("Logout Successful")
        except NameError as name_error:
            name_error = str(name_error)
            self._LOG.error("NameError Raised :%s" % (name_error))
            print(name_error)
            return

    def do_whoami(self, args):
        """
        usage: whoaami [-h]

        To print the name of the user who is currently logged into the session

        optional arguments:
                -h, --help         show this help message and exit
        """
        k = shlex.split(args)
        w_parser = argparse.ArgumentParser(
            description='To print the name of the user who is currently logged into the session',
            usage="whoaami [-h]")
        try:
            margs = w_parser.parse_args(k)
        except SystemExit:
            return

        if self._commcell_obj:
            self._LOG.info(
                "Currently logged in user: %s" %
                self._commcell_obj.commcell_username)
            print(self._commcell_obj._user)
        else:
            print("Operation failed. No user currently logged in")

    def do_quit(self, args):
        """
        usage: quit [-h]

        Quit

        optional arguments:
                -h, --help         show this help message and exit
        """
        k = shlex.split(args)
        quit_parser = argparse.ArgumentParser(
            description='Quit', usage="quit [-h]")
        try:
            margs = quit_parser.parse_args(k)
        except SystemExit:
            return
        print("Quit Command Initiated ")
        print("Exiting.")
        try:
            if self._commcell_obj is None:
                return
            self._commcell_obj.logout()
            self._LOG.info("SuccessFully Logged out of the commserve")
        except NameError as name_exception:
            self._LOG.error("NameError Raised :%s" % (name_exception))
        finally:
            raise SystemExit

    def emptyline(self):
        """
        Called when an empty line is entered in response to the prompt.
        If this method is not overridden, it repeats the last nonempty
        command entered.
        """
        if self.lastcmd:
            self.lastcmd = ""
            return self.onecmd('\n')


if __name__ == '__main__':

    tokenpath = None
    try:

        simpana_default_obj = SimpanaDefaults.Simpanadefaults()
        sd = cvc_default_show_deleted
        # PARSER
        parser = argparse.ArgumentParser(prog=sys.argv[0])
        subparsers = parser.add_subparsers(help='Perform operations')

        # SUBPARSER FOR LOGIN
        parser_a = subparsers.add_parser('login', help='Login to Commserver')
        parser_a.add_argument(
            '-u',
            dest="username",
            help='Username',
            type=str,
            default=None)
        parser_a.add_argument(
            '-p',
            dest="password",
            help='Password',
            type=str,
            default=None)
        parser_a.add_argument(
            '-wch',
            dest="webConsoleHostName",
            help='Web Console Host Name',
            type=str,
            default=None)
        parser_a.add_argument(
            "-i",
            dest="instanceName",
            help="Instance Name",
            type=str,
            default=None)
        parser_a.add_argument(
            '-k',
            dest="key",
            help='key-16 characters',
            type=str,
            default=None)
        parser_a.add_argument(
            '-f',
            dest="tokenFilePath",
            help='Token File Path',
            type=str,
            default=None)
        parser_a.add_argument(
            '-lf',
            dest="logFilePath",
            help='Log File Path',
            type=str,
            default=None)
        parser_a.add_argument(
            '-https',
            dest="force_https",
            help='Login is forced to use https protocol',
            choices=[
                'true',
                'false'],
            type=str.lower,
            default=None,
            required=False)
        parser_a.add_argument(
            '-cert',
            dest="certificate_path",
            help='Certificate Path',
            type=str,
            default=None)
        parser_a.add_argument(
            '-at',
            dest="agent_type",
            help='Agent type(fs/vsa)',
            type=str,
            default='')
        parser_a.set_defaults(action='login')
        # SUBPARSER FOR LOGOUT
        parser_b = subparsers.add_parser('logout', help='Logout of Commserver')
        parser_b.add_argument(
            "-i",
            dest="instanceName",
            help="Instance Name",
            type=str,
            default=None)
        parser_b.add_argument(
            '-k',
            dest="key",
            help='key-16 characters',
            type=str,
            default=None)
        parser_b.add_argument(
            '-tf',
            dest="tokenFilePath",
            help='Token File Path',
            type=str,
            default=None)
        parser_b.add_argument(
            '-lf',
            dest="logFilePath",
            help='Log File Path',
            type=str,
            default=None)
        parser_b.set_defaults(action='logout')

        # BACKUP COMMANDS
        if cvc_backup:
            # ARGUMENTS FOR AD-HOC BACKUP
            content_group = parser.add_mutually_exclusive_group()
            content_group.add_argument(
                '-path',
                dest="contentPath",
                help="Adhoc Backup Path",
                nargs='+',
                type=str,
                default=None)
            content_group.add_argument(
                '-df',
                dest="directiveFilePath",
                help="Directive File Path for Adhoc Backup. The file should be present on the machine from where command is run.",
                type=str,
                default=None)
            sc_group = parser.add_mutually_exclusive_group()
            sc_group.add_argument(
                '-scid',
                dest="subclientId",
                help="Subclient ID",
                type=str,
                default=None)
            sc_group.add_argument(
                '-sc',
                dest="subClientName",
                help='Subclient Name',
                type=str,
                default=None)
            parser.add_argument(
                '-bk',
                dest="backupSetName",
                help='Backupset Name',
                type=str,
                default=None)
            parser.add_argument(
                "-i",
                dest="instanceName",
                help="Instance Name",
                type=str,
                default=None)
            parser.add_argument(
                "-a",
                dest="agentName",
                help="Agent Name",
                type=str,
                default="File System")
            parser.add_argument(
                '-k',
                dest="key",
                help='key-16 characters',
                type=str,
                default=None)
            parser.add_argument(
                '-tf',
                dest="tokenFilePath",
                help='Token File Path',
                type=str,
                default=None)
            parser.add_argument(
                '-of',
                dest="outputFilePath",
                help='Output File Path',
                type=str,
                default=None)
            parser.add_argument(
                '-lf',
                dest="logFilePath",
                help='Log File Path',
                type=str,
                default=None)
            parser.add_argument(
                '-at',
                dest="agent_type",
                help='Agent type(fs/vsa)',
                type=str,
                default='')
            parser.set_defaults(action='adHocBackup')
            # SUBPARSER FOR BACKUP
            parser_c = subparsers.add_parser('backup', help='Run backup job, Not supported for VSA', epilog="NOTE: This operation is not supported for VSA")
            parser_c.add_argument(
                dest='path',
                type=str,
                nargs='?',
                help='File or folder to backup with default options. Other user provided options will be ignored and default values will be used.',
                default=None)
            parser_c.add_argument(
                '-c',
                dest="clientName",
                help='Client Name {0}'.format(
                    "[Disabled]" if cvc_restrict_alt_client else ""),
                type=str,
                default=None)
            sc_group = parser_c.add_mutually_exclusive_group()
            sc_group.add_argument(
                '-scid',
                dest="subclientId",
                help="Subclient ID",
                type=str,
                default=None)
            sc_group.add_argument(
                '-sc',
                dest="subClientName",
                help='Subclient Name',
                type=str,
                default=None)
            parser_c.add_argument(
                '-bk',
                dest="backupSetName",
                help='Backupset Name',
                type=str,
                default=None)
            parser_c.add_argument(
                '-l',
                dest="level",
                help='Backup Level',
                type=str,
                choices=[
                    'full',
                    'incremental',
                    'synthetic_full',
                    'differential'],
                default='incremental')
            adhoc_content_group = parser_c.add_mutually_exclusive_group()
            adhoc_content_group.add_argument(
                '-path',
                dest="contentPath",
                help="Adhoc Backup Path",
                nargs='+',
                type=str,
                default=None)
            adhoc_content_group.add_argument(
                '-df',
                dest="directiveFilePath",
                help="Directive File Path. The file should be present on the machine from where command is run.",
                type=str,
                default=None)
            parser_c.add_argument(
                "-i",
                dest="instanceName",
                help="Instance Name",
                type=str,
                default=None)
            parser_c.add_argument(
                "-a",
                dest="agentName",
                help="Agent Name",
                type=str,
                default="File System")
            parser_c.add_argument(
                '-k',
                dest="key",
                help='key-16 characters',
                type=str,
                default=None)
            parser_c.add_argument(
                '-tf',
                dest="tokenFilePath",
                help='Token File Path',
                type=str,
                default=None)
            parser_c.add_argument(
                '-of',
                dest="outputFilePath",
                help='Output File Path',
                type=str,
                default=None)
            parser_c.add_argument(
                '-lf',
                dest="logFilePath",
                help='Log File Path',
                type=str,
                default=None)
            parser_c.add_argument(
                '-at',
                dest="agent_type",
                help='Agent type(fs/vsa)',
                type=str,
                default='')
            parser_c.set_defaults(action='backup')

        # RECOVER COMMANDS
        if cvc_recover:
            # SUBPARSER FOR BROWSE
            parser_d = subparsers.add_parser(
                'browse', help='Run Browse Operation')
            parser_d.add_argument(
                dest='path',
                type=str,
                nargs='?',
                help='Path for browse with default options. This overrides the user provided values and instead default values are chosen',
                default=None)
            parser_d.add_argument(
                '-c',
                dest="clientName",
                help='Client Name {0}'.format(
                    '[Disabled]' if cvc_restrict_alt_client else ''),
                type=str,
                default=None)
            parser_d.add_argument(
                '-bk',
                dest="backupSetName",
                help='Backupset Name',
                type=str,
                default=None)
            parser_d.add_argument(
                '-sc',
                dest="subClientName",
                help='Subclient Name. Name to be passed even in case of default subclient',
                type=str,
                default=None)
            parser_d.add_argument(
                '-p',
                dest="browsepath",
                help='Browse Path',
                type=str,
                default=None)
            parser_d.add_argument(
                '-ftime',
                dest="fromTime",
                help='The start time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.',
                type=str,
                default=0)
            parser_d.add_argument(
                '-ttime',
                dest="toTime",
                help='The end time of the backup window that you specify for a point-in-time browse operation. The format is yyyy-mm-dd hh:mm:ss.',
                type=str,
                default=0)
            parser_d.add_argument(
                '-allVersions',
                dest="allVersions",
                help='option to browse all versions. For VSA, Index files after backup option must be enabled on VM group.',
                action='store_true')
            parser_d.add_argument(
                "-i",
                dest="instanceName",
                help="Instance Name",
                type=str,
                default=None)
            parser_d.add_argument(
                "-a",
                dest="agentName",
                help="Agent Name",
                type=str,
                default="File System")
            parser_d.add_argument(
                '-k',
                dest="key",
                help='key-16 characters',
                type=str,
                default=None)
            parser_d.add_argument(
                '-tf',
                dest="tokenFilePath",
                help='Token File Path',
                type=str,
                default=None)
            parser_d.add_argument(
                '-lf',
                dest="logFilePath",
                help='Log File Path',
                type=str,
                default=None)
            parser_d.add_argument(
                "-filter",
                "--browseFilter",
                dest="browse_filter",
                nargs='+',
                type=str,
                default=None,
                help="File name filters for the browse")
            parser_d.add_argument(
                '-at',
                dest="agent_type",
                help='Agent type(fs/vsa)',
                type=str,
                default='')
            parser_d.add_argument(
                "-cp",
                "--copyPrecedence",
                dest="copy_precedence",
                type=int,
                default=None,
                help="Copy Precedence")
            parser_d.add_argument(
                '-sd',
                dest="show_deleted",
                help='Show deleted items {True,False}. %s by default' %
                str(sd),
                default=str(sd),
                choices=[
                    'True',
                    'False'])
            parser_d.set_defaults(action='browse')

            # SUBPARSER FOR FIND OPERATION
            find_parser = subparsers.add_parser('find', help='Run Find Operation')
            find_parser.add_argument(
                '-c',
                '--clientname',
                dest="clientName",
                help='Client Name {0}'.format('[Disabled]' if cvc_restrict_alt_client else ''),
                type=str,
                default=None)
            find_parser.add_argument(
                '-bk',
                '--backupset',
                dest="backupSetName",
                help='Backupset Name',
                type=str,
                default=None)
            find_parser.add_argument(
                '-sc',
                '--subclient',
                dest="subClientName",
                help='Subclient Name. Name to be passed even in case of default subclient',
                type=str,
                default=None)
            find_parser.add_argument(
                '-path',
                '--path',
                dest="findPath",
                help='Find Path',
                type=str,
                default="")
            find_parser.add_argument(
                '-ftime',
                '--fromtime',
                dest="fromTime",
                help='The start time of the backup window that you specify for a point-in-time find operation. The format is yyyy-mm-dd hh:mm:ss.',
                type=str,
                default=0)
            find_parser.add_argument(
                '-ttime',
                '--totime',
                dest="toTime",
                help='The end time of the backup window that you specify for a point-in-time find operation. The format is yyyy-mm-dd hh:mm:ss.',
                type=str,
                default=0)
            find_parser.add_argument(
                "-i",
                "--instancename",
                dest="instanceName",
                help="Instance Name",
                type=str,
                default=None)
            find_parser.add_argument(
                '-k',
                dest="key",
                help='key-16 characters',
                type=str,
                default=None)
            find_parser.add_argument(
                '-tf',
                dest="tokenFilePath",
                help='Token File Path',
                type=str,
                default=None)
            find_parser.add_argument(
                '-lf',
                dest="logFilePath",
                help='Log File Path',
                type=str,
                default=None)
            find_parser.add_argument(
                "-f",
                "--filename",
                dest="filename",
                required=True,
                type=str,
                help="File or Folder name")
            find_parser.add_argument(
                '-at',
                dest="agent_type",
                help='Agent type(fs/vsa)',
                type=str,
                default='')
            find_parser.add_argument(
                "-cp",
                "--copyPrecedence",
                dest="copy_precedence",
                type=int,
                default=None,
                help="Copy Precedence")
            find_parser.add_argument(
                '-sd',
                dest="show_deleted",
                help='Show deleted items {True,False}. %s by default' %
                str(sd),
                default=str(sd),
                choices=[
                    'True',
                    'False'])
            find_parser.set_defaults(action='find')

            # SUBPARSER FOR RESTORE
            parser_e = subparsers.add_parser('restore', help='Run restore job')
            parser_e.add_argument(
                dest='path',
                type=str,
                nargs='?',
                help='File or folder to restore with default options. Other user provided options will be ignored and default values will be used.',
                default=None)
            parser_e.add_argument(
                '-c',
                dest="clientName",
                help='Client Name {0}'.format(
                    '[Disabled]' if cvc_restrict_alt_client else ''),
                type=str,
                default=None)
            parser_e.add_argument(
                '-sc',
                dest="subClientName",
                help='Subclient Name. Name to be passed even in case of default subclient',
                type=str,
                default=None)
            parser_e.add_argument(
                '-bk',
                dest="backupSetName",
                help='Backupset Name',
                type=str,
                default=None)
            restore_group = parser_e.add_mutually_exclusive_group()
            restore_group.add_argument(
                "-path",
                nargs='+',
                dest="sourcepath",
                default=None,
                type=str,
                help='Source Paths')
            restore_group.add_argument(
                "-l",
                dest="restorefilelist",
                help='Restore File List. The file should be present on the machine from where command is run.',
                default=None,
                type=str)
            parser_e.add_argument(
                "-dc",
                dest="destclient",
                help="Destination Client {0}".format(
                    "[Disabled]" if cvc_restrict_alt_client else ""),
                default=None,
                type=str)
            parser_e.add_argument(
                "-dp",
                dest="destpath",
                help="Destination Path",
                default=None,
                type=str)
            parser_e.add_argument(
                '-ftime',
                dest="fromTime",
                help='The start time of the backup window that you specify for a point-in-time restore operation. The format is yyyy-mm-dd hh:mm:ss.',
                type=str,
                default=None)
            parser_e.add_argument(
                '-ttime',
                dest="toTime",
                help='The end time of the backup window that you specify for a point-in-time restore operation. The format is yyyy-mm-dd hh:mm:ss.',
                type=str,
                default=None)
            parser_e.add_argument(
                '-versions',
                dest="versions",
                help='Versions to be restored. "All" or "all" or list of version numbers such as "1,2,5".',
                type=str,
                default=None)
            uo = cvc_restore_default_overwrite
            parser_e.add_argument(
                '-uo',
                dest="unconditional_overwrite",
                help='Unconditional Overwrite {True,False}. %s by default' %
                str(uo),
                default=str(uo),
                choices=[
                    'True',
                    'False'])
            parser_e.add_argument(
                "-i",
                dest="instanceName",
                help="Instance Name",
                type=str,
                default=None)
            parser_e.add_argument(
                "-a",
                dest="agentName",
                help="Agent Name",
                type=str,
                default="File System")
            parser_e.add_argument(
                '-k',
                dest="key",
                help='key-16 characters',
                type=str,
                default=None)
            parser_e.add_argument(
                '-tf',
                dest="tokenFilePath",
                help='Token File Path',
                type=str,
                default=None)
            parser_e.add_argument(
                '-of',
                dest="outputFilePath",
                help='Output File Path',
                type=str,
                default=None)
            parser_e.add_argument(
                '-lf',
                dest="logFilePath",
                help='Log File Path',
                type=str,
                default=None)
            parser_e.add_argument(
                '-filter',
                "--browseFilter",
                dest="browse_filter",
                nargs='+',
                type=str,
                default=None,
                help="Browse Filters")
            parser_e.add_argument(
                "-cp",
                "--copyPrecedence",
                dest="copy_precedence",
                type=int,
                default=None,
                help="Copy Precedence")
            parser_e.add_argument(
                '-at',
                dest="agent_type",
                help='Agent type(fs/vsa)',
                type=str,
                default='')
            parser_e.add_argument(
                '-sd',
                dest="show_deleted",
                help='Show deleted items {True,False}. Set this to True to restore deleted items. %s by default.' %
                str(sd),
                default=str(sd),
                choices=[
                    'True',
                    'False'])
            parser_e.set_defaults(action='restore')

        # CONFIGURE COMMANDS
        if cvc_configure:
            # SUBPARSER FOR SUBCLIENT
            parser_f = subparsers.add_parser(
                'subclient', help='Subclient Operations, Not supported for VSA', epilog=" NOTE: Subclient operations are not allowed for VSA.")
            subclient_group = parser_f.add_mutually_exclusive_group(
                required=True)
            subclient_group.add_argument(
                '-create',
                dest="subclient_create",
                help="Create Subclient",
                default=None,
                action="store_true")
            subclient_group.add_argument(
                '-update',
                dest="subclient_update",
                help="Update Subclient",
                default=None,
                action="store_true")
            subclient_group.add_argument(
                '-delete',
                dest="subclient_delete",
                help="Delete Subclient",
                default=None,
                action="store_true")
            parser_f.add_argument(
                '-c',
                dest="clientName",
                help='Client Name',
                type=str,
                default=None)
            parser_f.add_argument(
                "-a",
                dest="agentName",
                help="Agent Name",
                type=str,
                default="File System")
            parser_f.add_argument(
                '-bk',
                dest="backupSetName",
                help='Backupset Name',
                type=str,
                default=None)
            parser_f.add_argument(
                '-sc',
                dest="subClientName",
                help='Subclient Name',
                type=str,
                required=True)
            parser_f.add_argument(
                "-path",
                dest="path",
                help="Paths to be added to subclient content",
                type=str,
                default=None,
                action="append")
            parser_f.add_argument(
                "-excludepath",
                dest="exclude_path",
                help="Filter Path(s)",
                type=str,
                default=None,
                action="append")
            parser_f.add_argument(
                "-dsp",
                dest="dsp",
                help='Default Storage Policy',
                type=str,
                default=None)
            parser_f.add_argument(
                "-overwrite",
                dest='overwrite',
                help='Overwrite {True,False}',
                default='False',
                choices=[
                    'True',
                    'False'])
            parser_f.add_argument(
                "-i",
                dest="instanceName",
                help="Instance Name",
                type=str,
                default=None)
            parser_f.add_argument(
                '-k',
                dest="key",
                help='key-16 characters',
                type=str,
                default=None)
            parser_f.add_argument(
                '-tf',
                dest="tokenFilePath",
                help='Token File Path',
                type=str,
                default=None)
            parser_f.add_argument(
                '-lf',
                dest="logFilePath",
                help='Log File Path',
                type=str,
                default=None)
            parser_f.add_argument(
                '-at',
                dest="agent_type",
                help='Agent type(fs)',
                type=str,
                default='')
            parser_f.set_defaults(action='subclient')

        # SUBPARSER FOR JOB STATUS
        parser_g = subparsers.add_parser('job_status', help='Get job status')
        parser_g.add_argument(
            "-jid",
            dest="jobId",
            help='Job ID',
            type=str,
            default=None,
            required=True)
        parser_g.add_argument(
            "-i",
            dest="instanceName",
            help="Instance Name",
            type=str,
            default=None)
        parser_g.add_argument(
            '-k',
            dest="key",
            help='key-16 characters',
            type=str,
            default=None)
        parser_g.add_argument(
            '-tf',
            dest="tokenFilePath",
            help='Token File Path',
            type=str,
            default=None)
        parser_g.add_argument(
            '-of',
            dest="outputFilePath",
            help='Output File Path',
            type=str,
            default=None)
        parser_g.add_argument(
            '-lf',
            dest="logFilePath",
            help='Log File Path',
            type=str,
            default=None)
        parser_g.set_defaults(action='job_status')

        if len(sys.argv) > 1:
            """
            Non-interactive approach is chosen.
            """
            # importing module specific to non-interactive mode
            from Cryptodome.Cipher import AES
            if (len(sys.argv) == 2 and sys.argv[1] not in
                    ["login", "logout", "find", "backup", "restore", "job_status", "subclient", "browse"]
                    and sys.argv[1].startswith("-") is False):
                """ AD HOC BACKUP WITH DEFAULT OPTIONS """
                if not cvc_backup:
                    print("Backup commands not available")
                    exit(2)
                adHocInstanceName = 'Instance001'
                (lflag, adHocLoggingPath, lines1, lines2) = get_logging_path(
                    adHocInstanceName, None)
                if lflag:
                    LOG = logger.CVCLogger()
                    LOG.initializelogger('cvc.log', adHocLoggingPath)
                    LOG = LOG.log
                    LOG.info("Running in Non-interactive Mode")
                    LOG.info(
                        "Command being executed : " +
                        ' '.join(
                            str(e) for e in sys.argv))
                    LOG.info("Running adhoc backup with default options")
                    if lines1:
                        print_log_lines(lines1)
                    if lines2:
                        print_log_lines(lines2)
                else:
                    exit(2)
                adHocPath = sys.argv[1]
                if platform.system() == 'Linux':
                    if adHocPath.startswith("/") is False:
                        print(
                            "Operation failed. Invalid path provided as input for ad hoc backup")
                        LOG.error(
                            "Invalid path provided as input for ad hoc backup")
                        exit(2)
                elif platform.system() == 'Windows':
                    if adHocPath.find("/") == - \
                            1 and adHocPath.find("\\") == -1:
                        print(
                            "Operation failed. Invalid path provided as input for ad hoc backup")
                        LOG.error(
                            "Invalid path provided as input for ad hoc backup")
                        exit(2)
                else:
                    LOG.error("Unsupported OS. Exiting")
                    print("Operation failed. Unsupported OS.")
                    exit(2)
                adHocPath = [adHocPath]
                adHocAgentName = "file system"
                adHocEncKey = "This is a key123"
                adHocTokenpath = get_token_path(adHocInstanceName)
                NONINTERACTIVE_OBJ = Noninteractive()
                NONINTERACTIVE_OBJ.backup_ni(
                    adHocTokenpath,
                    None,
                    None,
                    None,
                    None,
                    'Incremental',
                    adHocPath,
                    None,
                    adHocInstanceName,
                    adHocAgentName,
                    adHocEncKey,
                    None,
                    adHocLoggingPath,
                    '')
                exit(0)
            try:
                args = parser.parse_args()
            except SystemExit:
                exit(1)
            instanceLoglines = []
            # check if the instance passed by user is valid
            if args.instanceName and not(
                    (sys.argv[1] == 'backup' or sys.argv[1] == 'restore' or sys.argv[1] == 'browse') and args.path):
                (flag, instanceLoglines) = check_instance(args.instanceName)
                if not flag:
                    print(
                        "Operation failed. Instance with the provided name does not exist")
                    exit(2)
                else:
                    iName = args.instanceName
            else:
                iName = 'Instance001'

            tokenpath = None
            loggingPath = None
            (lflag, loggingPath, lines1, lines2) = get_logging_path(
                iName, args.logFilePath)
            if lflag:
                LOG = logger.CVCLogger()
                LOG.initializelogger('cvc.log', loggingPath)
                LOG = LOG.log
                LOG.info("Running in Non-interactive Mode")

                if sys.argv[1] == 'login':
                    if "-p" in sys.argv:
                        sys.argv[sys.argv.index("-p") + 1] = "******"
                LOG.info("Command being executed : " + ' '.join(str(e)
                                                                for e in sys.argv))
                if instanceLoglines:
                    print_log_lines(instanceLoglines)
                if lines1:
                    print_log_lines(lines1)
                if lines2:
                    print_log_lines(lines2)
            else:
                exit(2)

            if args.tokenFilePath is not None:
                # Token file path provided by the user in the command is
                # considered as tokenpath.
                tokenpath = args.tokenFilePath
            else:
                tokenpath = get_token_path(iName)
            if args.key is not None:
                if len(args.key) != 16:
                    LOG.error("Key should be of 16 characters. Exiting")
                    print("Operation failed. Key should be of 16 characters. Exiting")
                    exit(2)
                encKey = args.key
            else:
                encKey = 'This is a key123'
            NONINTERACTIVE_OBJ = Noninteractive()
            if not(args.action == 'logout' or args.action == 'job_status'):
                agent_type = args.agent_type
                if len(agent_type) != 0:
                    if agent_type != 'fs' and agent_type != 'vsa':
                        print("Operation failed. Agent Type can only be 'fs' or 'vsa'")
                        exit(1)
            if args.action == 'login':

                # Set Force HTTPS to False, if reg key is set to 0 else True
                force_https = simpana_default_obj.force_https(iName, LOG)
                allow_http = simpana_default_obj.allow_http(iName, LOG)
                web_service_url = simpana_default_obj.web_service_url(iName, LOG)
                # User input takes first preference
                if args.force_https:
                    cvc_https = force_https = True if args.force_https.lower() == 'true' else False
                    # if user is forcing https through parameter, http shouldnt be allowed
                    if force_https:
                        allow_http = False

                cert_path = args.certificate_path
                if force_https and not cert_path:
                    cert_path = cvc_ca_bundle

                print_env_variables()

                NONINTERACTIVE_OBJ.login_ni(
                    tokenpath,
                    args.username,
                    args.password,
                    args.webConsoleHostName,
                    iName,
                    encKey,
                    force_https,
                    allow_http,
                    cert_path,
                    args.agent_type,
                    web_service_url=web_service_url)
            elif args.action == 'logout':
                NONINTERACTIVE_OBJ.logout_ni(tokenpath, encKey)
            elif args.action == 'backup':
                if args.path is not None:
                    # Adhoc backup with default options
                    NONINTERACTIVE_OBJ.backup_ni(
                        tokenpath, None, None, None, None, 'Incremental', [
                            args.path], None, iName, 'file system', 'This is a key123', None, loggingPath, args.agent_type)
                else:
                    NONINTERACTIVE_OBJ.backup_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        args.subclientId,
                        args.level,
                        args.contentPath,
                        args.directiveFilePath,
                        iName,
                        args.agentName,
                        encKey,
                        args.outputFilePath,
                        loggingPath,
                        args.agent_type)
            elif args.action == 'restore':
                if args.path is not None:
                    # Restore with default options
                    NONINTERACTIVE_OBJ.restore_ni(tokenpath,
                                                  None,
                                                  None,
                                                  None,
                                                  [args.path],
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  uo,
                                                  iName,
                                                  'file system',
                                                  'This is a key123',
                                                  None,
                                                  loggingPath,
                                                  None,
                                                  None,
                                                  args.agent_type,
                                                  show_deleted=cvc_default_show_deleted)
                elif args.sourcepath is not None or args.restorefilelist is not None:
                    NONINTERACTIVE_OBJ.restore_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        args.sourcepath,
                        args.restorefilelist,
                        args.destclient,
                        args.destpath,
                        args.fromTime,
                        args.toTime,
                        args.versions,
                        True if args.unconditional_overwrite == 'True' else False,
                        iName,
                        args.agentName,
                        encKey,
                        args.outputFilePath,
                        loggingPath,
                        args.browse_filter,
                        args.copy_precedence,
                        args.agent_type,
                        show_deleted=args.show_deleted == 'True')
                else:
                    LOG.error("Source path is not provided. Exiting")
                    print(
                        "Operation failed. Source path required for restore operation")
                    exit(1)
            elif args.action == 'job_status':
                NONINTERACTIVE_OBJ.job_status_ni(
                    tokenpath, args.jobId, encKey, args.outputFilePath, loggingPath)
            elif args.action == "subclient":
                if(args.subclient_create):
                    NONINTERACTIVE_OBJ.subclient_create_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        args.path,
                        args.exclude_path,
                        args.dsp,
                        iName,
                        args.agentName,
                        encKey,
                        loggingPath,
                        args.agent_type)
                elif(args.subclient_update):
                    NONINTERACTIVE_OBJ.subclient_update_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        args.path,
                        args.exclude_path,
                        args.overwrite,
                        iName,
                        args.agentName,
                        encKey,
                        loggingPath,
                        args.agent_type)
                else:
                    NONINTERACTIVE_OBJ.subclient_delete_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        iName,
                        args.agentName,
                        encKey,
                        loggingPath,
                        args.agent_type)
            elif args.action == 'browse':
                if args.path is not None:
                    # Browse with default options
                    NONINTERACTIVE_OBJ.browse_ni(
                        tokenpath,
                        None,
                        None,
                        None,
                        args.path,
                        0,
                        0,
                        False,
                        iName,
                        'file system',
                        None,
                        'This is a key123',
                        loggingPath,
                        args.agent_type,
                        show_deleted=cvc_default_show_deleted)
                elif args.browsepath is not None:
                    NONINTERACTIVE_OBJ.browse_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        args.browsepath,
                        args.fromTime,
                        args.toTime,
                        args.allVersions,
                        iName,
                        args.agentName,
                        args.browse_filter,
                        encKey,
                        loggingPath,
                        args.agent_type,
                        args.copy_precedence,
                        show_deleted=args.show_deleted == 'True')
                else:
                    LOG.info(
                        "Path is not passed in the browse command. Current working directory of local machine to be considered as browse path.")
                    NONINTERACTIVE_OBJ.browse_ni(
                        tokenpath,
                        args.clientName,
                        args.backupSetName,
                        args.subClientName,
                        os.getcwd(),
                        args.fromTime,
                        args.toTime,
                        args.allVersions,
                        iName,
                        args.agentName,
                        args.browse_filter,
                        encKey,
                        loggingPath,
                        args.agent_type,
                        args.copy_precedence)

            elif args.action == 'find':
                NONINTERACTIVE_OBJ.find_ni(
                    tokenpath,
                    args.clientName,
                    args.backupSetName,
                    args.subClientName,
                    args.findPath,
                    args.fromTime,
                    args.toTime,
                    iName,
                    args.agentName,
                    args.filename,
                    encKey,
                    args.agent_type,
                    args.copy_precedence,
                    loggingPath,
                    show_deleted=args.show_deleted == 'True'
                )
            elif args.action == 'adHocBackup':
                if args.contentPath or args.directiveFilePath:
                    NONINTERACTIVE_OBJ.backup_ni(
                        tokenpath,
                        None,
                        args.backupSetName,
                        args.subClientName,
                        args.subclientId,
                        'Incremental',
                        args.contentPath,
                        args.directiveFilePath,
                        iName,
                        args.agentName,
                        encKey,
                        args.outputFilePath,
                        loggingPath,
                        args.agent_type)
                else:
                    LOG.error(
                        "Insufficient information. Please provide a sub-command or provide content for adhoc backup")
                    print(
                        "Insufficient information. Please provide a sub-command or provide content for adhoc backup")
                    exit(1)
            exit(0)
        else:
            """
            Interactive approach is chosen.
            """
            # importing module specific to interactive mode
            try:
                import readline
            except ImportError:
                pass
            PROMPT_OBJ = MyPrompt()
            PROMPT_OBJ.prompt = 'cvc > '
            PROMPT_OBJ.cmdloop(
                'Starting prompt..')

    except SDKException as excp:
        print("Error encountered in SDK: %s" % str(excp))

    except Exception as cvc_exception:
        print("Failed with exception: %s" % str(cvc_exception))
