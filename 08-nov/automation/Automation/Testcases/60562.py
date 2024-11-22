from selenium.webdriver.common.by import By
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

    create_archive_plan()   --  Function to create an Archive Plan.

    add_server() --  Function to create a lustre server.

    run_archive_job()   --  Function to run Archive job.

    run_restore_job()   --  Function to run restore job.

    delete_archive_plan()   --  Function to delete an archive plan.

    delete_server() --  Function to delete a server.

    generate_test_data()    --  Function to generate test data with required file_size and modified_time attribute

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Archiving.Archiving import Archiving
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from AutomationUtils.constants import DistributedClusterPkgName
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import time


class TestCase(CVTestCase):
    """ Command center: Validate Archive and restore functionality for existing Lustre client from command center """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Testcase to Validate Archive and restore functionality for existing Lustre client from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.archiving = None
        self.file_servers = None
        self.table = None
        self.hostname = None
        self.client_machine = None
        self.access_node = None
        self.test_path = None
        self.origin_path = None
        self.restore_stub_path = None
        self.restore_data_path = None
        self.plan_name = None
        self.plan = None
        self.username = None
        self.password = None
        self.fs_plan = None
        self.fs_subclient = None
        self.op_helper = None
        self.restore_checksum = []
        self.tcinputs = {
            "AgentName": None,
            "AccessNode": None,
            "PrimaryStorageForPlan": None
        }

    def generate_test_data(self):
        """ Function to generate test data with required file_size and modified_time attribute """

        self.log.info("Test-case will generate 4 files.")
        self.log.info("First two files will be 1.5MB in size and last two files will be 20KB")
        self.log.info(
            "First three files will have access and modified time greater than 3 months")
        self.log.info("The last file will have latest timestamp.")
        self.log.info("First two files should get archived based on file size and modified time rule.")
        self.log.info("Third file will not qualify file size rule. fourth file wont qualify any rule.")

        self.op_helper.org_hashcode = self.op_helper.prepare_turbo_testdata(
            self.origin_path,
            self.op_helper.test_file_list,
            size1=1536 * 1024,
            size2=20 * 1024)

        # Gets checksum for the files qualified for stubbing.
        self.restore_checksum.extend(
            self.op_helper.client_machine.get_checksum_list(self.op_helper.client_machine.join_path(
                self.origin_path, self.op_helper.test_file_list[0][0])))
        self.restore_checksum.extend(
            self.op_helper.client_machine.get_checksum_list(self.op_helper.client_machine.join_path(
                self.origin_path, self.op_helper.test_file_list[1][0])))

        # Modify timestamp  of 3 files to 1 year old.
        for i in range(3):
            self.op_helper.client_machine.modify_item_datetime(path=self.op_helper.client_machine.join_path(
                self.origin_path, self.op_helper.test_file_list[i][0]),
                creation_time=datetime(year=2019, month=1, day=1),
                access_time=datetime(year=2019, month=1, day=1),
                modified_time=datetime(year=2019, month=1, day=1))

        self.log.info("Test data populated successfully.")

    @test_step
    def add_fs_server(self):
        """ Install new file server client """

        self.navigator.navigate_to_file_servers()
        self.file_servers.add_distributed_app(pkg=DistributedClusterPkgName.LUSTREFS,
                                              server_name=self.hostname,
                                              access_nodes=[self.access_node],
                                              plan_name=self.fs_plan)

    @test_step
    def create_archive_plan(self):
        """ Creates an Archive Plan """

        self.navigator.navigate_to_plan()
        storage = {
            'pri_storage': self.tcinputs.get('PrimaryStorageForPlan'),
            'pri_ret_period': None,
            'ret_unit': None
        }

        archiving_rules = {
            'last_modified': self.tcinputs.get('LastModifiedTime', 30),
            'last_modified_unit': self.tcinputs.get('LastModifiedUnit', 'days'),
            'last_accessed': self.tcinputs.get('LastAccessedTime', 0),
            'last_accessed_unit': self.tcinputs.get('LastAccessedUnit', 'days'),
            'file_size': self.tcinputs.get('FileSize', 30),
            'file_size_unit': self.tcinputs.get('FileSizeUnit', 'KB'),
        }
        self.plan.create_archive_plan(plan_name=self.plan_name, storage=storage, archiving_rules=archiving_rules)

    @test_step
    def add_server(self):
        """ Function to create a Lustre server. """
        self.navigator.navigate_to_archiving()

        self.archiving.add_distributed_app(pkg=DistributedClusterPkgName.LUSTREFS,
                                           server_name=self.hostname,
                                           access_nodes=[self.access_node],
                                           archive_paths=[self.origin_path],
                                           plan_name=self.plan_name,
                                           existing_server=True)
        self.admin_console.refresh_page()

    @test_step
    def run_archive_job(self):
        """ Function to run Archive job. """
        self.navigator.navigate_to_archiving()
        self.admin_console.refresh_page()
        job_id = self.archiving.run_archive(client_name=self.hostname)
        if self.commcell.job_controller.get(job_id).wait_for_completion(timeout=240):
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
        if self.client_machine.check_directory_exists(restore_path):
            self.client_machine.remove_directory(restore_path)
        self.client_machine.create_directory(restore_path, False)
        self.navigator.navigate_to_archiving()
        time.sleep(30)
        self.admin_console.refresh_page()
        job_id = self.archiving.restore_subclient(
            self.hostname,
            restore_path=restore_path,
            backupset_name=None,
            subclient_name=None,
            unconditional_overwrite=True,
            restore_ACLs=False,
            restore_data_instead_of_stub=data,
            notify=False,
            selected_files=[self.op_helper.client_machine.join_path(self.origin_path,
                                                                    self.op_helper.test_file_list[i][0]) for i in
                            range(2)])
        if self.commcell.job_controller.get(job_id).wait_for_completion(timeout=120):
            self.log.info("Job completed Successfully.")
            time.sleep(15)
        else:
            raise CVTestStepFailure("Job could not be completed")

    @test_step
    def recall_verify(self, checksum, path):
        """Recalls and Verifies checksum integrity of the given path"""
        try:
            for i in range(len(path)):
                self.op_helper.recall(org_hashcode=[checksum[i]], path=path[i])
        except Exception:
            for i in range(len(path)):
                self.op_helper.recall(org_hashcode=[checksum[i]], path=path[i])

    @test_step
    def delete_archive_plan(self):
        """ Deletes an Archive Plan """
        self.navigator.navigate_to_plan()
        plan_names = self.table.get_column_data('Plan name')

        if self.plan_name in plan_names:
            self.plan.delete_plan(self.plan_name)
            self.admin_console.wait_for_completion()

    @test_step
    def delete_server(self):
        """ Deletes the created Server """
        self.navigator.navigate_to_archiving()
        server_names = self.table.get_column_data('Name')
        server_name = self.hostname

        if server_name in server_names:
            self.archiving.retire_server(self.hostname, wait=False)
            time.sleep(200)
            self.commcell.clients.refresh()
            self.admin_console.refresh_page()

        server_names = self.table.get_column_data('Name')
        if server_name in server_names:
            self.archiving.delete_server(self.hostname)
            time.sleep(200)
            self.commcell.clients.refresh()
            self.admin_console.refresh_page()

    def open_navigation_bar(self):
        """Opens and pins navigation bar."""
        try:
            self.navigator.navigate_to_plan()
        except NoSuchElementException:
            nav_bar = self.admin_console.driver.find_element(By.XPATH, "//div[@class='menu-btn button']")
            nav_bar.click()

    def setup(self):
        """ Pre-requisites for this testcase """

        self.log.info("Initializing pre-requisites")
        self.hostname = f"test{int(time.time())}"
        self.access_node = self.tcinputs.get("AccessNode")
        self.plan_name = f"plan{int(time.time())}"
        self.test_path = self.tcinputs.get("TestPath", f"/test_2_12/{self.id}")
        self.username = self.tcinputs.get("ImpersonateUser")
        self.password = self.tcinputs.get("Password")
        self.fs_plan = self.tcinputs.get("fsplan")
        self.client_machine = Machine(machine_name=self.access_node, commcell_object=self.commcell)
        self.op_helper = cvonepas_helper(self)
        self.op_helper.client_machine = self.client_machine
        self.origin_path = self.client_machine.join_path(self.test_path, "origin")
        self.restore_data_path = self.client_machine.join_path(self.test_path, "restore_data")
        self.restore_stub_path = self.client_machine.join_path(self.test_path, "restore_stub")
        self.op_helper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", False),
                                         ("test4.txt", False)]
        self.generate_test_data()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.table = Rtable(self.admin_console)
        self.plan = Plans(self.admin_console)
        self.archiving = Archiving(self.admin_console)
        self.file_servers = FileServers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.open_navigation_bar()

    def run(self):
        """Main function for test case execution"""

        _desc = """
        1) Add a Lustre File Server at FileServer Page.
        2) Create Archive plan.
        3) Add an Existing Lustre server on Archiver Server Page
        4) Run Archive job.
        5) Verify eligible files got stubbed.
        6) Run another Archive Job to backup the stubs.
        7) Recall stubs and verify. 	
        8) Restore the data with option restore data instead of stub selected and verify data files are restored.
        9) Verify restored data files.
        10) Restore the stubs with option restore data instead of stub deselected and verify stubs are restored.
        11) Recall and verify restored stub files.
        12) Delete Server.
        13) Delete Archive plan.
        """
        try:

            self.add_fs_server()

            self.create_archive_plan()

            self.add_server()

            self.run_archive_job()

            self.op_helper.verify_stub(path=self.origin_path, test_data_list=self.op_helper.test_file_list)

            self.run_archive_job()

            time.sleep(120)
            self.op_helper.recall(org_hashcode=self.op_helper.org_hashcode, path=self.origin_path)

            self.run_restore_job(data=True, restore_path=self.restore_data_path)

            self.op_helper.verify_stub(path=self.restore_data_path,
                                       test_data_list=[("test1.txt", False), ("test2.txt", False)])

            self.recall_verify(checksum=self.restore_checksum, path=[self.op_helper.client_machine.join_path(
                self.restore_data_path, self.op_helper.test_file_list[i][0]) for i in range(2)])

            self.run_restore_job(data=False, restore_path=self.restore_stub_path)

            self.op_helper.verify_stub(path=self.restore_stub_path,
                                       test_data_list=[("test1.txt", True), ("test2.txt", True)])

            self.recall_verify(checksum=self.restore_checksum, path=[self.op_helper.client_machine.join_path(
                self.restore_stub_path, self.op_helper.test_file_list[i][0]) for i in range(2)])

            self.delete_server()

            self.delete_archive_plan()

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
