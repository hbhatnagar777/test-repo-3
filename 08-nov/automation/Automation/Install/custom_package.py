# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for custom package related operations from cloud

CustomPackage:    Class for creating custom packages from cloud

CustomPackageCloudXML:   Class for creating xml needed to create custom package from Cloud - cloud.commvault.com

CustomPackageWizardXML:  Class for Creating Custom Package xml needed to create custom package from 
                         cloud with New Custom Package Wizard

CustomPackageCreation:   Class for creating a custom package with user selected options

CustomPackage:

    __init__()                  --  initialize instance of the CustomPackage class

    create()                    --  Create a custom package using cloud form

    download()                  --  Download custom package from download center

    proxy_list()                --  Gets the list of Available clients from Proxy client group

    check_packages()            --  This method checks for presence of custom packages for a given package profile

    get_pkg_path()              --  Module to get unique profile directory path for given Custom package inputs.

CustomPackageCloudXML:

    create_installer_object(inputs ,commcell_obj) -- creates a machine object for the client,
    to get the OS details, then  initialize the class instance accordingly

    __init__(input_answers)             --  Initializes the CustomPackageCloudXML

    generate_xml()                      --  Generates the xml needed for Custom Package

    _request_id()                       --  Creates requestId tag and appends its child Tags

    _create_root()                      --  returns the XML object

    _input_xml()                        --  Appends the Input XML Tags

    _custom_install_package()           --  Appends the Custom Install Package Tags

    _package_info()                     --  Appends the Package Info Tags

    _proxy_info()                       --  Appends the Proxy Information Tags

    _admin_info()                       --  Appends the Admin Information Tags

    _advanced_info()                    --  Appends the Advanced Information Tags

CustomPackageCreation:

    __init__()                  --  initialize instance of the CustomPackageCreation class

    copy_media_to_client()      --  To copy media to remote client

    execute_command()           -- To execute script on remote windows client

    generate_json_for_custom_package()      --  Generates JSON for interactive creation of custom package

    create_custom_package()     --  Create a custom package

    compare_screens()           --  Module to compare the screens that are supposed to be seen by the user and the actual screens seen
                                    while custom package installation

