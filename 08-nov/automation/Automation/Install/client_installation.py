# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing Install related operations on Commcell.

Installation,DebianInstallation and WindowsInstallation are the three classes defined.

Installation:   Class for representing all the common methods associated with the Installation

DebianInstallation:   Class for methods specific to deployment of debian client to the commcell

WindowsInstallation:   Class for methods specific to deployment of windows client to the commcell

Installation:

    create_installer_object(inputs ,commcell_obj) -- creates a machine object for the client,
    to get the OS details, then  initialize the class instance accordingly

    __init__(inputs,commcell_object)    --  initialize instance of the Installation class

    client_machine_obj()                --  returns the client machine object where
                                                installation is performed

    commcell_obj()                      --  returns all the commcell object

    automation_obj()                    --  returns the controller machine object

    delete_client_from_commcell()       --  deletes the client from commcell

    validate_installed_client()         --  checks if client is Installed Properly
                                               by performing a readiness check and if the client
                                                is added to the client group

    commcell_install_authcode()         --  Creates a new authcode on commcell for all client installations

    donwload_software()                 --  Initiates Download software on the commcell with specific options

    push_servicepack_and_hotfix()       --  Triggers installation of service pack and hotfixes for the client

    parse_response()                    --  Parses the Sim registration Response

DebianInstallation:

    __init__ (inputs, commcell_obj)     --  Initialize the Debian Client Installation
    class

    local_mount_path()                  --  returns the path where DVD drive to be
                                                mounted

    install_client()                    --  performs the installation of the client
                                                on the target machine

    uninstall_existing_instance()       --  uninstalls the client if an Instance
                                                already exists on the client

    _mount_directory()                  --  Mount the drive on the target machine
                                                where client has to be installed

    _run_installer_command()            --  Runs the command to Trigger Installation
                                                on the client

    execute_register_me_command()       --  Executes the command to register the
                                                client to commserver using register me

WindowsInstallation:

    __init__ (inputs, commcell_obj)     --  Initialize the Debian Client Installation
    class

    _set_error_level()                  --  Appends the default commands to get
                                                the exitcode from batch file

    _mount_network_drive()              --  Appends the default commands to mount
                                                a network drive on windows client

    install_client()                    --  Performs the installation of the client
                                                on the target machine

    uninstall_existing_instance()       --  Uninstalls the client if an Instance
                                                already exists on the client

    _mount_directory()                  --  Mount the drive on the target machine
                                                where client has to be installed

    _build_batch_file()                 --  Creates a batch file with all the
                                                commands needed for Installation

    _build_batch_file_interactive()     --  Creates a batch file with all the
                                                commands needed for interactive installation

    _build_json()                       --  Builds a json file with all the values as dict
                                                needed for the interactiveinstallation.exe

    _get_command_to_run()               --  gets the command needed to trigger
                                                the installation on the client

    _copy_files_to_client()             --  Copies the created batch file to
                                                the client machine

    _run_installer_command()            --  Runs the command to Trigger Installation
                                                on the client

    execute_register_me_command()       --  Executes the command to register the
                                                client to commserver using register me

    uninstall_existing_instance()       --  Uninstalls the existing Instance on the client

    install_client()                    --  Installs a client
