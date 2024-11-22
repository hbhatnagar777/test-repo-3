# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing laptop operations on Commcell

LaptopHelper:
    __init__()             --  initialize instance of the LaptopHelper class

    __repr__()             --  Representation string for the instance of the LaptopHelper class.

    environment_info()     --  Logs the environment details

    initialize()           --  Initialize objects for laptop test cases

    install_laptop()       --  Module to install a laptop client.
                                This is the common module that multiple Laptop testcases will utilize for
                                a. Custom package creation and download from cloud
                                b. Custom package installation on Laptop client
                                c. Laptop client registration via authcode/user
                                d. Post registration, automatic laptop osc backups and restore validation
                                e. Laptop client validation

                                It can
                                    - Execute in MSP/Non MSP mode
                                    - Supports all options to create custom package
                                    - Can install via authcode/user
                                    - Can register via user/authcode
                                    - Can execute osc/regular backups.

                                This module will be called with various arguments for validation.

    install_and_register()  -- Laptop installation and registration

    uninstall_laptop()     --  Module to uninstall laptop client and hard delete from commcell

    generate_email_body()  --  generates email content with headers, data and returns html string.

    delete_user_from_db()  --  Deletes deleted user entry from DB

    set_inputs()           --  Creates a dictionary for test case inputs needed for a given test case for Laptops.

    set_default_plan()     --  Sets default plan and organization client group name for the organization

    set_authcode()         --  Create an authcode for the Organization

    set_blacklisted_users()
                           --  Adds / Remove blacklisted users

    create_custom_package()
                           --  Module to create custom package

    copy_client_logs()     --  Copy client logs to a network path

    cleanup()              --  Module to perform cleanups for laptop testcases

    cleanup_clients()      --  Module to perform cleanups for laptop install testcases

    generate_email_body()  -- generates email content with headers, data and returns html string.

    verify_automatic_schedule_restore()
                           --  Waits until the next automatic job starts and validates with restore

    validate_trueup()      --  Validates if trueup phases ran successfully on laptop

    create_rdp_sessions()  -- Create RDP sessions for all activation users given in test case inputs

    set_laptop_backup()    -- Sets Laptop backup status to ON/OFF for a client.

    laptop_status()        -- Logs Laptop's db status and client registry values for the given clientobject of Commcell

"""

"""Main file for performing laptop operations on user centric clients on Commcell

LaptopHelperUserCentric:
    __init__()              -- Initialize instance of the LaptopHelperUserCentric class

    install_laptop()        -- Module to install a laptop client in USER CENTRIC MODE

    install_and_register()  -- Laptop installation and registration for user centric clients

    create_pseudo_map()     -- Create user to Pseudo client dictionary

    check_pseudo_clients()  -- Checks if pseudo clients are created on the Commcell for each user in the user map

    cleanup_user_centric()  -- Module to perform cleanups for shared laptop testcases

    validate_end_user_data() -- Validates if owner of client sees only their profile data
