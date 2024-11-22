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


class TestCase(CVTestCase):
    """Test case class for testing Amazon DocumentDB basic snap backup and restore operations

        Input JSON:

            Required Parameters Example:
            {
                "ClientName":   "Automation",
                "InstanceName": "DocumentDB",
                "AccessNode":   "AmazonCS",
                "StoragePolicy": "cs-dedup",
                "AccessKey":    "xxxxxxxx",
                "SecretKey":    "xxxxxxxx"
                "Content": [{
                    "type": "cluster"
                    "name": "docdbtest",
                    "path": "us-east-2",
                    "displayName": "docdbtest",
                    "allOrAnyChildren": True
                }]
            }

            Optional Parameters Example:
            {
                "SubclientName": "XXXX",
            }

            No optional parameters we use default subclient name and content as
            all redshift clusters across all regions:

                SubclientName : "Subclient_55128"
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Amazon DocumentDB Basic Acceptance - Snapshot Backup and Restore"
        self.tcinputs = {
            'AccessNode': None,
            'StoragePolicy': None,
            'AccessKey': None,
            'SecretKey': None,
            'Content': None
        }
        self.helper = None
        self.subclient_name = None
        self.content = None
        self.client_name = None
        self.instance_name = None
        self.storage_policy = None
        self.access_node = None
        self.access_key = None
        self.secret_key = None

    def setup(self):
        """Sets up the test case related helper function and members"""
        self.helper = AmazonCloudDatabaseHelper(self)
        self.subclient_name = "subclient_55128"

    def run(self):
        """Main function for test case execution"""

        try:
            # Initialize test case inputs
            self.helper.populate_tc_inputs(self)

            self.log.info("""\n
                    Amazon DocumentDB Basic Acceptance - Snap Backup and Restore

                    This test case does the following :
                    Step 1. Create instance for this testcase if it doesn't exist.
                    Step 2. Create subclient for this testcase if it doesn't exist
                    Step 3. Run snap backup of the subclient and verify that it ran without any failures;
                            All available clusters should be snapshotted and verify that the snapshots are
                            present in available state at AWS.
                    Step 4. Run restore job by selecting a random snapshot from backup; Verify that the
                            cluster is restored successfully and is in available state. If the restore is
                            successful delete the restored cluster
                    """)

            #   Step 1 - Create Instance for this testcase if it doesn't exist
            if self.agent.instances.has_instance(self.instance_name):
                self.instance = self.agent.instances.get(self.instance_name)
                self.log.info("Instance %s already exists. Using existing instance.", self.instance.instance_name)
            else:
                self.log.info(
                    "Instance %s does not exist. Creating %s instance.",
                    self.instance_name,
                    self.instance_name)
                redshift_options = {
                    "instance_name": self.instance_name,
                    "storage_plan": self.storage_policy,
                    "storage_policy": self.storage_policy,
                    "access_node": self.access_node,
                    "access_key": self.access_key,
                    "secret_key": self.secret_key,
                    "cloudapps_type": 'amazon_docdb'
                }
                self.instance = self.agent.instances.add_cloud_storage_instance(redshift_options)
                self.log.info("Instance %s created", self.instance.instance_name)

            #   Step 2 - Create subclient for this testcase if it doesn't exist
            backup_set = self.instance.backupsets.get('defaultBackupset')
            if backup_set.subclients.has_subclient(self.subclient_name):
                self.subclient = backup_set.subclients.get(self.subclient_name)
                self.log.info(
                    "subclient with name: %s, already exists. Using existing subclient.",
                    self.subclient_name)
            else:
                self.log.info(
                    "subclient with name: %s does not exist. Creating new subclient ...",
                    self.subclient_name)
                self.subclient = backup_set.subclients.add(self.subclient_name,
                                                           self.storage_policy,
                                                           "Created from Automation")
                self.log.info("Subclient %s created", self.subclient_name)
            self.subclient.storage_policy = self.storage_policy
            self.subclient.enable_intelli_snap("Amazon Web Services")
            self.subclient.content = self.content

            #   Step 3 : Run snap backup of the subclient and verify that it ran without any failures;
            #   All available clusters should be snapshotted and verify that the snapshots are
            #   present in available state at AWS.
            job = self.helper.run_backup_verify()

            #   Step 4, Run restore job by selecting a random snapshot from backup; Verify that the
            #   cluster is restored successfully and is in available state. If the restore is
            #   successful delete the restored cluster
            self.helper.run_restore_verify(job)

            self.log.info("Test case execution completed successfully")

        except Exception as exception:
            traceback.print_exc()
            self.log.error('Failed with error: %s', str(exception))
            self.status = 'FAILED'
            self.result_string = str(exception)
