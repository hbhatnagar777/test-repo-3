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

    add_server() --  Function to create a Hadoop server.

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
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Bigdata.instances import Instances
import time


class TestCase(CVTestCase):
    """ Command center: Validate Archive and restore functionality for existing Hadoop client from command center """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Testcase to Validate Archive and restore functionality for existing Hadoop client from command center"
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
        self.qualified_path = None
        self.unqualified_path = None
        self.test_data_qualified = None
        self.test_data_unqualified = None
        self.restore_data_path = None
        self.plan_name = None
        self.plan = None
        self.username = None
        self.password = None
        self.fs_subclient = None
        self.fs_plan = None
        self.op_helper = None
        self.big_data = None
        self.restore_checksum = []
        self.tcinputs = {
            "AgentName": None,
            "AccessNode": None,
            "PrimaryStorageForPlan": None
        }

    def generate_test_data(self):
        """ Function to generate test data with required file_size and modified_time attribute """

        self.client_machine.generate_test_data(self.qualified_path, sparse=False, files=5, file_size=5)
        self.client_machine.generate_test_data(self.unqualified_path, sparse=False, files=5, file_size=3)
        self.test_data_qualified = self.client_machine.get_test_data_info(self.qualified_path, checksum=True)
        self.test_data_unqualified = self.client_machine.get_test_data_info(self.unqualified_path, checksum=True)

        self.log.info("Test data populated successfully.")

    @test_step
    def add_fs_server(self):
        """ Install new Hadoop client """

        self.navigator.navigate_to_big_data()
        hadoop_server = self.big_data.add_hadoop_server()

        hadoop_server.add_hadoop_parameters(name="automation_test", access_nodes=[self.access_node], hdfs_user="hdfs",
                                            plan_name=self.fs_plan)
        hadoop_server.save()
        self.log.info("Server Added")

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
            'last_modified': self.tcinputs.get('LastModifiedTime', 0),
            'last_modified_unit': self.tcinputs.get('LastModifiedUnit', 'days'),
            'last_accessed': self.tcinputs.get('LastAccessedTime', 0),
            'last_accessed_unit': self.tcinputs.get('LastAccessedUnit', 'days'),
            'file_size': self.tcinputs.get('FileSize', 4),
            'file_size_unit': self.tcinputs.get('FileSizeUnit', 'MB'),
        }
        self.plan.create_archive_plan(plan_name=self.plan_name, storage=storage, archiving_rules=archiving_rules,
                                      delete_files=True)

    @test_step
    def add_server(self):
        """ Function to create a Hadoop server. """
        self.navigator.navigate_to_archiving()

        self.archiving.add_distributed_app(pkg='HADOOP', server_name=self.hostname,
                                           access_nodes=[self.access_node],
                                           archive_paths=[self.origin_path],
                                           plan_name=self.plan_name, existing_server=True)
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

    def verify_delete(self):
        """ Function to verify qualified files got deleted. """

        qualified_data = self.client_machine.get_test_data_info(self.qualified_path)
        unqualified_data = self.client_machine.get_test_data_info(self.unqualified_path)

        self.log.info(qualified_data)
        self.log.info(unqualified_data)

        if "regularfile" not in qualified_data:
            self.log.info("Qualified Data is Deleted.")
        else:
            raise Exception("Qualified Data is not deleted.")

        if unqualified_data == self.test_data_unqualified:
            self.log.info("Unqualified data is intact")
        else:
            raise Exception("Unqualified data is also deleted.")

    @test_step
    def run_restore_job(self, restore_path=None):
        """ Function to run restore job.
         Args:
            restore_path    (str)   --  Path at which the file is to be restored.
        """
        if self.client_machine.check_directory_exists(restore_path):
            self.client_machine.remove_directory(restore_path)
        self.client_machine.create_directory(restore_path)
        self.navigator.navigate_to_archiving()
        time.sleep(30)
        self.admin_console.refresh_page()
        self.archiving.access_server(self.hostname)
        self.admin_console.wait_for_completion()
        job_id = self.archiving.subclient_level_restore(
            restore_path=restore_path,
            unconditional_overwrite=True,
            notify=False,
            selected_files=[self.qualified_path],
            hadoop_restore=True,
            show_deleted_files=False)
        if self.commcell.job_controller.get(job_id).wait_for_completion(timeout=120):
            self.log.info("Job completed Successfully.")
            time.sleep(15)
        else:
            raise CVTestStepFailure("Job could not be completed")

    @test_step
    def restore_verify(self):
        """Recalls and Verifies checksum integrity of the given path"""

        qualified_data = self.client_machine.get_test_data_info(self.client_machine.join_path(
            self.restore_data_path, "qualified"))

        self.log.info(qualified_data)
        self.log.info(self.test_data_qualified)

        if "regularfile" in qualified_data:
            self.log.info("Qualified data restored correctly")
        else:
            raise Exception("Qualified data is not restored correctly.")

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

    def setup(self):
        """ Pre-requisites for this testcase """

        self.log.info("Initializing pre-requisites")
        self.hostname = f"automation_test"
        self.access_node = self.tcinputs.get("AccessNode")
        self.plan_name = f"plan{int(time.time())}"
        self.fs_plan = self.tcinputs.get("fsplan")
        self.test_path = self.tcinputs.get("TestPath", f"/automation/{self.id}")
        self.username = self.tcinputs.get("ImpersonateUser")
        self.password = self.tcinputs.get("Password")
        self.client_machine = Machine(hdfs_user="hdfs", machine_name=self.access_node,
                                      commcell_object=self.commcell, run_as_sudo=True)
        self.op_helper = cvonepas_helper(self)
        self.op_helper.client_machine = self.client_machine
        self.origin_path = self.client_machine.join_path(self.test_path, "origin")
        self.qualified_path = self.client_machine.join_path(self.origin_path, "qualified")
        self.unqualified_path = self.client_machine.join_path(self.origin_path, "unqualified")
        self.restore_data_path = self.client_machine.join_path(self.test_path, "restore_data")

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
        self.big_data = Instances(self.admin_console)
        self.navigator = self.admin_console.navigator

    def run(self):
        """Main function for test case execution"""

        _desc = """
        1) Add Hadoop Big Data Server.
        2) Create Archive plan.
        3) Add Existing Hadoop server on Archiver Page.
        4) Run Archive job.
        5) Verify eligible files got deleted.
        6) Run another Archive Job to mark deleted in index.
        7) Restore the data with option restore deleted items selected and verify qualified data files are restored.
        8) Verify restored data files.
        9) Delete Server.
        10) Delete Archive plan.
        """
        try:

            self.add_fs_server()

            self.create_archive_plan()

            self.add_server()

            self.run_archive_job()

            self.verify_delete()

            self.run_archive_job()

            self.run_restore_job(restore_path=self.restore_data_path)

            self.restore_verify()

            self.delete_server()

            self.delete_archive_plan()

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
