# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    wait_for_job_completion()   --  Waits for completion of job and gets the
                                    end date once job completes

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    create_sybase_helper_object()--  creates object of MYSQLHelper class

    backup_validate()          --  method to run backup job

    restore_validate()          --  method to run restore and validate test data

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "": {
                    "ClientName": "sybase_client",
                    "Plan": "plan",
                    "InstanceName": "sybase_instance",
                    "SA_Username": "sa_username",
                    "Password": "sa_password",
                    "OSUsername": "os_username",
                    "OSPassword": "os_password"
                }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.SybaseUtils.sybasehelper import SybaseHelper, SybaseCVHelper


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for Sybase Snap IDA on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Snap Command Center Acceptance"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.helper = None
        self.snapshot_enabled = None
        self.cv_helper = None
        self.restore_panel = None
        self.database_group = None
        self.database_name = "CV_70845"
        self.automation_instance = None
        self.instance = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "Plan": None,
            "SA_Username": None,
            "Password": None,
            "OSUsername": None,
            "OSPassword": None
        }
        self.snap_engine = self.tcinputs.get("SnapEngine") or "NetApp"

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open(maximize=True)
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.database_group = SubClient(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        self.cv_helper.sybase_cleanup_test_data(self.database_name)
        self.helper.sybase_helper_cleanup()

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.SYBASE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def add_instance(self):
        """Adds new instance"""
        unix = "windows" not in self.client.os_info.lower()
        self.database_instances.add_sybase_instance(server_name=self.tcinputs["ClientName"],
                                                    instance_name=self.tcinputs["InstanceName"],
                                                    plan=self.tcinputs["Plan"],
                                                    sa_user_name=self.tcinputs["SA_Username"],
                                                    password=self.tcinputs["Password"],
                                                    unix=unix,
                                                    os_user_name=self.tcinputs['OSUsername'],
                                                    os_password=self.tcinputs['OSPassword'])
        self.automation_instance = True

    @test_step
    def create_sybase_helper_object(self):
        """Creates object of sybasehelper class"""
        self.instance = self.client.agents.get("sybase").instances.get(
            self.tcinputs["InstanceName"])
        self.helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.cv_helper = SybaseCVHelper(self.helper)
        self.helper.csdb = self.csdb
        self.helper.sybase_sa_userpassword = self.helper.get_sybase_user_password()

    def backup_and_validate(self, backup_type):
        """Executes backup according to backup type
        Args:
            backup_type  (RBackup.BackupType):  Type of backup required
        """
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
        elif backup_type.value == "INCREMENTAL":
            self.log.info("Transaction Log Backup")
        job_id = self.database_group.backup(backup_type=backup_type)
        self.wait_for_job_completion(job_id)

    @test_step
    def restore_validate(self, user_database_name, user_table_list, db_list=None, all_db=False):
        """Executes restore according to restore type input and validates restore
            db_list  (list)          : List of databases to restore
            user_database_name (str) : database name to restore
            user_table_list (list)   : List of table list to restore
            all_db (Boolean)         : Executes full server restore
                default: False
        """
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["InstanceName"])
        status, all_database_list_before_restore = self.helper.get_database_list()
        all_table_list_before_restore = self.cv_helper.get_all_database_tables()
        table_content_before = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_before[table] = self.helper.get_table_content(
                user_database_name, table)

        self.log.info("Drop all user databases before full server restore")
        self.cv_helper.drop_user_databases(all_database_list_before_restore)

        self.log.info("Shutdown sybase server before full server restore")
        self.helper.shutdown_sybase_server()
        self.log.info("Shutdown of sybase server is successful")
        self.db_instance_details.access_restore()
        self.admin_console.wait_for_completion(wait_time=1000)

        if all_db:
            db_list = all_database_list_before_restore
        self.restore_panel = self.db_instance_details.restore_folders(
            DBInstances.Types.SYBASE, items_to_restore=db_list)
        job_id = self.restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)

        database_status = False
        table_status = False

        status, all_database_list_after_restore = self.helper.get_database_list()
        all_table_list_after_restore = self.cv_helper.get_all_database_tables()
        table_content_after = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_after[table] = self.helper.get_table_content(
                user_database_name, table)

        if all_database_list_before_restore == all_database_list_after_restore:
            database_status = True
        if self.cv_helper.comparing_dict_of_list(
                all_table_list_before_restore,
                all_table_list_after_restore):
            table_status = True
        table_content_status = self.cv_helper.comparing_dict_of_list(
            table_content_before, table_content_after)
        self.log.info("Database status : %s", database_status)
        self.log.info("Database List before : %s", all_database_list_before_restore)
        self.log.info("Database List after : %s", all_database_list_after_restore)
        self.log.info("Table List status after validation : %s", table_status)
        self.log.info("Table Content status after validation : %s", table_content_status)
        if database_status and table_status and table_content_status:
            return True
        else:
            raise CVTestStepFailure("Restore validation failed after full server restore")

    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.snapshot_enabled is not None and not self.snapshot_enabled:
            self.navigate_to_instance(self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
            self.db_instance_details.click_on_entity('default')
            self.database_group.disable_snapshot()
        if self.automation_instance:
            self.navigate_to_instance()
            self.db_instance_details.delete_instance()

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.SYBASE,
                                                          self.tcinputs["InstanceName"],
                                                          self.tcinputs["ClientName"]):
                self.log.info("Instance found")
            else:
                self.log.info("Instance not found. Creating new instance")
                self.add_instance()
                self.log.info("Instance successfully created")
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity("default")
            self.snapshot_enabled = self.database_group.is_snapshot_enabled()
            self.database_group.disable_snapshot()
            self.database_group.enable_snapshot(
                snap_engine=self.snap_engine)

            self.create_sybase_helper_object()
            user_tables = ["T_FULL", "T_TLOG1"]
            self.cv_helper.sybase_populate_data(self.database_name, user_tables[0])
            self.backup_and_validate(RBackup.BackupType.FULL)
            self.cv_helper.single_table_populate(self.database_name, user_tables[1])
            self.backup_and_validate(RBackup.BackupType.INCR)

            restore_status = self.restore_validate(user_database_name=self.database_name,
                                                   user_table_list=user_tables, all_db=True)
            if restore_status:
                self.log.info("Full Sybase Server Restore Succeeded")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
