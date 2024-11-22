# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    deallocate_resources() -- cleanup

    get_active_files_store() -- returns store object

    run_backup_job() --  run a backup job on a subclient

    mark_mountpath_state() -- mark a mountpath as online or offline

    get_zeroref_count_for_store()  --  get pending delete count for one substore of ddb store

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case



Input JSON:

54604: {
        "MountPathList" : "F:\\ZeroRefMountPath1,F:\\ZeroRefMountPath2",
        "AgentName": "File System",
        "MediaAgentName": "bbcs7_2",
        "ClientName" : "mmdedup35"
}

Design Steps:
-deallocate resources
-create resources
-disable RWP
-create data and run 2 backups
-get chunk of job that will be deleted, confirm it exists
-delete job, run data aging
-run a new backup
-verify mmdeletedaf empties of the chunkid I'm tracking
-rename mp folder
-mark mp offline via query
-add new mp
-add reg key DDBMarkAndSweepRunIntervalSeconds
-run backup to trigger MS
-get current zerorefcount, it should be non-zero now on each of the 2 partitions
-remove reg key DDBMarkAndSweepRunIntervalSeconds
-run dataaging/backup/checkzeroref 3 times, to confirm its not draining because mp is offline
-rename mp folder back to original name
-mark mp online via query
-for loop of 10, run data aging/backup, and verify that zeroref goes down
-validate physical pruning (check_file_exists on the chunk)
-tear down: re-enable RWP, deallocate resources


