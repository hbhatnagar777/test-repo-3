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

    run()           --  run function of this test case

"""
from time import sleep

from cvpysdk.job import Job
from cvpysdk.policies.storage_policies import StoragePolicies
from cvpysdk.subclient import Subclients

from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.SQL.configure_sql_replication_group import SQLServerReplication
from Web.AdminConsole.DR.monitor import ReplicationMonitor


from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
    CVWebAutomationException
)
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """Admin Console: SQL Live Sync"""

    test_step = TestStep()
    SUBCLIENT = ["TC54047_1", "TC54047_2"]
    DB_NAME = ["Dummy DB", "Dummy DB1", "Dummy DB2"]
    STAND_BY_GROUP_NAME = "StandBy"

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Admin Console: SQL Live Sync"
        self.utils = None
        self.browser = None
        self.webconsole = None
        self.replication = None
        self.sql_client = None
        self.admin_console = None
        self.navigator = None
        self._subclient = None
        self.tcinputs = {
            "DestinationClient": "string",
            "DestinationInstance": "string",
            "SQLSourceUsername": "string",
            "SQLSourcePassword": "string",
            "SQLDestinationUsername": "string",
            "SQLDestinationPassword": "string"
        }

    def init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.create_db()
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.replication = ReplicationGroup(self.admin_console)
            self.navigator.navigate_to_replication_groups_page()
            self.replication_details = ReplicationDetails(self.admin_console)
            self.sql_client = MSSQL(self._get_server_fqdn(self.tcinputs["DestinationInstance"]),
                                    self.tcinputs["SQLDestinationUsername"],
                                    self.tcinputs["SQLDestinationPassword"],
                                    "master", as_dict=False, use_pyodbc=True)

            self.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def create_db(self):
        """Creates a new subclient with a dummy DB and also performs full and transaction log
        backup"""
        subclients = Subclients(self.instance)

        sql_helper = SQLHelper(self,
                               self.tcinputs["ClientName"],
                               self._get_server_fqdn(self.instance.name),
                               self.tcinputs["SQLSourceUsername"],
                               self.tcinputs["SQLSourcePassword"])

        self.log.info("Deleting existing subclient created by the current testcase")
        subclient_name = TestCase.SUBCLIENT[0]
        iter_ = iter(TestCase.SUBCLIENT)
        for subclient in iter_:
            if subclients.has_subclient(subclient):
                subclients.delete(subclient)
                try:
                    subclient_name = next(iter_)
                except StopIteration:
                    pass
                break

        self.log.info("Deleting existing databases created by the current testcase")
        if sql_helper.dbinit.check_database(TestCase.DB_NAME[0]):
            sql_helper.dbinit.drop_databases(TestCase.DB_NAME[0])
        sql_helper.dbinit.db_new_create(TestCase.DB_NAME[0],
                                        noofdbs=2,
                                        nooffilegroupsdb=0,
                                        nooffilesfilegroup=0,
                                        nooftablesfilegroup=1,
                                        noofrowstable=1)

        sql_helper.create_subclient(subclient_name,
                                    [TestCase.DB_NAME[1], TestCase.DB_NAME[2]],
                                    list(StoragePolicies(
                                        self.commcell).all_storage_policies.keys())[0])

        subclients.refresh()
        self._subclient = subclients.get(subclient_name)
        sql_helper.sql_backup(backup_type="full")
        sleep(5)
        sql_helper.sql_backup(backup_type="transaction_log")

    def check_for_restored_databases(self, db_name):
        """Checks for the restored databases"""
        result = self.sql_client.execute("SELECT name FROM sys.databases")
        self.log.info("Checks for restored databases")
        if db_name not in list(map(lambda row: str(row[0]), result.rows)):
            raise CVTestStepFailure("Restoring DB is not present")

    def query_stand_by_database(self):
        """Queries the given database on the target machine"""
        self.log.info("Queries the standby database")
        try:
            self.sql_client.execute(f"Use [{TestCase.DB_NAME[2]}] Select t from tabm11")
        except Exception as excep:
            raise CVTestStepFailure(f"Failed to query stand by DB. {excep}")

    def check_for_job_completion(self, jobs):
        """Checks for the completion of job

        Args:
            jobs (dict): Dict of jobs which are currently running

        """
        latest_job = list()
        for attempt in range(101):
            self.log.info("Waiting for the job to be scheduled")
            sleep(3)
            jobs_ = self.commcell.job_controller.active_jobs(job_filter="replication")
            latest_job = jobs_.keys() - jobs.keys()
            if latest_job:
                break
        if not latest_job:
            raise CVTestStepFailure("Job is not being scheduled to run")
        latest_job = latest_job.pop()
        job = Job(self.commcell, latest_job)
        self.log.info(f"Job Id: {job.job_id}")
        if job.wait_for_completion() is False:
            raise CVTestStepFailure(
                f"Job: {latest_job}:{self.commcell.job_controller.get(latest_job).pending_reason}"
            )

    def cleanup(self):
        """Deletes the already existing replication group created by automation as well as
         replicated DB"""
        if self.replication.has_group(self.name):
            self.replication.delete_group(self.name)
        if self.replication.has_group(TestCase.STAND_BY_GROUP_NAME):
            self.replication.delete_group(TestCase.STAND_BY_GROUP_NAME)

        for db_ in TestCase.DB_NAME + ["Invoker"]:
            try:
                self.sql_client.execute(f"DROP DATABASE {db_};")
            except Exception:
                pass

    def check_source_and_target_versions(self):
        """Checks the source and destination MSSQL version"""
        sql_source = MSSQL(self._get_server_fqdn(self.instance.name),
                           self.tcinputs["SQLSourceUsername"],
                           self.tcinputs["SQLSourcePassword"],
                           "master", as_dict=False, use_pyodbc=True)

        src = self._get_mssql_version(sql_source)
        dst = self._get_mssql_version(self.sql_client)
        if src > dst:
            raise CVTestStepFailure(f"Destination version is greater than source.\n Source:{src} "
                                    f"\t Destination{dst}")

    @staticmethod
    def _get_mssql_version(mssql):
        result = mssql.execute("SELECT @@Version")
        version = result.rows[0][0].split(" ", 8)[-2]
        return int(version.replace(".", ""))

    def _get_server_fqdn(self, name):
        instance = name.upper()
        index = instance.find("\\")
        if index == -1:
            index = len(name)
        return (f'{self.commcell.clients[instance[:index].lower()]["hostname"].upper()}'
                f'{instance[index:]}')

    @test_step
    def create_replication_group(self, name, database, stand_by_mode=False):
        """Verifies the ability of the user to create a new replication group"""

        self.check_source_and_target_versions()
        sql_replication = SQLServerReplication(self.admin_console)
        self.replication.configure_sql_server_replication_group()
        sql_replication.set_source(name, self.tcinputs["ClientName"],
                                   self.tcinputs["InstanceName"].upper(), database)
        sql_replication.set_target(self.tcinputs["DestinationClient"],
                                   self.tcinputs["DestinationInstance"].upper())

        if stand_by_mode:
            sql_replication.set_advanced_options(sync_delay=0, standby=True,
                                                 undo_file_path=r"C:\CreatedByAutomation")

        jobs = self.commcell.job_controller.active_jobs(job_filter="replication")
        sql_replication.submit()
        self.check_for_job_completion(jobs)
        self.check_for_restored_databases(*database)

    @test_step
    def bring_db_online(self, group_name, database):
        """Brings the Replicated Databases in the replication group back online"""
        replication_monitor = ReplicationMonitor(self.browser.driver)
        self.navigator.navigate_to_replication_monitor()
        replication_monitor.bring_online(group_name)
        result = self.sql_client.execute(f"select state_desc as STATE from sys.databases WHERE "
                                         f"name = '{database}'")
        if result.rows[0][0] != 'ONLINE':
            raise CVTestStepFailure("Could not bring back the DB online")
        self.navigator.navigate_to_replication_groups_page()

    @test_step
    def edit_replication_group(self):
        """Verifies the ability of the user to edit the replication group"""
        self.replication.access_group(self.name)
        live_sync = ReplicationDetails(self.admin_console)
        sql_replication = live_sync.manage_content()
        sql_replication.edit_content()
        sql_replication.set_target()
        sql_replication.set_redirect_options(TestCase.DB_NAME[1],
                                             "Invoker",
                                             r"C:\CreatedByAutomation",
                                             r"C:\CreatedByAutomation")
        try:
            sql_replication.set_advanced_options()
            raise CVTestStepFailure("Able to edit Live Sync options under edit replication group")
        except CVWebAutomationException:
            pass
        sql_replication.save_edited_changes()
        self.replication_details.replicate_now(self.name)
        job_id = self.admin_console.get_jobid_from_popup()
        job = Job(self.commcell, job_id)
        if job.wait_for_completion() is False:
            raise CVTestStepFailure(
                f"Job: {job_id}:{self.commcell.job_controller.get(job_id).pending_reason}")
        self.check_for_restored_databases("Invoker")

    @test_step
    def delete_replication_group(self):
        """Verifies the ability of the user to delete the replication group"""
        self.navigator.navigate_to_replication_groups_page()
        self.replication.delete_group(self.name)
        self.replication.delete_group(TestCase.STAND_BY_GROUP_NAME)

    def run(self):
        """test cases steps"""
        try:
            self.init_tc()
            self.create_replication_group(self.name, [TestCase.DB_NAME[1]])
            self.bring_db_online(self.name, TestCase.DB_NAME[1])
            self.edit_replication_group()
            self.create_replication_group(TestCase.STAND_BY_GROUP_NAME, [TestCase.DB_NAME[2]],
                                          stand_by_mode=True)
            self.query_stand_by_database()
            self.bring_db_online(TestCase.STAND_BY_GROUP_NAME, TestCase.DB_NAME[1])
            self.delete_replication_group()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
