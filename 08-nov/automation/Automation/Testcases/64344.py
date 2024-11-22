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

    restore()                   --  Method to restore data from previous cycle to salesforce and wait for job completion

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" parameter to run this testcase on an existing
    Salesforce pseudoclient. If not provided, a new pseudoclient will be created.

    "testCases": {
        "64344": {
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
                "db_type": "POSTGRESQL"
            },
            "postgresql_options": {
                "db_host_name": "",
                "db_user_name": "postgres",
                "db_password": ""
            }
            "profile": "Admin",
            "plan": "",
            "resource_pool": "",
            "storage_policy": "",
            "sf_object": "Contact",
            "fields": ["FirstName", "LastName", "Email", "Phone"]
        }
    }
"""
import random
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.AdminConsole.Salesforce.constants import GroupOperation, ColumnOperation
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore, SimplifiedFilterModel, RuleGroupModel, RuleModel
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper

DATABASE = 'tc_64344'
APP_NAME = f"TC_64344_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Object restore from previous cycle with field filters"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.app_name = APP_NAME
        self.restored_data = None

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.app_name = self.sf_helper.ClientName
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
        if self.status == PASSED:
            self.restored_data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.restored_data]
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.restored_data)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_database(DATABASE)

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE)
            self.sf_apps.add_org(
                org_name=self.app_name,
                plan=self.sf_helper.plan,
                oauth=True,
                **self.sf_helper.salesforce_options.__dict__,
                **infra_options.__dict__
            )
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_full(self):
        """Method to run full backup and wait for job completion"""
        try:
            return self.sf_app_details.backup(backup_type="full")[-1]
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def restore(self, backup_job_id):
        """Method to restore data from previous cycle to salesforce and wait for job completion"""
        try:
            backup_job = self.commcell.job_controller.get(backup_job_id)
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            self.sf_app_details.select_time_for_restore(datetime.fromtimestamp(backup_job.start_timestamp))
            self.restored_data = [self.data[i] for i in random.sample(range(0, len(self.data)-1), 5)]
            simplified_model = SimplifiedFilterModel(
                rule_groups=[RuleGroupModel(operation=GroupOperation.ALL,
                                            rules=[
                                                RuleModel(
                                                    column="FirstName",
                                                    value=record["FirstName"],
                                                    filter=ColumnOperation.EQUALS_TO),
                                                RuleModel(
                                                    column="LastName",
                                                    value=record["LastName"],
                                                    filter=ColumnOperation.EQUALS_TO)])
                             for record in self.restored_data],
                operation=GroupOperation.ANY)
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects/',
                file_folders=[self.sf_helper.sf_object],
                field_filters=simplified_model
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
            self.sf_apps.access_organization(self.app_name)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Main function for test case execution"""
        try:
            # Create new Salesforce App in Command Center
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()
            # Create new records in Salesforce object
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, self.data)
            # Run full backup
            job_id = self.backup_full()
            # Modify records in Salesforce object
            incremental_data = self.sf_helper.create_incremental_data(self.sf_helper.sf_object, self.data.copy())
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, incremental_data)
            # Run incremental backup
            self.backup_full()
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, incremental_data)
            # Run restore to Salesforce and validate
            self.restore(job_id)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, self.restored_data)
            # Delete Salesforce App
            if "ClientName" not in self.tcinputs:
                self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
