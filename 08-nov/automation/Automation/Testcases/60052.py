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

    perform_hub_setup()         --  Created new tenant user and performs initial setup in hub

    create_org()                --  Method to create a new Salesforce app in commcell

    backup_full()               --  Method to run full backup and wait for job completion

    backup_incremental()        --  Method to run incremental backup and wait for job completion

    restore()                   --  Method to restore data from media to Salesforce and wait for job completion

    delete()                    --  Deletes Salesforce pseudoclient

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. If ring hostname is not provided, then the commcell hostname provided in
    the input json is used.

    "testCases": {
        "60052": {
            "salesforce_options": {
                "login_url": "https://login.salesforce.com",
                "salesforce_user_name": "",
                "salesforce_user_password": "",
                "salesforce_user_token": "",
                "consumer_id": "",
                "consumer_secret": "",
                "sandbox": false
            },
            "profile": "Admin",
            "sf_object": "Contact",
            "fields": ["FirstName", "LastName", "Email", "Phone"],
            "ring_hostname": ""
        }
    }
"""
from datetime import datetime
from cvpysdk.commcell import Commcell
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from AutomationUtils.config import get_config
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.salesforce import SalesforceHub
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations

TENANT_PASSWORD = get_config().Metallic.tenant_password


class TestCase(CVTestCase):
    """Class for executing basic acceptance test for Salesforce on Metallic"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Metallic_Salesforce_Acceptance"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.hub_management = None
        self.tenant_commcell = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.app_name = f"TC_60052_{datetime.now().strftime('%d_%B_%H_%M')}"

    def setup(self):
        """Method to setup test variables"""
        # Initialize SalesforceHelper and connect to Salesforce API
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        # Create new tenant user
        ring_hostname = self.tcinputs.get("ring_hostname", self.commcell.webconsole_hostname)
        self.hub_management = HubManagement(self, ring_hostname)
        company = datetime.now().strftime("Salesforce-Auto-%d-%b-%H-%M-%y")
        username = self.hub_management.create_tenant(
            company_name=company,
            email=f"cvautouser-{datetime.now().strftime('%d-%B-%H-%M')}@{company}.com"
        )
        self.tenant_commcell = Commcell(ring_hostname, username, TENANT_PASSWORD)
        self.log.info("Connection established with CS using new tenant user")
        # Open browser and login to Metallic Hub
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(username, TENANT_PASSWORD, stay_logged_in=True)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            self.hub_management.deactivate_tenant()
            self.hub_management.delete_tenant()

    @test_step
    def perform_hub_setup(self):
        """Created new tenant user and performs initial setup in hub"""
        try:
            SalesforceHub(self.admin_console).perform_initial_setup()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            self.sf_apps.add_org(
                org_name=self.app_name,
                click_on_add_org=False,
                **self.sf_helper.salesforce_options.__dict__,
                region="East US"
            )
            self.app_name = self.sf_app_details.org_name
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_full(self):
        """Method to run full backup and wait for job completion"""
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
        """Method to restore data from media to salesforce and wait for job completion"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.click_on_restore(self.app_name)
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects/',
                file_folders=[self.sf_helper.sf_object]
            )
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete(self):
        """Deletes Salesforce pseudoclient"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Main function for test case execution"""
        try:
            # Perform initial setup in Hub
            self.perform_hub_setup()
            # Setup testcase variables
            self.navigator = self.admin_console.navigator
            self.sf_apps = SalesforceOrganizations(self.admin_console, self.tenant_commcell)
            self.sf_app_details = SalesforceOverview(self.admin_console, self.tenant_commcell)
            # Create new Salesforce pseudoclient
            self.create_app()
            # Create new records in Salesforce object
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)
            # Run full backup
            self.sf_helper.wait_for_automatic_full(self.app_name)
            # Modify records in Salesforce object
            self.data = self.sf_helper.create_incremental_data(self.sf_helper.sf_object, self.data)
            # Run incremental backup
            self.backup_incremental()
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            self.data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.data]
            # Run restore to Salesforce and validate
            self.restore()
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, self.data)
            # Delete pseudoclient
            self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
