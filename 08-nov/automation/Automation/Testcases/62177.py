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

    create_org()                --  Method to create a new Salesforce app in commcell

    backup()                    --  Method to run full backup and wait for job suspend

    set_backup_api_limit()      --  Method to set backup API limit

    create_files()              --  Creates files in Salesforce if existing files do not hit API limit

    resume_job()                --  Method that resumes job and waits for completion

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. It is recommended to override the rec_count parameter as REST API is
    used for this testcase, and high rec_count will use up a lot of API calls. Pass the "ClientName" parameter to run
    this testcase on an existing Salesforce pseudoclient. If not provided, a new pseudoclient will be created.

    "testCases": {
        "62177": {
            "ClientName": "",
            "salesforce_options": {
                "login_url": "https://login.salesforce.com",
                "salesforce_user_name": "",
                "salesforce_user_password": "",
                "salesforce_user_token": "",
                "consumer_id": "",
                "consumer_secret": "",
                "sandbox": false
            },
            "infrastructure_options": {
                "access_node": "",
                "cache_path": "/var/cache/commvault",
                "db_type": "SQLSERVER"
            },
            "postgresql_options": {
                "db_host_name": "",
                "db_user_name": "",
                "db_password": ""
            },
            "sqlserver_options": {
                "db_host_name": "",
                "db_instance": "",
                "db_user_name": "",
                "db_password": ""
            },
            "plan": "",
            "rec_count": 100
        }
    }
"""
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Salesforce.configuration import SalesforceConfiguration
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType, CONTENT_DOCUMENT, CONTENT_VERSION

DATABASE = 'tc_62177'
ORG_NAME = f"TC_62177_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing basic acceptance test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: File backup with API limit"
        self.browser = None
        self.admin_console = None
        self.rec_count = None
        self.content_document = list()
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.sf_config = None
        self.org_name = ORG_NAME

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        self.rec_count = int(self.sf_helper.rest_limit / 100) + 10
        self.log.info(f"Salesforce API limit is {self.sf_helper.rest_limit}")
        self.log.info(f"Setting record count as {self.rec_count}")
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_sqlserver_database(DATABASE)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.admin_console.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceOrganizations(self.admin_console, self.commcell)
        self.sf_app_details = SalesforceOverview(self.admin_console, self.commcell)
        self.sf_config = SalesforceConfiguration(self.admin_console)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            if self.content_document:
                delete_data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.content_document]
                self.sf_helper.delete_object_data(CONTENT_DOCUMENT, delete_data)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_sqlserver_database(DATABASE)

    @test_step
    def create_org(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(
                db_name=DATABASE,
                db_type=DbType.SQLSERVER,
                **self.sf_helper.sqlserver_options.__dict__
            )
            self.sf_apps.add_org(
                org_name=self.org_name,
                plan=self.sf_helper.plan,
                oauth=False,
                **self.sf_helper.salesforce_options.__dict__,
                **infra_options.__dict__
            )
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_job_committed(self, job_id):
        """Method to validate job status to be committed"""
        try:
            if (status := self.commcell.job_controller.get(job_id).status.lower()) != 'committed':
                Exception(f"Job {job_id} finished with status {status}, instead of committed")
            self.log.info(f"Job {job_id} got Committed")
            return True
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_job_completed(self, job_id):
        """Method to validate job status to be completed"""
        try:
            if (status := self.commcell.job_controller.get(job_id).status.lower()) != 'completed':
                Exception(f"Job {job_id} finished with status {status}, instead of completed")
            self.log.info(f"Job {job_id} got completed")
            return True
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup(self):
        """Method to run full backup and wait for job to get suspended"""
        try:
            job_id, inc_job_id = self.sf_app_details.backup(backup_type='full', wait_for_job_completion=True)
            self.validate_job_committed(job_id)
            self.validate_job_committed(inc_job_id)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for completion"""
        try:
            job_id, = self.sf_app_details.backup()
            return job_id
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def set_backup_api_limit(self, limit):
        """
        Method to set backup API limit

        Args:
            limit (int): backup API limit (between 1 and 99)
        """
        try:
            self.sf_app_details.access_configuration_tab()
            self.sf_config.api_limit = limit
            self.sf_config.access_overview_tab()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_files(self, rec_count=None):
        """Creates files in Salesforce if existing files do not hit API limit"""
        count = self.sf_helper.rest_query(f"SELECT Count(Id) FROM {CONTENT_VERSION}", current_session=False)[0][
            'expr0']
        if count < (rec_count or self.rec_count):
            content_version2, content_document2 = self.sf_helper.create_files((rec_count or self.rec_count) - count)
            self.content_document.extend(content_document2)
            self.sf_helper.validate_files_in_salesforce(content_version2, content_document2)
        else:
            self.log.info(f"Found {count} records in ContentVersion. Skipping creating new files...")

    @test_step
    def resume_job(self, job_id):
        """
        Method that resumes job and waits for completion

        Args:
            job_id (int): Job id
        """
        try:
            job = self.commcell.job_controller.get(job_id)
            job.resume(wait_for_job_to_resume=True)
            self.log.info(f"Job {job_id} resumed successfully")
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete(self):
        """Deletes Salesforce app from Commcell"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.delete(force_delete=True)
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Main function for test case execution"""
        try:
            # Create new Salesforce App in Command Center
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.org_name)
            else:
                self.create_org()
            # Change backup API limit
            self.set_backup_api_limit(1)
            # Create new records in Salesforce object
            self.create_files()
            # Run full backup and wait for job to finish with Committed status
            self.backup()
            # Add more files
            self.set_backup_api_limit(2)
            self.create_files(self.rec_count*2)
            # Run incremental backup and wait for job to finish with Committed status
            job_id = self.backup_incremental()
            self.validate_job_committed(job_id)
            # Change backup API limit
            self.set_backup_api_limit(50)
            # Run incremental backup and validate job status as completed
            job_id = self.backup_incremental()
            self.validate_job_completed(job_id)
            # Delete Salesforce App
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_client(self.org_name)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
