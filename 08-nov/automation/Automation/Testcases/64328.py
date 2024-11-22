# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    setup_environment() -- configures entities based on inputs

    get_active_files_store() -- gets active files DDB store id

    cleanup()                --  cleanups all created entities

    validate_default_threshold_csdb() -- validate the chunk table threshold set in MMEntityProp for the stores

    run_backups()                  -- runs backup need for the case

    get_ms_run_times()             -- fetches the last MS run times for the stores

    validate_primary_records()     -- validates whether primary records are created for the backups or not

    ma_side_threshold_validation() -- validates whether DDB received correct threshold values or not

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample JSON: values under [] are optional
    "64328": {
        "ClientName": "",
        "AgentName": "File System",
        "MediaAgentName": "",
        "CloudLibraryName": "",
        ** optional **
        "DDBPath": ""
        "existingCloudPool": "",
        "existingDiskPool": ""
        *above pool inputs are required only if stores are created on setup prior to SP34 and setup is upgraded later.*
    }
    Note: for creating new stores, the MA provided should be >= SP34


Note:
    1. providing cloud library is must as there are various vendors for configuration. best is to have it ready
    2. for linux, its mandatory to provide ddb path for a lvm volume
    3. ensure that MP on cloud library is set with pruner MA

Steps:
    1.  Configure Environment with a Disk Store and 2 Cloud Stores
    2.  Run 3 backups each, second backup with partial content, 3rd backup with same content as 2nd one.
        (Disk Store: 15%, Cloud Store1: 15%, Cloud Store2: 67%) of original content
    3.  Validate that CSDB threshold values are set properly. Disk: No entry, Cloud: 20 %, existing stores: -1
    4.  Validate no new primary records are created for 2nd, 3rd backups. Only references should be made.
    5.  Delete first backup jobs, run DA and wait for Phase 2 pruning to happen.
    6.  Delete second backup jobs, run DA and wait for MS to kick in.
    7.  Dump the chunk tables and validate whether MS updated the deletedRecords or not
    8.  Run new backups and validate primary records.
        Disk Store: no records added (only 15% valid data in chunks, but ChunkTableThreshold is 0),
        Cloud Store1: new records added (only 15% valid data in chunks, ChunkTableThreshold is 20),
        Cloud Store2: no records added (67% valid data in chunks, ChunkTableThreshold is 20),
    9. Cleanup environment
