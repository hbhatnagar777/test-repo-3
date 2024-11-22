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
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case
"""
import time
import shutil
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Basic Acceptance for NDMP Backup and restore: Cluster As a CLient"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "SynthRestore support - place holder for test case"
        self.tcinputs = {
            "SubclientContent": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }
    
    def setup(self, is_cluster=True):
        """Initialize NAS client and create library and storage policy entities"""
        self.nas_helper = NASHelper()
        self.is_cluster = is_cluster
        self.client_machine = Machine()
        
        # Create entities for disklibrary and storagepolicy
        self.log.info("Creating disklibrary and storagepolicy")
        self.entities = CVEntities(self)
        self.entity_props = self.entities.create(["disklibrary", "storagepolicy"])
        storagepolicy_props = self.entity_props['storagepolicy']
        self.sp_name = storagepolicy_props.get('name')
        self.sc_name = self.id
            
        # Create subclient for NDMP iDA
        self.log.info("Creating subclient for NDMP iDA")
        self.subclient = self.backupset.subclients.add(self.sc_name, self.sp_name)

        self.log.info('Setting subclient content : %s', self.tcinputs['SubclientContent'])
        self.subclient.content = [self.tcinputs['SubclientContent']]
        self.subclient.refresh()
        
        self.log.info("Creating NAS Client object")
        self.nas_client = self.nas_helper.get_nas_client(self.client, self.agent, is_cluster=self.is_cluster)

        self.log.info("Make a CIFS Share connection")
        self.nas_client.connect_to_cifs_share(
            str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
        )
            
    def run(self):
        """Execution method for this test case"""
        try:
        
            self.log.info("Creating test data")
            for content in self.subclient.content:
                volume_path, _ = self.nas_client.get_path_from_content(content)
                
                test_data_size = 10
                test_data_path = OptionsSelector.get_drive(self.client_machine)
                self.nas_client._local_machine.generate_test_data(test_data_path, 0, 1, file_size=test_data_size, levels=0, custom_file_name=f'file{self.id}.txt')
                test_data_path = f'{test_data_path}files_with_custom_name'
                custom_file_name = f'file{self.id}1.txt'
                self.log.info(f'Generated Test Data at path: {test_data_path}')
                self.log.info(f'Created file: {custom_file_name}')
                self.log.info(f'Copying test data to: {volume_path}')
                        
                self.nas_client._local_machine.copy_folder_to_network_share(
                    test_data_path, volume_path, self.tcinputs['CIFSShareUser'], self.tcinputs['CIFSSharePassword']
                )
                    
                shutil.rmtree(test_data_path)

            
            # Run full backup job for NDMP iDA
            self.log.info("Run full backup job for NDMP iDA")
            job = self.subclient.backup(backup_level='full')

            self.log.info("Started full backup with Job ID: %s", job.job_id)
            full_job_id = str(job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run full backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running full backup job")
            
            # Run restore in-place 
            self.log.info("Run Restore in place")
            job = self.subclient.restore_in_place([f'{self.subclient.content[0]}/files_with_custom_name/{custom_file_name}'], synth_restore=True)
            self.log.info("Started restore in place job with Job ID: %s", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished restore in place job")
            
            # Delete the backup job from SP copy and run data aging
            self.log.info("Deleting full backup job: %s", full_job_id)
            self.storage_policy = self.commcell.policies.storage_policies.get(self.sp_name)
            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.delete_job(full_job_id)
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
            self.log.error(f'Failed with error: {str(exp)}')
            self.result_string = str(exp)
            self.status = constants.FAILED
            
        finally:
            self.log.info("TC tear_down complete")