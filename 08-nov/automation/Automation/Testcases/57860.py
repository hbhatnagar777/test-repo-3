# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function for this test case

    create_pseudoclient()   --  Creates new Salesforce pseudoclient

    restore()               --  Runs object level restore to Salesforce and waits for completion

    run()                   --  run function of this test case

    teardown()              --  teardown function for this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by provided any of
    the following variables in testcase inputs.

    "testCases": {
        "57860": {
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

DATABASE = 'tc_57860'
APP_NAME = f"TC_57860_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing ACCT1 of Salesforce backup and Restore test case """

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: ACCT1"
        self.data = None
        self.sf_helper = None

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
                "db_name": DATABASE,
                "db_type": DbType.POSTGRESQL
            }
        )

    def restore(self):
        """Runs object level restore to Salesforce and waits for completion"""
        self.log.info("Running restore to salesforce from database")
        job = self.instance.restore_to_salesforce_from_database()
        self.log.info(f"Job id is {job.job_id}. Waiting for completion")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run job: {job.job_id} with error: {job.delay_reason}")
        self.log.info(f"Successfully finished {job.job_id} job")

    def run(self):
        """Main function for test case execution"""
        try:
            # Add records to Salesforce object
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)
            # Create new Salesforce pseudoclient
            self.create_pseudoclient()
            # Run full backup
            self.sf_helper.run_backup(self.subclient, 'Full')
            # Modify records in Salesforce object
            self.data = self.sf_helper.create_incremental_data(self.sf_helper.sf_object, self.data)
            # Run incremental backup
            self.sf_helper.run_backup(self.subclient)
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            # Run restore to Salesforce and validate
            self.restore()
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, self.data)
        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes the test data"""
        if self.status == constants.PASSED:
            self.data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.data]
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            self.sf_helper.delete_postgresql_database(DATABASE)
            self.commcell.clients.delete(self.client.client_name)