"""
import csv
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Basic validations for Dedup Chunk Table"
        self.tcinputs = {
            "MediaAgentName": None,
            "CloudLibraryName": None,
        }
        self.disk_library_name = None
        self.cloud_library_name = None
        self.backupset_name_prefix = None
        self.subclient_name_suffix = None
        self.storage_policy_name_prefix = None
        self.content_path = None
        self.dump_location = None
        self.disk_ddb_path = None
        self.cloud_ddb_path = None
        self.cloud_ddb_path_2 = None
        self.disk_mount_path = None
        self.scale_factor = None
        self.disk_subclient = None
        self.cloud_subclient = None
        self.cloud_subclient_2 = None
        self.disk_library = None
        self.cloud_library = None
        self.disk_primary_copy = None
        self.cloud_primary_copy = None
        self.cloud_primary_copy_2 = None
        self.disk_storage_policy = None
        self.cloud_storage_policy = None
        self.cloud_storage_policy_2 = None
        self.client_machine = None
        self.media_agent_machine = None
        self.mm_helper = None
        self.op_selector = None
        self.dedupe_helper = None
        self.time_moved_unix = False

    def setup(self):
        """ Setup function of this test case. """
        # input values
        ddb_path = self.tcinputs.get('DDBPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor')
        self.cloud_library_name = self.tcinputs.get('CloudLibraryName')

        # defining names
        self.disk_library_name = f"{str(self.id)}_Lib_{self.tcinputs.get('MediaAgentName')[::-1]}_Disk"
        self.subclient_name_suffix = f"{str(self.id)}_SC_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.backupset_name_prefix = f"{str(self.id)}_BS_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.storage_policy_name_prefix = f"{str(self.id)}_SP_{self.tcinputs.get('MediaAgentName')[::-1]}"

        # machine objects
        self.client_machine = Machine(self.tcinputs.get('ClientName'), self.commcell)
        self.media_agent_machine = Machine(self.tcinputs.get('MediaAgentName'), self.commcell)

        # select drive on client & MA for content and DDB
        self.op_selector = OptionsSelector(self.commcell)
        client_path = self.client_machine.join_path(
            self.op_selector.get_drive(self.client_machine, 25*1024), 'automation', self.id)
        media_agent_path = self.media_agent_machine.join_path(
            self.op_selector.get_drive(self.media_agent_machine, 25*1024), 'automation', self.id)

        self.content_path = self.client_machine.join_path(client_path, 'content_path')
        self.dump_location = self.media_agent_machine.join_path(media_agent_path, 'DumpPath')
        self.disk_mount_path = self.media_agent_machine.join_path(media_agent_path, 'DiskMP')

        if not ddb_path:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not provided for Unix MA!..")
            ddb_path = self.media_agent_machine.join_path(media_agent_path, 'DDBs')
            self.disk_ddb_path = self.media_agent_machine.join_path(ddb_path, 'DiskDDB')
            self.cloud_ddb_path = self.media_agent_machine.join_path(ddb_path, 'CloudDDB')
            self.cloud_ddb_path_2 = self.media_agent_machine.join_path(ddb_path, 'CloudDDB_2')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", ddb_path)
            ddb_path = self.media_agent_machine.join_path(ddb_path, 'automation', self.id, 'DDBs')
            self.disk_ddb_path = self.media_agent_machine.join_path(ddb_path, 'DiskDDB')
            self.cloud_ddb_path = self.media_agent_machine.join_path(ddb_path, 'CloudDDB')
            self.cloud_ddb_path_2 = self.media_agent_machine.join_path(ddb_path, 'CloudDDB_2')

        # helper objects
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("Setting up environment...")

        self.disk_library = self.mm_helper.configure_disk_library(self.disk_library_name,
                                                                  self.tcinputs.get('MediaAgentName'),
                                                                  self.disk_mount_path)

        if not self.commcell.disk_libraries.has_library(self.cloud_library_name):
            self.log.error("Cloud library %s does not exist!", self.cloud_library_name)
            raise Exception(f"Cloud library {self.cloud_library_name} does not exist!")
        self.cloud_library = self.commcell.disk_libraries.get(self.cloud_library_name)

        if not self.media_agent_machine.check_directory_exists(self.disk_ddb_path):
            self.media_agent_machine.create_directory(self.disk_ddb_path)
        if not self.media_agent_machine.check_directory_exists(self.cloud_ddb_path):
            self.media_agent_machine.create_directory(self.cloud_ddb_path)

        self.disk_storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
            f"{self.storage_policy_name_prefix}_Disk", library_name=self.disk_library_name,
            ddb_ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.media_agent_machine.join_path(self.disk_ddb_path, "Part1Dir"))
        self.cloud_storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
            f"{self.storage_policy_name_prefix}_Cloud", library_name=self.cloud_library_name,
            ddb_ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.media_agent_machine.join_path(self.cloud_ddb_path, "Part1Dir"))
        self.cloud_storage_policy_2 = self.dedupe_helper.configure_dedupe_storage_policy(
            f"{self.storage_policy_name_prefix}_Cloud_2", library_name=self.cloud_library_name,
            ddb_ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.media_agent_machine.join_path(self.cloud_ddb_path_2, "Part1Dir"))

        self.log.info("Setting MS interval to 1 hour for the dedupe stores")
        disk_store, cloud_store, cloud_store_2 = self.get_active_files_stores()
        self.dedupe_helper.set_mark_and_sweep_interval(disk_store.store_id, 1)
        self.dedupe_helper.set_mark_and_sweep_interval(cloud_store.store_id, 1)
        self.dedupe_helper.set_mark_and_sweep_interval(cloud_store_2.store_id, 1)

        self.log.info("Adding secondary partitions for the stores")
        self.disk_storage_policy.add_ddb_partition(
            str(self.disk_storage_policy.get_copy('Primary').copy_id), str(disk_store.store_id),
            self.media_agent_machine.join_path(self.disk_ddb_path, "Part2Dir"), self.tcinputs.get('MediaAgentName'))
        self.cloud_storage_policy.add_ddb_partition(
            str(self.cloud_storage_policy.get_copy('Primary').copy_id), str(cloud_store.store_id),
            self.media_agent_machine.join_path(self.cloud_ddb_path, "Part2Dir"), self.tcinputs.get('MediaAgentName'))
        self.cloud_storage_policy_2.add_ddb_partition(
            str(self.cloud_storage_policy_2.get_copy('Primary').copy_id), str(cloud_store_2.store_id),
            self.media_agent_machine.join_path(self.cloud_ddb_path_2, "Part2Dir"), self.tcinputs.get('MediaAgentName'))

        self.log.info("setting primary copy retentions to 1 day, 0 cycle")
        self.disk_primary_copy = self.disk_storage_policy.get_copy('Primary')
        self.disk_primary_copy.copy_retention = (1, 0, 1)
        self.cloud_primary_copy = self.cloud_storage_policy.get_copy('Primary')
        self.cloud_primary_copy.copy_retention = (1, 0, 1)
        self.cloud_primary_copy_2 = self.cloud_storage_policy_2.get_copy('Primary')
        self.cloud_primary_copy_2.copy_retention = (1, 0, 1)

        self.log.info("limit max chunk size on the copies to produce more chunks")
        query = f'''update MMDataPath set ChunkSizeMB = 100
                where CopyId in (
                {self.disk_primary_copy.copy_id}, {self.cloud_primary_copy.copy_id}, {self.cloud_primary_copy_2.copy_id}
                )'''
        self.op_selector.update_commserve_db(query)

        self.mm_helper.configure_backupset(f"{self.backupset_name_prefix}_Disk", self.agent)
        self.mm_helper.configure_backupset(f"{self.backupset_name_prefix}_Cloud", self.agent)
        self.mm_helper.configure_backupset(f"{self.backupset_name_prefix}_Cloud_2", self.agent)

        self.disk_subclient = self.mm_helper.configure_subclient(f"{self.backupset_name_prefix}_Disk",
                                                                 f"{self.subclient_name_suffix}_Disk",
                                                                 f"{self.storage_policy_name_prefix}_Disk",
                                                                 self.client_machine.join_path(
                                                                     self.content_path, 'generated_content_disk'),
                                                                 self.agent)
        self.cloud_subclient = self.mm_helper.configure_subclient(f"{self.backupset_name_prefix}_Cloud",
                                                                  f"{self.subclient_name_suffix}_Cloud",
                                                                  f"{self.storage_policy_name_prefix}_Cloud",
                                                                  self.client_machine.join_path(
                                                                      self.content_path, 'generated_content_cloud'),
                                                                  self.agent)
        self.cloud_subclient_2 = self.mm_helper.configure_subclient(f"{self.backupset_name_prefix}_Cloud_2",
                                                                    f"{self.subclient_name_suffix}_Cloud_2",
                                                                    f"{self.storage_policy_name_prefix}_Cloud_2",
                                                                    self.client_machine.join_path(
                                                                        self.content_path, 'generated_content_cloud_2'),
                                                                    self.agent)
        self.disk_subclient.data_readers = 1
        self.disk_subclient.allow_multiple_readers = True
        self.cloud_subclient.data_readers = 1
        self.cloud_subclient.allow_multiple_readers = True
        self.cloud_subclient_2.data_readers = 1
        self.cloud_subclient_2.allow_multiple_readers = True

        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)

    def get_active_files_stores(self):
        """Returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        disk_engine = self.commcell.deduplication_engines.get(f"{self.storage_policy_name_prefix}_Disk", 'primary')
        cloud_engine = self.commcell.deduplication_engines.get(f"{self.storage_policy_name_prefix}_Cloud", 'primary')
        cloud_engine_2 = self.commcell.deduplication_engines.get(
            f"{self.storage_policy_name_prefix}_Cloud_2", 'primary')
        return (disk_engine.get(disk_engine.all_stores[0][0]),
                cloud_engine.get(cloud_engine.all_stores[0][0]), cloud_engine_2.get(cloud_engine_2.all_stores[0][0]))

    def cleanup(self):
        """Performs cleanup of all entities"""
        try:
            self.log.info("cleanup started")

            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("deleting content")
                self.client_machine.remove_directory(self.content_path)

            if self.agent.backupsets.has_backupset(f"{self.backupset_name_prefix}_Disk"):
                self.log.info("deleting backupset: %s", f"{self.backupset_name_prefix}_Disk")
                self.agent.backupsets.delete(f"{self.backupset_name_prefix}_Disk")
            if self.agent.backupsets.has_backupset(f"{self.backupset_name_prefix}_Cloud"):
                self.log.info("deleting backupset: %s", f"{self.backupset_name_prefix}_Cloud")
                self.agent.backupsets.delete(f"{self.backupset_name_prefix}_Cloud")
            if self.agent.backupsets.has_backupset(f"{self.backupset_name_prefix}_Cloud_2"):
                self.log.info("deleting backupset: %s", f"{self.backupset_name_prefix}_Cloud_2")
                self.agent.backupsets.delete(f"{self.backupset_name_prefix}_Cloud_2")

            if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name_prefix}_Disk"):
                self.log.info("deleting storage policy: %s", f"{self.storage_policy_name_prefix}_Disk")
                self.commcell.storage_policies.delete(f"{self.storage_policy_name_prefix}_Disk")
            if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name_prefix}_Cloud"):
                self.log.info("deleting storage policy: %s", f"{self.storage_policy_name_prefix}_Cloud")
                self.commcell.storage_policies.delete(f"{self.storage_policy_name_prefix}_Cloud")
            if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name_prefix}_Cloud_2"):
                self.log.info("deleting storage policy: %s", f"{self.storage_policy_name_prefix}_Cloud_2")
                self.commcell.storage_policies.delete(f"{self.storage_policy_name_prefix}_Cloud_2")

            if self.commcell.disk_libraries.has_library(self.disk_library_name):
                self.log.info("deleting library: %s", self.disk_library_name)
                self.commcell.disk_libraries.delete(self.disk_library_name)
            self.log.info("cleanup completed")
        except Exception as exe:
            self.log.warning("error in cleanup: %s. please cleanup manually", str(exe))

    def validate_default_threshold_csdb(self, disk_store, cloud_store, cloud_store_2=None, existing=False):
        """Validate the Chunk Table Threshold set in MMEntityProp for the Stores

        Args:
            disk_store      (Store) : Store object for the Disk DDB Engine

            cloud_store     (Store) : Store object for the Cloud DDB Engine 1

            cloud_store_2   (Store) : Store object for the Cloud DDB Engine 2

            existing        (bool)  : Boolean value to indicate whether the stores are existing or newly created

        Returns:
            (bool): returns whether threshold values are set properly in CSDB
        """
        query = f'''select	EntityId, intVal
                from	MMEntityProp
                where	propertyName = 'ChunkTableThreshold'
                    and	EntityId in ({disk_store.store_id}, {cloud_store.store_id}
                    {("," + str(cloud_store_2.store_id)) if cloud_store_2 else ""})
                order by EntityId'''
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info("Result: %s", result)
        threshold_dicts = {int(row[0]): int(row[1]) for row in result}
        if not existing:
            # newly created stores
            if len(threshold_dicts) == 2:
                if (threshold_dicts.get(int(cloud_store.store_id)) == 20
                        and threshold_dicts.get(int(cloud_store_2.store_id)) == 20):
                    return True
        else:
            # existing stores
            if len(threshold_dicts) == 2:
                if (threshold_dicts.get(int(disk_store.store_id)) == -1
                        and threshold_dicts.get(int(cloud_store.store_id)) == -1):
                    return True
        return False

    def run_backups(self, size=2048, backup_type="FULL", delete_content=False):
        """Run backup by generating new content to get unique blocks for dedupe backups.

        Args:
            size            (int)   : size of backup content to generate
                Default - 2048 MB

            backup_type     (str)   : type of backup to run
                Default - FULL

            delete_content   (bool) : deleting alternate content(every 3rd file) before running backup
                Default - False
        Returns:
            (Job, Job): returns tuple of job objects for the backup jobs
        """
        additional_content = self.client_machine.join_path(self.content_path, 'generated_content')
        if not delete_content and size > 0:
            self.client_machine.create_directory(self.content_path, force_create=True)
            self.op_selector.create_uncompressable_data(self.client_machine,
                                                        f'{additional_content}_disk', size//1024,
                                                        num_of_folders=0, file_size=512)
            self.op_selector.create_uncompressable_data(self.client_machine,
                                                        f'{additional_content}_cloud', size // 1024,
                                                        num_of_folders=0, file_size=512)
            self.op_selector.create_uncompressable_data(self.client_machine,
                                                        f'{additional_content}_cloud_2', size // 1024,
                                                        num_of_folders=0, file_size=512)
        elif delete_content:
            self.log.info("Deleting Content: Disk SC: 85%, Cloud SC1: 85%, Cloud SC2: 33%")
            self.op_selector.delete_nth_files_in_directory(
                self.client_machine, f'{additional_content}_disk', selector=7, operation='keep')
            self.op_selector.delete_nth_files_in_directory(
                self.client_machine, f'{additional_content}_cloud', selector=7, operation='keep')
            self.op_selector.delete_nth_files_in_directory(
                self.client_machine, f'{additional_content}_cloud_2', selector=3, operation='delete')

        self.log.info("Running %s backups...", backup_type)
        job1 = self.disk_subclient.backup(backup_type)
        self.log.info("Disk SC Backup job: %s", job1.job_id)
        job2 = self.cloud_subclient.backup(backup_type)
        self.log.info("Cloud SC1 Backup job: %s", job2.job_id)
        job3 = self.cloud_subclient_2.backup(backup_type)
        self.log.info("Cloud SC2 Backup job: %s", job3.job_id)
        if not job1.wait_for_completion():
            raise Exception(f"Backup Job {job1.job_id} failed with error: {job1.delay_reason}")
        if not job2.wait_for_completion():
            raise Exception(f"Backup Job {job2.job_id} failed with error: {job2.delay_reason}")
        if not job3.wait_for_completion():
            raise Exception(f"Backup Job {job3.job_id} failed with error: {job3.delay_reason}")
        self.log.info("Backup jobs completed.")
        return job1, job2, job3

    def get_ms_run_times(self, disk_store, cloud_store, cloud_store_2):
        """Fetches the last MS Run times for the stores

        Args:
            disk_store      (Store) : Store object for the Disk DDB Engine

            cloud_store     (Store) : Store object for the Cloud DDB Engine 1

            cloud_store_2   (Store) : Store object for the Cloud DDB Engine 2

        Returns:
            (dict): returns dictionary of DDB MS run times for each store
        """
        self.log.info("Fetching MS Last run times for the Stores")
        query = f"""select	EntityId, longlongVal
                from	MMEntityProp
                where	propertyName = 'DDBMSRunTime'
                    and EntityId in ({disk_store.all_substores[0][0]}, {cloud_store.all_substores[0][0]}, {cloud_store_2.all_substores[0][0]})"""
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info("Result: %s", str(result))
        ms_run_times = dict()
        for row in result:
            ms_run_times[row[0]] = int(row[1])
        return ms_run_times

    def validate_primary_records(self, jobs_tuple, expected):
        """Validates whether primary records are created for the Backups or not

        Args:
            jobs_tuple  (tuple)  : tuple of Job objects for backups

            expected    (bool)   : Boolean to check if new primary records are expected or not
        Returns:
            (bool): Boolean whether new primary records are created according to expectation
        """
        primary_objects = []
        for job in jobs_tuple:
            primary_objects.append(int(self.dedupe_helper.get_primary_objects(job.job_id)))
        if not expected:
            if primary_objects[0] <= 10 and primary_objects[1] <= 10 and primary_objects[2] <= 10:
                self.log.info("No new Primary records were created for all the stores")
                return True
        else:
            if primary_objects[0] <= 10 and primary_objects[1] > 10 and primary_objects[2] <= 10:
                self.log.info("Primary records created just for 1st cloud store with <20% valid data")
                return True
        return False

    # def ma_side_threshold_validation(self, disk_store, cloud_store):
    #     """Validates whether DDB received correct threshold values or not
    #
    #     Args:
    #         disk_store (Store)  : Store object for the DDB of Disk storage
    #
    #         cloud_store (Store) : Store object for the DDB of Cloud storage
    #
    #     Returns:
    #         (bool): returns whether threshold values are received correctly by DDB
    #     """
    #     log_file = "SIDBEngine.log"
    #     log_phrase = ", Dedup Chunk Ratio"
    #     disk_phrase = " " + str(disk_store.store_id) + "-0-"
    #     cloud_phrase = " " + str(cloud_store.store_id) + "-0-"
    #
    #     (matched_lines, matched_string) = self.dedupe_helper.parse_log(
    #         self.tcinputs["MediaAgentName"], log_file, regex=log_phrase, escape_regex=True)
    #     flag = 0
    #     for matched_line in matched_lines:
    #         if disk_phrase in matched_line:
    #             self.log.info("Logging for disk store: %s", matched_line)
    #             if '[0%]' in matched_line:
    #                 flag += 1
    #         if cloud_phrase in matched_line:
    #             self.log.info("Logging for cloud store: %s", matched_line)
    #             if '[20%]' in matched_line:
    #                 flag += 1
    #         if flag == 2:
    #             return True
    #     return False

    def run(self):
        """Run function of this test case"""
        try:
            if self.tcinputs.get('existingDiskPool') and self.tcinputs.get('existingCloudPool'):
                existing_disk_pool = self.commcell.storage_pools.get(self.tcinputs.get('existingDiskPool'))
                existing_cloud_pool = self.commcell.storage_pools.get(self.tcinputs.get('existingCloudPool'))
                existing_disk_engine = self.commcell.deduplication_engines.get(
                    existing_disk_pool.global_policy_name, existing_disk_pool.copy_name)
                existing_cloud_engine = self.commcell.deduplication_engines.get(
                    existing_cloud_pool.global_policy_name, existing_cloud_pool.copy_name)

                if not self.validate_default_threshold_csdb(
                        existing_disk_engine.get(existing_disk_engine.all_stores[0][0]),
                        existing_cloud_engine.get(existing_cloud_engine.all_stores[0][0]), existing=True):
                    raise Exception(
                        "Default Threshold values not set properly in the CSDB. Should be -1 for all existing stores")
                self.log.info("Threshold values set properly to -1 for existing stores in CSDB")

            self.cleanup()
            self.setup_environment()

            jobs_set1 = self.run_backups()
            jobs_set2 = self.run_backups(delete_content=True)

            disk_store, cloud_store, cloud_store_2 = self.get_active_files_stores()

            if not self.validate_default_threshold_csdb(disk_store, cloud_store, cloud_store_2, existing=False):
                raise Exception("Default Threshold values not set properly in the CSDB for newly created stores")
            self.log.info("Threshold values set properly in CSDB for newly created stores")

            self.log.info("*** Validating Primary Record count for 2nd Full Backups:"
                          " new primary records should not created for all stores ***")
            if not self.validate_primary_records(jobs_set2, expected=False):
                raise Exception("Primary records validation failed")
            self.log.info("Primary records validation passed")

            jobs_set3 = self.run_backups(size=0)

            self.log.info("*** Validating Primary Record count for 3nd Full Backups:"
                          " new primary records should not created for all stores ***")
            if not self.validate_primary_records(jobs_set3, expected=False):
                raise Exception("Primary records validation failed")
            self.log.info("Primary records validation passed")
            # self.log.info("*** Validating Dedup Chunk Ratio Threshold value received by SIDB on MA ***")
            # if not self.ma_side_threshold_validation(disk_store, cloud_store):
            #     raise Exception("MA side threshold validation Failed")
            # self.log.info("MA side threshold validation Passed")

            self.log.info("Deleting 1st Backup [%s] on Store [%s]", jobs_set1[0].job_id, disk_store.store_id)
            self.disk_primary_copy.delete_job(jobs_set1[0].job_id)
            self.log.info("Deleting 1st Backup [%s] on Store [%s]", jobs_set1[1].job_id, cloud_store.store_id)
            self.cloud_primary_copy.delete_job(jobs_set1[1].job_id)
            self.log.info("Deleting 1st Backup [%s] on Store [%s]", jobs_set1[2].job_id, cloud_store_2.store_id)
            self.cloud_primary_copy_2.delete_job(jobs_set1[2].job_id)

            self.log.info("Submitting Data Aging Job to age the data")
            da_job1 = self.mm_helper.submit_data_aging_job()
            if not da_job1.wait_for_completion():
                raise Exception(
                    f"Failed to run Data Aging (Job Id: {da_job1.job_id}) with error: {da_job1.delay_reason}")
            self.log.info("Data Aging job(Id: %s) completed", da_job1.job_id)

            self.log.info("Waiting for Phase 2 pruning to kick off for all stores")
            pruning_done = 0
            for _ in range(1, 11):
                self.log.info("sleeping for 180 seconds")
                time.sleep(180)
                if pruning_done & 1 == 0:
                    matched_lines_disk = self.dedupe_helper.validate_pruning_phase(
                        disk_store.store_id, self.tcinputs.get('MediaAgentName'), 2)
                if pruning_done & 2 == 0:
                    matched_lines_cloud = self.dedupe_helper.validate_pruning_phase(
                        cloud_store.store_id, self.tcinputs.get('MediaAgentName'), 2)
                if pruning_done & 4 == 0:
                    matched_lines_cloud_2 = self.dedupe_helper.validate_pruning_phase(
                        cloud_store_2.store_id, self.tcinputs.get('MediaAgentName'), 2)
                if pruning_done & 1 == 0 and matched_lines_disk:
                    self.log.info(matched_lines_disk)
                    pruning_done = pruning_done | 1
                if pruning_done & 2 == 0 and matched_lines_cloud:
                    self.log.info(matched_lines_cloud)
                    pruning_done = pruning_done | 2
                if pruning_done & 4 == 0 and matched_lines_cloud_2:
                    self.log.info(matched_lines_cloud_2)
                    pruning_done = pruning_done | 4
                if pruning_done == 7:
                    self.log.info("Phase 2 pruning kicked off for all stores")
                    break
            if pruning_done != 7:
                raise Exception("Phase 2 pruning isn't started even after 30 mins. pruning_done flag: %d", pruning_done)

            self.log.info("Wait for sidb processes to go down")
            if self.dedupe_helper.wait_till_sidb_down(
                    str(disk_store.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d has gone down", disk_store.store_id)
            else:
                self.log.error("sidb process for engine %d did not go down in the wait period", disk_store.store_id)
                raise Exception("sidb process did not go down under the wait period")
            if self.dedupe_helper.wait_till_sidb_down(
                    str(cloud_store.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d has gone down", cloud_store.store_id)
            else:
                self.log.error("sidb process for engine %d did not go down in the wait period", cloud_store.store_id)
                raise Exception("sidb process did not go down under the wait period")
            if self.dedupe_helper.wait_till_sidb_down(
                    str(cloud_store_2.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d has gone down", cloud_store_2.store_id)
            else:
                self.log.error("sidb process for engine %d did not go down in the wait period", cloud_store_2.store_id)
                raise Exception("sidb process did not go down under the wait period")

            old_ms_run_times = self.get_ms_run_times(disk_store, cloud_store, cloud_store_2)

            self.log.info("Moving time ahead by 1:15:00 hrs on the media agent machine to force MS")
            if self.media_agent_machine.os_info.lower() == 'unix':
                self.media_agent_machine.execute_command("date --set='+1 hours +15 minutes'")
                self.time_moved_unix = True
            elif self.media_agent_machine.os_info.lower() == 'windows':
                self.log.info("disabling the windows time service")
                self.media_agent_machine.execute_command("stop-service w32time")
                self.media_agent_machine.execute_command("Set-Service -Name w32time -StartupType Disabled")
                self.log.info("windows time service disabled")
                self.media_agent_machine.execute_command("set-date -adjust 01:15:00")
            self.log.info("time moved ahead by 1:15:00 hrs on the media agent machine ")

            self.log.info("Deleting 2nd Backup [%s] on Store [%s]", jobs_set2[0].job_id, disk_store.store_id)
            self.disk_primary_copy.delete_job(jobs_set2[0].job_id)
            self.log.info("Deleting 2nd Backup [%s] on Store [%s]", jobs_set2[1].job_id, cloud_store.store_id)
            self.cloud_primary_copy.delete_job(jobs_set2[1].job_id)
            self.log.info("Deleting 2nd Backup [%s] on Store [%s]", jobs_set2[2].job_id, cloud_store_2.store_id)
            self.cloud_primary_copy_2.delete_job(jobs_set2[2].job_id)

            self.log.info("Submitting Data Aging Job to force MS")
            da_job2 = self.mm_helper.submit_data_aging_job()
            if not da_job2.wait_for_completion():
                raise Exception(
                    f"Failed to run Data Aging (Job Id: {da_job2.job_id}) with error: {da_job2.delay_reason}")
            self.log.info("Data Aging job(Id: %s) completed", da_job2.job_id)

            self.log.info("Wait for MS to kick off and complete")
            ms_done = 0
            for _ in range(1, 11):
                self.log.info("sleeping for 180 seconds")
                time.sleep(180)
                new_ms_run_times = self.get_ms_run_times(disk_store, cloud_store, cloud_store_2)
                for sub_store_id in new_ms_run_times.keys():
                    if new_ms_run_times.get(sub_store_id, 0) > old_ms_run_times.get(sub_store_id, 0):
                        ms_done += 1
                if ms_done == 3:
                    self.log.info("MS is kicked off for all stores")
                    break
                ms_done = 0
            if ms_done != 3:
                raise Exception("MS isn't kicked off even after 30 minutes. ms_done flag: %d", ms_done)

            self.log.info("Wait for sidb processes to go down")
            if self.dedupe_helper.wait_till_sidb_down(
                    str(disk_store.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d has gone down", disk_store.store_id)
            else:
                self.log.error("sidb process for engine %d did not go down in the wait period", disk_store.store_id)
                raise Exception("sidb process did not go down under the wait period")
            if self.dedupe_helper.wait_till_sidb_down(
                    str(cloud_store.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d has gone down", cloud_store.store_id)
            else:
                self.log.error("sidb process for engine %d did not go down in the wait period", cloud_store.store_id)
                raise Exception("sidb process did not go down under the wait period")
            if self.dedupe_helper.wait_till_sidb_down(
                    str(cloud_store_2.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d has gone down", cloud_store_2.store_id)
            else:
                self.log.error("sidb process for engine %d did not go down in the wait period", cloud_store_2.store_id)
                raise Exception("sidb process did not go down under the wait period")

            self.log.info("*** Validating Dump Chunk Tables whether deleted records are added or not ***")
            self.media_agent_machine.create_directory(self.dump_location, force_create=True)
            dump_file_path_disk = self.media_agent_machine.join_path(self.dump_location, "dump_file_disk.csv")
            dump_file_path_cloud = self.media_agent_machine.join_path(self.dump_location, "dump_file_cloud.csv")
            dump_file_path_cloud_2 = self.media_agent_machine.join_path(self.dump_location, "dump_file_cloud_2.csv")
            ma_obj = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
            if self.media_agent_machine.os_info.lower() == 'unix':
                base_path = self.media_agent_machine.join_path(ma_obj.install_directory, "Base")
                command1 = f"(cd {base_path} ; ./sidb2 -dump Chunk -i {disk_store.store_id} -split 0 {dump_file_path_disk}"
                command2 = f"(cd {base_path} ; ./sidb2 -dump Chunk -i {cloud_store.store_id} -split 0 {dump_file_path_cloud}"
                command3 = f"(cd {base_path} ; ./sidb2 -dump Chunk -i {cloud_store_2.store_id} -split 0 {dump_file_path_cloud_2}"
            elif self.media_agent_machine.os_info.lower() == 'windows':
                base_path = '& "' + self.media_agent_machine.join_path(ma_obj.install_directory, "Base", "sidb2") + '"'
                command1 = f'{base_path} -dump Chunk -i {disk_store.store_id} -split 0 {dump_file_path_disk}'
                command2 = f'{base_path} -dump Chunk -i {cloud_store.store_id} -split 0 {dump_file_path_cloud}'
                command3 = f'{base_path} -dump Chunk -i {cloud_store_2.store_id} -split 0 {dump_file_path_cloud_2}'
            self.media_agent_machine.execute_command(command1)
            self.media_agent_machine.execute_command(command2)
            self.media_agent_machine.execute_command(command3)
            self.log.info("giving a 60 seconds gap for the dump files to be written to %s on MA", self.dump_location)
            time.sleep(60)

            self.log.info("Reading the dump files")
            chunk_table_file_disk = self.media_agent_machine.read_file(dump_file_path_disk)
            chunk_table_file_cloud = self.media_agent_machine.read_file(dump_file_path_cloud)
            chunk_table_file_cloud_2 = self.media_agent_machine.read_file(dump_file_path_cloud_2)
            self.log.info("Read the dumped file contents. Parsing it to fetch deleted records count")
            input_reader_disk = csv.reader(chunk_table_file_disk.split("\n"))
            input_reader_cloud = csv.reader(chunk_table_file_cloud.split("\n"))
            input_reader_cloud_2 = csv.reader(chunk_table_file_cloud_2.split("\n"))

            deleted_records_disk = 0
            deleted_records_cloud = 0
            deleted_records_cloud_2 = 0
            for rows in input_reader_disk:
                if input_reader_disk.line_num < 3 or rows == []:
                    continue
                deleted_records_disk += int(rows[8].strip())
            for rows in input_reader_cloud:
                if input_reader_cloud.line_num < 3 or rows == []:
                    continue
                deleted_records_cloud += int(rows[8].strip())
            for rows in input_reader_cloud_2:
                if input_reader_cloud_2.line_num < 3 or rows == []:
                    continue
                deleted_records_cloud_2 += int(rows[8].strip())
            self.log.info(
                "Delete Records: Disk DDB(%s) - [%s], Cloud DDB(%s) - [%s], Cloud DDB2(%s) - [%s]",
                disk_store.store_id, deleted_records_disk,
                cloud_store.store_id, deleted_records_cloud, cloud_store_2.store_id, deleted_records_cloud_2)
            if deleted_records_disk > 0 and deleted_records_cloud > 0 and deleted_records_cloud_2 > 0:
                self.log.info("Validation Passed. Chunk Tables are updated for all DDBs")
            else:
                raise Exception("Validation Failed. Chunk Tables are not updated for all DDBs")

            if self.media_agent_machine.os_info.lower() == 'unix':
                self.media_agent_machine.execute_command("date --set='-1 hours -15 minutes'")
                self.time_moved_unix = False
            elif self.media_agent_machine.os_info.lower() == 'windows':
                self.media_agent_machine.execute_command("set-date -adjust -01:15:00")
            self.log.info("time reverted back by 1:15:00 hrs on the media agent machine ")

            jobs_set4 = self.run_backups(size=0)
            self.log.info("*** Validating Primary Record count for 4th Full Backups:"
                          " new primary records should get created for Cloud store only ***")
            if not self.validate_primary_records(jobs_set4, expected=True):
                raise Exception("Primary records validation failed for new backup after Chunk table is updated")
            self.log.info("Primary records validation passed for new backup after Chunk table is updated")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED. Cleaning Up the Entities')
        else:
            self.log.warning('Test Case FAILED. Please check logs for debugging')

        if self.media_agent_machine.os_info.lower() == 'unix' and self.time_moved_unix:
            self.media_agent_machine.execute_command("date --set='-1 hours -15 minutes'")
        if self.media_agent_machine.os_info.lower() == 'windows':
            self.log.info("enabling the windows time service")
            self.media_agent_machine.execute_command("Set-Service -Name w32time -StartupType Automatic")
            self.media_agent_machine.execute_command("start-service w32time")
            self.log.info("windows time service enabled")
        self.cleanup()
