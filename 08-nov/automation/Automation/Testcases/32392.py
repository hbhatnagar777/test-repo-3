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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    validate_csdb() --  verify csdb database for concurrent LAN

Design Steps:
1. Disable the 'Optimize for concurrent LAN backup' MediaAgent property.
2. Create Disk library (DL1) for primary copy.
3. Add additional mountpath to the library (DL1).
4. Create deduplication enabled storage policy using DL1.
5. Create library for (DL2) secondary copy.
6. Create non-dedupe secondary copy using DL2.
7. Set retention of 0-day & 1-cycle on all copies.
8. Remove association of secondary copy with System Created Autocopy schedule.
9. create backupsetand subclient.
10. Run backups (full, Incremental, Incremental, Synthetic Full (SF1), Incremental, Synthetic Full (SF2) ).
11. Verify if client’s clBackup.log has logging -
    CVArchive::getPipelineMode() - Using default pipeline mode [Pipeline] for [Bkp] pipe
12. Run restore from primary copy
13. Verify if client’s clRestore.log has logging - 
    CVArchive::getPipelineMode() - Using default pipeline mode [Pipeline] for [Restore] pipe
14. Run auxcopy job
15. Run restore from non-dedupe secondary copy
16. Run DataAging on the storage_policy.
17. Enable the 'Optimize for concurrent LAN backup' MediaAgent property.