"""
import os
import time
import re
import inspect
import subprocess
import json
import xmltodict

from cvpysdk.deployment.deploymentconstants import DownloadOptions

from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager
from Install import installer_utils, installer_constants


class Installation(object):
    """Class for performing Install operations on a remote client."""

    @staticmethod
    def create_installer_object(inputs, commcell_object):
        """Returns the instance of one of the Subclasses WindowsInstallation /
        DebianInstallation based on the OS details of the remote client.

        creates a machine object to the client to determine if it is a windows
        or mac client then creates respective client subclass object

        """
        client_machine = Machine(inputs['client_host_name'],
                                 username=inputs['client_user_name'],
                                 password=inputs['client_password'])

        if client_machine.os_info == 'WINDOWS':
            obj = WindowsInstallation(inputs, commcell_object)
        else:
            obj = DebianInstallation(inputs, commcell_object)

        obj.client_machine_obj = client_machine
        return obj

    def __init__(self, inputs, commcell_obj):
        """Initialize the Installation class instance for performing Install related
            operations.

            Args:
                commcell_object
                       (object)    --  Instance of the Commcell class

                inputs (dict)
                    --  Inputs for Installation
                            Supported key / value for inputs:
                            Mandatory:
                                client_name:        (str)        Client name
                                client_host_name:   (str)        Client host name
                                client_user_name:   (str)        Client user name to access client
                                client_password:    (str)        Client password to access client
                                executable_name:    (str)        Executable name of the Custom package
                                package_location:   (str)        Custom package executable directory path
                            Optional:
                                Tenant_company:     (str)        Organization (company) name
                                registering_user:   (str)        User name for registering user
                                registering_user_password
                                                    (str)        Password for registering user
                                organization_object:(object)     Tenant organization object
                                install_authcode:   (str)        Silent install with authcode
                                delete_client:      (bool)       If False, will skip deleting the client on commcell
                                register_auth_code: (str)        If provided register with this AuthCode with Sim
                                client_hostname: (str)           Client will be registered with this hostname
                                endpointurl: (str)               Endpoint URL
                                registration_time_limit (str)    registration time limit
            Returns:
                object  -   instance of the Installation class

        """
        self.log = logger.get_log()

        # Mandatory inputs:
        self.client_host_name = inputs.get('client_host_name')
        self.client_user_name = inputs.get('client_user_name')
        self.client_password = inputs.get('client_password')
        self.client_name = inputs.get('client_name')
        self.executable_name = inputs.get('executable_name')

        # Optional inputs:
        self.registering_user = inputs.get('registering_user')
        self.registering_user_password = inputs.get('registering_user_password')
        self.commserv_host_name = commcell_obj.commserv_hostname
        self.commserv_client_name = commcell_obj.commserv_name
        self.tenant_object = inputs.get('organization_object')
        if inputs.get("Tenant_company") is not None:
            self.tenant_client_group = inputs.get("Tenant_company") + " clients"
        self.hard_delete_client = inputs.get('delete_client', True)
        self.register_auth_code = inputs.get('register_auth_code')
        self.change_client_hostname = inputs.get('client_hostname')
        self.endpointurl = inputs.get('endpointurl')
        self.install_authcode = inputs.get('install_authcode')
        self.test_results_path = inputs.get('package_location', constants.TEMP_DIR)
        self.register_with_authcode = inputs.get('install_with_authcode')
        self.register_with_SAML = inputs.get('register_with_SAML')
        self.takeover_client = inputs.get('takeover_client')
        self.backupnow = inputs.get('BackupNow')
        self.saml_email = inputs.get('saml_email')
        self.register_with_authcode = inputs.get('install_with_authcode')
        self.registration_time_limit = inputs.get('registration_time_limit')
        self.install_type = inputs.get('install_type')
        self._commcell_obj = commcell_obj
        self.command_list = []
        self.timestamp = installer_utils.get_current_time()
        self._client_machine_obj = None
        self._automation_obj = None
        self.result_string = None
        self.installer_path = None
        self.installer_path_password = None
        self.installer_path_username = None
        self.json_file = None
        self._utility = OptionsSelector(self._commcell_obj)

    def delete_client_from_commcell(self):
        """Deletes the client from commcell if a client with the same name is
            present in the commcell console."""

        if not self.hard_delete_client:
            self.log.info("Skipping client deletion from commcell.")
            return 0

        self._utility.delete_client(self.client_name)

        if self.tenant_object is not None:
            # Refresh organization properties after deleting the clients.
            self.log.info("Refreshing properties for tenant [{0}].".format(self.tenant_object))
            self.tenant_object.refresh()

    def validate_installed_client(self):
        """
        Performs the following validations to validate client Installation
            1: check Readiness.
            2: check if the client is added to the client group specified.

        Raises:
                Exception  - if the client is not registered in Organization
        """

        CommonUtils(self.commcell_obj).check_client_readiness([self.client_name])

        self.log.info("Validating if client [{0}] is part of tenant client group [{1}]"
                      "".format(self.client_name, self.tenant_client_group))

        client_group_obj = self.commcell_obj.client_groups.get(self.tenant_client_group)
        clients_in_client_group = client_group_obj.associated_clients

        if not self.client_name in clients_in_client_group:
            raise Exception('Client is not registered to the organization')

    def commcell_install_authcode(self):
        """ Creates a new authcode on commcell for all client installations
            This is independent of the Organization as this generates an auth code with organization id as 0
            AC->Administration->Commcell"""

        self.log.info("Creating a new Auth Code at Commcell level for client installations")

        new_auth_code = self._commcell_obj.enable_auth_code()

        self.log.info("New installation Auth Code for Commcell = [%s]", new_auth_code)

        return new_auth_code

    def download_software(self, options=None, os_list=None, service_pack=None):
        """ Initiates Download software on the commcell with specific options

            Args:
                options      (enum)            --  Download option to download software
                                                    Default : DownloadOptions.LATEST_HOTFIXES.value

                os_list      (list of enum)    --  list of windows/unix packages to be downloaded

                service_pack (int)             --  service pack to be downloaded

            Returns:
                object  -   Instance of Job Class for the given job id

        """
        try:
            if options is None:
                options = DownloadOptions.LATEST_HOTFIXES.value
            download_job = self._commcell_obj.download_software(options=options, os_list=os_list)
            self.log.info("Job %s started for downloading packages", download_job.job_id)
            _ = JobManager(download_job, self._commcell_obj).wait_for_state()
            return download_job

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def push_servicepack_and_hotfix(self, reboot_client=False, run_db_maintenance=True):
        """Triggers installation of service pack and hotfixes for the client

        Args:
            reboot_client (bool)            -- boolean to specify whether to reboot the client or not
                                                default: False

            run_db_maintenance (bool)      -- boolean to specify whether to run db maintenance not
                                                default: True

        Returns:
            object - instance of the Job class for this install job

        Raises:
            Exception:
        """
        try:
            client_obj = self._commcell_obj.clients.get(self.client_name)
            install_job = client_obj.push_servicepack_and_hotfix(reboot_client, run_db_maintenance)
            self.log.info("Job %s started for Installing packages", install_job.job_id)
            _ = JobManager(install_job, self._commcell_obj).wait_for_state()
            return install_job

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def parse_response(self, response):
        """ Parses the Sim registration Response

        Args:
            response (str) : Sim Registration response

        Returns:
            None

        Raises:
            Exception:
            - If failed to parse Sim Call Wrapper response
        """
        if 'clientComposition' in response:
            error_code = int(response['clientComposition']['clientError'].get('@ErrorCode'))
            error_string = response['clientComposition']['clientError'].get('@ErrorString')
            if 'userActivationInfo' in response['clientComposition']:
                activation_details = response['clientComposition']['userActivationInfo']['@activationDetails']
                self.log.info("""
                    Activation response:    [{0}]""".format(activation_details)
                )
                activation_response = xmltodict.parse(activation_details)
                if 'App_ActivateClientResp' in activation_response:
                    if 'error' in activation_response['App_ActivateClientResp']:
                        actv_error = int(activation_response['App_ActivateClientResp']['error'].get('@errorCode'))
                        actv_errorstring = activation_response['App_ActivateClientResp']['error'].get('@errorMessage')
                        error_code = actv_error if actv_error != 0 else error_code
                        if actv_errorstring:
                            self.log.error("Activation error: [{0}]".format(actv_errorstring))
                            error_string = actv_errorstring
        elif 'SimError' in response:
            error_code = int(response['SimError'].get('@ErrorCode'))
            error_string = response['SimError'].get('@ErrorString')
        else:
            self.log.error("Sim Response does not contain client side composition or any sim errors")
            raise Exception("Failed to parse SimCallWrapper output")

        # Check error code and error string from the SimCallWrapper output.
        if error_code != 0 or error_string:
            self.log.error("SimCallWrapper ErrorCode [{0}]. Client ErrorString: [{1}]".format(error_code, error_string))
            raise Exception("Client Registration failed with error [{0}]".format(error_string))

    @property
    def client_machine_obj(self):
        """Returns the client machine object if it not already initialized"""
        if self._client_machine_obj is None:
            self._client_machine_obj = Machine(self.client_host_name,
                                               username=self.client_user_name,
                                               password=self.client_password)
        return self._client_machine_obj

    @client_machine_obj.setter
    def client_machine_obj(self, value):
        self._client_machine_obj = value

    @property
    def commcell_obj(self):
        """Returns the commcell object."""
        return self._commcell_obj

    @property
    def automation_obj(self):
        """Creates and Returns the Machine object of the current machine where automation
        is currently running.
        """
        if self._automation_obj is None:
            import socket
            self._automation_obj = Machine(socket.gethostname())
        return self._automation_obj

class DebianInstallation(Installation):
    """Class for performing Install operations on a debian/Mac client."""

    def __init__(self, inputs, commcell_obj):
        """Initialize the Installation class instance for performing Install related
            operations.

            Args:
                commcell_object     (object)    --  instance of the Commcell class

                inputs (dict)
                    --  Inputs for Installation
                            Supported key / value for inputs:
                            Mandatory:
                                client_name:        (str)        Client name
                                client_host_name:   (str)        Client host name
                                client_user_name:   (str)        Client user name to access client
                                client_password:    (str)        Client password to access client
                                executable_name:    (str)        Executable name of the Custom package
                                package_location:   (str)        Custom package executable directory path
                            Optional:
                                Tenant_company:     (str)        Organization (company) name
                                registering_user:   (str)        User name for registering user
                                registering_user_password
                                                    (str)        Password for registering user
                                organization_object:(object)     Tenant organization object
                                install_authcode:   (str)        Silent install with authcode
                                delete_client:      (bool)       If False, will skip deleting the client on commcell
                                register_auth_code: (str)        If provided register with this AuthCode with Sim
                                client_new_hostname (str)            Client will be registered with this hostname
                                endpointurl: (str)               Endpoint URL
                                registration_time_limit (str)    registration time limit

            Returns:
                object  -   instance of the DebianInstallation class

        """
        super(DebianInstallation, self).__init__(inputs, commcell_obj)
        self._local_mount_path = None

    def _copy_files_to_client(self, file_name, overwrite=True):
        """Copies the created Batch file to the Client Machine
        Args:
                file_name     (str)  --  Name of the file to be copied to Client
                
                overwrite     (bool) --  Overwrite existing file.
        """

        file_path = self.client_machine_obj.os_sep.join([self.local_mount_path, os.path.basename(file_name)])
        if not overwrite and self.client_machine_obj.check_file_exists(file_path):
            self.log.info("File [{0}] exists on the client [{1}]".format(file_path, self.client_host_name))
            return True
        
        self.log.info("Copying file [{0}] on Client [{1}] at [{2}]"
                      "".format(file_name, self.client_host_name, self.local_mount_path))

        self.log.info("Creating Mount path [{0}] to copy the package".format(self.local_mount_path))        
        
        cmd_to_run = "mkdir -p %s" % self.local_mount_path
        unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

        if unix_output_obj.exit_code != 0:
            self.log.error("Unable to create mount path on the remote machine")
        else:
            cmd_to_run = 'umount ' + self.local_mount_path

            self.log.info("""Unmounting the network drive if it is already mounted
                            Executing command : [{0}]""".format(cmd_to_run))

            unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)
            if unix_output_obj.exit_code != 0:
                self.log.info("Failed to unmount %s" % unix_output_obj.output)

        self.client_machine_obj.copy_from_local(file_name, self.local_mount_path)

        self.log.info("Successfully copied file [{0}] on the client [{1}] at [{2}]"
                      "".format(file_name, self.client_host_name, self.local_mount_path))

    def _mount_directory(self):
        """Mounts the DVD location on the client machine
            Installer is always triggered from the mounted drive
        """
        self.log.info("Creating Mount Directory to mount the Pkg Location")
        cmd_to_run = "mkdir -p %s" % self.local_mount_path
        unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

        if unix_output_obj.exit_code != 0:
            self.log.info("WARNING: unable to create mount directory on the remote machine")
        else:
            self.log.info("Unmounting the network drive if it is already mounted")
            cmd_to_run = 'umount ' + self.local_mount_path
            unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

            if unix_output_obj.exit_code != 0:
                self.log.error("Unable to mount ENG share with error %s" % unix_output_obj.output)

            self.log.info("Mounting ENG share at location: %s" % self.local_mount_path)
            cmd_to_run = "mount_smbfs '//" + self.installer_path_username.split('\\')[0] + ";" + \
                         self.installer_path_username.split('\\')[1] + ":" + \
                         self.installer_path_password + "@%s' %s" % (
                             self.installer_path.replace('\\', '/').replace('//', ''),
                             self.local_mount_path)
            unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

            if unix_output_obj.exit_code != 0:
                self.log.error("Unable to mount ENG share with error" + unix_output_obj.output)
                raise Exception("Failed while running the mount command")

    def _run_installer_command(self):
        """Runs the command to  trigger commvault Installation package on the client
        machine.
        """
        cmd_to_run = r'echo ' + "\'" + \
                     self.client_password + "\' " + "| " + \
                     r'sudo -S installer -pkg ' + \
                     self.local_mount_path + r'/' + \
                     self.executable_name + ' ' +\
                     r'-target /'

        self.log.info("Executing Laptop package Install command:%s on Host:%s" % (cmd_to_run, self.client_host_name))

        unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

        if unix_output_obj.exit_code == 0:
            self.log.info("Installation on host: %s succeeded" % self.client_host_name)
        else:
            self.log.error("Package installation failed on Host: %s with error %s" % (
                self.client_host_name, unix_output_obj.output))

    def install_client(self):
        """Installs the client on the remote machine depending on the giver user inputs"""

        try:
            self.log.info("Starting installation on client [{0}]".format(self.client_host_name))

            self._copy_files_to_client(os.path.join(self.test_results_path, self.executable_name))
            self.create_ini_file_with_auth_code()
            self._run_installer_command()

            self.log.info("Installing Custom package completed successfully for [{0}]".format(self.client_host_name))

            # Observed that mac client takes some time to activate. adding some sleep time here, before moving ahead.
            self._utility.sleep_time(60)

        except Exception as err:
            self.log.exception("Client install failed: %s" % str(err))
            raise err

    def create_ini_file_with_auth_code(self):
        ini_file = r"/Library/Application Support/Commvault/install.ini"
        if self.install_authcode:
            # In case of authcode install, create file for Mac.
            self._utility.create_directory(self.client_machine_obj, r"/Library/Application Support/Commvault")
            self.client_machine_obj.delete_file(ini_file)
            self.client_machine_obj.create_file(ini_file, r'AUTH_CODE="'+self.install_authcode+'"')
        else:
            # Else, delete the file for sim registration
            self.client_machine_obj.delete_file(ini_file)

    def uninstall_existing_instance(self):
        """Uninstalls the existing Instance on the client
        By default instance that is picked is Instance001
        """

        self.log.info("Checking if instance exists on client [{0}]".format(self.client_host_name))
        cmd_to_run = r'ls -ld /etc/CommVaultRegistry/Galaxy/Instance001 2>/dev/null | wc -l'
        unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)
        JobManager(commcell=self._commcell_obj).kill_active_jobs(self.client_name)

        if "1" in unix_output_obj.output:
            self.log.info("Uninstalling existing instance on client [{0}]".format(self.client_host_name))

            cmd_to_run = r'echo ' + "\'" + self.client_password + "\'" + \
                         r' | sudo -S /usr/local/bin/cvpkgrm -i Instance001'

            self.log.info("Executing command [{0}] on client [{1}]".format(cmd_to_run, self.client_host_name))

            unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

            if not (str(unix_output_obj.exit_code) == "0" or "Password" in str(unix_output_obj.output[0])):
                raise Exception("Failed to uninstall existing instance on client [{0}]".format(self.client_name))
        else:
            self.log.info("No Instance found on the client [{0}]".format(self.client_host_name))

        self.log.info("Uninstallation for client [{0}] completed successfully".format(self.client_host_name))

    def execute_register_me_command(
            self, username=None, password=None, client_post_register=None, register_with_client=None
    ):
        """Executes the command to register client to commserver using the RegisterME API

        Args:
            username (str)    : Username for the user to register the client

            password (str)    : Password for the user

            client_post_register (str): In some install scenarios like reinstall and registration of an existing
                                    locally uninstalled client, the actual client name may change post registration.
                                    In such cases need to pass the expected client name post registration.

            register_with_client (str): This is the client name with which to register the client.

        Returns:
            None

        Raises:
            Exception:
                - if Failed to run SIMCallWrapper.exe for Registering the client
                - if SIMCallWrapper Execution failed
        """

        username = self.registering_user if username is None else username
        password = self.registering_user_password if password is None else password
        register_with_client = self.client_name if register_with_client is None else register_with_client
        base_path = self.client_machine_obj.get_registry_value("Base", "dBASEHOME")
        output_file = self.local_mount_path + r'RegisterME_output.xml'

        if self.register_auth_code:
            registration_source = " -authcode " + self.register_auth_code
        else:
            registration_source = " -user " + "\"" + username + "\"" +" -password " + "\'" + password + "\'"

        if self.change_client_hostname is not None:
            client_hostname = self.change_client_hostname
        else:
            client_hostname = self.client_host_name

        simcallwrapper = self.client_machine_obj.os_sep.join([base_path, installer_constants.SIM_CALL_WRAPPER_EXE_UNIX])

        if self.endpointurl:
            endpointstring = " -url " + self.endpointurl
        else:
            endpointstring = " -CSHost " + self.commserv_host_name
                    
        sim_cmd = r'sudo -u ' + self.client_user_name + ' ' + simcallwrapper + ' ' +\
                     "-OpType 1000" + registration_source + endpointstring + \
                     " -clientname " + register_with_client + " -ClientHostName " + client_hostname + \
                     " -registerme -output " + output_file

        self.log.info("Executing command [{0}] on client [{1}]".format(sim_cmd, self.client_host_name))

        start = time.time()
        return_code = self.client_machine_obj.execute_command(sim_cmd)
        end = time.time()
        registration_time = int(end - start)
        registration_time_seconds = round(registration_time)
        registration_time = str(registration_time_seconds) + 's'
        self.log.info("Time taken for registration : {0}".format(registration_time))
        if registration_time_seconds > int(self.registration_time_limit):
            raise Exception("Time taken for registration:{0}, which is greater than {1}".format(registration_time, str(self.registration_time_limit)))
                
        output = return_code.formatted_output

        self.log.info("Output obtained from running Register me is:" + str(output))
        self.log.info("SimCallWrapper output for file [{0}] on client [{1}]".format(output_file, self.client_host_name))

        if not self.client_machine_obj.check_file_exists(output_file):
            self.log.error("SimCallWrapper output file [{0}] does not exist.".format(output_file))

        file_output = self.client_machine_obj.read_file(output_file)
        self.log.info("""
            Output: {0}""".format(file_output))
        _response = xmltodict.parse(file_output)['CVInstallManager_ClientSetup']
        self.parse_response(_response)

        # Validate SimCallWrapper output
        if return_code.exit_code != 0:
            self.log.error("SimCallWrapper execution failed.")
            raise Exception("Failed to run SIMCallWrapper for registering the client")

        # If new client is expected to be registered and activated it should be present in the SimCallWrapper
        # execution response.
        if client_post_register and not re.search(client_post_register, file_output):
            self.log.error("New client name [{0}] not found in SimCallWrapper Response".format(client_post_register))

        self.log.info("SIMCallWrapper executed successfully")

        self._utility.sleep_time(10)

        return {'registration_time': registration_time}
    
    @property
    def local_mount_path(self):
        """Returns the default mount location to mount the DVD Path"""
        if self._local_mount_path is None:
            self._local_mount_path = r'/Users/' + self.client_user_name + r'/autoeng/'
        return self._local_mount_path

class WindowsInstallation(Installation):
    """Class for performing Install operations on a Windows client."""

    def __init__(self, inputs, commcell_obj):
        """Initialize the Installation class instance for performing Install related
            operations.

            Args:
                commcell_object     (object)    --  instance of the Commcell class

                inputs (dict)
                    --  Inputs for Installation
                            Mandatory:
                                client_name:        (str)        Client name
                                client_host_name:   (str)        Client host name
                                client_user_name:   (str)        Client user name to access client
                                client_password:    (str)        Client password to access client
                                executable_name:    (str)        Executable name of the Custom package
                                package_location:   (str)        Custom package executable directory path
                            Optional:
                                Tenant_company:     (str)        Organization (company) name
                                registering_user:   (str)        User name for registering user
                                registering_user_password
                                                    (str)        Password for registering user
                                organization_object:(object)     Tenant organization object
                                install_authcode:   (str)        Silent install with authcode
                                delete_client:      (bool)       If False, will skip deleting the client on commcell
                                register_auth_code: (str)        If provided register with this AuthCode with Sim
                                client_new_hostname (str)            Client will be registered with this hostname
                                endpointurl: (str)               Endpoint URL
                                registration_time_limit (str)    registration time limit

            Returns:
                object  -   instance of the WindowsInstallation class

        """
        super(WindowsInstallation, self).__init__(inputs, commcell_obj)
        self.install_batch_file = None
        self.remote_dir = installer_constants.REMOTE_FILE_COPY_LOC
        self.interactiveinstall_exe_path = installer_constants.INTERACTIVE_INSTALL_EXE_PATH
        self._install_options = " /wait /silent /install /silent"

        if inputs.get('install_authcode') is not None:
            self._install_options += " /authcode {0}".format(inputs['install_authcode'])

    def _set_error_level(self):
        """Set the error level and errcode in batch script"""

        set_error_level = "set exitcode=%ERRORLEVEL%" + installer_utils.output_pipe_path_inside_batch()
        get_exit_code = "EXIT %exitcode%" + installer_utils.output_pipe_path_inside_batch()
        self.command_list.extend([set_error_level, get_exit_code])

    def _mount_network_drive(self):
        """appends the regular commands to mount a network drive in a batch file"""

        net_use_disconnect = "net use * /D /Y" + installer_utils.output_pipe_path_inside_batch()
        net_use = "net use * \"" + self.installer_path + "\"" + " " + \
                  self.installer_path_password + " /USER:" + \
                  self.installer_path_username + installer_utils.output_pipe_path_inside_batch()
        get_drive_letter = "for /f \"tokens=2\" %%i in (\'net use * \"" + self.installer_path + \
                           "\" ^| find \"is now connected\"\') do set netdrive=%%i"
        self.command_list.extend([net_use_disconnect, net_use, get_drive_letter])

    def _build_batch_file(self):
        """Build Batch script for windows Package Installation"""

        self.log.info("Creating batch script for installation on client [{0}]".format(self.client_host_name))


        self.command_list = []

        if not installer_utils.is_path_local(self.installer_path):
            self._mount_network_drive()

        self._get_command_to_run()
        self._set_error_level()
        local_file = os.path.join(self.test_results_path, "cvinstall.bat")
        self.install_batch_file = installer_utils.create_batch_file_for_remote(
            commands=self.command_list, file_name=local_file)

        self.log.info("Successfully created batch script [{0}]".format(self.install_batch_file))


    def _build_batch_file_interactive(self):
        """Build Batch script for windows Package Installation"""

        self.log.info("Creating batch script for interactive installation on client [{0}]".format(self.client_host_name))
        command_list = []
        path = self.installer_path + "\\" + self.executable_name
        local_file = os.path.join(self.test_results_path, "cvinstall.bat")
        self._build_json()
        self._copy_files_to_client(self.interactiveinstall_exe_path)
        exe_path = os.path.join(self.remote_dir, os.path.basename(self.interactiveinstall_exe_path))
        command_list.append(exe_path + ' -PLAY "'+self.json_file+'" -PATH "'+path+'"')
        self.install_batch_file = installer_utils.create_batch_file_for_remote(
            commands=command_list, file_name=local_file)

        self.log.info("Successfully created batch script [{0}]".format(self.install_batch_file))

    def _build_json(self):
        """Build json for windows Package Interactive Installation"""

        self.log.info("Creating json for interactive installation on client [{0}]".format(self.client_host_name))
        self.json_file = os.path.join(self.test_results_path, "installation_%s.json" % self.timestamp)
        data_dict = {
            'LaptopUserName': self.registering_user,
            'LaptopUserPassword': self.registering_user_password,
            'clientName': self.client_name,
            'installMode': 1,
            'IsInstallingFromCustomPackage': True,
            'IsBootstrapper': True,
            "IsBootStrapMode": True,
            "RegisterLaptopClient": True,
            "register_with_authcode": self.register_with_authcode,
            "authcode": self.install_authcode,
            "register_with_SAML": self.register_with_SAML,
            "saml_email": self.saml_email,
            "takeover_client": self.takeover_client,
            "BackupNow": self.backupnow}

        with open(self.json_file, 'w') as outfile:
            json.dump(data_dict, outfile)
        self._copy_files_to_client(self.json_file)
        self.json_file = os.path.join(self.remote_dir, "installation_%s.json" % self.timestamp)
        #self.client_machine_obj.create_file(self.json_file, data)
        self.log.info("Successfully created json [{0}]".format(self.json_file))

    def _get_command_to_run(self):
        """Get the command to run for Installation depending on drive location"""

        if not installer_utils.is_path_local(self.installer_path):
            cmd = ("%netdrive%\\" +
                   self.executable_name +
                   self._install_options +
                   installer_utils.output_pipe_path_inside_batch())
        else:
            cmd = (self.installer_path +
                   "\\" +
                   self.executable_name +
                   self._install_options +
                   installer_utils.output_pipe_path_inside_batch())

        self.log.info("Command to execute on client [{0}] is : [{1}]".format(self.client_host_name, cmd))

        self.command_list.append(cmd)

    def _copy_files_to_client(self, file_name, overwrite=True):
        """Copies the created Batch file to the Client Machine
        Args:
                file_name     (str)  --  Name of the file to be copied to Client
                
                overwrite     (bool) --  Overwrite existing file.
        """

        self.log.info("Copying file [{0}] on Client [{1}] at [{2}]"
                      "".format(file_name, self.client_host_name, self.remote_dir))

        file_path = self.client_machine_obj.os_sep.join([self.remote_dir, os.path.basename(file_name)])
        if not overwrite and self.client_machine_obj.check_file_exists(file_path):
            self.log.info("File [{0}] exists on the client [{1}]".format(file_path, self.client_host_name))
            return True
        self._utility.create_directory(self.client_machine_obj, self.remote_dir)
        self.client_machine_obj.copy_from_local(file_name, self.remote_dir)

        self.log.info("Successfully copied file [{0}] on the client [{1}]".format(file_name, self.client_host_name))

    def install_client(self):
        """Installs the client on the given Remote machine """
        try:
            self.log.info("Starting installation process on client [{0}]".format(self.client_host_name))
            taskname = 'install'
            self._copy_files_to_client(os.path.join(self.test_results_path, self.executable_name))
            self.installer_path = self.remote_dir

            if self.install_type:
                self._build_batch_file_interactive()
                self._copy_files_to_client(self.install_batch_file)
                _cmd = os.path.join(self.remote_dir, os.path.basename(self.install_batch_file))
                _command = 'psexec \\\\' + self.client_host_name + \
                    r' -u ' + self.client_user_name + \
                    ' -p ' + self.client_password + \
                    ' -i 1' + \
                    ' "' + _cmd + '" -accepteula'

                self.log.info("Executing command [{0}] on client [{1}]".format(_command, self.client_name))
                self.log.info(_command)
                self.log.info(subprocess.check_output(_command, timeout=20000))
                self.log.info("Client installation and Activation succeeded through EdgeMonitor App")
            else:
                self._build_batch_file()
                self._copy_files_to_client(self.install_batch_file)
                install_cmd = os.path.join(self.remote_dir, os.path.basename(self.install_batch_file))

                task_options = ''.join([r'/RU "NT AUTHORITY\SYSTEM"',
                                        " /SC Hourly /TN \"" + taskname + "\" /TR \"" + install_cmd + "\""])
                output = self.client_machine_obj.create_task(task_options)
                _ = self.client_machine_obj.execute_task(taskname)
                self._utility.sleep_time(10, "Give some time for install to proceed")
                _ = self.client_machine_obj.wait_for_task(taskname)
                self.client_machine_obj.delete_task(taskname)

                self.log.info("Deleting batch file [{0}]".format(self.install_batch_file))

                self.automation_obj.delete_file(self.install_batch_file)

                self.log.info("Installing Custom package completed successfully for [{0}]".format(self.client_host_name))

        except Exception as err:
            self.log.exception("Client install failed: %s" % str(err))
            self.client_machine_obj.delete_task(taskname)
            raise err

    def execute_register_me_command(
            self, username=None, password=None, client_post_register=None, register_with_client=None
        ):
        """Executes the command to register client to commserver using the RegisterME API

        Args:
            username (str)    : Username for the user to register the client

            password (str)    : Password for the user

            client_post_register (str): In some install scenarios like reinstall and registration of an existing
                                    locally uninstalled client, the actual client name may change post registration.
                                    In such cases need to pass the expected client name post registration.

            register_with_client (str): This is the client name with which to register the client.

        Returns:
            None

        Raises:
            Exception:
                - if Failed to run SIMCallWrapper.exe for Registering the client
                - if SIMCallWrapper Execution failed
        """

        username = self.registering_user if username is None else username
        password = self.registering_user_password if password is None else password
        register_with_client = self.client_name if register_with_client is None else register_with_client

        base_path = self.client_machine_obj.get_registry_value("Base", "dBASEHOME")
        base_path = base_path.replace("Program Files", "Progra~1")
        output_file = installer_constants.REGISTER_ME_XML_OP

        if self.register_auth_code:
            registration_source = " -authcode " + self.register_auth_code
        else:
            registration_source = " -user " + username + " -password " + password

        if self.change_client_hostname is not None:
            client_hostname = self.change_client_hostname
        else:
            client_hostname = self.client_host_name

        if self.endpointurl:
            endpointstring = " -url " + self.endpointurl
        else:
            endpointstring = " -CSHost " + self.commserv_host_name
            
        sim_cmd = os.path.join(base_path, installer_constants.SIM_CALL_WRAPPER_EXE) + \
            " -OpType 1000" + registration_source + " -ClientHostName " + client_hostname + \
            " -clientname " + register_with_client + endpointstring + " -registerme -output " + output_file

        self.log.info("Executing command [{0}] on client [{1}]".format(sim_cmd, self.client_host_name))
        
        start = time.time()
        return_code = self.client_machine_obj.execute_command(sim_cmd)
        end = time.time()
        registration_time = int(end - start)
        registration_time_seconds = round(registration_time)
        registration_time = str(registration_time_seconds) + 's'
        self.log.info("Time taken for registration : {0}".format(registration_time))
        if registration_time_seconds > int(self.registration_time_limit):
            raise Exception("Time taken for registration:{0}, which is greater than {1}".format(registration_time, str(self.registration_time_limit)))           
                
        output = return_code.formatted_output

        self.log.info("Output obtained from running Register me is:" + str(output))
        self.log.info("SimCallWrapper.exe output for [{0}] on client [{1}]".format(output_file, self.client_host_name))

        if not self.client_machine_obj.check_file_exists(output_file):
            self.log.error("SimCallWrapper.exe output file [{0}] does not exist.".format(output_file))

        file_output = self.client_machine_obj.read_file(output_file)
        self.log.info("""Output: {0}""".format(file_output))
        _response = xmltodict.parse(file_output)['CVInstallManager_ClientSetup']
        self.parse_response(_response)

        # Validate SimCallWrapper output
        if return_code.exit_code != 0 or not re.search(r'SimCallWrapper completed', output):
            self.log.error("SimCallWrapper execution failed.")
            raise Exception("Failed to run SIMCallWrapper.exe for registering the client")

        # If new client is expected to be registered and activated it should be present in the SimCallWrapper
        # execution response.
        if client_post_register and not re.search(client_post_register, file_output):
            self.log.error("New client name [{0}] not found in SimCallWrapper Response".format(client_post_register))

        self.log.info("SIMCallWrapper executed successfully")

        self._utility.sleep_time(10)
        
        return {'registration_time': registration_time}

    def uninstall_existing_instance(self):
        """Uninstalls the existing Instance on the client
        By default instance that is picked is Instance001
        """
        self.log.info("Uninstalling existing instance on client [{0}]".format(self.client_host_name))

        JobManager(commcell=self._commcell_obj).kill_active_jobs(self.client_name)
        self.command_list = []
        self.command_list.append(r"SET regPath=%WINDIR%\System32")
        self.command_list.append(
            "FOR /f \"usebackq tokens=3 skip=2\" %%L IN "
            "(`%regPath%\REG QUERY "
            "\"HKLM\SOFTWARE\CommVault Systems\Galaxy\Instance001\InstalledPackages\" "
            "/v BundleProviderKey 2^>null`) DO SET bundlekey=%%L")
        self.command_list.append(
            "IF NOT \"%bundlekey%\"==\"\" "
            "(START \"\" /wait \"%ALLUSERSPROFILE%\Package Cache\%bundlekey%\Setup.exe\" "
            "/uninstall /silent /instance Instance001)")

        self.log.info("Uninstall command: Setup.exe /uninstall /silent /instance Instance001")

        self._set_error_level()

        local_file = os.path.join(self.test_results_path, "cvuninstall.bat")
        self.install_batch_file = installer_utils.create_batch_file_for_remote(
            commands=self.command_list, file_name=local_file)
        self._copy_files_to_client(self.install_batch_file, False)
        _command = os.path.join(self.remote_dir, os.path.basename(self.install_batch_file))

        self.log.info("Executing command [{0}] on client [{1}]".format(_command, self.client_host_name))

        return_code = self.client_machine_obj.execute_command(_command)

        if return_code.exit_code != 0:
            self.log.info("Result String is " + installer_constants.QINSTALLER_RETURNCODES[return_code])
            raise Exception("Failed to uninstall client [{0}].Please check install.log of client"
                            "".format(self.client_host_name))

        self.log.info("Uninstallation for client [{0}] completed successfully".format(self.client_host_name))

