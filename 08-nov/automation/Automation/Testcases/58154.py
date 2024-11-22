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
from cvpysdk import job
from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper


class TestCase(CVTestCase):
    """Admin Console: Verify restartabiity for full and incremental backup"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify restartabiity for full and incremental backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.dynamodb_helper = None
        self.dynamodb_instance = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
        self.browse = None
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
            self.navigator.navigate_to_db_instances()
            self.database_instance = DBInstances(self.admin_console)
            self.database_type = self.database_instance.Types.DYNAMODB
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)
            self.browse = Browse(self.admin_console)
            self.dynamodb_helper = AmazonDynamoDBCLIHelper(
                self.tcinputs['secret_key'], self.tcinputs['access_key'])
            self.dynamodb_helper.initialize_client('ap-southeast-1')

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
    def validate_restartability(self):
        """Submits DynamoDB backup and validates job restartability

        Raises:
            Exception
                if job could not be suspended
                if backup job failed
        """
        count = 0
        bkp = self.dynamodb_subclient.backup()
        job_obj = job.Job(self.commcell, bkp)
        while count < 100:
            if job_obj.num_of_files_transferred > 0:
                job_obj.pause(wait_for_job_to_pause=True)
                break
            else:
                count += 1
                sleep(2)
        else:
            raise CVTestStepFailure("The job could not be suspended")
        self.log.info("Resuming the job after 10 seconds")
        sleep(10)
        job_obj.resume()
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")

    @test_step
    def submit_in_place_restore(self):
        """Submits in place restore

        Raises:
            Exception if restore job failed
        """
        self.dynamodb_subclient.access_restore()
        self.browse.access_folder('ap-southeast-1')
        table_list = self.browse.get_column_data('Table')
        mapping_dict = {
            'ap-southeast-1': table_list
        }
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.click_on_entity('Sub_58154')
        self.dynamodb_subclient.access_restore()
        restore_panel_obj = self.dynamodb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'Sub_58154')
        jobid = restore_panel_obj.same_account_same_region(adjust_write_capacity=1000)
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")

    @test_step
    def cleanup(self):
        """deletes the dynamodb instance"""
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.delete_instance()

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB',self.tcinputs['cloud_account']):
                self.cleanup()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'], 0)
            self.db_instance_details.click_on_entity('default')
            self.dynamodb_subclient.disable_backup()
            self.navigate_to_dynamodb_instance()
            add_subclient_obj = self.db_instance_details.click_add_subclient(self.database_type)
            subclient_content = ['Asia Pacific (Singapore) (ap-southeast-1)']
            add_subclient_obj.add_dynamodb_subclient('Sub_58154', self.tcinputs['plan'],
                                                     content=subclient_content,
                                                     streams=1,
                                                     adjust_read_capacity=0)
            self.log.info("Validating restart ability for full backup")
            self.validate_restartability()
            self.admin_console.refresh_page()
            self.log.info("Verifying restore from restarted backup")
            self.submit_in_place_restore()
            self.navigate_to_dynamodb_instance()
            self.db_instance_details.click_on_entity('Sub_58154')
            bkp = self.dynamodb_subclient.backup()
            job_status = self.wait_for_job_completion(bkp)
            if not job_status:
                raise CVTestStepFailure("Backup of dynamodb table group failed")
            self.admin_console.refresh_page()
            self.log.info("Validating restart ability for incremental backup")
            self.validate_restartability()
            self.admin_console.refresh_page()
            self.log.info("Verifying restore from restarted backup")
            self.submit_in_place_restore()
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
