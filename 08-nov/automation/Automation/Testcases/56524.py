# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
 "56524": {
          "cloud_account": "XXXX",
          "plan": "XXXX",
          "access_key": "XXXX",
          "secret_key": "XXXX",
        }

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper


class TestCase(CVTestCase):
    """Admin Console: DynamoDB point in time restore with overwrite option"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DynamoDB point in time restore with overwrite option"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.database_instance = None
        self.database_type = None
        self.dynamodb_helper = None
        self.dynamodb_instance = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "secret_key": None,
            "access_key": None
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
            self.table = Rtable(self.admin_console)
            self.navigator.navigate_to_db_instances()
            self.database_instance = DBInstances(self.admin_console)
            self.database_type = self.database_instance.Types.DYNAMODB
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)
            self.dynamodb_helper = AmazonDynamoDBCLIHelper(
                self.tcinputs['secret_key'], self.tcinputs['access_key'])
            self.dynamodb_helper.initialize_client('us-east-2')

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_dynamodb_instance(self):
        """Navigates to dynamodb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'DynamoDB',
                                               self.tcinputs['cloud_account'])

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def submit_backup(self, backup_type=Backup.BackupType.INCR):
        """Submits DynamoDB backup and validates it
        Args:
            backup_type    (str): Backup type, full or incremental
        Returns:
            bkp            (str): The jobid of backup
        """
        bkp = self.dynamodb_subclient.backup(backup_type)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")
        job_type = 'Incremental'
        if backup_type == Backup.BackupType.FULL:
            job_type = 'Full'    
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(bkp, job_type)  
        return bkp

    @test_step
    def submit_point_in_time_restore(self, subclient, bkp_jobid, table_name):
        """Submits restore of given subclient to the PIT of given backup jobid
        Args:
                subclient   (str):  The subclient name to restore from

                bkp_jobid   (str):  The jobid of backup job to restore from

                table_name  (str):  Name of table to restore
        """
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.list_backup_history_of_entity(subclient)
        self.table.access_context_action_item(bkp_jobid,
                                              self.admin_console.props['action.restore'])
        mapping_dict = {
            'us-east-2': table_name
        }
        restore_panel_obj = self.dynamodb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'Sub_56524')
        jobid = restore_panel_obj.same_account_same_region()
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")

    @test_step
    def cleanup(self):
        """Delete the Instances and subclients created by test case"""
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.delete_instance()

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            table_name = 'TC_56524'
            partition_key = 'id'
            self.dynamodb_helper.create_dynamodb_table(table_name, partition_key)
            self.dynamodb_helper.populate_dynamodb_table(table_name, partition_key, 20)
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB', self.tcinputs['cloud_account']):
                self.cleanup()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'], 0)
            self.db_instance_details.click_on_entity('default')
            self.dynamodb_subclient.disable_backup()
            self.navigate_to_dynamodb_instance()
            add_subclient_obj = self.db_instance_details.click_add_subclient(self.database_type)
            subclient_content = ['US East (Ohio) (us-east-2)']
            add_subclient_obj.add_dynamodb_subclient('Sub_56524', self.tcinputs['plan'],
                                                     subclient_content)
            org_table_id = self.dynamodb_helper.get_table_id(table_name)

            # Run three backups and submit point in time restore to each backup and validate

            bkp_1 = self.submit_backup(backup_type=Backup.BackupType.FULL)
            self.dynamodb_helper.populate_dynamodb_table(table_name, 'id', 40)
            bkp_2 = self.submit_backup()
            self.dynamodb_helper.populate_dynamodb_table(table_name, 'id', 60)
            self.submit_backup()
            self.submit_point_in_time_restore('Sub_56524', bkp_1, table_name)
            bkp1_table_id = self.dynamodb_helper.get_table_id(table_name)
            if org_table_id == bkp1_table_id:
                raise CVTestStepFailure("Table was not overwritten after 1st restore")
            self.dynamodb_helper.validate_dynamodb_table(table_name, 'id', 20)
            self.submit_point_in_time_restore('Sub_56524', bkp_2, table_name)
            bkp2_table_id = self.dynamodb_helper.get_table_id(table_name)
            if org_table_id == bkp2_table_id:
                raise CVTestStepFailure("Table was not overwritten after 2nd  restore")
            self.dynamodb_helper.validate_dynamodb_table(table_name, 'id', 40)
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Cleanup the tables created on DynamoDB"""
        self.dynamodb_helper.delete_dynamodb_table('TC_56524')