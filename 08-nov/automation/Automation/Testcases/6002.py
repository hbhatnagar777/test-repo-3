# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
Usecase of this testcase ----------------add
TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    validate_csdb() --  verify csdb database for concurrent LAN

Design Steps:
    1. Create a SP pointing to a Tape library (SP_Tape) 
	2. Create a new backupset and subclients.
	3. Run backups to SP_Tape and note the media barcode (M1).
	4. After backup finished, mark M1full, Run same backup again and note down the media barcode (M2).
	5. Delete the backupset.
	6. Mark Media M2 Full or Appendable
	7. Run data aging.
	8. Verify Media is recycled. 
	9. Create a SP pointing to a Magnetic library (SP_Mag)
	10. Create a new backupset and subclients.
	11. Run backups to SP_Mag - with "Mark media full after Successful operation" backup option
	12. Delete the backupset.
	13. Validate job pruned. 
	14. Run another backup to SP_Tape.
	15. Verify recycled media is used. 
	16. Create two Storage policies: one with magnetic and one with Tape library. 
	17. Create backupset with two subclients one pointing to magnetic and one pointing to tape. 
	18. Run backup for both subclients. 
	19. Reassociate the subclients SP to "not assigned" from storage policy level for both.
	20. Delete both the storage policies ( tape and magnetic).
	21. Run Data Aging.
	22. Media on tape should be recycled and go back to scratch pool. 
	23. Verify jobs are pruned on magnetic library. 

Sample Input:
    "6002": {
            "ClientName": "ClientName",
            "MediaAgentName": "MediaAgentName",
            "TapeLibraryName": "Tape Library Name",
            "AgentName": "File System"
        }
PreRequisite - Tape Library with 2 Media in library. 
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from cvpysdk.policies.storage_policies import StoragePolicy

