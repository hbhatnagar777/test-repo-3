# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for testing file system restores

TestCase:
    __init__()                                  --  Initialize TestCase class

    setup()                                     --  Setup function for this test case

    create_app()                                --  Creates new Salesforce pseudoclient

    create_objects()                            --  Creates hierarchy of objects in Salesforce

    validate_object_data()                      --  Validates restored data with salesforce

    run()                                       --  Run function for this test case

    run_restore_to_file_system()                --  Runs restore to file system from sync db

    teardown()                                  --  Teardown function for this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "70786": {
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
from Web.AdminConsole.Salesforce.constants import DependentLevel, ReactRestoreTarget, ParentLevel
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType

DATABASE = 'tc_70786'
APP_NAME = f"TC_70786_{datetime.now().strftime('%d_%B_%H_%M')}"
FIELD_LABELS = ("SF_Field1", "SF_Field2")


class TestCase(CVTestCase):
    """Class for executing SF_ Prefix and Self-Reference Object test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: SF_ prefix and self-reference object"
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
        self.self_ref_obj = None
        self.self_ref_obj_data = None
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
            label=f"SF_{APP_NAME}_parent",
            field_labels=FIELD_LABELS,
            rec_count=10
        )
        self.immediate_child, self.immediate_child_data = self.sf_helper.create_child_object(
            label=f"SF_{APP_NAME}_child",
            parent_object=self.parent_object,
            field_labels=FIELD_LABELS,
            rec_count=10,
            relation_type="Lookup"
        )
        self.all_children.append(self.immediate_child)
        self.all_children_data.append(self.immediate_child_data)
        for i in range(2):
            child_object, child_data = self.sf_helper.create_child_object(
                label=f"SF_{APP_NAME}_grandchild_{i + 1}",
                parent_object=self.all_children[-1],
                field_labels=FIELD_LABELS,
                rec_count=10,
                relation_type="Lookup"
            )
            self.all_children.append(child_object)
            self.all_children_data.append(child_data)

    @test_step
    def create_self_ref_object(self):
        """Creates self-reference object in Salesforce"""
        self.self_ref_obj, self.self_ref_obj_data = self.sf_helper.create_test_object(
            label=f"{APP_NAME}",
            field_labels=FIELD_LABELS,
            rec_count=10
        )
        self.self_ref_obj = self.sf_helper.create_custom_field(self.self_ref_obj, self.self_ref_obj.label, "Lookup",
                                                               self.self_ref_obj)

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
            return self.sf_app_details.backup(backup_type="full")[0]
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
    def delete(self):
        """Deletes Salesforce app from Commcell"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def delete_all_object_data(self):
        """Deletes all object's data"""
        for child_object, child_data in zip(reversed(self.all_children), reversed(self.all_children_data)):
            self.sf_helper.delete_object_data(child_object.fullName, child_data)
        self.sf_helper.delete_object_data(self.parent_object.fullName, self.parent_data)

    @test_step
    def restore(self, sf_object):
        """
        Method to restore data from database to salesforce and wait for job completion

        Args:
            sf_object (str): Object name to restore
        """
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.click_on_restore()
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects/',
                file_folders=[sf_object],
                dependent_level=DependentLevel.ALL,
                parent_level=ParentLevel.ALL,
            )
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.org_name)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_object_data(self, objects, data):
        """
        Validates restored data

        Raises:
            Exception: if validation fails
        """
        try:
            for sf_object, obj_data in zip(objects, data):
                self.sf_helper.validate_object_data_in_salesforce(sf_object.fullName, obj_data)
        except Exception as exp:
            raise CVTestStepFailure from exp

    def update_reference_data(self, sf_object, data):
        """
        Updates reference data with new Ids

        Args:
            sf_object (str): Object name
            data (list): List of dictionaries containing object data
        """
        id_map = {record['Id']: record['Name'] for record in data}
        restored_data_map = {record['Name']: record['Id'] for record in
                             self.sf_helper.bulk_query(
                                 f"SELECT Id, Name from {sf_object} WHERE Name IN {tuple(record['Name'] for record in data)}")}
        for record in data:
            if record.get(sf_object):
                record[sf_object] = restored_data_map[id_map[record[sf_object]]]

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
            # Delete all objects data
            self.delete_all_object_data()
            # Restore immediate object with all parent and dependents
            self.restore(self.immediate_child.fullName)
            # Validate objects data
            self.validate_object_data([self.parent_object, *self.all_children],
                                      [self.parent_data, *self.all_children_data])
            # Create self-reference object
            self.create_self_ref_object()
            # Create reference records
            self.self_ref_obj_data = [*self.sf_helper.create_records(self.self_ref_obj.fullName, rec_count=10),
                                      *self.self_ref_obj_data]
            # Run incremental backup
            self.backup_incremental()
            # Delete self-reference object data
            self.sf_helper.delete_object_data(self.self_ref_obj.fullName, self.self_ref_obj_data)
            # Restore self-reference object
            self.restore(self.self_ref_obj.fullName)
            # Update new Ids in self-reference object data
            self.update_reference_data(self.self_ref_obj.fullName, self.self_ref_obj_data)
            # Validate self-reference object data
            self.sf_helper.validate_object_data_in_salesforce(self.self_ref_obj.fullName, self.self_ref_obj_data,
                                                              fields=[field for field in
                                                                      self.self_ref_obj_data[0].keys() if
                                                                      field != "Id"])
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
            self.sf_helper.delete_custom_object(self.self_ref_obj.fullName)
            for child_object in reversed(self.all_children):
                self.sf_helper.delete_custom_object(child_object.fullName)
            self.sf_helper.delete_custom_object(self.parent_object.fullName)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_postgresql_database(DATABASE)
