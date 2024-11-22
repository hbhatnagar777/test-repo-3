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

    run_metadata_restore_to_salesforce()        --  Runs metadata restore to Salesforce and waits for job completion

    run()                                       --  Run function for this test case

    tear_down()                                 --  Teardown function for this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs.

    "testCases": {
        "60486": {
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

DATABASE = 'tc_60486'
APP_NAME = f"TC_60486_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing Metadata backup and in place restore to cloud test case """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Metadata backup and in place restore to cloud"
        self.sf_helper = None
        self.custom_object = None

    def setup(self):
        """Setup function of this test case"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)

    def create_pseudoclient(self):
        """Creates new Salesforce pseudoclient"""
        self.client, self.instance, self.backupset, self.subclient = self.sf_helper.add_salesforce_client(
            name=APP_NAME,
            db_options={
                "db_enabled": True,
                "db_name": DATABASE
            }
        )
        self.subclient.enable_metadata()
        self.sf_helper.run_backup(self.subclient, "Full")

    def run_metadata_restore_to_salesforce(self):
        """Runs metadata restore to Salesforce and waits for job completion"""
        self.log.info(f"Running metadata restore to salesforce")
        job = self.instance.metadata_restore_to_salesforce(
            paths=[f"/Metadata/unpackaged/objects/{self.custom_object.fullName}.object"]
        )
        self.log.info(f"Job id is {job.job_id}. Waiting for completion")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run job: {job.job_id} with error: {job.delay_reason}")
        self.log.info(f"Successfully finished {job.job_id} job")

    def run(self):
        """Run function for this test case"""
        try:
            # Create a CustomObject in Salesforce
            self.custom_object = self.sf_helper.create_custom_object(APP_NAME)
            # Create a new Salesforce pseudoclient and enable metadata backup
            self.create_pseudoclient()
            # Run full backup
            self.sf_helper.run_backup(self.subclient, "Full")
            # Delete CustomObject in Salesforce
            self.sf_helper.delete_custom_object(self.custom_object.fullName)
            # Restore Metadata to Salesforce
            self.run_metadata_restore_to_salesforce()
            # Validate that CustomObject got recreated in Salesforce
            self.sf_helper.validate_object_exists_in_salesforce(self.custom_object)
        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function for this test case"""
        if self.status == constants.PASSED:
            self.sf_helper.delete_custom_object(self.custom_object.fullName)
            self.commcell.clients.delete(self.client.client_name)
