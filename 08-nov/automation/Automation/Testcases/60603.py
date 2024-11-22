# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  Initialize TestCase class

    setup()                                 --  Setup function for this test case

    create_app()                            --  Method to create a new Salesforce app in commcell

    backup_full()                           --  Method to run full backup and wait for job completion

    backup_incremental()                    --  Method to run incremental backup and wait for job completion

    run_restore_to_database_and_validate()  --  Runs out of place restore, waits for job completion and validates
    schema in database

    run()                                   --  Run function for this test case

    delete()                                --  Deletes Salesforce app from commcell

    tear_down()                             --  Teardown function for this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "60603": {
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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.AdminConsole.Salesforce.constants import ReactRestoreTarget
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType

DATABASE = 'tc_60603'
APP_NAME = f"TC_60603_{datetime.now().strftime('%d_%B_%H_%M')}"
FIELD_LABELS = ("Test Field 1", "Test Field 2", "Test Field 3")


class TestCase(CVTestCase):
    """Class for executing Running incremental backups with schema change test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Incremental backups with schema change (PostgreSQL)"
        self.browser = None
        self.admin_console = None
        self.sf_object = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
        self.sync_db_name = DATABASE

    def setup(self):
        """Setup function of this test case"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
            self.sync_db_name = self.sf_helper.sync_db_name(self.org_name).lower()
        else:
            self.sf_helper.create_new_postgresql_database(DATABASE)
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

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE, db_type=DbType.POSTGRESQL)
            self.sf_apps.add_org(
                org_name=APP_NAME,
                plan=self.sf_helper.plan,
                oauth=False,
                **self.sf_helper.salesforce_options.__dict__,
                **infra_options.__dict__
            )
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
    def run_restore_to_database_and_validate(self):
        """Runs out of place restore, waits for job completion and validates schema in database"""
        try:
            restore_db_name = DATABASE + "_restore"
            infra_options = self.sf_helper.updated_infrastructure_options(
                db_name=restore_db_name,
                db_type=DbType.POSTGRESQL
            )
            self.sf_helper.create_new_postgresql_database(restore_db_name)
            self.log.info(f"Running out of place restore to database {restore_db_name} on {infra_options.db_host_name}")
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.click_on_restore(self.org_name)
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects',
                file_folders=[self.sf_object.fullName],
                restore_target=ReactRestoreTarget.DATABASE,
                **infra_options.__dict__
            )
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, restore_db_name)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete(self):
        """Deletes Salesforce pseudoclient"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Run function for this test case"""
        try:
            # Create new CustomObject in Salesforce
            self.sf_object, _ = self.sf_helper.create_test_object(APP_NAME, FIELD_LABELS[:-1])
            # Create new Salesforce pseudoclient
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()
            # Back up CustomObject and validates schema in syncdb
            self.backup_full()
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, self.sync_db_name)
            # Create new field in Salesforce, run backup and validate in syncdb
            self.sf_object, _ = self.sf_helper.create_field_for_incremental(self.sf_object, FIELD_LABELS[-1])
            self.backup_incremental()
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, self.sync_db_name)
            # Delete a field in Salesforce, run backup and validate in syncdb
            deleted_field = [field.fullName for field in self.sf_object.fields if field.label == FIELD_LABELS[0]]
            self.sf_object = self.sf_helper.delete_custom_field(self.sf_object, deleted_field[0])
            self.backup_incremental()
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, self.sync_db_name, deleted_field)
            # Run out of place restore and validate
            self.run_restore_to_database_and_validate()
            # Delete Salesforce pseudoclient
            if "ClientName" not in self.tcinputs:
                self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Teardown function for this test case"""
        if self.status == PASSED:
            self.sf_helper.delete_custom_object(self.sf_object.fullName)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_postgresql_database(DATABASE)
            self.sf_helper.delete_postgresql_database(DATABASE + "_restore")
