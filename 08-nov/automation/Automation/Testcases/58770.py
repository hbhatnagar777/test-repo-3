# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    create_nas_server() --  Function to create a Non-NDMP NAS server.

    validate_server_creation()  --  Function to validate Non-NDMP NAS server creation, default Archiveset and default Subclient.

    validate_subclient_creation()   --  Function to validate default Subclient properties are created as per the Plan

    run_archive_job()   --  Function to run Archive job thrice.

    run_restore_job()   --  Function to run restore job.

    generate_test_data()    --  Function to generate test data with required file_size and modified_time attribute

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Archiving.Archiving import Archiving
from cvpysdk.subclients.fssubclient import FileSystemSubclient
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from datetime import datetime
import time
from AutomationUtils import config
_CONF = config.get_config()
_CONSTANTS = _CONF.NetworkShare

class TestCase(CVTestCase):
    """ Command center: Adding and validating a new non-NDMP NAS client and validate Archive and Restore """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Testcase for Adding and validating a new non-NDMP NAS client and validate Archive and Restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.archiving = None
        self.table = None
        self.hostname = None
        self.client_machine = None
        self.access_node = None
        self.test_path = None
        self.origin_path = None
        self.data_path = None
        self.stub_path = None
        self.plan_name = None,
        self.username = None
        self.password = None
        self.fs_subclient = None
        self.op_helper = None
        self.tcinputs = {
            "AgentName": None,
            "AccessNode": None
        }

    @test_step
    def create_nas_server(self):
        """ Function to create a Non-NDMP NAS server. """
        self.navigator.navigate_to_archiving()
        server_names = self.table.get_column_data('Name')
        server_name = self.hostname

        if server_name in server_names:
            self.archiving.retire_server(self.hostname)
            time.sleep(200)
            self.commcell.clients.refresh()
            self.admin_console.refresh_page()

        server_names = self.table.get_column_data('Name')

        if server_name in server_names:
            self.archiving.delete_server(self.hostname)
            time.sleep(200)
            self.commcell.clients.refresh()
            self.admin_console.refresh_page()

        self.archiving.add_new_server(server_type="NAS", host_name=self.hostname, access_node=self.access_node,
                                      archive_paths=[self.origin_path],
                                      plan=self.plan_name,
                                      username=self.username, password=self.password)

    def validate_server_creation(self):
        """ Function to validate Non-NDMP NAS server creation, default Archiveset and default Subclient. """
        time.sleep(30)
        self.commcell.refresh()
        client = self.commcell.clients.get(self.hostname)
        self.log.info("NAS client with given hostname Creation Successful")
        agent = client.agents.get("Windows File System")
        self.log.info("Windows File System agent Creation Successful")
        archive_set = agent.backupsets.get("DefaultArchivingSet")
        self.log.info("Default Archiveset Creation Successful")
        subclient = archive_set.subclients.get("default")
        self.fs_subclient = FileSystemSubclient(backupset_object=archive_set, subclient_name="default")
        self.log.info("Default Subclient Creation Successful")

    def validate_subclient_creation(self):
        """ Function to validate default Subclient properties are created as per the Plan """
        subclient = self.fs_subclient
        plan = self.commcell.plans.get(self.plan_name)

        if subclient.backup_nodes[0]['clientName'] == self.access_node:
            self.log.info("Subclient Data Access Nodes are inherited from Client")
        else:
            raise CVTestStepFailure("Subclient Data Access Nodes are not inherited from Client")

        if subclient.content == [self.origin_path]:
            self.log.info("Subclient Content Paths are inherited from Client")
        else:
            raise CVTestStepFailure("Subclient Content Paths are not inherited from Client")

        plan_archiver_retention = \
            plan._plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy']['subClientList'][
                0][
                'fsSubClientProp']['extendRetentionForNDays']
        if subclient.archiver_retention_days == plan_archiver_retention:
            self.log.info("Subclient Archiver Retention is inherited from plan.")
        else:
            raise CVTestStepFailure("Subclient Archiver Retention is not inherited from plan.")

        plan_disk_cleanup_rules = plan._plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy'][
            'subClientList'][0][
            'fsSubClientProp']['diskCleanupRules']
        if subclient.disk_cleanup_rules == plan_disk_cleanup_rules:
            self.log.info("Subclient Disk Cleanup rules are inherited from Plan")
        else:
            raise CVTestStepFailure("Subclient Disk Cleanup rules are not inherited from Plan")

        plan_retention = {}
        plan_retention['days'] = plan._plan_properties['storage']['copy'][0]['retentionRules'][
            'retainBackupDataForDays']
        plan_retention['cycles'] = plan._plan_properties['storage']['copy'][0]['retentionRules'][
            'retainBackupDataForCycles']
        plan_retention['archiveDays'] = plan._plan_properties['storage']['copy'][0]['retentionRules'][
            'retainArchiverDataForDays']

        storage_policy_retention = self.commcell.storage_policies.get(self.plan_name).get_copy(
                "Primary").copy_retention
        if storage_policy_retention == plan_retention:
            self.log.info("Retention rules in the storage policy is inherited from Plan")
        else:
            raise CVTestStepFailure("Retention rules in the storage policy is not inherited from Plan")

    @test_step
    def run_archive_job(self):
        """ Function to run Archive job thrice. """
        self.navigator.navigate_to_archiving()
        for i in range(3):
            job_id = self.archiving.run_archive(client_name=self.hostname)
            if self.commcell.job_controller.get(job_id).wait_for_completion(timeout=120):
                self.log.info("Job completed Successfully.")
                time.sleep(15)
                self.admin_console.refresh_page()
            else:
                raise CVTestStepFailure("Job could not be completed")

    @test_step
    def run_restore_job(self, data=True, restore_path=None):
        """ Function to run restore job.
         Args:
            data     (bool)   --  Will restore data instead of Stub if True, else will restore data.
            restore_path    (str)   --  Path at which the file is to be restored.
        """
        self.navigator.navigate_to_archiving()
        time.sleep(30)
        self.admin_console.refresh_page()
        job_id = self.archiving.restore_subclient(
            self.hostname,
            proxy_client=self.access_node,
            restore_path=restore_path,
            backupset_name=None,
            subclient_name=None,
            unconditional_overwrite=True,
            restore_ACLs=False,
            restore_data_instead_of_stub=data,
            impersonate_user=self.username,
            impersonate_password=self.password,
            notify=False,
            selected_files=[self.op_helper.client_machine.join_path(self.origin_path,
                                                                    self.op_helper.test_file_list[0][0])])
        if self.commcell.job_controller.get(job_id).wait_for_completion(timeout=120):
            self.log.info("Job completed Successfully.")
            time.sleep(15)
        else:
            raise CVTestStepFailure("Job could not be completed")

    def generate_test_data(self):
        """ Function to generate test data with required file_size and modified_time attribute """
        self.op_helper.prepare_turbo_testdata(
            self.origin_path,
            [("test1.txt", True), ("test2.txt", False), ("test3.txt", True),
             ("test4.txt", False)],
            size1=1536 * 1024,
            size2=20 * 1024)

        for i in range(2):
            self.op_helper.client_machine.modify_item_datetime(path=self.op_helper.client_machine.join_path(
                self.origin_path, self.op_helper.test_file_list[i][0]),
                creation_time=datetime(year=2019, month=1, day=1),
                access_time=datetime(year=2019, month=1, day=1),
                modified_time=datetime(year=2019, month=1, day=1))

        self.op_helper.org_hashcode = self.op_helper.client_machine.get_checksum_list(self.origin_path)
        self.log.info("Test data populated successfully.")

    def setup(self):
        """ Pre-requisites for this testcase """

        self.log.info("Initializing pre-requisites")
        self.hostname = self.tcinputs.get("HostName", "172.19.69.32")
        self.access_node = self.tcinputs.get("AccessNode")
        self.plan_name = self.tcinputs.get("PlanName", "defaultPlan")
        self.test_path = self.tcinputs.get("TestPath", _CONSTANTS.TestPath)
        self.username = self.tcinputs.get("ImpersonateUser", _CONSTANTS.ImpersonateUser)
        self.password = self.tcinputs.get("Password", _CONSTANTS.Password)
        self.client_machine = Machine(machine_name=self.access_node, commcell_object=self.commcell)
        self.test_path = self.client_machine.join_path(self.test_path, "58770")
        self.op_helper = cvonepas_helper(self)
        self.op_helper.client_machine = self.client_machine
        self.origin_path = self.client_machine.join_path(self.test_path, "origin")
        self.data_path = self.client_machine.join_path(self.test_path, "data")
        self.stub_path = self.client_machine.join_path(self.test_path, "stub")
        self.op_helper.test_file_list = [("test1.txt", True), ("test2.txt", False), ("test3.txt", False),
                                         ("test4.txt", False)]
        self.generate_test_data()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.table = Table(self.admin_console)
        self.archiving = Archiving(self.admin_console)
        self.navigator = self.admin_console.navigator

    def run(self):
        """Main function for test case execution"""

        _desc = """
        Adding a new non NDMP NAS client :
        1)	Provide the hostname if the client.
        2)	Select the share Type CIFS.
        3)	Access node (unix/windows proxy) based on the share type.
        4)	Select the archive plan.
        5)	Provide the user credentials for the CIFS  share.
        6)	Provide the path to archive and submit.
        Validation
        7)	Validate NAS Server created with specified hostname.
        8)	validate subclient creation: Make sure defaultarchive set created with default subclient with Rules, retention days and storage policy settings are inherited from the plan.
        9)	Content path and Access node should be set the subclient level.
        10)	Run the archive  job make sure the files are archived  based  on the rules specified.
        11)	Restore the data  with option restore data instead of stub selected  and make sure the files are restored.
        12)	Restore the stubs with option restore data instead of stub deselected and make sure stubs are restored.
        """
        try:
            self.create_nas_server()

            self.validate_server_creation()

            self.validate_subclient_creation()

            self.admin_console.refresh_page()

            self.run_archive_job()

            self.op_helper.verify_stub(path=self.origin_path, test_data_list=self.op_helper.test_file_list,
                                       is_nas_turbo_type=True)

            self.run_restore_job(data=True, restore_path=self.data_path)

            self.op_helper.verify_stub(path=self.data_path, test_data_list=[("test1.txt", False)],
                                       is_nas_turbo_type=True)

            self.run_restore_job(data=False, restore_path=self.stub_path)

            self.op_helper.verify_stub(path=self.stub_path, test_data_list=[("test1.txt", True)],
                                       is_nas_turbo_type=True)

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
