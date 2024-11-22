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

    create_app()                --  Method to create a new Salesforce app in commcell

    backup_full()               --  Method to run full backup and wait for job completion

    backup_incremental()        --  Method to run incremental backup and wait for job completion

    restore()                   --  Method to restore data from database to salesforce and wait for job completion

    delete()                    --  Deletes Salesforce app from Commcell

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "60604": {
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
                "db_type": "POSTGRESQL",
                "db_host_name": "",
                "db_user_name": "postgres",
                "db_password": ""
            },
            "profile": "Admin",
            "plan": "",
            "resource_pool": "",
            "storage_policy": "",
            "sf_object": "Contact",
            "fields": ["FirstName", "LastName", "Email", "Phone"]
        }
    }
"""
from datetime import datetime
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations

DATABASE = 'tc_60604'
APP_NAME = f"TC_60604_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing basic acceptance test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Metadata backup and in place restore to cloud"
        self.browser = None
        self.admin_console = None
        self.sf_object = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_database(DATABASE)
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

    def tear_down(self):
        """Tear down method for testcase"""
        if "ClientName" not in self.tcinputs:
            self.sf_helper.delete_database(DATABASE)
        if self.status == PASSED:
            self.sf_helper.delete_custom_object(self.sf_object.fullName)

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE, db_type=DbType.POSTGRESQL)
            sf_options = self.sf_helper.updated_salesforce_options(salesforce_credential_name=APP_NAME)
            self.sf_apps.add_org(
                org_name=APP_NAME,
                plan=self.sf_helper.plan,
                oauth=False,
                **sf_options.__dict__,
                **infra_options.__dict__,
            )
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_full(self):
        """Method to run full backup wait for job completion"""
        try:
            self.sf_app_details.backup(backup_type="full")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for job completion"""
        try:
            self.sf_app_details.backup()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def restore(self):
        """Method to restore data from database to salesforce and wait for job completion"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.click_on_restore(self.org_name)
            job_id = RSalesforceRestore(self.admin_console).metadata_restore(
                path='/Metadata/unpackaged/objects',
                file_folders=[f'{self.sf_object.fullName}.object']
            )
            job = self.commcell.job_controller.get(job_id)
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
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Main function for test case execution"""
        try:
            # Create new Salesforce app in Command Center and set metadata restore
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()
            # Add metadata to Content
            self.sf_app_details.content = [
                self.admin_console.props['label.allSfMetadata'],
                self.admin_console.props['label.allSfFiles']
            ]
            # Create new custom object in Salesforce
            self.sf_object = self.sf_helper.create_custom_object(APP_NAME)
            # Run full backup
            self.backup_full()
            # Modify custom object definition
            self.sf_object = self.sf_helper.create_custom_field(self.sf_object, 'Incremental Field')
            # Run incremental backup
            self.backup_incremental()
            # Delete data from Salesforce
            self.sf_helper.delete_custom_object(self.sf_object.fullName)
            # Run restore
            self.restore()
            # Validate in Salesforce
            self.sf_helper.validate_object_exists_in_salesforce(self.sf_object)
            # Delete Salesforce app
            if "ClientName" not in self.tcinputs:
                self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
