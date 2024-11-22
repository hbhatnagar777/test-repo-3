# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"59503": {
          "cloud_account": "XXXXX",
          "plan": "plan",
          "account_uri": "https://XXXXX.documents.azure.com:443/",
          "account_key": "XXXXXXXX"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  Initialize TestCase class

    init_tc()                       --  Initial configuration for the test case

    navigate_to_cosmosdb_instance() --  Navigates to cosmosdb instance details page

    create_test_data()              --  Creates cosmosdb database, container and populates test data

    wait_for_job_completion()       --  Waits for job completion gets the object

    submit_backup()                 --  Submits CosmosDB backup and validates it

    submit_in_place_restore()       --  Submits in place restore of CosmosDB database

    cleanup()                       --  Delete the instance and subclient created by test case

    run()                           --  Run function of this test case

    tear_down()                     --  Tear down method to cleanup the entities
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.azure_cosmos_sql_api import CosmosSQLAPI


class TestCase(CVTestCase):
    """Command center: Acceptance test case for Azure Cosmos SQL API database"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command center: Acceptance test case for Azure Cosmos SQL API database"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.cosmosdb_helper = None
        self.cosmosdb_helper_dest = None
        self.cosmosdb_instance = None
        self.db_instance_details = None
        self.cosmosdb_subclient = None
        self.account_name = None
        self.tcinputs = {
            "cloud_account": None,
            "access_node": None,
            "plan": None,
            "account_uri": None,
            "account_key": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.database_instance = DBInstances(self.admin_console)
            self.database_type = self.database_instance.Types.COSMOSDB_SQL
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.cosmosdb_subclient = SubClient(self.admin_console)
            self.cosmosdb_helper = CosmosSQLAPI(self.tcinputs['account_uri'],
                                                self.tcinputs['account_key'])
            self.account_name = self.tcinputs['account_uri'].split('.')[0].split('//')[1]
            self.cosmosdb_helper_dest = CosmosSQLAPI(self.tcinputs['account_uri'],
                                                     self.tcinputs['account_key'])

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_cosmosdb_instance(self):
        """Navigates to cosmosdb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(
            self.database_instance.Types.CLOUD_DB,
            self.tcinputs['cloud_account'],
            self.tcinputs['cloud_account']
        )

    @test_step
    def create_test_data(self, database_name, container_name, partition_key):
        """Creates cosmosdb database, container and populates test data
        Args:
            database_name   (str):  Name of database to create
            container_name  (str):  Name of container to create
            partition_key   (str):  Name of partition key column
        """
        self.cosmosdb_helper.create_database(database_name)
        self.cosmosdb_helper.create_container(database_name, container_name, partition_key, 400)
        self.cosmosdb_helper.populate_container(database_name, container_name, partition_key, 20)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def submit_backup(self, level='Incremental'):
        """Submits CosmosDB backup and validates it
        Args:
            level    (str): Backup level- full or incremental

        """
        backup_type = RBackup.BackupType(level.upper())

        bkp = self.cosmosdb_subclient.backup(backup_type)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of cosmosdb container group failed")
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(bkp, level)

    @test_step
    def submit_in_place_restore(self, database_name):
        """Submits in place restore of CosmosDB database
        Args:
            database_name   (str):  Database to restore
        """
        self.db_instance_details.access_restore()
        mapping_dict = {
            self.account_name: [database_name]
        }
        restore_panel_obj = self.db_instance_details.restore_files_from_multiple_pages(
            self.database_type,
            mapping_dict,
            self.tcinputs['cloud_account']
        )
        jobid = restore_panel_obj.in_place_restore()
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")

    @test_step
    def cleanup(self):
        """Delete the Instances and subclients created by test case
        """
        self.navigator.navigate_to_db_instances()
        if self.database_instance.is_instance_exists(
                self.database_instance.Types.CLOUD_DB,
                self.tcinputs['cloud_account'],
                self.tcinputs['cloud_account']
        ):
            self.database_instance.select_instance(
                self.database_instance.Types.CLOUD_DB,
                self.tcinputs['cloud_account'],
                self.tcinputs['cloud_account']
            )
            errors = self.db_instance_details.delete_instance(check_errors=True)
            if errors:
                raise Exception(f"Instance deletion failed with error: {errors}")

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            self.cleanup()
            database_name = 'db_59503'
            container_name = 'container_59503'
            content = {
                self.account_name: {database_name: [container_name]}
            }
            self.create_test_data(database_name, container_name, 'uid')
            self.database_instance.add_cosmosdb_sql_instance(
                self.tcinputs['cloud_account'],
                self.tcinputs['access_node'],
                self.tcinputs['plan'],
                content=content
            )
            self.db_instance_details.click_on_entity('default')
            self.submit_backup(level='Full')
            self.cosmosdb_helper.populate_container(database_name, container_name, 'uid', 20, 21)
            self.submit_backup()
            self.navigate_to_cosmosdb_instance()
            self.submit_in_place_restore(database_name)
            self.cosmosdb_helper_dest.validate_container(database_name, container_name, 'uid', 40)
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """cleanup the CosmosDB database created by test tcase"""
        self.cosmosdb_helper.delete_database('db_59503')
