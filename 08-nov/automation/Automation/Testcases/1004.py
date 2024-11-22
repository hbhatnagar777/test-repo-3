# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for uploading package to Download Center, and removing existing package with same name

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
import json
import os

from cvpysdk import commcell
from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Install.custom_package import CustomPackageCloudXML
from Install.client_installation import Installation
from Install import installer_constants


class TestCase(CVTestCase):
    """Test case class for testing Download Center Upload and Delete Packages operations."""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("SaaS - New Organization OnBoarding - Package Creation"
                     " and Upload to Download Center")
        self.product = self.products_list.USERDEFINED
        self.feature = self.features_list.USERDEFINED
        self.show_to_user = True
        self.workflow_commcell_obj = None
        self.webserver_machine = None
        self.status = constants.PASSED
        self._automation_obj = None
        self._proxy_default_port = "443"
        self.result_string = ""
        self.tcinputs = {
            "Cloud_Username": None,
            "Cloud_Password": None,
            "Tenant_company": None,
            "Tenant_username": None,
            "Tenant_password": None,
            "Mac_machine_client_name": None,
            "Mac_machine_host_name": None,
            "Mac_machine_user_name": None,
            "Mac_machine_password": None,
            "Windows_machine_client_name": None,
            "Windows_machine_host_name": None,
            "Windows_machine_user_name": None,
            "Windows_machine_password": None
        }

    @property
    def automation_obj(self):
        """
        Creats an object for the current Automation controller using machine clas
        retuens:
            Automation Object (Obj) -- Machine class object for controller
        """
        if self._automation_obj is None:
            import socket
            self._automation_obj = Machine(socket.gethostname())
        return self._automation_obj

    def setup(self):
        """Initializes pre-requisites for test case"""
        log = logger.get_log()
        try:
            web_server = self.commcell.download_center.servers_for_browse[0]
            log.info('Checking if the web server repository is a valid Commcell Client')
            if self.commcell.clients.has_client(web_server):
                log.info('Initializing connection to the client')
                self.webserver_machine = Machine(web_server, self.commcell)
                log.info('Connection to the client initialized successfully')
            else:
                log.error('Web Server is not a valid client')
                raise Exception('Web Server is not a valid client')

        except Exception as excp:
            log.error('Setup for the test case failed. Error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def _upload_to_downloadcenter(self):
        """
        This Method Uploads the custom packages that are created to download center
        """

        log = logger.get_log()
        for each_pkg in installer_constants.PACKAGES_TO_DOWNLOAD.keys():
            _files_to_upload = []
            _package_name = "{0} [Organization: {1}]".format(each_pkg,
                                                             self.tcinputs['Tenant_company'])
            log.info(
                'Check if the package: %s is already exists at Download Center'
                %_package_name)
            if self.commcell.download_center.has_package(_package_name):
                log.info('Package exists. Trying to remove the package')
                self.commcell.download_center.delete_package(_package_name)

            if self.commcell.download_center.has_package(_package_name):
                log.error('Failed to remove the package from Download Center')
                raise Exception('Failed to remove the package from Download Center')
            else:
                log.info('Package successfully removed from Download Center')
            for each_platform in installer_constants.PACKAGES_TO_DOWNLOAD[each_pkg].keys():
                _files_to_upload.append(
                    installer_constants.PACKAGES_TO_DOWNLOAD[each_pkg][each_platform])
            log.info('Copy the package from local machine to the DC repository')

            for each_custom_package in _files_to_upload:
                self.webserver_machine.copy_from_local(
                    os.path.join(constants.TEMP_DIR, each_custom_package),
                    installer_constants.REMOTEFILECOPYLOC)
            version = '11'
            platform_download_locations = []
            for custom_pkg in _files_to_upload:
                temp_dict = {}
                for each_pfm in installer_constants.PACKAGES_TO_DOWNLOAD[each_pkg].keys():
                    if installer_constants.PACKAGES_TO_DOWNLOAD[each_pkg][each_pfm] == custom_pkg:
                        temp_dict['platform'] = each_pfm
                temp_dict['download_type'] = "Exe"
                temp_dict['location'] = os.path.join(installer_constants.REMOTEFILECOPYLOC,
                                                     custom_pkg)
                platform_download_locations.append(temp_dict)

            log.info('Package copied to the DC repository successfully')
            log.info('Attempting to upload the new package to Download Center')

            self.commcell.download_center.upload_package(
                _package_name,
                installer_constants.DOWNLOAD_CENTER_CATEGORY,
                version,
                platform_download_locations,
                sub_category=installer_constants.DOWNLOAD_CENTER_SUB_CATEGORY)
                # description=self.tcinputs['Description'],
                # vendor=self.tcinputs['Vendor'],
                # visible_to=self.tcinputs['VisibleTo']

            if self.commcell.download_center.has_package(_package_name):
                log.info('Package uploaded succesfully')
            else:
                raise Exception('Failed to upload the package to Download Center')

    def _get_proxy_details(self):
        """
        This Method gets the list of Available clients from Proxy client group
        """
        log = logger.get_log()
        proxy_list = []
        proxy_client_group = installer_constants.PROXY_GROUP_NAME
        if not self.commcell.client_groups.has_clientgroup(proxy_client_group):
            log.info("Commserver doesn't has the proxy group {0}").format(proxy_client_group)
            raise Exception("Failed to find the Proxy Group")
        else:
            client_group_obj = self.commcell.client_groups.get(proxy_client_group)
            clients_in_proxy_group = client_group_obj._associated_clients
            for each_client in clients_in_proxy_group:
                client_name = each_client
                host_name = self.commcell.clients._clients[client_name.lower()]['hostname']
                #By default we are assuming constant port number
                #if the port number changes per client in future then
                #we need to use clientobj.network.port to get the proxy port number.
                proxy_list.append(client_name+":"+host_name+":"+self._proxy_default_port)

        self.tcinputs["proxy_list"] = proxy_list

    def _run_backup(self, subclient, backup_type):
        """Initiates backup job and waits for completion
              Args:
                subclient:     (object)  --  object for the subclient to be used
                backup_type:    (string) --  type of the backup to be used
        """
        log = logger.get_log()
        log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        log.info("Started {0} backup with Job ID: {1}".format(backup_type, str(job.job_id)))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        log.info("Successfully finished {0} backup job".format(backup_type))

        return job

    def _run_backup_and_restore(self, client_name):
        """Performs a backup and restore for the specified client
        Args:
                client_name:     (String)  --  client name on which backup and restore
                to be performed
        Raises:
            SDKException:
                if it fails to perform a backup and restore operation
        """
        log = logger.get_log()
        self.commcell.clients.refresh()
        client = self.commcell.clients.get(client_name)
        log.info("Created client object: " + str(client))
        agent = client.agents.get('File System')
        log.info("Created agent object: " + str(agent))
        backupset = agent.backupsets.get('defaultBackupset')
        log.info("Created backupset object: " + str(backupset))
        subclient = backupset.subclients.get('default')
        log.info("Created subclient object: " + str(subclient))

        options_selector = OptionsSelector(self.commcell)

        log.info("Create Machine class object")
        client_machine = Machine(
            client.client_name,
            username=self.tcinputs["CCUserName"],
            password=self.tcinputs["CCPassword"]
        )

        log.info("Read subclient content")
        log.info("Subclient Content: {0}".format(subclient.content))

        drive = options_selector.get_drive(client_machine, size=500)
        test_data_path = drive + 'TestData'

        subclient_content_backup = subclient.content

        log.info("Add test data path to subclient content")
        subclient.content += [test_data_path]

        log.info("Generating test data at: {0}".format(test_data_path))
        client_machine.generate_test_data(test_data_path)

        job = self._run_backup(subclient, 'FULL')

        log.info("Get backed up content size")
        size = 200
        self.csdb.execute(
            'SELECT totalBackupSize FROM JMBkpStats WHERE jobID = {0}'.format(job.job_id)
        )
        size += int(self.csdb.fetch_one_row()[0]) / (1024 * 1024)
        log.info("Total Backed up size: {0}".format(size))

        windows_restore_client, windows_restore_location = \
            options_selector.get_windows_restore_client(size=size)

        log.info("*" * 10 + " Run out of place restore " + "*" * 10)

        job = subclient.restore_out_of_place(
            windows_restore_client.machine_name,
            windows_restore_location, subclient.content
        )
        log.info("Started Restore out of place with job id: " + str(job.job_id))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + job.delay_reason
            )

        log.info("Successfully finished restore out of place")

        log.info("Form windows restore location for Test data")
        windows_restore_location = windows_restore_location + "\\" + "TestData"
        log.info("Windows restore location: %s", windows_restore_location)

        log.info("Validate restored content")
        diff = []
        diff = client_machine.compare_folders(
            windows_restore_client, test_data_path, windows_restore_location
        )

        if diff != []:
            log.error(
                "Restore Validation failed. List of different files \n{0}".format(diff)
            )
            raise Exception(
                "Restore out of place validation failed. Please check logs for more details."
            )

        log.info("Restore out of place validation was successful")

        client_machine.remove_directory(test_data_path)
        subclient.content = subclient_content_backup

    def run(self):
        """ Main function for test case execution.
        This Method creates custom packages and Installs them onto clients.
        If Installation is sucessful custom packages are uploaded to cloud.

        Raises:
            SDKException:
                if it fails to download the package
        """
        log = logger.get_log()
        log.info("Started executing %s testcase", self.id)
        try:
            organization_name = self.tcinputs['Tenant_company']
            if organization_name:
                log.info("Trying to get authcode from company {0}".format(organization_name))
                organization = self.commcell.organizations.get(organization_name)
                self.tcinputs["authcode"] = organization.auth_code
            self.tcinputs["commserv_host_name"] = self.commcell.commserv_hostname
            self.tcinputs["commserv_client_name"] = self.commcell.commserv_name
            self._get_proxy_details()
            self.tcinputs['commserver_version'] = self.commcell.commserv_version

            self._create_custom_package()
            for each_pkg in installer_constants.PACKAGES_TO_DOWNLOAD.keys():
                _package_name = "{0} [RequestID: {1}]".format(each_pkg, self.request_id)
                for each_platform in installer_constants.PACKAGES_TO_DOWNLOAD[each_pkg].keys():
                    self._download_packages_from_download_center(_package_name, each_platform)

            self.tcinputs["commcell_username"] = self.tcinputs["Tenant_username"]
            self.tcinputs["commcell_password"] = self.tcinputs["Tenant_password"]

            log.info("-----Custom package creation & Installation for AD_PROXY_PACKAGES-----")
            self.tcinputs["client_user_name"] = self.tcinputs['Windows_machine_user_name']
            self.tcinputs["client_password"] = self.tcinputs['Windows_machine_password']
            self.tcinputs["client_name"] = self.tcinputs['Windows_machine_client_name']
            self.tcinputs["client_host_name"] = self.tcinputs['Windows_machine_host_name']
            self.tcinputs['executable_name'] = "WinX64_Proxy.exe"
            installer_obj = Installation.create_installer_object(self.tcinputs, self.commcell)
            installer_obj.install_client()
            self.commcell.refresh()
            installer_obj.validate_installed_client()

            log.info("-----Custom package creation & Installation for EDGE_PACKAGE_WINDOWS-----")
            self.tcinputs['executable_name'] = "WinX64_Client.exe"
            installer_obj = Installation.create_installer_object(self.tcinputs, self.commcell)
            installer_obj.install_client()
            installer_obj.execute_register_me_command()
            self.commcell.refresh()
            installer_obj.validate_installed_client()

            log.info("-----Custom package creation & Installation for EDGE_PACKAGE_MAC-----")
            self.tcinputs["client_user_name"] = self.tcinputs['Mac_machine_user_name']
            self.tcinputs["client_password"] = self.tcinputs['Mac_machine_password']
            self.tcinputs["client_name"] = self.tcinputs['Mac_machine_client_name']
            self.tcinputs["client_host_name"] = self.tcinputs['Mac_machine_host_name']
            self.tcinputs['executable_name'] = "Mac_client.pkg"
            installer_obj = Installation.create_installer_object(self.tcinputs, self.commcell)
            installer_obj.install_client()
            self.commcell.refresh()
            installer_obj.validate_installed_client()

            #Uploaded the created Packages to Download center
            self._upload_to_downloadcenter()

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """
        This method deletes the machine object created for the client and the Automation controller

        """
        if self.webserver_machine:
            self.webserver_machine.disconnect()
        if self._automation_obj:
            del self._automation_obj
        del self.webserver_machine

    def _create_custom_package(self):
        """
        This method helps to create a cusom package using cloud form

        Raises:
            SDKException:
                if it fails to download the package
        """
        log = logger.get_log()
        log.info("----Creating custom packages by calling  Workflow in cloud----")
        self.workflow_commcell_obj = commcell.Commcell(
            installer_constants.FOREVERCELL_HOSTNAME,
            self.tcinputs['Cloud_Username'],
            self.tcinputs['Cloud_Password'])
        workflows_obj = self.workflow_commcell_obj.workflows
        custom_workflow_obj = workflows_obj.get(installer_constants.FOREVERCELL_WORKFLOW_NAME)
        custom_pkg_xml_object = CustomPackageCloudXML(self.tcinputs)
        workflow_inputs = custom_pkg_xml_object.generate_xml()
        response = custom_workflow_obj.execute_workflow(workflow_inputs)
        jobcontroller_job = self.workflow_commcell_obj.job_controller
        job_obj = jobcontroller_job.get(response['jobId'])
        self.request_id = json.loads(response['outputs'])['requestId']
        log.info("Job ID is %s and Request ID is %s are received from workflow"
                 % (response['jobId'], self.request_id))
        if job_obj.wait_for_completion(60):
            log.info("Custom Package created successfully")
        else:
            raise Exception("Failed to create Custom Package")

    def _download_packages_from_download_center(self, package, platform):
        """
        This Method Downloads the custom package from the cloud
        Args:
            package     (str)  --  Name of the Package to be downloaded
            platform    (str)  --  platform name of the package

        Raises:
            SDKException:
                if it fails to download the package
        """
        _download_location = constants.TEMP_DIR
        return self.workflow_commcell_obj.download_center.download_package(
            package,
            _download_location,
            platform)