Sample Input - 
    "32392": {
        "AgentName": "File System",
        "MediaAgentName": "MediaAgentName",
        "ClientName": "ClientName"
        }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from cvpysdk.storage import MediaAgent


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oper - Data Pipe (SDT off)-Basic Functionality-UNIX,Win"
        self.MediaAgent = None
        self.common_util = None
        self.MMHelper = None
        self.DedupeHelper = None
        self.primary_library_name = None
        self.secondary_library_name = None
        self.storage_policy_name = None
        self.ddb_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.client_machine = None
        self.ma_machine = None
        self.primary_mount_path1 = None
        self.primary_mount_path2 = None
        self.secondary_mount_path = None
        self.partition_path = None
        self.media_agent_name = None

        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.media_agent_name = self.tcinputs.get('MediaAgentName')
        self.MMHelper = MMHelper(self)
        self.DedupeHelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)
        self.primary_library_name = '%s_disk_library_1' % str(self.id)
        self.secondary_library_name = '%s_disk_library_2' % str(self.id)
        self.storage_policy_name = '%s_storage_policy' % str(self.id)
        self.ddb_ma_name = self.tcinputs.get("MediaAgentName")
        self.backupset_name = '%s_backup_set' % str(self.id)
        self.subclient_name = '%s_subclient' % str(self.id)

        self.client_machine = options_selector.get_machine_object(
            self.tcinputs['ClientName'])
        self.ma_machine = options_selector.get_machine_object(
            self.tcinputs['MediaAgentName'])

        # select drive in client machine
        self.log.info(
            'Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(
            self.client_machine, size=10 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        # select drive in media agent machine.
        self.log.info('Selecting drive in the media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=10 * 1024)
        if ma_drive is None:
            raise Exception("No space for hosting backup and ddb")
        self.log.info('selected drive: %s', ma_drive)

        self.primary_mount_path1 = self.ma_machine.join_path(
            ma_drive, 'Automation', str(self.id), 'MP1')
        self.primary_mount_path2 = self.ma_machine.join_path(
            ma_drive, 'Automation', str(self.id), 'MP2')
        self.secondary_mount_path = self.ma_machine.join_path(
            ma_drive, 'Automation', str(self.id), 'secondaryMP')

        # Content Path
        self.content_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata')

        # Restore Path
        self.restore_dest_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Restoredata')

        # DDB Path
        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

        # clean up
        self._cleanup()

        # Create directory
        self.client_machine.create_directory(self.content_path)
        self.client_machine.create_directory(self.restore_dest_path)

        self.MediaAgent = MediaAgent(self.commcell, self.tcinputs.get('MediaAgentName'))


    def validate_csdb(self, client_id):
        """
            Validate if concurrent LAN optimization is disabled or not
            Args:
                client_id (int) -- client id to check in table

            Return:
                (Bool) True if disabled
                (Bool) False if enabled
        """
        self.log.info(
            "validating whether concurrent LAN optimization is disabled or not for media agent %s", client_id)
        query = f"""SELECT Attribute&32 FROM MMHost WHERE ClientId={client_id}"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] == '0':
            return True
        return False

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info(
            "********************** CLEANUP STARTING *************************")
        try:

            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists",
                          self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Backup set exists! Deleting it.")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting Storage Policy: %s if exists",
                          self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted Storage Policy: %s",
                              self.storage_policy_name)

            # Delete Library
            self.log.info(
                "Deleting primary copy library: %s if exists", self.primary_library_name)
            if self.commcell.disk_libraries.has_library(self.primary_library_name):
                self.commcell.disk_libraries.delete(self.primary_library_name)
                self.log.info("Deleted library: %s", self.primary_library_name)

            # Delete Library
            self.log.info("Deleting secondary  library: %s if exists",
                          self.secondary_library_name)
            if self.commcell.disk_libraries.has_library(self.secondary_library_name):
                self.commcell.disk_libraries.delete(
                    self.secondary_library_name)
                self.log.info("Deleted library: %s",
                              self.secondary_library_name)

            # Restore and content folder if created.
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            self.log.info("Removed Content directory")

            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            self.log.info("Removed Restore directory")


        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def run(self):
        """Run function of this test case"""
        try:
            # disable concurrent LAN backup using Media Helper set_opt_lan
            self.log.info(
                "setting Optimize for concurrent LAN backups disable")
            self.MediaAgent.set_concurrent_lan(False)

            # Verfiy CSDB
            if self.validate_csdb(int(self.MediaAgent.media_agent_id)):
                self.log.info(
                    "Optimize for concurrent LAN backups attribute 32 disabled.")
            else:
                # raise an error - add
                self.log.error(
                    "Optimize for concurrent LAN backups failed to disable attribute 32")
                raise Exception("failed to disable attribute 32")

            # Create a disk Library DL1
            primary_library_obj1 = self.MMHelper.configure_disk_library(
                library_name=self.primary_library_name,
                mount_path=self.primary_mount_path1
            )
            # configure mount path
            self.MMHelper.configure_disk_mount_path(
                primary_library_obj1, self.primary_mount_path2, self.media_agent_name)

            # Create dedupe enabled Storage Policy
            storage_policy = self.DedupeHelper.configure_dedupe_storage_policy(
                self.storage_policy_name, primary_library_obj1,
                self.tcinputs['MediaAgentName'],
                self.partition_path
            )
            self.log.info("Created Dedupe enabled storage policy!")
            # Create DL2
            self.MMHelper.configure_disk_library(
                library_name=self.secondary_library_name,
                mount_path=self.secondary_mount_path
            )
            self.log.info("Created Disk Library 2")

            # non-dedupe secoundary copy with DL2
            secondary_copy_name = '%s_copy_nondedupe' % str(self.id)
            secondary_copy = self.MMHelper.configure_secondary_copy(
                secondary_copy_name, self.storage_policy_name,
                self.secondary_library_name,
                self.tcinputs['MediaAgentName']
            )
            self.log.info("Created non dedupe secondary copy for Disk Library 2!")

            # setting retention to 0 days and 1 cycle.
            self.log.info(
                "Setting Retention: 0-days and 1-cycle on Secondary Copy")
            retention = (0, 1, -1)
            secondary_copy.copy_retention = retention
            primary_copy = storage_policy.get_copy("Primary")
            primary_copy.copy_retention = retention

            # Remove association
            self.MMHelper.remove_autocopy_schedule(
                storage_policy_name= self.storage_policy_name,
                copy_name=secondary_copy_name)

            # Create Backup -
            self.log.info("creating backupset %s", self.backupset_name)

            self.MMHelper.configure_backupset(self.backupset_name)

            # create subclient -
            self.log.info("creating subclient %s", self.subclient_name)
            subclient = self.MMHelper.configure_subclient(
                self.backupset_name, self.subclient_name,
                self.storage_policy_name, self.content_path, self.agent
            )

            # Run Backups -
            self.log.info("Starting backup jobs for subclient %s", self.subclient_name)
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']

            for sequence_index in range(len(job_types_sequence_list)):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    if not self.MMHelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 5):
                        self.log.error(
                            "unable to Generate Data at %s", self.content_path)
                        raise Exception(
                            "unable to Generate Data at {0}".format(self.content_path))
                    self.log.info("Generated Data at %s", self.content_path)
                # Perform Backup

                job_id = self.common_util.subclient_backup(
                    subclient, job_types_sequence_list[sequence_index]).job_id

                self.log.info('job_id %s', job_id)

                # verifying clbackup.log on client.
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    matched_line, matched_string = self.DedupeHelper.parse_log(
                        self.tcinputs['ClientName'],
                        'clbackup.log',
                        '[Pipeline] for [Bkp] pipe',
                        job_id
                    )
                    if matched_line or matched_string:
                        self.log.info('matched line: %s', matched_line)
                        self.log.info('matched string: %s', matched_string)
                    else:
                        raise Exception("No logs found for backup job!")


            # Restore from primary copy
            restore_job = subclient.restore_out_of_place(self.client, self.restore_dest_path,
                                                         [self.content_path])
            self.log.info(
                "restore job [%s] has started from primary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error(
                    "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(
                "restore job [%s] has completed.", restore_job.job_id)

            # Verifying restore job logs
            matched_line, matched_string = self.DedupeHelper.parse_log(
                self.tcinputs['ClientName'],
                'clRestore.log',
                '[Pipeline] for [Restore] pipe',
                restore_job.job_id
            )
            if matched_line or matched_string:
                self.log.info('matched line: %s', matched_line)
                self.log.info('matched string: %s', matched_string)
            else:
                raise Exception("No logs found for restore job!")

            # Run Aux copy Job
            auxcopy_job = storage_policy.run_aux_copy()
            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            if not auxcopy_job.wait_for_completion():
                self.log.error(
                    "Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id, auxcopy_job.delay_reason)
                raise Exception(
                    "Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id, auxcopy_job.delay_reason))
            self.log.info(
                "Auxcopy job [%s] has completed.", auxcopy_job.job_id)

            # Remove content and Restore from non dedupe secondary copy -- add restore validation ----add
            self.client_machine.remove_directory(self.restore_dest_path)
            restore_job = subclient.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path],
                                                         copy_precedence=2)
            self.log.info(
                "restore job [%s] has started from non dedupe secondary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error(
                    "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging(storage_policy_name=self.storage_policy_name,
                                                          is_granular=True, include_all_clients=True)
            self.log.info(
                "Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(
                "Data Aging job [%s] has completed.", data_aging_job.job_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("setting Optimize for concurrent LAN backups enable")
        self.MediaAgent.set_concurrent_lan(True)
        if not self.validate_csdb(self.MediaAgent.media_agent_id):
            self.log.info(
                "Optimize for concurrent LAN backups attribute 32 enabled.")
        else:
            self.log.error(
                "Optimize for concurrent LAN backups failed to enabled attribute 32")
            raise Exception("failed to enabled attribute 32")

        if self.status != constants.FAILED:
            self.log.info(
                "Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment ...")
