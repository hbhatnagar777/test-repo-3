# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case
"""

import time
from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.options_selector import CVEntities
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance
from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing TC - FlexGroup Vol Support for NDMP IntelliSnap backup"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "FlexGroup Vol Support for NDMP IntelliSnap backup"
        self.tcinputs = {
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "SubclientContent": None,
            "FilerRestoreLocation": None,
            "MediaAgent": None
        }
        
    def setup(self, is_cluster=True):
        """Initializes NAS client object and create library and storage policy entities"""
        self.nas_helper = NASHelper()
        self.is_cluster = is_cluster
        self.client_machine = Machine()
        self.client_ma = self.tcinputs['MediaAgent']
        self.entities = CVEntities(self)
        self.disklib_props, self.entity_props = self.nas_helper.create_entities(self.commcell, self.id, self.client_ma)

        storagepolicy_props = self.entity_props['storagepolicy']
        self.sp_name = storagepolicy_props.get('name')
        self.sc_name = self.id

        # Create subclient for NDMP iDA
        self.log.info("Creating subclient for NDMP iDA")
        self.subclient = self.backupset.subclients.add(self.sc_name, self.sp_name)
        self.log.info('Setting subclient content : %s', self.tcinputs['SubclientContent'])
        self.subclient.content = [self.tcinputs['SubclientContent']]
        self.subclient.refresh()
        
        # check if IntelliSnap is enabled at client level
        if not self.client.is_intelli_snap_enabled:
            self.log.info("IntelliSnap is not enabled for client, enabling it.")
            self.client.enable_intelli_snap()

            self.log.info("IntelliSnap for client is enabled.")
        
        # Check if IntelliSnap is enabled at subclient level
        if not self.subclient.is_intelli_snap_enabled:
            self.log.info("Intellisnap is not enabled at subclient level, enabling it.")
            self.subclient.enable_intelli_snap("NetApp")

            self.log.info("IntelliSnap for subclient is enabled.")
            
        self.log.info("Creating NAS Client object")
        self.nas_client = self.nas_helper.get_nas_client(self.client, self.agent, is_cluster=self.is_cluster)
        
        self.log.info("Make a CIFS Share connection")
        self.nas_client.connect_to_cifs_share(
            str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
        )

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            # check the data readers count
            self.log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self.log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                self.log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            # Run full backup job for NDMP iDA
            self.log.info("Run full backup job for NDMP iDA")
            job = self.subclient.backup("FULL")

            self.log.info("Started full backup with Job ID: %s", job.job_id)
            full_job_id = str(job.job_id)
            
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run full backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running full backup job")
            
            for content in self.subclient.content:
                volume_path, _ = self.nas_client.get_path_from_content(content)
                self.nas_helper.copy_test_data(self.nas_client, volume_path)
            
            # Run inc backup job for NDMP iDA
            self.log.info("Run incremental backup job for NDMP iDA")
            job = self.subclient.backup("INCREMENTAL")
            
            self.log.info("Started inc backup with Job ID: %s", job.job_id)
            inc_job_id = str(job.job_id)
            
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run inc backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running inc backup job")
            
            for content in self.subclient.content:
                volume_path, _ = self.nas_client.get_path_from_content(content)
                self.nas_helper.copy_test_data(self.nas_client, volume_path)

            # Run diff backup job for NDMP iDA
            self.log.info("Run differential backup job for NDMP iDA")
            job = self.subclient.backup("DIFFERENTIAL")
            
            self.log.info("Started diff backup with Job ID: %s", job.job_id)
            diff_job_id = str(job.job_id)
            
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run diff backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running diff backup job")
            
            # Run restore out-of-place 
            job = self.subclient.restore_out_of_place(
                self.client.client_name,
                str(self.tcinputs['FilerRestoreLocation']),
                self.subclient.content)
            
            self.log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )
            
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                )

            self.log.info("Successfully finished Restore out of place to Filer")
            
            # Validate restore content
            self.nas_helper.validate_filer_to_filer_restored_content(
                self.nas_client, self.subclient.content, str(self.tcinputs['FilerRestoreLocation'])
            )
            
            # Run restore in-place 
            self.log.info("Run Restore in place")
            job = self.subclient.restore_in_place([f'{self.subclient.content[0]}'])
            self.log.info("Started restore in place job with Job ID: %s", job.job_id)
            
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: {0}".format(job.delay_reason)
                )

            self.log.info("Successfully finished Restore in place to Filer")
            
            # Validate restore content
            self.nas_helper.validate_filer_to_filer_restored_content(
                self.nas_client, self.subclient.content, str(self.tcinputs['FilerRestoreLocation'])
            )

            self.log.info("*" * 10 + "Running backup copy now" + "*" * 10)
            self.storage_policy = self.commcell.policies.storage_policies.get(self.sp_name)
            job = self.storage_policy.run_backup_copy()
            self.log.info("Backup copy workflow job id is : %s", format(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + str(job.delay_reason)
                )
            self.log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))

            if job.status != 'Completed':
                raise Exception(
                    "job: {0} for Backup copy operation is completed with errors, Reason: {1}".format(
                        job.job_id, job.delay_reason)
                )

            self.log.info("*" * 10 + " Run in place restore from backup copy " + "*" * 10)
            copy_precedence = SnapBasicAcceptance._get_copy_precedence(
                self, storage_policy=self.sp_name, storage_policy_copy="Primary"
            )

            job = self.subclient.restore_in_place(
                self.subclient.content, copy_precedence=int(copy_precedence)
            )

            self.log.info(
                "Started restore in place from backup copy job with Job ID: %s", format(job.job_id)
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to restore from backup copy with error: {0}".format(str(job.delay_reason))
                )

            self.log.info("Successfully finished Restore in place from backup copy")

            # Delete the backup job from SP copy and run data aging
            self.log.info("Deleting full backup job: %s", full_job_id)
            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.delete_job(full_job_id)
            self.copy.delete_job(inc_job_id)
            self.copy.delete_job(diff_job_id)
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
            time.sleep(60)
                              
        except Exception as exp:
            self.log.error(f'Failed with error: {str(exp)}')
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.log.info("Test case complete")
           
    def tear_down(self):
        try:
            if self.backupset.subclients.has_subclient(self.sc_name):
                self.backupset.subclients.delete(self.sc_name)
            self.entities.delete(self.entity_props)
            
        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
