# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.

    Input Example FOR DELL EMC ISILON:

    "testCases": {
    "58848": {
        "AgentName":"File System",
        "NASServerClientName":"isilon",
        "NASServerHostName":"isilon.host.name",
        "PlanName": "Server plan",
        "ArrayName": "isilon.host.name",
        "ControlHost":"isilon.host.name",
        "WindowsDataAccessNodes": "NODE1,NODE2",
        "TestPathList": r"\\isilon.host.name\\SHARE1,/isilon.host.name/SHARE2"
        }
    }
    
    Input Example FOR NUTANIX FILES:   

    "testCases": {
    "58848": {
        "AgentName":"File System",
        "NutanixFilesClientName":"nutanix",
        "FileServer":"nutanix.host.name",
        "PlanName": "Server plan",
        "WindowsDataAccessNodes": "NODE1,NODE2",
        "TestPathList": r"\\nutanix.host.name\SHARE1"
        }
    }

    Input Example FOR QUMULO FILE STORAGE:   

    "testCases": {
    "58848": {
        "AgentName":"File System",
        "QumuloFileStorageName":"qumulo.host.name",
        "QumuloFileStorage":"qumulo.host.name",
        "PlanName": "Server plan",
        "WindowsDataAccessNodes": "NODE1,NODE2",
        "TestPathList": r"\\qumulo.host.name\SHARE1"
        }
    }

