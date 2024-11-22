# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Helper file for performing install operations

InstallHelper: Helper class to perform Install operations

InstallHelper:

    wait_for_services()             --  waits for the communication services to come up
                                        on client

    revert_snap()                   --  To revert the snap of a virtual machine

    execute_command()               --  To execute the command on the remote machine using PsExec.exe

    restart_services()              --  Restart services on the client

    install_software()              --  Install specific feature packages on a client

    uninstall_client()              -- Module to uninstall client and hard delete from commcell

UnixInstallHelper:

    install_software()              --  Install specific feature packages on a client

    uninstall_client()              -- Module to uninstall client and hard delete from commcell

    silent_install()                -- Unattended installation of client based on feature release

    restart_services()              --  Restart services on the client

WindowsInstallHelper:

    install_software()              --  Install specific feature packages on a client

    uninstall_client()              -- Module to uninstall client and hard delete from commcell

    silent_install()                -- Unattended installation of client based on feature release

    restart_services()              --  Restart services on the client

"""
import os
import time
import socket
import subprocess
from base64 import b64encode
from datetime import datetime
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils import database_helper
from AutomationUtils import config, constants
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.options_selector import OptionsSelector
from Install import installer_utils, installer_constants
from Install.bootstrapper_helper import BootstrapperHelper
from Install.silent_install_helper import SilentInstallHelper
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class InstallHelper:
    """Helper class to perform  install operations"""

    def __new__(cls, commcell, machine_obj=None, tc_object=None):
        """
        Returns the respective class object based on the platform OS

        Args:
           commcell   -- commcell object

           machine_obj -- machine object

           tc_object  --  testcase object

        Returns (obj) -- Return the class object based on the OS

        """
        if cls is not __class__ or machine_obj is None:
            return super().__new__(cls)

        if 'windows' in machine_obj.os_info.lower():
            return object.__new__(WindowsInstallHelper)

        elif 'unix' in machine_obj.os_info.lower():
            return object.__new__(UnixInstallHelper)

    def __init__(self, commcell, machine_obj=None, tc_object=None):
        """
        constructor for install related files
        """
        self.log = logger.get_log()
        self.commcell = commcell
        try:
            self.commserv = "" if commcell is None else self.commcell.commserv_client
        except Exception as exp:
            self.log.info("soft error incase of metallic cases")
            self.log.warning(exp)
        self.machine = Machine()
        self.config_json = config.get_config()
        self.options_selector = "" if commcell is None else OptionsSelector(self.commcell)
        self.client_machine_obj = machine_obj
        self.test_results_path = constants.TEMP_DIR
        self.tc_object = tc_object
        self.starttime = None
        self.revision = None

    def wait_for_services(self, wait_time=3600, retry=180, client=None):
        """
        waits for the communication services on client to come up

        Args:
            wait_time  (int)    -- Time to wait for the services to come up

            retry      (int)    -- Retry interval for checking the services

            client     (object) -- client obj

        Returns:
            None

        Raises:
            Exception

            if communication services are down after a threshold time

        """
        self.log.info("waiting for services on the commcell machine")
        myclient = self.commserv
        if client:
            myclient = client
        start_time = time.time()
        while time.time() - start_time < wait_time:
            try:
                if myclient.is_ready:
                    self.log.info(f"communication services are up and running:{myclient}")
                    return
            except Exception:
                continue

            time.sleep(retry)
        raise Exception("Communication services are down")

    def execute_command(
            self,
            hostname=None,
            username=None,
            password=None,
            command=None):
        """
        To execute the command on the remote machine using PsExec.exe

        Args:
            hostname    (str)   -- Full hostname of the machine to execute command on
            username    (str)   -- Username to connect to the machine
            password    (str)   -- Password to connect to the machine
            command     (str)   -- Command to execute on the remote machine

        Returns:
            (int)       -- Return code of the command executed

        """
        exe_path = self.machine.join_path(AUTOMATION_DIRECTORY, 'CompiledBins', 'PsExec.exe')

        command = (f'"{exe_path}"'
                   ' -i 1'
                   f' "\\\\{hostname}"'
                   f' -u "{username}"'
                   f' -p "{password}"'
                   f' {command}')

        return subprocess.call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    def is_controller_machine(self):

        """
        Checks if the machine object is controller

        Returns:
            (boolean)   -- Returns True is machine object is controller else False
        """

        names=[]
        try:
            fqdn = socket.getfqdn()
            ip = socket.gethostbyname(fqdn)
            names.append(fqdn)
            names.append(ip)

        except socket.gaierror:
            ip = socket.gethostbyname(socket.gethostname())
            names.append(ip)

        names.append(socket.gethostname())
        client_hostname = self.client_machine_obj.machine_name

        if client_hostname in names:
            return True
        return False

    def revert_snap(
            self,
            server_name=None,
            username=None,
            password=None,
            vm_name=None,
            snap_name='fresh'):
        """
        To revert the snap of a VM

        Args:
            server_name     (str)   -- Full hostname of the Server machine

            username        (str)   -- Username to login

            password        (str)   -- password of the machine

            vm_name         (str)   -- Name of the VM to revert snap

            snap_name       (str)   -- Snap name to revert the VM to
                                        default: 'fresh'

        """
        if not username and not password:
            machine = Machine(machine_name=server_name, commcell_object=self.commcell)
        else:
            machine = Machine(server_name, username=username, password=password)
        command = {
            "server_name": server_name,
            "vm_name": vm_name,
            "operation": "RevertSnap",
            "extra_args": snap_name,
            "vhd_name": "$null"
        }

        script_path = machine.join_path(
            AUTOMATION_DIRECTORY,
            "VirtualServer",
            "VSAUtils",
            "HyperVOperation.ps1"
        )
        output = machine.execute_script(script_path, command)

        command['operation'] = "PowerOn"
        output = machine.execute_script(script_path, command)

        if '0' in output.formatted_output:
            self.log.info('Successfully reverted VM %s to snap %s', vm_name, snap_name)
            self.log.info('VM is powered on successfully')

            # To wait for the machine to come up
            self.log.info('Sleeping for 3 minutes for the machine %s to be up', vm_name)
            time.sleep(180)
        else:
            self.log.error('Failed to Revert VM %s, please check the logs', vm_name)
            raise Exception(f'Failed to Revert VM {vm_name}, please check the logs')

    def get_machine_objects(self, type_of_machines=0):
        """
            This Method returns the list of machine objects
                Args:
                    type_of_machines    (int)  --  Create Machine Class Object

                            0 : Both the machines (Windows and Unix Machine are created)
                            1: Only Windows Machine is created
                            2: Only Unix Machine is
                            3: Windows 32 bit machine is created
                            default : 0

                Returns:
                    list  -   list of machine objects are returned

                Raise :
                    Exception:
                        - if failed to get the machine object
                        - type_of_machines >2  or <0

                Note:
                    Details to be mentioned on the config.json file under Install.

                        Machine_user_name   (str): Client UserName

                        Machine_password    (str): Client Password

                        Machine_host_name   (str): Client Hostname
        """

        config_json = config.get_config()
        list_of_machine_objects = []

        if type_of_machines not in [0, 1, 2, 3]:
            raise Exception("Type_machines selected invalid")

        if type_of_machines in [0, 1]:
            windows_machine_obj = self.options_selector.get_machine_object(
                machine=config_json.Install.windows_client.machine_host,
                username=config_json.Install.windows_client.machine_username,
                password=config_json.Install.windows_client.machine_password)

            self.log.info("Windows machine object created")
            list_of_machine_objects.append(windows_machine_obj)

        if type_of_machines in [3]:
            windows_machine_obj = self.options_selector.get_machine_object(
                machine=config_json.Install.windows_client32.machine_host,
                username=config_json.Install.windows_client32.machine_username,
                password=config_json.Install.windows_client32.machine_password)

            self.log.info("Windows machine object created")
            list_of_machine_objects.append(windows_machine_obj)

        if type_of_machines in [0, 2]:
            unix_machine_obj = self.options_selector.get_machine_object(
                machine=config_json.Install.unix_client.machine_host,
                username=config_json.Install.unix_client.machine_username,
                password=config_json.Install.unix_client.machine_password)

            self.log.info("Unix machine object created")
            list_of_machine_objects.append(unix_machine_obj)

        return list_of_machine_objects

    def install_software(
            self,
            client_computers=None,
            features=None,
            username=None,
            password=None,
            install_path=None,
            client_group_name=None,
            storage_policy_name=None,
            sw_cache_client=None,
            **kwargs):
        """
                    client_computers    (list)      -- client hostname list

                    features (list of features)   -- list of features to be installed
                                                     default - ['FILE_SYSTEM']

                    username    (str)             -- username of the machine to install features on

                        default : None

                    password    (str)             -- password

                        default : None

                    install_path (str)            -- Software Installation Path

                        default :  None

                    client_group_name (list)        -- List of client groups for the client

                         default : None

                    storage_policy_name (str)       -- Storage policy for the default subclient

                         default : None

                    sw_cache_client (str)           -- Remote Cache Client Name/ Over-riding Software Cache

                        default : None (Use CS Cache by default)

                    **kwargs: (dict) -- Key value pairs for supporting conditional initializations
                    Supported -
                    oem_id (int)                    -- OEM to used for Installation (Metallic/Commvault)
                    install_flags (dict)            -- dictionary of install flag values

                        default : None

                    Ex : install_flags = {"preferredIPfamily":2, "install32Base":True}

                """
        raise NotImplementedError("Module not implemented for the class")

    def install_commserve(self, install_inputs, feature_release, packages=None):
        """
        Installs the Commserve package on the Machine

            Args:
                    install_inputs    (dict)   -- testcase inputs / Dictionary with supported keys

                                         --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                                Windows CS
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)

                                Linux CS
                                commservePassword   (str)        Commserve Password without Encoding/Encrypting

                            Optional:
                                commserveUsername   (str)        Commserve Username
                                useExistingDump     (str)        Use existing dump for Dm2 / Workflow Engine ("0" or 1")
                                useExsitingCSdump   (str)        Use CS dump ("0" or "1")
                                CommservDumpPath    (str)        Dump path for Commserve
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                DM2DumpPath         (str)        Dump path for DM2 webservice
                                WFEngineDumpPath    (str)        Dump path for Workflow Engine
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                sqlSaPassword       (str)        Sa (user) password for SQL access
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                oem_id               (int)       OEM to used for Installation (Metallic/Commvault)


                   feature_release(str) -- feature release of the bootstrapper
                                           eg: SP20, SP21

                   packages(list)       -- list of features to be installed
                                            features=['FILE_SYSTEM', 'MEDIA_AGENT']
                                            default - ['FILE_SYSTEM']

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath

        """
        raise NotImplementedError("Module not implemented for the class")

    def uninstall_client(self, delete_client=True):
        """ Module to uninstall client and hard delete from commcell.
            Deletes the Instance001 associated to the Commcell / Decoupled Client.

         Args:
            delete_client (bool)       : Delete client from commcell?

                                        False : Client in de-configured state on commcell

                                              : Client not part of Commcell (Decoupled Uninstallation)


        Exception:

            Machine Object not created with Credentials.

            If failed to uninstall client

            Failed to delete the client from Commcell : As client not part of commcell (Decoupled Client Instance)


        Note:
            Machine object should always be created with Machine credentials.

                Details to be mentioned on the config.json file under Install.

                        Machine_user_name   (str): Client UserName

                        Machine_password    (str): Client Password

                        Machine_host_name   (str): Client Hostname

            Delete client should be False for Uninstalling decoupled client

        """
        raise NotImplementedError("Module not implemented for the class")

    def silent_install(self, client_name, tcinputs, feature_release=None, packages=None):
        """
        Installs the client on the remote machine depending on the giver user inputs/ Server selected

            Args:
                    client_name (str)    -- Client Name provided for installation

                    tcinputs     (dict)  -- testcase inputs / Dictionary with supported keys

                                         --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                Windows & Unix Client Authentication
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)
                                (OR)
                                authCode            (str)        AuthCode provided for the particular user/company

                                mediaPath           (str)        Filer Path required for Unix installations
                                                                (Path till media)
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                            Optional:
                                commserveUsername   (str)        Commserve Username
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                installDirectoryUnix(str)        Path on which software to be installed on Unix Client
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                clientGroupName(str)             Client Group on the CS
                                networkGateway(str)              Network Gateway flag - client uses to connect to CS
                                force_ipv4(unix)       (int)    0 for both IPv4 and IPv6 support
                                                                1 for IPv4 support only
                                                                2 for IPv6 support only
                                oem_id               (int)       OEM to used for Installation (Metallic/Commvault)


                    feature_release(str) -- feature release of the bootstrapper
                                            eg: SP21, SP22

                    packages(list)       -- list of features to be installed

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath

        """
        raise NotImplementedError("Module not implemented for the class")

    def repair_client(self, **kwargs):
        """
            This method repairs the instance of a commvault client
            **kwargs: (dict)                -- Key value pairs for supporting conditional initializations
            Supported -

            repair_with_creds (bool)        -- Use machine credentials to repair client

                default : False

            reboot_client (bool)            -- boolean to specify whether to reboot the client
                    or not

                default : False

            Returns:
                (bool)  --  returns True or False based on repair job
        """
        try:
            _client_obj = self.commcell.clients.get(self.client_host)
            _username = self.get_machine_creds[0] if kwargs.get('repair_with_creds', False) else None
            _password = b64encode(self.get_machine_creds[1].encode()).decode() if kwargs.get(
                'repair_with_creds', False) else None
            job_obj = _client_obj.repair_software(username=_username, password=_password,
                                                  reboot_client=kwargs.get('reboot_client', False))
            self.log.info(f"Repair job with job id-{job_obj.job_id} started")
            if job_obj.wait_for_completion():
                self.log.info("Repair Job Successful")
                return True
            else:
                self.log.error("Repair Job Failed")
                return False
        except Exception as exp:
            raise Exception(f"Client repair failed with error {exp}")

    def restart_services(self):
        """
            This Method starts the service on the client when the client is not reachable

                Raises:
                SDKException:
                    Response was not success

        """
        raise NotImplementedError("Module not implemented for the class")

    def silent_install_friendly(self, friendly_path):
        """

        """
        if friendly_path[:2] == "//":
            local_path = installer_utils.mount_network_path(friendly_path, self.client_machine_obj, self)
        else:
            local_path = friendly_path
        friendly_list = self.client_machine_obj.get_folders_in_path(local_path, recurse=False)[1:]
        friendly_details_dict = {}
        for friendly_update_path in friendly_list:
            friendly_name = friendly_update_path.split(self.client_machine_obj.os_sep)[-1]
            friendly_details_dict[friendly_name] = installer_utils.get_details_from_friendly(
                self.client_machine_obj, friendly_update_path)

        friendly_names = list(friendly_details_dict.keys())
        service_pack = friendly_details_dict[friendly_names[0]]['ActiveSP'] \
            if friendly_details_dict[friendly_names[0]] else self.config_json.Install.commserve_client.sp_version
        bootstrapper_obj = BootstrapperHelper(feature_release=service_pack, machine_obj=self.client_machine_obj)
        download_inputs = {"download_full_kit": True}
        self.log.info("Downloading Media using Bootstrapper")
        bootstrapper_obj.extract_bootstrapper()
        media_path = bootstrapper_obj.download_payload_from_bootstrapper(download_inputs=download_inputs)
        service_pack_to_install = installer_utils.get_latest_recut_from_xml(service_pack)
        sp_trans_id = service_pack_to_install.split('_')[1]
        cu_number = installer_utils.get_latest_cu_from_xml(service_pack_to_install)
        cu_trans_id = installer_utils.get_cu_trans_id_from_xml(service_pack_to_install, cu_number)
        requires_update_set = set()
        for friendlies in friendly_names:
            friendly_tran_id = friendly_details_dict[friendlies]['TransactionID']
            if friendly_tran_id < sp_trans_id:
                raise Exception(f"Friendly is not applicable to latest recut {service_pack_to_install}. "
                                f"Please refresh and try again")
            if friendly_tran_id > cu_trans_id:
                friendlies_req = friendly_details_dict[friendlies]['REQUIRES'].split(':')
                friendlies_req = [x.split(';')[0] for x in friendlies_req]
                requires_update_set.update(friendlies_req)
        flavour = str(friendly_names[0].split('_')[0]) \
            if 'windows' not in self.client_machine_obj.os_info.lower() else 'BinaryPayload'
        cu_pack_path = self.client_machine_obj.join_path(media_path, flavour, 'LooseUpdates', 'CU'+str(cu_number))
        loose_updates_path = self.client_machine_obj.join_path(cu_pack_path, 'Updates')
        loose_updates_list = self.client_machine_obj.get_folders_in_path(loose_updates_path, recurse=False)[1:]
        cu_hotfix_list = installer_utils.list_hotfixes_in_cu_pack(cu_pack_path, self.client_machine_obj)
        cu_hotfix_list = [x.split('_')[-1] for x in cu_hotfix_list]
        required_updates = []
        for updates in requires_update_set:
            found = 0
            if updates in cu_hotfix_list:
                found = 1
            else:
                for loose_update in loose_updates_list:
                    if updates in loose_update:
                        found = 1
            if found == 0:
                required_updates.append(updates)
        if required_updates:
            raise Exception(f"Missing updates {required_updates}")

        for friendlies in friendly_names:
            destin_path = self.client_machine_obj.join_path(loose_updates_path, friendlies)
            source_path = self.client_machine_obj.join_path(local_path, friendlies)
            self.client_machine_obj.copy_folder(source_path, destin_path, '-r')

        return media_path

    def run_db_query(self, query, user_name, password, dbserver, dbname, retryattempts=3):
        """ runs given query in Database

        Args:
        query (str) -- Database query to execute

        user_name (str) -- Database user name

        password (str) -- Database password

        dbserver (str) -- Database server

        dbname (str) -- Database name

        retryattempts  (int)    --  The number of attempts to retry

        Raises:
        Exception:
        - if failed to update data in DB
        """
        counter = 1
        while counter < retryattempts:
            try:
                mssql = database_helper.MSSQL(dbserver, user_name, password, dbname)
                break
            except Exception as excp:
                self.log.error("Failed to open connection with dbserver:" + dbserver)
                self.log.info("Exception: " + str(excp))
                time.sleep(60)
                counter = counter + 1

        self.log.info("Executing DB query: \n %s", str(query))
        mssql.execute(query)

    def install_acceptance_update(self, status, failure_reason, machine_name, latest_recut=""):
        """ Insert the testcase details in  doInstallAcceptance Table
        Args:

            status (str)               : Test status

            failure_reason (str)      : Failure Reason

        Returns: None
        """

        self.log.info("Updating doInstallAcceptance Table")

        db_table = self.config_json.Install.acceptance_db_creds.db_table
        if self.commcell:
            cs_version = str(self.commcell.version)
            revision = self.sp_revision
            commcell_name = self.commcell.commserv_name
        else:
            cs_version = '11.0.0'
            revision = latest_recut
            commcell_name = '-'
        controller = Machine().machine_name
        client = machine_name

        db_query = r"""UPDATE {} SET 
                           [Commserve] = '{}', 
                           [Client] = '{}', 
                           [CSVersion] = '{}', 
                           [Revision] = '{}', 
                           [Controller] = '{}', 
                           [Result] = '{}', 
                           [FailureReason] = '{}', 
                           [TestCase] = '{}', 
                           [TestName] = '{}', 
                           [Comments] = '{}',
                           [MediaPath] = '{}'
                           WHERE [Date] = '{}'
                               """.format(db_table, commcell_name, client, cs_version, revision,
                                          controller, status, failure_reason, self.tc_object.id,
                                          self.tc_object.name, '', self.tc_object.media_path, self.starttime)

        self.run_db_query(
            query=db_query,
            user_name=self.config_json.Install.acceptance_db_creds.db_username,
            password=self.config_json.Install.acceptance_db_creds.db_password,
            dbserver=self.config_json.Install.acceptance_db_creds.db_server,
            dbname=self.config_json.Install.acceptance_db_creds.dbname
        )

    def install_acceptance_insert(self, status='In Progress'):
        """ Insert the testcase details in  doInstallAcceptance Table
        Args:
            status (str)               : Test status

        Returns: None

        """

        self.log.info("Updating doInstallAcceptance Table")
        db_table = self.config_json.Install.acceptance_db_creds.db_table
        cs_version = str(self.commcell.version) if self.commcell is not None else '-'
        revision = self.sp_revision if self.commcell is not None else '-'
        commcell_name = self.commcell.commserv_name if self.commcell is not None else '-'
        controller = Machine().machine_name
        date = str(datetime.now().strftime("%d %b %Y %H:%M"))
        failure_reason = "-"

        db_query = r"""USE WFENGINE; INSERT INTO {} (Commserve, Client, CSVersion, Revision, Controller, 
        Result, FailureReason, Date, TestCase, TestName, Comments, MediaPath)
                        values
                        ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                        """.format(db_table, commcell_name, commcell_name, cs_version, revision,
                                   controller, status, failure_reason, date, self.tc_object.id,
                                   self.tc_object.name, '', self.tc_object.media_path)
        self.starttime = date

        self.run_db_query(
            query=db_query,
            user_name=self.config_json.Install.acceptance_db_creds.db_username,
            password=self.config_json.Install.acceptance_db_creds.db_password,
            dbserver=self.config_json.Install.acceptance_db_creds.db_server,
            dbname=self.config_json.Install.acceptance_db_creds.dbname
        )
        self.log.info("Marked testcase as InProgress in {0}.format(db_table)")

    @property
    def client_host(self):
        """ Read only attribute for client host """
        raise NotImplementedError(
            'Property Not Implemented by the Child Class')

    @property
    def get_machine_creds(self):
        """ Read only attribute for client host """
        raise NotImplementedError(
            'Property Not Implemented by the Child Class')

    @property
    def sp_revision(self):
        """ Get the revision installed on the CS """

        query = """
            select MAX(S2.RevisionId) FROM PatchSPVersion S join simInstalledPackages P on S.id=P.SPVersionID
            JOIN PatchSPVersion S2 ON S.Release=S2.Release AND S.SPMajor=S2.SPMajor AND S.SPMinor=S2.SPMinor
            AND S.TransactionID=S2.TransactionID and p.ClientId=2
            """
        csdb = database_helper.CommServDatabase(self.commcell)
        database_helper.set_csdb(csdb)
        csdb.execute(query)
        data = csdb.fetch_all_rows()
        self.revision = data[0][0]
        return data[0][0]


class UnixInstallHelper(InstallHelper):
    """Helper class to perform Unix install operations"""

    def __init__(self, commcell, machine_obj=None, tc_object=None):
        """
        Initialises the UnixInstallHelper class

        Args:

            commcell   -- commcell object

            machine_obj -- machine object
        """
        super(UnixInstallHelper, self).__init__(commcell, machine_obj, tc_object)

    def install_software(
            self,
            client_computers=None,
            features=None,
            username=None,
            password=None,
            install_path=None,
            client_group_name=None,
            storage_policy_name=None,
            sw_cache_client=None,
            **kwargs):
        """
            client_computers    (list)      -- client hostname list

            features (list of features)   -- list of features to be installed
                                             default - ['FILE_SYSTEM']

            username    (str)             -- username of the machine to install features on

                default : None

            password    (str)             -- password

                default : None

            install_path (str)            -- Software Installation Path

                default :  None

            client_group_name (list)        -- List of client groups for the client

                 default : None

            storage_policy_name (str)       -- Storage policy for the default subclient

                 default : None

            sw_cache_client (str)           -- Remote Cache Client Name/ Over-riding Software Cache

                default : None (Use CS Cache by default)

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -
            oem_id (int)                    -- OEM to used for Installation (Metallic/Commvault)
            install_flags (dict)            -- dictionary of install flag values

                default : None

            Ex : install_flags = {"preferredIPfamily":2, "install32Base":True}

            db2_logs_location (dict) - dictionary of db2 logs location
            Ex: db2_logs_location = {
                                    "db2ArchivePath": "/opt/Archive/",
                                    "db2RetrievePath": "/opt/Retrieve/",
                                    "db2AuditErrorPath": "/opt/Audit/"
                            }
        """
        if client_computers is None:
            client_computers = [self.client_host]

        if features is None:
            features = ['FILE_SYSTEM']

        feature_vals = []
        for feature in features:
            feature_vals.append(getattr(UnixDownloadFeatures, feature).value)

        if username is None or password is None:
            username = self.config_json.Install.unix_client.machine_username
            password = self.config_json.Install.unix_client.machine_password

        self.log.info("Installing software for features {0} on client {1}".format(features, client_computers))

        return self.commcell.install_software(
            client_computers=client_computers,
            windows_features=None,
            unix_features=feature_vals,
            username=username,
            password=b64encode(password.encode()).decode(),
            install_path=install_path,
            client_group_name=client_group_name,
            storage_policy_name=storage_policy_name,
            sw_cache_client=sw_cache_client,
            **kwargs
        )

    def install_commserve(self, install_inputs, feature_release, packages=None):
        """
        Installs the Commserve package on the Machine
            Args:
                    install_inputs    (dict)   -- testcase inputs / Dictionary with supported keys

                                         --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                                Windows CS
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)

                                Linux CS
                                commservePassword   (str)        Commserve Password without Encoding/Encrypting

                            Optional:
                                commserveUsername   (str)        Commserve Username
                                useExistingDump     (str)        Use existing dump for Dm2 / Workflow Engine ("0" or 1")
                                useExsitingCSdump   (str)        Use CS dump ("0" or "1")
                                CommservDumpPath    (str)        Dump path for Commserve
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                DM2DumpPath         (str)        Dump path for DM2 webservice
                                WFEngineDumpPath    (str)        Dump path for Workflow Engine
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                sqlSaPassword       (str)        Sa (user) password for SQL access
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                oem_id               (int)       OEM to used for Installation (Metallic/Commvault)


                   feature_release(str) -- feature release of the bootstrapper
                                           eg: SP20, SP21, SP28_transaction_DVD

                   packages(list)       -- list of features to be installed
                                            features=['FILE_SYSTEM', 'MEDIA_AGENT']
                                            default - ['FILE_SYSTEM']

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath

        """
        self.log.info("Installing Commserve Package on the Unix machine")
        try:
            client_name = install_inputs.get("csClientName", self.config_json.Install.commserve_client.client_name)

            if packages is None:
                packages = ["COMMSERVE"]

            else:
                packages.append("COMMSERVE")

            package_list = []
            for package in packages:
                package_list.append(getattr(UnixDownloadFeatures, package).value)

            silent_helper = SilentInstallHelper.create_installer_object(client_name,
                                                                        feature_release.upper(),
                                                                        self.client_machine_obj,
                                                                        install_inputs)
            silent_helper.silent_install(package_list)

        except Exception as exp:
            self.log.error("Failed to install commvault software on :%s" % self.client_machine_obj.machine_name)
            raise Exception("\n [{0}]".format(str(exp)))

    def uninstall_client(self, delete_client=True, instance="Instance001"):
        """ Module to uninstall client and hard delete from commcell.
            Deletes the Instance001 associated to the Commcell / Decoupled Client.

         Args:
            delete_client (bool)       : Delete client from commcell?

                                        False : Client in de-configured state on commcell

                                              : Client not part of Commcell (Decoupled Uninstallation)


        Exception:

            Machine Object not created with Credentials.

            If failed to uninstall client

            Failed to delete the client from Commcell : As client not part of commcell (Decoupled Client Instance)


        Note:
            Machine object should always be created with Machine credentials.

                Details to be mentioned on the config.json file under Install.

                        Machine_user_name   (str): Client UserName

                        Machine_password    (str): Client Password

                        Machine_host_name   (str): Client Hostname

            Delete client should be False for Uninstalling decoupled client

        """
        client_hostname = self.client_machine_obj.machine_name
        try:
            # This done to make sure we get the response code after executing on CLI
            if not (self.client_machine_obj.username and self.client_machine_obj.password):
                self.log.info("Creating machine object with credentials")
                self.client_machine_obj = self.options_selector.get_machine_object(
                    machine=self.config_json.Install.unix_client.machine_host,
                    username=self.config_json.Install.unix_client.machine_username,
                    password=self.config_json.Install.unix_client.machine_password)

            if self.is_controller_machine():
                raise Exception("Uninstall of controller should not be attempted")

            self.log.info("Checking if instance exists on client [{0}]".format(client_hostname))
            cmd_to_run = rf'ls -ld /etc/CommVaultRegistry/Galaxy/{instance} 2>/dev/null | wc -l'
            unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

            if "1" in unix_output_obj.output:
                self.log.info(f"Uninstalling existing {instance} on client {client_hostname}")

                if "darwin" in self.client_machine_obj.os_flavour.lower():
                    cmd_to_run = r'echo ' + "\'" + self.client_machine_obj.password + "\'" + \
                                  rf' | sudo -S /usr/local/bin/cvpkgrm -i {instance}'

                else:
                    cmd_to_run = f'/usr/bin/cvpkgrm -i {instance}'

                self.log.info("Executing command [{0}] on client [{1}]"
                              .format(cmd_to_run, client_hostname))

                unix_output_obj = self.client_machine_obj.execute_command(cmd_to_run)

                if not (str(unix_output_obj.exit_code) == "0" or "Password" in str(unix_output_obj.output[0])):
                    raise Exception("Failed to uninstall existing instance on client [{0}]".format(client_hostname))

                if self.client_machine_obj.check_directory_exists('/opt/commvaultDR'):
                    self.client_machine_obj.clear_folder_content('/opt/commvaultDR')

                job_results_dir = 'C:\\Commvault'
                while self.client_machine_obj.check_directory_exists(job_results_dir):
                    self.client_machine_obj.delete_file(job_results_dir)
                    job_results_dir += '1'

                if delete_client:
                    if self.commcell.clients.has_client(client_hostname):
                        client_obj = self.commcell.clients.get(client_hostname)
                        self.options_selector.delete_client(client_obj.client_name, disable_delete_auth_workflow=True)

            else:
                self.log.info("No Instance found on the client [{0}]".format(client_hostname))

            self.log.info("Uninstallation for client [{0}] completed successfully".format(client_hostname))

        except Exception as excp:
            self.log.error("Failed to uninstall existing commvault instance on [{0}]"
                           .format(client_hostname))
            raise Exception("\n [{0}]".format(str(excp)))

    def silent_install(self, client_name, tcinputs, feature_release=None, packages=None):
        """
        Installs the client on the remote machine depending on the giver user inputs/ Server selected

            Args:
                    client_name (str)    -- Client Name provided for installation

                    tcinputs     (dict)  -- testcase inputs / Dictionary with supported keys

                                         --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname
                                mediaPath           (str)        Filer Path required for Unix installations
                                                                (Path till media)

                                Windows & Unix Client Authentication
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)
                                (OR)
                                authCode            (str)        AuthCode provided for the particular user/company

                            Optional:
                                commserveUsername   (str)        Commserve Username
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                installDirectoryUnix(str)        Path on which software to be installed on Unix Client
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                force_ipv4(unix)       (int)     0 for both IPv4 and IPv6 support
                                                                 1 for IPv4 support only
                                                                 2 for IPv6 support only
                                oem_id               (int)       OEM to used for Installation (Metallic/Commvault)


                    feature_release(str) -- feature release of the bootstrapper
                                            eg: SP20, SP21

                    packages(list)       -- list of features to be installed
                                            eg: features=['FILE_SYSTEM', 'MEDIA_AGENT']
                                            default - ['FILE_SYSTEM']
            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath
        """
        self.log.info("Starting installation on Unix Machine")
        try:
            if not (self.client_machine_obj.username and self.client_machine_obj.password):
                self.log.info("Creating machine object with credentials.")
                self.client_machine_obj = self.options_selector.get_machine_object(
                    machine=self.config_json.Install.unix_client.machine_host,
                    username=self.config_json.Install.unix_client.machine_username,
                    password=self.config_json.Install.unix_client.machine_password)

            if feature_release is None:
                feature_release = "SP" + str(self.commcell.commserv_version)

            if packages is None:
                packages = ['FILE_SYSTEM']

            package_list = []
            for package in packages:
                package_list.append(getattr(UnixDownloadFeatures, package).value)

            silent_helper = SilentInstallHelper.create_installer_object(client_name,
                                                                        feature_release.upper(),
                                                                        self.client_machine_obj,
                                                                        tcinputs)
            silent_helper.silent_install(package_list)
            self.commcell.refresh()

        except Exception as exp:
            self.log.error("Failed to install commvault software on :%s" % self.client_machine_obj)
            raise Exception("\n [{0}]".format(str(exp)))

    def restart_services(self):
        """
            This Method starts the service on the client when the client is not reachable

            Raises:
                SDKException:
                    Response was not success

        """

        self.client_machine_obj.execute_command("commvault -all restart")
        client_obj = self.commcell.clients.get(self.client_host)
        if not client_obj.is_ready:
            raise Exception("Failed to restart services on the client:%s", client_obj.client_name)

        self.log.info("Successfully Restarted services on the Client: %s", client_obj.client_name)

    @property
    def client_host(self):
        """ Read only attribute for client host """
        return self.config_json.Install.unix_client.machine_host

    @property
    def get_machine_creds(self):
        """ Read only attribute for client host """
        return (self.config_json.Install.unix_client.machine_username,
                self.config_json.Install.unix_client.machine_password)


class WindowsInstallHelper(InstallHelper):
    """Helper class to perform Windows install operations"""

    def __init__(self, commcell, machine_obj=None, tc_object=None):
        """
        Initialises the WindowsInstallHelper class

        Args:

            commcell   -- commcell object

           machine_obj -- machine object
        """
        super(WindowsInstallHelper, self).__init__(commcell, machine_obj, tc_object)
        self.remote_dir = installer_constants.REMOTE_FILE_COPY_LOC

    def _copy_files_to_client(self, file_name):
        """Copies the created Batch file to the Client Machine
                Args:
                        file_name     (str)  --  Name of the file to be copied to Client
                """

        self.log.info("Copying file [{0}] on Client [{1}] at [{2}]"
                      "".format(file_name, self.client_machine_obj.machine_name, self.remote_dir))
        if not self.client_machine_obj.check_directory_exists(self.remote_dir):
            self.client_machine_obj.create_directory(self.remote_dir)
        self.client_machine_obj.copy_from_local(file_name, self.remote_dir)

        self.log.info("Successfully copied file [{0}] on the client [{1}]"
                      .format(file_name, self.client_machine_obj.machine_name))

    def install_software(
            self,
            client_computers=None,
            features=None,
            username=None,
            password=None,
            install_path=None,
            client_group_name=None,
            storage_policy_name=None,
            sw_cache_client=None,
            **kwargs):
        """
            client_computers    (list)      -- client hostname list

            features (list of features)   -- list of features to be installed
                                            eg: features=['FILE_SYSTEM', 'MEDIA_AGENT']
                                            default - ['FILE_SYSTEM']

            username    (str)             -- username of the machine to install features on

                default : None

            password    (str)             -- password

                default : None

            install_path (str)             -- Software Installation Path

                default : None

            client_group_name (list)        -- List of client groups for the client

                 default : None

            storage_policy_name (str)       -- Storage policy for the default subclient

                 default : None

            sw_cache_client (str)           -- Remote Cache Client Name/ Over-riding Software Cache

                default : None (Use CS Cache by default)

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -
            install_flags (dict)            -- dictionary of install flag values

                default : None

            Ex : install_flags = {"preferredIPfamily":2, "install32Base":True}
        """
        if client_computers is None:
            client_computers = [self.client_host]

        if features is None:
            features = ['FILE_SYSTEM']

        feature_vals = []
        for feature in features:
            feature_vals.append(getattr(WindowsDownloadFeatures, feature).value)

        if username is None or password is None:
            username = self.config_json.Install.windows_client.machine_username
            password = self.config_json.Install.windows_client.machine_password

        self.log.info("Installing software for features {0} on clients {1}".format(features, client_computers))

        return self.commcell.install_software(
            client_computers=client_computers,
            windows_features=feature_vals,
            unix_features=None,
            username=username,
            password=b64encode(password.encode()).decode(),
            install_path=install_path,
            client_group_name=client_group_name,
            storage_policy_name=storage_policy_name,
            sw_cache_client=sw_cache_client,
            **kwargs
        )

    def install_commserve(self, install_inputs, feature_release, packages=None):
        """
        Installs the Commserve package on the Machine

            Args:
                    install_inputs    (dict)   -- testcase inputs / Dictionary with supported keys

                                         --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                                Windows CS
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)

                                Linux CS
                                commservePassword   (str)        Commserve Password without Encoding/Encrypting

                            Optional:
                                commserveUsername   (str)        Commserve Username
                                useExistingDump     (str)        Use existing dump for Dm2 / Workflow Engine ("0" or 1")
                                useExsitingCSdump   (str)        Use CS dump ("0" or "1")
                                CommservDumpPath    (str)        Dump path for Commserve
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                DM2DumpPath         (str)        Dump path for DM2 webservice
                                WFEngineDumpPath    (str)        Dump path for Workflow Engine
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                sqlSaPassword       (str)        Sa (user) password for SQL access
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                oem_id               (int)       OEM to used for Installation (Metallic/Commvault)


                   feature_release(str) -- feature release of the bootstrapper
                                           eg: SP20, SP21 , SP28_transaction_RDVD

                   packages(list)       -- list of features to be installed
                                            features=['FILE_SYSTEM', 'MEDIA_AGENT']
                                            default - ['FILE_SYSTEM']

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath

        """

        self.log.info("Installing Commserve Package on the Windows Machine")
        try:
            client_name = install_inputs.get("csClientName", self.config_json.Install.commserve_client.client_name)

            if packages is None:
                packages = ["COMMSERVE"]

            else:
                packages.append("COMMSERVE")

            package_list = []
            for package in packages:
                package_list.append(getattr(WindowsDownloadFeatures, package).value)

            silent_helper = SilentInstallHelper.create_installer_object(client_name,
                                                                        feature_release.upper(),
                                                                        self.client_machine_obj,
                                                                        install_inputs)
            silent_helper.silent_install(package_list)

        except Exception as exp:
            self.log.error("Failed to install commvault software on :%s" % self.client_machine_obj.machine_name)
            raise Exception("\n [{0}]".format(str(exp)))

    def uninstall_client(self, delete_client=True, instance="Instance001"):
        """ Module to uninstall client and hard delete from commcell.
            Deletes the Instance001 associated to the Commcell / Decoupled Client.

         Args:
            delete_client (bool)       : Delete client from commcell?

                                        False : Client in de-configured state on commcell

                                              : Client not part of Commcell (Decoupled Uninstallation)


        Exception:

            Machine Object not created with Credentials.

            If failed to uninstall client

            Failed to delete the client from Commcell : As client not part of commcell (Decoupled Client Instance)


        Note:
            Machine object should always be created with Machine credentials.

                Details to be mentioned on the config.json file under Install.

                        Machine_user_name   (str): Client UserName

                        Machine_password    (str): Client Password

                        Machine_host_name   (str): Client Hostname

            Delete client should be False for Uninstalling decoupled client

        """
        client_hostname = self.client_machine_obj.machine_name
        try:
            # This done to make sure we get the response code/message after executing on CLI
            if not (self.client_machine_obj.username and self.client_machine_obj.password):
                self.log.info("Creating machine object with credentials.")
                self.client_machine_obj = self.options_selector.get_machine_object(
                    machine=self.config_json.Install.windows_client.machine_host,
                    username=self.config_json.Install.windows_client.machine_username,
                    password=self.config_json.Install.windows_client.machine_password)

            if self.is_controller_machine():
                raise Exception("Uninstall of controller should not be attempted")

            try:
                self.client_machine_obj.execute_command("Restart-Service 'SQL SERVER (COMMVAULT)' -Force")
            except Exception as exp:
                self.log.info(f"Unable to restart SQL Service:{exp}")

            self.log.info("Uninstalling [{0}] on client [{1}]".format(instance, client_hostname))
            command_list = []
            command_list.append(r"SET regPath=%WINDIR%\System32")
            command_list.append(
                "FOR /f \"usebackq tokens=3 skip=2\" %%L IN "
                "(`%regPath%\REG QUERY "
                f"\"HKLM\SOFTWARE\CommVault Systems\Galaxy\{instance}\InstalledPackages\" "
                "/v BundleProviderKey 2^>null`) DO SET bundlekey=%%L")
            command_list.append(
                "IF NOT \"%bundlekey%\"==\"\" "
                "(START \"\" /wait \"%ALLUSERSPROFILE%\Package Cache\%bundlekey%\Setup.exe\" "
                f"/uninstall /silent /instance {instance})"
            )

            self.log.info("Uninstall command: Setup.exe /uninstall /silent /instance {0}".format(instance))

            local_file = os.path.join(self.test_results_path, "cvuninstall.bat")
            install_batch_file = installer_utils.create_batch_file_for_remote(
                commands=command_list, file_name=local_file)
            self._copy_files_to_client(install_batch_file)
            _command = os.path.join(self.remote_dir, os.path.basename(install_batch_file))

            self.log.info("Executing command [{0}] on client [{1}]".format(_command, client_hostname))

            return_code = self.client_machine_obj.execute_command(_command)

            if return_code.exit_code != 0:
                self.log.info("Result String is " + installer_constants.QINSTALLER_RETURNCODES[return_code])
                raise Exception("Failed to uninstall client [{0}].Please check install.log of client"
                                "".format(client_hostname))

            self.log.info("Uninstallation for client [{0}] completed successfully".format(client_hostname))

            if self.client_machine_obj.check_directory_exists('C:\\DR'):
                self.client_machine_obj.clear_folder_content('C:\\DR')

            job_results_dir = 'C:\\Commvault'
            while self.client_machine_obj.check_directory_exists(job_results_dir):
                self.client_machine_obj.delete_file(job_results_dir)
                job_results_dir += '1'

            if delete_client:
                if self.commcell.clients.has_client(client_hostname):
                    client_obj = self.commcell.clients.get(client_hostname)
                    self.options_selector.delete_client(client_obj.client_name, disable_delete_auth_workflow=True)

        except Exception as excp:
            self.log.error("Failed to uninstall existing commvault instance on [{0}]".format(client_hostname))
            raise Exception("\n [{0}]".format(str(excp)))

    def silent_install(self, client_name, tcinputs, feature_release=None, packages=None):
        """
        Installs the client on the remote machine depending on the giver user inputs/ Server selected

            Args:
                    client_name (str)    -- Client Name provided for installation

                    tcinputs    (dict)   -- testcase inputs / Dictionary with supported keys

                                         --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                                Windows & Unix Client Authentication
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)
                                (OR)
                                authCode            (str)        AuthCode provided for the particular user/company

                            Optional:
                                commserveUsername   (str)        Commserve Username
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                installDirectoryUnix(str)        Path on which software to be installed on Unix Client
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                oem_id               (int)       OEM to used for Installation (Metallic/Commvault)


                   feature_release(str) -- feature release of the bootstrapper
                                           eg: SP20, SP21 , Sp28_transaction_RDVD

                   packages(list)       -- list of features to be installed
                                            features=['FILE_SYSTEM', 'MEDIA_AGENT']
                                            default - ['FILE_SYSTEM']

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath

        """
        self.log.info("Starting installation on Windows Machine")
        try:
            if not (self.client_machine_obj.username and self.client_machine_obj.password):
                self.log.info("Creating machine object with credentials.")
                self.client_machine_obj = self.options_selector.get_machine_object(
                    machine=self.config_json.Install.windows_client.machine_host,
                    username=self.config_json.Install.windows_client.machine_username,
                    password=self.config_json.Install.windows_client.machine_password)

            if feature_release is None:
                feature_release = "SP" + str(self.commcell.commserv_version)

            if packages is None:
                packages = ['FILE_SYSTEM']

            package_list = []
            for package in packages:
                package_list.append(getattr(WindowsDownloadFeatures, package).value)

            silent_helper = SilentInstallHelper.create_installer_object(client_name,
                                                                        feature_release.upper(),
                                                                        self.client_machine_obj,
                                                                        tcinputs)
            silent_helper.silent_install(package_list)
            self.commcell.refresh()

        except Exception as exp:
            self.log.error("Failed to install commvault software on :%s" % self.client_machine_obj)
            raise Exception("\n [{0}]".format(str(exp)))

    def restart_services(self):
        """
            This Method starts the service on the client when the client is not reachable

            Raises:
                SDKException:
                    Response was not success

        """
        self.client_machine_obj.restart_all_cv_services()
        client_obj = self.commcell.clients.get(self.client_host)
        if not client_obj.is_ready:
            raise Exception("Failed to restart services on the client:%s", client_obj.client_name)

        self.log.info("Successfully Restarted services on the Client: %s", client_obj.client_name)

    @property
    def client_host(self):
        """ Read only attribute for client host """
        return self.config_json.Install.windows_client.machine_host

    @property
    def get_machine_creds(self):
        """ Read only attribute for client host """
        return (self.config_json.Install.windows_client.machine_username,
                self.config_json.Install.windows_client.machine_password)