"""

import time
from datetime import datetime
import inspect
import subprocess
import re
import os.path
import psutil

from cvpysdk.commcell import Commcell

from AutomationUtils.config import get_config
from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Install.custom_package import CustomPackage
from Install.client_installation import Installation
from Install.custom_package import CustomPackageCloudXML, CustomPackageWizardXML
from Install import installer_constants
from Server.serverhelper import ServerTestCases
from Server.Security.securityhelper import OrganizationHelper
from Server.JobManager.jobmanager_helper import JobManager
from Server.Scheduler import schedulerhelper
from Laptop.CloudLaptop.cloudlaptophelper import CloudLaptopHelper
from Laptop import laptopconstants
from Web.AdminConsole.Laptop.LaptopDetails import LaptopDetails
from Web.AdminConsole.Laptop.Laptops import Laptops
from Web.AdminConsole.AdminConsolePages.regions import Regions
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain

class LaptopHelper(object):
    """LaptopHelper helper class to perform laptop related operations"""

    def __init__(self, init_object, **kwargs):
        """Initialize instance of the LaptopHelper class.

        Args:
            init_object: (object) --  TestCase OR Commcell object

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations of
                                instance of various classes.

                                Supported :
                                    company:    (str)    -- Name of company with which to
                                                            initialize OrganizationHelper class
                                                            instance.

                                    plan:       (str)    -- Plan name
                                                            Default: Default plan name for the company
        """
        self.log = logger.get_log()
        self._init_object = init_object
        if isinstance(init_object, Commcell):
            self._commcell = init_object
            self._testcase = None
            self._testcaseid = OptionsSelector.get_custom_str()
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell
            self._testcaseid = str(self._init_object.id)

        self.utils = CommonUtils(self._testcase) if self._testcase is not None else CommonUtils(self._commcell)
        self.tc = ServerTestCases(self._testcase) if self._testcase is not None else None
        self.utility = OptionsSelector(self._commcell)
        self.entities = CVEntities(init_object)
        self.jobhelper = JobManager(commcell=self._commcell)
        self.installer = None
        self._expected_owners = None
        self.rdp_sessions_list = []
        self.metalllic_id=None
        self.reporting_db_utility=None
        self.reportingdb_commcell=None
        self.install_starttime=None
        self.metallic_table = None
        self.laptop_package_info = {} 
        self.revision = None
        self.starttime = None
        
        if 'company' in kwargs:
            self.organization = OrganizationHelper(self._commcell, kwargs['company'])
            self._company_name = kwargs['company']
            self._company_object = self.organization.company
            if 'plan' in kwargs:
                self.organization.tenant_client_group = kwargs['plan']
        else:
            self.organization = OrganizationHelper(self._commcell)
            self._company_name = None
            self._company_object = None

        laptop_config = get_config().Laptop.Install
        self.skip_client_cleanup = "yes" if laptop_config.SkipClientCleanup == "yes" else "no"
        self.skip_postosc_backup = False if laptop_config.SkipPostOscBackup == "yes" else True
        self.skip_osc_job_wait = True if laptop_config.SkipPostOscJobWait == "yes" else False
        self.copy_logs = "no" if laptop_config.SkipCopyingLogs == "yes" else "yes"
        self.forevercell_user = laptop_config.ForevercellUser
        self.forevercell_passwd = laptop_config.ForevercellPassword
        self.laptop_config = laptop_config

    def __repr__(self):
        """Representation string for the instance of the LaptopHelper class."""
        return "LaptopHelper class instance for company [%s]", self._company_name

    def environment_info(self):
        """ Logs the environment details """
        _ = self.utility.get_gxglobalparam_val('Secure Agent Install')
        self.organization.is_msp()

    def uninstall_laptop(self, laptop_details, delete_client=True):
        """ Module to uninstall a laptop client

         Args:
            laptop_details (dict)      : Laptop Details
                Supported Keys:

                        Machine_client_name (str): Laptop name

                        Machine_user_name   (str): Laptop user name

                        Machine_password    (str): Laptop password

                        Machine_host_name   (str): Laptop hostname

            delete_client (bool)       : Delete client from commcell? Default: True

        Exception:
            If failed to uninstall laptop
        """
        try:
            client_name = laptop_details.get('Machine_client_name')
            if client_name:
                uninstall_args = {
                    'client_user_name': laptop_details['Machine_user_name'],
                    'client_password': laptop_details['Machine_password'],
                    'client_host_name': laptop_details['Machine_host_name'],
                    'client_name': client_name
                }
                self.tc.log_step("Uninstalling client [{0}]".format(client_name))
                installer = Installation.create_installer_object(uninstall_args, self._commcell)
                installer.uninstall_existing_instance()
                if delete_client:
                    installer.delete_client_from_commcell()

        except Exception as excp:
            self.log.error("Failed to uninstall existing commvault instance on [{0}]".format(client_name))
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete_installer(self, tcinputs):
        if 'mac' in tcinputs['os_type'].lower():
            return 0        
        installer_path = r"C:\Program Files\Commvault\installer"
        self.log.info("Deleting files and folders under directory [{0}]".format(installer_path))
        delete_files = 'forfiles /P "' + installer_path + '" /M * /C "cmd /c if @isdir==FALSE del @file"'
        delete_directories = 'forfiles /P "' + installer_path + '" /M * /C "cmd /c if @isdir==TRUE rmdir /S /Q @file"'
        tcinputs['Machine_object'].execute_command(delete_directories)
        tcinputs['Machine_object'].execute_command(delete_files)
        
    def set_os_type(self, tcinputs):
        if 'windows' in tcinputs['os_type'].lower():
            # Placeholder for Windows 32 bit vx Windows 64 bit. Update this when adding support for Windows 32 bit. 
            pass
        elif 'mac' in tcinputs['os_type'].lower():
            # Find whether it is arm64 OR x86_64 
            processor_type = tcinputs['Machine_object'].execute_command('uname -m')
            if 'arm64' in processor_type.formatted_output:
                tcinputs['os_type'] = 'macOS_arm64'
            elif 'x86_64' in processor_type.formatted_output:
                tcinputs['os_type'] = 'macOS'                
            else:
                raise Exception("Failed to get platform type for Mac")
        else:
            raise Exception("Unsupported Platform type provided.")
        
    def install_laptop(self, tcinputs, config_kwargs, install_kwargs, custompackage_kwargs=None):
        """ Module to install a laptop client

        Args:
            tcinputs (dict)            : Testcase input answers
                metallic_ring (bool):    If set it means the installation is being attempted on a Metallic ring. 
                                         In all such cases skip DB read queries. 

            config_kwargs (dict)       : Testcase configuration arguments
            -------------------------------------------------------------

                Supported:
                ----------

                os                    (str): Operating system for which to execute the module.
                (Mandatory)

                org_enable_auth_code (bool): If true will disable/enable authcode for the organization.
                (Optional)                    Default:False

                override_auth_code (bool):   If set to true, an existing authcode for the Tenant company shall be
                (Optional)                       ignored, and a new authcode will be created.
                                              Default: True [New authcode will be created whenever org_enable_auth_code
                                                              is set to True]

                org_set_default_plan (bool): If true will set default plan(provided in test inputs) for organization.
                (Optional)                    Default:False
                


            install_kwargs (dict)      : Client installation arguments
            ----------------------------------------------------------

                Supported:
                ----------

                expected_owners (list):         Client owner validation would be done using this list.
                (Optional)                       If not set then the activation user would be assumed as the client
                                                    owner.

                install_with_authcode (bool):   If True, silent installation will be done on the client using /authcode
                (Optional)                        option.
                                                  Default: None

                execute_simcallwrapper (bool):  If true, SimCallWrapper will register the client post install. Else not
                (Optional)                        Default: False

                authcode (str):                 This is authcode which will be used in silent install
                (Optional)

                check_num_of_devices (bool):    If true validation for clients joined in the organization shall
                (Optional)                          be validated, else not.
                                                    Default: True

                client_groups (list):           If provided the laptops shall be validated to be a part of only these
                (Optional)                          client groups. Else default client groups shall be assumed in the
                                                    underlying called module.
                                                    Default: None

                delete_client (bool):           If set, client would not be hard deleted from the commcell after
                (Optional)                          uninstall.
                                                    Default: True

                new_client_name (str):          Post client registration this new client name shall be
                (Optional)                        considered for further processing.
                                                    Default: False

                register_with_new_name (bool):  If set to true the client shall be registered with a new name.
                (Optional)                          Default: False

                register_authcode (str):        If authcode is provided here, the client will be registered with this
                (Optional)                          authcode with SimcallWrapper
                                                    *Do not confuse it with authcode with install*
                                                    *This authcode is provided with SimCallWrapper*
                                                    *As per SP14 design, client should register for Server Plan*
                                                    Default: None

                client_hostname (str):          Client will be registered with this hostname
                (Optional)                      Default: None


                skip_osc    (bool):             If true:
                (Optional)                      Will not wait for the filtered automatic jobs to trigger
                                                    (Reinstall cases for laptop, where the owner does not change)

                blacklist_user (str):           Add this user to blacklist user group
                (Optional)                      Default: None


                remove_blacklisted_user (str):  Remove this user from blacklist user group
                (Optional)                      Default: None

                post_osc_backup (bool):         If set to False will skip sublicent content modification and auto
                (Optional)                          backup job execution from osc
                                                    Default: True

                nLaptopAgent (int):             Expected values (0/1)
                (Optional)                          Default: 1

                validate_user (bool):            If true:
                                                 Validates the username with which the job triggered from the Backunow
                                                 button.

                backupnow  (bool):                If true:
                                                 Validate the BackupNow button on the Edgemonitor app.

                wait_for_reinstalled_client (bool):
                (Optional)                      If set to true wait for the client to be activated post re-install.
                                                    Default: False

                sleep_before_osc (bool):
                (Optional)                      If set to true wait for the client to restore active state post
                                                    re-install.
                                                    Default: False

                activation_time_limit (int):    Activation time limit.
                                                    Default: 8

                check_client_activation (bool): Check client is activated to respective plan
                                                    Default: True
                                                    Else:
                                                        True:  If org_set_default_plan option is set to True
                                                        False: If org_set_default_plan option is set to False
                                                    Else:
                                                        False:

                cloud_laptop (bool):              Is cloud laptop (true/false) Default: False
                
                endpointurl (str):              Endpointurl for Universal installer
                
                client_activation_mode (bool):    Check client activated mode via registry setting OR check the client group 

            custompackage_kwargs (dict) : Custom package creation arguments
            ---------------------------------------------------------------

                Supported:
                ----------
                servicePack  (str):               Service pack for which to create the custom package
                                                    e.g: SP14

                SP_revision  (str):               Service Pack Revision for the custom package to create

                skip_creation (bool):             Skip package creation if skip_creation is set to true
                (Optional)                          Default: False

                authcode_flag (bool):             If set, custom package shall be created with relevant authcode for
                (Optional)                          either the tenant or from commcell level.
                                                    Default: False

                ClientGroups (str):               If provided custom package shall be created with this client group,
                                                    which means the laptop is supposed to be associated to this
                                                    client group post install
                                                    Default: None

                laptopClient (str):               "true"/"false": Configure for laptop client?
                (Optional)                          Default: true

                Custom_pkg_username (str):        Username with which the custom package is created.
                (Optional)                          Default: None

                Custom_pkg_password (str):        Password for the user with which the custom package is created.
                (Optional)                          Default: None

                requireCredentials (str):         Require credentials
                (Optional)                          Default: "true"

                backupMonitor (str):              Enable Edge monitor app process
                (Optional)                          Default: "true", Options: "false" / "true"

                SubClientPlan (str):              Plan name to be burnt with custom package
                                                    Default: ''

        Returns: None

        Exception:
            - If install is set to be done with auth_code but auth_code is not set.
            - Client not registered with commcell.
        """

        if install_kwargs.get("insert_laptop_results", True):
            self.laptop_acceptance_insert(tcinputs)
        
        if custompackage_kwargs is None:
            custompackage_kwargs = {}
        cp_authcode = None

        try:
            #-------------------------------------------------------------------------------------
            # Setup
            #-------------------------------------------------------------------------------------

            # Setup machine object and os_type
            machine_object = self.utility.get_machine_object(
                tcinputs['Machine_host_name'], tcinputs['Machine_user_name'], tcinputs['Machine_password']
            )
            tcinputs['Machine_object'] = machine_object
            self.set_os_type(tcinputs)
            

            # Log the environment info before proceeding with the Laptop installation.
            # Open RDP sessions to the client which is being installed.
            # To Do : Add SQL queries at plan/organization/commcell levels to get all existing details before install.
            if not tcinputs['metallic_ring']:
                self.environment_info()
            self.delete_installer(tcinputs)
            self.create_rdp_sessions(tcinputs)

            self.log.info("Client platform: [{0}]".format(tcinputs['os_type']))
            tcinputs['Machine_client_name'] = tcinputs.get('Machine_client_name', machine_object.machine_name)

            # Add/remove blacklisted user groups before installation.
            self.set_blacklisted_users(
                install_kwargs.get('blacklist_user'), install_kwargs.get('remove_blacklisted_user')
            )

            # Set authcode for organization
            if config_kwargs.get('org_enable_auth_code', False):
                install_authcode = self.set_authcode(config_kwargs.get('override_auth_code', True))
                cp_authcode = install_authcode

            # Set default plan and client group name for organization
            plan_name = tcinputs.get('Plan', tcinputs.get('Default_Plan'))
            if config_kwargs.get('org_set_default_plan', False):
                self.set_default_plan(plan_name)

            # If silent install has to be done through authcode.
            # Enabling authcode at org level does not mean user wants to install with authcode.
            # Covers negative scenarios where user provides wrong authcode to install and org authcode is different
            if install_kwargs.get('install_with_authcode'):
                # User provided authcode in test case
                if install_kwargs.get('authcode'):
                    install_authcode = install_kwargs.get('authcode')
                    cp_authcode = install_authcode

                # If user says install with authcode but by now authcode is not set or not provided, exception out.
                if not install_authcode or install_authcode is None:
                    raise Exception("Please provide auth code to use during install.")
            else:
                install_authcode = None

            #-------------------------------------------------------------------------------------
            # Create custom package
            #-------------------------------------------------------------------------------------

            custompackage_kwargs['choose_os'] = tcinputs['choose_os']
            custompackage_kwargs['authcode'] = cp_authcode
            custompackage_kwargs['cloud_laptop'] = install_kwargs.get('cloud_laptop')
            custompackage_kwargs['endpointurl'] = install_kwargs.get('endpointurl')
            custompackage_kwargs['os_type'] = tcinputs['os_type']
            # If local package location is provided use that rather than creating a new package.            
            if tcinputs.get('PkgLocation'):
                self.log.info("Skipping custom package creation, as custom package has been provided via config.json")
                pkg_path = self.utility.copy_files_locally(tcinputs['PkgLocation'], tcinputs['PkgUser'], tcinputs['PkgPassword'])                           
            else:
                pkg_path = self.create_custom_package(custompackage_kwargs)

            #-------------------------------------------------------------------------------------
            # Install laptop
            #-------------------------------------------------------------------------------------

            install_args = {
                'BackupNow': install_kwargs.get('backupnow', False),
                'client_user_name': tcinputs['Machine_user_name'],
                'client_password': tcinputs['Machine_password'],
                'client_host_name': tcinputs['Machine_host_name'],
                'client_hostname': install_kwargs.get('client_hostname'),
                'client_name': tcinputs['Machine_client_name'],
                'delete_client': install_kwargs.get('delete_client', True),
                'executable_name': installer_constants.PACKAGE_EXE_MAP[tcinputs['os_type']],
                'install_authcode': install_authcode,
                'install_type': install_kwargs.get('interactive_install', False),
                'install_with_authcode': install_kwargs.get('install_with_authcode'),
                'organization_object': self._company_object,
                'package_location': pkg_path,
                'registering_user': tcinputs['Activation_User'],
                'registering_user_password': tcinputs.get('Activation_Password'),
                'register_auth_code': install_kwargs.get('register_authcode'),
                'register_with_SAML': install_kwargs.get('register_with_SAML', False),
                'saml_email': tcinputs['saml_email'] if install_kwargs.get('register_with_SAML') else None,
                'takeover_client': install_kwargs.get('takeover_client', False),
                'Tenant_company': self._company_name,
                'LaunchEdgeMonitor': install_kwargs.get("LaunchEdgeMonitor", "true"),
                'check_client_activation': install_kwargs.get('check_client_activation', True),
                'endpointurl': install_kwargs.get('endpointurl', None),
                'registration_time_limit': install_kwargs.get('registration_time_limit', tcinputs['registration_time_limit'])
            }

            register_args = {
                'register_with_new_name': install_kwargs.get('register_with_new_name'),
                'new_client_name': install_kwargs.get('new_client_name'),
                'wait_for_reinstalled_client': install_kwargs.get('wait_for_reinstalled_client', False),
                'Machine_object': tcinputs['Machine_object'],
                'Plan': plan_name,
                'activation_time_limit': install_kwargs.get('activation_time_limit', 8),
                'org_set_default_plan': config_kwargs.get('org_set_default_plan', False),
                'client_activation_mode': install_kwargs.get('client_activation_mode', False)
            }

            client_obj = self.install_and_register(
                tcinputs['Machine_client_name'],
                install_kwargs.get('execute_simcallwrapper'),
                install_args,
                **register_args
            )
            tcinputs['client_object'] = client_obj
            

            #---------------------------------------------------------------------------------
            # OSC Backup and Restore
            #---------------------------------------------------------------------------------

            self.tc.log_step("""
                -  [{0}] Backup and restore phase""".format(tcinputs['Machine_host_name']))

            # After reinstalls especially in cases of Multiple companies with same client name and different
            # hostname. Even after activation the client takes some time to initialize.
            # Subclient content if modified is reverted back to original contents.
            if install_kwargs.get('sleep_before_osc', False):
                self.utility.sleep_time(120, "Waiting before osc backup and restore")

            if install_kwargs.get('cloud_laptop'):
                cloud_laptop = CloudLaptopHelper(self._testcase)
                cloud_laptop.osc_backup_and_restore(
                    client_obj,
                    validate=True,
                    postbackup=install_kwargs.get('post_osc_backup', self.skip_postosc_backup),
                    skip_osc=install_kwargs.get('skip_osc', self.skip_osc_job_wait),
					options=tcinputs['osc_options']
                )
            else:
                # Sometimes Sim registration is quick and before check client check readiness and edge monitor running
                # or not the backup job is completed. So for full backups check for all states, and for incrementals
                # since there are no checks after subclient content modification, capturing incremental backup job is
                # immediate.
                self.utils.osc_backup_and_restore(
                    client_obj,
                    validate=True,
                    postbackup=install_kwargs.get('post_osc_backup', self.skip_postosc_backup),
                    skip_osc=install_kwargs.get('skip_osc', self.skip_osc_job_wait),
                    options=tcinputs['osc_options'],
                    validate_user=install_kwargs.get('validate_user', False),
                    registering_user=tcinputs['Activation_User'],
                    current_state=['completed', 'running', 'waiting'],
                    incr_current_state=['running', 'waiting', 'pending']
                )

            #---------------------------------------------------------------------------------
            # Install validation
            #---------------------------------------------------------------------------------

            self.tc.log_step("""
                -  [{0}] Validation phase""".format(tcinputs['Machine_host_name']))
            
            # Adding this check here as we saw issues where Edge Monitor App dies after user registration and before running
            # backup. The validation for edge app running succeeds as its just before user registration.
            # SP27 Form 1590 :Summary : Update to fix EdgeMonitor Mac app crash when laptop user belongs to AD            
            if install_kwargs.get("LaunchEdgeMonitor") == "true":
                self.is_edge_monitor_running(client_obj)
            
            expected_owners = install_kwargs.get('expected_owners', [tcinputs['Activation_User']])
            blacklist_user = install_kwargs.get('blacklist_user')
            if blacklist_user and blacklist_user in expected_owners:
                expected_owners.remove(blacklist_user)
            self.organization.validate_client(client_obj,
                                              expected_owners=expected_owners,
                                              client_groups=install_kwargs.get('client_groups'),
                                              clients_joined=install_kwargs.get('check_num_of_devices', True),
                                              nLaptopAgent=install_kwargs.get('nLaptopAgent', 1))

            # Capture Laptop Package size
            if install_kwargs.get("insert_laptop_results", True):
                self.laptop_acceptance_update(tcinputs, self.laptop_package_info, 'Pass', '-')

        except Exception as excp:
            if install_kwargs.get("insert_laptop_results", True):
                self.laptop_acceptance_update(tcinputs, self.laptop_package_info, 'Fail', str(excp).replace("'", ''))
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def install_and_register(self, client, register, install_args, **registration_args):
        """ Laptop installation and registration
        Args:

            client (str):                    Client Name

            register (bool):                 Register client post install

            install_args (dict):             Installation arguments
            --------------------

                Supported
                ---------

                LaunchEdgeMonitor (str):        Enable Edge monitor app process
                (Optional)                          Default: "true", Options: "false" / "true"

                backupnow  (bool):              If true:
                                                Validate the BackupNow button on the Edgemonitor app.

                register_authcode (str):        If authcode is provided here, the client will be registered with this
                (Optional)                          authcode with SimcallWrapper
                                                    *Do not confuse it with authcode with install*
                                                    *This authcode is provided with SimCallWrapper*
                                                    *As per SP14 design, client should register for Server Plan*
                                                    Default: None

                client_host_name (str):          Client hostname
                (Mandatory)                      Default: None

                client_new_hostname (str):           Client will be registered with this hostname
                (Mandatory)                      Default: None

                client_user_name (str):          Client will be registered with this name
                (Mandatory)                      Default: None

                client_password (str):           Client password
                (Mandatory)                      Default: None

                client_name (str):               Client name
                (Mandatory)                      Default: None

                delete_client (bool):            Delete client from Commcell before install and in cleanup
                (Mandatory)                      Default: True

                executable_name (str):           Custom Package executable name
                (Mandatory)                      Default: Computed from constants

                install_authcode (str):          Installation will be done with this auth code
                (Optional)                       Default: None

                install_type (bool):             Installation Type (True/False)
                (Mandatory)                      Default: False

                organization_object (object):    Organization object
                (Mandatory)                      Default: Computed in __init__

                package_location (str):          Location where packages would be copied to the client
                (Mandatory)                      Default: None

                registering_user (str):          This user name would be used to register the client
                (Mandatory)                      Default: None

                registering_user_password (str): Registering user password
                (Mandatory)                      Default: None

                register_auth_code (str):        Registration would be done with this auth code
                (optional)                       Default: None

                register_with_SAML (bool):       SAML Registration (True/False)
                (Mandatory)                      Default: False

                saml_email (str):                SAML email
                (Optional)                       Default: None

                takeover_client (bool):          Takeover client
                (Mandatory)                      Default: False

                Tenant_company (str):            Tenant company name
                (Mandatory)                      Default: None

                check_client_activation (bool): Check client is activated to respective plan
                                                    Default: True
                                                    Else:
                                                        True:  If org_set_default_plan option is set to True
                                                        False: If org_set_default_plan option is set to False
                                                    Else:
                                                        False:

            ----------------------------------------------------------------------------------------------------------

            registration_args (dict):        Registration Arguments
            -------------------------

                Supported
                ---------

                org_set_default_plan (bool): If true will set default plan(provided in test inputs) for organization.
                (Optional)                    Default:False

                activation_time_limit (int):    Activation time limit.
                                                    Default: 8


                new_client_name (str):          Post client registration this new client name shall be
                (Optional)                        considered for further processing.
                                                    Default: False

                register_with_new_name (bool):  If set to true the client shall be registered with a new name.
                (Optional)                          Default: False

                wait_for_reinstalled_client (bool):
                (Optional)                      If set to true wait for the client to be activated post re-install.
                                                    Default: False

                Machine_object (object):        Client Machine object for Machine class
                (Optional)

                Plan  (str):                    Plan name
                (Optional)

            ----------------------------------------------------------------------------------------------------------

        Returns
            client object (obj):    Machine class object for the client

        Raises
            Exception
                - if failed to install client

        """
        try:

            self.tc.log_step("Custom package Installation for [{0}]".format(install_args['client_host_name']))

            self.tc.log_step("""
                - [{1}]     Install custom package with following parameters
                  [{0}]
            """.format(install_args, install_args['client_host_name']))
            self.installer = Installation.create_installer_object(install_args, self._commcell)
            self.installer.uninstall_existing_instance()
            self.installer.delete_client_from_commcell()
            if self._company_object:
                pre_machine_count = self._company_object.machine_count
            self.installer.install_client()
            registered_client = client

            debuglevel = 5
            for servicetype in ['ApplicationMgr', 'ccsdb', 'cvd']:
                self.log.info("Setting debug log level for [{0}] service to [{1}] ".format(servicetype, debuglevel))
                registration_args['Machine_object'].set_logging_debug_level(servicetype, level=debuglevel)
            
            if register:
                register_with_client = client
                if registration_args.get('register_with_new_name'):
                    register_with_client = registration_args['new_client_name']

                registered_client = registration_args.get('new_client_name', registered_client)
                registration_info = self.installer.execute_register_me_command(register_with_client=register_with_client,
                                                                               client_post_register=registered_client)

            self._commcell.refresh()

            # In reinstall of client (takeover) the client activation takes time even though the client is ready
            # and part of defaults Plans client group.(Because of old entry). The old client is also part of
            # company's devices. Observed if proceed without sleep, subclient content is overridden and removed
            # for reinstalled client, so osc backup triggered through manually updated content immediately after
            # registration fails.
            if not registration_args.get('new_client_name'):
                if registration_args.get('wait_for_reinstalled_client', False):
                    self.utility.sleep_time(120, "Waiting for reinstalled client to be activated.")
                elif self._company_object:
                    _ = self.organization.is_device_associated(pre_machine_count)

            # In case the client name is supposed to change post registration [ Reinstall scenarios ],
            # then set the client name.
            # Also, Wait until client ready, before creating client object.
            # Because when client object is created with commcell object, it checks for client readiness, and if
            # client is not ready exceptions out.
            # Also, post simwrapper execution or even without it, when cvd registers/activates clients, client
            # is not ready [ Client check readiness fails ] for certain interval of time.
            new_client = registration_args.get('new_client_name')
            client = new_client if new_client else client
            _ = self.utility.wait_until_client_ready(client)
            client_obj = self.utility.get_machine_object(client) if new_client else registration_args['Machine_object']

            if install_args.get("LaunchEdgeMonitor") == "true":
                self.is_edge_monitor_running(client_obj)

            # By default check if client was activated post install.
            # Otherwise honor whatever is set in check_client_activation
            # If that's not set, honor if default plan is set as part of testcase via org_set_default_plan
            if install_args.get('check_client_activation', registration_args.get('org_set_default_plan', False)):
                if not install_args.get('check_client_activation', False):
                    _ = self.organization.is_client_activated(
                        client,
                        registration_args['Plan'],
                        time_limit=registration_args.get('activation_time_limit', 8)
                    )
                else:
                    _ = self.utility.is_regkey_set(registration_args['Machine_object'], "FileSystemAgent", "ActivatedMode", 2, 2, True, 1)                

            return client_obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        
    def create_rdp_sessions(self, tcinputs, machine_object=None):
        """
            Create RDP sessions for all activation users given in test case inputs

        Args:

            machine_object   (obj):    Machine object for the machine for which the RDP session has to be opened

            tcinputs (dict):   TestCase dictionary containing Activation Users and Passwords

        Raises
            Exception:
                - If failed to create RDP Sessions.

        """
        try:
            if not machine_object:
                machine_object = tcinputs['Machine_object']

            for key, _ in tcinputs.items():
                if 'Activation_User' not in key or tcinputs.get(key) is None:
                    continue
                user = tcinputs[key]
                passkey = "Activation_Password"
                user_index = key.split('Activation_User')[1]
                if user_index:
                    passkey += str(user_index)
                password = tcinputs[passkey]
                if user in tcinputs.get('Skip_RDP_Users', []):
                    self.log.info("Skip creating RDP session for user [{0}]".format(user))
                    continue

                rdp_handler = self.utility.start_rdp_session(machine_object, user, password)
                if isinstance(rdp_handler, subprocess.Popen):
                    self.rdp_sessions_list.append(rdp_handler)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete_user_from_db(self, user):
        """
            Deletes deleted user entry from DB

        Args:

            user   (str):    User name

        Raises
            Exception:
                - If failed to delete user

        """
        try:

            user_to_search = user + '(Deleted'
            _query = "select id from umusers where login like '%{}%'".format(user_to_search)
            userid = self.utility.exec_commserv_query(_query)
            if userid[0][0]:
                self.utility.update_commserve_db("delete from umusers where id="+str(userid[0][0]))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    @staticmethod
    def set_inputs(testcase, organization, common_inputs=None, platform_inputs=None, os_type=None):
        """
            Creates a dictionary for test case inputs needed for a given test case for Laptops.
            Reads the config defined constants and gets all the required inputs and creates key value pairs for
            these inputs and returns back the dictionary of inputs to caller.

        Args:

            testcase (obj):                            Testcase object

            organization (str):                        Name of the organization for which to fetch inputs from constants
                                                        Defined as of writing are :
                                                        Company1, Company2, Commcell, CustomDomainCompany

            common_inputs (list):                      This is list of common inputs needed from Organization constants

            platform_inputs (list):                    This is list of platform specific inputs needed from
                                                        Organization.'Windows/Mac' constants

        Returns:

            inputs (dict):    Key value dictionary for the required inputs for testcase fetched from constants

        Raises
            Exception:
                - If failed to get the inputs

        """
        inputs = {}
        try:
            if os_type is not None and os_type != 'None':
                platform = os_type
            else:
                platform = testcase.tsName.lower().split('_')[1].capitalize()
            laptop_config = get_config().Laptop.Install
            org_data = laptop_config._asdict()[organization]._asdict()
            os_map = org_data[platform]._asdict() if platform in org_data else {}

            if platform.lower() == 'windows':
                inputs['os_type'] = 'Windows'
                inputs['osc_options'] = None
                inputs['choose_os'] = 'WinX64'
            elif 'mac' in platform.lower():
                inputs['os_type'] = 'Mac'
                inputs['osc_options'] = '-testuser root -testgroup admin'
                inputs['choose_os'] = 'Mac'

            machine_config = laptop_config._asdict()[platform.lower()]._asdict()
            inputs["Machine_host_name"] = os_map.get("Machine_host_name", machine_config.get("Machine_host_name"))
            inputs["Machine_client_name"] = os_map.get("Machine_client_name", machine_config.get("Machine_client_name"))
            inputs["Machine_user_name"] = os_map.get("Machine_user_name", machine_config.get("Machine_user_name"))
            inputs["Machine_password"] = os_map.get("Machine_password", machine_config.get("Machine_password"))
            inputs["Machine_fqdn_name"] = os_map.get("Machine_fqdn_name", machine_config.get("Machine_fqdn_name"))

            inputs["Activation_User"] = org_data.get("Activation_User", machine_config.get("Activation_User"))
            inputs["Activation_Password"] = org_data.get("Activation_Password", machine_config.get("Activation_Password"))
            inputs["Default_Plan"] = org_data.get("Default_Plan", machine_config.get("Default_Plan"))
            inputs["Tenant_company"] = org_data.get("Tenant_company", machine_config.get("Tenant_company"))
            inputs["Tenant_admin"] = org_data.get("Tenant_admin", machine_config.get("Tenant_admin"))
            inputs["Tenant_password"] = org_data.get("Tenant_password", machine_config.get("Tenant_password"))
            inputs["metallic_ring"] = True if 'MetallicPackageCreation' in organization else False

            if common_inputs:
                for key in common_inputs:
                    inputs[key] = org_data[key]

            if platform_inputs and os_map:
                for key in platform_inputs:
                    inputs[key] = os_map[key]
            inputs['registration_time_limit'] = laptop_config.registration_time_limit
            inputs['report_db_server'] = laptop_config.report_db_server
            inputs['report_user'] = laptop_config.report_user
            inputs['report_password'] = laptop_config.report_password
            inputs['report_db'] = laptop_config.report_db
            inputs['report_table'] = laptop_config.report_table
            
            return inputs

        except KeyError as _:
            raise Exception("Failed to fetch inputs from config.json for {0} and {1}".format(organization, platform))
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def set_authcode(self, override=True):
        """ Create an authcode for the Organization

            Args:

                override (bool):    Recreate authcode for organization if it's already created

            Returns:

                authcode (str):     Auth code for the Organization

            Exception:

                - If failed to get the authcode for the oprganization
        """
        authcode = self._company_object.auth_code
        if (override) or (authcode is None):
            self.tc.log_step("""
                - Enable and get new authcode for Organization
            """)
            _ = self.organization.modify_auth_code('disable')
            authcode = self.organization.modify_auth_code('enable')
        else:
            self.log.info("Using existing authcode [{0}] for Organization".format(authcode))

        return authcode

    def set_default_plan(self, plan_name):
        """ Sets default plan and organization client group name for the organization

            Args:
                Plan name (str)   :  Plan name

        """
        self.tc.log_step("""
            - Set default plan for Tenant Company, and validate that the default plan can be set.
        """)
        self.organization.default_plan = plan_name
        self.organization.tenant_client_group = plan_name

    def set_blacklisted_users(self, user_to_blacklist=None, approve_user=None):
        """ Adds / Remove blacklisted users

            Args:

                user_to_blacklist (str):    User who needs to be blacklisted

                approve_user (str):         User who needs to be removed from blacklisted group

        """
        if user_to_blacklist or approve_user:
            self.organization.create_blacklisted_group()
        else:
            self.log.info("No user provided to blacklist or approve.")
            return

        if user_to_blacklist:
            self.organization.add_user_to_blacklisted_group(user_to_blacklist)

        if approve_user:
            self.organization.remove_user_from_blacklisted_group(approve_user)

    def set_laptop_backup(self, client_name, toggle):
        """ Sets Laptop backup status to ON/OFF for a client.

            Args:
                client_name   (str):       Client name

                toggle       (str):        Enable laptop backup on client
                                            Accepted values:
                                                ON/OFF

                Returns:
                    None

                Raises:
                    Exception:
                        - If module fail to execute at any step
        """
        try:
            if toggle not in ['ON', 'OFF']:
                raise Exception ("toggle option can only take in values ON/OFF")

            # Set laptop backup status on the client.
            qscript = "-sn enableLaptopBackup -si '{0}' -si '{1}'".format(toggle, client_name)
            self.log.info("Setting laptop backup status [{0}] on client [{1}]".format(toggle, client_name))
            self.log.info("Executing qoperation execscript {0}".format(qscript))
            response = self._commcell._qoperation_execscript(qscript)
            self.log.info("qscript response: [{0}]".format(str(response)))
            if not bool(re.search('completed', str(response))):
                raise Exception("Failed to set laptop backup status [{0}] on client [{1}]".format(toggle, client_name))

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def laptop_status(
            self, machine_obj, client_obj, client_status=4096, workstation=1, nlaptopagent=1, activated_mode=1):
        """ Logs Laptop's db status for the given clientobject of Commcell
            Registries on the client

            Args:
                machine_obj  (obj):       Machine class object of the client

                client_obj   (obj):       Client object for the given Commcell

                client_status (int):      DB status of the client in DB

                workstation (int):        Personal Workstation attrval in client prop

                nlaptopagent (int):       Clients FileSystemAgent>nLaptopAgent in registry post install

                activated_mode (int):     Clients FileSystemAgent>ActivateMode in registry post install

                Returns:
                    None

                Raises:
                    Exception:
                        - If module fail to execute at any step
        """
        try:
            client_name = client_obj.client_name
            client_id = client_obj.client_id

            # Check status in app_client
            query = "select status from app_client where id = {0}".format(client_id)
            resultset = self.utility.exec_commserv_query(query)
            laptop_status = resultset[0][0]
            self.log.info("Laptop [{0}] status in app_client [{1}]".format(client_name, laptop_status))
            assert int(client_status) == int(laptop_status), "DB validation failed."

            # Check workstation status in app_clientprop
            query = """select attrval from app_clientprop
                        where attrname = 'Personal Workstation' and componentNameId = {0}""".format(client_id)
            resultset = self.utility.exec_commserv_query(query)
            workstation_status = resultset[0][0]
            self.log.info(
                "Laptop [{0}] workstation status in app_clientprop [{1}]".format(client_name, workstation_status)
            )
            assert int(workstation_status) == int(workstation), "DB validation failed."

            _ = self.utility.check_reg_key(machine_obj, 'FileSystemAgent', 'nLaptopAgent', nlaptopagent)
            _ = self.utility.check_reg_key(machine_obj, 'FileSystemAgent', 'ActivatedMode', activated_mode)

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def create_custom_package(self, custompackage_kwargs):
        """ Module to create custom package

         Args:

            custompackage_kwargs (dict) : Custom package arguments and values clubbed in a dictionary
            ---------------------------------------------------------------

                Supported:
                ----------
                servicePack  (str):               Service pack for which to create the custom package
                                                    e.g: SP14

                SP_revision  (str):               Service Pack Revision for the custom package to create

                skip_creation (bool):             Skip package creation if skip_creation is set to true
                (Optional)                          Default: False

                authcode_flag (bool):             If set, custom package shall be created with relevant authcode for
                (Optional)                          either the tenant or from commcell level.
                                                    Default: False

                ClientGroups (str):               If provided custom package shall be created with this client group,
                                                    which means the laptop is supposed to be associated to this
                                                    client group post install
                                                    Default: None

                laptopClient (str):               "true"/"false": Configure for laptop client?
                (Optional)                          Default: true

                Custom_pkg_username (str):        Username with which the custom package is created.
                (Optional)                          Default: None

                Custom_pkg_password (str):        Password for the user with which the custom package is created.
                (Optional)                          Default: None

                requireCredentials (str):         Require credentials
                (Optional)                          Default: "true"

                backupMonitor (str):              Enable Edge monitor app process
                (Optional)                          Default: "true", Options: "false" / "true"

                authcode (str):                   Authcode (If Applicable)

                choose_os (str):                  Choose operating system to execute on. (This is essentially used in 
                                                    custom package creation               
                
                os_type (str):                    This is used in identifying the platform+architecture combination 
                                                    Windows x64 and x86_64
                                                    macOS x86_64 and macOS_arm64

                cloud_laptop (bool):              Is cloud laptop (true/false) Default: False

                SubClientPlan (str):              Plan name to be burnt with custom package

                endpointurl (str):                Endpoint URL for Universal installer
                 
        Returns:
            Package Path (str):     Location where Custom packages are downloaded
        """
        try:
            custom_package = CustomPackage()
            if custompackage_kwargs['choose_os'] == 'Mac':
                platform_list = [custompackage_kwargs['os_type']]
            else:
                platform_list = ['Windows-x64']

            authcode = custompackage_kwargs['authcode'] if custompackage_kwargs.get('authcode_flag', False) else None
            cargs = {
                'commcell_object': self._commcell,
                'proxy_list': custom_package.proxy_list(self._commcell),
                'servicePack': custompackage_kwargs.get('servicePack'),
                'SP_revision': custompackage_kwargs.get('SP_revision', self.sp_revision),
                'authcode': authcode,
                'WindowsSubClientPolicy': custompackage_kwargs.get('WindowsSubClientPolicy', ""),
                'MacSubClientPolicy': custompackage_kwargs.get('MacSubClientPolicy', ""),
                'SubClientPlan': custompackage_kwargs.get('SubClientPlan', ''),
                'ClientGroups': custompackage_kwargs.get('ClientGroups', []),
                'Custom_pkg_username': custompackage_kwargs.get('Custom_pkg_username'),
                'Custom_pkg_password': custompackage_kwargs.get('Custom_pkg_password'),
                'laptopClient': custompackage_kwargs.get('laptopClient', "true"),
                'requireCredentials': custompackage_kwargs.get('requireCredentials', "true"),
                'backupMonitor': custompackage_kwargs.get('backupMonitor', "true"),
                'hideApps': custompackage_kwargs.get('hideApps', "false"),
                'chooseOS': custompackage_kwargs['choose_os'],
                'cloud_laptop': custompackage_kwargs.get('cloud_laptop', False),
                'endpointurl': custompackage_kwargs.get('endpointurl', '')
            }
            pkg_path = custom_package.get_pkg_path(cargs)
            
            laptop_config = get_config().Laptop.Install
            force = laptop_config.ForceCreatePackage
                
            if not custompackage_kwargs.get('skip_creation', False):
                self.tc.log_step("""- Create custom package phase""")
                input_xml = CustomPackageWizardXML(cargs).generate_xml()
                
                package_info = custom_package.check_packages(pkg_path, platform_list)
                self.laptop_package_info = package_info
                
                if force == "yes" or not package_info:
                    # Initialize cloud object only when we need to create custom package
                    custom_package.cloud_commcell = (self.forevercell_user, self.forevercell_passwd)
                    _ = custom_package.create(input_xml)
                    package_info = custom_package.download(download_dir=pkg_path, platform_list=platform_list)
                    
            self.laptop_package_info = package_info
            self.log.info("Package info {0}".format(package_info))
            
            return pkg_path

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_edge_monitor_running(self, machine):
        """ Method to check if CvEdgeMonitor process is running on the client

            machine (object)    : Machine object

            Raises:
                Exception:
                    If CvEdgeMonitor process is not running.

        """
        if machine.os_info.lower() == "windows":
            process_name = "CvEdgeMonitor"
        else:
            process_name = "EdgeMonitor"
        if not machine.is_process_running(process_name, 300, 1):
            self.log.exception("EdgeMonitor validation failed.")
            raise Exception("Edge Monitor App was not launched on [{0}]".format(machine.machine_name))
        else:
            self.log.info("Edge Monitor App launched successfully on [{0}]".format(machine.machine_name))

    def copy_client_logs(self, machine_object, source_dir=None, network_path=None, username=None, password=None):
        """ Copy client logs to a network path

         Args:
                machine_object  (object):                       Client object for Machine class

                network_path (str):                             Network path where logs would be copied over

                username (str):                                 Network path's user name

                password (str):                                 Network path password

        Returns: bool
            False: If failed to copy logs.

        Raises: Exception:
            - If exceptions out while performing any operation.

        """
        try:
            os_sep = machine_object.os_sep
            os_info = machine_object.os_info
            client = machine_object.machine_name

            if network_path is None:
                laptop_config = get_config().Laptop.Install
                network_path = laptop_config.NetworkPath
                username = laptop_config.NetworkUser
                password = laptop_config.NetworkPassword
                if not network_path or network_path is None:
                    self.log.error("NetworkPath is not defined in the input template config. Skip copying client logs")

            # Create destination location first.
            drive = machine_object.mount_network_path(network_path, username, password)
            dest_path = os_sep.join([drive + ":", self._testcaseid, os_info, OptionsSelector.get_custom_str()])
            self.utility.create_directory(machine_object, dest_path)

            if source_dir is None:
                # Get client install path
                if machine_object.os_info == 'WINDOWS':
                    install_dir = self.utility.check_reg_key(machine_object, 'Base', 'dGALAXYHOME')
                    if not install_dir:
                        self.log.error("Failed to get installation directory for client [{0}]".format(client))
                        self.log.error("Failed to copy logs for client [{0}]".format(client))
                        return False
                    source_dir = os_sep.join([install_dir, "Log Files"])
                else:
                    source_dir = laptopconstants.UNIX_INSTALL_DIR

            self.log.info("Copying logs from client [{0}]. From [{1}] to [{2}]".format(client, source_dir, dest_path))
            machine_object.copy_folder(source_dir, dest_path)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            machine_object.unmount_drive(drive)

    def cleanup_rdp_sessions(self):
        for rdp_handler in self.rdp_sessions_list:
            try:
                self.log.info("Closing RDP session with pid [{0}]".format(rdp_handler.pid))
                for child in psutil.Process(rdp_handler.pid).children(recursive=True):
                    self.log.info("Killing RDP child pid [{0}] for process [{1}]".format(child.pid, child.name))
                    child.kill()
                rdp_handler.kill()
            except Exception as excp:
                if "No such process" in str(excp) or "NoSuchProcess no process found with pid" in str(excp):
                    self.log.info("RDP session not found.")

    def cleanup(self, tcinputs, delete_client=True):
        """ Module to perform cleanups for laptop testcases

         Args:
            tcinputs (dict)            : Testcase input answers

            delete_client (bool)       : Hard delete client from commcell
                                            Default: True
        """
        self.log.info("***Starting laptop cleanup***")
        self.cleanup_rdp_sessions()
        self.utils.cleanup()
        self.organization.cleanup()
        self.cleanup_clients(tcinputs, delete_client)
        self.entities.cleanup()

    def cleanup_clients(self, tcinputs, delete_client=True):
        """ Module to perform cleanups for laptop install testcases

         Args:
            tcinputs (dict)            : Testcase input answers

            delete_client (bool)       : Hard delete client from commcell
                                            Default: True

        Returns:
            True:     If client cleanup is set to be skipped

        Raises:
            Exception: If failed to cleanup clients at any step.
        """
        try:
            # Copy client logs to network location.
            if tcinputs['Machine_object'].os_info.lower() == "windows" and self.copy_logs == "yes":
                self.copy_client_logs(tcinputs['Machine_object'])
            else:
                self.log.info("Skip copying client logs.")

            if self.skip_client_cleanup == "yes":
                self.log.info("Client cleanup skipped as config parameter is set to skip client cleanup")
                return True

            self.log.info("***Cleaning up laptop devices***")
            self.uninstall_laptop(tcinputs, delete_client)

            self._commcell.refresh()

            if delete_client:
                # Hard delete clients from commcell
                client_name = tcinputs.get('Machine_client_name')
                if client_name:
                    for client in [client_name + laptopconstants.REINSTALL_NAME,
                                   client_name + laptopconstants.REINSTALLED_CLIENT_STR,
                                   client_name + laptopconstants.REPURPOSED_CLIENT]:
                        if self._commcell.clients.has_client(client):
                            self.utility.delete_client(client)

            # This Key exists for only usercentric laptop automation. delete all the Pseudo clients if present.
            for each_user in tcinputs.get('user_map', []):
                client = tcinputs['user_map'][each_user]['pseudo_client']
                if self._commcell.clients.has_client(client):
                    self.utility.delete_client(client)

        except Exception as excp:
            self.log.error("""Cleanup failed for laptop test cases.""")
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def generate_email_body(self, data):
        '''
        generates email content with headers, data and returns html string.

        @args:

        data (dictionary)     : body of the mail in dictionary format

        returns

        items(list)    : list of items as html in email body

        '''
        style = ''' <html>
        <style type="text/css">
        table {
         border-collapse: collapse;
          width: 40%;
          text-align: middle;
          }
        table td, th {
          border: 1px solid blue;
          padding: 10px;

          }

        #summary{
            border-color: #348dd4;
        }
        #summary_head{
            color: #fff;
            text-transform: uppercase;
        }
        #summary th{
            background-color: #84E8F5;

        }
        #summary tr{
            background-color: #F7D0C6;

        }
        #summary tr:nth-child(even){
            background: #C3F5C4;

        }
        #summary tr:nth-child(odd){
            background: #D8E6FA;

        }
        header h2 {
            margin: 20px;
        }

        </style>

        <header>
            <h2>Laptop CPU Performance</h2>
        </header>
        <body>
        '''
        items = []
        headers = ['OS', 'PROCESS', 'SERIVICEPACK', 'CPU']
        items.append('<p>The below Table gives us the average cpu performance for scancheck,FileScan,clBackup process.</p>')
        items.append('%s<table id="summary">' % style + '<tr>')
        for tag in headers:
            items.append('<th><b>%s</th>' % tag)
        items.append('</tr>')

        sp_list = data.SERVICEPACK.unique()
        os_list = data.OS.unique()
        process_list = data.PROCESS.unique()

        for os in os_list:
            items.append('<tr>')
            items.append('<th rowspan="6"><strong><font color="black">%s</td>' % str(os))
            for process in process_list:
                items.append('<th rowspan="2"><strong><font color="black">%s</td>' % str(process))
                val = {}
                sp_max = None
                for sp in sp_list:
                    val[sp] = data.query('PROCESS=="' + process + '" and SERVICEPACK=="' + sp + '" and OS=="' + os + '"')['CPU'].mean()
                sp_max = max([[val[key], key] for key in val])[1]
                for sp in sp_list:
                    items.append('<th><b>%s</th>' % sp)
                    if sp == sp_max:
                        items.append('<td><strong><font color="red">%s</td>' % val[sp])
                        items.append('</tr>')
                    else:
                        items.append('<td><strong><font color="Green">%s</td>' % val[sp])
                        items.append('</tr>')

        items.append('</table>')

        items.append('<p>The below graphs gives us the cpu performance for scancheck,FileScan,clBackup process.</p>')
        items.append('<h2 style="color: #2e6c80;"><img src="c:\cpu_prescan.png" alt="Graph for cpu performance"'
                     'width="500" height="500" /></h2>')
        items.append('<h2 style="color: #2e6c80;"><img src="c:\cpu_scan.png" alt="Graph for cpu performance"'
                     'width="500" height="500" /></h2>')
        items.append('<h2 style="color: #2e6c80;"><img src="c:\cpu_clbackup.png" alt="Graph for cpu performance"'
                     'width="500" height="500" /></h2>')

        items.append("</body></html>")
        self.log.info('\n'.join(items))
        return '\n'.join(items)

    def verify_automatic_schedule_restore(self, path, tmp_path, subclient_obj, machine, client_name, sch_obj, validate,
                                          cleanup, previous_job, newcontent=False, add_data=True, subclient_content=None):
        '''
            Waits until next automatic schedule job starts/completes  and validates by running restore
            Args:
                path (str)            : source path where data to be generated and validate
                tmp_path (str)        : tmp_path where restore to be done
                subclient_obj (obj)   : Sub client object
                machine (obj)         : machine object on which validation is done
                client_name           : client name
                sch_obj (obj)         : schedule object on which to be validate the job
                validate (boolean)    : restore to be validated or not
                cleanup (boolean)     : cleanup of restored folder to be done or not
                previous_job (int)    : previous job for the schedule
                add_data (Boolean)    : to generate test data or not
                subclient_content (list): list of sub client content to be updated

            Returns: the latest automatic schedule backup job ran
        '''

        if add_data:
            if machine.os_info in 'Unix':
                machine.generate_test_data(path, hlinks=False, slinks=False, sparse=False,
                                           options="-testuser root -testgroup wheel")
            else:
                machine.generate_test_data(path, hlinks=False, slinks=False, sparse=False)
        if subclient_content:
            subclient_obj.content = subclient_content
        _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self._commcell)
        self.log.info('Verify whether job triggered due to content change or not')
        previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job, newcontent)

        if not previous_job:
            raise Exception(" automatic job didnt trigger in scheduled time")
        self.log.info("Run a restore of the incremental backup data and verify correct data is restored.")
        _ = CommonUtils(self).subclient_restore_from_job(
            data_path=path,
            tmp_path=tmp_path,
            job=previous_job,
            cleanup=cleanup,
            subclient=subclient_obj,
            client=client_name,
            validate=validate)

        return previous_job

    def validate_trueup(self, machine, client, subclient, phase, job):
        '''Validates trueup phases on laptop
        Args:
                machine (obj)    : Machine object on which trueup has to be validated
                client (obj)     : Client object on which trueup has to be validated
                subclient (obj)  : Subclient object on which trueup has ot be validated
                phase (int)      : Phase on which trueup has to be validated
                job (obj)        : job object on which trueup has to be validated

            Returns: True/False'''

        trueup_state_file_path = None
        self.log.info("Validate treup phases started")
        try:
            job_result = r"CV_JobResults\iDataAgent\FileSystemAgent" if machine.os_info == "WINDOWS" else ""
            trueup_state_file_path = machine.join_path(
                client.job_results_directory,
                job_result,
                "2",
                subclient.subclient_id,
                "TrueupState.cvf"
                )

            self.log.info("Get TrueUpDCReadyForScan from Trueupstate file")
            contents = machine.read_file(trueup_state_file_path)
            dcready = contents.split("TrueUpDCReadyForScan=")[1].split(" ")[0]

            if phase == 1:
                if '"false"' in dcready:
                    self.log("TrueupDCcreadyforscan is False in phase1, check Logs")
                    raise Exception("TrueupDCcreadyforscan is False in phase1, check Logs")
                elif '"true"' in dcready:
                    self.log.info("TrueupDCcreadyforscan is correctly set to True")
                    return True
                else:
                    raise Exception("TrueupDCcreadyforscan in Phase1 is set inappropriately , check Logs")
            elif phase == 2:
                if '"true"' in dcready:
                    self.log("TrueupDCcreadyforscan is True in phase2, check Logs")
                    raise Exception("TrueupDCcreadyforscan is True in phase2, check Logs")
                elif '"false"' in dcready:
                    self.log.info("TrueupDCcreadyforscan is correctly set to False in Phase2")
                else:
                    raise Exception("TrueupDCcreadyforscan in Phase2 is set inappropriately , check Logs")

                trueup_ran_query = ("select count(*) from JMMisc WITH (NOLOCK) where jobid"
                                    " = {0} and itemType = {1}".format(job.job_id, "38"))
                trueup_ran = self.utility.exec_commserv_query(trueup_ran_query)
                if trueup_ran[0][0] == '1':
                    return True
                return False
        except Exception as err:
            self.log.error(err)
            raise Exception("Failed to validate Trueup")
        
    def elasticplan_region_validation(self, admin_console, tcinputs, config_kwargs):
        '''Validates laptop elastic plan association to elastic plan and storage rule
        based on its region
        Args:
                admin_console(obj)    : Admin Console object for operations on adminconsole
                tcinputs (dict)       : Test case input answers containing parameters for test case
                config_kwargs (dict)  : Test case configuration arguments
        '''
        self.log.info("Validating Elastic Plan Client")
        try:
            self.validate_laptop_elasticplan_association(admin_console, tcinputs, config_kwargs)
            self.validate_postactivation_laptop_region_association(admin_console, tcinputs)
            self.validate_backup_and_restore(admin_console, tcinputs)
            self.region_change_validation(admin_console, tcinputs)
            self.validate_browse_and_restore(admin_console, tcinputs)
        except Exception as err:
            self.log.error(err)
        else:
            self.log.info("Elastic Plan Association Checked Successfully")

    def validate_laptop_elasticplan_association(self, admin_console, tcinputs, config_kwargs):
        """ This will validate that an installed laptop is associated with the elastic plan, that 
        is the default plan for the company, config.json has the default plan, installed laptop
        has an associated plan, verifies that they are the same 
        Args:
                admin_console(obj)    : Admin Console object for operations on adminconsole
                tcinputs (dict)       : Test case input answers containing parameters for test case
                config_kwargs (dict)  : Test case configuration arguments
        """
        self.log.info("Checking association of installed laptop with Companny's default plan")
        if config_kwargs.get('org_set_default_plan'):
            default_company_plan = tcinputs.get('Default_Plan')      
        else:
            self.log.error(f"Company {tcinputs.get('Tenant_company')} has no default plan set")
            self.log.info(f"Exiting validate_laptop_elasticplan_association() now")
            return

        client_name = tcinputs.get('Machine_client_name')       
        try:
            admin_console.navigator.navigate_to_devices()
            installed_laptop_details = LaptopDetails(admin_page=admin_console, commcell=self._commcell).\
                laptop_region_plan(client_name.lower())
                    
        except Exception as err:
            self.log.error(err)
            raise Exception("Failed to extract laptop info")
        else:
            laptop_associated_plan = installed_laptop_details['Laptop Plan']
            if default_company_plan == laptop_associated_plan:
                self.log.info("Validated: Installed Laptop is associated with the Company's default plan")
            else:
                self.log.info("Installed Laptop is not associated with the Company's default plan")

    def validate_postactivation_laptop_region_association(self, admin_console, tcinputs):
        ''' Validates laptop region and plan backup destinations are assigned correctly in the 
        Regions page
        Args:
                admin_console(obj)    : Admin Console object for operations on adminconsole
                tcinputs (dict)       : Test case input answers containing parameters for test case
        '''
        self.log.info("Checking if Laptop Plan is attached to all the regions correctly or not")
        
        client_name = tcinputs.get('Machine_client_name')  
        laptop_region = None
        laptop_region1 = None
        lap_help_obj = LaptopHelper(self._commcell, company=tcinputs['Tenant_company'])
        try:
            lap_det_obj = LaptopDetails(admin_console, lap_help_obj._commcell)
            admin_console.navigator.navigate_to_devices()
            installed_laptop_details = lap_det_obj.laptop_region_plan(client_name.lower())
            
        except Exception as err:
            self.log.error(err)
            raise Exception("Failed to extract laptop info")
        else:
            laptop_region = installed_laptop_details.get('Laptop Region').split('\n')[0]
            laptop_region1 = installed_laptop_details.get('Laptop Region')
            
        if laptop_region is not None:       
            admin_console.navigator.navigate_to_regions()
            if '(' in laptop_region:
                laptop_region = laptop_region.split('(')[1][:-2]
            list_of_laptops = Regions(admin_console).get_associated_servers_plans(laptop_region, server=True)
            self.log.info(f"Column Names: {list_of_laptops}")
            
            if client_name.lower() in list_of_laptops:
                self.log.info(f"Validated: Laptop {client_name} is activated to the correct region, {laptop_region}")
            else:
                raise Exception("Laptop is not activated to the correct region")

        laptop_plan_name = installed_laptop_details['Laptop Plan']
        new_region_name = tcinputs.get('Region')
        self.log.info(new_region_name)
        for des in new_region_name:
            admin_console.navigator.navigate_to_regions()
            list_of_plans = Regions(admin_console).get_associated_servers_plans(des, plan=True)
            self.log.info(f"Column Names: {list_of_plans}")
            if laptop_plan_name not in list_of_plans:
                self.log.info(f"Region {des} does not have the plan, {laptop_plan_name}")
            else:
                self.log.info(f"Validated: Laptop Plan {laptop_plan_name} is correctly attached to the region {des}")
        self.log.info(f"Verifying correct storage policy is associated to the default subclient of client: {client_name.lower()}")
        client_obj = self._commcell.clients.get(client_name)
        agent_obj = client_obj.agents.get('File System')
        backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
        subclient_obj = backupset_obj.subclients.get('default')
        actual_storage_policy_name = subclient_obj.storage_policy
        self.log.info(f"Subclient is associated to the Storage Policy: {actual_storage_policy_name}")
        required_storage_policy_name = laptop_plan_name + '-' + laptop_region1
        self.log.info(f"Checking storage policy according to region: {required_storage_policy_name}")
        if actual_storage_policy_name.lower().replace(' ', '') == required_storage_policy_name.lower().replace(' ', ''):
            self.log.info("Subclient is associated to the correct storage policy, according to region")
        else:
            raise Exception("Subclient is not associated to the correct storage policy")

    def validate_backup_and_restore(self, admin_console, tcinputs):
        ''' Validates laptop backup and restore are properly functioning
        Args:
                admin_console(obj)    : Admin Console object for operations on adminconsole
                tcinputs (dict)       : Test case input answers containing parameters for test case
        '''
        lap_help_obj = LaptopHelper(self._commcell, company=tcinputs['Tenant_company'])
        self.log.info("Testing Backup and Restore")
        self.log.info("Performing Subclient Backup now")
        laptop_helper_obj = LaptopMain(admin_page=admin_console, commcell=lap_help_obj._commcell)
        laptop_helper_obj.client_name = tcinputs.get('Machine_client_name').lower()
        backup_job = laptop_helper_obj.perform_backup_now()
        self.log.info("Performing Subclient Restore now")
        Laptops(admin_console).restore_from_details_page(laptop_helper_obj.client_name, source_data_path="C:")
        self.log.info("Validated backup and restore jobs")
        self.log.info("Exiting validate_backup_and_restore() now")

    def region_change_validation(self, admin_console, tcinputs):
        ''' Validates laptop region change and subsequent checks are working
        Args:
                admin_console(obj)    : Admin Console object for operations on adminconsole
                tcinputs (dict)       : Test case input answers containing parameters for test case
        '''
        self.log.info("Checking region changes and all other activities")
        client_name = tcinputs.get('Machine_client_name')  
        lap_help_obj = LaptopHelper(self._commcell, company=tcinputs['Tenant_company'])
        lap_det_obj = LaptopDetails(admin_console, lap_help_obj._commcell)
        try:
            admin_console.navigator.navigate_to_devices()
            installed_laptop_details = lap_det_obj.laptop_region_plan(client_name.lower())
            
        except Exception as err:
            self.log.error(err)
            raise Exception("Failed to extract laptop info")
        else:
            laptop_region = installed_laptop_details.get('Laptop Region').split('\n')[0]
        region_name = tcinputs.get('Region')
        self.log.info(region_name)

        self.log.info(f"Laptop Region currently: {laptop_region}")
        for des in region_name:
            if des != laptop_region:
                lap_det_obj.change_laptop_region(client_name.lower(), des)
                break
        self.utility.sleep_time(5)
        client_name = client_name.lower()
        admin_console.navigator.navigate_to_devices()
        Laptops(admin_console).deactivate_laptop(client_name)
        Laptops(admin_console).activate_laptop_byuser(client_name)
        self.log.info("Region changed: Checking for correct region association now")
        self.validate_postactivation_laptop_region_association(admin_console, tcinputs)
        self.log.info("Region changed: Checking for successful backup and restore now")
        self.validate_backup_and_restore(admin_console, tcinputs)
        self.log.info("Validated: Checked Region Change for a Laptop Client, Exiting now")
        
    def validate_browse_and_restore(self, admin_console, tcinputs):
        ''' Validates browse and restore works for the different storage copies as a result
        of multiple storage rules
        Args:
                admin_console(obj)    : Admin Console object for operations on adminconsole
                tcinputs (dict)       : Test case input answers containing parameters for test case
        '''
        self.log.info("Checking Browse and Restore from all Backup Destinations")
        client_name = tcinputs.get('Machine_client_name')
        plan_name = tcinputs.get('Default_Plan')
        lap_obj = Laptops(admin_console)
        lap_obj.browse_restore_storage_policies(plan_name, client_name.lower())
        self.log.info("Done checking Browse and Restore, Exiting")

    def laptop_acceptance_update(self, tcinputs, laptop_package_info, status, failiure_reason):
        """ Insert the testcase details in  doLaptopPackageSize Table
        Args:
            tcinputs (dict)            : Testcase input answers
            
            laptop_package_info (dict) : Laptop Package Information 

            status (str)               : Test status 
            
            failiure_reason (str)      : Failiure Reason
             
        Returns: None

        """        
        
        laptop_config = get_config().Laptop.Install
        insert_in_db = laptop_config.LaptopPackageSizeInsertInDB
        
        if insert_in_db != "yes":
            self.log.info("LaptopPackageSizeInsertInDB is not set to yes in DB. Skipping DB update")
            return 0 
        
        self.log.info("Updating doLaptopPackageSize Table on [{0}]".format(tcinputs['report_db_server']))
        
        db_table = tcinputs['report_table']
        db_commcell = self._commcell
        self.metallic_table = db_table
        csversion = str(self._commcell.version)
        if self.revision is not None: 
            revision = self.revision
        else:
            revision = self.sp_revision if not tcinputs.get('metallic_ring') else '-'
        commcell_name = self._commcell.commserv_name
        self.reportingdb_commcell = db_commcell
        self.reporting_db_utility = OptionsSelector(db_commcell)
        controller = Machine().machine_name
        if not laptop_package_info:
            laptop_package_info = {'-':{'size': 0}} 
            
        for package in laptop_package_info:
            size = laptop_package_info[package]['size']
            package_size = str(laptop_package_info[package]['size']) + 'MB'
            #package_path = laptop_package_info[package]['download_path']
            #_limit = 125 if 'mac' in package.lower() else 125  # Original 
            _limit = 130 if 'mac' in package.lower() else 180  # Changed because package size increased with CU 
            exception = False
            if size is not None and size > _limit:
                failiure_reason = "Package size = "+str(size)+". Package size is greater than" + str(_limit) + "MB"
                exception = True  
                 
            db_query = r"""UPDATE {} SET 
                        [Commserve] = '{}', 
                        [Client] = '{}', 
                        [CSVersion] = '{}', 
                        [Revision] = '{}', 
                        [Package] = '{}', 
                        [Size] = '{}', 
                        [Controller] = '{}', 
                        [Result] = '{}', 
                        [FailiureReason] = '{}', 
                        [TestCase] = '{}', 
                        [TestName] = '{}', 
                        [Comments] = '{}'
                        WHERE [Date] = '{}'
                            """.format(db_table, commcell_name, tcinputs['Machine_client_name'], csversion, revision, 
                                       package, package_size, controller, status, failiure_reason, self._testcaseid, self._init_object.name , '', self.starttime)

            self.reporting_db_utility.update_commserve_db(
                query=db_query, 
                user_name=tcinputs['report_user'], 
                password=tcinputs['report_password'], 
                dbserver=tcinputs['report_db_server'], 
                dbname=tcinputs['report_db']
            )
            
            if exception:
                raise Exception(failiure_reason)

    def laptop_acceptance_insert(self, tcinputs, status='In Progress'):
        """ Insert the testcase details in  doLaptopPackageSize Table
        Args:
            tcinputs (dict)            : Testcase input answers
            
            status (str)               : Test status                         

        Returns: None

        """        
        
        laptop_config = get_config().Laptop.Install
        insert_in_db = laptop_config.LaptopPackageSizeInsertInDB
        
        if insert_in_db != "yes":
            self.log.info("LaptopPackageSizeInsertInDB is not set to yes in DB. Skipping DB update")
            return 0 
        
        self.log.info("Inserting data in doLaptopPackageSize Table on [{0}]".format(tcinputs['report_db_server']))
        
        db_table = tcinputs['report_table']
        self.metallic_table = db_table
        csversion = str(self._commcell.version)
         
        if self.revision is not None: 
            revision = self.revision
        else:
            revision = self.sp_revision if not tcinputs.get('metallic_ring') else '-' 
        db_commcell = self._commcell
        commcell_name = self._commcell.commserv_name
        self.reportingdb_commcell = db_commcell
        self.reporting_db_utility = OptionsSelector(db_commcell)
        controller = Machine().machine_name
        db_table = tcinputs['report_table']
        date = str(datetime.now().strftime("%d %b %Y %H:%M"))
        failiure_reason = "-" 
        package = '-'
        package_size = '-'
            
        db_query = r"""INSERT INTO {} (Commserve, Client, CSVersion, Revision, Package, Size, Controller, Result, FailiureReason, Date, TestCase, TestName, Comments) 
                        values
                        ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                        """.format(db_table, commcell_name, tcinputs['Machine_client_name'], csversion, revision, 
                                   package, package_size, controller, status, failiure_reason, date, self._testcaseid, self._init_object.name , '')
        self.starttime = date            

        self.reporting_db_utility.update_commserve_db(
            query=db_query, 
            user_name=tcinputs['report_user'], 
            password=tcinputs['report_password'], 
            dbserver=tcinputs['report_db_server'], 
            dbname=tcinputs['report_db']
        )        
        
    @property
    def company(self):
        ''' Read only attribute for company object '''
        return self._company_object

    @property
    def sp_revision(self):
        """ Get the revision installed on the CS """

        query = """
        select MAX(S2.RevisionId) FROM PatchSPVersion S join simInstalledPackages P on S.id=P.SPVersionID
        JOIN PatchSPVersion S2 ON S.Release=S2.Release AND S.SPMajor=S2.SPMajor AND S.SPMinor=S2.SPMinor
        AND S.TransactionID=S2.TransactionID and p.ClientId=2
        """
        resultset = self.utility.exec_commserv_query(query)
        return resultset[0][0]

    @property
    def expected_owners(self):
        """ Returns the list of laptop's expected owners """
        return self._expected_owners

    @expected_owners.setter
    def expected_owners(self, value):
        """ Set's the laptops expected owners """
        if isinstance(value, str):
            self._expected_owners = [value]
        elif isinstance(value, list):
            self._expected_owners = value
            
    def deactivate_laptop(self, laptop_name):
        """Deactivates a laptop"""
        request_json = {
            "clientOperationType": 1,
            "clients": [
                {
                    "clientId": int(self._commcell.clients.get(name= laptop_name).client_id),
                    "_type_": 3
                }
            ],
            "additonalTasks": [
                {
                    "value": "Deactivate",
                    "key": "LaptopAssociationRequest"
                }
            ]
        }
        
        flag, response = self._commcell._cvpysdk_object.make_request('POST', self._commcell._services['GET_ALL_CLIENTS'] + '/Plan', request_json)

        if flag:
            if response.json() and 'operationStatus' in response.json():
                response_json = response.json()['operationStatus']
                if response_json.get('errorCode'):
                    raise Exception(response_json.get('errorMessage', ""))
            else:
                raise Exception('Failed to get the response')
        else:
            raise Exception(self._commcell._update_response_(response.text))

class LaptopHelperUserCentric(LaptopHelper):
    """LaptopHelper helper class to perform laptop related operations for user centric laptops"""

    def __init__(self, init_object, **kwargs):
        """Initialize instance of the LaptopHelperUserCentric class.

        Args:
            init_object: (object) --  TestCase OR Commcell object

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations of
                                instance of various classes.

                                Supported :
                                    company:    (str)    -- Name of company with which to
                                                            initialize OrganizationHelper class
                                                            instance."""
        super(LaptopHelperUserCentric, self).__init__(init_object, **kwargs)

        # Enable shared laptop usage for the organization.
        if not self.organization.shared_laptop_usage:
            self.organization.shared_laptop_usage = True

    def install_laptop(self, tcinputs, config_kwargs, install_kwargs, custompackage_kwargs=None):
        """ Module to install a laptop client in USER CENTRIC MODE

        Args:
            tcinputs (dict)            : Testcase input answers

            config_kwargs (dict)       : Testcase configuration arguments
            -------------------------------------------------------------

                Supported:
                ----------

                os                    (str): Operating system for which to execute the module.
                (Mandatory)

                org_enable_auth_code (bool): If true will disable/enable authcode for the organization.
                (Optional)                    Default:False

                override_auth_code (bool):   If set to true, an existing authcode for the Tenant company shall be
                (Optional)                       ignored, and a new authcode will be created.
                                              Default: True [New authcode will be created whenever org_enable_auth_code
                                                              is set to True]

                org_set_default_plan (bool): If true will set default plan(provided in test inputs) for organization.
                (Optional)                    Default:False

            install_kwargs (dict)      : Client installation arguments
            ----------------------------------------------------------

                Supported:
                ----------

                expected_owners (list):         Client owner validation would be done using this list.
                (Optional)                       If not set then the activation user would be assumed as the client
                                                    owner.

                install_with_authcode (bool):   If True, silent installation will be done on the client using /authcode
                (Optional)                        option.
                                                  Default: None

                execute_simcallwrapper (bool):  If true, SimCallWrapper will register the client post install. Else not
                (Optional)                        Default: False

                authcode (str):                 This is authcode which will be used in silent install
                (Optional)

                check_num_of_devices (bool):    If true validation for clients joined in the organization shall
                (Optional)                          be validated, else not.
                                                    Default: True

                client_groups (list):           If provided the laptops shall be validated to be a part of only these
                (Optional)                          client groups. Else default client groups shall be assumed in the
                                                    underlying called module.
                                                    Default: None

                pseudo_client_groups (list):    If provided the pseudo clients shall be validated to be a part of these
                (Optional)                          client groups. Else default client groups shall be assumed in the
                                                    underlying called module.
                                                    Default: None

                delete_client (bool):           If set, client would not be hard deleted from the commcell after
                (Optional)                          uninstall.
                                                    Default: True

                new_client_name (str):          Post client registration this new client name shall be
                (Optional)                        considered for further processing.
                                                    Default: False

                register_with_new_name (bool):  If set to true the client shall be registered with a new name.
                (Optional)                          Default: False

                register_authcode (str):        If authcode is provided here, the client will be registered with this
                (Optional)                          authcode with SimcallWrapper
                                                    *Do not confuse it with authcode with install*
                                                    *This authcode is provided with SimCallWrapper*
                                                    *As per SP14 design, client should register for Server Plan*
                                                    Default: None

                client_hostname (str):          Client will be registered with this hostname
                (Optional)                      Default: None


                skip_osc    (bool):             If true:
                (Optional)                      Will not wait for the filtered automatic jobs to trigger
                                                    (Reinstall cases for laptop, where the owner does not change)

                blacklist_user (str):           Add this user to blacklist user group
                (Optional)                      Default: None


                remove_blacklisted_user (str):  Remove this user from blacklist user group
                (Optional)                      Default: None

                post_osc_backup (bool):         If set to False will skip sublicent content modification and auto
                (Optional)                          backup job execution from osc
                                                    Default: True

                nLaptopAgent (int):             Expected values (0/1)
                (Optional)                          Default: 1

                validate_user (bool):            If true:
                                                 Validates the username with which the job triggered from the Backunow
                                                 button.

                backupnow  (bool):                If true:
                                                 Validate the BackupNow button on the Edgemonitor app.

                wait_for_reinstalled_client (bool):
                (Optional)                      If set to true wait for the client to be activated post re-install.
                                                    Default: False

                sleep_before_osc (bool):
                (Optional)                      If set to true wait for the client to restore active state post
                                                    re-install.
                                                    Default: False

                activation_time_limit (int):    Activation time limit.
                                                    Default: 12

                check_client_activation (bool): Check client is activated to respective plan
                                                    Default: True
                                                    Else:
                                                        True:  If org_set_default_plan option is set to True
                                                        False: If org_set_default_plan option is set to False
                                                    Else:
                                                        False:

            custompackage_kwargs (dict) : Custom package creation arguments
            ---------------------------------------------------------------

                Supported:
                ----------
                servicePack  (str):               Service pack for which to create the custom package
                                                    e.g: SP14

                SP_revision  (str):               Service Pack Revision for the custom package to create

                skip_creation (bool):             Skip package creation if skip_creation is set to true
                (Optional)                          Default: False

                authcode_flag (bool):             If set, custom package shall be created with relevant authcode for
                (Optional)                          either the tenant or from commcell level.
                                                    Default: False

                ClientGroups (str):               If provided custom package shall be created with this client group,
                                                    which means the laptop is supposed to be associated to this
                                                    client group post install
                                                    Default: None

                laptopClient (str):               "true"/"false": Configure for laptop client?
                (Optional)                          Default: true

                Custom_pkg_username (str):        Username with which the custom package is created.
                (Optional)                          Default: None

                Custom_pkg_password (str):        Password for the user with which the custom package is created.
                (Optional)                          Default: None

                requireCredentials (str):         Require credentials
                (Optional)                          Default: "true"

                backupMonitor (str):              Enable Edge monitor app process
                (Optional)                          Default: "true", Options: "false" / "true"

        Returns: None

        Exception:
            - If install is set to be done with auth_code but auth_code is not set.
            - Client not registered with commcell.
        """

        if custompackage_kwargs is None:
            custompackage_kwargs = {}
        cp_authcode = None

        try:
            #-------------------------------------------------------------------------------------
            # Setup
            #-------------------------------------------------------------------------------------

            # Setup machine object
            machine_object = self.utility.get_machine_object(
                tcinputs['Machine_host_name'], tcinputs['Machine_user_name'], tcinputs['Machine_password']
            )
            tcinputs['Machine_object'] = machine_object

            # Log the environment info before proceeding with the Laptop installation.
            # To Do : Add SQL queries at plan/organization/commcell levels to get all existing details before install.
            self.environment_info()
            self.create_rdp_sessions(tcinputs)
            self.log.info("Client platform: [{0}]".format(tcinputs['os_type']))
            tcinputs['Machine_client_name'] = tcinputs.get('Machine_client_name', machine_object.machine_name)

            # Add/remove blacklisted user groups before installation.
            self.set_blacklisted_users(
                install_kwargs.get('blacklist_user'), install_kwargs.get('remove_blacklisted_user')
            )

            # Set authcode for organization
            if config_kwargs.get('org_enable_auth_code', False):
                install_authcode = self.set_authcode(config_kwargs.get('override_auth_code', True))
                cp_authcode = install_authcode

            # Set default plan and client group name for organization
            plan_name = tcinputs.get('Plan', tcinputs.get('Default_Plan'))
            if config_kwargs.get('org_set_default_plan', False):
                self.set_default_plan(plan_name)

            # If silent install has to be done through authcode.
            # Enabling authcode at org level does not mean user wants to install with authcode.
            # Covers negative scenarios where user provides wrong authcode to install and org authcode is different
            if install_kwargs.get('install_with_authcode'):
                # User provided authcode in test case
                if install_kwargs.get('authcode'):
                    install_authcode = install_kwargs.get('authcode')
                    cp_authcode = install_authcode

                # If user says install with authcode but by now authcode is not set or not provided, exception out.
                if not install_authcode or install_authcode is None:
                    raise Exception("Please provide auth code to use during install.")
            else:
                install_authcode = None

            #-------------------------------------------------------------------------------------
            # Create custom package
            #-------------------------------------------------------------------------------------

            custompackage_kwargs['authcode'] = cp_authcode
            custompackage_kwargs['choose_os'] = tcinputs['choose_os']            
            pkg_path = self.create_custom_package(custompackage_kwargs)

            #-------------------------------------------------------------------------------------
            # Install laptop
            #-------------------------------------------------------------------------------------

            install_args = {
                'BackupNow': install_kwargs.get('backupnow', False),
                'client_user_name': tcinputs['Machine_user_name'],
                'client_password': tcinputs['Machine_password'],
                'client_host_name': tcinputs['Machine_host_name'],
                'client_hostname': install_kwargs.get('client_hostname'),
                'client_name': tcinputs['Machine_client_name'],
                'delete_client': install_kwargs.get('delete_client', True),
                'executable_name': installer_constants.PACKAGE_EXE_MAP[tcinputs['os_type']],
                'install_authcode': install_authcode,
                'install_type': install_kwargs.get('interactive_install', False),
                'install_with_authcode': install_kwargs.get('install_with_authcode'),
                'organization_object': self._company_object,
                'package_location': pkg_path,
                'registering_user': tcinputs['Activation_User'],
                'registering_user_password': tcinputs.get('Activation_Password'),
                'register_auth_code': install_kwargs.get('register_authcode'),
                'register_with_SAML': install_kwargs.get('register_with_SAML', False),
                'saml_email': tcinputs['saml_email'] if install_kwargs.get('register_with_SAML') else None,
                'takeover_client': install_kwargs.get('takeover_client', False),
                'Tenant_company': self._company_name,
                'user_map': tcinputs['user_map'],
                'LaunchEdgeMonitor': install_kwargs.get("LaunchEdgeMonitor", "true"),
                'check_client_activation': install_kwargs.get('check_client_activation', True)
            }

            register_args = {
                'register_with_new_name': install_kwargs.get('register_with_new_name'),
                'new_client_name': install_kwargs.get('new_client_name'),
                'wait_for_reinstalled_client': install_kwargs.get('wait_for_reinstalled_client', False),
                'Machine_object': tcinputs['Machine_object'],
                'Plan': plan_name,
                'activation_time_limit': install_kwargs.get('activation_time_limit', 12),
                'org_set_default_plan': config_kwargs.get('org_set_default_plan', False)
            }

            client_data = self.install_and_register(
                tcinputs['Machine_client_name'],
                install_kwargs.get('execute_simcallwrapper'),
                install_args,
                **register_args
            )
            client_obj = client_data[1]
            client_name = client_data[0]

            #---------------------------------------------------------------------------------
            # Validate if Pseudo Clients are created for every user in  UserCentric Mode
            #---------------------------------------------------------------------------------
            self.check_pseudo_clients(tcinputs['user_map'])

            #---------------------------------------------------------------------------------
            # OSC Backup and Restore
            # 1: OSC Backup Job shouldn't run for the Physical clients
            # 2: Backup job runs only for the Pseudo client.
            #       -if OSC job is running wait for the job to finish.
            #       -else check if a FULL job is already ran for the client and validate the job
            #---------------------------------------------------------------------------------

            self.tc.log_step("""
                -  [{0}] Backup and restore phase""".format(tcinputs['Machine_host_name']))

            # After reinstalls especially in cases of Multiple companies with same client name and different hostname
            # Even after activation the client takes some time to initialize. Subclient content if modified is
            # reverted back to original contents.
            if install_kwargs.get('sleep_before_osc', False):
                self.utility.sleep_time(120, "Waiting before osc backup and restore")

            for key in tcinputs['user_map']:
                self.utils.osc_backup_and_restore(
                    client_name,
                    validate=True,
                    postbackup=install_kwargs.get('post_osc_backup', self.skip_postosc_backup),
                    skip_osc=install_kwargs.get('skip_osc', self.skip_osc_job_wait),
                    options=tcinputs['osc_options'],
                    validate_user=install_kwargs.get('validate_user', False),
                    registering_user=tcinputs['Activation_User'],
                    client_name=tcinputs['user_map'][key]['pseudo_client'],
                    current_state=['completed', 'running', 'waiting'],
                    incr_current_state=['running', 'waiting', 'pending']
                )

            #---------------------------------------------------------------------------------
            # Install validation
            # 1: For Physical clients no Owner should be set
            # 2: For Pseudo clients
            #       - For each pseudo client and make sure it's owner is set
            #       - Validate the pseudo client count after installation.
            #---------------------------------------------------------------------------------

            self.tc.log_step("""set_inputs
                -  [{0}] Validation phase""".format(tcinputs['Machine_host_name']))

            # Physical client does not get associated to Plan client groups.
            client_groups = install_kwargs.get('client_groups', ['Laptop Clients', self.organization.company_name])
            expected_owners = install_kwargs.get('expected_owners', [])
            blacklist_user = install_kwargs.get('blacklist_user')
            if blacklist_user and blacklist_user in expected_owners:
                expected_owners.remove(blacklist_user)
            self.organization.validate_client(client_obj,
                                              expected_owners=expected_owners,
                                              client_groups=client_groups,
                                              clients_joined=install_kwargs.get('check_num_of_devices', True),
                                              increment_client_count_by=len(list(tcinputs['user_map'].keys())),
                                              nLaptopAgent=install_kwargs.get('nLaptopAgent', 1),
                                              client_name=client_name)

            # Validation for User Centric pseudo clients
            for each_user in tcinputs.get('user_map', []):
                self.organization.validate_usercentric_client(
                    tcinputs['user_map'][each_user]['pseudo_client'],
                    expected_owners=[each_user],
                    client_groups=install_kwargs.get('pseudo_client_groups', install_kwargs.get('client_groups'))
                )

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def sendemail_scaletest(self, tcinputs, status):
        """
            generates email content with headers, data and returns html string.

            @args:

            data (dictionary)     : body of the mail in dictionary format

            returns

            items(list)    : list of items as html in email body
        """

        style = ''' <html>
        <style type="text/css">
   

   
        header h2 {
            margin: 20px;
        }

        </style>

        <header>
            <h2>Scale test for cloud laptops</h2>
        </header>
        <body>
        '''

        items = []
        laptop_config = get_config().Laptop.Install
        logs_network_path = laptop_config.NetworkPath
        items.append('<p> %s' % style + '</p>')
        items.append('<p>The below information is from the automation run for scale test on cloudlaptops</p>')
        items.append('<p><b> ClientName: </b> %s' % tcinputs['Machine_client_name'])
        items.append('<p><b> DataPath: </b> %s' % tcinputs['testdatapath'])
        items.append('<p> <b>Number of folders:</b> %s' % tcinputs['numfolders'])
        items.append('<p> <b>Number of files: </b>%s' % tcinputs['numfiles'])
        font_color = "red"
        if status == 'PASSED':
            font_color = "green"

        items.append('<p> <b>Result of run:</b> <b><font color="%s">%s</b></font color>' % (font_color, status))
        items.append('<p><b> Logs location for client and CS :</b> %s' % logs_network_path)

        items.append("</body></html>")
        self.log.info('\n'.join(items))
        mail = Mailer({'receiver':tcinputs['receivers']}, commcell_object=self._commcell)
        mail.mail("Scale testrun  for clouLaptops", '\n'.join(items))


    def install_and_register(self, client, register, install_args, **registration_args):
        """ Laptop installation and registration for user centric clients
        Args:

            client (str):                    Client Name

            register (bool):                 Register client post install

            install_args (dict):             Installation arguments
            --------------------

                Supported
                ---------

                LaunchEdgeMonitor (str):         Enable Edge monitor app process
                (Optional)                          Default: "true", Options: "false" / "true"

                user_map    (dict):            User map dictionary for the User Centric clients
                    e.g
                    {
                        '######':
                            {
                                'domain': '######',
                                'domain_user': 'testuser_01',
                                'password': '_password',
                                'pseudo_client': clientname_######_testuser_01
                            },
                        'testuser_02':
                            {
                                'domain': '######',
                                'domain_user': 'testuser_02',
                                'password': '_password',
                                'pseudo_client': clientname_######_testuser_02
                            }
                    }

                backupnow  (bool):                If true:
                                                 Validate the BackupNow button on the Edgemonitor app.

                register_authcode (str):        If authcode is provided here, the client will be registered with this
                (Optional)                          authcode with SimcallWrapper
                                                    *Do not confuse it with authcode with install*
                                                    *This authcode is provided with SimCallWrapper*
                                                    *As per SP14 design, client should register for Server Plan*
                                                    Default: None

                client_host_name (str):          Client hostname
                (Mandatory)                      Default: None

                client_hostname (str):           Client will be registered with this hostname
                (Mandatory)                      Default: None

                client_user_name (str):          Client will be registered with this name
                (Mandatory)                      Default: None

                client_password (str):           Client password
                (Mandatory)                      Default: None

                client_name (str):               Client name
                (Mandatory)                      Default: None

                delete_client (bool):            Delete client from Commcell before install and in cleanup
                (Mandatory)                      Default: True

                executable_name (str):           Custom Package executable name
                (Mandatory)                      Default: Computed from constants

                install_authcode (str):          Installation will be done with this auth code
                (Optional)                       Default: None

                install_type (bool):             Installation Type (True/False)
                (Mandatory)                      Default: False

                organization_object (object):    Organization object
                (Mandatory)                      Default: Computed in __init__

                package_location (str):          Location where packages would be copied to the client
                (Mandatory)                      Default: None

                registering_user (str):          This user name would be used to register the client
                (Mandatory)                      Default: None

                registering_user_password (str): Registering user password
                (Mandatory)                      Default: None

                register_auth_code (str):        Registration would be done with this auth code
                (optional)                       Default: None

                register_with_SAML (bool):       SAML Registration (True/False)
                (Mandatory)                      Default: False

                saml_email (str):                SAML email
                (Optional)                       Default: None

                takeover_client (bool):          Takeover client
                (Mandatory)                      Default: False

                Tenant_company (str):            Tenant company name
                (Mandatory)                      Default: None

                check_client_activation (bool): Check client is activated to respective plan
                                                    Default: True
                                                    Else:
                                                        True:  If org_set_default_plan option is set to True
                                                        False: If org_set_default_plan option is set to False
                                                    Else:
                                                        False:

            ----------------------------------------------------------------------------------------------------------

            registration_args (dict):        Registration Arguments
            -------------------------

                Supported
                ---------

                org_set_default_plan (bool): If true will set default plan(provided in test inputs) for organization.
                (Optional)                    Default:False

                activation_time_limit (int):    Activation time limit.
                                                    Default: 12


                new_client_name (str):          Post client registration this new client name shall be
                (Optional)                        considered for further processing.
                                                    Default: False

                register_with_new_name (bool):  If set to true the client shall be registered with a new name.
                (Optional)                          Default: False

                wait_for_reinstalled_client (bool):
                (Optional)                      If set to true wait for the client to be activated post re-install.
                                                    Default: False

                Machine_object (object):        Client Machine object for Machine class
                (Optional)

                Plan  (str):                    Plan name
                (Optional)

            ----------------------------------------------------------------------------------------------------------

        Returns: Tuple
            (Client name (str):    Client name,
             client object (obj):    Machine class object for the client)

        Raises
            Exception
                - if failed to install client

        """
        try:

            self.tc.log_step("Custom package Installation for [{0}]".format(install_args['client_host_name']))

            self.tc.log_step("""
                - [{1}]     Install custom package with following parameters
                  [{0}]
            """.format(install_args, install_args['client_host_name']))
            self.installer = Installation.create_installer_object(install_args, self._commcell)
            self.installer.uninstall_existing_instance()
            self.installer.delete_client_from_commcell()
            if self._company_object:
                pre_machine_count = self._company_object.machine_count
            self.installer.install_client()
            registered_client = client

            if register:
                register_with_client = client
                if registration_args.get('register_with_new_name'):
                    register_with_client = registration_args['new_client_name']
                registered_client = registration_args.get('new_client_name', registered_client)

                for each_user in install_args['user_map']:
                    self.installer.execute_register_me_command(
                        username=each_user,
                        password=install_args['user_map'][each_user]['password'],
                        register_with_client=register_with_client,
                        client_post_register=registered_client
                    )
            self._commcell.refresh()

            # In reinstall of client (takeover) the client activation takes time even though the client is ready
            # and part of defaults Plans client group.(Because of old entry). The old client is also part of
            # company's devices. Observed if proceed without sleep, subclient content is overridden and removed
            # for reinstalled client, so osc backup triggered through manually updated content immediately after
            # registration fails.
            if not registration_args.get('new_client_name'):
                if registration_args.get('wait_for_reinstalled_client', False):
                    self.utility.sleep_time(120, "Waiting for reinstalled client to be activated.")
                elif self._company_object:
                    _ = self.organization.is_device_associated(pre_machine_count)

            # In case the client name is supposed to change post registration [ Reinstall scenarios ],
            # then set the client name.
            # Also, Wait until client ready, before creating client object.
            # Because when client object is created with commcell object, it checks for client readiness, and if
            # client is not ready exceptions out.
            # Also, post simwrapper execution or even without it, when cvd registers/activates clients, client
            # is not ready [ Client check readiness fails ] for certain interval of time.
            new_client = registration_args.get('new_client_name')
            client = new_client if new_client else client
            _ = self.utility.wait_until_client_ready(client)
            client_obj = self.utility.get_machine_object(client) if new_client else registration_args['Machine_object']

            if install_args.get("LaunchEdgeMonitor") == "true":
                self.is_edge_monitor_running(client_obj)

            # By default check if client was activated post install.
            # Otherwise honor whatever is set in check_client_activation
            # If that's not set, honor if default plan is set as part of testcase via org_set_default_plan
            if install_args.get('check_client_activation', registration_args.get('org_set_default_plan', False)):
                for each_user in install_args['user_map']:
                    _ = self.organization.is_client_activated(
                        install_args['user_map'][each_user]['pseudo_client'],
                        registration_args['Plan'],
                        time_limit=registration_args.get('activation_time_limit', 12)
                    )

            return (client, client_obj)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    @staticmethod
    def create_pseudo_map(test_inputs):
        """ Create user map for User Centric clients

         Args:

            test_inputs (dict)          : test case inputs

        Returns:

            Dictionary containing details for each user
            e.g
            {
                '######':
                    {
                        'domain': '######',
                        'domain_user': 'testuser_01',
                        'password': '######',
                        'pseudo_client': clientname_testuser_01
                    },
                'testuser_02':
                    {
                        'domain': '######',
                        'domain_user': 'testuser_02',
                        'password': '######',
                        'pseudo_client': clientname_testuser_02
                    }
            }

        Raises
            Exception
                - If failed to create mapping

        """
        try:
            client_name = test_inputs.get('Machine_client_name', test_inputs['Machine_host_name'])
            usermap = {}
            for key, _ in test_inputs.items():
                if 'Activation_User' not in key or test_inputs.get(key) is None:
                    continue
                user = test_inputs[key]
                domain = user.split("\\")[0]
                domain_username = user.split("\\")[1]
                usermap[user] = {}
                usermap[user]['domain'] = domain
                usermap[user]['domain_user'] = domain_username
                usermap[user]['pseudo_client'] = '_'.join([client_name, domain, domain_username])
                passkey = "Activation_Password"
                user_index = key.split('Activation_User')[1]
                if user_index:
                    passkey += str(user_index)
                usermap[user]['password'] = test_inputs.get(passkey, '')

            return usermap

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def check_pseudo_clients(self, user_map):
        """ Checks if pseudo clients are created on the Commcell for each user in the user map

         Args:

            user_map (dict)             : user map for Pseudo clients

        Example:

            Dictionary containing details for each user
            e.g
            {
                '######':
                    {
                        'domain': '######',
                        'domain_user': 'testuser_01',
                        'pseudo_client': clientname_testuser_01
                    },
                'testuser_02':
                    {
                        'domain': '######',
                        'domain_user': 'testuser_02',
                        'pseudo_client': clientname_testuser_02
                    }
            }

        Raises
            Exception
                - If pseudo client does not exist on Commcell

        """
        try:
            self._commcell.refresh()
            for each_user in user_map:
                client_name = user_map[each_user]['pseudo_client']
                if not self._commcell.clients.has_client(client_name):
                    self.log.error("Pseudo client [{0}] is not created".format(client_name))
                    raise Exception("Pseudo client [{0}] is not created in UserCentric Mode".format(client_name))
                else:
                    self.log.info("Pseudo client is [{0}] created on Commcell".format(client_name))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def cleanup_user_centric(self, tcinputs, delete_client=True):
        """ Module to perform cleanups for shared laptop testcases

         Args:
            tcinputs (dict)            : Testcase input answers

            delete_client (bool)       : Hard delete client from commcell
                                            Default: True
        """
        # Disable shared laptop usage on the organization.
        if not self._company_name:
            self.log.info("Disabling shared laptop for Commcell")
            self._commcell.disable_shared_laptop()
        else:
            self.organization.shared_laptop_usage = False
        self.cleanup(tcinputs, delete_client)

    def validate_end_user_data(self, tcinputs):
        """ Validates if owner of client sees only their profile data
        Args:
            tcinputs (dict)            : Testcase input answers
        """

        if tcinputs['os_type'] == 'Windows':
            path = 'C:\\Users'
        else:
            path = '/Users'
        for key in tcinputs['user_map']:
            validation_user = tcinputs['user_map'][key]['domain_user']
            validation_client = tcinputs['user_map'][key]['pseudo_client']
            subclient_obj = CommonUtils.get_subclient(self, validation_client)
            self.log.info("Validating backed up data for user: {}".format(key))
            browse_results = subclient_obj.browse(path=path)
            if not len(browse_results[0]) == 1:
                self.log.error("Browse_results: {}".format(browse_results))
                raise Exception("Browse results returned data for more than one user")
            if not os.path.basename(browse_results[0][0]) == validation_user:
                self.log.error("Browse_results: {}".format(browse_results))
                raise Exception("Browse results returned data of different user")
            self.log.info("validation success")

class LaptopHelperMetallic(LaptopHelper):
    """LaptopHelper helper class to perform laptop related operations for Metallic"""

    def __init__(self, init_object, **kwargs):
        """Initialize instance of the LaptopHelperMetallic class.

        Args:
            init_object: (object) --  TestCase OR Commcell object

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations of
                                instance of various classes.

                                Supported :
                                    company:    (str)    -- Name of company with which to
                                                            initialize OrganizationHelper class
                                                            instance."""
        super(LaptopHelperMetallic, self).__init__(init_object, **kwargs)
   
    def insert_testcase_details(self, tcinputs):
        """ Insert the testcase details in  MetallicEndpointAutomation Table
        Args:
            tcinputs (dict)            : Testcase input answers

        Returns: None

        """
        
        self.log.info("Updating MetallicEndpointAutomation Table on [{0}]".format(tcinputs['report_db_server']))
        start_time = str(datetime.now().strftime("%d %b %Y %H:%M"))
        self.install_starttime = datetime.now()
        db_table = tcinputs['report_table']
        self.metallic_table = db_table
        feature_release = 'SP'+str(self._commcell.commserv_version)
        db_query = r"""INSERT INTO {} (TestCase, Summary, OS, FeatureRelease, DownloadTime, InstallTime, RegistrationTime, ActivationTime, FullBackupTime, RestoreTime, StartTime, EndTime, TimeTaken, LogLocation, Status) 
                    values
                    ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                    """.format(db_table, self._testcaseid, self._init_object.name, tcinputs['os_type'], feature_release, 
                               '-', '-', '-', '-', '-', '-', start_time, '-', '-', '-', 'In progress')
                                      
        db_commcell = self._commcell
        self.reportingdb_commcell = db_commcell
        self.reporting_db_utility = OptionsSelector(db_commcell)        
        self.reporting_db_utility.update_commserve_db(
            query=db_query, 
            user_name=tcinputs['report_user'], 
            password=tcinputs['report_password'], 
            dbserver=tcinputs['report_db_server'], 
            dbname=tcinputs['report_db']
        )
        _query = "select * from {0} where StartTime='{1}'".format(db_table, start_time)
        resultset = self.reporting_db_utility.update_commserve_db(
            query=_query, 
            user_name=tcinputs['report_user'], 
            password=tcinputs['report_password'], 
            dbserver=tcinputs['report_db_server'], 
            dbname=tcinputs['report_db']
        )        
        self.metalllic_id = resultset._rows[0][0]

    def update_testcase_details(self, column_name, value): 
        """ Update every activity time in  MetallicEndpointAutomation Table
        Args:
            column_name     : Name of the Column need to be inserted in DB
                                 EX: 'InstallTime' , 'Activation Time'
            
            value           : value of the column need to be inserted in DB
                                 EX: 4 m , ' 2 m'

        Returns: None

        """
        metallic_id = self.metalllic_id                        
        db_query = "update {} set {}='{}' where id = {}".format(self.metallic_table, column_name, value, metallic_id)
        self.reporting_db_utility.update_commserve_db(db_query)
    
    def install_laptop(self, tcinputs, config_kwargs, install_kwargs, custom_pkg_path):
        """ Module to install a laptop client

        Args:
            tcinputs (dict)            : Testcase input answers

            config_kwargs (dict)       : Testcase configuration arguments
            -------------------------------------------------------------

                Supported:
                ----------

                os                    (str): Operating system for which to execute the module.
                (Mandatory)

                org_enable_auth_code (bool): If true will disable/enable authcode for the organization.
                (Optional)                    Default:False

                override_auth_code (bool):   If set to true, an existing authcode for the Tenant company shall be
                (Optional)                       ignored, and a new authcode will be created.
                                              Default: True [New authcode will be created whenever org_enable_auth_code
                                                              is set to True]

                org_set_default_plan (bool): If true will set default plan(provided in test inputs) for organization.
                (Optional)                    Default:False

            install_kwargs (dict)      : Client installation arguments
            ----------------------------------------------------------

                Supported:
                ----------

                expected_owners (list):         Client owner validation would be done using this list.
                (Optional)                       If not set then the activation user would be assumed as the client
                                                    owner.

                install_with_authcode (bool):   If True, silent installation will be done on the client using /authcode
                (Optional)                        option.
                                                  Default: None

                execute_simcallwrapper (bool):  If true, SimCallWrapper will register the client post install. Else not
                (Optional)                        Default: False

                authcode (str):                 This is authcode which will be used in silent install
                (Optional)

                check_num_of_devices (bool):    If true validation for clients joined in the organization shall
                (Optional)                          be validated, else not.
                                                    Default: True

                client_groups (list):           If provided the laptops shall be validated to be a part of only these
                (Optional)                          client groups. Else default client groups shall be assumed in the
                                                    underlying called module.
                                                    Default: None

                delete_client (bool):           If set, client would not be hard deleted from the commcell after
                (Optional)                          uninstall.
                                                    Default: True

                new_client_name (str):          Post client registration this new client name shall be
                (Optional)                        considered for further processing.
                                                    Default: False

                register_with_new_name (bool):  If set to true the client shall be registered with a new name.
                (Optional)                          Default: False

                register_authcode (str):        If authcode is provided here, the client will be registered with this
                (Optional)                          authcode with SimcallWrapper
                                                    *Do not confuse it with authcode with install*
                                                    *This authcode is provided with SimCallWrapper*
                                                    *As per SP14 design, client should register for Server Plan*
                                                    Default: None

                client_hostname (str):          Client will be registered with this hostname
                (Optional)                      Default: None


                skip_osc    (bool):             If true:
                (Optional)                      Will not wait for the filtered automatic jobs to trigger
                                                    (Reinstall cases for laptop, where the owner does not change)

                blacklist_user (str):           Add this user to blacklist user group
                (Optional)                      Default: None


                remove_blacklisted_user (str):  Remove this user from blacklist user group
                (Optional)                      Default: None

                post_osc_backup (bool):         If set to False will skip sublicent content modification and auto
                (Optional)                          backup job execution from osc
                                                    Default: True

                nLaptopAgent (int):             Expected values (0/1)
                (Optional)                          Default: 1

                validate_user (bool):            If true:
                                                 Validates the username with which the job triggered from the Backunow
                                                 button.

                backupnow  (bool):                If true:
                                                 Validate the BackupNow button on the Edgemonitor app.

                wait_for_reinstalled_client (bool):
                (Optional)                      If set to true wait for the client to be activated post re-install.
                                                    Default: False

                sleep_before_osc (bool):
                (Optional)                      If set to true wait for the client to restore active state post
                                                    re-install.
                                                    Default: False

                activation_time_limit (int):    Activation time limit.
                                                    Default: 8

                check_client_activation (bool): Check client is activated to respective plan
                                                    Default: True
                                                    Else:
                                                        True:  If org_set_default_plan option is set to True
                                                        False: If org_set_default_plan option is set to False
                                                    Else:
                                                        False:


        custom_pkg_path:
        ----------------
        For mettalic default package path set as constants.TEMP_DIR+testcaseid in testcase
        
        Exception:
            - If install is set to be done with auth_code but auth_code is not set.
            - Client not registered with commcell.
        """
        
        self.insert_testcase_details(tcinputs)

        try:
            #-------------------------------------------------------------------------------------
            # Setup
            #-------------------------------------------------------------------------------------

            # Setup machine object
            machine_object = self.utility.get_machine_object(
                tcinputs['Machine_host_name'], tcinputs['Machine_user_name'], tcinputs['Machine_password']
            )
            tcinputs['Machine_object'] = machine_object

            self.log.info("Client platform: [{0}]".format(tcinputs['os_type']))
            tcinputs['Machine_client_name'] = tcinputs.get('Machine_client_name', machine_object.machine_name)

            # Add/remove blacklisted user groups before installation.
            self.set_blacklisted_users(
                install_kwargs.get('blacklist_user'), install_kwargs.get('remove_blacklisted_user')
            )

            install_authcode = None

            #-------------------------------------------------------------------------------------
            # Install laptop
            #-------------------------------------------------------------------------------------

            install_args = {
                'BackupNow': install_kwargs.get('backupnow', False),
                'client_user_name': tcinputs['Machine_user_name'],
                'client_password': tcinputs['Machine_password'],
                'client_host_name': tcinputs['Machine_host_name'],
                'client_hostname': install_kwargs.get('client_hostname'),
                'client_name': tcinputs['Machine_client_name'],
                'delete_client': install_kwargs.get('delete_client', True),
                'executable_name': installer_constants.METALLIC_PACKAGE_EXE_MAP[tcinputs['os_type']],
                'install_authcode': install_authcode,
                'install_type': install_kwargs.get('interactive_install', False),
                'install_with_authcode': install_kwargs.get('install_with_authcode'),
                'organization_object': self._company_object,
                'package_location': custom_pkg_path,
                'registering_user': tcinputs['Activation_User'],
                'registering_user_password': tcinputs.get('Activation_Password'),
                'register_auth_code': install_kwargs.get('register_authcode'),
                'register_with_SAML': install_kwargs.get('register_with_SAML', False),
                'saml_email': tcinputs['saml_email'] if install_kwargs.get('register_with_SAML') else None,
                'takeover_client': install_kwargs.get('takeover_client', False),
                'Tenant_company': self._company_name,
                'LaunchEdgeMonitor': install_kwargs.get("LaunchEdgeMonitor", "true"),
                'check_client_activation': install_kwargs.get('check_client_activation', True)
            }

            register_args = {
                'register_with_new_name': install_kwargs.get('register_with_new_name'),
                'new_client_name': install_kwargs.get('new_client_name'),
                'wait_for_reinstalled_client': install_kwargs.get('wait_for_reinstalled_client', False),
                'Machine_object': tcinputs['Machine_object'],
                'Default_Plan': tcinputs.get('Default_Plan'),
                'activation_time_limit': install_kwargs.get('activation_time_limit', 8),
                'org_set_default_plan': config_kwargs.get('org_set_default_plan', False)
            }

            client_obj = self.install_and_register(
                tcinputs['Machine_client_name'],
                install_kwargs.get('execute_simcallwrapper'),
                install_args,
                **register_args
            )

            #---------------------------------------------------------------------------------
            # OSC Backup and Restore
            #---------------------------------------------------------------------------------

            self.tc.log_step("""
                -  [{0}] Backup and restore phase""".format(tcinputs['Machine_host_name']))
                
            # After reinstalls especially in cases of Multiple companies with same client name and different
            # hostname. Even after activation the client takes some time to initialize.
            # Subclient content if modified is reverted back to original contents.
            if install_kwargs.get('sleep_before_osc', False):
                self.utility.sleep_time(120, "Waiting before osc backup and restore")
                
            # Sometimes Sim registration is quick and before check client check readiness and edge monitor running
            # or not the backup job is completed. So for full backups check for all states, and for incrementals
            # since there are no checks after subclient content modification, capturing incremental backup job is
            # immediate.
            self.utils.osc_backup_and_restore(
                client_obj,
                validate=True,
                postbackup=install_kwargs.get('post_osc_backup', False),
                skip_osc=install_kwargs.get('skip_osc', False),
                options=tcinputs['osc_options'],
                validate_user=install_kwargs.get('validate_user', False),
                registering_user=tcinputs['Activation_User'],
                laptop_helper_object=self,
                current_state='running'

            )

            #---------------------------------------------------------------------------------
            # Install validation
            #---------------------------------------------------------------------------------

            self.tc.log_step("""
                -  [{0}] Validation phase""".format(tcinputs['Machine_host_name']))
            expected_owners = install_kwargs.get('expected_owners', [tcinputs['Activation_User']])
            blacklist_user = install_kwargs.get('blacklist_user')
            if blacklist_user and blacklist_user in expected_owners:
                expected_owners.remove(blacklist_user)
            self.organization.validate_client(
                client_obj,
                expected_owners=expected_owners,
                client_groups=install_kwargs.get('client_groups', [tcinputs['Tenant_company']]),
                clients_joined=install_kwargs.get('check_num_of_devices', True),
                nLaptopAgent=install_kwargs.get('nLaptopAgent', 1)
            )
            self.update_testcase_details('Status', "Pass")
            
        except Exception as excp:
            self.update_testcase_details('Status', "Fail")
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        
        finally:
            time.sleep(5)
            cur_time = str(datetime.now().strftime("%d %b %Y %H:%M"))
            end_time = datetime.now()
            curelap_time = (end_time - self.install_starttime).total_seconds()
            totaltime = str(round(curelap_time/60)) + 'm'
            self.update_testcase_details('EndTime', str(cur_time))
            self.update_testcase_details('TimeTaken', totaltime)

    def install_and_register(self, client, register, install_args, **registration_args):
        """ Laptop installation and registration
        Args:

            client (str):                    Client Name

            register (bool):                 Register client post install

            install_args (dict):             Installation arguments
            --------------------

                Supported
                ---------

                LaunchEdgeMonitor (str):        Enable Edge monitor app process
                (Optional)                          Default: "true", Options: "false" / "true"

                backupnow  (bool):              If true:
                                                Validate the BackupNow button on the Edgemonitor app.

                register_authcode (str):        If authcode is provided here, the client will be registered with this
                (Optional)                          authcode with SimcallWrapper
                                                    *Do not confuse it with authcode with install*
                                                    *This authcode is provided with SimCallWrapper*
                                                    *As per SP14 design, client should register for Server Plan*
                                                    Default: None

                client_host_name (str):          Client hostname
                (Mandatory)                      Default: None

                client_new_hostname (str):           Client will be registered with this hostname
                (Mandatory)                      Default: None

                client_user_name (str):          Client will be registered with this name
                (Mandatory)                      Default: None

                client_password (str):           Client password
                (Mandatory)                      Default: None

                client_name (str):               Client name
                (Mandatory)                      Default: None

                delete_client (bool):            Delete client from Commcell before install and in cleanup
                (Mandatory)                      Default: True

                executable_name (str):           Custom Package executable name
                (Mandatory)                      Default: Computed from constants

                install_authcode (str):          Installation will be done with this auth code
                (Optional)                       Default: None

                install_type (bool):             Installation Type (True/False)
                (Mandatory)                      Default: False

                organization_object (object):    Organization object
                (Mandatory)                      Default: Computed in __init__

                package_location (str):          Location where packages would be copied to the client
                (Mandatory)                      Default: None

                registering_user (str):          This user name would be used to register the client
                (Mandatory)                      Default: None

                registering_user_password (str): Registering user password
                (Mandatory)                      Default: None

                register_auth_code (str):        Registration would be done with this auth code
                (optional)                       Default: None

                register_with_SAML (bool):       SAML Registration (True/False)
                (Mandatory)                      Default: False

                saml_email (str):                SAML email
                (Optional)                       Default: None

                takeover_client (bool):          Takeover client
                (Mandatory)                      Default: False

                Tenant_company (str):            Tenant company name
                (Mandatory)                      Default: None

                check_client_activation (bool): Check client is activated to respective plan
                                                    Default: True
                                                    Else:
                                                        True:  If org_set_default_plan option is set to True
                                                        False: If org_set_default_plan option is set to False
                                                    Else:
                                                        False:

            ----------------------------------------------------------------------------------------------------------

            registration_args (dict):        Registration Arguments
            -------------------------

                Supported
                ---------

                org_set_default_plan (bool): If true will set default plan(provided in test inputs) for organization.
                (Optional)                    Default:False

                activation_time_limit (int):    Activation time limit.
                                                    Default: 8


                new_client_name (str):          Post client registration this new client name shall be
                (Optional)                        considered for further processing.
                                                    Default: False

                register_with_new_name (bool):  If set to true the client shall be registered with a new name.
                (Optional)                          Default: False

                wait_for_reinstalled_client (bool):
                (Optional)                      If set to true wait for the client to be activated post re-install.
                                                    Default: False

                Machine_object (object):        Client Machine object for Machine class
                (Optional)

                Plan  (str):                    Plan name
                (Optional)

            ----------------------------------------------------------------------------------------------------------

        Returns
            client object (obj):    Machine class object for the client

        Raises
            Exception
                - if failed to install client

        """
        try:

            self.tc.log_step("""
                - [{1}]     Install custom package with following parameters
                  [{0}]
            """.format(install_args, install_args['client_host_name']))
            self.installer = Installation.create_installer_object(install_args, self._commcell)
            self.installer.uninstall_existing_instance()
            self.installer.delete_client_from_commcell()
            if self._company_object:
                pre_machine_count = self._company_object.machine_count
            
            
            start = time.time()
            self.installer.install_client()
            end = time.time()
            time_taken = int(end - start)/60
            time_taken = round(time_taken)
            time_taken = str(time_taken) + 'm'            
            self.log.info("Time taken to install packages: {0}".format(time_taken))
            self.update_testcase_details('InstallTime', time_taken)   

            registered_client = client

            if register:
                register_with_client = client
                if registration_args.get('register_with_new_name'):
                    register_with_client = registration_args['new_client_name']

                registered_client = registration_args.get('new_client_name', registered_client)
                start = time.time()
                self.installer.execute_register_me_command(register_with_client=register_with_client,
                                                           client_post_register=registered_client)
                end = time.time()
                time_taken = int(end - start)
                time_taken = round(time_taken)
                time_taken = str(time_taken) + 's'
                self.log.info("Time taken to registration : {0}".format(time_taken))
                self.update_testcase_details('RegistrationTime', time_taken) 
               
            self._commcell.refresh()
            
            # Check activated mode on the client
            start = time.time()
            _ = self.utility.is_regkey_set(registration_args['Machine_object'], "FileSystemAgent", "ActivatedMode", 2, 2, True, 1)
            
            end = time.time()
            time_taken = int(end - start)
            time_taken = round(time_taken)
            time_taken = str(time_taken) + 's'
            self.log.info("Time taken for Activation: {0}".format(time_taken))
            self.update_testcase_details('ActivationTime', time_taken)  
            
            if self._company_object:
                _ = self.organization.is_device_associated(pre_machine_count)
                    
                    
            new_client = registration_args.get('new_client_name')
            client = new_client if new_client else client
            client_obj = self.utility.get_machine_object(client) if new_client else registration_args['Machine_object']

            if install_args.get("LaunchEdgeMonitor") == "true":
                self.is_edge_monitor_running(client_obj)

            # Get subclient's storage policy 
            subclient = self.utils.get_subclient(client)
            self.log.info("Storage Policy associated with default subclient [{0}]".format(subclient.storage_policy))            
            assert subclient.storage_policy == registration_args['Default_Plan'], "Plan validation failed"
            self.log.info("Plan validation for subclient succeeded. subclient associated to Plan's storage policy")

            return client_obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