"""""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.nutanix_files import NutanixFiles
from Web.AdminConsole.FileServerPages.qumulo_file_storage import QumuloFileStorage
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.NAS.nas_file_servers import Vendor
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays
import AutomationUtils.config as config
from Web.Common.page_object import TestStep, handle_testcase_exception
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from functools import partial
from cvpysdk.job import Job

constants = config.get_config()


class TestCase(CVTestCase):
    """
    Command Center - Client Creation for
    Dell EMC Isilon NAS File Server
    Nutanix Files
    Qumulo File Storage

    """

    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Command Center - Client Creation for \
                    Dell EMC Isilon NAS File Server \
                    Nutanix Files \
                    Qumulo File Storage"
        self.browser = None
        self.admin_console = None
        self.admin_page = None
        self.arrays = None
        self.content = None
        self.tcinputs = {"TestPathList": None, "PlanName": None}
        self.host_name = None
        self.client_name = None
        self.nutanix_files = None
        self.qumulo_file_storage = None
        self.host_name = None
        self.plan_name = None
        self.file_server = None
        self.arrays = None
        self.test_path_list = []
        self.array_details = {}
        self.cifs = None
        self.nfs = None
        self.cifs_content = []
        self.nfs_content = []
        self.machine = None
        self.tmp_path = None
        self.run_nfs = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # SETTING UP ALL COMMON INPUTS
        self.browser = BrowserFactory().create_browser_object()
        self.plan_name = self.tcinputs.get("PlanName")
        self.test_path_list = self.tcinputs.get('TestPathList').split(',')
        self.cifs_content = list(filter(lambda path: path if path.startswith("\\") else (self.nfs_content.append(path) if path.startswith("/") or path.find(":/") else None), self.test_path_list))

        assert self.tcinputs.get('WindowsDataAccessNodes', False) or self.tcinputs.get('UnixDataAccessNodes', False), \
            'Either WindowsDataAccessNodes OR UnixDataAccessNodes MUST BE SPECIFIED AS AN INPUT, REFER TO DOCSTRING'

        if self.cifs_content:
            self.cifs = {'access_nodes': self.tcinputs.get('WindowsDataAccessNodes').split(','), 'content': self.cifs_content,
                         'impersonate_user': {'username': constants.FileSystem.WINDOWS.TestPathUserName,
                                              'password': constants.FileSystem.WINDOWS.TestPathPassword}}
        if self.nfs_content:
            self.nfs = {'access_nodes': self.tcinputs.get('UnixDataAccessNodes').split(','), 'content': self.nfs_content}

        # SETTING DELL EMC ISILON SPECIFIC INPUTS
        if self.tcinputs.get("NASServerClientName", False):
            self.client_name = self.tcinputs.get("NASServerClientName")
            self.host_name = self.tcinputs.get("NASServerHostName")
            self.array_details = {'array_name': self.tcinputs.get('ArrayName'),
                                  'control_host': self.tcinputs.get('ControlHost'),
                                  'username': constants.Array.DellEMCIsilon.Username,
                                  'password': constants.Array.DellEMCIsilon.Password}

        # SETTING UP NUTANIX FILES SERVER INPUTS
        elif self.tcinputs.get("NutanixFilesClientName", False):
            self.client_name = self.tcinputs.get("NutanixFilesClientName")
            self.array_details = {'array_name': self.tcinputs.get('NutanixFilesServer'),
                                  'username': constants.Array.NutanixFiles.Username,
                                  'password': constants.Array.NutanixFiles.Password}

        # SETTING UP QUMULO FILE STORAGE INPUTS
        elif self.tcinputs.get("QumuloFileStorageName", False):
            self.client_name = self.tcinputs.get("QumuloFileStorageName")
            self.array_details = {'array_name': self.tcinputs.get('QumuloFileStorage'),
                                  'username': constants.Array.QumuloFileStorage.Username,
                                  'password': constants.Array.QumuloFileStorage.Password}

        else:
            raise Exception("NASServerClientName,NutanixFilesClientName or QumuloFileStorageName MUST BE GIVEN AS INPUT.")

        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()
        self.file_server = FileServers(self.admin_console)
        self.admin_page = self.admin_console.navigator
        self.arrays = Arrays(self.admin_console)
        self.admin_console.navigator.navigate_to_file_servers()
        self.machine = Machine(self.cifs['access_nodes'][0], commcell_object=self.commcell)
        self.run_nfs = self.tcinputs.get("RunNFS", False)

    @test_step
    def cleanup(self):
        """Cleans up the testcase pre-requisites"""
        self.admin_page.navigate_to_arrays()
        array_list = [array['name'] for array in self.arrays.array_list()]
        if self.array_details['array_name'] in array_list:
            self.delete_array()
        if self.client_name in self.commcell.clients.all_clients:
            self.retire_client()

    @test_step
    def add_dell_emc_isilon_client(self):
        """"Adds a Dell EMC Isilon client."""
        self.log.info("01. Creating the Dell EMC Isilon NAS/Network Share Client.")
        self.file_server.add_nas_client(name=self.client_name,
                                        host_name=self.host_name,
                                        plan=self.plan_name,
                                        vendor=Vendor.DELL_EMC_ISILON,
                                        array_details=self.array_details,
                                        cifs=self.cifs,
                                        nfs=self.nfs)

    @test_step
    def add_nutanix_files_client(self):
        """Adds a Nutanix Files client."""
        self.log.info("01. Creating the Nutanix Files Server Client.")
        self.nutanix_files = NutanixFiles(self.admin_console, self.array_details)
        self.nutanix_files.add_nutanix_files(name=self.client_name,
                                             plan=self.plan_name,
                                             array_details=self.array_details,
                                             cifs=self.cifs,
                                             nfs=self.nfs)

    @test_step
    def add_qumulo_file_storage_client(self):
        """Adds a Qumulo File Storage client."""
        self.log.info("01. Creating the Qumulo File Storage Client.")
        self.qumulo_file_storage = QumuloFileStorage(self.admin_console)
        self.qumulo_file_storage.add_qumulo_file_storage(name=self.client_name,
                                                         qumulo_cluster=self.array_details['array_name'],
                                                         plan=self.plan_name,
                                                         username=self.array_details['username'],
                                                         password=self.array_details['password'],
                                                         cifs=self.cifs,
                                                         nfs=self.nfs)

    @test_step
    def add_client(self):
        """Adds a client based on value of test case input."""
        self.admin_page.navigate_to_file_servers()
        if self.tcinputs.get("NASServerClientName", False):
            self.add_dell_emc_isilon_client()
        elif self.tcinputs.get("NutanixFilesClientName", False):
            self.add_nutanix_files_client()
        else:
            self.add_qumulo_file_storage_client()

    @test_step
    def access_server_from_file_servers_page(self):
        """Accesses the desired server from the File Servers page."""
        self.log.info("02. Verifying client was created successfully by searching for it.")
        self.admin_page.navigate_to_file_servers()
        self.file_server.access_server(self.client_name)

    @test_step
    def delete_array(self):
        """Deletes the array."""
        self.arrays = Arrays(self.admin_console)
        self.arrays.action_delete_array(self.array_details['array_name'])

    @test_step
    def retire_client(self):
        """Retires the client."""
        self.admin_page.navigate_to_file_servers()
        self.file_server.retire_server(self.client_name)

    def backup(self, backup_level, agent):
        """Runs a backup."""
        self.admin_console.navigator.navigate_to_file_servers()
        job_id = self.file_server.backup_subclient(self.client_name, backup_level, agent=agent)
        Job(self.commcell, job_id).wait_for_completion()

    @test_step
    def run_cycle_of_backups(self):
        """Runs a cycle of backups."""
        impersonation_args = {'username': self.cifs['impersonate_user']['username'], 'password': self.cifs['impersonate_user']['password']}
        partial_generate_test_data = partial(self.machine.generate_test_data, **impersonation_args)
        partial_rename_test_data = partial(self.machine.modify_test_data, rename=True)
        partial_modify_test_data = partial(self.machine.modify_test_data, modify=True)
        agent = 'CIFS'
        content = self.cifs_content

        if isinstance(self.machine, UnixMachine):
            partial_generate_test_data = partial(self.machine.generate_test_data)
            agent = 'NFS'
            content = self.nfs_content

        # ADD FILES AND RUN FULL
        full_paths = [self.machine.join_path(path, "FULL") for path in content]
        list(map(partial_generate_test_data, full_paths))
        self.backup("Full", agent)

        # ADD FILES AND RUN INCREMENTAL
        incr_paths = [self.machine.join_path(path, "INCREMENTAL") for path in content]
        list(map(partial_generate_test_data, incr_paths))
        self.backup("Incremental", agent)

        # MODIFY FILES AND RUN INCREMENTAL
        list(map(partial_modify_test_data, incr_paths))
        self.backup("Incremental", agent)

        self.backup("Synthfull", agent)

        # RENAME FILES AND RUN INCREMENTAL
        list(map(partial_rename_test_data, incr_paths))
        self.backup("Incremental", agent)

    @test_step
    def restore_and_verify(self, proxy, content, impersonate_user=None):
        """Restores from the subclient and verifies the restored data"""
        source = ["_".join((path, "SOURCE")) for path in content]
        list(map(self.machine.rename_file_or_folder, self.test_path_list, source))
        restore_job_id = self.file_server.restore_subclient(self.client_name, proxy, selected_files=content, impersonate_user=impersonate_user)
        Job(self.commcell, restore_job_id).wait_for_completion()
        result, diff = self.machine.compare_meta_data(source[0], content[0])
        if result:
            self.log.info("Metadata comparison was successful.")
        else:
            self.log.info(f"Metadata comparison failed, diff = {diff}")

    def run(self):
        """Main function for test case execution."""

        try:
            self.cleanup()
            self.add_client()
            self.access_server_from_file_servers_page()
            self.run_cycle_of_backups()
            self.restore_and_verify(self.cifs['access_nodes'][0], self.cifs_content, self.cifs['impersonate_user'])
            if self.run_nfs:
                self.machine = Machine(self.nfs['access_nodes'][0], commcell_object=self.commcell)
                self.run_cycle_of_backups()
                self.restore_and_verify(self.nfs['access_nodes'][0], self.nfs_content)
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)





