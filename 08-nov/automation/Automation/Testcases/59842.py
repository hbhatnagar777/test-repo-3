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

    previous_run_cleanup() -- for deleting the left over backupset and storage policy from the previous run

    run_backup_job()   -- runs backup job of given type

    wait_for_job_backup_phase() -- cause the program to wait for the  backup phase of the job

    ddb_subclient_load() -- load the DDB subclient for running DDB backups

    create_resources() -- creates the objects, defines paths for this testcase

    check_for_snapshot() --  checks whether snapshot is created or not

    validations_checks() -- runs all the validations for the tc

    run()           --  run function of this test case

    create_common_items() -- creates items which are to be left behind,
                            there are common resources which
                            can be used by other ddb backup testcases too
                            they will act as default placeholders for ddb subclient

    tear_down()     --  tear down function of this test case

basic idea of the test case:
checks if the DDBBackup job and the suspend/resume functionality
is working correctly or not.
    # SUSPEND RESUME DDBBackup job case

validations used:
    a.	Validate, this DDB Backup job, quiesced the store from #3 (sidbengine log)
    b.	Validate, snapshot was created (clbackupParent log)
    c.	Validate, snapshot was deleted (query for mounted  snaps on unix)
        make sure new snapshot is created on resume - thus there will be multiple snapshot files c


input json file arguments required:

                        "ClientName": "name of the client machine without as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agent as in commserve"
                        "testcaseFactor": "factor to change the data content ->
                         can control the overlap
                        of DDBbackup job with sidb2.exe process to be online"
                        -> increase it to generate more content
                        -> simulates the overlap of DDBBackup job snapshot creation while
                           dedupe backup job is in progress over the same DDB store.
                        -> keep it 1 => default (based on system performance change it)
                        # client and media agent machine should be different to
                        # make sure for test
                        "mount_path" : "enter the unix path to library folder
                         for creating mount path"
                        "dedup_path": "enter the unix path to DDB folder
                         for creating dedup store path"

Design steps:
pre run: create resources
1.	Have dedupe SP
2.	Make sure DDBBackup subclient exists and is associated to valid SP
3.	Run backup with new content (we need to run backups on multiple subclients,
    all pointing to same store with generated content so
     that SIDB2 process is up for some good enough time)

Run:
4.	After creating resources and running one "FULL" backup,
    run another "FULL" backup with new content,
    while the job is in progress and reaches 'backup' phase, start a DDB backup job
5.  When the DDB backup job is in the backup phase, suspend it. After momentary wait, resume it.
6.	After all the executing jobs complete
    a.	Validate, this DDB Backup job, quiesced the store from #3 (sidbengine log)
    b.	Validate, snapshot was created (clbackupParent log)
    c.	Validate, snapshot was deleted (query for mounted  snaps on unix)
        make sure new snapshot is created on resume -
         thus there will be multiple snapshot files created

