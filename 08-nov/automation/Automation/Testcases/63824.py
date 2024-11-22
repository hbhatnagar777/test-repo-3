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
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case


    Input Example:

    "testCases": {

		"63824": {
            "Regions": [],
            "CloudAccount": None,
            "CloudAccountPassword": None,
            "AccessNodes": [],
            "Plan": None,
            "SubscriptionId": None,
            "CredentialName": None,
            "TenantID": None,
            "ApplicationID": None,
            "ApplicationSecret": None
		}
    }
"""

import time

from Reports.utils import TestCaseUtils
from Application.CloudApps.azure_cosmos_sql_api import CosmosCassandraAPI
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import CosmosDBCassandraInstanceDetails

CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate Instance creation/backup/restore for CosmosDB Cassandra API Instance"""

    test_step = TestStep()

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Acceptance test for CosmosDB Cassandra API"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.dbinstances = None
        self.cosmoshelper = None
        self.orig_data = None
        self.restore_data = None
        self.dbinstancedetails = None
        self.cloudaccountname = None
        self.tcinputs = {
            "Regions": [],
            "CloudAccount": None,
            "CloudAccountPassword": None,
            "AccessNodes": [],
            "Plan": None,
            "SubscriptionId": None,
            "CredentialName": None,
            "TenantID": None,
            "ApplicationID": None,
            "ApplicationSecret": None
        }

    def refresh(self, wait_time=60):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
        self.admin_console.refresh_page()

    def navigate_to_database_page(self):
        """ Navigates to the input client page """
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_databases()
        self.refresh()

    def navigate_to_instance_page(self):
        """ Navigates to the input client page """
        self.navigate_to_database_page()
        self.dbinstances.access_instances_tab()
        self.refresh()

    def navigate_to_instance_details_page(self):
        """ Navigates to the input client page """
        self.navigate_to_instance_page()
        if self.dbinstances.is_instance_exists(
                DBInstances.Types.CLOUD_DB,
                self.instance_name,
                self.cloudaccountname):
            self.dbinstances.select_instance(
                DBInstances.Types.CLOUD_DB, self.instance_name)
        self.refresh()

    @test_step
    def delete_instance(self, instance_name):
        """Delete the instance"""
        self.navigate_to_instance_page()
        if self.dbinstances.is_instance_exists(
                DBInstances.Types.CLOUD_DB,
                instance_name,
                self.cloudaccountname):
            self.dbinstances.select_instance(
                DBInstances.Types.CLOUD_DB, instance_name)
            self.dbinstancedetails.delete_instance()

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion(timeout=60)

    def restore_from_calender(self, recovery_time=None):
        """
        Selects the backupset and calendar options then clicks on restore

        Args:
            calendar (dict): Dict containing year, month, date, hours, minutes
        """
        recovery_panel = RPanelInfo(
            self.admin_console,
            title="Recovery points")
        if recovery_time:
            calender = {
                'date': (recovery_time.split("-"))[0],
                'month': (recovery_time.split("-"))[1],
                'year': (recovery_time.split("-"))[2]
            }
            recovery_panel.date_picker(calendar)
        recovery_panel.click_button("Restore")

    @test_step
    def restore_from_instance(self):
        """in place restore from instance actions"""
        self.orig_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.navigate_to_instance_page()
        backup_jobid = self.dbinstances.backup(instance=self.instance_name)
        self.wait_for_job_completion(backup_jobid)
        self.cosmoshelper.drop_table(self.keyspace, self.tablename)
        self.navigate_to_instance_page()
        self.refresh()
        self.dbinstances.access_restore(instance=self.instance_name)
        restorepanel = self.dbinstancedetails.restore_folders(
            database_type=DBInstances.Types.COSMOSDB_CASSANDRA,
            dbaccount=self.tcinputs["CloudAccount"],
            items_to_restore=[self.keyspace])
        restore_jobid = restorepanel.in_place_restore(
            adjust_throughput=400, overwrite=True)
        self.wait_for_job_completion(restore_jobid)
        self.restore_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.validate_restore_data(self.orig_data, self.restore_data)

    @test_step
    def recover_point_restore_from_instance_prop(self):
        """restore from recover points under instance properties overview tab"""
        self.log.info(
            "restore from recoery pointunder instance properties overview tab")
        self.cosmoshelper.add_test_data(
            self.keyspace, self.tablename, user_ids=[6, 7])
        self.orig_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.navigate_to_instance_page()
        backup_jobid = self.dbinstances.backup(instance=self.instance_name)
        self.wait_for_job_completion(backup_jobid)
        self.cosmoshelper.drop_table(self.keyspace, self.tablename)
        self.navigate_to_instance_details_page()
        self.refresh()
        self.restore_from_calender()
        restorepanel = self.dbinstancedetails.restore_folders(
            database_type=DBInstances.Types.COSMOSDB_CASSANDRA,
            dbaccount=self.tcinputs["CloudAccount"],
            items_to_restore=[self.keyspace])
        restore_jobid = restorepanel.in_place_restore(
            adjust_throughput=400, overwrite=True)
        self.wait_for_job_completion(restore_jobid)
        self.restore_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.validate_restore_data(self.orig_data, self.restore_data)

    @test_step
    def recover_point_restore_from_subclient_prop(self):
        """restore from recovery point under subclient details page"""
        self.log.info(
            "restore from recovery point under subclient details page")
        self.cosmoshelper.add_test_data(
            self.keyspace, self.tablename, user_ids=[8, 9])
        self.orig_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.navigate_to_instance_page()
        backup_jobid = self.dbinstances.backup(instance=self.instance_name)
        self.wait_for_job_completion(backup_jobid)
        self.cosmoshelper.drop_table(self.keyspace, self.tablename)
        self.navigate_to_instance_details_page()
        self.dbinstancedetails.click_on_entity('default')
        self.refresh()
        self.restore_from_calender()
        restorepanel = self.dbinstancedetails.restore_folders(
            database_type=DBInstances.Types.COSMOSDB_CASSANDRA,
            dbaccount=self.tcinputs["CloudAccount"],
            items_to_restore=[self.keyspace])
        restore_jobid = restorepanel.in_place_restore(
            adjust_throughput=400, overwrite=True)
        self.wait_for_job_completion(restore_jobid)
        self.restore_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.validate_restore_data(self.orig_data, self.restore_data)

    @test_step
    def restore_from_job(self):
        """in place restore from job"""
        self.log.info("restore from job")
        self.cosmoshelper.create_table(self.keyspace, self.tablename2)
        self.cosmoshelper.add_test_data(
            self.keyspace, self.tablename2, user_ids=[
                1, 2, 3, 4, 5])
        self.orig_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename2)
        self.navigate_to_instance_page()
        backup_jobid = self.dbinstances.backup(instance=self.instance_name)
        self.wait_for_job_completion(backup_jobid)
        self.cosmoshelper.drop_table(self.keyspace, self.tablename2)
        self.navigate_to_instance_details_page()
        self.refresh()
        self.dbinstancedetails.list_backup_history_of_entity('default')

        myjobs = Jobs(self.admin_console)
        myjobs.access_job_by_id(job_id=backup_jobid)
        self.admin_console.click_button(value='Restore')
        time.sleep(240)
        restorepanel = self.dbinstancedetails.restore_folders(
            database_type=DBInstances.Types.COSMOSDB_CASSANDRA,
            dbaccount=self.tcinputs["CloudAccount"],
            items_to_restore=[self.keyspace])
        restore_jobid = restorepanel.in_place_restore(
            adjust_throughput=400, overwrite=True)
        self.wait_for_job_completion(restore_jobid)
        self.restore_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename2)
        self.validate_restore_data(self.orig_data, self.restore_data)

    @test_step
    def out_of_place_restore_from_job(self):
        """out of place restore from job"""
        self.log.info("out of place restore from job")
        self.cosmoshelper.truncate_table(self.keyspace, self.tablename)
        self.cosmoshelper.add_test_data(
            self.keyspace, self.tablename, user_ids=[11, 12])
        self.orig_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.navigate_to_instance_page()
        backup_jobid = self.dbinstances.backup(instance=self.instance_name)
        self.wait_for_job_completion(backup_jobid)
        self.cosmoshelper.drop_table(self.keyspace, self.tablename)
        self.navigate_to_instance_details_page()
        self.refresh()
        self.dbinstancedetails.list_backup_history_of_entity('default')

        myjobs = Jobs(self.admin_console)
        myjobs.access_job_by_id(job_id=backup_jobid)
        self.admin_console.click_button(value='Restore')
        time.sleep(240)
        restorepanel = self.dbinstancedetails.restore_folders(
            database_type=DBInstances.Types.COSMOSDB_CASSANDRA,
            dbaccount=self.tcinputs["CloudAccount"],
            items_to_restore=[self.keyspace])

        restore_jobid = restorepanel.out_of_place_restore(
            adjust_throughput=400, dest_keyspace='restore1', dest_table=None)
        self.wait_for_job_completion(restore_jobid)
        self.restore_data = self.cosmoshelper.get_rows(
            'restore1', self.tablename)
        self.validate_restore_data(self.orig_data, self.restore_data)

    def validate_restore_data(self, orig_data, dest_data):
        """compare the original data and the restored data"""
        if sorted(orig_data) == sorted(dest_data):
            self.log.info("restored data are same as original data")
        else:
            raise Exception("restored data does not match with original data")

    def populate_test_data(self):
        """populate test data"""
        self.cosmoshelper = CosmosCassandraAPI(
            cloudaccount=self.tcinputs["CloudAccount"],
            cloudaccount_password=self.tcinputs["CloudAccountPassword"])
        self.cosmoshelper.drop_keyspace(self.keyspace)
        self.cosmoshelper.drop_keyspace('restore1')
        self.cosmoshelper.create_keyspace(self.keyspace)
        self.cosmoshelper.create_table(self.keyspace, self.tablename)
        self.cosmoshelper.add_test_data(
            self.keyspace, self.tablename, user_ids=[
                1, 2, 3, 4, 5])

    @test_step
    def cleanup_testdata(self):
        """drop test keyspaces, disconnect db connections and delete db instances"""
        self.cosmoshelper.drop_keyspace(self.keyspace)
        self.cosmoshelper.drop_keyspace('restore1')
        self.cosmoshelper.disconnect()

    def setup(self):
        """Initializes object required for this testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self._inputJSONnode['commcell']['commcellUsername'],
                password=self._inputJSONnode['commcell']['commcellPassword'])
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception
        self.dbinstances = DBInstances(self.admin_console)
        self.dbinstancedetails = CosmosDBCassandraInstanceDetails(
            self.admin_console)
        self.instance_name = "automated_cosmosdb_cassandra_" + self.id
        self.cloudaccount = self.tcinputs["CloudAccount"]
        self.keyspace = 'automationks_' + self.id
        self.tablename = 'automationtb_' + self.id
        self.tablename2 = 'automationtb2_' + self.id
        self.cloudaccountname = self.tcinputs["CloudAccount"] + "_automation"
        self.pathlist = ["/" + self.cloudaccount]

    def run(self):
        """Run function of this testcase"""
        try:
            _desc = """
                This test case will cover CosmosDB Cassandra API acceptance test:
                1: delete instance if exist
                2: connect to cloud account populate test data
                3: create CosmosDB Cassandra AP instance
                4: Run full backup job and restore from protect -> databases instance page
                5: update data, run inc job and restore from RPC on instance properties page
                6: update data, run inc job and restore from RPC on subclient properties page
                7: update data, run inc job and restore from job
                8: update data, run inc job and out of restore from job
                9: delete test instances
                10: cleanup test data, drop db connections
            """
            self.log.info(_desc)
            self.delete_instance(self.instance_name)
            self.populate_test_data()
            self.dbinstances.add_cosmosdb_cassandra_instance(
                regions=self.tcinputs["Regions"],
                instance_name=self.instance_name,
                cloud_account=self.cloudaccountname,
                access_nodes=self.tcinputs["AccessNodes"],
                plan=self.tcinputs["Plan"],
                content=self.pathlist,
                subscription_id=self.tcinputs["SubscriptionId"],
                credential_name=self.tcinputs["CredentialName"],
                tenant_id=self.tcinputs["TenantID"],
                application_id=self.tcinputs["ApplicationID"],
                application_secret=self.tcinputs["ApplicationSecret"])
            self.restore_from_instance()
            self.recover_point_restore_from_instance_prop()
            self.recover_point_restore_from_subclient_prop()
            self.out_of_place_restore_from_job()
            self.restore_from_job()
            self.delete_instance(self.instance_name)
            self.cleanup_testdata()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
