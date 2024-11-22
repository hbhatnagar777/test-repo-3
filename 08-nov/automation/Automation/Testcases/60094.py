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
    the following variables in testcase inputs.

    "testCases": {
        "60094": {
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
from Application.CloudApps.SalesforceUtils.constants import DbType
from Web.Common.page_object import TestStep

DATABASE = 'tc_60094'
APP_NAME = f"TC_60094_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing Running incremental backups with schema change test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Running incremental backups with schema change"
        self.sf_helper = None
        self.field_labels = ["Test Field 1", "Test Field 2", "Test Field 3"]
        self.sf_object = None
        self.deleted_fields = None

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

    def run_restore_to_database_and_validate(self):
        """Runs out of place restore, waits for job completion and validates schema in database"""
        restore_db_name = DATABASE + "_restore"
        infra_options = self.sf_helper.updated_infrastructure_options(
            db_name=restore_db_name,
            db_type=DbType.POSTGRESQL
        )
        self.sf_helper.create_new_postgresql_database(restore_db_name)
        self.log.info(f"Running out of place restore to database {restore_db_name} on {infra_options.db_host_name}")
        job = self.instance.restore_to_database(
            paths=[f"/Objects/{self.sf_object.fullName}"],
            **infra_options.__dict__
        )
        self.log.info(f"Job id is {job.job_id}. Waiting for completion")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run job: {job.job_id} with error: {job.delay_reason}")
        self.log.info(f"Successfully finished {job.job_id} job")
        self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, restore_db_name)

    def run(self):
        """Run function for this test case"""
        try:
            # Create new Salesforce pseudoclient
            self.create_pseudoclient()
            # Create new CustomObject in Salesforce
            self.sf_object, _ = self.sf_helper.create_test_object(APP_NAME, self.field_labels[:-1])
            # Back up CustomObject and validates schema in syncdb
            self.sf_helper.run_backup(self.subclient, 'Full')
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, DATABASE)
            # Create new field in Salesforce, run backup and validate in syncdb
            self.sf_object, _ = self.sf_helper.create_field_for_incremental(self.sf_object, self.field_labels[-1])
            self.sf_helper.run_backup(self.subclient)
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, DATABASE)
            # Delete a field in Salesforce, run backup and validate in syncdb
            deleted_field = [field.fullName for field in self.sf_object.fields if field.label == self.field_labels[0]]
            self.sf_object = self.sf_helper.delete_custom_field(self.sf_object, deleted_field[0])
            self.sf_helper.run_backup(self.subclient)
            self.sf_helper.validate_schema_in_postgresql_database(self.sf_object, DATABASE, deleted_field)
            # Run out of place restore and validate
            self.run_restore_to_database_and_validate()
        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = exp
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function for this test case"""
        if self.status == constants.PASSED:
            self.sf_helper.delete_custom_object(self.sf_object.fullName)
            self.sf_helper.delete_postgresql_database(DATABASE)
            self.sf_helper.delete_postgresql_database(DATABASE + "_restore")
            self.commcell.clients.delete(self.client.client_name)