"""
import json
import inspect
import os
from pprint import pformat
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element

from cvpysdk import commcell
from AutomationUtils import logger, constants, config
from AutomationUtils.machine import Machine
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from Install.bootstrapper_helper import BootstrapperHelper
from Install.installer_constants import REMOTE_FILE_COPY_LOC, INTERACTIVE_INSTALL_EXE_PATH, ScreenNameChangeDuringInstallDict, ScreensSeenOnlyDuringCustomPackageCreation, IgnoreList
from Install import installer_constants
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.options_selector import OptionsSelector


class CustomPackage(object):
    """ This class provides custom package related operations from cloud """

    def __init__(self, cloud_user=None, cloud_password=None, commcell_obj=None):
        """initialize instance of the CustomPackage class

        Args:

            cloud_user        (str)    -- Cloud user name for accessing cloud.commvault.com

            cloud_password    (str)    -- Cloud password for accessing cloud.commvault.com

            commcell_obj      (obj)    -- Commcell object for forevercell commcell

        """
        self.log = logger.get_log()
        self._forevercell = installer_constants.FOREVERCELL_HOSTNAME
        self._cloud_workflow = installer_constants.FOREVERCELL_WORKFLOW_NAME
        self._proxy_list = None
        self.config_json = config.get_config()

        # If cloud commcell object is provided use it
        if commcell_obj is not None:
            self._commcell = commcell_obj
        # Check if cloud user is provided then create cloud commcell object with it.
        elif cloud_user is not None:
            self.cloud_commcell = (cloud_user, cloud_password)
        else:
            self._commcell = None

        self._job_manager = JobManager(commcell=self._commcell)
        self._request_id = None

    def create(self, input_xml, workflow=None):
        """
        This method helps to create a custom package using cloud form

        Args:
            input_xml    (str):    -- Input XML for the workflow which'll create custom package

            workflow     (str)     -- Name of the workflow to execute for package creation

        Returns:
            Request id for the package creation request.

        Raises:
            SDKException:
                - if failed to create package
        """
        try:

            workflow = self._cloud_workflow if workflow is None else workflow

            self.log.info("Creating custom package from Workflow [{0}] on cloud".format(workflow))

            workflows = self._commcell.workflows
            custom_workflow = workflows.get(workflow)

            self.log.info("Executing workflow to create custom package with input xml: [{0}]".format(input_xml))

            response = custom_workflow.execute_workflow(input_xml)
            job_id = response[0]['jobId']
            request_id = response[0]['requestId']

            self.log.info("Job ID [{0}] and Request ID [{1}] received from workflow [{2}]"
                          "".format(str(job_id), str(request_id), workflow))

            self._job_manager.job = response[1]
            self._job_manager.wait_for_state('completed', time_limit=120)

            self.log.info("Custom Package created successfully")

            self.request_id = request_id
            return request_id

        except Exception as excp:
            self.log.exception("Failed in custom package creation !!")
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def download(self, proxy_list=None, download_dir=None, workflow=None, platform_list=[]):
        """
        This method helps to download custom package from cloud Download Center

        Args:
            proxy_list        (list)    -- Custom client proxy string with format:
                                            [cl1:cl1_hostname:4333, cl2:cl2_hostname:4333]

            download_dir      (str)     -- Download custom package created from cloud.

            workflow     (str)          -- Name of the workflow used for creating package creation

            platform_list        (list)   -- Platforms list to check in the packages path
                                             Supported:
                                                macOS
                                                Windows-x64
                                                Windows-x86

        Returns:
            (dict)    Dictionary with package name, size

        Raises:
            SDKException:
                - if failed to download package
        """
        try:
            if not platform_list:
                platform_list = ['macOS', 'macOS_arm64', 'Windows-x64', 'Windows-x86']
            workflow = self._cloud_workflow if workflow is None else workflow
            download_packages = installer_constants.PACKAGES_TO_DOWNLOAD
            download_dir = constants.TEMP_DIR if download_dir is None else download_dir
            if proxy_list is None:
                proxy_list = self._proxy_list
            
            return_value = {}
            _machine = Machine()

            for _package in download_packages.keys():
                if not proxy_list and _package == "Proxy Packages":
                    self.log.info("Proxy not provided. Skip downloading proxy packages")
                    continue

                pkg_name = "{0} [requestid: {1}]".format(_package, self.request_id)

                self.log.info("Downloading packages for [{0}] at [{1}]".format(pkg_name, download_dir))

                for _platform in platform_list:
                    _binary = download_packages[_package][_platform]
                    self.log.info("Downloading binary: [{0}] for [{1}]".format(_binary, _platform))
                    self._commcell.download_center.download_package(pkg_name, download_dir, _platform)
                    return_value[_binary] = {}
                    return_value[_binary]['size'] = _machine.get_file_size(os.path.join(download_dir, _binary))
                    return_value[_binary]['download_path'] = download_dir

                self.log.info("Downloaded all packages at [{0}]".format(download_dir))

            return return_value

        except Exception as excp:
            self.log.exception("Failed to download custom packages !!")
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def proxy_list(self, commcell_obj, proxy_client_group=None, proxy_port=None):
        """ This Method gets the list of Available clients from Proxy client group

            Args:

                commcell_obj        (obj)    -- Commcell object for CS

                proxy_client_group  (str)    -- Proxy client group to check for proxy clients

                proxy_port          (int)    -- Common proxy port configured for client

        Returns:
            (str)    Generated custom network proxy string and returns back.
                        Format : [client1:client1_hostname:4333, client2:client2_hostname:4333]

        Raises:
            SDKException:
                - if failed to generate proxy list.
        """
        try:
            proxy_list = []

            if proxy_client_group is None:
                proxy_client_group = installer_constants.PROXY_GROUP_NAME

            if commcell_obj.client_groups.has_clientgroup(proxy_client_group):
                client_group_obj = commcell_obj.client_groups.get(proxy_client_group)
                clients_in_proxy_group = client_group_obj.associated_clients

                for client_name in clients_in_proxy_group:
                    host_name = commcell_obj.clients.all_clients[client_name.lower()]['hostname']

                    # Getting the tunnel connection port for client
                    _port = commcell_obj.clients.get(client_name).network._tunnel_connection_port
                    self.log.info("Tunnel connection port for client [{0}]: [{1}]".format(client_name, _port))

                    if _port is not None and _port != "" and proxy_port is not None:
                        if str(_port) != str(proxy_port):
                            self.log.error("Error!. Proxy port [{0}] and client tunnel"
                                           "connection port [{1}] do not match".format(proxy_port, _port))
                            _proxy_port = proxy_port
                        else:
                            _proxy_port = _port
                    else:
                        _proxy_port = installer_constants.PROXY_DEFAULT_PORT

                    proxy_list.append(client_name + ":" + host_name + ":" + _proxy_port)
            else:
                self.log.info("Creating client group [{0}]".format(proxy_client_group))
                commcell_obj.client_groups.add(proxy_client_group)

            self.log.info("Proxy client list for client group [{0}]: [{1}]".format(proxy_client_group, proxy_list))

            self._proxy_list = proxy_list
            return proxy_list

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    def get_pkg_path(self, custom_package_dict):
        """
        Module to get unique profile directory path for given Custom package creation inputs.
        After the custom packages are created they can be copied over to this path to maintain unique profies.

        Args:
            custom_package_dict        (dict)    -- Keyword arguments for creating custom package

        Returns:
            (str)    -- Returns the directory path where custom packages have to be checked/downloaded

        Raises:
            SDKException:
                - if failed to execute at a given point of execution.
        """
        try:
            package_profile = 'Rev'
            for key in ['SP_revision', 'authcode', 'SubClientPlan',
                        'Custom_pkg_username', 'laptopClient', 'ClientGroups',
                        'backupMonitor', 'hideApps', 'cloud_laptop']:
                key_str = custom_package_dict.get(key) if custom_package_dict.get(key) is not None else 'NA'
                if not key_str:
                    key_str = 'NA'
                package_profile += str(key_str) + "_"

            if custom_package_dict.get('proxy_list'):
                package_profile += "_proxy"
            
            if custom_package_dict.get('endpointurl', False):
                cs_name = custom_package_dict.get('endpointurl').replace(':', '_endpointurl_').replace('/', '')
            else:
                cs_name = custom_package_dict['commcell_object'].commserv_hostname
                
            dir_str = cs_name + "_SP" + str(custom_package_dict['commcell_object'].commserv_version)
            return os.path.join(constants.TEMP_DIR, dir_str, package_profile)

        except Exception as excp:
            self.log.exception("Failed to get custom packages path!!")
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def check_packages(self, packages_path, platform_list):
        """
        This method checks for presence of custom packages for a given package profile
        If all relevant packages are found module returns True, else False

        Args:
            packages_path        (str)    -- Path where the custom packages have to be checked for availability

            platform_list        (list)   -- Platforms list to check in the packages path
                                             Supported:
                                                macOS
                                                Windows-x64
                                                Windows-x86

        Returns:
            (bool)    -- True if all packages are found, else return False

        Raises:
            SDKException:
                - if failed to execute at a given point of execution.
        """
        try:
            self.log.info("Checking custom packages availability at [{0}]".format(packages_path))

            download_packages = installer_constants.PACKAGES_TO_DOWNLOAD
            controller = Machine()
            return_value = {}
            
            if not controller.check_directory_exists(packages_path):
                self.log.info("""Custom Packages path [{0}] does not exist on [{1}]"""
                              .format(packages_path, controller.machine_name))
                self.log.info("Creating [{0}] on [{1}]".format(packages_path, controller.machine_name))
                controller.create_directory(packages_path)
                return False

            for _package in download_packages:
                if not self._proxy_list and _package == "Proxy Packages":
                    self.log.info("Proxy not provided. Skip checking proxy packages")
                    continue

                for _platform in platform_list:
                    pkg = download_packages[_package][_platform]
                    if controller.check_file_exists(os.path.join(packages_path, pkg)):
                        self.log.info("Package [{0}] found".format(pkg))
                        return_value[pkg] = {}
                        return_value[pkg]['size'] = controller.get_file_size(os.path.join(packages_path, pkg))
                        return_value[pkg]['download_path'] = packages_path
                    else:
                        self.log.info("Package [{0}] not found".format(pkg))
                        return False

            self.log.info("All relevant custom packages found at [{0}]".format(packages_path))
                    
            return return_value

        except KeyError as kerror:
            self.log.error("Failed to get platform info for [{0}]".format(kerror))
        except Exception as excp:
            self.log.exception("Failed to check for custom packages !!")
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    @property
    def request_id(self):
        """ Read only attribute for request_id"""
        return self._request_id

    @request_id.setter
    def request_id(self, value):
        """ Sets the request_id attribute of the class"""
        self._request_id = value

    @property
    def cloud_commcell(self):
        """ Read only attribute for cloud_commcell"""
        return self._commcell

    @cloud_commcell.setter
    def cloud_commcell(self, cloud_credentials=None):
        """ Sets the cloud_commcell attribute of the class
        Args:

            cloud_credentials (tuple) : Cloud user name and password passed as a tuple to the setter

        Returns:
            cloud commcell object

        Raises
            Exception:
                - If failed to create cloud object.
        """
        try:
            if cloud_credentials is None:
                cloud_user = self.config_json.cloud.username
                cloud_password = self.config_json.cloud.password
            else:
                cloud_user = cloud_credentials[0]
                cloud_password = cloud_credentials[1]

            self.log.info("Creating forevercell commcell object for cloud user {0}".format(cloud_user))
            self._commcell = commcell.Commcell(self._forevercell, cloud_user, cloud_password)
            return self._commcell

        except Exception as excp:
            raise Exception("\n {0}: Failed to initialize cloud object{1}".format(inspect.stack()[0][3], str(excp)))


class CustomPackageCloudXML(object):
    """Class for Creating Custom Package xml needed to create custom package from cloud"""

    def __init__(self, input_answers):
        """Initialize the CustomPackageCloudXML class instance for generating XML

            Args:
                input_answers (dict) -- inputs for Installation

                    Supported keywords:
                    ------------------

                    commcell_object: (obj) (Mandatory): Commcell object

                    Custom_pkg_username: (str) (optional): User name for logging in commcell

                    Custom_pkg_password: (str) (optional): Password for logging in commcell

                    authcode: (str) (optional): Package will be created with this auth code

                    servicePack: (str)  (optional): Service Pack for which the package has to be created

                    SP_revision: (int) (optional): Service pack revision for which package needs to be created.
                                                    If not provided, this would not be populated with package creation

                    proxy_list (list) (optional): Proxy string list for clients in given format
                                                    [cl1:cl1_hostname:4333, cl2:cl2_hostname:4333]

                    ClientGroups (list) (optional): List of client groups to add the laptop client

                    WindowsSubClientPolicy (str) (optional): Windows sub client policy

                    MacSubClientPolicy (str) (optional): Mac Subclient policy

                    SubClientPlan (str) (optional): Sub client plan

                    laptopClient (str): Configure package for laptop client? ("true", "false")

                    requireCredentials (str): Require credentials? (Default: "true")

                    backupMonitor (str): Enable Edge Monitor shortcut (Windows) ('true', 'false')

                    hideApps (str): Show Edge Monitor App (Mac) ('true', 'false')

                    chooseOS (str): Platform to create packages for.

                    cloud_laptop (bool): Is cloud laptop? Default: False
                    
                    endpointurl (str): Endpoint URL 

            Returns:
                object  -   instance of the CustomPackageCloudXML class

        """
        self.input_answers = input_answers
        self._commcell = input_answers['commcell_object']
        if input_answers.get('servicePack') is None:
            self.input_answers['servicePack'] = 'SP' + str(self._commcell.commserv_version)
        self.input_answers['commserv_host_name'] = self._commcell.commserv_hostname
        self.input_answers['commserv_client_name'] = self._commcell.commserv_name
        if input_answers.get('backupMonitor') is None:
            self.input_answers['backupMonitor'] = "true"
        if input_answers.get('hideApps') is None:
            self.input_answers['hideApps'] = "false"
        if input_answers.get('Custom_pkg_username') is None:
            self.input_answers['Custom_pkg_username'] = ""
        if input_answers.get('Custom_pkg_password') is None:
            self.input_answers['Custom_pkg_password'] = ""
        if input_answers.get('authcode') is None:
            self.input_answers['authcode'] = ""
        if input_answers.get('ClientGroups') is None:
            self.input_answers['ClientGroups'] = []
        if input_answers.get('WindowsSubClientPolicy') is None:
            self.input_answers['WindowsSubClientPolicy'] = ""
        if input_answers.get('MacSubClientPolicy') is None:
            self.input_answers['MacSubClientPolicy'] = ""
        if input_answers.get('SubClientPlan') is None:
            self.input_answers['SubClientPlan'] = ""
        if input_answers.get('laptopClient') is None or input_answers.get('laptopClient') == "true":
            self.input_answers['laptopClient'] = "true"
        else:
            self.input_answers['laptopClient'] = "false"
        if input_answers.get('requireCredentials') is None or input_answers.get('requireCredentials') == "true":
            self.input_answers['requireCredentials'] = "true"
        else:
            self.input_answers['requireCredentials'] = "false"
        self.input_answers['cloud_laptop'] = input_answers.get('cloud_laptop', False)
        self.input_answers['endpointurl'] = input_answers.get('endpointurl', '')

        self.log = logger.get_log()
        self.log.info("Custom package creation input arguments: [{0}]".format(self.input_answers))

    def generate_xml(self):
        """generates the xml for CustomPackageCloudXML class

            Returns:
                str  -   xml in String Format

        """
        self.log.info("Generating xml from inputs [{0}]".format(pformat(self.input_answers)))
        simxml = self._create_root()
        simxml = ET.tostring(simxml).decode('utf-8')
        return simxml

    def _create_root(self):
        """
        This Method creates Root Tag and appends child tags to it
            Returns:
                Object            --  XML Root Object

            Raises:
                SDKException:
                    if any exception raised while generating the XML
        """
        try:
            root = Element('inputs')
            root.append(self._input_xml())
            return root

        except Exception as excp:
            self.log.exception("Failed to create root tag: %s" % excp)
            return None

    def _request_id(self):
        """Creates requestId tag and appends its child Tags"""
        request_id_component = Element('requestId')
        request_id_component.text = self.input_answers['request_id']
        return request_id_component

    def _input_xml(self):
        """Creates inputXML tag and appends its child Tags"""
        input_xml_component = Element('inputXML')
        input_xml_component.append(self._custom_install_package())
        return input_xml_component

    def _custom_install_package(self):
        """Creates Custom_Install_Package tag and appends its child Tags"""
        custom_package_component = Element('Custom_Install_Package')
        custom_package_component.append(self._package_info())
        custom_package_component.append(self._proxy_info())
        custom_package_component.append(self._admin_info())
        custom_package_component.append(self._advanced_info())
        return custom_package_component

    def _package_info(self):
        """Creates Package_Info tag and appends its child Tags"""
        package_info_component = Element('Package_Info')
        package_info_component.set('shortNameCS', self.input_answers.get('commserv_client_name', ''))
        package_info_component.set('hostNameCS', self.input_answers.get('commserv_host_name', ''))
        proxy_list = self.input_answers.get('proxy_list')
        if proxy_list is None or not proxy_list:
            package_info_component.set('useProxy', 'false')
        else:
            package_info_component.set('useProxy', 'true')
        package_info_component.set('servicePack', self.input_answers['servicePack'])
        rev = self.input_answers.get('SP_revision')
        if rev is not None and str(rev) != '0':
            package_info_component.set('revision', 'Rev' + str(rev))
        package_info_component.set('multiRules', 'false')
        package_info_component.set('requireCredentials', str(self.input_answers['requireCredentials']))
        if self.input_answers['laptopClient'] == 'true': 
            package_info_component.set('chooseClient', 'Desktop/Laptop')
        else:
            package_info_component.set('chooseClient', '')
        package_info_component.set('chooseOS', "[" + self.input_answers.get('chooseOS') + "]")
        if self.input_answers['cloud_laptop']:
            package_info_component.set('additionalPackages', "Storage Accelerator")
        return package_info_component

    def _proxy_info(self):
        """Creates Proxy_Info tag and appends its child Tags"""
        proxy_info_component = Element('Proxy_Info')
        if 'proxy_list' in self.input_answers.keys() and self.input_answers['proxy_list']:
            client_list = []
            hostname_list = []
            port_number_list = []
            for each_proxy in self.input_answers['proxy_list']:
                client_list.append(each_proxy.split(':')[0])
                hostname_list.append(each_proxy.split(':')[1])
                port_number_list.append(each_proxy.split(':')[2])
            proxy_info_component.set('proxyClientName', "[" + ",".join(str(name) for name in client_list) + "]")
            proxy_info_component.set('proxyHostname', "[" + ",".join(str(name) for name in hostname_list) + "]")
            proxy_info_component.set('proxyPort', "[" + ",".join(str(name) for name in port_number_list) + "]")
        else:
            proxy_info_component.set('proxyClientName', "[]")
            proxy_info_component.set('proxyHostname', "[]")
            proxy_info_component.set('proxyPort', "[]")
        proxy_info_component.set('httpProxyHostname', '')
        proxy_info_component.set('httpProxyPort', '')
        proxy_info_component.set('autoHTTPProxy', 'true')
        return proxy_info_component

    def _admin_info(self):
        """Creates Admin_Info tag and appends its child Tags"""
        admin_info_component = Element('Admin_Info')
        admin_info_component.set('username', self.input_answers.get('Custom_pkg_username', ''))
        admin_info_component.set('password', self.input_answers.get('Custom_pkg_password', ''))
        admin_info_component.set('authCode', self.input_answers.get('authcode', ''))
        admin_info_component.set('authLater', "false")
        return admin_info_component

    def _advanced_info(self):
        """Creates Advanced_Info tag and appends its child Tags"""
        advanced_info_component = Element('Advanced_Info')
        advanced_info_component.set('editAdvancedOptions', 'false')
        advanced_info_component.set('clientGroup', self.input_answers.get('ClientGroups', []))
        advanced_info_component.set('windowsSubclientPolicy', self.input_answers.get('WindowsSubClientPolicy', ""))
        advanced_info_component.set('macSubclientPolicy', self.input_answers.get('MacSubClientPolicy', ""))
        advanced_info_component.set('showInstallDirectory', 'false')
        advanced_info_component.set('hideApps', self.input_answers.get('hideApps', 'false'))
        advanced_info_component.set('includeVPN', 'false')

        advanced_info_component.set('backupMonitor', self.input_answers.get('backupMonitor', 'true'))
        advanced_info_component.set('migrationAssistant', 'true')
        advanced_info_component.set('processManager', 'true')
        advanced_info_component.set('subClientPlan', self.input_answers.get('SubClientPlan', ''))
        advanced_info_component.set('thirdParty', 'false')
        return advanced_info_component

class CustomPackageWizardXML(object):
    """Class for Creating Custom Package xml needed to create custom package from cloud with New Custom Package Wizard"""

    def __init__(self, input_answers):
        """Initialize the CustomPackageCloudXML class instance for generating XML

            Args:
                input_answers (dict) -- inputs for Installation

                    Supported keywords:
                    ------------------

                    commcell_object: (obj) (Mandatory): Commcell object

                    Custom_pkg_username: (str) (optional): User name for logging in commcell

                    Custom_pkg_password: (str) (optional): Password for logging in commcell

                    authcode: (str) (optional): Package will be created with this auth code

                    servicePack: (str)  (optional): Service Pack for which the package has to be created

                    SP_revision: (int) (optional): Service pack revision for which package needs to be created.
                                                    If not provided, this would not be populated with package creation

                    proxy_list (list) (optional): Proxy string list for clients in given format
                                                    [cl1:cl1_hostname:4333, cl2:cl2_hostname:4333]

                    ClientGroups (list) (optional): List of client groups to add the laptop client

                    WindowsSubClientPolicy (str) (optional): Windows sub client policy

                    MacSubClientPolicy (str) (optional): Mac Subclient policy

                    SubClientPlan (str) (optional): Sub client plan

                    laptopClient (str): Configure package for laptop client? ("true", "false")

                    requireCredentials (str): Require credentials? (Default: "true")

                    backupMonitor (str): Enable Edge Monitor shortcut (Windows) ('true', 'false')

                    hideApps (str): Show Edge Monitor App (Mac) ('true', 'false')

                    chooseOS (str): Platform to create packages for.

                    cloud_laptop (bool): Is cloud laptop? Default: False
                    
                    endpointurl (str): Endpoint URL 

            Returns:
                object  -   instance of the CustomPackageCloudXML class

        """
        self.input_answers = input_answers
        self._commcell = input_answers['commcell_object']
        if input_answers.get('servicePack') is None:
            self.input_answers['servicePack'] = 'SP' + str(self._commcell.commserv_version)
        self.input_answers['commserv_host_name'] = self._commcell.commserv_hostname
        self.input_answers['commserv_client_name'] = self._commcell.commserv_name
        if input_answers.get('backupMonitor') is None:
            self.input_answers['backupMonitor'] = "true"
        if input_answers.get('hideApps') is None:
            self.input_answers['hideApps'] = "false"
        if input_answers.get('Custom_pkg_username') is None:
            self.input_answers['Custom_pkg_username'] = ""
        if input_answers.get('Custom_pkg_password') is None:
            self.input_answers['Custom_pkg_password'] = ""
        if input_answers.get('authcode') is None:
            self.input_answers['authcode'] = ""
        if input_answers.get('ClientGroups') is None:
            self.input_answers['ClientGroups'] = []
        if input_answers.get('WindowsSubClientPolicy') is None:
            self.input_answers['WindowsSubClientPolicy'] = ""
        if input_answers.get('MacSubClientPolicy') is None:
            self.input_answers['MacSubClientPolicy'] = ""
        if input_answers.get('SubClientPlan') is None:
            self.input_answers['SubClientPlan'] = ""
        if input_answers.get('laptopClient') is None or input_answers.get('laptopClient') == "true":
            self.input_answers['laptopClient'] = "true"
        else:
            self.input_answers['laptopClient'] = "false"
        if input_answers.get('requireCredentials') is None or input_answers.get('requireCredentials') == "true":
            self.input_answers['requireCredentials'] = "true"
        else:
            self.input_answers['requireCredentials'] = "false"
        self.input_answers['cloud_laptop'] = input_answers.get('cloud_laptop', False)
        if input_answers.get('endpointurl') is None:
            self.input_answers['endpointurl'] = ""

        self.log = logger.get_log()
        self.log.info("Custom package creation input arguments: [{0}]".format(self.input_answers))

    def generate_xml(self):
        """generates the xml for CustomPackageCloudXML class

            Returns:
                str  -   xml in String Format

        """
        self.log.info("Generating xml from inputs [{0}]".format(pformat(self.input_answers)))
        simxml = self._create_root()
        simxml = ET.tostring(simxml).decode('utf-8')
        return simxml

    def _create_root(self):
        """
        This Method creates Root Tag and appends child tags to it
            Returns:
                Object            --  XML Root Object

            Raises:
                SDKException:
                    if any exception raised while generating the XML
        """
        try:
            root = Element('inputs')
            root.append(self._cloudmode_xml())
            root.append(self._input_xml())
            return root

        except Exception as excp:
            self.log.exception("Failed to create root tag: %s" % excp)
            return None

    def _request_id(self):
        """Creates requestId tag and appends its child Tags"""
        request_id_component = Element('requestId')
        request_id_component.text = self.input_answers['request_id']
        return request_id_component


    def _cloudmode_xml(self):
        """Creates inputXML tag and appends its child Tags"""
        cloudmode_xml_component = Element('CloudMode')
        cloudmode_xml_component.text = 'Test'
        return cloudmode_xml_component

    def _input_xml(self):
        """Creates inputXML tag and appends its child Tags"""
        input_xml_component = Element('inputXML')
        input_xml_component.append(self._custom_install_package())
        return input_xml_component

    def _custom_install_package(self):
        """Creates Custom_Install_Package tag and appends its child Tags"""
        custom_package_component = Element('Custom_Install_Package')        
        custom_package_component.append(self._package_info())
        custom_package_component.append(self._proxy_info())
        custom_package_component.append(self._http_proxy_info())
        custom_package_component.append(self._roles_info())
        custom_package_component.append(self._admin_info())
        custom_package_component.append(self._advanced_info())
        return custom_package_component

    def _package_info(self):
        """Creates Package_Info tag and appends its child Tags"""
        package_info_component = Element('Package_Info')

        package_info_component.set('profile', 'New')
        package_info_component.set('servicePack', self.input_answers['servicePack'])
        package_info_component.set('uid', 'Automation')
        package_info_component.set('transactionId', "")
        package_info_component.set('cloudMode', 'Test')
        
        rev = self.input_answers.get('SP_revision')
        if rev is not None and str(rev) != '0':
            package_info_component.set('revision', 'Rev' + str(rev))

        _os = self.input_answers.get('chooseOS', '')
        if 'mac' in self.input_answers.get('chooseOS', '').lower():
            _os = "macOS"
             
        package_info_component.set('chooseOS', "[" + _os + "]")
        package_info_component.set('endPoint', self.input_answers['endpointurl'])
        if self.input_answers['cloud_laptop']:
            package_info_component.set('chooseCloudDirect', "true")
            package_info_component.set('additionalPackages', "Storage Accelerator")
        else:
            package_info_component.set('chooseCloudDirect', "false")
        return package_info_component

    def _proxy_info(self):
        """Creates Proxy_Info tag and appends its child Tags"""
        proxy_info_component = Element('Gateway_Info')
        if 'proxy_list' in self.input_answers.keys() and self.input_answers['proxy_list']:
            client_list = []
            hostname_list = []
            port_number_list = []
            for each_proxy in self.input_answers['proxy_list']:
                client_list.append(each_proxy.split(':')[0])
                hostname_list.append(each_proxy.split(':')[1])
                port_number_list.append(each_proxy.split(':')[2])
            proxy_info_component.set('GatewayName', ",".join(str(name) for name in client_list))
            proxy_info_component.set('GatewayPort', ",".join(str(name) for name in port_number_list))
        else:
            # If endpoint is not provided AND no proxy info is available then, write the CS info in Gateway info 
            if not self.input_answers['endpointurl']:
                proxy_info_component.set('GatewayName', self.input_answers.get('commserv_host_name', ''))
                proxy_info_component.set('GatewayPort', "8403")
            else:
            # if no CS info or proxy or endpoint is provided then write nothing in GatewayName
                proxy_info_component.set('GatewayName', '')
                proxy_info_component.set('GatewayPort', '')
        proxy_info_component.set('connectLater', "false")
        proxy_info_component.set('showToUserGateway', "false")
        
        return proxy_info_component

    def _http_proxy_info(self):
        """Creates Proxy_Info tag and appends its child Tags"""
        http_proxy_info_component = Element('HttpProxy_Info')
        http_proxy_info_component.set('httpProxyHostname', "")
        http_proxy_info_component.set('httpProxyPort', "")
        http_proxy_info_component.set('autoHTTPProxy', 'true')
        return http_proxy_info_component

    def _roles_info(self):
        """Creates Proxy_Info tag and appends its child Tags"""
        roles_info_component = Element('Roles_Info')
        if self.input_answers['laptopClient'] == 'true':
            roles_info_component.set('SelectedRoles', 'Laptop')
        else:
            roles_info_component.set('SelectedRoles', 'File server')
        roles_info_component.set('showToUser', 'false')

        return roles_info_component
        
    def _admin_info(self):
        """Creates Admin_Info tag and appends its child Tags"""
        admin_info_component = Element('Admin_Info')
        admin_info_component.set('requireCredentials', str(self.input_answers['requireCredentials']))
        admin_info_component.set('username', self.input_answers.get('Custom_pkg_username', ''))
        admin_info_component.set('password', self.input_answers.get('Custom_pkg_password', ''))
        admin_info_component.set('authCode', self.input_answers.get('authcode', ''))
        return admin_info_component

    def _advanced_info(self):
        """Creates Advanced_Info tag and appends its child Tags"""
        advanced_info_component = Element('Advanced_Info')
        advanced_info_component.set('clientGroup', self.input_answers.get('ClientGroups', []))
        advanced_info_component.set('windowsSubclientPolicy', self.input_answers.get('WindowsSubClientPolicy', ""))
        advanced_info_component.set('macSubclientPolicy', self.input_answers.get('MacSubClientPolicy', ""))
        advanced_info_component.set('showInstallDirectory', 'false')
        advanced_info_component.set('hideApps', self.input_answers.get('hideApps', 'false'))
        advanced_info_component.set('includeVPN', 'false')
        advanced_info_component.set('backupMonitor', self.input_answers.get('backupMonitor', 'true'))
        advanced_info_component.set('migrationAssistant', 'true')
        advanced_info_component.set('processManager', 'true')
        advanced_info_component.set('subClientPlan', self.input_answers.get('SubClientPlan', ''))
        advanced_info_component.set('thirdParty', 'false')
        return advanced_info_component

class CustomPackageCreation:

    """Class for creating a Custom Package on a client."""

    def __init__(self, commcell, feature_release, machine_obj, remote_machine_credentials=None):
        """
            Initialize instance of the CustomPackageCreation class.
                Args:
                    commcell -- commcell object for creation of custom package

                    feature_release -- feature release of the bootstrapper

                    machine_obj -- machine object

                    remote_machine_credentials (dict)
                    --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                                Windows Client
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)

                                Unix Client
                                commservePassword   (str)        Commserve Password without Encoding/Encrypting

        """
        self.id = None
        self.install_directory = None
        self.options_selector = None
        self.commcell = commcell
        self.remote_media_path = None
        self.bootstrapper = None
        self.log = logger.get_log()
        self.feature_release = feature_release
        self.machine_obj = machine_obj
        self.config_json = config.get_config()
        self.remote_machine_credentials = remote_machine_credentials
        self.remote_clientname = remote_machine_credentials["remote_clientname"]
        self.remote_username = remote_machine_credentials["remote_username"]
        self.remote_userpassword = remote_machine_credentials["remote_userpassword"]
        self.machine = Machine(self.remote_clientname,
                               username=self.remote_username,
                               password=self.remote_userpassword)
        self.log_directory = REMOTE_FILE_COPY_LOC

    def copy_media_to_client(self, media_path, remote_loc):
        """
            To copy media from controller to remote client machine

            Args:
                media_path         (str)   -- Path where media resides

                remote_loc         (str)   -- Destination path
        """
        output = self.machine.copy_from_local(media_path, remote_loc, raise_exception=True)
        if not output:
            raise Exception(f'Failed to copy media to the machine {self.machine.machine_name}')
        self.log.info('Successfully copied media to machine %s', self.machine.machine_name)

    def execute_command(self, command=None):
        """
            To execute the command on the remote machine using PaExec.exe

            Args:

                command     (str)   -- Command to execute on the remote machine

            Returns:
                (int)       -- Return code of the command executed
        """

        task_name = 'Interactive Installation Schedule'
        systime = self.machine.add_minutes_to_system_time(2).strip()
        sysdate = self.machine.execute_command(r'get-date -Format "MM\/dd\/yyyy"').output.strip()
        task_options = "/tn \"" + task_name + "\" /tr \"" + command + "\" /sc once /st " + \
                       systime + " /sd " + sysdate + " /f"
        task_status_check_command = "$events = @(" \
                                    "Get-WinEvent  -FilterXml @\'\n" \
                                    "<QueryList>\n" \
                                    "<Query Id=\"0\" Path=\"Microsoft-Windows-TaskScheduler/Operational\">\n" \
                                    "<Select Path=\"Microsoft-Windows-TaskScheduler/Operational\">\n" \
                                    "*[EventData/Data[@Name=\'TaskName\']=\'\\{0}\']\n" \
                                    "</Select>\n" \
                                    "</Query>\n" \
                                    "</QueryList>\n" \
                                    "\'@  -ErrorAction Stop -MaxEvents 2\n" \
                                    ");" \
                                    "$events".format(task_name)

        self.machine.create_task(task_options)
        self.machine.wait_for_task(task_name, taskstatus="Running", retry_interval=60)
        self.machine.wait_for_task(task_name, retry_interval=120, time_limit=120)
        self.log.info('Checking the status of Installer Task Schedule')
        output = self.machine.execute_command(task_status_check_command)
        if ': 201' in output.output and 'with return code 0.' in ' '.join(output.output.replace('\r\n', '').split()):
            self.log.info('Interactive Install exe completed successfully')
        else:
            self.log.info('Unable to fetch Task results from Event Viewer')
        self.machine.delete_task(task_name)

    def generate_json_for_custom_package(self, **kwargs):
        """
                To generate the JSON file for creation and installation
                of custom package using the InteractiveInstaller binary

               Args:
                    **kwargs (dict) -- inputs for Installation

                    Supported keywords:
                    ------------------

                    commcellUser: (str) (optional): Username of tbe commcell object

                    IsUpdate: (bool) (optional): For specifying whether the installation is an update

                    FEATURE_SELECTION: (dict) (optional): For specifying the packages to be installed.
                                                          Default is Filesystem and FileSystem Core

                    IsBootstrapper: (bool) (optional): Whether the installer is Bootstrapper

                    IsToDownload: (bool)  (optional): Whether the media is for installation or for
                                                      downloading packages for installation on other
                                                      systems

                    CreateNewInstanceCustomPackage: (bool) (optional): Creates a new instance custom package
                                                                       if set to True

                    CreateNewInstance: (bool) (optional): Decides the instance of the

                    OEMID: (int)  (optional): To select the OEM id for custom packages.
                                              Default is 1 (Commvault)

                    installMode: (str) (optional): Select the install mode for the custom package

                    SaveUserAnswers: (bool) (optional): To select the SaveUserAnswers option

                    Instance: (str)  (optional): Selects the instance for which the custom package is
                                                 being created for

                    BootStrapMode: (bool) (optional): Boolean value for bootstrap mode

                    SelectedPackages: (str) (optional): Packages are selected in string

                    CreateSelfExtracting: (bool)  (optional): Whether to create the media as a self
                                                              extracting boolean

                    RestoreOnly: (bool) (optional): To enable restore only option

                    DecoupledInstall: (bool) (optional): Boolean value for decoupled install mode

                    CreateSeedPackage: (bool) (optional): To enable roles manager option

                    ShowToUsers: (bool)  (optional): To enable show to users option

                    CommserveName: (str) (optional): Name of the Commserver

                    donot_configure_Edge_Monitor: (bool) (optional):  To configure the Edge Monitor Role

                    installOption: (bool) (optional): To select the installation Option.
                                                      Default is install updates

                    enable_two_FA:  (bool) (optional): To enable/disable two factor authentication
                                                     Default is False

                    token_URL:  (str): URL to connect to the controll and fetch the 2tfa pin
                                       Default is null
                Returns: None


        """
        self.config_json = config.get_config()

        # Generating JSON for custom package creation
        custom_package_json = {
            "commcellUser": kwargs.get("commcellUser", self.commcell.commcell_username),
            "IsUpdate": kwargs.get("IsUpdate", False),
            "FEATURE_SELECTION": kwargs.get("FEATURE_SELECTION", {
                "Microsoft Windows": [
                    "File System Core",
                    "File System"
                ]
            }),
            "IsBootstrapper": kwargs.get("IsBootstrapper", True),
            "IsToDownload": kwargs.get("IsToDownload", True),
            "CreateNewInstanceCustomPackage": kwargs.get("CreateNewInstanceCustomPackage", False),
            "CreateNewInstance": kwargs.get("CreateNewInstance", False),
            "OEMID": kwargs.get("OEMID", "1"),
            "SelectedOS": [
                "WinX64"
            ],
            "installMode": kwargs.get("installMode", "0"),
            "SaveUserAnswers": kwargs.get("SaveUserAnswers", False),
            "Instance": kwargs.get("Instance", "Instance001"),
            "BootStrapMode": kwargs.get("BootStrapMode", True),
            "SelectedPackages": kwargs.get("SelectedPackages", "1,702"),
            "commcellPassword": kwargs.get("commcellPassword", None),
            "CustomPackageDir": REMOTE_FILE_COPY_LOC + "\\" + kwargs.get("CustomPackageDir", "CustomPackageLocation"),
            "CreateSelfExtracting": kwargs.get("CreateSelfExtracting", False),
            "RestoreOnly": kwargs.get("RestoreOnly", False),
            "DecoupledInstall": kwargs.get("DecoupledInstall", False),
            "CreateSeedPackage": kwargs.get("CreateSeedPackage", False),
            "ShowToUsers": kwargs.get("ShowToUsers", False),
            "donot_configure_Edge_Monitor": kwargs.get("donot_configure_Edge_Monitor", False),
            "IsInstallingFromCustomPackage": kwargs.get("IsInstallingFromCustomPackage", False),
            "installOption": kwargs.get("installOption", None),
            "two_FA_enabled": kwargs.get("enable_two_FA", False),
            "token_URL": kwargs.get("token_URL", None)
        }
        if kwargs.get("clientName"):
            client_cred = {
                "clientName": kwargs.get("clientName", None),
                "ClientHostName": kwargs.get("ClientHostName", None)}
            custom_package_json.update(client_cred)
        if kwargs.get("CommserveName"):
            cs_cred = {
                "CommserveName": kwargs.get("CommserveName")
            }
            custom_package_json.update(cs_cred)

        # To store the generated CustomPackage JSON file
        custom_input = f'{AUTOMATION_DIRECTORY}\\CustomPackageInput.json'
        with open(custom_input, 'w') as file:
            file.write(json.dumps(custom_package_json))

    def create_custom_package(self, **kwargs):
        """
                To generate a custom package

                Args:

                    **kwargs         (str)   -- To take different parameters as per testcase requirement


        """
        self.bootstrapper = BootstrapperHelper(self.feature_release, self.machine)
        self.bootstrapper.extract_bootstrapper()
        self.remote_media_path = self.bootstrapper.remote_drive + \
                                 installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH

        # To initialize options selector class
        self.options_selector = OptionsSelector(self.commcell)

        # To select drive with enough space
        self.log.info('Selecting drive on the machine based on space available')
        drive = self.options_selector.get_drive(self.machine, size=50)
        if drive is None:
            raise Exception(f"Installation cancelled, Insufficient space on machine {self.machine.machine_name}")
        self.log.info('Selected Drive: %s', drive)

        # Directory to copy the batch file, installer and interactive installation exe
        self.install_directory = kwargs.get("install_directory", self.machine.join_path(drive, 'CustomPackageLOC'))

        # To create log directory on the machine
        if not self.machine.check_directory_exists(self.log_directory):
            self.machine.create_directory(self.log_directory)
            self.log.info('Successfully created log directory in path "%s"', self.log_directory)

        # To remove install directory if exists
        if self.machine.check_directory_exists(self.install_directory):
            self.machine.remove_directory(self.install_directory)
            self.log.info('Successfully removed directory %s', self.install_directory)

        # To create install directory on the machine
        self.machine.create_directory(self.install_directory)
        self.log.info('Successfully created install directory in path "%s"', self.install_directory)

        # Interactive install exe to perform install interactively
        exe_file = INTERACTIVE_INSTALL_EXE_PATH

        # To copy the exe file
        self.copy_media_to_client(exe_file, self.install_directory)

        # To generate the user input json
        custom_package_json = kwargs.get("custom_package_json", f'{AUTOMATION_DIRECTORY}\CustomPackageInput.json')

        # To copy the user input json
        self.copy_media_to_client(custom_package_json, self.install_directory)

        batch_file = f'{self.install_directory}\install.bat'
        install_exe = f'{self.install_directory}\InteractiveInstall.exe'
        setup_exe = f'{self.remote_media_path}\Setup.exe'
        custom_package_json = f'{self.install_directory}\CustomPackageInput.json'

        # To generate the install.bat file
        command = rf'''"{install_exe}" -PATH "{setup_exe}" -PLAY "{custom_package_json}"
                      set errorCode = %ERRORLEVEL%
                      EXIT %errorCode%
                      '''
        if not self.machine.create_file(batch_file, command):
            raise Exception('Batch file creation failed')

        self.log.info('Install logs are written to InteractiveInstall.log inside %s on the client machine',
                      self.log_directory)
        self.log.info('Custom Package Creation started')
        self.execute_command(command=f'"{batch_file}"')

        # To remove install directory on the machine
        try:
            self.machine.remove_directory(self.install_directory)
            self.log.info('Successfully deleted install directory in path "%s"', self.install_directory)
        except Exception as exp:
            self.log.info("Failed to clean up the directory", exp)

    def compare_screens(self, **kwargs):
        """
            Compares the screen that are supposed to be seen by the user and the actual screens seen
            while custom package installation

            :args
                self.id (str) (mandatory): Testcase number of the executing function

                install_directory (str) (optional): To create the install directory

        """

        # To initialize options selector class
        self.options_selector = OptionsSelector(self.commcell)

        # To select drive with enough space
        self.log.info('Selecting drive on the machine based on space available')
        drive = self.options_selector.get_drive(self.machine, size=50)
        if drive is None:
            raise Exception(f"Installation cancelled, Insufficient space on machine {self.machine.machine_name}")
        self.log.info('Selected Drive: %s', drive)

        self.id = kwargs.get("self.id", "")

        self.install_directory = kwargs.get("install_directory", self.machine.join_path(drive, 'CustomPackageLOC'))
        install_xml = self.machine.read_file(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\install.xml")
        root = ET.fromstring(install_xml)
        self.log.info(install_xml[:4])
        _retcode = True
        views_to_be_seen = []
        for type_tag in root.findall('Dialogs'):
            dialog_name = type_tag.get("name").split('.')[2]
            value = type_tag.get("show")
            self.log.info(dialog_name, value)
            if value == "1":
                views_to_be_seen.append(dialog_name)
        self.log.info(views_to_be_seen)

        dialogs_seen = json.loads(self.machine.read_file(f"{REMOTE_FILE_COPY_LOC}\\Output.json"))
        print(dialogs_seen)
        views_seen_by_user = []
        for each in dialogs_seen:
            if each not in IgnoreList and each not in ScreensSeenOnlyDuringCustomPackageCreation:
                if each in ScreenNameChangeDuringInstallDict.keys():
                    views_seen_by_user.append(ScreenNameChangeDuringInstallDict[each])
                else:
                    views_seen_by_user.append(each)
        self.log.info("List of screens to be seen are :" + str(views_seen_by_user))

        for view in views_to_be_seen:
            if view not in views_seen_by_user:
                self.log.info(f"{view} screen supposed to be seen but not shown, please check")

        return _retcode
