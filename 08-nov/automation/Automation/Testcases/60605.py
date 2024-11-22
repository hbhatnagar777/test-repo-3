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
    __init__()                                  --  Initialize TestCase class

    setup()                                     --  Setup function for this test case

    create_pseudoclient()                       --  Creates new Salesforce pseudoclient

    run_restore_to_database_and_validate()      --  Runs out of place restore, waits for job completion and validates
                                                    schema in database

    run()                                       --  Run function for this test case

    teardown()                                  --  Teardown function for this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "60605": {
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
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Salesforce.constants import DependentLevel
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType

DATABASE = 'tc_60605'
APP_NAME = f"TC_60605_{datetime.now().strftime('%d_%B_%H_%M')}"
FIELD_LABELS = ("Test Field 1", "Test Field 2")


class TestCase(CVTestCase):
    """Class for executing Running incremental backups with schema change test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Restoring dependent objects to cloud (PostgreSQL)"
        self.sf_helper = None
        self.browser = None
        self.admin_console = None
        self.parent_object = None
        self.parent_data = None
        self.immediate_child = None
        self.immediate_child_data = None
        self.all_children = list()
        self.all_children_data = list()
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
        
    def create_objects(self):
        """Creates hierarchy of objects in Salesforce"""
        self.parent_object, self.parent_data = self.sf_helper.create_test_object(
            label=f"{APP_NAME}_parent",
            field_labels=FIELD_LABELS,
            rec_count=self.sf_helper.rec_count
        )
        self.immediate_child, self.immediate_child_data = self.sf_helper.create_child_object(
            label=f"{APP_NAME}_child",
            parent_object=self.parent_object,
            field_labels=FIELD_LABELS,
            rec_count=self.sf_helper.rec_count//10
        )
        self.all_children.append(self.immediate_child)
        self.all_children_data.append(self.immediate_child_data)
        for i in range(2):
            child_object, child_data = self.sf_helper.create_child_object(
                label=f"{APP_NAME}_grandchild_{i+1}",
                parent_object=self.all_children[-1],
                field_labels=FIELD_LABELS,
                rec_count=self.sf_helper.rec_count//10
            )
            self.all_children.append(child_object)
            self.all_children_data.append(child_data)

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
    def run_restore_to_salesforce(self, dependent_level):
        """
        Runs restore to Salesforce from sync db

        Args:
            dependent_level (DependentLevel): Dependent level for restore job

        Returns:
            None
        """
        try:
            self.log.info(f"Running restore to salesforce from database with dependent level {dependent_level}")
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.click_on_restore(self.org_name)
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects',
                file_folders=[self.parent_object.fullName],
                dependent_level=dependent_level
            )
            job = self.commcell.job_controller.get(job_id)
            self.log.info(f"Job id is {job.job_id}. Waiting for completion")
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job: {job.job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished {job.job_id} job")
        except Exception as exp:
            raise CVTestStepFailure from exp

    def validate_delete(self, *objects):
        """
        Validates that records got deleted from all Salesforce CustomObjects successfully

        Args:
            objects (CompoundValue): List of objects to validate

        Returns:
            None

        Raises:
            Exception: if number of records in any CustomObject is not zero
        """
        self.log.info(f"Validating that {[sobject.fullName for sobject in objects]} are empty")
        for sf_object in objects:
            data = self.sf_helper.rest_query(f"SELECT Count(Id) FROM {sf_object.fullName}")
            if not (rec_count := data[0]['expr0']) == 0:
                raise Exception(f"Delete unsuccessful. Object {sf_object.fullName} still contains {rec_count} records")
            self.log.info(f"{sf_object.fullName} does not have any records")

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
        """Run function for this test case"""
        try:
            # Create CustomObjects in Salesforce
            self.create_objects()
            # Create new Salesforce app
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()
            # Run a full backup
            self.backup_full()
            # Delete all objects in Salesforce and validate deletion
            for child_object, child_data in zip(reversed(self.all_children), reversed(self.all_children_data)):
                self.sf_helper.delete_object_data(child_object.fullName, child_data)
            self.sf_helper.delete_object_data(self.parent_object.fullName, self.parent_data)
            self.validate_delete(*self.all_children, self.parent_object)
            # Run restore to Salesforce with dependent level 'No Children'
            self.run_restore_to_salesforce(DependentLevel.NONE)
            # Validate restore in Salesforce
            self.sf_helper.validate_object_data_in_salesforce(self.parent_object.fullName, self.parent_data)
            self.validate_delete(*self.all_children)
            # Delete objects in Salesforce
            self.sf_helper.delete_object_data(self.parent_object.fullName)
            self.validate_delete(self.parent_object)
            # Run restore to Salesforce with dependent level 'Immediate Children'
            self.run_restore_to_salesforce(DependentLevel.IMMEDIATE)
            # Validate restore in Salesforce
            self.sf_helper.validate_object_data_in_salesforce(self.parent_object.fullName, self.parent_data)
            self.sf_helper.validate_object_data_in_salesforce(self.immediate_child.fullName, self.immediate_child_data)
            self.validate_delete(*self.all_children[1:])
            # Delete objects in Salesforce
            self.sf_helper.delete_object_data(self.immediate_child.fullName)
            self.sf_helper.delete_object_data(self.parent_object.fullName)
            self.validate_delete(self.parent_object, self.immediate_child)
            # Run restore to Salesforce with dependent level 'All Children'
            self.run_restore_to_salesforce(DependentLevel.ALL)
            # Validate restore in Salesforce
            self.sf_helper.validate_object_data_in_salesforce(self.parent_object.fullName, self.parent_data)
            for child_object, child_data in zip(self.all_children, self.all_children_data):
                self.sf_helper.validate_object_data_in_salesforce(child_object.fullName, child_data)
            # Delete Salesforce App
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
            for child_object in reversed(self.all_children):
                self.sf_helper.delete_custom_object(child_object.fullName)
            self.sf_helper.delete_custom_object(self.parent_object.fullName)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_postgresql_database(DATABASE)
