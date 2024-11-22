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

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.


    "testCases": {
        "64413": {
            "ClientName": "",
            "DestinationClient": "",
            "salesforce_options": {
                "login_url": "https://login.salesforce.com",
                "salesforce_user_name": "",
                "salesforce_user_password": "",
                "salesforce_user_token": "",
                "consumer_id": "",
                "consumer_secret": "",
                "sandbox": false
            },
            "out_of_place_options": {
                "login_url": "https://test.salesforce.com",
                "salesforce_user_name": "",
                "sandbox": true
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
from Web.AdminConsole.Salesforce.constants import FieldMapping, ParentLevel, DependentLevel
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType

DATABASE = 'tc_64413'
OUT_OF_PLACE_DATABASE = 'tc_64413_out_of_place'
APP_NAME = f"TC_64413_{datetime.now().strftime('%d_%B_%H_%M')}"
OUT_OF_PLACE_APP_NAME = f"TC_64413_{datetime.now().strftime('%d_%B_%H_%M')}_out_of_place"
FIELD_LABELS = ("Test Field 1", "Test Field 2")
FIELD_LABELS_IN_SF = ("TestField1__c", "TestField2__c")


class TestCase(CVTestCase):
    """Class for executing Out of place restore with CvExternalId test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Out of place restore with CvExternalId Field Mapping"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.parent_object = None
        self.parent_data = None
        self.immediate_child = None
        self.immediate_child_data = None
        self.all_children = list()
        self.all_children_data = list()
        self.created_objects = None
        self.created_data = None
        self.sf_helper = None
        self.sf_helper_out_of_place = None
        self.sf_apps = None
        self.sf_app_details = None
        self.sf_object = None
        self.org_name = APP_NAME
        self.out_of_place_org_name = OUT_OF_PLACE_APP_NAME

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper_out_of_place = SalesforceHelper(
            self.tcinputs | {'salesforce_options': self.tcinputs.get("out_of_place_options")},
            self.commcell)
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
            for obj in reversed(self.created_objects):
                self.sf_helper.delete_custom_object(obj)
                self.sf_helper_out_of_place.delete_custom_object(obj)
            if not ("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.sf_helper.delete_database(DATABASE)
                self.sf_helper.delete_database(OUT_OF_PLACE_DATABASE)

    def create_objects(self):
        """Creates hierarchy of objects in Salesforce"""
        self.parent_object, self.parent_data = self.sf_helper.create_test_object(
            label=f"{APP_NAME}_parent",
            field_labels=FIELD_LABELS,
            rec_count=10
        )
        self.immediate_child, self.immediate_child_data = self.sf_helper.create_child_object(
            label=f"{APP_NAME}_child",
            parent_object=self.parent_object,
            field_labels=FIELD_LABELS,
            rec_count=10
        )
        self.all_children.append(self.immediate_child)
        self.all_children_data.append(self.immediate_child_data)
        for i in range(2):
            child_object, child_data = self.sf_helper.create_child_object(
                label=f"{APP_NAME}_grandchild_{i + 1}",
                parent_object=self.all_children[-1],
                field_labels=FIELD_LABELS,
                rec_count=10
            )
            self.all_children.append(child_object)
            self.all_children_data.append(child_data)
        self.created_objects = [self.parent_object.fullName,
                                *[child.fullName for child in self.all_children]]
        self.created_data = [self.parent_data,  *self.all_children_data]

    @test_step
    def validate_object_data(self, objects, data):
        """
        Validates restored data with sandbox

        Raises:
            Exception: if validation fails
        """
        try:

            for sf_object, obj_data in zip(objects, data):
                self.sf_helper_out_of_place.validate_object_data_in_salesforce(
                    sf_object, obj_data, fields=FIELD_LABELS_IN_SF)

        except Exception as exp:
            raise CVTestStepFailure from exp

    def modify_data(self, objects, data):
        """
        Modifies data in Salesforce

        Args:
            objects (list): List of Salesforce objects
            data (list): List of data to modify

        Returns:
            list: Objects
            list: Modified data
        """
        for sf_object, obj_data in zip(objects, data):
            filtered_data = [{key: val for key, val in row.items() if key in ("Id", *FIELD_LABELS_IN_SF)} for row in
                             obj_data]
            obj_data[:10] = self.sf_helper.modify_records(sf_object, filtered_data)
        return objects, data

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
            self.sf_app_details.content = ['All metadata']
            self.admin_console.navigator.navigate_to_salesforce()
            infra_options = self.sf_helper_out_of_place.updated_infrastructure_options(
                db_name=OUT_OF_PLACE_DATABASE,
                db_type=DbType.POSTGRESQL
            )
            sf_options = self.sf_helper_out_of_place.updated_salesforce_options(
                **self.sf_helper_out_of_place.out_of_place_options)
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
    def restore_object_metadata(self):
        """Method to restore object metadata to salesforce and wait for job completion"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.refresh_orgs()
            self.sf_apps.click_on_restore(self.org_name)
            job_id = RSalesforceRestore(self.admin_console).metadata_restore(
                path='/Metadata/unpackaged/objects',
                file_folders=[f"{obj}.object" for obj in self.created_objects],
                destination_organization=self.out_of_place_org_name,
            )
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
        except Exception as exp:
            raise CVTestStepFailure from exp

    def update_field_perms(self, objects, fields):
        """Updates field permissions on sandbox"""
        for sf_object in objects:
            for field in fields:
                self.sf_helper_out_of_place.update_field_permissions(sf_object, field)

    @test_step
    def restore(self):
        """Method to restore data from database to salesforce and wait for job completion"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.org_name)
            self.sf_app_details.click_on_restore()
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects/',
                file_folders=[self.immediate_child.fullName],
                destination_organization=self.out_of_place_org_name,
                field_mapping=FieldMapping.CV_EXTERNAL_ID,
                dependent_level=DependentLevel.ALL,
                parent_level=ParentLevel.ALL,
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
            if not ("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.create_apps()
            # Create hierarchy of objects in Salesforce
            self.create_objects()
            # Run full backup
            self.backup_full()
            # Run object metadata restore to sandbox
            self.restore_object_metadata()
            # Update Field Permissions on sandbox
            self.update_field_perms(self.created_objects, FIELD_LABELS_IN_SF)
            # Run object restore to sandbox
            self.restore()
            # Validate records got restored in sandbox
            self.validate_object_data(self.created_objects, self.created_data)
            # Modify data in production org
            self.created_objects, self.created_data = self.modify_data(self.created_objects, self.created_data)
            # Run incremental backup
            self.backup_incremental()
            # Run out of place restore
            self.restore()
            # Validate changed records got restored in sandbox
            self.validate_object_data(self.created_objects, self.created_data)
            # Delete Salesforce Apps
            if not ("ClientName" in self.tcinputs and "DestinationClientName" in self.tcinputs):
                self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
