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
            "ArrayName" - Array Name input to create array
            "VendorName" - Vendor Name input to create array
            "UserName" - UserName input to create array
            "Password" - Password input to create array
            "ControlHost" - ControlHost input to create array
            "SubclientContent" - SubclientContent to run backup for

Steps:
            # Create a NAS Client with NDMP and NetworkShare iDA
            # Refreshing the clients associated with the commcell Object
            # Check if client is present
            # Adding array entry for NAS client
            # Create entities for disklibrary and storagepolicy
            # Create subclient for NDMP iDA
            # Run full backup job for NDMP iDA
            # Try to Retire the client when backup data is still valid
            # Check if client is present
            # Run restore in-place from a deconfigured client
            # Check if client can be reconfigured
            # Delete the backup job from SP copy and run data aging
            # Try to Retire the client when backup data is aged but array management entry exists
            # Check if client is present
            # Delete array management entry
            # Try to retire client when there is no backup data and no array management entry
            # Retire should be successful
            # Clean up
"""
import time
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities

class TestCase(CVTestCase):
    """Class for verifying the Retire Option for NAS client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Retire Client - Perform Retire Operation on a NAS client."
        self.tcinputs = {
            "HostName": None,
            "Agent": None,
            "ArrayName": None,
            "VendorName": None,
            "UserName": None,
            "Password": None,
            "ControlHost": None,
            "SubclientContent": None
        }


    def run(self):
        """Main function for test case execution"""
        try:

            # Create a NAS Client with NDMP and NetworkShare iDA
            self.client = self.commcell.clients.add_nas_client(self.tcinputs['HostName'],
                                                               self.tcinputs['HostName'],
                                                               self.tcinputs['UserName'],
                                                               self.tcinputs['Password'])

            self.log.info("Client added is: %s", self.client.client_name)

            # Check if client is present
            if self.commcell.clients.has_client(self.tcinputs['HostName']):
                self.log.info("Client is present.")

            # Adding array entry for NAS client
            self.log.info("Adding array management entry for :%s", self.tcinputs['ArrayName'])
            control_host_id = self.commcell.array_management.add_array(self.tcinputs['VendorName'],
                                                                       self.tcinputs['ArrayName'],
                                                                       self.tcinputs['UserName'],
                                                                       b64encode(self.tcinputs['Password'].encode()).decode(),
                                                                       self.tcinputs['ControlHost'],
                                                                       config_data=None,
                                                                       is_ocum=False)
            self.log.info("Successfully added the Array with ControlHost id:%s", control_host_id)

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

            # Run full backup job for NDMP iDA
            self.log.info("Run full backup job for NDMP iDA")
            job = self.subclient.backup(backup_level='full')

            self.log.info("Started full backup with Job ID: %s", job.job_id)
            fulljobid = str(job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run full backup job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished running full backup job")

            # Try to Retire the client when backup data is still valid
            try:
                self.log.info("Try to Retire the client when backup data is still valid")
                self.client.retire()
            except Exception:
                self.log.info("Retire client failed as expected when backup data is still valid")

            # Check if client is present
            if self.commcell.clients.has_client(self.tcinputs['HostName']):
                self.log.info("Client is still present & deconfigured.")

            # Run restore in-place from a deconfigured client
            self.log.info("Run Restore in place from a deconfigured client")
            job = self.subclient.restore_in_place([self.subclient.content[0]])
            self.log.info("Started restore in place job with Job ID: %s", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: %s", job.delay_reason
                )
            self.log.info("Successfully finished restore in place job")

            # Check if client can be reconfigured
            self.log.info("Reconfiguring the client")
            self.client.reconfigure_client()
            self.log.info("Client is successfully reconfigured now")

            # Delete the backup job from SP copy and run data aging
            self.log.info("Deleting full backup job: %s", fulljobid)
            self.storage_policy = self.commcell.policies.storage_policies.get(sp_name)
            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.delete_job(fulljobid)
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
            time.sleep(60)

            #Try to Retire the client when backup data is aged but array management entry exists
            try:
                self.log.info("Try to Retire the client when backup data is aged \
                               but array management entry is still present")
                self.client.retire()
            except Exception:
                self.log.info("Retire client failed as expected when backup data "\
                              "is aged but array entry still present")

            # Check if client is present
            if self.commcell.clients.has_client(self.tcinputs['HostName']):
                self.log.info("Client is still present & configured.")

            # Delete array management entry
            self.log.info("Deleting array management entry")
            error_message = self.commcell.array_management.delete_array(control_host_id)
            self.log.info("%s", error_message)

            # Try to retire client when there is no backup data and no array management entry
            self.log.info("Try to Retire the client when there is no backup data \
                           and no array management entry")
            error_message = self.client.retire()
            self.log.info("%s", error_message)

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