class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Oper-Recycle Media type and magnetic"
        self.MMHelper = None
        self.min_interval = None
        self.ma_name = None
        self.client_name = None
        self.MediaAgent = None
        self.tape_lib_name = None
        self.disk_library_name = None
        self.tape_storage_policy = None
        self.disk_storage_policy = None
        self.backupset_name_1 = None
        self.backupset_name_2 = None
        self.subclient_name_1 = None
        self.subclient_name_2 = None
        self.client_machine = None
        self.ma_machine = None
        self.primary_mount_path = None
        self.content_path = None
        self.restore_path = None

        self.tcinputs = {
            'ClientName': None,
            'MediaAgentName': None,
            'TapeLibraryName': None,
            'AgentName': None
        }

    def setup(self):
        """Setup function of this test case"""
        self.MMHelper = MMHelper(self)
        options_selector = OptionsSelector(self.commcell)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.client_name = self.tcinputs.get('ClientName')

        # Library Name
        self.tape_lib_name = self.tcinputs.get('TapeLibraryName')
        self.disk_library_name = f'{self.id}_magnetic_disk'

        # Storage Policy Name
        self.tape_storage_policy = f"{self.id}_tape_SP"
        self.disk_storage_policy = f"{self.id}_disk_SP"

        # Backupset Name
        self.backupset_name_1 = f"{self.id}_tape_backupset"
        self.backupset_name_2 = f"{self.id}_disk_backupset"

        # Subclient Name
        self.subclient_name_1 = f"{self.id}_tape_subclient"
        self.subclient_name_2 = f"{self.id}_disk_subclient"

        # Creating Machine Object
        self.client_machine = options_selector.get_machine_object(self.client_name)
        self.ma_machine = options_selector.get_machine_object(self.ma_name)

        # select drive in client machine
        self.log.info(
            'Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(
            self.client_machine, size=40 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        # select drive in media agent machine.
        self.log.info('Selecting drive in the media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=40 * 1024)
        if ma_drive is None:
            raise Exception("No space for hosting backup and ddb")
        self.log.info('selected drive: %s', ma_drive)

        # primary mount path for disk library
        self.primary_mount_path = self.ma_machine.join_path(
            ma_drive, 'Automation', str(self.id), 'primaryMP')
        # content path
        self.content_path = self.client_machine.join_path(
            client_drive, str(self.id), 'Content'
        )
        # restore path
        self.restore_path = self.client_machine.join_path(
            client_drive, str(self.id), 'Restore'
        )

        # Clean Up
        self._cleanup()

    def run_backup_job(self, subclient, mark_media_full=False):
        """
        Run full backup job for a given subclient.
        Args:
            subclient (str) -- name of subclient for which backup needs to be run.
            content_paths (str) -- to create new dummy data
        """
        if not self.MMHelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 5):
            raise Exception(
                "unable to Generate Data at {0}".format(self.content_path))
        self.log.info("Generated Data at %s", self.content_path)

        # Start Backup
        self.log.info("Stating backup job for %s", subclient)
        if mark_media_full:
            job = subclient.backup(r'full', advanced_options={'mediaOpt': {'markMediaFullOnSuccess': True}})
        else:
            job = subclient.backup(r'full')
        if not job.wait_for_completion():
            self.log.info("Failed to run FULL backup job on CS with error: {0}".format(job.delay_reason))
        self.log.info("Backup completed for job id %s", job.job_id)
        return job.job_id

    def get_barcode(self, job_id):
        """
            Get the barcode used in job from MMMedia table
            Args:
                job id (int) -- job id for which barcode is required

            Return:
                (str) barcode
        """
        query = f"""
            SELECT Distinct MM.BarCode, MV.VolumeId
            FROM MMMedia MM Join MMVolume MV On 
            MM.MediaId = MV.MediaId 
            JOIN  archChunk AC on AC.VolumeId = MV.VolumeId
            JOIN archChunkMapping ACM on ACM.archChunkId = AC.id
            AND ACM.chunkCommCellId = AC.commCellId
            Where ACM.jobId = {job_id}
        """

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        return cur[0]
    
    def check_media_status(self, barcode, full=True):
        """
        Check media status

        Args:
            barcode (str)   -   barcode that needs to check status.
        """
        command = f"qinfo media -b {barcode}"
        self._log.info("Executing Script - %s", command)
        response = self.commcell.execute_qcommand(command).text
        self.log.info(response)
        response = response.replace("\t", "")
        s = list(map(str, response.split("\n")))[5]
        status = s.split(":")[1]
        if not full and status != 'Idle':
            raise Exception(f"Media {barcode} is still marked Full!")
        if full and status != 'Full':
            raise Exception(f"Media {barcode} is not marked Full")
        self.log.info("Media Verification Successful!")

    def mark_media_full(self, barcode):
        """
        Marks the barcode full

        Args:
            barcode (str)   -   barcode that needs to be marked full.
        """
        command = f"qmedia markfull -b {barcode}"
        self._log.info("Executing Script - %s", command)
        self.commcell.execute_qcommand(command)
        # Verifying if media full.
        self.check_media_status(barcode)

    def configure_sp_with_stream(self, storage_policy_name, library_name):
        self._log.info("check SP: %s", storage_policy_name)
        if not self.commcell.storage_policies.has_policy(storage_policy_name):
            self._log.info("adding Storage policy...")
            storage_policy = self.commcell.storage_policies.add(
                storage_policy_name=storage_policy_name,
                library=library_name,
                media_agent=self.ma_name,
                number_of_streams=1
            )
            self._log.info("Storage policy config done.")
            return storage_policy
        self._log.info("Storage policy exists!")
        storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        return storage_policy

    def run(self):
        try:
            # Storage Policy for tape library set No. of Streams to 1.
            self.log.info("Creating Storage Policy %s", self.tape_storage_policy)
            self.configure_sp_with_stream(
                self.tape_storage_policy,
                self.tape_lib_name
            )

            # Creating Backup set
            self.log.info("Creating Backupset %s", self.backupset_name_1)
            self.MMHelper.configure_backupset(self.backupset_name_1)

            # Creating Subclient
            self.log.info("Creating Subclient %s", self.subclient_name_1)
            subclient1 = self.MMHelper.configure_subclient(
                self.backupset_name_1,
                self.subclient_name_1,
                self.tape_storage_policy,
                self.content_path
            )

            # Run backup job
            job_id1 = self.run_backup_job(subclient1)

            # Get the barcode for the jobid
            barcode1 = self.get_barcode(job_id1)
            self.log.info(f"{barcode1} barcode for job {job_id1}")

            # Mark and verify barcode full for Barcode 1
            self.mark_media_full(barcode1)
            self.log.info(f"{barcode1} marked full!")

            # Run backup job
            job_id2 = self.run_backup_job(subclient1)

            # Get the barcode for the jobid
            barcode2 = self.get_barcode(job_id2)
            self.log.info(f"{barcode2} barcode for job {job_id2}")

            # Verify different media is used.
            if barcode1 == barcode2:
                raise Exception(f"Same media used for both backup jobs {barcode1}")

            # Mark and Verify Media Full Barcode 2
            self.mark_media_full(barcode2)
            self.log.info(f"{barcode2} marked full!")

            # Deleting backup set
            self.log.info("Deleting Backupset %s", self.backupset_name_1)
            self.agent.backupsets.delete(self.backupset_name_1)

            # Run Data Aginig Job
            self.log.info("Starting Data Aging Job!")
            data_aging_job = self.commcell.run_data_aging()
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

            # Verify DB- After deleting backupset
            if not self.MMHelper.validate_job_prune(job_id1):
                raise Exception(f"Job {job_id1} is not pruned.")
            
            if not self.MMHelper.validate_job_prune(job_id2):
                raise Exception(f"Job {job_id2} is not pruned.")

            # Verify Media (barcode1 and barcode2) are recycled.
            self.check_media_status(barcode1, full=False)
            self.check_media_status(barcode2, full=False)
            self.log.info(f"{barcode1}, {barcode2} Media has been recycled!")

        # Test Media Recycle for Magnetic Disk Library

            # Creating a Disk Library
            self.log.info("Creating library %s", self.disk_library_name)
            self.MMHelper.configure_disk_library(
                self.disk_library_name,
                self.ma_name,
                self.primary_mount_path
            )

            # Creating a Storage Policy
            self.log.info("Creating storage policy %s", self.disk_storage_policy)
            self.MMHelper.configure_storage_policy(
                self.disk_storage_policy,
                self.disk_library_name,
                self.ma_name
            )

            # Creating a backupset
            self.log.info("Creating Backupset %s", self.backupset_name_1)
            self.MMHelper.configure_backupset(self.backupset_name_2)

            # Creating a subclient
            self.log.info("Creating Subclient %s", self.subclient_name_2)
            subclient2 = self.MMHelper.configure_subclient(
                self.backupset_name_2,
                self.subclient_name_2,
                self.disk_storage_policy,
                self.content_path
            )

            # Run Backup and mark media full after successful operation.
            job_id3 = self.run_backup_job(subclient2, mark_media_full=True)

            # Delete the backupset
            self.log.info("Deleting Backupset %s", self.backupset_name_2)
            self.agent.backupsets.delete(self.backupset_name_2)

            # Run Data Aging Job
            self.log.info("Starting Data Aging Job!")
            data_aging_job = self.commcell.run_data_aging()
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

            # Verify DB - after deleting backupset
            if not self.MMHelper.validate_job_prune(job_id3):
                raise Exception(f"Job {job_id3} is not pruned.")

        # Run backups to Tape Storage Policy (should use recycled media)

            # Creating Backup set
            self.MMHelper.configure_backupset(self.backupset_name_1)
            # Creating Subclient
            subclient3 = self.MMHelper.configure_subclient(
                self.backupset_name_1,
                self.subclient_name_1,
                self.tape_storage_policy,
                self.content_path
            )
            # Running backup job
            job_id4 = self.run_backup_job(subclient3)

            # Getting the media used for this job
            barcode3 = self.get_barcode(job_id4)
            self.log.info(f"{barcode3} Media used for job {job_id4}")

            # Validate Recycled media is used. i.e either barcode 1 or barcode 2
            if barcode3 not in (barcode1, barcode2):
                raise Exception("Tape Media did not recycled successfully!")

            # Mark Meda Full
            self.mark_media_full(barcode3)
            self.log.info(f"{barcode3} Media Marked Full!")

        # Recycle Media Test by deleting Storage Policy.
            # Reassociating Tape Storage Policy
            self.log.info(f"Reassociating Storage Policy {self.tape_storage_policy}")
            StoragePolicy(self.commcell, self.tape_storage_policy).reassociate_all_subclients()

            # Deleting Storage Policy
            self.log.info(f"Deleting Storage Policy {self.tape_storage_policy}")
            self.commcell.storage_policies.delete(self.tape_storage_policy)

            # Creating a backupset
            self.MMHelper.configure_backupset(self.backupset_name_2)

            # Creating a subclient
            subclient2 = self.MMHelper.configure_subclient(
                self.backupset_name_2,
                self.subclient_name_2,
                self.disk_storage_policy,
                self.content_path
            )

            # Run Backup
            job_id5 = self.run_backup_job(subclient2)

            # reassociate storage policy
            self.log.info(f"Re-Associating Storage Policy {self.disk_storage_policy}")
            StoragePolicy(self.commcell, self.disk_storage_policy).reassociate_all_subclients()

            # Deleting Storage Policy
            self.log.info(f"Deleting Storage Policy {self.disk_storage_policy}")
            self.commcell.storage_policies.delete(self.disk_storage_policy)

            # Run Data Aging Job
            self.log.info("Starting Data Aging Job!")
            data_aging_job = self.commcell.run_data_aging()
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

            # Verify DB - After deleting SP for tape
            if not self.MMHelper.validate_job_prune(job_id4):
                raise Exception(f"Job {job_id4} is not pruned.")
            # Verify DB - after deleting SP for magnetic
            if not self.MMHelper.validate_job_prune(job_id5):
                raise Exception(f"Job {job_id5} is not pruned.")

            # Verify if Tape Media (barcode 3) is recycled.
            self.check_media_status(barcode3, full=False)
            self.log.info(f"{barcode3} Media is Recycled!")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def _cleanup(self):
        self.log.info('************************ Clean Up Started *********************************')
        try:
            # Deleting backupsets
            self.log.info("Deleting BackupSet: %s if exists",
                          self.backupset_name_1)
            if self.agent.backupsets.has_backupset(self.backupset_name_1):
                self.agent.backupsets.delete(self.backupset_name_1)
                self.log.info("Deleted BackupSet: %s", self.backupset_name_1)

            self.log.info("Deleting BackupSet: %s if exits", self.backupset_name_2)
            if self.agent.backupsets.has_backupset(self.backupset_name_2):
                self.agent.backupsets.delete(self.backupset_name_2)
                self.log.info("Deleted BackupSet: %s", self.backupset_name_2)

            # Deleting Storage Policies
            self.log.info("Deleting Storage Policy: %s if exists",
                          self.tape_storage_policy)
            if self.commcell.storage_policies.has_policy(self.tape_storage_policy):
                self.commcell.storage_policies.delete(self.tape_storage_policy)
                self.log.info("Deleted Storage Policy: %s", self.tape_storage_policy)

            self.log.info("Deleting Storage Policy: %s if exists", self.disk_storage_policy)
            if self.commcell.storage_policies.has_policy(self.disk_storage_policy):
                self.commcell.storage_policies.delete(self.disk_storage_policy)
                self.log.info("Deleted Storage Policy: %s", self.disk_storage_policy)

            # Deleting Library
            self.log.info(
                "Deleting primary copy library: %s if exists", self.disk_library_name)
            if self.commcell.disk_libraries.has_library(self.disk_library_name):
                self.commcell.disk_libraries.delete(self.disk_library_name)
                self.log.info("Deleted library: %s", self.disk_library_name)

            # Deleting Restore and Content Folder
            self.log.info("Deleting restore path: %s if exists", self.restore_path)
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted restore path: %s", self.restore_path)

            # Deleting Content Path
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted content path: %s", self.content_path)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")
