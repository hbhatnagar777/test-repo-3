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

    run_restore_to_salesforce_from_database()   --  Runs restore to Salesforce from sync db

    validate_delete()                           --  Validates that data got deleted in Salesforce successfully

    run()                                       --  Run function for this test case

    teardown()                                  --  Teardown function for this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs.

    "testCases": {
        "60477": {
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
from AutomationUtils import constants
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Web.Common.page_object import TestStep

DATABASE = 'tc_60477'
APP_NAME = f"TC_60477_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing Restoring dependent objects to cloud test case """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Restoring dependent objects to cloud"
        self.sf_helper = None
        self.field_labels = ["Test Field 1", "Test Field 2"]
        self.parent_object = None
        self.parent_data = None
        self.immediate_child = None
        self.immediate_child_data = None
        self.all_children = list()
        self.all_children_data = list()

    def setup(self):
        """Setup function of this test case"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        self.sf_helper.create_new_postgresql_database(DATABASE)

    def create_pseudoclient(self):
        """Creates new Salesforce pseudoclient"""
        self.client, self.instance, self.backupset, self.subclient = self.sf_helper.add_salesforce_client(
            name=APP_NAME,
            db_options={
                "db_name": DATABASE
            }
        )

    def create_objects(self):
        """Creates hierarchy of objects in Salesforce"""
        self.parent_object, self.parent_data = self.sf_helper.create_test_object(
            label=f"{APP_NAME}_parent",
            field_labels=self.field_labels,
            rec_count=10
        )
        self.immediate_child, self.immediate_child_data = self.sf_helper.create_child_object(
            label=f"{APP_NAME}_child",
            parent_object=self.parent_object,
            field_labels=self.field_labels,
            rec_count=10
        )
        self.all_children.append(self.immediate_child)
        self.all_children_data.append(self.immediate_child_data)
        for i in range(2):
            child_object, child_data = self.sf_helper.create_child_object(
                label=f"{APP_NAME}_grandchild_{i+1}",
                parent_object=self.all_children[-1],
                field_labels=self.field_labels,
                rec_count=10
            )
            self.all_children.append(child_object)
            self.all_children_data.append(child_data)

    def run_restore_to_salesforce_from_database(self, dependent_level):
        """
        Runs restore to Salesforce from sync db

        Args:
            dependent_level (int): Dependent level for restore job (0, 1 or -1)

        Returns:
            None
        """
        self.log.info(f"Running restore to salesforce from database with dependent level {dependent_level}")
        job = self.instance.restore_to_salesforce_from_database(
            paths=[f"/Objects/{self.parent_object.fullName}"],
            dependent_restore_level=dependent_level
        )
        self.log.info(f"Job id is {job.job_id}. Waiting for completion")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run job: {job.job_id} with error: {job.delay_reason}")
        self.log.info(f"Successfully finished {job.job_id} job")

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
        self.log.info(f"Validating that {objects} are empty")
        for sf_object in objects:
            data = self.sf_helper.rest_query(f"SELECT Count(Id) FROM {sf_object.fullName}")
            if not (rec_count := data[0]['expr0']) == 0:
                raise Exception(f"Delete unsuccessful. Object {sf_object.fullName} still contains {rec_count} records")
            self.log.info(f"{sf_object.fullName} does not have any records")

    def run(self):
        """Run function for this test case"""
        try:
            # Create CustomObjects in Salesforce
            self.create_objects()
            # Create new Salesforce pseudoclient
            self.create_pseudoclient()
            # Run a full backup
            self.sf_helper.run_backup(self.subclient, 'Full')
            # Delete all objects in Salesforce and validate deletion
            for child_object, child_data in zip(reversed(self.all_children), reversed(self.all_children_data)):
                self.sf_helper.delete_object_data(child_object.fullName, child_data)
            self.sf_helper.delete_object_data(self.parent_object.fullName, self.parent_data)
            self.validate_delete(*self.all_children, self.parent_object)
            # Run restore to Salesforce with dependent level 'No Children'
            self.run_restore_to_salesforce_from_database(0)
            # Validate restore in Salesforce
            self.sf_helper.validate_object_data_in_salesforce(self.parent_object.fullName, self.parent_data)
            self.validate_delete(*self.all_children)
            # Delete objects in Salesforce
            self.sf_helper.delete_object_data(self.parent_object.fullName)
            self.validate_delete(self.parent_object)
            # Run restore to Salesforce with dependent level 'Immediate Children'
            self.run_restore_to_salesforce_from_database(1)
            # Validate restore in Salesforce
            self.sf_helper.validate_object_data_in_salesforce(self.parent_object.fullName, self.parent_data)
            self.sf_helper.validate_object_data_in_salesforce(self.immediate_child.fullName, self.immediate_child_data)
            self.validate_delete(*self.all_children[1:])
            # Delete objects in Salesforce
            self.sf_helper.delete_object_data(self.immediate_child.fullName)
            self.sf_helper.delete_object_data(self.parent_object.fullName)
            self.validate_delete(self.parent_object, self.immediate_child)
            # Run restore to Salesforce with dependent level 'All Children'
            self.run_restore_to_salesforce_from_database(-1)
            # Validate restore in Salesforce
            self.sf_helper.validate_object_data_in_salesforce(self.parent_object.fullName, self.parent_data)
            for child_object, child_data in zip(self.all_children, self.all_children_data):
                self.sf_helper.validate_object_data_in_salesforce(child_object.fullName, child_data)
        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function for this test case"""
        if self.status == constants.PASSED:
            for child_object in reversed(self.all_children):
                self.sf_helper.delete_custom_object(child_object.fullName)
            self.sf_helper.delete_custom_object(self.parent_object.fullName)
            self.sf_helper.delete_postgresql_database(DATABASE)
            self.commcell.clients.delete(self.client.client_name)
