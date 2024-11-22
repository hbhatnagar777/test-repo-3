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
    __init__()                                          --  initialize TestCase class

    setup()                                             --  setup method for test case

    tear_down()                                         --  tear down method for testcase

    create_app_with_plan_and_password_authentication()  --  Method to create a new Salesforce app in commcell with plan
                                                            and password authentication

    create_app_with_plan_and_oauth_new_credentials()    --  Method to create a new Salesforce app in commcell with plan
                                                            and new Salesforce OAuth credentials

    create_app_with_plan_and_existing_credentials()     --  Method to create a new Salesforce app in commcell with plan
                                                            and existing Salesforce OAuth credentials

    create_app_with_resource_pool_and_password_authentication() --  Method to create a new Salesforce app in commcell
                                                            with resource pool and password authentication

    create_app_with_resource_pool_and_oauth()           --  Method to create a new Salesforce app in commcell with
                                                            resource pool and OAuth

    delete_credentials()                                --  Method to delete Salesforce connected app credentials from
                                                            commcell

    delete_app()                                        --  Method to delete Salesforce app

    run()                                               --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs.

    "testCases": {
        "60223": {
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
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Salesforce.salesforce_app_details import SalesforceAppDetails
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.salesforce_apps import SalesforceApps
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager

DATABASE = 'tc_60223'
APP_NAME = f"TC_60223_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing testcase to check Add app page in Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Create new app in Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.sf_apps = None
        self.sf_app = None
        self.credential_manager = None
        self.sf_helper = None
        self.salesforce_options = None
        self.infrastructure_options = None

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs)
        self.sf_helper.create_new_postgresql_database(DATABASE)
        self.salesforce_options = self.sf_helper.updated_salesforce_options(salesforce_credential_name=APP_NAME)
        self.infrastructure_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.log.info("Connection established with CS")
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceApps(self.admin_console, self.commcell)
        self.sf_app = SalesforceAppDetails(self.admin_console, self.commcell)
        self.credential_manager = CredentialManager(self.admin_console)

    @test_step
    def create_app_with_plan_and_password_authentication(self):
        """Method to create a new Salesforce app in commcell with plan and password authentication"""
        try:
            self.sf_apps.add_app(
                app_name=APP_NAME,
                plan=self.sf_helper.plan,
                oauth=False,
                **self.infrastructure_options.__dict__,
                **self.salesforce_options.__dict__,
            )
            self.sf_app.delete(retire=True)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_app_with_plan_and_oauth_new_credentials(self):
        """Method to create a new Salesforce app in commcell with plan and new Salesforce OAuth credentials"""
        try:
            self.sf_apps.add_app(
                app_name=APP_NAME,
                plan=self.sf_helper.plan,
                **self.infrastructure_options.__dict__,
                **self.salesforce_options.__dict__
            )
            self.sf_app.delete(retire=True)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_app_with_plan_and_existing_credentials(self):
        """Method to create a new Salesforce app in commcell with plan and existing Salesforce OAuth credentials"""
        try:
            self.sf_apps.add_app(
                app_name=APP_NAME,
                plan=self.sf_helper.plan,
                **self.infrastructure_options.__dict__,
                **self.salesforce_options.__dict__
            )
            self.sf_app.delete(retire=True)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_app_with_resource_pool_and_password_authentication(self):
        """Method to create a new Salesforce app in commcell with resource pool and password authentication"""
        try:
            self.sf_apps.add_app(
                app_name=APP_NAME,
                plan=self.sf_helper.resource_pool,
                oauth=False,
                **self.infrastructure_options.__dict__,
                **self.salesforce_options.__dict__
            )
            self.sf_app.delete(retire=True)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_app_with_resource_pool_and_oauth(self):
        """Method to create a new Salesforce app in commcell with resource pool and OAuth"""
        try:
            self.sf_apps.add_app(
                app_name=APP_NAME,
                plan=self.sf_helper.resource_pool,
                **self.infrastructure_options.__dict__,
                **self.salesforce_options.__dict__
            )
            self.sf_app.delete(retire=True)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete_credentials(self):
        """Method to delete Salesforce connected app credentials from commcell"""
        try:
            self.navigator.navigate_to_credential_manager()
            self.credential_manager.action_remove_credential(self.salesforce_options.salesforce_credential_name)
            self.navigator.navigate_to_salesforce()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def tear_down(self):
        """Teardown method for test case"""
        self.navigator.navigate_to_salesforce()
        if self.sf_apps.check_if_app_exists(APP_NAME):
            self.sf_apps.access_app(APP_NAME).delete(retire=True)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_app_with_plan_and_password_authentication()
            self.create_app_with_plan_and_oauth_new_credentials()
            self.create_app_with_plan_and_existing_credentials()
            self.delete_credentials()
            self.create_app_with_resource_pool_and_password_authentication()
            self.create_app_with_resource_pool_and_oauth()
        except Exception as exp:
            handle_testcase_exception(self, exp)
