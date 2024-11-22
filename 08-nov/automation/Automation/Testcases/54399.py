# -*- coding: utf-8 -*-
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

    "54399": {
				"CloudLibrary" : "Name of the existing cloud library",
				"AgentName": "File System",
				"MediaAgentName": "Name of the media agent",
				"DatamoverMA" : "Name of the datamover MA",
				"ClientName" : "Name of the client",
				"ClientSystemDriveLetter" : "Client System Drive"
			}

"""
import time
from cvpysdk.exception import SDKException
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "cloud restore"
        self.tcinputs = {
            "CloudLibrary": None,
            "MediaAgentName": None,
            "DatamoverMA": None,
        }

        self.look_ahead_reader_regkey = ""
        self.sp_obj = None
        self.backupset_obj = None
        self.job_runtime_array = []
        self.subclient_obj = None
        self.fulljob_restoredir = None
        self.content_path = None
        self.storage_policy_name = None
        self.clientsystemdrive = None
        self.machineobj = None
        self.ma_machineobj = None
        self.datamoverma = None
        self.library_name = None
        self.mediaagentname = None
        self.backupset_name = None
        self.subclient_name = None
        self.dedup_obj = None
        self.mmhelper_obj = None
        self.plan_name = None
        self.plan_ob = None
        self.storage_pool_name = None
        self.agent = None
        self.storage_pool_ob = None
        self.restore_path = None
        self.subclient_ob = None
        self.storage_assigned_ob = None
        self.backup_set = None
        self.plan_type = None

    def setup(self):
        """Setup function of this test case"""
        self.library_name = self.tcinputs['CloudLibrary']
        self.datamoverma = self.tcinputs['DatamoverMA']
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.plan_name = "plan" + str(self.id)
        self.plan_type = "Server"

        self.dedup_obj = DedupeHelper(self)
        self.dedup_obj.mediaagentname = self.mediaagentname
        self.mmhelper_obj = MMHelper(self)
        self.machineobj = Machine(self.client)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        optionobj = OptionsSelector(self.commcell)
        self.clientsystemdrive = optionobj.get_drive(self.machineobj, 25*1024)
        # self.storage_policy_name = "{0}_{1}".format("cloudsp_tc", self.id)
        self.backupset_name = "{0}_{1}".format("cloudbkpset_tc", self.id)
        self.subclient_name = "{0}_{1}".format("cloudsubclient_tc", self.id)
        self.content_path = self.machineobj.join_path(self.clientsystemdrive, "cloudrestoretestsc")
        self.fulljob_restoredir = self.machineobj.join_path(self.clientsystemdrive, "cloudrestoretest_restoredir")

    def run(self):
        """Run function of this test case"""
        try:
            # Variable initialization
            self.log.info("---Check Library exists---")
            if not self.commcell.disk_libraries.has_library(self.library_name):
                self.log.error("FAILURE : cloud disk library not found. Halting this test case.")
                self.status = constants.FAILED
                self.result_string = "Cloud disk library not found. Halting this test case."
                raise Exception("Cloud disk library not found. Halting this test case.")
            else:
                self.log.info("---Using the existing cloud library - {0}---".format(self.library_name))

            use_existing = False
            self.log.info("----------Configuring TC environment-----------")
            # Delete Backupset if it exists
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("backup set {0} exists .. Deleting the same".format(self.backupset_name))
                try:
                    self.agent.backupsets.delete(self.backupset_name)
                    self.log.info("Successfully deleted backupset {0}".format(self.backupset_name))
                except SDKException:
                    self.log.error("Failed to delete backup set. Halting the test case.")
                    raise Exception("Failed to delete backup set. Halting the test case.")


            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Plan {0} exists. Deleting it.".format(self.plan_name))
                try:
                    self.commcell.plans.delete(self.plan_name)
                except SDKException as ex:
                    self.log.error("Failed to delete plan {0}".format(self.plan_name))
                    self.log.warning("Continuing with same plan")
                    use_existing = True
            if not use_existing:
                self.log.info("Creating new Plan - {0}".format(self.plan_name))
                #Letting storage policy throw its own exception if it fails
                self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type=self.plan_type,
                                                       storage_pool_name=self.library_name)

                self.log.info("---Successfully created Plan - {0}".format(self.plan_name))
                self.plan_ob.schedule_policies['data'].disable()
                self.mmhelper_obj.remove_autocopy_schedule(self.plan_ob.storage_policy.storage_policy_name, "Primary")

            # Configure backup set and subclients
            use_existing = False
            self.log.info("---Configuring backup set---")
            self.backupset_obj = MMHelper.configure_backupset(self)

            self.tcinputs['ContentPath'] = self.content_path
            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)
            if self.machineobj.check_directory_exists(self.fulljob_restoredir):
                self.machineobj.remove_directory(self.fulljob_restoredir)
            self.machineobj.create_directory(self.content_path)

            # STEP : Create a new dedup storage policy using following information
            # Cloud Library , MA
            #
            #current_content_dir = "{0}{1}{2}".format(self.content_path, self.machineobj.os_sep, self.subclient_name)
            current_content_dir = self.machineobj.join_path(self.content_path, self.subclient_name)
            self.machineobj.create_directory(current_content_dir)


            # STEP : Generate unique data - 500 MB on client and take a backup
            self.log.info("---Creating uncompressable unique data---")
            self.mmhelper_obj.create_uncompressable_data(self.client.client_name, current_content_dir, 0.5, 1)

            self.log.info("---Configuring subclient---")
            # Adding subclient to backupset
            self.subclient_obj = self.backupset_obj.subclients.add(self.subclient_name)
            self.log.info(f"Added subclient to backupset [{self.subclient_name}]")
            self.log.info("Adding plan to subclient")
            # Associating plan and content_path to subclient
            self.subclient_obj.plan = [self.plan_ob, [self.content_path]]
            self.log.info(f"Plan [{self.plan_name}] and content_path [{self.content_path}] got added to the subclient [{self.subclient_name}]")

            self.log.info("----------TC environment configuration completed----------")

            fulljobobj = None
            try:
                self.log.info("Starting a FULL backup job")
                fulljobobj = self.subclient_obj.backup("Full")
                self.log.info("Successfully initiated a backup job on subclient with jobid - {0}".format(
                    fulljobobj.job_id))
                if fulljobobj.wait_for_completion() is False:
                    raise Exception("Backup job {0} did not complete in given timeout".format(fulljobobj.job_id))
            except SDKException as ex:
                raise Exception("Failed to run a backup on subclient {0}".format(
                    self.subclient_obj.subclient_name))

            self.log.info("Backup job {0} completed successfully.".format(fulljobobj.job_id))

            # STEP : Generate unique data plus add existing data to the content again
            #
            self.log.info("Copy existing 500 MB data to different directory")
            duplicate_content_dir = self.machineobj.join_path(self.content_path,
                                                              "PreviousBackupContent_{0}".format(self.subclient_name))
            self.machineobj.create_directory(duplicate_content_dir)
            source_for_copy = self.machineobj.get_folders_in_path(current_content_dir)[0]
            self.log.info("Firing command powershell.exe -command copy-item  {0} {1}".format(
                source_for_copy + self.machineobj.os_sep + "*",
                duplicate_content_dir + self.machineobj.os_sep))
            self.machineobj.execute_command("powershell.exe -command copy-item {0} {1}".format(
                source_for_copy + self.machineobj.os_sep + "*",
                duplicate_content_dir + self.machineobj.os_sep))

            self.log.info("Copying to {0} completed successfully".format(duplicate_content_dir))

            self.log.info("Creating 500 MB unique content for same backup job")
            self.mmhelper_obj.create_uncompressable_data(self.client.client_name, duplicate_content_dir, 0.5, 1)
            self.log.info("Successfully created 500 MB unique content")
            # # Associating plan and content_path to subclient
            # self.subclient_obj.plan = [self.plan_ob, [duplicate_content_dir]]
            # self.log.info(
            #     f"Plan [{self.plan_name}] and content_path [{duplicate_content_dir}] got added to the subclient [{self.subclient_name}]")

            incrjobobj = None
            try:
                self.log.info("Starting an INCR backup job")
                incrjobobj = self.subclient_obj.backup("Incremental")
                self.log.info("Successfully initiated a backup job on subclient with jobid - {0}".format(
                    incrjobobj.job_id))
                if incrjobobj.wait_for_completion() is False:
                    raise Exception("Backup job {0} did not complete in given timeout".format(incrjobobj.job_id))
            except SDKException as ex:
                raise Exception("Failed to run a backup on subclient {0}".format(
                    self.subclient_obj.subclient_name))
            self.log.info("Backup job {0} completed successfully.".format(incrjobobj.job_id))

            # STEP
            # Set LookaheadReaderRegistry
            for i in range(0, 2):
                if i % 2 == 0:
                    self.log.info("---Cloud restores without lookaheadreader---")
                    self.look_ahead_reader_regkey = "DataMoverUseLookAheadLinkReader"
                    self.log.info("Setting lookaheadreader registry value to {0} on MA".format(i))
                    self.set_and_validate_regkey("MediaAgent", self.look_ahead_reader_regkey, i, "DWord")
                else:
                    self.log.info("Setting lookaheadreader registry value to {0} on MA".format(i))
                    self.set_and_validate_regkey("MediaAgent", self.look_ahead_reader_regkey, i, "DWord")

            # STEP : Restore using first job and validate following
            # checksum of restored entity matches with source
            # CacheHit = 0 , Number of runs = Non-Zero
            # 1148654 [DM_BASE    ] 3-# LookAheadCtrs: Links (CacheHit/Exp/UnExp/Total): 0/431/0/431,
            # StopCount: Int/Ext [1/0], DDB Wait [0]
            # 1148653 [DM_BASE    ] 2-# SfileRdrCtrs: Blks read [212], Runs [3], Run
            # Len [104656.99] KB (102.20 MB), Async Reads [105], MPIds [1], Files:
            # Hits/Opened [1/105]

                self.log.info("Starting restore on following content directory - {0}".format(current_content_dir))
                try:
                    jobobj = self.subclient_obj.restore_out_of_place(self.client, self.fulljob_restoredir,
                                                                     [current_content_dir], True, True)
                    # self.log.info("Successfully initiated a restore job on subclient with joid - {0}").format(
                    #    jobobj.job_id)
                    if jobobj.wait_for_completion() is False:
                        raise Exception("Failed to complete restore for job {0} within give timeout".format(
                            jobobj.job_id))
                except SDKException as ex:
                    raise Exception("Failed to run restore on subclient {0} with error ==> {1}".format(
                        self.subclient_obj.subclient_name, ex.exception_message))
                job_runtime_list = []
                restore_runtime_job1 = jobobj.summary['jobEndTime'] - jobobj.summary['jobStartTime']
                job_runtime_list.append(restore_runtime_job1)
                self.log.info("Run Time for Restore job => {0}".format(restore_runtime_job1))

                # STEP
                # Validate logs for correct lookaheadreader and sfilereader log lines
                # 5620  db4   05/14 14:35:37 11061 33--1 [DM_BASE    ] Scratch mem [0], Wait for commit [0],
                # Commit by rng [1], DV2LookAltPrim [1]; Lookahead - [1], # of lnks [256],
                # DisableMediaBasedChunk [0] MaxChunkSizeGB [64]
                # 5620  db4   05/14 16:19:07 11062 34--1 [DM_BASE    ] Scratch mem [0],
                # Wait for commit [0], Commit by rng [1], DV2LookAltPrim [1]; Lookahead -
                # [0], # of lnks [256], DisableMediaBasedChunk [0] MaxChunkSizeGB [64]
                if i%2:
                    regkey_logline = r'Look ahead reader enabled. Links \[\d+\]'
                else:
                    regkey_logline = r'Look ahead reader disabled'
                lookahead_logline = r'LookAheadCtrs: Links \(CacheHit/Exp/UnExp/Total\): 0/\d+/0/\d+'
                sfilerdr_logline = r"SfileRdrCtrs: Blks read \[\d+\], Runs \[\d+\],"
                regkey_matched_line = self.dedup_obj.parse_log(
                    self.datamoverma, "CVD.log", regkey_logline, jobobj.job_id, False)[0]
                lookahead_matched_line = self.dedup_obj.parse_log(
                    self.datamoverma, "CVD.log", lookahead_logline, jobobj.job_id, False)[0]
                sfilerdr_matched_line = self.dedup_obj.parse_log(
                    self.datamoverma, "CVD.log", sfilerdr_logline, jobobj.job_id, False)[0]

                # When lookahead reader is disabled
                if i == 0:
                    if (regkey_matched_line and lookahead_matched_line is None and
                            sfilerdr_matched_line is None):
                        self.log.info("Successfully validated logs with disabled LookAheadReader")
                        self.log.info("Log Lines :  {0}".format(regkey_matched_line))
                    else:
                        self.log.error("---Failure in log validation step with disabled LookAheadReader.---")
                # When lookahead reader is enabled
                if i == 1:
                    if regkey_matched_line and lookahead_matched_line and sfilerdr_matched_line:
                        self.log.info("Successfully validated logs with enabled LookAheadReader.")
                        self.log.info(
                            "Log Lines :  {0}\n{1}\n{2}".format(
                                regkey_matched_line,
                                lookahead_matched_line,
                                sfilerdr_matched_line))
                    else:
                        self.log.error("---Failure in log validation step with enabled LookAheadReader.---")

            # STEP : Restore using second job and validate following
            # checksum of restored entity matches with source
            # CacheHit = Non-Zero , Number of runs = Non-Zero
                self.log.info("Starting restore on following content directory - {0}".format(duplicate_content_dir))
                try:
                    jobobj = self.subclient_obj.restore_out_of_place(self.client, self.fulljob_restoredir,
                                                                     [duplicate_content_dir], True, True)
                    # self.log.info("Successfully initiated a restore job on subclient with joid - {0}").format(
                    #    jobobj.job_id)
                    if jobobj.wait_for_completion() is False:
                        raise Exception("Failed to complete restore for job {0} within give timeout".format(
                            jobobj.job_id))
                except SDKException as ex:
                    raise Exception("Failed to run restore on subclient {0} with error ==> {1}".format(
                        self.subclient_obj.subclient_name, ex.exception_message))

                restore_runtime_job2 = jobobj.summary['jobEndTime'] - jobobj.summary['jobStartTime']
                job_runtime_list.append(restore_runtime_job2)
                self.log.info("Run Time for Restore job  => {0}".format(restore_runtime_job2))
                self.job_runtime_array.append([restore_runtime_job1, restore_runtime_job2])

                # STEP
                # Log validation
                lookahead_logline = r'LookAheadCtrs: Links \(CacheHit/Exp/UnExp/Total\): \d+/\d+/0/\d+'
                regkey_matched_line = self.dedup_obj.parse_log(
                    self.datamoverma, "CVD.log", regkey_logline, jobobj.job_id, False)[0]
                lookahead_matched_line = self.dedup_obj.parse_log(
                    self.datamoverma, "CVD.log", lookahead_logline, jobobj.job_id, False)[0]
                sfilerdr_matched_line = self.dedup_obj.parse_log(
                    self.datamoverma, "CVD.log", sfilerdr_logline, jobobj.job_id, False)[0]
                # When lookahead reader is disabled
                if i == 0:
                    if regkey_matched_line  and lookahead_matched_line is None and sfilerdr_matched_line is None:
                        self.log.info("Successfully validated logs with disabled LookAheadReader")
                        self.log.info("Log Lines :  {0}".format(regkey_matched_line))

                    else:
                        self.log.error("---Failure in log validation step with disabled LookAheadReader.---")
                # When lookahead reader is enabled
                if i == 1:
                    if regkey_matched_line and lookahead_matched_line and sfilerdr_matched_line:
                        self.log.info("Successfully validated logs with enabled LookAheadReader.")
                        self.log.info(
                            "Log Lines :  {0}\n{1}\n{2}".format(
                                regkey_matched_line,
                                lookahead_matched_line,
                                sfilerdr_matched_line))
                    else:
                        self.log.error("---Failure in log validation step with disabled LookAheadReader.---")

                # Step
                # Perform data validation
                self.log.info("Performing data validation for content dir ==> {0} and restore dir ==>{1}".format(
                    self.content_path, self.fulljob_restoredir))
                # time.sleep(180)
                difflist = self.machineobj.compare_folders(self.machineobj, self.content_path, self.fulljob_restoredir)
                if not difflist:
                    self.log.info("Successfully validated the data")
                else:
                    self.log.error("Failed to validate the data after cloud restore")
                    self.log.error("DIFFLIST ==> {0} ".format(difflist))
                    raise Exception("Failed to validate the data after cloud restore")

            # STEP
            # Validate that runtime without lookaheadreader > with lookaheadreader

            failtc = 0
            if self.job_runtime_array[0][0] < self.job_runtime_array[1][0]:
                self.log.error("First restore job without lookahead {0} completed faster "
                               "than with lookahead {1}".format(self.job_runtime_array[0][0],
                                                                self.job_runtime_array[1][0]))
                self.status = constants.FAILED
                self.result_string = "{0}\n{1}".format(
                    self.result_string, "First restore job without lookahead completed faster than with lookahead")
                failtc = 1
            else:
                self.log.info("---First restore job with lookahead {0} completed faster "
                              "than without lookahead {1}---".format(self.job_runtime_array[1][0],
                                                                     self.job_runtime_array[0][0]))
            if self.job_runtime_array[0][1] < self.job_runtime_array[1][1]:
                self.log.error("Second restore job without lookahead {0} completed faster "
                               "than with lookahead {1}".format(self.job_runtime_array[0][1],
                                                                self.job_runtime_array[1][1]))
                self.status = constants.FAILED
                self.result_string = "{0}\n{1}".format(
                    self.result_string, "Second restore job without lookahead completed faster than with lookahead")
                failtc = 1
            else:
                self.log.info("---Second restore job with lookahead {0} completed faster "
                              "than without lookahead {1}---".format(self.job_runtime_array[1][1],
                                                                     self.job_runtime_array[0][1]))

            if failtc == 1:
                raise Exception("---Cloud Restore TC failed as restore without lookahead was found to be faster than"
                                " restore with lookahead")
            else:
                self.log.info("===Successfully completed Cloud Restore TestCase===")
                # Validate Logs

        except Exception as exp:
            self.log.error('Failed to execute test case with error: {0}'.format(str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
            self.log.info("Deleted the generated data.")
        else:
            self.log.info("Content directory does not exist.")
        if self.machineobj.check_directory_exists(self.fulljob_restoredir):
            self.machineobj.remove_directory(self.fulljob_restoredir)
            self.log.info("Deleted the restored data.")
        else:
            self.log.info("Restore directory does not exist.")
        self.log.info("Deleting backup set {0}".format(self.backupset_name))
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
        self.log.info("Deleting plan {0}".format(self.plan_name))
        if self.commcell.plans.has_plan(self.plan_name):
            self.commcell.plans.delete(self.plan_name)
        self.log.info("Setting lookaheadreader registry value to 1 on MA")
        self.set_and_validate_regkey("MediaAgent", self.look_ahead_reader_regkey, 1, "DWord")

    def set_and_validate_regkey(self, key, value, data, regtype):
        """Set registry key and validate that it is set correctly
        Agrs:
        key (str)   -- registry key

        value(str)  -- new registry entry under key

        data (str)  -- value to be set for newly created registry entry

        regtype (str) -- type of the registry value to add

        Return:
            True if successful or Exception in case of failure in setting the reistry key value
        """
        self.log.info("Setting registry {0}\\{1} to {2}".format(key, value, data))
        self.ma_machineobj.update_registry(key, value, data, regtype)
        if self.ma_machineobj.get_registry_value(key, value) != str(data):
            raise Exception("Failed to set registry value {0}\\{1} to {2}".format(key, value, data))
        self.log.info("Successfully set registry {0}\\{1} to {2}".format(key, value, data))
        return True