"""
import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = """UNIX Suspend / Resume case for DDBBackup Job"""
        self.tcinputs = {
            "MediaAgentName": None,
            "testcaseFactor": None,
            "mount_path": None,
            "dedup_path": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.testcase_path_client = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.job = None
        self.ddbbackup_subclient = None
        self.sidb_id = None
        self.substore_id = None
        self.ddb_backup_job = None
        self.num_snapshot = None
        self.dummy_content_path = None
        self.ma_name = None
        
    def setup(self):
        """assign values to variables for testcase"""
        self.library_name = str(self.id) + "_lib"
        self.storage_policy_name = str(self.id) + "_SP"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.client)
        self.media_agent_machine = machine.Machine(
            self.tcinputs.get("MediaAgentName"), self.commcell)
        self.ma_name = self.tcinputs.get("MediaAgentName")

    def previous_run_clean_up(self):
        """
        deletes items from the previous run of the testcase

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if clean up is not successful
                special message is shown if storage policy of the testcase from previous runs
                still is associated to the subclient.
        """
        self.log.info("********* previous run clean up **********")
        try:
            self.log.info("Deleting Backupset %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)

            self.ddb_subclient_load()
            if self.ddbbackup_subclient.storage_policy == self.storage_policy_name:
                self.log.info(
                    "testcase storage policy is associated to the DDB subclient: trying to dis-associate it")
                self.create_common_items()

            self.log.info("Deleting Storage policy %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            self.log.info("Deleting Library %s if exists", self.library_name)
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.warning("previous run clean up ERROR %s", str(exp))

    def run_backup_job(self, job_type, different_subclient=None):
        """
        running a backup job depending on argument

        Args:
            job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)

            different_subclient   (subclient object)
                                            if the backup job is not
                                            to be run on the default
                                            subclient object of the
                                            testcase.
        Returns:
            job object

        Raises:
            Exceptions
                if job does not complete successfully

        """
        self.log.info("Starting backup job type: %s", job_type)
        if different_subclient is not None:
            job = different_subclient.backup(job_type)
        else:
            job = self.subclient.backup(job_type)
        self.log.info("Backup job: %s", str(job.job_id))
        self.log.info("job type: %s", job_type)
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)
        return job

    def wait_for_job_backup_phase(self, job):
        """
        wait till the job comes in backup phase

        Args:
            job       (job object)          job currently
                                            in progress

        Returns:
            boolean

        Exceptions:
            None
        """
        # till the point job is not finished, check
        # purposely left previous phase check out
        while not job.is_finished and job.status.lower not in [
                "failed", "killed"]:
            if job.phase.lower() == "backup":
                return True
            time.sleep(1)
            # check every 1 second if the job is in backup phase
            # at the very first moment it is found in backup phase, send an alert
        # else we have missed the very first moment for backup phase
        # wait till the job is finished and return False
        return False

    def ddb_subclient_load(self):
        """
        sets the ddb subclient variable from MA of our testcase

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if DDBBackup subclient does not exist.

        """
        # check if DDBBackup subclient exists, if it doesn't fail the testcase
        default_backup_set = self.commcell.clients.get(
            self.tcinputs.get("MediaAgentName")).agents.get(
                "File System").backupsets.get(
                    "defaultBackupSet")

        if default_backup_set.subclients.has_subclient("DDBBackup"):
            self.log.info("DDBBackup subclient exists")
            self.log.info(
                "Storage policy associated with the DDBBackup subclient is %s",
                default_backup_set.subclients.get("DDBBackup").storage_policy)
            self.ddbbackup_subclient = default_backup_set.subclients.get(
                "DDBBackup")
        else:
            raise Exception("DDBBackup Subclient does not exist:FAILED")

    def create_resources(self):
        """
        creates the required resources/ defines paths for this testcase

        Args:
            None

        Returns:
            None

        """
        # as part of testcase setup, we run a dedupe backup job under create resources heading
        # to populate the ddb on MA so that there are some representative
        # entries

        # create the required resources for the testcase
        # get the drive path with required free space

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)

        # creating testcase directory, mount path, content path, dedup
        # store path
        self.testcase_path_client = f"{drive_path_client}{self.id}"

        self.mount_path = self.media_agent_machine.join_path(
            self.tcinputs.get("mount_path"), self.id)
        self.dedup_store_path = self.media_agent_machine.join_path(
            self.tcinputs.get("dedup_path"), self.id)

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.client_machine.create_directory(self.content_path, force_create=True)

        # create library
        self.library = self.mm_helper.configure_disk_library(
            self.library_name, self.tcinputs.get("MediaAgentName"), self.mount_path)

        # create SP
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            self.storage_policy_name,
            self.library_name,
            self.tcinputs.get("MediaAgentName"),
            self.dedup_store_path)

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(
            self.backupset_name, self.agent)

        # representative entries to be added in the same dedupe store
        self.log.info("generate dummy content for representative subclient")
        self.dummy_content_path = self.client_machine.join_path(
            self.content_path, "dummy_content")
        if self.mm_helper.create_uncompressable_data(
                self.client.client_name, self.dummy_content_path, 2.0, 1):
            self.log.info(
                "generated content for dummy subclient %s",
                "dummy_" + self.subclient_name)

        # create dummy subclient and add content
        self.subclient = self.mm_helper.configure_subclient(
            self.backupset_name,
            "dummy_" + self.subclient_name,
            self.storage_policy_name,
            self.dummy_content_path,
            self.agent)

        self.log.info("run dedupe full backup for populating ddb")
        self.run_backup_job("FULL")

        self.log.info("generate content for actual subclient")
        self.content_path = self.client_machine.join_path(
            self.content_path, "actual_content")
        size = 2.5 * int(self.tcinputs.get("testcaseFactor"))
        if self.mm_helper.create_uncompressable_data(
                self.client.client_name, self.content_path, size, 1):
            self.log.info(
                "generated content for subclient %s",
                self.subclient_name)
            self.log.info("content generated size %s GB", size)

        # create subclient and add subclient content
        self.subclient = self.mm_helper.configure_subclient(
            self.backupset_name,
            self.subclient_name,
            self.storage_policy_name,
            self.content_path,
            self.agent)

        self.ddb_subclient_load()

    def check_for_snapshot(self, ddb_backup_job_id):
        """
        This function checks if snapshot has been created or not.
        Args:
            None

        Returns:
            None

        Raises:
            Exceptions None
        """
        statement = "lvcreate --snapshot"
        (matched_line, matched_string) = self.dedup_helper.parse_log(
            self.tcinputs.get("MediaAgentName"),
            "clBackupParent.log",
            regex=statement,
            jobid=ddb_backup_job_id,
            escape_regex=True,
            single_file=True)
        return matched_line, matched_string

    def validations_checks(self):
        """
        do all the validations for the testcase here

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if there is a problem in validations.

        """
        common = str(self.sidb_id) + "-0-" + str(self.substore_id) + "-0"
        # SIDBEngId-GrNo-SubStoId-SpltNo

        error_flag = []
        self.log.info("VALIDATIONS AND CHECKS BEGIN")
        self.log.info("******************************************")
        self.log.info("******************************************")

        self.log.info(
            "validate if the DDB Backup job quiesced the ddb store for the dedupe backup job")
        self.log.info("******************************************")
        statement = "Suspended the DDB, Quiesce Token"
        found = False
        quiesced_ddb_store = []
        (matched_lines, matched_string) = self.dedup_helper.parse_log(
            self.tcinputs.get("MediaAgentName"), "SIDBEngine.log", regex=statement,
            escape_regex=True, single_file=True)
        for matched_line in matched_lines:
            if common in matched_line:
                found = True
                quiesced_ddb_store.append(matched_line)
        if found:
            self.log.info(
                "Result: Pass Quiescing took place for the DDb store of this testcase")
        else:
            self.log.info("Result: Fail")
            error_flag += ["quiesce did not take place for the ddb store of this testcase"]
        self.log.info("******************************************")

        self.log.info("validate the creation of snapshot")
        self.log.info("******************************************")
        (matched_line, matched_string) = self.check_for_snapshot(self.ddb_backup_job.job_id)
        # since the DDBBackup job was suspened thus snapshot creation will
        # take place again
        self.log.info("Number of snapshots before Suspend/Resume %s", str(self.num_snapshot))
        if matched_line and len(matched_string) >= 2*self.num_snapshot:
            self.log.info("Result :Pass")
            self.log.info(matched_string)
        else:
            self.log.error("Result: Failed")
            self.log.info(matched_string)
            error_flag += ["failed to find: 'Shadow Creation succeeded, ShadowId is'"]
        self.log.info("******************************************")

        self.log.info(
            "validate whether the snapshot was deleted/ unmounted (in the case of unix)")
        self.log.info("******************************************")
        # carry the matched_string list from above validation
        # there can be multiple snapshots created which
        # may lead to multiple files created belonging to
        # snapshot which may need to be mounted
        # if the snapshot has been deleted then these files will not exist
        # here
        if not matched_line:
            self.log.info("Result: Failed")
            self.log.error(
                "since snapshot was not created thus no deletion will take place")
            error_flag += ["no snapshot created thus no deletion"]
        elif len(matched_string) <= 1:
            self.log.info(
                "only single snapshot was created, multiple snapshots should have been created")
            error_flag += ["multiple snapshots not created"]
        else:
            self.log.info("checking for deletion of created snapshot")
        command = 'if test -e "{0}"; then echo "TRUE"; fi'
        snapshot_deleted = True
        for line in matched_line:
            line_contents = line.split()
            file_path = line_contents[-1].rpartition(
                '/')[0] + "/" + line_contents[-2]
            output = self.media_agent_machine.execute(
                command.format(file_path))
            if output == "TRUE":
                # this means that the snapshot file exists
                # snapshot has not been deleted
                snapshot_deleted = False
                self.log.info(
                    "snapshot file %s NOT DELETED from volume group", line_contents[-2])
            else:
                self.log.info(
                    "snapshot file %s deleted from volume group", line_contents[-2])
        if snapshot_deleted:
            self.log.info("Result:Pass")
        else:
            self.log.info("Result: Failed")
            self.log.error("snapshot was not deleted")
            error_flag += ["snapshot was not deleted automatically as part of the DDBBackup"]

        if error_flag:
            # if the list is not empty then error was there, fail the test
            # case
            self.log.info(error_flag)
            raise Exception("testcase failed")

    def run(self):
        """
        Run function of this test case

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if error in running the testcase.
        """
        try:
            self.previous_run_clean_up()
            self.create_resources()

            # run a job to initialize the DDB
            job = self.subclient.backup("FULL")
            self.log.info("Backup job: %s", str(job.job_id))

            # wait for the job to complete
            if not job.wait_for_completion():
                raise Exception("Job {0} Failed with {1}".
                                format(job.job_id, job.delay_reason))
            self.log.info("job %s complete", job.job_id)

            # get store and substore info
            return_list = self.dedup_helper.get_sidb_ids(
                self.storage_policy.storage_policy_id, "Primary")
            self.sidb_id = int(return_list[0])
            self.substore_id = int(return_list[1])

            # add dummy file to split path
            split_folder_path = self.media_agent_machine.join_path(self.dedup_store_path, "CV_SIDB", '2',
                                                                   str(self.sidb_id), "Split00")
            dummy_file_path = self.media_agent_machine.join_path(split_folder_path, "Dummy_folder")
            self.opt_selector.create_uncompressable_data(self.ma_name, dummy_file_path, 20.0, 1,
                                                         suffix="Secondary_647431.idx")

            # crate new content for subclient
            self.log.info("generate content for actual subclient")
            self.content_path = self.client_machine.join_path(
                self.content_path, "actual_content", "1")
            size = 2.5 * int(self.tcinputs.get("testcaseFactor"))
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.content_path, size, 1):
                self.log.info(
                    "generated content for subclient %s",
                    self.subclient_name)
                self.log.info("content generated size %s GB", size)

            jobs_list = []

            # run backup with the testcase subclient
            job = self.subclient.backup("FULL")
            self.log.info("Backup job: %s", str(job.job_id))
            time.sleep(5)
            jobs_list.append(job)

            # wait for job to go into backup phase, then start the DDB Back up job
            # starting the ddb backup job when dedupe backup job is in backup phase
            # leads to strong chance of sidb2 process being active when ddb is being read
            # for snapshot to be taken

            if self.wait_for_job_backup_phase(job):
                # now job is in backup phase for the very first time
                # start the DDB Backup job
                time.sleep(3)
                self.log.info("the dedupe backup job is in BACKUP phase now")
                self.log.info("starting DDB Backup job...")
                self.ddb_backup_job = self.ddbbackup_subclient.backup("FULL")
                self.log.info("DDB Backup job: %s", str(self.ddb_backup_job.job_id))
                jobs_list.append(self.ddb_backup_job)

                if self.wait_for_job_backup_phase(self.ddb_backup_job):
                    # when the DDB Backup job is in back up phase, suspend the job
                    # give some time in between
                    self.log.info("the DDBBackup job is in backup phase")
                    self.log.info("waiting for creation of snapshot")
                    time.sleep(10)
                    wait_limit = 0

                    self.log.info("wait for maximum five minutes")
                    while wait_limit < 60:
                        (matched_line, matched_string) = self.check_for_snapshot(self.ddb_backup_job.job_id)
                        if matched_line:
                            # record the number of snapshots created
                            # there can be multiple snapshots considering ddbs spread over multiple
                            # volume groups
                            self.num_snapshot = len(matched_line)
                            for line in matched_line:
                                line_contents = line.split()
                                file_path = line_contents[-1].rpartition(
                                    '/')[0] + "/" + line_contents[-2]
                                self.log.info("the snapshot location is %s", file_path)

                            break
                        wait_limit += 1
                        time.sleep(5)
                        self.log.info("Another 5 second try")

                    if wait_limit == 60:
                        raise Exception("snapshot was not created: check DDBBackup job logs")
                    self.log.info("suspending the DDBBackup job")
                    self.log.info("waiting for DDBBackup job to get suspended")
                    self.ddb_backup_job.pause(wait_for_job_to_pause=True)
                else:
                    self.log.info(
                        "failed to get the DDB backup job in BACKUP PHASE")
                    raise Exception(
                        "failed to get DDB backup job in BACKUP PHASE to start DDB backup job")
            else:
                self.log.info(
                    "failed to get the dedupe backup job in BACKUP PHASE")
                raise Exception(
                    "failed to get dedupe backup job in BACKUP PHASE to start DDB backup job")
            # when ddb backup job runs, it will backup all
            # the partitions of the ddb on the particular
            # media agent, we will require the index made to refer
            # to which partition's part is stored where
            # as a result of ddb backup job

            # now resume the DDB Backup job
            self.log.info("Resume the DDBBackup job")
            self.ddb_backup_job.resume(wait_for_job_to_resume=True)

            self.log.info("wait for all the jobs to be completed...")
            for job in jobs_list:
                if not job.wait_for_completion():
                    raise Exception("Job {0} Failed with {1}".
                                    format(job.job_id, job.delay_reason))
                self.log.info("job %s complete", job.job_id)

            # remove dummy file
            self.media_agent_machine.remove_directory(dummy_file_path)

            # get the sidb id, sidb sub-store id to check for quiescing of ddb
            # store
            return_list = self.dedup_helper.get_sidb_ids(
                self.storage_policy.storage_policy_id, "Primary")
            self.sidb_id = int(return_list[0])
            self.substore_id = int(return_list[1])

            self.validations_checks()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def create_common_items(self):
        """
        creates items which are to be left behind, there are common resources which
        can be used by other ddb backup testcases too
        they will act as default placeholders for ddb subclient

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if error in re-associating storage policy of ddb subclient.
        """
        mount_path = self.media_agent_machine.join_path(self.tcinputs.get(
            "mount_path"), f"ddb_cases_common_files_{self.ma_name}", f"mount_path_common_lib_{self.ma_name}")
        dedup_store_path = self.media_agent_machine.join_path(self.tcinputs.get(
            "dedup_path"), f"ddb_cases_common_files_{self.ma_name}", f"dedup_path_common_sp_{self.ma_name}")

        # create common library
        self.mm_helper.configure_disk_library(
            f"common_lib_ddb_cases_{self.ma_name}", self.tcinputs.get("MediaAgentName"), mount_path)

        # create SP
        self.dedup_helper.configure_dedupe_storage_policy(
            f"common_sp_ddb_cases_{self.ma_name}", f"common_lib_ddb_cases_{self.ma_name}",
            self.tcinputs.get("MediaAgentName"), dedup_store_path)

        self.ddbbackup_subclient.storage_policy = f"common_sp_ddb_cases_{self.ma_name}"
        self.run_backup_job("FULL", different_subclient=self.ddbbackup_subclient)

    def tear_down(self):
        """
        deletes all items of the testcase

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if error in cleanup.
        """
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            self.log.info("deleting backupset and SP of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            # in case the storage policy of this testcase gets associated to the DDB subclient
            # will cause error in clean up
            # create a new common policy - leave it behind - delete the
            # testcase storage policy

            # do this only if testcase storage policy is associated to the DDB
            # subclient
            self.ddb_subclient_load()
            if self.ddbbackup_subclient.storage_policy == self.storage_policy_name:
                self.log.info(
                    "testcase storage policy is associated to the DDB subclient:"
                    " trying to dis-associate it")
                self.create_common_items()

            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("storage policy deleted")
            else:
                self.log.info("storage policy does not exist.")

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted")
            else:
                self.log.info("Library does not exist.")

            if self.client_machine.check_directory_exists(self.dummy_content_path):
                self.client_machine.remove_directory(self.dummy_content_path)
                self.log.info("Deleted the dummy generated data.")
            else:
                self.log.info("dummy content directory does not exist.")

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
