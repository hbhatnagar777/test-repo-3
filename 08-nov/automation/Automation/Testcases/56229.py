# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    setup()                --  setup function of this test case

    run()                  --  run function of this test case
"""

import traceback
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps.amazon_helper import AmazonCloudDatabaseHelper
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper


class TestCase(CVTestCase):
    """Test case class for testing Amazon DynamoDB basic backup and restore operations

        Input JSON:

            Required Parameters Example:
            {
                "ClientName":   "Automation",
                "InstanceName": "DynamoDB",
                "AccessNode":   "AmazonCS",
                "StoragePolicy": "cs-dedup",
                "AccessKey":    "xxxxxxxx",
                "SecretKey":    "xxxxxxxx"
            }

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Amazon DynamoDB Basic Acceptance - Backup and Restore"
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'AccessNode': None,
            'StoragePolicy': None,
            'AccessKey': None,
            'SecretKey': None
        }
        self.helper = None
        self.dynamodb_helper = None
        self.subclient_name = None
        self.content = None
        self.client_name = None
        self.instance_name = None
        self.storage_policy = None
        self.access_node = None
        self.access_key = None
        self.secret_key = None
        self.region = None

    def setup(self):
        """Sets up the test case related helper function and members"""
        self.helper = AmazonCloudDatabaseHelper(self)
        self.helper.populate_tc_inputs(self)
        self.dynamodb_helper = AmazonDynamoDBCLIHelper(self.access_key, self.secret_key)
        self.region = 'us-east-2'
        self.dynamodb_helper.initialize_client(self.region)
        self.subclient_name = "subclient_56229"
        self.content = None
        self.table_name = None

    def run(self):
        """Main function for test case execution"""

        try:

            self.log.info("""
                    Amazon Dynamodb Basic Acceptance - Instance creation, backup, restore

                    This test case does the following :
                    Step 1. Create instance for this testcase if it doesn't exist.
                    Step 2. Create a dynamodb table
                    Step 3. Create subclient for this testcase if it doesn't exist
                    Step 4. Run backup of the subclient and verify that it ran without any failures
                    Step 5. Run restore job of the created table and run validation on data
                    """)

            #   Step 1 - Create DynamoDB instance for this testcase if it doesn't exist
            if self.agent.instances.has_instance(self.instance_name):
                self.instance = self.agent.instances.get(self.instance_name)
                self.log.info("Instance %s already exists. Using existing instance.",
                              self.instance.instance_name)
            else:
                self.log.info(
                    "Instance %s does not exist. Creating %s instance.",
                    self.instance_name,
                    self.instance_name)
                dynamodb_options = {
                    "instance_name": self.instance_name,
                    "storage_plan": self.storage_policy,
                    "storage_policy": self.storage_policy,
                    "access_node": self.access_node,
                    "access_key": self.access_key,
                    "secret_key": self.secret_key,
                    "cloudapps_type": 'amazon_dynamodb'
                }
                self.instance = self.agent.instances.add_cloud_storage_instance(dynamodb_options)
                self.log.info("Instance %s created", self.instance.instance_name)

            #   Step 2 - Create dynamodb table and populate data
            self.log.info("Creating dynamodb table")
            self.table_name = 'TC_56229'
            self.dynamodb_helper.create_dynamodb_table(self.table_name, 'id')
            self.log.info("Populating the table with records")
            self.dynamodb_helper.populate_dynamodb_table(self.table_name, 'id', 10)

            #   Step 3 - Create subclient with created table as content
            self.log.info("Creating Subclient with new table as content")
            self.content = [{
                "type": "45",
                "name": self.table_name,
                "path": self.region,
                "displayName": self.table_name,
                "allOrAnyChildren": True,
                "negation": False
            }]

            backup_set = self.instance.backupsets.get('defaultBackupset')
            if backup_set.subclients.has_subclient(self.subclient_name):
                self.subclient = backup_set.subclients.get(self.subclient_name)
                self.log.info(
                    "subclient with name: %s, already exists. "
                    "Using existing subclient.", self.subclient_name)

            else:
                self.log.info(
                    "subclient with name: %s does not exist. Creating new subclient ...",
                    self.subclient_name)
                self.subclient = backup_set.subclients.add(
                    self.subclient_name, self.storage_policy, "Created from Automation")
            self.log.info("Subclient %s created", self.subclient_name)
            self.subclient.storage_policy = self.storage_policy
            self.subclient.content = self.content

            #   Step 4, Run backup of the created subclient
            self.dynamodb_helper.run_dynamodb_backup(self.subclient, 'full')

            # Step 5, Run restore and validate the content after restore
            destination_table_name = self.table_name + '_restored'
            self.log.info("Starting restore of source table:{0} to new table:{1}"
                          .format(self.table_name, destination_table_name))
            table_map = [{
                'srcTable':{'name': self.table_name, 'region':self.region},
                'destTable':{'name': destination_table_name, 'region': self.region}
                }]
            options = {
                'paths': [(str('/'+self.region+'/'+self.table_name))],
                'table_map': table_map,
                'adjust_write_capacity': 100,
                'destination_client': self.client_name,
                'destination_instance': self.instance_name
            }
            job = self.subclient.restore(destination="", source="", restore_options=options)
            self.log.info("Started restore job with job id: %s", str(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        job.delay_reason))

            if not job.status.lower() == "completed":
                raise Exception(
                    "Job status is not Completed, job has status: {0}".format(
                        job.status))
            self.log.info("Successfully finished restore job %s", str(job.job_id))
            self.log.info("Running validation on the restored table")
            self.dynamodb_helper.validate_dynamodb_table(destination_table_name, 'id', 10)
            self.log.info("Validation passed, test case completed")

        except Exception as exception:
            traceback.print_exc()
            self.log.error('Failed with error: %s', str(exception))
            self.status = 'FAILED'
            self.result_string = str(exception)

    def tear_down(self):
        self.log.info("Tear Down Function")
        self.log.info("Cleanup the tables created during test case run")
        # Drop the tables created during TC run
        try:
            self.dynamodb_helper.delete_dynamodb_table(self.table_name)
            self.dynamodb_helper.delete_dynamodb_table(self.table_name + '_restored')
        except Exception as exp:
            self.log.error("Clean up failed")
            self.log.error(exp)
