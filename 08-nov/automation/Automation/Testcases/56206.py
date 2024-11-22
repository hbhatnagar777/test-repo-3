# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    setup()                --  setup function of this test case

    make_instance_available()       --  starts RDS instances

    run()                  --  run function of this test case

    make_instance_unavailable()     --  stops RDS instances set to available by this test case
"""

import traceback
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps.amazon_helper import AmazonCloudDatabaseHelper, AmazonRDSCLIHelper


class TestCase(CVTestCase):
    """Test case class for testing Amazon RDS basic snap backup and restore operations

        Input JSON:

            Required Parameters Example:
            {
                "ClientName":   "Automation",
                "InstanceName": "RDS",
                "AccessNode":   "AmazonCS",
                "StoragePolicy": "cs-dedup",
                "AccessKey":    "xxxxxxxx",
                "SecretKey":    "xxxxxxxx"
                "Content": [{
                    "type": "instance"
                    "name": "rdstest",
                    "path": "us-east-2",
                    "displayName": "rdstest",
                    "allOrAnyChildren": True
                }]
            }

            Optional Parameters Example:
            {
                "SubclientName": "XXXX",
            }

            No optional parameters we use default subclient name as:

                SubclientName : "Subclient_56206"
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Amazon RDS Basic Acceptance - Snapshot Backup and Restore"
        self.tcinputs = {
            'AccessNode': None,
            'StoragePolicy': None,
            'AccessKey': None,
            'SecretKey': None,
            'Content': None
        }
        self.helper = None
        self.rdsclihelper = None
        self.subclient_name = None
        self.content = None
        self.client_name = None
        self.instance_name = None
        self.storage_policy = None
        self.access_node = None
        self.access_key = None
        self.secret_key = None
        self.instances_made_available = []

    def setup(self):
        """Sets up the test case related helper function and members"""
        self.helper = AmazonCloudDatabaseHelper(self)
        self.subclient_name = "subclient_56206"

    def make_instance_available(self):
        """function to set instances that aren't in available to available state"""
        self.rdsclihelper = AmazonRDSCLIHelper(
            secret_key=self.secret_key,
            access_key=self.access_key)
        for rds_instance in self.content:
            if self.rdsclihelper.is_instance_present(rds_instance["path"], rds_instance["name"], availability=True):
                self.log.info("Instance %s is in available state", rds_instance["name"])
            else:
                self.instances_made_available.append({"path": rds_instance["path"], "name": rds_instance["name"]})
                self.log.info("Instance %s is not in available state", rds_instance["name"])
                self.log.info("Setting Instance %s to available state", rds_instance["name"])
                self.rdsclihelper.start_rds_instance(
                    region=rds_instance["path"],
                    instance_identifier=rds_instance["name"]
                )

    def make_instance_unavailable(self):
        """Stops the RDS instances that make_rds_available set to available state"""
        for rds_instance in self.instances_made_available:
            self.log.info("Instance %s is being stopped", rds_instance["name"])
            self.rdsclihelper.stop_rds_instance(
                region=rds_instance["path"],
                instance_identifier=rds_instance["name"]
            )

    def run(self):
        """Main function for test case execution"""

        try:
            # Initialize test case inputs
            self.helper.populate_tc_inputs(self)

            self.log.info("""\n
                    Amazon RDS Basic Acceptance - Snap Backup and Restore

                    This test case does the following :
                    Step 1. Create instance for this testcase if it doesn't exist.
                    Step 2. Create subclient for this testcase if it doesn't exist
                    Step 3. Sets RDS instances of subclient that are not available to an available state. 
                    Step 4. Run snap backup of the subclient and verify that it ran without any failures;
                            All available clusters should be snapshotted and verify that the snapshots are
                            present in available state at AWS.
                    Step 5. Run restore job by selecting a random snapshot from backup; Verify that the
                            cluster is restored successfully and is in available state. If the restore is
                            successful delete the restored cluster
                    Step 6. Stops the RDS instances that were made available by the testcase.
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
                    "cloudapps_type": 'amazon_rds'
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

            #  Step 3, checking if the instance is in available state and sets it to available if not.

            self.make_instance_available()
            #   Step 4 : Run snap backup of the subclient and verify that it ran without any failures;
            #   All available instances should be snapshotted and verify that the snapshots are
            #   present in available state at AWS.
            job = self.helper.run_backup_verify()

            #   Step 5, Run restore job by selecting a random snapshot from backup; Verify that the
            #   instance is restored successfully and is in available state. If the restore is
            #   successful delete the restored instance
            self.helper.run_restore_verify(job)

            self.log.info("Test case execution completed successfully")

        except Exception as exception:
            traceback.print_exc()
            self.log.error('Failed with error: %s', str(exception))
            self.status = 'FAILED'
            self.result_string = str(exception)
        finally:
            # Stops the instances that were not in available state prior to running the testcase
            self.make_instance_unavailable()