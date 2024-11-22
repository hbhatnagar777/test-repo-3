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

    seed()                      --  Method to seed data from salesforce prod to sandbox and wait for job completion

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    "testCases": {
        "62176": {
            "out_of_place_options": {
                "login_url": "https://test.salesforce.com",
                "salesforce_user_name": "",
                "sandbox": true
            },
            "sf_object": "Account",
            "fields": ["Name"]
        }
    }

    The following inputs are optional and values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "62176": {
            "ClientName": "",
            "DestinationClientName": "",
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
        }
    }
"""
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.AdminConsole.Salesforce.SandboxSeeding import SalesforceSandboxSeed, TemplateConfig
from Web.AdminConsole.Salesforce.constants import SeedRecordType
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType

DATABASE = 'tc_62176'
OUT_OF_PLACE_DATABASE = f"{DATABASE}_out_of_place"
APP_NAME = f"TC_62176_{datetime.now().strftime('%d_%B_%H_%M')}"
OUT_OF_PLACE_APP_NAME = f"{APP_NAME}_out_of_place"


class TestCase(CVTestCase):
    """Class for executing sandbox seeding test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Sandbox seeding"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
        self.sandbox_seeding = None
        self.template_records = None
        self.template_name = APP_NAME
        self.out_of_place_org_name = OUT_OF_PLACE_APP_NAME

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
            self.out_of_place_org_name = self.sf_helper.DestinationClientName
        else:
            self.sf_helper.create_new_database(DATABASE)
            self.sf_helper.create_new_database(OUT_OF_PLACE_DATABASE)
        self.template_records = self.sf_helper.rec_count // 10
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
        self.sandbox_seeding = SalesforceSandboxSeed(self.admin_console)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            if not ("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.sf_helper.delete_database(DATABASE)
                self.sf_helper.delete_database(OUT_OF_PLACE_DATABASE)

    @test_step
    def create_apps(self):
        """Method to create a new Salesforce apps in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE, db_type=DbType.POSTGRESQL)
            self.sf_apps.add_org(
                org_name=APP_NAME,
                plan=self.sf_helper.plan,
                oauth=False,
                **self.sf_helper.salesforce_options.__dict__,
                **infra_options.__dict__
            )
            self.admin_console.navigator.navigate_to_salesforce()
            infra_options = self.sf_helper.updated_infrastructure_options(
                db_name=OUT_OF_PLACE_DATABASE,
                db_type=DbType.POSTGRESQL
            )
            sf_options = self.sf_helper.updated_salesforce_options(**self.sf_helper.out_of_place_options)
            self.sf_apps.add_org(
                org_name=OUT_OF_PLACE_APP_NAME,
                plan=self.sf_helper.plan,
                oauth=False,
                **sf_options.__dict__,
                **infra_options.__dict__
            )
            self.admin_console.navigator.navigate_to_salesforce()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_full(self):
        """Method to run full backup and wait for job completion"""
        try:
            self.sf_apps.backup(self.org_name, backup_type="full")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for job completion"""
        try:
            self.sf_apps.backup(self.org_name)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_seed_template(self):
        """Method to create new sandbox seeding template"""
        try:
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.access_sandbox_seed_tab()
            template_config = TemplateConfig(self.sf_helper.sf_object, SeedRecordType.RECENT_RECORDS, param=self.template_records)
            self.sandbox_seeding.create_new_template(self.template_name, [template_config])
            self.admin_console.navigator.navigate_to_salesforce()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def seed(self):
        """Method to run seeding job"""
        try:
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.access_sandbox_seed_tab()
            job_id = self.sandbox_seeding.seed_sandbox(self.template_name, self.out_of_place_org_name)
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
            self.admin_console.navigator.navigate_to_salesforce()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete(self):
        """Deletes Salesforce app from Commcell"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(OUT_OF_PLACE_APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Main function for test case execution"""
        try:
            # Create new Salesforce Apps in Command Center for source and destination organizations
            if not ("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.create_apps()
            # Create new records in Salesforce object
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)
            # # Run full backup
            self.backup_full()
            # Create Incremental data
            modified_data = self.sf_helper.modify_records(self.sf_helper.sf_object,
                                                          self.data[:self.template_records].copy())
            # Run Incremental backup
            self.backup_incremental()
            # Create a new sandbox seeding template
            self.create_seed_template()
            # Run seeding job
            self.seed()
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, modified_data,
                                                              **self.sf_helper.out_of_place_options)
            # Delete Salesforce Apps
            if not ("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.delete()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
