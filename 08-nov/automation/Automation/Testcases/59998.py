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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

Inputs:
            "Client" - Client that will be created
            "HostName" - HostName for the client that will be created
            "Agent" - Agent that will be created
            "FullSnapName" - Full Snap Name
            "IncSnapName" - Inc Snap Name
            "DiffSnapName" - Diff Snap Name
            "NDMPUserName" - UserName input to create client
            "NDMPPassword" - Password input to create client
            "FilerRestoreLocation" - Restore location for out-of-place restore
            "SubclientContent" - SubclientContent to run backup for
            "listenPort" - Port number for NDMP detect

Steps:
            # Create a NAS Client with NDMP and NetworkShare iDA
            # Refreshing the clients associated with the commcell Object
            # Check if client is present
            # Create entities for disklibrary and storagepolicy
            # Create subclient for NDMP iDA
            # Run full, inc, diff Backup jobs using Snapshot to Backup option for NDMP iDA
            # Restore out-of-place
            # Run restore in-place
            # Run data aging
            # Retire Client
            # Clean up
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from cvpysdk.exception import SDKException

class TestCase(CVTestCase):
    """Class for verifying Basic NDMP backup and restore operation using Snapshot to Backup \
    option for Oracle ZFS Storage client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle ZFS Storage - NDMP iDA - NDMP backup and restore using SnapShot \
        to Backup option"
        self.tcinputs = {
            "HostName": None,
            "Agent": None,
            "FullSnapName": None,
            "IncSnapName": None,
            "DiffSnapName": None,
            "NDMPUserName": None,
            "NDMPPassword": None,
            "SubclientContent": None,
            "FilerRestoreLocation": None,
            "listenPort": None
        }

    def run_snapshot_to_backup(self, backup_type, snap_name):
        """Initiates the snap backup job and waits till completeion"""
        self.log.info(
            "*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10
        )
        self.log.info("Running backup with snapshot to backup option using snap: " + snap_name)
        job = self.subclient.backup(backup_type, snap_name=snap_name)
        self.log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason))
        self.log.info("Succesfully finished %s backup", backup_type)

        return job

    def run(self):
        """Main function for test case execution"""
        try:

            # Create a NAS Client with NDMP and NetworkShare iDA
            self.client = self.commcell.clients.add_nas_client(self.tcinputs['HostName'],
                                                               self.tcinputs['HostName'],
                                                               self.tcinputs['NDMPUserName'],
                                                               self.tcinputs['NDMPPassword'],
                                                               self.tcinputs['listenPort'])

            self.log.info("Client added is: %s", self.client.client_name)

            # Check if client is present
            if self.commcell.clients.has_client(self.tcinputs['HostName']):
                self.log.info("Client is present.")

            self.client_machine = Machine(self.client.client_name, self.commcell)

            self.agent = self.client.agents.get(self.tcinputs['Agent'])
            self.backupset = self.agent.backupsets.get('defaultBackupSet')

            # Create entities for disklibrary and storagepolicy
            self.log.info("Creating disklibrary and storagepolicy")
            entities = CVEntities(self)
            entity_props = entities.create(["disklibrary", "storagepolicy"])

            # Create subclient for NDMP iDA
            storagepolicy_props = entity_props['storagepolicy']
            sp_name = storagepolicy_props.get('name')
            sc_name = self.id
            self.log.info("Creating subclient for NDMP iDA")
            self.subclient = self.backupset.subclients.add(sc_name, sp_name)

            self.log.info('Setting subclient content : %s', self.tcinputs['SubclientContent'])
            self.subclient.content = [self.tcinputs['SubclientContent']]
            self.subclient.refresh()

            # Run full backup job using 'snapshot to backup' for NDMP iDA
            self.log.info("Run full backup job using 'snapshot to backup' for NDMP iDA")
            job = self.run_snapshot_to_backup("FULL", snap_name=self.tcinputs['FullSnapName'])
            self.log.info("Started full backup with Job ID: %s", job.job_id)
            fulljobid = str(job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run full backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running full backup job with snapshot \
                          to backup option ")


            # Run Inc backup job using 'snapshot to backup' for NDMP iDA
            self.log.info("Run Inc backup job using 'snapshot to backup' for NDMP iDA")
            job = self.run_snapshot_to_backup("INCREMENTAL", snap_name=self.tcinputs['IncSnapName'])
            self.log.info("Started inc backup with Job ID: %s", job.job_id)
            incjobid = str(job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Incremental backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running inc backup job with snapshot \
                          to backup option ")

            # Run Diff backup job using 'snapshot to backup' for NDMP iDA
            self.log.info("Run Diff backup job using 'snapshot to backup' for NDMP iDA")
            job = self.run_snapshot_to_backup("DIFFERENTIAL", snap_name=self.tcinputs['DiffSnapName'])
            self.log.info("Started Diff backup with Job ID: %s", job.job_id)
            diffjobid = str(job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Differential backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running Diff backup job with snapshot \
                          to backup option ")


            # Run restore out-of-place
            self.log.info("Run Restore out-of-place")
            job = self.subclient.restore_out_of_place(self.client, self.tcinputs['FilerRestoreLocation'], [self.subclient.content[0]])
            self.log.info("Started restore out-of-place job with Job ID: %s", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out-of-place job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished restore out-of-place job")

            # Run restore in-place
            self.log.info("Run Restore in place")
            job = self.subclient.restore_in_place([self.subclient.content[0]])
            self.log.info("Started restore in place job with Job ID: %s", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished restore in place job")

            # Delete the backup job from SP copy and run data aging
            self.log.info("Deleting backup jobs: %s %s", fulljobid, incjobid)
            self.storage_policy = self.commcell.policies.storage_policies.get(sp_name)
            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.delete_job(fulljobid)
            self.copy.delete_job(incjobid)
            self.copy.delete_job(diffjobid)
            da_job = self.commcell.run_data_aging('Primary',
                                                  sp_name,
                                                  is_granular=True,
                                                  include_all_clients=True,
                                                  select_copies=True,
                                                  prune_selected_copies=True)
            self.log.info("Start data aging: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job job with error: %s", da_job.delay_reason
                )
            self.log.info("Data aging job completed!")
            time.sleep(180)
            self.commcell.clients.refresh()

            # Try to retire client when there is no backup data
            self.log.info("Try to Retire the client when there is no backup data")
            try:
                error_message = self.client.retire()
                self.log.info("%s", error_message)
            except SDKException as e:
                if e.exception_id == '101':
                    self.log.info("{0}".format(e.exception_message))
                else:
                    raise Exception(e)

            self.commcell.clients.refresh()

            # Check if client is present
            if not self.commcell.clients.has_client(self.tcinputs['HostName']):
                self.log.info("Client is now retired")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            # Clean up
            entities.delete(entity_props)
            