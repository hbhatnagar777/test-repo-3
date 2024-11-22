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

    run()                       --  run function of this test case

Input Example:

    "testCases": {
        "60607": {
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
        "60607": {
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
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Salesforce.data_masking import MaskType, Configuration, DataMasking
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType

DATABASE = 'tc_60607'
OUT_OF_PLACE_DATABASE = f"{DATABASE}_out_of_place"
APP_NAME = f"TC_60607_{datetime.now().strftime('%d_%B_%H_%M')}"
OUT_OF_PLACE_APP_NAME = f"{APP_NAME}_out_of_place"


class TestCase(CVTestCase):
    """Class for executing Out of place restore with data masking policy test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Out of place restore with data masking policy"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
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
        if self.status == PASSED:
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            if not("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
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
    def create_data_masking_policy(self):
        """Method to create new dictionary data masking policy"""
        try:
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.click_on_data_masking()
            describe = self.sf_helper.describe_object(self.sf_helper.sf_object)
            dictionary_configuration = Configuration(
                sobject=self.sf_helper.sf_object,
                fields=[field for field in describe['fields'] if field['name'] in self.sf_helper.fields],
                type=MaskType.dictionary
            )
            DataMasking(self.admin_console).add(APP_NAME, dictionary_configuration)
            self.admin_console.navigator.navigate_to_salesforce()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def restore(self):
        """Method to restore data from database to salesforce and wait for job completion"""
        try:
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.click_on_restore()
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects/',
                file_folders=[self.sf_helper.sf_object],
                destination_organization=self.out_of_place_org_name,
                masking_policies=[APP_NAME]
            )
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
            if not("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.create_apps()
            # Create new records in Salesforce object and validate records created successfully
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, self.data)
            # Run full backup
            self.backup_full()
            # Create a new data masking policy
            self.create_data_masking_policy()
            # Run out of place restore and validate
            self.restore()
            self.sf_helper.validate_dictionary_data_masking_policy(
                sobject=self.sf_helper.sf_object,
                field=self.sf_helper.fields[0],
                source_data=self.data,
                **self.sf_helper.out_of_place_options
            )
            # Delete Salesforce Apps
            if not("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