"""
import time
from AutomationUtils import constants
from AutomationUtils import config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "zeroref_pruning_offline_mountpath"
        self.tcinputs = {
            "MediaAgentName": None,
            "MountPathList": None,
        }

        self.backupset_obj = None
        self.mediaagentname = None
        self.machineobj = None
        self.ma_machineobj = None
        self.mm_helper = None
        self.dedup_obj = None
        self.subclient_obj = None
        self.is_time_moved = False
        self.dedup_path = None
        self.dedup_path_base = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.client_system_drive = None
        self.mountpathlist = None
        self.sqluser = None
        self.sqlpassword = None
        self.ma_system_drive = None
        self.storage_pool = None
        self.storage_pool_name = None
        self.sidb_id = None
        self.storage_policy = None
        self.store_obj = None
        self.substore_id = None
        self.is_user_defined_dedup = False
        self.result_string = ""
        self.ma_client = None

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        self.mm_helper = mahelper.MMHelper(self)
        self.dedup_obj = DedupeHelper(self)
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        suffix = str(self.mediaagentname)[:] + "_" + str(self.client.client_name)[:]
        self.mountpathlist = self.tcinputs['MountPathList'].split(',')

        self.machineobj = Machine(self.client)
        self.client_system_drive = optionobj.get_drive(self.machineobj, 25*1024)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        self.ma_system_drive = optionobj.get_drive(self.ma_machineobj, 25*1024)

        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machineobj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for a linux MA!")
            raise Exception("LVM enabled dedup path not supplied for a linux MA!")
        if self.is_user_defined_dedup:
            self.dedup_path_base = self.ma_machineobj.join_path(self.tcinputs["dedup_path"],
                                                                "DDBs", "tc_%s_%s" % (self.id, suffix))
        else:
            self.dedup_path_base = self.ma_machineobj.join_path(self.ma_system_drive,
                                                                "DDBs", "tc_%s_%s" % (self.id, suffix))
        self.dedup_path = self.ma_machineobj.join_path(self.dedup_path_base, "partition1")
        self.storage_pool_name = "%s_POOL_%s" % (str(self.id), suffix)
        self.storage_policy_name = "%s_SP_%s" % (str(self.id), suffix)
        self.backupset_name = "%s_BS_%s" % (str(self.id), suffix)
        self.subclient_name = "%s_SC_%s" % (str(self.id), suffix)
        self.content_path = self.machineobj.join_path(self.client_system_drive, "content_54604")
        self.mountpathlist = ["%s_%s" % (x, suffix) for x in self.mountpathlist]
        self.sqluser = config.get_config().SQL.Username
        self.sqlpassword = config.get_config().SQL.Password

        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))

    def deallocate_resources(self):
        """
        removes all resources allocated by the Testcase
        """
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("dependent storage policy deleted")
        else:
            self.log.info("dependent storage policy does not exist.")

        if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.commcell.storage_pools.delete(self.storage_pool_name)
            self.log.info("Storage pool deleted")
        else:
            self.log.info("Storage pool does not exist.")
        self.commcell.disk_libraries.refresh()

        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

        self.log.info("clean up successful")

    def get_active_files_store(self):
        """returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def run_backup_job(self, backuptype="Full"):
        """
        Run a backup job on subclient
        Args:
            backuptype (str) -- Backup type , Full by default.

        Return:
            job object of the successfully completed job.
        """

        job = self.subclient_obj.backup(backuptype)
        if not job.wait_for_completion():
            raise Exception("Failed to run %s backup with error: %s" % (backuptype, job.delay_reason))
        self.log.info("Backup job [%s] completed", job.job_id)
        return job

    def mark_mountpath_state(self, mountpath_id, state):
        """
        Mark a mountpath as online or offline
        Args:

            mountpath_id (int) -- Mount path id to be marked online or offline

            state (str) -- mountpath state to mark - online or offline

        Return:
            n/a
        """

        if state.lower() == "offline":
            query = "update mmmountpath set isoffline=1, isEnabled = 0 where mountpathid = %s " % mountpath_id
        else:
            query = "update mmmountpath set isoffline=0, isEnabled = 1 where mountpathid = %s " % mountpath_id
        self.log.info("QUERY: %s", query)
        self.mm_helper.execute_update_query(query, self.sqlpassword, self.sqluser)
        self.log.info("successfully updated mountpath status")

    def get_zeroref_count_for_store(self, engine_id, sub_id):
        """
        Get latest pending delete count for one substore of ddb store as present in idxsidbusagehistory table
        Args:
            engine_id (int) -- SIDB engine id.
            sub_id (int) -- SIDB substore id.

        Return:
            zeroref_count:  (int)    An integer representing the latest pending delete count for the substore
        """

        query = "select top 1 zerorefcount from IdxSIDBUsageHistory where sidbstoreid=%s and substoreid=%s and " \
                "historytype=0 order by ModifiedTime desc" % (engine_id, sub_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        zeroref_count = self.csdb.fetch_one_row()[0]
        self.log.info("QUERY OUTPUT : %s" % zeroref_count)
        return zeroref_count

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("cleaning up previous run")
            self.deallocate_resources()

            self.log.info("TC environment configuration started")

            # create Storage Pool
            self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpathlist[0],
                                                                self.mediaagentname, self.mediaagentname,
                                                                self.dedup_path)

            self.log.info("---Successfully configured Storage Pool - %s", self.storage_pool_name)

            # get library object from storage pool so another mountpath can be added later
            self.commcell.disk_libraries.refresh()
            disk_library_obj = self.commcell.disk_libraries.get(self.storage_pool_name)

            # create dependent storage policy
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     library=self.storage_pool_name,
                                                                     media_agent=self.mediaagentname,
                                                                     global_policy_name=self.storage_pool_name,
                                                                     dedup_media_agent=self.mediaagentname,
                                                                     dedup_path=self.dedup_path)

            self.log.info("---Successfully configured dependent storage policy - %s", self.storage_policy_name)

            # get dependent copy object to be referenced later
            sp_copy_obj = self.storage_policy.get_copy("Primary")

            # adding second partition to the ddb store
            self.get_active_files_store()
            self.sidb_id = self.store_obj.store_id
            self.substore_id = self.store_obj.all_substores[0][0]
            new_ddb_path = self.ma_machineobj.join_path(self.dedup_path_base, "partition2")
            self.store_obj.add_partition(new_ddb_path, self.mediaagentname)
            self.log.info("---Successfully added second partition to the ddb---")

            # Configure backup set and subclients
            self.log.info("---Configuring backup set---")
            self.backupset_obj = self.mm_helper.configure_backupset(self.backupset_name)

            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)
            self.machineobj.create_directory(self.content_path)

            self.log.info("---Configuring subclient---")
            self.subclient_obj = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name,
                                                                    self.storage_policy_name,
                                                                    content_path=self.content_path)

            self.subclient_obj.data_readers = 1

            # disable RWP so mountpath can get renamed later in TC
            if self.ma_machineobj.os_info.lower() == 'windows':
                self.log.info('Disabling Ransomware protection on MA')
                self.commcell.media_agents.get(
                    self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)
                self.log.info("Successfully disabled Ransomware protection on MA")

            self.log.info("----------TC environment configuration completed----------")

            # STEP : Generate unique data - 500 MB on client and take 2 backups
            self.log.info("---Creating uncompressable unique data---")
            backup_jobs_list = []
            for interval in range(0, 2):
                self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.1)
                self.log.info("starting backup job")
                backup_jobs_list.append(self.run_backup_job())
                # sleep in between backup jobs to avoid job overlap problem
                time.sleep(15)

            # STEP : Make sure that idxsidbusagehistory shows pending deletes as 0
            zerorefcount_before = self.get_zeroref_count_for_store(self.sidb_id, self.substore_id)
            self.log.info("Before deleting any backup jobs, zeroref count on store = %s", zerorefcount_before)

            # Get Mountpath ID
            self.log.info("Fetching MountPathID for the mount path in library %s", self.storage_pool_name)
            query = "select mountpathid,mountpathname from mmmountpath where libraryid = ( select LibraryId from " \
                    "mmlibrary where aliasname =  '%s')" % self.storage_pool_name
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            mountpath_id, mountpath_name = self.csdb.fetch_one_row()
            self.log.info("MountPathID = %s and MountPathName = %s", mountpath_id, mountpath_name)

            # STEP : Make a note of chunk for job being deleted and confirm its presence
            delete_job = backup_jobs_list[-1]
            query = """select id,volumeid from archchunk where id = (
                        select archchunkid from archchunkmapping where archfileid in (
                        select id from archfile where jobid=%s and filetype=1))""" % delete_job.job_id
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            chunk_id, volume_id = self.csdb.fetch_one_row()
            self.log.info("chunkid = %s and volumeid = %s", chunk_id, volume_id)

            # check if chunk folder exists
            self.log.info("wait 1 min to make sure chunk has been written to disk before confirming its existence")
            time.sleep(60)
            os_sep = self.ma_machineobj.os_sep
            chunk_to_validate = "%s%s%s%sCV_MAGNETIC%sV_%s%sCHUNK_%s" \
                                "%sSFILE_CONTAINER.idx" % (self.mountpathlist[0],
                                                           os_sep, mountpath_name, os_sep, os_sep, volume_id,
                                                           os_sep, chunk_id, os_sep)

            if self.ma_machineobj.check_file_exists(chunk_to_validate):
                self.log.info("Successfully validated presence of chunk - %s", chunk_to_validate)
            else:
                # Raise Exception and terminate TC as something is wrong.
                raise Exception("Failed to validate presence of chunk - %s", chunk_to_validate)

            # Update MMConfig to get pruning done faster
            self.mm_helper.update_mmconfig_param(
                'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 1, 1)

            # STEP : Delete Job and run data aging
            self.log.info('Deleting backup job [%s]', delete_job.job_id)
            sp_copy_obj.delete_job(delete_job.job_id)
            data_aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                                  storage_policy_name=self.storage_policy_name,
                                                                  is_granular=True, include_all=False,
                                                                  include_all_clients=True,
                                                                  select_copies=True, prune_selected_copies=True)
            self.log.info("data aging job: %s", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.info("Failed to run data aging with error: %s", data_aging_job.delay_reason)

            # Delete contents of content directory
            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)
            self.machineobj.create_directory(self.content_path)

            # Run a backup
            self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.1)
            self.run_backup_job()
            chunk_deleted = False
            for attempt in range(1, 11):
                self.log.info("MMDeletedAF Validation Attempt - [%s]", attempt)
                query = "select archchunkid from mmdeletedaf where sidbstoreid=%s" % self.sidb_id
                self.log.info("QUERY: %s", query)
                self.csdb.execute(query)
                chunk_id = self.csdb.fetch_one_row()[0]
                if chunk_id == '':
                    self.log.info("MMDeletedAF does not have any entry for chunk %s", chunk_to_validate)
                    chunk_deleted = True
                else:
                    self.log.error("MMDeletedAF still has entry for chunk %s", chunk_to_validate)
                    self.log.info("Sleeping for 2 minutes")
                    time.sleep(120)
            if not chunk_deleted:
                raise Exception("MMDeletedAF entries not being picked up for "
                                "pruning even after 20 minutes.. Exiting ..")

            # STEP : Rename the mount path folder and make it inaccessible
            self.log.info(f'renaming mountpath {self.mountpathlist[0]} to make it inaccessible')
            self.ma_machineobj.rename_file_or_folder(self.mountpathlist[0],
                                                     "%s_renamed" % (self.mountpathlist[0]))

            self.log.info("Marking MountPath offline for library %s", self.storage_pool_name)
            self.mark_mountpath_state(mountpath_id, 'offline')
            self.log.info("Successfully marked MountPath offline")

            # STEP : Add new MP
            self.log.info("Adding a new mount path %s to library to enable backups", self.mountpathlist[1])
            disk_library_obj.add_mount_path(self.mountpathlist[1], self.mediaagentname)
            self.log.info("Successfully added new mountpath - %s", self.mountpathlist[1])

            # add reg key to override CS settings and run Mark and Sweep immediately
            self.log.info("setting DDBMarkAndSweepRunIntervalSeconds additional setting to 120")
            self.ma_client.add_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds",
                                                  "INTEGER", "120")
            self.log.info("wait 30 seconds to make sure reg key is set on ma")
            time.sleep(30)

            # run backup to make sure MS gets triggered and zeroref gets generated
            iteration = 1
            zerorefcount_added = False
            self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.1)
            while not zerorefcount_added and iteration < 3:
                self.run_backup_job()
                zerorefcount_after = self.get_zeroref_count_for_store(self.sidb_id, self.substore_id)
                self.log.info("After deleting the backup job, zeroref count on store = %s", zerorefcount_after)
                if zerorefcount_after != 0:
                    zerorefcount_added = True
                else:
                    self.log.info(f'iteration {iteration} of 3 has no zeroref yet, will run another backup'
                                  f' to try to trigger MS again...')
                    iteration += 1
            if iteration == 3:
                self.log.error("FAILURE : no zeroref generated")
                self.result_string = "%s\n%s", \
                    self.result_string, \
                    "FAILURE : no zeroref generated"
                raise Exception(self.result_string)

            # remove reg key that runs Mark and Sweep immediately
            self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
            self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

            # Keep running backups and checking the zeroref count is non-zero
            for attempt in range(0, 3):
                data_aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                                      storage_policy_name=self.storage_policy_name,
                                                                      is_granular=True, include_all=False,
                                                                      include_all_clients=True,
                                                                      select_copies=True, prune_selected_copies=True)
                self.log.info("data aging job: %s", data_aging_job.job_id)
                if not data_aging_job.wait_for_completion():
                    self.log.info("Failed to run data aging with error: %s", data_aging_job.delay_reason)

                self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.1)
                self.run_backup_job()

                zerorefcount_current = self.get_zeroref_count_for_store(self.sidb_id, self.substore_id)
                self.log.info("After deleting the backup job, zeroref count on store = %s", zerorefcount_current)
                if zerorefcount_current < zerorefcount_after:
                    self.log.error("ERROR : Zeroref count has decreased even when MountPath is offline")
                    self.result_string = "%s\n%s" % (
                        self.result_string, "ERROR : Zeroref count has decreased even when MountPath is offline")
                else:
                    self.log.info("Successfully validated - Zeroref count has not gone down when MountPath is offline")
                time.sleep(60)

            # STEP : Now enable MountPath
            self.log.info("Renaming the mountpath folder back to its original name")
            self.ma_machineobj.rename_file_or_folder("%s_renamed" % (self.mountpathlist[0]),
                                                     self.mountpathlist[0])

            self.log.info("Marking MountPath online for library %s", self.storage_pool_name)
            self.mark_mountpath_state(mountpath_id, 'online')
            self.log.info("Successfully marked MountPath online")

            # STEP : Run another couple of backups and check if pruning has caught up
            zeroref_count_verification = False
            for attempt in range(0, 10):
                self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.1)
                self.run_backup_job()
                data_aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                                      storage_policy_name=self.storage_policy_name,
                                                                      is_granular=True, include_all=False,
                                                                      include_all_clients=True,
                                                                      select_copies=True, prune_selected_copies=True)
                self.log.info("data aging job: %s", data_aging_job.job_id)
                if not data_aging_job.wait_for_completion():
                    self.log.info("Failed to run data aging with error: %s", data_aging_job.delay_reason)
                zerorefcount_final = self.get_zeroref_count_for_store(self.sidb_id, self.substore_id)
                self.log.info("After enabling mount path, zeroref count on store = %s", zerorefcount_final)
                if zerorefcount_final <= zerorefcount_before:
                    self.log.info("Successfully verified that zeroref count has gone down after enabling mountpath")
                    zeroref_count_verification = True
                    break
                else:
                    self.log.warning("Zeroref count is not going down even when mountpath is online, trying again")

            if not zeroref_count_verification:
                self.log.error("Zeroref count is not going down even after 100 minutes since mountpath came online")

            # STEP : Validate successful physical pruning by checking existence of volume and chunk folder
            self.log.info("Sleep to allow 1 minute before checking that idx file is gone from disk")
            time.sleep(60)
            if self.ma_machineobj.check_file_exists(chunk_to_validate):
                self.log.error("FAILURE : Chunk is still present after pruning - %s", chunk_to_validate)
                self.result_string = "%s\n%s", \
                                     self.result_string, \
                                     "FAILURE : Chunk is still present after pruning - %s" % chunk_to_validate
                raise Exception(self.result_string)
            else:
                self.log.info("SUCCESS : Chunk has been successfully deleted physically- %s", chunk_to_validate)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        # remove reg key that runs Mark and Sweep immediately
        self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

        if self.ma_machineobj.os_info.lower() == 'windows':
            self.log.info('Enabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
            self.log.info("Successfully enabled Ransomware protection on MA")

        self.log.info("Performing unconditional cleanup")
        self.deallocate_resources()
