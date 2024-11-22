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
            "NDMPUserName" - UserName input to create client
            "NDMPPassword" - Password input to create client
            "SubclientContent" - SubclientContent to run backup for
            "listenPort" - Port number for NDMP detect

Steps:
            # Create a NAS Client with NDMP and NetworkShare iDA
            # Refreshing the clients associated with the commcell Object
            # Check if client is present
            # Create entities for disklibrary and storagepolicy
            # Create subclient for NDMP iDA
            # Run full, inc, diff Backup jobs
            # Run data aging
            # Retire Client
            # Clean up
"""
import time
from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from cvpysdk.exception import SDKException

class TestCase(CVTestCase):
    """Class for verifying Basic NDMP ZFS backup and restore operation for Oracle ZFS Storage client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle ZFS Storage - NDMP iDA - ZFS backup - Basic Acceptance NDMP backup and restore"
        self.tcinputs = {
            "HostName": None,
            "Agent": None,
            "NDMPUserName": None,
            "NDMPPassword": None,
            "SubclientContent": None,
            "listenPort": None,
            "MediaAgent": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.nas_helper = NASHelper()
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
            self.client_ma = self.tcinputs['MediaAgent']
            self.entities = CVEntities(self)
            self.disklib_props, self.entity_props = self.nas_helper.create_entities(self.commcell, self.id,
                                                                                    self.client_ma)

            storagepolicy_props = self.entity_props['storagepolicy']
            self.sp_name = storagepolicy_props.get('name')
            self.sc_name = self.id

            # Create subclient for NDMP iDA
            self.log.info("Creating subclient for NDMP iDA")
            self.subclient = self.backupset.subclients.add(self.sc_name, self.sp_name)
            self.log.info('Setting subclient content : %s', self.tcinputs['SubclientContent'])
            self.subclient.content = [self.tcinputs['SubclientContent']]
            self.subclient.refresh()

            # Run full ZFS backup job for NDMP iDA
            self.log.info("Run full ZFS backup job for NDMP iDA")
            job = self.subclient.backup("FULL", block_backup=True)
            self.log.info("Started full ZFS backup with Job ID: %s", job.job_id)
            fulljobid = str(job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run full ZFS backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running full ZFS backup job ")

            maclient = self.commcell.clients.get(self.subclient.storage_ma)
            mamachine = Machine(maclient)

            if mamachine.get_logs_for_job_from_file(
                    job.job_id,
                    "NasBackup.log",
                    "TYPE\=zfs"):
                self.log.info(
                    'NDMP full backup job is run with block backup')
            else:
                self.log.info(
                    'NDMP full backup job is NOT run with block backup')
                raise Exception(
                    'NDMP full backup job is NOT run with block backup')

            # Run Inc ZFS backup job for NDMP iDA
            self.log.info("Run Inc ZFS backup job for NDMP iDA")
            job = self.subclient.backup("INCREMENTAL", block_backup=True)
            self.log.info("Started inc ZFS backup with Job ID: %s", job.job_id)
            incjobid = str(job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Incremental ZFS backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running inc ZFS backup job  ")

            if mamachine.get_logs_for_job_from_file(
                    job.job_id,
                    "NasBackup.log",
                    "TYPE\=zfs"):
                self.log.info(
                    'NDMP inc backup job is run with block backup')
            else:
                self.log.info(
                    'NDMP inc backup job is NOT run with block backup')
                raise Exception(
                    'NDMP inc backup job is NOT run with block backup')

            # Run Diff ZFS backup job for NDMP iDA
            self.log.info("Run Diff ZFS backup job for NDMP iDA")
            job = self.subclient.backup("DIFFERENTIAL", block_backup=True)
            self.log.info("Started Diff ZFS backup with Job ID: %s", job.job_id)
            diffjobid = str(job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Differential ZFS backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running Diff ZFS backup job ")

            if mamachine.get_logs_for_job_from_file(
                    job.job_id,
                    "NasBackup.log",
                    "TYPE\=zfs"):
                self.log.info(
                    'NDMP diff backup job is run with block backup')
            else:
                self.log.info(
                    'NDMP diff backup job is NOT run with block backup')
                raise Exception(
                    'NDMP diff backup job is NOT run with block backup')

            # Delete the backup job from SP copy and run data aging
            self.log.info("Deleting backup jobs: %s %s %s", fulljobid, incjobid, diffjobid)
            self.storage_policy = self.commcell.policies.storage_policies.get(self.sp_name)
            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.delete_job(fulljobid)
            self.copy.delete_job(incjobid)
            self.copy.delete_job(diffjobid)
            da_job = self.commcell.run_data_aging('Primary',
                                                  self.sp_name,
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
            self.entities.delete(self.entity_props)