# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""This file contains classes named DedupeHelper, CloudLibrary and MMHelper which consists of
 methods required for MM testcase assistance like DB queries, log parsing, etc.

Class DedupeHelper:
    parse_log()                     --  parsing log files in search of a particular pattern

    change_path()                   --  modifies given path to network path

    get_primary_objects()           --  Gets primary objects on a SIDB

    get_secondary_objects()         --  Gets secondary objects on a SIDB

    get_primary_objects_sec()       --  Gets primary objects of a secondary copy

    get_secondary_objects_sec()     --  Gets secondary objects on secondary copy

    get_sidb_ids()                  --  get SIDB store and substore id

    get_network_transfer_bytes()    --  gets bytes transfered for a job

    submit_backup_memdb_recon()     --  Launches full backup, kills SIDB to initiate a
                                        full DDB Recon

    poll_ddb_reconstruction()       --  Polls CSDB for recon job

    get_reconstruction_type()	    --  returns if Delta recon or Regular recon or Full recon

    execute_sidb_command()          --  executes given sidb2 command and returns back the
                                        output and status

    get_ddb_partition_ma()          --  Returns dictionary with partition number as key and
                                        client object of DDB MA as value

    get_sidb_dump()                 --  Dumps DDB table and returns the content of the dump as
                                        a string

    get_ddb_recon_details()         --  gets non-memDB reconstruction job details

    is_ddb_online()                 --  Checks if DDB status is online or offline

    get_db_sidb_ids()           	-- get SIDB store and substore ids for DB agent

    get_vm_sidb_ids()           	-- get SIDB store and substore ids for VSA agent

    get_running_sidb_processes()    -- Find out SIDB2 proecesses running on given DDB MA and return details
                                       about Engine Id, Partition ID, Process ID, Job ID

    is_sidb_running()               -- Check if sidb process for given engine id and partition id (optional)
                                       is running on DDB MA

    wait_till_sidb_down()           -- Periodically checks for SIDB process to shut down within given timeout period
                                       and returns when either SIDB process goes down or when timeout expires.

    setup_dedupe_environment()      -- get testcase object and setup library,dedupe storage policy,
                                        backupset and subclient

    configure_dedupe_storage_policy()   -- creates a new dedupe storage policy if not exists

    configure_global_dedupe_storage_policy()    --  creates a new global dedupe storage policy if not exists

    configure_dedupe_secondary_copy()   -- creates Synchronous copy for the storage policy

    get_primary_recs_count()        -- get latest count of total primary records on the store

    get_zeroref_recs_count()        -- get latest count of total ZeroRef records on the store

    get_secondary_recs_count()      -- get latest count of total secondary records on the store

    run_dv2_job()                   -- run ddb verification on the specified storage policy copy

    set_mark_and_sweep_interval()   -- Set Mark and Sweep Interval time for a store using Qoperation ExecScript

    get_ddb_mapping_for_subclient() -- Get the DDB Store object for DDB associated to a subclient on given copy

    seal_ddb()                      -- Seals the deduplication database

    mark_substore_for_recovery()    -- Mark substore for recovery

    sidb_stats()                    --  Run sidb stats command and get the output.

    validate_pruning_phase()        --  Validate Phase 1/2/3 pruning is complete for a given sidb store

    configure_mm_tc_environment()   --  Create multi-partition storage pools, storage policies and subclients
                                        for setting up MM test case environment

    add_n_partitions_to_store()     -- Add provided number of partitions to given SIDB store

    update_ddb_settings()           -- Update DDB settings for a given storage policy copy


Class MMHelper:

    unset_object_lock()         -- unset the object lock on storage in CSDB

    set_bucket_lock()           -- set the right flag for bucket lock in CSDB

    update_mmpruneprocess()     -- set MMPruneProcessInterval value

    run_backup()                -- backup job that creates unique data

    get_drive_pool_id()         -- get drivepool id

    get_spare_pool_id()         -- get spare pool id

    get_copy_id()               -- get storage policy copy id

    get_mount_path_id()         -- get mountPath id from mountpath name

    get_device_controller_id()  -- get device controller id from mountpath id and media agent id

    get_device_id()             -- get the device id for the given mountpath id

    get_media_location()        -- get media location id

    get_device_path()           -- get device path from mountpath id

    get_device_access_type()     -- get the device access type for the given mountpath id and mediaagent name

    remove_content_subclient()  -- Deletes subclient data

    get_archive_file_size()     -- Gets sum of archive file size on a copy/for a job

    set_opt_lan()               -- Modifies Optimize for concurrent LAN backups option on the MA

    get_global_param_value()    -- gets param value from gxglobalparam table

    get_jobs_picked_for_aux()   -- gets number of jobs picked by an auxcopy job

    get_to_be_copied_jobs()     -- gets number of jobs in to-be-copied state for a copy

    move_job_start_time()       -- moves job start and end time to number of days behind

    get_ma_using_hostname()     -- returns the media agent object of the specified media agent hostname

    retire_media_agent()                 -- Retires the MA role of the media agent

    retire_client()             -- Uninstalls the CommVault Software, releases the license and deletes the client if it exists.

    execute_update_query()      -- executes update query on CSDB

    cleanup()                   -- deletes backupset, storage policy

    validate_copy_prune()       -- verifies if a copy exits or deleted

    validate_job_prune()        -- Validates if a job is aged by checking table entries

    validate_jmdatastats()      -- Validate if a job id exists in table jmdatastats

    validate_archfile()         -- Validate if archfile entry for job id is exists

    validate_archfilecopy()     -- validate if archfilecopy entry for job id exists

    validate_archchunkmapping() -- Validate if archchunkmapping entry for job id exists

    validate_job_retentionflag()-- Validate if extended retention flag is set for a job id

    setup_environment()         -- get testcase object and setup library, non dedupe storage
                                   policy, backupset and subclient

    configure_disk_library()    -- Create a new disk library if not exists

    configure_disk_mount_path() -- Adds a mount path [local/remote] to the disk library

    configure_air_gap_protect_pool() -- Adds air gap protect pool

    configure_storage_pool()    -- Adds a new dedupe or non-dedupe storage pool

    enable_worm()               -- Enable WORM on the storage policy

    get_copy_store_seal_frequency() -- Get the copy store seal frequency

    delete_storage_pool()       -- Deletes the storage pool if it exists

    delete_storage_policy()     -- Deletes the storage policy if it exists

    configure_cloud_library()   -- Adds a new Cloud Library to the Commcell

    configure_cloud_mount_path()-- Adds a mount path to the cloud library

    configure_storage_policy()  -- creates a new storage policy if not exists

    configure_backupset()       -- Creates a new backupset if not exits

    configure_subclient()       -- Gets or creates the subclient using the config parameters

    configure_secondary_copy()  -- Creates a new secondary copy if doesnt exist

    create_uncompressable_data() -- Creates unique uncompressable data

    execute_select_query()      -- Executes CSDB select query

    unload_drive()              -- Unloads the drive on the library given

    remove_autocopy_schedule()  -- Removes association with System Created Automatic Auxcopy schedule on the given copy

    ransomware_protection_status()   --  This function checks the state of ransomware protection

    ransomware_driver_loaded()  --  This function checks if the cvdlp driver is loaded or not
                                    by executing cmd line fltmc instances command

    uncheck_high_latency()      -- It will uncheck the high latency option for client side cache
                                   Prevent unintentional enabling of high latency setting when using
                                   client side cache.
                                   Useful while writing certain testcases.

    get_drive_pool()            -- Returns the DrivePool(s) of the tape library

    get_master_pool()           -- Returns the master pool(s) of the tape library

    update_mmconfig_param()     -- Update MM Config Parameter

    submit_data_aging_job()     -- submits and runs a data aging job and makes sure to wait if an
                                   existing data aging job is in progress.

    enable_global_encryption()  -- enable global encryption settings on Commcell

    disable_global_encryption() -- disable global encryption settings on Commcell

    getDeletedAFcount()         -- get the count for entries belonging to a particular store in mmdeletedAF

    execute_stored_proc()       -- execute stored proc and measure time taken by stored proc

    get_chunks_for_job()        --  Fetches the Details of Chunks Created by the Job

    get_bad_chunks()            --  Get chunks from archChunkDDBDrop which were marked bad

    generate_automation_path()    -- Generate the path for automatuon use

    wait_for_job_state()        --  Waits for the job to be in the given state

    wait_for_job_completion()   --  Waits for the job to be completed

    get_recall_wf_job()         --  Get the cloud recall workflow job id

    set_encryption()            --  This method is to set encryption using random Cipher and key length.

    get_mount_path_name()       --  returns unique mount path name on the library

    get_source_ma_id_for_auxcopy()  -- get the source media agent for the given aux copy job.

    restart_mm_service()        --  Restarts the Media Manager service

    add_storage_pool_using_existing_library() -- Adds a new storage pool to commcell using existing library

    edit_mountpath_properties() --  Edit the properties of the given mountpath on a library

    validate_trigger_status() --  validates whether the trigger is disabled or not on a table

    check_copy_association_to_AGP() -- check whether copy is associated to AGP (Air Gap Protect) or not

    can_disable_compliance_lock() -- method to check whether the copy is eligible to disable compliance lock or not

    disable_compliance_lock() --  method to unset compliance lock

    wait_for_online_status_air_gap_protect() -- Waits until Air Gap Protect storage is fully configured; i.e.; Status changes to 'Online'


CloudLibrary:
    __init__(libraryname, libraryinfo)             --  initialize the cloud library class
     instance for the commcell

    cleanup_entities(commcell, log, entity_config) --   static method to cleanup commcell entities.


Class PowerManagement:

    configure_cloud_mediaagent()	 -- Setup and configure cloud MediaAgent

    power_off_media_agents()         -- power-off a list of MediaAgents simultaneously

    power_on_media_agents()          -- power-on a list of MediaAgents simultaneously

    validate_powermgmtjobtovmmap_table () -- Validate the entry on MMPowerMgmtJobToVMMap table for the job and MediaAgent

    get_time_to_power_off()     --  This method fetches time to power-off from log

    date_time_diff()        --  Finds the difference between two dates in minutes or seconds

    verify_power_off_idle_time()        --  This method verifies the idle time for power managed MA.

"""

import os
import time
import re
import random
import zipfile, threading
from datetime import datetime

from cvpysdk.job import Job
from cvpysdk.client import Client
from cvpysdk.storage import MediaAgent
from cvpysdk.deduplication_engines import DeduplicationEngines, DeduplicationEngine, Store, SubStore
from cvpysdk.storage_pool import StoragePoolType
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils import logger, cvhelper
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import commonutils
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents import mediaagentconstants


class DedupeHelper(object):
    """ Base class for deduplication helper functions"""

    def __init__(self, test_case_obj):
        """Initializes BasicOperations object"""
        self.tcinputs = test_case_obj.tcinputs
        self.commcell = test_case_obj.commcell
        self.client = getattr(test_case_obj, '_client')
        self._log = logger.get_log()
        self.comm_untils = CommonUtils(self)
        self.commserver_name = self.commcell.commserv_name
        self.id = test_case_obj.id
        self.log_dir = test_case_obj.log_dir
        self.csdb = test_case_obj.csdb
        self.agent = getattr(test_case_obj, '_agent')
        self.backupset_name = None
        self.subclient_name = None
        self.storage_policy_name = None
        self.library_name = None
        self.client_machine = None
        self.storage_pool_name = None
        self.ddb_path = self.tcinputs.get("DedupeStorePath")
        if hasattr(test_case_obj, 'backupset_name'):
            self.backupset_name = test_case_obj.backupset_name
        if hasattr(test_case_obj, 'subclient_name'):
            self.subclient_name = test_case_obj.subclient_name
        if hasattr(test_case_obj, 'storage_policy_name'):
            self.storage_policy_name = test_case_obj.storage_policy_name
        if hasattr(test_case_obj, 'library_name'):
            self.library_name = test_case_obj.library_name
        if hasattr(test_case_obj, 'ddb_path') and self.ddb_path:
            self.ddb_path = test_case_obj.ddb_path
        if hasattr(test_case_obj, 'storage_pool_name'):
            self.storage_pool_name = test_case_obj.storage_pool_name
        if hasattr(test_case_obj, 'client_machine'):
            self.client_machine = test_case_obj.client_machine

        try:
            self.backupset = test_case_obj.backupset
        except Exception:
            self.backupset = None
        try:
            self.subclient = test_case_obj.subclient
        except Exception:
            self.subclient = None
        self.mmhelper = MMHelper(test_case_obj)
        self.option_selector = OptionsSelector(self.commcell)
        if hasattr(test_case_obj, 'MediaAgentName'):
            self.machine = Machine(str(self.tcinputs["MediaAgentName"]), self.commcell)

    def get_ddb_mapping_for_subclient(self, subc_id, sp_name, copy_name):
        """
        Get the DDB associated with given sublient id on a given copy ID

        Args:
            subc_id     (int)   -   subclient id
            sp_name     (str)   -   name of storage policy
            copy_name   (str)   -   name of the copy

        Return:
            DDB Store Object corresponding to DDB ID from ArchSubclientCopyDDBMap table for given subclient and
            copy id pair
        """
        dedup_engines = DeduplicationEngines(self.commcell)
        dedup_engine = dedup_engines.get(sp_name, copy_name)
        copyid = self.mmhelper.get_copy_id(sp_name, copy_name)
        query = "select sidbstoreid from archsubclientcopyddbmap where appid=%s and " \
                " copyid=%s" % (subc_id, copyid)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        engineid = int(self.csdb.fetch_one_row()[0])
        return dedup_engine.get(engineid)

    def is_ddb_flag_set(self, ddb_store_obj, flags_enum):
        """
        Check if DDB flag is set

        ddb_store_obj   (object)    : Store class object for the DDB whose flags need to be checked
        flags_enum      (str)       : Flag value to be checked in Flags column of IdxSIDBStore table. The valid
                                    strings can be found in DEDUPLICATION_STORE_FLAGS dictionary of
                                    mediaagentconstants.py
                                    Eg. To check if Resync flag is set :
                                    flags_enum = IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC

        Return:
            Boolean value based on whether flag is set or not
        """

        if ddb_store_obj.store_flags & mediaagentconstants.DEDUPLICATION_STORE_FLAGS[flags_enum] == \
                mediaagentconstants.DEDUPLICATION_STORE_FLAGS[flags_enum]:
            self._log.info("Flag %s is set", mediaagentconstants.DEDUPLICATION_STORE_FLAGS[flags_enum])
            return True
        else:
            self._log.info("Flag %s is not set", mediaagentconstants.DEDUPLICATION_STORE_FLAGS[flags_enum])
            return False

    def setup_dedupe_environment(self):
        """
                get testcase object and setup library, dedupe storage policy, backupset and subclient

                Returns:
                    (object)    -- object of disk library
                    (object)    -- object of storage policy
                    (object)    -- object of backupset
                    (object)    -- object of subclient
        """
        disk_library = self.mmhelper.configure_disk_library()
        storage_policy = self.configure_dedupe_storage_policy()
        backupset = self.mmhelper.configure_backupset()
        subclient = self.mmhelper.configure_subclient()
        return disk_library, storage_policy, backupset, subclient

    def configure_dedupe_storage_policy(self,
                                        storage_policy_name=None,
                                        library_name=None,
                                        ma_name=None,
                                        ddb_path=None,
                                        ddb_ma_name=None,
                                        storage_pool_name=None,
                                        is_dedup_storage_pool=None
                                        ):
        """
                creates a new dedupe storage policy if not exists
                Agrs:
                    storage_policy_name (str)   -- storage policy name to create

                    library_name (str)          -- library to use for creating storage policy

                    ma_name (str)               -- datapath MA name

                    ddb_path (str)              -- path to create DDB store

                    ddb_ma_name (str)           -- MA name to create DDB store


                    storage_pool_name (str)     -- Storage Pool name to use for creating storage policy
                                                   ** if storage pool name is given then library,
                                                      ma_name, ddb_path and ddb_ma_name are not required

                    is_dedup_storage_pool (bool)-- deduplication is enabled or not

                Return:
                    (object)    -- storage policy object
        """
        if storage_pool_name != None and is_dedup_storage_pool == True:
            if not self.commcell.storage_policies.has_policy(storage_policy_name):
                self._log.info("adding Dependent Storage policy...")
                self.commcell.storage_policies.add(storage_policy_name=storage_policy_name,
                                                   global_policy_name=storage_pool_name,
                                                   global_dedup_policy=is_dedup_storage_pool)
                self._log.info("Dependent Storage policy config done.")
            else:
                self._log.info("Storage policy exists!")
            storage_policy = self.commcell.storage_policies.get(storage_policy_name)
            return storage_policy
        # config storage policy
        if storage_policy_name is None:
            storage_policy_name = self.storage_policy_name
        if library_name is None:
            library_name = self.library_name

        if ma_name is None:
            if ddb_ma_name is not None:
                ma_name = ddb_ma_name
            else:
                ma_name = self.tcinputs.get("MediaAgentName")

        if ddb_ma_name is None:
            ddb_ma_name = self.tcinputs.get("DDBMediaAgentName", ma_name)

        if ddb_path is None:
            ddb_path = self.ddb_path

        ddb_path = ddb_path + self.option_selector.get_custom_str()
        ddbma_machine_object = self.option_selector.get_machine_object(ddb_ma_name)
        if not ddbma_machine_object.check_directory_exists(ddb_path):
            ddbma_machine_object.create_directory(ddb_path)
        self._log.info("check SP: %s", storage_policy_name)
        if not self.commcell.storage_policies.has_policy(storage_policy_name):
            self._log.info("adding Storage policy...")
            self.commcell.storage_policies.add(storage_policy_name, library_name, ma_name,
                                               ddb_path, dedup_media_agent=ddb_ma_name)
            self._log.info("Storage policy config done.")
        else:
            self._log.info("Storage policy exists!")
        storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        return storage_policy

    def configure_global_dedupe_storage_policy(self, global_storage_policy_name, library_name, media_agent_name,
                                               ddb_path, ddb_media_agent):
        """
            creates a new global dedupe storage policy if not exists
                Args:
                    global_storage_policy_name (str)   --   global storage policy name to create

                    library_name (str)          --  library to use for creating storage policy

                    media_agent_name (str)   --  media_agent to be assigned

                    ddb_path (str)              -- path to create DDB store

                    ddb_media_agent         (str)   --  media agent name on which deduplication store
                                                    is to be hosted

                Return:
                    (object)    -- storage policy object
        """

        self._log.info("Check for GDSP : %s", global_storage_policy_name)
        if not self.commcell.storage_policies.has_policy(global_storage_policy_name):
            ddbma_machine_obj = self.option_selector.get_machine_object(ddb_media_agent)
            if not ddbma_machine_obj.check_directory_exists(ddb_path):
                ddbma_machine_obj.create_directory(ddb_path)
            self._log.info("Adding a new GDSP: %s", global_storage_policy_name)
            gdsp = self.commcell.storage_policies.add_global_storage_policy(global_storage_policy_name, library_name,
                                                                            media_agent_name, ddb_path, ddb_media_agent)
            self._log.info("GDSP Configuration Done.")
            return gdsp
        else:
            self._log.info('GDSP already exists')
            return self.commcell.storage_policies.get(global_storage_policy_name)

    def configure_dedupe_secondary_copy(self, storage_policy, copy_name, library_name, media_agent_name, partition_path,
                                        ddb_media_agent, **kwargs):
        """Creates Synchronous copy for this storage policy

            Args:
                storage_policy          (object) --  instance of storage policy to add the copy to

                copy_name               (str)   --  copy name to create

                library_name            (str)   --  library name to be assigned

                media_agent_name        (str)   --  media_agent to be assigned

                partition_path          (str)   --  path where deduplication store is to be hosted

                ddb_media_agent         (str)   --  media agent name on which deduplication store
                                                    is to be hosted

            \*\*kwargs  (dict)  --  Optional arguments

                Available kwargs Options:

                dash_full               (bool)  --  enable DASH full on deduplication store (True/False)

                source_side_disk_cache  (bool)  -- enable source side disk cache (True/False)

                software_compression    (bool)  -- enable software compression (True/False)

            Return:
                    (object)    -- storage policy copy object
        """
        dash_full = kwargs.get('dash_full', None)
        source_side_disk_cache = kwargs.get('source_side_disk_cache', None)
        software_compression = kwargs.get('software_compression', None)
        self._log.info("Check Secondary Copy: %s", copy_name)
        if not storage_policy.has_copy(copy_name):
            ddbma_machine_obj = self.option_selector.get_machine_object(ddb_media_agent)
            if not ddbma_machine_obj.check_directory_exists(partition_path):
                ddbma_machine_obj.create_directory(partition_path)
            self._log.info("Adding a new synchronous secondary copy: %s", copy_name)
            storage_policy.create_dedupe_secondary_copy(copy_name, library_name, media_agent_name,
                                                        partition_path,
                                                        ddb_media_agent, dash_full,
                                                        source_side_disk_cache,
                                                        software_compression)
            self._log.info("Secondary Copy has created")
        else:
            self._log.info("Storage PolicyCopy Exists!")
        return storage_policy.get_copy(copy_name)

    def _retry_on_exception(self, func, max_retries=3, *args, **kwargs):
        """
        Retry a function on exception up to `max_retries` times.
        """
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)  # Execute the function
            except Exception as e:
                if attempt == max_retries:
                    raise e  # Raise the exception if all retries fail
                else:
                    self._log.warning("Attempt [%d/%d] for [%s] with args [%s] and kwargs [%s] failed: %s", attempt,
                                      max_retries, func.__name__, args, kwargs, e)

    def parse_log(self,
                  client,
                  log_file,
                  regex,
                  jobid=None,
                  escape_regex=True,
                  single_file=False,
                  only_first_match=False):
        """
        This function parses the log file in the specified location based on
        the given job id and pattern

        Args:
            client  (str)   --  MA/Client Name on which log is to be parsed

            log_file (str)  --  Name of log file to be parsed

            regex   (str)   --  Pattern to be searched for in the log file

            jobid   (str)   --  job id of the job within the pattern to be searched

            escape_regex (bool) -- Add escape characters in regular expression before actual comparison

            single_file (bool) -- to parse only the provided log file instead of all older logs

            only_first_match (bool) -- to parse only for the first match instead of all matches

        Returns:
           (tuple) --  Result of string searched on all log files of a file name

        """
        matched_strings = []
        matched_lines = []
        self.client_machine = Machine(client, self.commcell)
        log_path = self.client_machine.client_object.log_directory
        # refreshing the client object if the log path is none to prevent Invalid Path Exception
        for _ in range(3):
            if log_path is None:
                self.client_machine.client_object.refresh()
                log_path = self.client_machine.client_object.log_directory
            else:
                break
        else:
            if log_path is None:
                raise Exception("Unable to get the client log directory path")
        if escape_regex:
            self._log.info("Escaping regular expression as escape_regex is True")
            regex = re.escape(regex)
        self._log.info("Log path : {0}".format(str(log_path)))
        if not single_file:
            all_log_files = self.client_machine.get_files_in_path(log_path, recurse=False)
            self._log.info("Got files in path ")
            log_files = [x for x in all_log_files if os.path.splitext(log_file)[0].lower() in x.lower()]
        else:
            log_files = [self.client_machine.join_path(log_path, log_file)]

        if len(log_files) > 1:
            log_files.sort(reverse=True)
            log_files.insert(0, log_files.pop())
        self._log.info("List of log files to parse: %s", log_files)

        # get log file versions
        for file in log_files:
            # decompress the log file if it is compressed
            if os.path.splitext(file)[1].lower() in ['.zip', '.bz2']:
                if os.path.splitext(file)[1].lower() == '.zip':
                    log_dir = self.client_machine.join_path(self.client_machine.client_object.install_directory,
                                                            'Log Files')
                    base_dir = self.client_machine.join_path(self.client_machine.client_object.install_directory,
                                                             'Base')
                    command = '"%s%sunzip" -o "%s" -d "%s"' % (base_dir, self.client_machine.os_sep, file, log_dir)
                    self._log.info("Decompressing .zip file %s", file)
                else:
                    command = 'bzip2 -d %s' % file
                    self._log.info("Decompressing .bz2 file %s", file)

                try:
                    response = self._retry_on_exception(self.client_machine.client_object.execute_command,
                                                        3, command)
                except Exception as e:
                    self._log.error("Failed to decompress log file [%s] : %s", file, e)
                    raise Exception("Failed to decompress log file [%s] : %s" % (file, e))
                if response[0] == 0:
                    self._log.info('Successfully decompressed log file %s', file)
                    file = os.path.splitext(file)[0]
                else:
                    self._log.error("Failed to decompress log file [%s]", file)
                    raise Exception("Failed to decompress log file [%s]" % file)

            # read the log file
            try:
                self._log.info("Reading log file [%s]", file)
                lines = self._retry_on_exception(self.client_machine.read_file,
                                                 3, file).splitlines()
            except Exception as e:
                self._log.error("Failed to read decompress log file [%s] : %s", file, e)
                raise Exception("Failed to read decompress log file [%s] : %s" % (file, e))

            if not jobid and lines:
                self._log.info("Searching for [{0} in file {1}]".format(regex, file))
                for line in lines:
                    line = str(line)
                    regex_check = re.search(regex, line)
                    if regex_check:
                        matched_lines.append(line)
                        matched_strings.append(regex_check.group(0))
                        if only_first_match:
                            break
            elif lines:
                self._log.info("""Searching for string [{0}] for job [{1}] in file [{2}]
                               """.format(regex, jobid, file))
                for line in lines:
                    # required to change a byte stream to string
                    line = str(line)
                    jobid_check = re.search(" {0} ".format(str(jobid)), line)
                    if jobid_check:
                        regex_check = re.search(regex, line)
                        if regex_check:
                            matched_lines.append(line)
                            matched_strings.append(regex_check.group(0))
                            if only_first_match:
                                break
            if matched_lines:
                self._log.info(f"Found {len(matched_lines)} matching line(s)")
                return matched_lines, matched_strings
        else:
            self._log.error("Not found!")
            return None, None

    def change_path(self, file_path, machine_name):
        """
        change path to a UNC path

            Args:
                file_path (str)     --Path of file

                machine_name (str)  -- Name of mahine on which the file resides

            Returns:
                Network path of the file

        """
        drive = file_path[:1]
        path = file_path[3:]
        new_path = "\\\\{0}\\{1}$\\{2}".format(str(machine_name), str(drive), str(path))
        return new_path

    def get_primary_objects(self, jobid):
        """
        get primary records

            Args:
                jobid   (str)   --Job Id for which primary records to be checked

            Returns:
                Number of primary records added according to the CSDB

        """
        query = """select sum(primaryObjects) from archFileCopyDedup where archfileid in
                (select id from archFile where fileType =1 and jobId = {0} and flags&131072 = 0)
                """.format(jobid)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(cur[0]))
        return cur[0]

    def get_secondary_objects(self, jobid):
        """
        get secondary objects

            Args:
                jobid (str)     --Job id for which secondary records to be fetched

            Returns:
                Number of secondary records in the DDB for this particular job

        """
        query = """select sum(secondaryObjects) from archFileCopyDedup where archfileid in
                 (select id from archFile where fileType =1 and jobId = {0})""".format(jobid)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur[0])))
        return cur[0]

    def get_primary_objects_sec(self, bkup_jobid, copy_name):
        """
        get primary records for secondary copy

            Args:
                bkup_jobid  (str)   --Job id of the initial backup

                copy_name   (str)   --Name of copy on which records are to be fetched

            Returns:
                Number of primary records on given copy for given job

        """
        query = ("""
                 select sum(primaryObjects) from archFileCopyDedup where archfileid in (select id
                 from archFile where fileType =1 and jobId = {0}) and archcopyid
                 in (select id from archgroupcopy where name =  '{1}')
                 """.format(str(bkup_jobid), str(copy_name)))
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur[0])))
        return cur[0]

    def get_secondary_objects_sec(self, bkup_jobid, copy_name):
        """
        get secondary records for secondary copy

            Args:
                bkup_jobid  (str)   --Job id of the initial backup

                copy_name   (str)   --Name of copy on which records are to be fetched

            Returns:
                Number of secondary records on given copy for given job

        """
        query = ("""
                 select sum(secondaryObjects) from archFileCopyDedup where archfileid in (select id
                 from archFile where fileType =1 and jobId = {0}) and archcopyid in (select id
                 from archgroupcopy where name = '{1}')
                 """.format(str(bkup_jobid), str(copy_name)))
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur[0])))
        return cur[0]

    def get_sidb_ids(self, sp_id, copy_name, multi_part=False):
        """
        get SIDB store and substore ids

        Args:
            sp_id   (str)   --  Storage policy id

            copy_name   (str) -- Storage policy copy name

            multi_part  (bool) -- set true for multi partition stores

        Returns:
            Store ID associated with the storage policy

            SubStore IDs associated with the storage policy copy

        """
        self._log.info("Getting SIDB ids for copy : {0}".format(copy_name))
        query = """
                SELECT SS.SIDBStoreId, SS.SubStoreId
                FROM IdxSIDBSubStore SS
                INNER JOIN archgroupcopy AGC
                on SS.SIDBStoreId = AGC.SIDBStoreId
                and AGC.archGroupId = {0} and AGC.name = '{1}'
                """.format(str(sp_id), copy_name)
        self._log.info("QUERY : {0}".format(query))
        self.csdb.execute(query)
        if multi_part:
            cur = self.csdb.fetch_all_rows()
        else:
            cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur)))

        return cur

    def get_db_sidb_ids(self, copy_id):
        """
        get SIDB store and substore ids for DB agent

        Args:
            copy_id   (str)   --  Storage policy copy id

        Returns:
            Store ID associated with the storage policy

            SubStore ID associated with the storage policy copy

        """
        self._log.info("Getting SIDB ids for copy id : {0}".format(copy_id))
        query = """
                select S.SIDBStoreId, SS.SubStoreId
                from IdxSIDBStore S,IdxSIDBSubStore Ss ,archCopySIDBStore ACS
                where  ACS.SIDBStoreId = S.SIDBStoreId 
                and S.SIDBStoreId = SS.SIDBStoreId
                and SS.SealedTime = 0
                and S.AppTypeGroupId = 1002
                and ACS.CopyId = {0}
                """.format(copy_id)
        self._log.info("QUERY : {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur)))
        return cur

    def get_vm_sidb_ids(self, copy_id):
        """
        get SIDB store and substore ids for VSA agent

        Args:
            copy_id   (str)   --  Storage policy copy id

        Returns:
            Store ID associated with the storage policy

            SubStore ID associated with the storage policy copy

        """
        self._log.info("Getting SIDB ids for copy id : {0}".format(copy_id))
        query = """
                select S.SIDBStoreId, SS.SubStoreId
                from IdxSIDBStore S,IdxSIDBSubStore Ss ,archCopySIDBStore ACS
                where  ACS.SIDBStoreId = S.SIDBStoreId 
                and S.SIDBStoreId = SS.SIDBStoreId
                and SS.SealedTime = 0
                and S.AppTypeGroupId = 1003
                and ACS.CopyId = {0}
                """.format(copy_id)
        self._log.info("QUERY : {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur)))
        return cur

    def get_network_transfer_bytes(self, jobid):
        """
        gets bytes transfered for a job

        Args:
            jobid (str) -- job ID

        Returns:
            network transferred bytes for a jobid

        """
        query = """select nwTransBytes/1024/1024 from JMBkpStats where jobId = {0}
                """.format(str(jobid))
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(str(cur[0])))
        return cur[0]

    def submit_backup_memdb_recon(self,
                                  subclient_object,
                                  sp_name,
                                  copy_name,
                                  time_out=5):
        """Launches full backup, kills SIDB to initiate a full DDB Recon

        Args:
            subclient_object (object)   -- subclient instance

            sp_name (str)               -- storage policy name

            copy_name (str)             -- storage policy copy name

            time_out (int)              -- Time out period to kill SIDB process
                Default : 5

        Returns:
            backup job ID

            reconstruction job ID

        """
        # get MA log location
        log_file = "SIDBEngine.log"
        bkp_job = subclient_object.backup("FULL")
        self._log.info("Backup job for delta recon: {0}".format(str(bkp_job.job_id)))
        if bkp_job:
            # parse log to find string: "Requested by Job-Id "+str(backupJobId)
            count = 0
            (matched_line, matched_string) = self.parse_log(self.tcinputs['MediaAgentName'],
                                                            log_file,
                                                            """Requested by Job-Id {0}""".format(
                                                                str(bkp_job.job_id)))
            while not matched_string:
                time.sleep(2)
                count += 1
                (matched_line, matched_string) = self.parse_log(
                    self.tcinputs['MediaAgentName'], log_file,
                    """Requested by Job-Id {0}""".format(str(bkp_job.job_id)))
                if count == 300:
                    self._log.error("SIDB2 process did not start in time")
                    return 0
            self._log.info("Going to kill SIDB2 prococess in {0} secs".format(str(time_out)))
            time.sleep(time_out)
            if self.machine.os_info == 'UNIX':
                kill_sidb_cmd = "kill -9 $(ps -e | grep 'sidb2' | awk '{print $1}')"
                exit, response, error = self.machine.client_object.execute_command(kill_sidb_cmd)
                if exit == 0:
                    self._log.info("SIDB Killed Successfully")
                else:
                    self._log.info("SIDB not killed")
            else:

                cmd_to_kill_sidb = """taskkill /F /IM SIDB2.exe /T /S {0} /U {1} /P {2}
                                   """.format(str(self.tcinputs["MediaAgentHostName"]),
                                              str(self.tcinputs["MediaAgentUsername"]),
                                              str(self.tcinputs["MediaAgentPassword"]))
                output = self.machine.execute_command(cmd_to_kill_sidb)
                if output._exit_code:
                    self._log.error("Failed to kill SIDB2 process")
                    raise Exception(
                        "Failed to kill SIDB2 process"
                    )
                else:
                    self._log.info("SIDB2 process killed")
        try:
            time.sleep(30)
            self._log.info("Attempting to resume backup job")
            bkp_job.resume()
        except Exception:
            pass

        recon_job = self.poll_ddb_reconstruction(sp_name, copy_name)

        try:
            time.sleep(30)
            self._log.info("Attempting to resume backup job")
            bkp_job.resume()
        except Exception:
            pass

        if not bkp_job.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup with error:{0}".format(bkp_job.delay_reason)
            )
        self._log.info("Backup job completed.")
        return bkp_job, recon_job

    def poll_ddb_reconstruction(self, sp_name, copy_name, no_wait=False):
        """
        Polls whether DDB reconstruction jobs started and if started waits for
        completion and reports the status.

        Args:
            sp_name (str)   -- storage policy name
            copy_name (str) -- storage policy copy name
            no_wait (boolean)   -- option to wait for recon job to complete

        Returns:
            Reconstruction job ID

        """
        count = 0
        interval = 0
        self._log.info("Poll DDB Recon...")
        query1 = "select id from archGroup where name = '{0}'".format(str(sp_name))
        self.csdb.execute(query1)
        cur = self.csdb.fetch_one_row()
        sp_id = cur[0]

        copyId = self.mmhelper.get_copy_id(str(sp_name), str(copy_name))
        storeId = self.get_sidb_ids(str(sp_id), str(copy_name))[0]

        self._log.info("Check if given copy is a GDSP dependent copy")

        query4 = """SELECT dedupeFlags&134217728    
                    FROM archGroupCopy
                    WHERE id = {0}""".format(str(copyId))
        self.csdb.execute(query4)
        # copy_id = copyId
        dedFlag = self.csdb.fetch_one_row()[0]
        if dedFlag == '134217728':
            self._log.info("Detected as a GDSP dependent copy")
            query5 = """
                    SELECT id
                    FROM archGroupCopy
                    WHERE SIDBStoreId = {0} AND dedupeFlags&268435456 = 268435456
                    """.format(str(storeId))
            self.csdb.execute(query5)
            copy_id = self.csdb.fetch_one_row()[0]
        else:
            copy_id = copyId

        while int(count) <= 0 and interval < 1800:
            time.sleep(10)
            interval = interval + 10
            _query = """select count(*) from JMAdminJobInfoTable where opType=80 and
                      archGrpCopyID = {0}""".format(str(copy_id))
            self._log.info("QUERY: {0}".format(_query))
            self.csdb.execute(_query)
            cur = self.csdb.fetch_one_row()
            count = cur[0]
            self._log.info("POLL: DDB reconstruction job: {0}".format(str(count)))
        if int(count) == 1:
            _query = """select jobId from JMAdminJobInfoTable where opType=80 and
                                  archGrpCopyID = {0}""".format(str(copy_id))
            self._log.info("QUERY: {0}".format(_query))
            self.csdb.execute(_query)
            cur = self.csdb.fetch_one_row()
            self._log.info("Recon Job: {0}".format(str(cur[0])))
            job_id = cur[0]

            recon_job = Job(self.commcell, job_id)
            if no_wait == False:
                if not recon_job.wait_for_completion():
                    raise Exception(
                        "Failed to run delta recon: {0}".format(recon_job.delay_reason)
                    )
                self._log.info("Recon job completed.")
            return recon_job
        raise Exception(
            "Reconstruction Job does not start in the 10 minutes wait time"
        )

    def get_reconstruction_type(self, recon_job_id):
        """
        returns if Delta recon or Regular recon or Full recon

        Args:
            recon_job_id (int/str)    -- reconstruction job ID

        Returns:
            Type of reconstruction job

        """
        recon_type = {
            1: 'Delta Reconstruction',
            2: 'Regular Reconstruction',
            4: 'Full Reconstruction'}
        _query = ("""
                  select flags
                  from IdxSIDBRecoveryHistory
                  where AdminJobId = {0}"""
                  .format(str(recon_job_id)))
        self._log.info("QUERY: {0}".format(_query))
        self.csdb.execute(_query)
        cur = self.csdb.fetch_one_row()
        recon_flag = int(cur[0])
        if recon_flag:
            if recon_flag == 1:
                self._log.info("Recon type: Delta Reconstruction")
                return recon_type[1]
            if recon_flag == 2:
                self._log.info("Recon type: Regular Reconstruction")
                return recon_type[2]
            if recon_flag == 4:
                self._log.info("Recon type: Full Reconstruction")
                return recon_type[4]
            raise Exception(
                "recon job type not found"
            )
        raise Exception(
            "no results returned - getReconstructionType"
        )

    def execute_sidb_command(self, operation, engineid, groupnumber, ddbmaobject):
        """Execute sidb2 command like compact or reindex to get output

        Args:
            operation (str)     -- sidb2 command option like compact or reindx or validate

            engineid (int)      -- sidbstore id

            groupnumber (int)   -- sidb partition number ( eg. single partition
                                    ddb has partition0 where as double partition ddb has
                                    partition0 and partition1)

            ddbmaobject (Client or String) -- Client object for DDB MA or Client Name

            instance (String)   --  Simpana instance
                                    Default : Instance001
        Returns:
            Output list - [returnstatus, output]
        """

        if isinstance(ddbmaobject, Client):
            ddbma_clientobj = ddbmaobject
        elif isinstance(ddbmaobject, str):
            ddbma_clientobj = self.commcell.clients.get(ddbmaobject)

        os_sep = '/'
        if ddbma_clientobj.os_info.lower().count('windows') > 0:
            os_sep = "\\"

        basedir = "{0}{1}Base{1}".format(ddbma_clientobj.install_directory, os_sep)
        sidb2cmd = "\"{0}sidb2\"".format(basedir)
        command = ""
        # If WIN MA, enclose in double quotes
        if ddbma_clientobj.os_info.lower().count('windows') > 0:
            command = "{0} -{5} -in {1} -cn {2} -i {3} -split {4}".format(
                sidb2cmd, ddbma_clientobj.instance, ddbma_clientobj.client_hostname,
                engineid, groupnumber, operation)
        if ddbma_clientobj.os_info.lower().count('linux') > 0:
            # If LINUX MA, use stdbuf -o0
            command = "stdbuf -o0 {0} -{5} -in {1} -cn {2} \
                        -i {3} -split {4}".format(sidb2cmd, ddbma_clientobj.instance,
                                                  ddbma_clientobj.client_hostname, engineid,
                                                  groupnumber, operation)

        self._log.info(command)
        output = ddbma_clientobj.execute_command(command)
        return output

    def get_ddb_partition_ma(self, sidbstoreid):
        """
        Return a dictionary having mapping of group number to ddb ma
        Args:
         sidbstoreid: sidb store id

        Return:
            Dictionary containing group number ==> DDB MA client object
        """
        query = """select idxsidbsubstore.GroupNumber,APP_Client.name from
        idxsidbsubstore inner join APP_Client
        on idxsidbsubstore.ClientId = APP_Client.id
        where sidbstoreid = {0}
        order by IdxSIDBSubStore.GroupNumber""".format(sidbstoreid)

        self._log.info("Firing query to find DDB MAs for given SIDB store ==> {0}".format(query))
        self.csdb.execute(query)

        ddbmalist = self.csdb.fetch_all_rows()
        ddbma_partition_dict = {}
        for ddbma in ddbmalist:
            self._log.info("Creating client object for DDB MA ==> {0}".format(ddbma[1]))
            ddbma_partition_dict[ddbma[0]] = self.commcell.clients.get(ddbma[1])
        return ddbma_partition_dict

    def get_sidb_dump(self, client_name, type, store_id, dump_path, split=0):
        """Dumps the SIDB and returns the table as string

        Args:
                client_name --  (str)   --  name of the client on which the ddb is located

                type        --  (str)   --  type of table
                                            (Primary/Secondary)

                store_id    --  (str)   -- DDB Store ID

                dump_path   --  (str)   --  Path where the sidb can be dumped

                split       --  (int)   --  Split number of DDB

        Returns:
                file content of the dump as a string

        """
        machine_obj = Machine(client_name, self.commcell)
        if machine_obj.os_info == 'WINDOWS':
            command = "& '{0}{1}Base{1}SIDB2.exe' -dump {2} -i {3} -split {4} {5}".format(
                machine_obj.client_object.install_directory, machine_obj.os_sep, type, store_id,
                split,
                dump_path)
            output = machine_obj.execute_command(command)
        elif machine_obj.os_info == 'UNIX':
            command = "(cd {0}{1}Base ; ./sidb2 -dump {2} -i {3} -split {4} {5})".format(
                machine_obj.client_object.install_directory, machine_obj.os_sep, type, store_id,
                split,
                dump_path)
            output = machine_obj.client_object.execute_command(command)

        time.sleep(60)

        dump = machine_obj.read_file(dump_path)
        return dump

    def get_ddb_recon_details(self, sp_id, wait_for_complete=True):
        """gets non-memDB reconstruction job details
        Args:
           sp_id                --  (str)   --  Storage policy ID

           wait_for_complete    --  (bool)  -- wait for job to complete
           Default : True

        Returns:
            Reconstruction job id

        """
        query = """select jobid 
                from jmadminjobinfotable 
                where optype = 80 
                and archGrpID = {0}
                """.format(sp_id)
        self.csdb.execute(query)
        recon_job_id = self.csdb.fetch_all_rows()[0][0]
        self._log.info("Started recon job : {0}".format(str(recon_job_id)))
        recon_job = self.commcell.job_controller.get(recon_job_id)
        if wait_for_complete:
            time.sleep(120)
            self._log.info("waiting for recon job to complete")
            if not recon_job.wait_for_completion():
                raise Exception(
                    "Failed to run {0}  with error: {1}".format("recon job", recon_job.delay_reason)
                )
            self._log.info("Recon job completed.")
        return recon_job_id

    def is_ddb_online(self, store_id, sub_store_id):
        """Checks if DDB status is online or offline
        Args:
           store_id         --  (str)   --  deduplication store id

           sub_store_id     --  (str)   --  deduplication substore id

        Returns:
            (int)   --  deduplication store status (0 - online, 1 - offline)

        """
        self._log.info("checking if DDB online")
        query = """SELECT status
                          FROM idxSidbSubStore
                          WHERE SIDBStoreId =  {0}
                          AND SubStoreId = {1}
                          """.format(store_id, sub_store_id)
        db_response = self.mmhelper.execute_select_query(query)
        return int(db_response[0][0])

    def get_running_sidb_processes(self, ddbma_object):
        """
        Find out SIDB2 proecesses running on given DDB MA and return details about each
        Engine ID
        Partition ID ( Group Number )
        Process ID
        Job ID

        Args:
            ddbmaobject     --  (client/str)    -- Client object or Client Name for DDB MA

        Returns:
            Output dictionary - {sidb2engineid:(groupnumber,pid,jobid),sidb2engineid:(groupnumber,pid, jobid)..}
        """
        if isinstance(ddbma_object, Client):
            ddbma_clientobj = ddbma_object
        elif isinstance(ddbma_object, str):
            ddbma_clientobj = self.commcell.clients.get(ddbma_object)
        is_windows = False
        # If its a windows machine, make a powershell command else a linux cli
        if ddbma_clientobj.os_info.lower().count('windows') > 0:
            command = "powershell.exe -command \"{0} {1}|{2}\"".format(
                "Get-WmiObject Win32_Process -Filter", "\\\"name = 'SIDB2.EXE'\\\"",
                " format-table -autosize ProcessId, CommandLine | out-string -width 200")
            is_windows = True
        else:
            command = "ps -eo pid,command | grep sidb2 | grep -v grep"

        self._log.info(command)
        output = ddbma_clientobj.execute_command(command)
        self._log.info(output[1])

        engine_partition_map = {}

        if output[0] != 0 or output[1].lower().count('sidb2') == 0:
            self._log.error("Failed to find any SIDB2 process")
            # return empty dictionary
            return engine_partition_map
        # output from windows & linux is in this format respectively, start parsing it
        """
        ProcessId CommandLine                                                                                                                
        --------- -----------                                                                                                                
        12164 "C:\Program Files\Commvault\ContentStore\Base\SIDB2.exe" -j 1714825 -i 808 -c 615 -in Instance001 
        -cn sbhidesp13cs -group 0
        14252 "C:\Program Files\Commvault\ContentStore\Base\SIDB2.exe" -j 1714829 -i 856 -c 722 -in Instance001
         -cn sbhidesp13cs -group 0

        [root@sbhidesp13lima1 /]# ps -eo pid,command | grep sidb2 | grep -v grep
        15348 /opt/commvault/Base/sidb2 -j 1714828 -i 7 -c 9 -in Instance001 -cn sbhidesp13lima1 -group 0
        15350 /opt/commvault/Base/sidb2 -j 1714828 -i 7 -c 9 -in Instance001 -cn sbhidesp13lima1 -group 1

        """

        # Create a datastructure which will be a dictionary of following type
        # key = engineid [as it will be unique ]
        # value = list of (group number, pid) tuples[ same engine can have multiple partitions running ]
        engine_regex = re.compile('-i \d+')
        groupid_regex = re.compile('-group \d')
        jobid_regex = re.compile('-j \d+')
        if is_windows is True:
            output_lines = output[1].split('\r\n')
        else:
            output_lines = output[1].split('\n')

            # start building dictionary from output
        for line in output_lines:
            line = line.strip()
            if line == '' or line.count('ProcessId') > 0 or line.count('CommandLine') > 0 or line.count('-----') > 0:
                # skip blank lines
                continue
            else:
                # extract process ID and command line
                pid = line.split()[0].strip()
                engine_id = engine_regex.findall(line)[0].split()[1]
                group_id = groupid_regex.findall(line)[0].split()[1]
                job_id = jobid_regex.findall(line)[0].split()[1]
                groupid_pid_tuple = (int(group_id), int(pid), int(job_id))
                if engine_id in engine_partition_map:
                    self._log.info("Appending groupid->partition->jobid {0} to engine id {1} ".format(
                        groupid_pid_tuple, engine_id))
                    engine_partition_map[engine_id].append(groupid_pid_tuple)
                else:
                    engine_partition_map[engine_id] = [groupid_pid_tuple]
                    self._log.info("Adding new engine id - partition pair " \
                                   "to map ==> {0} - {1}".format(engine_id, groupid_pid_tuple))

        return engine_partition_map

    def is_sidb_running(self, engine_id, ddbma_object, partition_number=-1):
        """
        Check if sidb process for given engine id and partition id (optional) is running on DDB MA

        Args:
            engine_id           --  (int)           --  SIDB Store ID
            ddbma_object        --  (client/str)    --  Client object or Client name for DDB MA
            partition_number    --  (int)           --  Group number (0,1 etc.) [ Optional ]
                                                        Default : Skip checking Partition Number and report
                                                        if SIDB for given engine ID is active  on the DDB MA

        Returns:
            List of (groupid,pid,jobid) tuples if SIDB process is running , empty list otherwise
        """
        self._log.info("Checking if sidb process for engine : {0} for partition :{1} is running" \
                       " on DDB MA {2}".format(engine_id, partition_number, ddbma_object.client_name))

        ddb_map = self.get_running_sidb_processes(ddbma_object)
        # If ddb_map is empty, no sidb process is running on MA
        if ddb_map == {}:
            return []
        else:
            # Check if key with given engine id exists
            try:
                group_pid_tuple_list = ddb_map[engine_id]
                self._log.info("Process id corresponding to engine id : {0} ==> {1}".format(engine_id,
                                                                                            group_pid_tuple_list))
                if (partition_number == -1):
                    # Immediately return True as user has not asked to validate a specific group number
                    return group_pid_tuple_list
                else:
                    # Loop over tuples list to see if user provided group number is present
                    for item in group_pid_tuple_list:
                        if item[0] != int(partition_number):
                            continue
                        else:
                            self._log.info("Found partition {0} running with pid {1}".format(partition_number,
                                                                                             item[1]))
                            return [item]

                    return []
            except:
                self._log.info("No process corresponding to engine id : {0} found".format(engine_id))
                return []

    def wait_till_sidb_down(self, engine_id, ddbma_object, partition_number=-1, timeout=600):
        """
        Periodically checks for SIDB process to shut down within given timeout period and returns when
        either SIDB process goes down or when timeout expires.

        Periodicity with which SIDB process status gets checked is 30 seconds.

        Args:
            engine_id                   --  (str)           --  SIDB Store ID
            ddbma_object                --  (client/str)    --  Client object or Client name for DDB MA
            partition_number            --  (int)           --  Group number (0,1 etc.) [ Optional ]
                                                                Default : Skip checking Partition Number and report
                                                                if SIDB for given engine ID is active  on the DDB MA
            timeout                     --  (int)           --  Maximum wait time in seconds [ Optional ]
                                                                Default : 600 seconds

        Returns:
            (Boolean) True if SIDB process stops running , False if it keeps running even after timeout
        """
        time_step = 30
        time_elapsed = 0
        while time_elapsed < timeout:
            is_running = self.is_sidb_running(engine_id, ddbma_object, partition_number)
            if is_running != []:
                self._log.info("SIDB Process still running ==> {0}".format(is_running))
                time.sleep(time_step)
                time_elapsed = time_elapsed + time_step
            else:
                self._log.info("SIDB Process doesn't seem to be running ==> {0}".format(is_running))
                return True

        # As we are here, it means we spent entire timeout period in waiting for SIDB to go down
        # Return False
        self._log.info("SIDB Process did not go down within given timeout period")
        return False

    def get_primary_recs_count(self, store_id, db_password=None, db_user=None):
        """
        get latest count of total primary records on the store
        Args:
            store_id (int): SIDB store ID or Engine ID to get primary count
            db_password (str): CSDB password to use to run query to get primary count
            db_user (str):  CSDB username to login

        Returns:
            (int) total primary records count on the store id
        """
        query = """with x as (
                select row_number() over (partition by substoreid order by modifiedtime desc) as y,*
                from idxsidbusagehistory where historytype = 0)
                select sum(x.primaryentries)
                from x where y = 1
                    and x.sidbstoreid = {0}
                group by x.sidbstoreid""".format(store_id)
        self._log.info("QUERY: {0}".format(query))
        result = self.mmhelper.execute_update_query(query, db_password=db_password, db_user=db_user)
        self._log.info("RESULT: {0}".format(result.rows[0][0]))
        return result.rows[0][0]

    def get_zeroref_recs_count(self, store_id, db_password=None, db_user=None):
        """
        get latest count of total primary records on the store
        Args:
            store_id (int): SIDB store ID or Engine ID to get zero ref count
            db_password (str): CSDB password to use to run query to get zero ref count
            db_user (str):  CSDB username to login

        Returns:
            (int) total primary records count on the store id
        """
        query = """with x as (
                select row_number() over (partition by substoreid order by modifiedtime desc) as y,*
                from idxsidbusagehistory where historytype = 0)
                select sum(x.Zerorefcount)
                from x where y = 1
                    and x.sidbstoreid = {0}
                group by x.sidbstoreid""".format(store_id)
        self._log.info("QUERY: {0}".format(query))
        result = self.mmhelper.execute_update_query(query, db_password=db_password, db_user=db_user)
        self._log.info("RESULT: {0}".format(result.rows[0][0]))
        return result.rows[0][0]

    def get_secondary_recs_count(self, store_id, db_password=None, db_user=None):
        """
        get latest count of total secondary records on the store
        Args:
            store_id (int): SIDB store ID or Engine ID to get secondary count
            db_password (str): CSDB password to use to run query to get secondary count
            db_user (str):  CSDB username to login

        Returns:
            (int) total secondary records count on the store id
        """
        query = """with x as (
                select row_number() over (partition by substoreid order by modifiedtime desc) as y,*
                from idxsidbusagehistory where historytype = 0)
                select sum(x.secondaryentries)
                from x where y = 1
                    and x.sidbstoreid = {0}
                group by x.sidbstoreid""".format(store_id)
        self._log.info("QUERY: {0}".format(query))
        result = self.mmhelper.execute_update_query(query, db_password=db_password, db_user=db_user)
        self._log.info("RESULT: {0}".format(result.rows[0][0]))
        return result.rows[0][0]

    def run_dv2_job(self, store, dv2_type='incremental', option='quick'):
        """
        Runs DV2 job with type and option selected and waits for job to complete

        Args:
            store (object) - object of the store to run DV2 job on

            dv2_type (str) - specify type either full or incremental

            option (str) - specify option, either quick or complete

        Returns:
             (object) - completed DV2 job object
        """

        self._log.info("running [%s] [%s] DV2 job on store [%s]...", dv2_type, option, store.store_id)
        if dv2_type == 'incremental' and option == 'quick':
            job = store.run_ddb_verification()
        elif dv2_type == 'incremental' and option == 'complete':
            job = store.run_ddb_verification(quick_verification=False)
        elif dv2_type == 'full' and option == 'quick':
            job = store.run_ddb_verification(incremental_verification=False)
        else:
            job = store.run_ddb_verification(incremental_verification=False, quick_verification=False)
        self._log.info("DV2 job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self._log.info("DV2 job completed.")
        return job

    def set_mark_and_sweep_interval(self, sidb_store_id, interval_in_hours):
        """
        Sets Mark and Sweep Interval time for a store using Qoperation ExecScript

        Args:
            sidb_store_id       (int)   -   SIDB engine ID
            interval_in_hours   (int)   -   Mark & Sweep Interval in Hours

        """
        command = "-sn SetDDBMarkAndSweepInterval -si SET -si %s -si %s" % (sidb_store_id, interval_in_hours)
        self._log.info("Executing Script - %s", command)
        return self.commcell._qoperation_execscript(command)

    def get_ddb_subc_association(self, subc_id, sp_copy_id):
        """
        Get the DDB associated with given sublient id on a given copy ID

        Args:
            subc_id    (int)   -   subclient id
            sp_copy_id (int)   -   copy id

        Return:
            Integer DDB ID from ArchSubclientCopyDDBMap table for given subclient and copy id pair
        """
        query = "select sidbstoreid from archsubclientcopyddbmap where appid=%s and " \
                " copyid=%s" % (subc_id, sp_copy_id)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        engineid = int(self.csdb.fetch_one_row()[0])
        return engineid

    def seal_ddb(self, storage_policy_name, copy_name, store_id):
        """
        Seals the deduplication database
        Args:
            storage_policy_name (str)   - storage policy name in commcell

            copy_name (str)             - copy name under storage policy

            store_id (int)              - deduplication store id in commcell
        """
        store = Store(self.commcell, storage_policy_name, copy_name, store_id)
        store.seal_deduplication_database()
        self._log.info("Sealed DDB - %s " % store_id)

    def mark_substore_for_recovery(self, storage_policy_name, copy_name, store_id, substore_id_list=None):
        """
        Mark substore for recovery
        Args:
            storage_policy_name (str)   - storage policy name in commcell

            copy_name (str)             - copy name under storage policy

            store_id (int)              - deduplication store id in commcell

            substore_id_list(list)           - list of substore id under deduplication store
        """

        # if substore_id_list is None then mark for recovery on all the substores in the given store
        if not substore_id_list:
            store = Store(self.commcell, storage_policy_name, copy_name, store_id)
            substore_list = store.all_substores
            for substore in substore_list:
                substore_obj = SubStore(self.commcell, storage_policy_name, copy_name, store_id, substore[0])
                substore_obj.mark_for_recovery()
                self._log.info("Marked substore %s for recovery " % substore[0])
        else:
            for substore_id in substore_id_list:
                substore_obj = SubStore(self.commcell, storage_policy_name, copy_name, store_id, substore_id)
                substore_obj.mark_for_recovery()
                self._log.info("Marked substore %s for recovery " % substore_id)

    def sidb_stats(self, ddbma_client, engine_id, split_number):
        """
        Run sidb stats command and get the output.
        Please make sure that SIDB2 process is not running before using this method.

        Args:
             ddbma_client (Object)      :   Client object for DDB MA
             engineid (int)             :   SIDB Engine ID
             split_number(int)          :   Group number starting eg. 0, 1
        """
        ddbma_machine = Machine(ddbma_client.client_name, self.commcell)
        command = ""
        # If WIN MA, enclose in double quotes
        output_file = f"\"{ddbma_client.job_results_directory}{ddbma_machine.os_sep}sidbstats_{engine_id}_{split_number}.csv\""

        if ddbma_machine.os_info == 'WINDOWS':
            sidb2_exe = f"{ddbma_client.install_directory}{ddbma_machine.os_sep}Base{ddbma_machine.os_sep}SIDB2.exe"
            command = f"& '{sidb2_exe}' -dump stats -i {engine_id} -split {split_number} {output_file}"
            self._log.info("Command for dumping: %s", command)
            ddbma_machine.execute_command(command)
            output_file = output_file.replace('"', '')
            output = ddbma_machine.read_file(output_file)

        if ddbma_machine.os_info == 'UNIX':
            # If LINUX MA, use stdbuf -o0
            sidb2_exe = f"{ddbma_client.install_directory}{ddbma_machine.os_sep}Base{ddbma_machine.os_sep}sidb2"
            command = f"stdbuf -o0 {sidb2_exe} -dump stats -i {engine_id} -split {split_number} {output_file}"

            self._log.info(command)
            ddbma_machine.execute_command(command)
            # Open the output file
            output_file = output_file.replace('"', '')
            output = ddbma_machine.read_file(output_file)

        self._log.info("Deleting the sidb2 stats output file")
        ddbma_machine.delete_file((output_file))
        return output

    def validate_pruning_phase(self, sidb_id, ma_name, phase=3):
        """
        Validate Phase 1/2/3 pruning is complete for a given sidb store

        Args:
            sidb_id (int)       --      sidb store id for which phase 3 pruning needs to be verified
            ma_name (str)       --      Datamover MA on which pruning needs to be checked
            phase   (int)       --      pruning phase that needs to be verified
        Returns:
            matched_lines - None if no match found or list of matched lines otherwise
        """
        self._log.info(f"Validating logs to confirm Phase {phase} pruning has occurred")
        if phase == 3:
            statement = f"{sidb_id}-{phase}.* Finalizing SI entries in chunk"
        if phase == 2:
            statement = f"{sidb_id}-{phase}.* Pruned AfId .* completely"
        (matched_lines, matched_string) = self.parse_log(ma_name, "SIDBPrune.log", regex=statement, escape_regex=False)
        if matched_lines != None:
            self._log.info(f"Found at least 1 log line with phase {phase} pruning")
        else:
            self._log.error("Pruning is not complete")

        return matched_lines

    def configure_mm_tc_environment(self, ddb_ma_machine,
                                    data_mover_ma,
                                    mount_path,
                                    dedup_store_path,
                                    num_partitions,
                                    **kwargs):
        """
        Create multi-partition storage pools, storage policies and subclients

        Args:
            ddb_ma_machine (object) -- DDB MA machine object
            data_mover_ma   (str)   -- Data mover MA name
            mount_path      (str)   -- Path on MA where disk will be mounted
            dedup_store_path (str)  -- DDB path on DDB MA
            num_partitions  (int)   -- number of DDB partitions on storage pool

        **kwargs -- Optional arguments, if not provided uses default values
            num_policies    (int)   -- number of storage policies to create; default = 1
            subclients_per_policy (int) -- number of subclients associated to each storage policy; default =1
            same_path       (bool)  -- If true, DDB partitions are created on same path else unique
                                       directories are created for each path; default = True

        Returns:
            (object)            -- storage pool object
            [list(objects)]     -- list of storage policy objects
            [list]     -- list of content paths
            [list(objects)]     -- list of subclient objects
        """
        num_policies = kwargs.get('num_policies', 1)
        subclients_per_policy = kwargs.get('subclients_per_policy', 1)
        same_path = kwargs.get('same_path', True)
        self._log.info(f"Creating Storage Pool with [{num_partitions}] partitions")
        self._log.info("Configuring Storage Pool ==> %s", self.storage_pool_name)

        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            storage_pool = self.commcell.storage_pools.add(
                storage_pool_name=self.storage_pool_name,
                mountpath=mount_path,
                media_agent=data_mover_ma,
                dedup_path=dedup_store_path if same_path else ddb_ma_machine.join_path(dedup_store_path, "partition1"),
                ddb_ma=ddb_ma_machine.machine_name)
        else:
            storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)

        # Getting engine details
        dedupe_engine = self.commcell.deduplication_engines.get(self.storage_pool_name, "Primary")
        store = dedupe_engine.get(dedupe_engine.all_stores[0][0])

        # Add n partitons to provided store
        self.add_n_partitions_to_store(store,
                                       ddb_ma_machine,
                                       dedup_store_path,
                                       num_partitions,
                                       same_path)
        self._log.info(f"Creating Dependent Storage Policies")
        storage_policy_list = []
        content_path_list = []
        subclient_list = []

        # Create Backupset
        self._log.info("Creating BackupSet %s", self.backupset_name)
        backup_set_obj = self.mmhelper.configure_backupset(self.backupset_name)

        # Create Storage Policies and subclients per policy based on provided input of num_policies
        # and subclients_per_policy respectively
        self._log.info(f"Configuring {num_policies} storage policies and subclients")
        for num in range(1, num_policies + 1):
            if num_policies > 1:
                storage_policy = f"{self.storage_policy_name}_{num}"
            else:
                storage_policy = self.storage_policy_name
            self._log.info("Configuring Dependent Storage Policy ==> %s", storage_policy)
            if not self.commcell.storage_policies.has_policy(storage_policy):
                storage_policy_obj = self.commcell.storage_policies.add(
                    storage_policy_name=storage_policy,
                    global_policy_name=storage_pool.storage_pool_name)
            else:
                storage_policy_obj = self.commcell.storage_policies.get(storage_policy)

            storage_policy_list.append(storage_policy_obj)

            for sub_num in range(1, subclients_per_policy + 1):
                subclient_name = f"{self.subclient_name}_{num}_{sub_num}"
                client_drive = self.option_selector.get_drive(self.client_machine, size=25 * 1024)
                client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
                content_path = self.client_machine.join_path(client_path, f"content{num}_{sub_num}")

                self._log.info(f"Configuring subclient {subclient_name} for storage policy {storage_policy}")

                content_path_list.append(content_path)

                subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                              subclient_name,
                                                              storage_policy,
                                                              content_path)

                subclient_list.append(subclient)
                # set data readers to 5
                subclient_list[-1].data_readers = 5

        return storage_pool, storage_policy_list, content_path_list, subclient_list

    def add_n_partitions_to_store(self,
                                  store,
                                  ddb_ma_machine,
                                  dedup_store_path,
                                  num_partitions,
                                  same_path=True
                                  ):
        """
        Create storage pool with provided number of partitions
        Args:
            store          (object) -- DDB engine Store object
            ddb_ma_machine (object) -- DDB MA machine object
            dedup_store_path (str)  -- DDB path on DDB MA
            num_partitions  (int)   -- number of DDB partitions on storage pool
            same_path       (bool)  -- If true, DDB partitions are created on same path else unique
                                       directories are created for each path

        Returns:
            None
        """
        store.refresh()
        self._log.info(f"Adding {num_partitions} partitions to SIDB store {store.store_name}")

        # Create and add n partitions to store
        for idx in range(2, num_partitions + 1):
            try:
                if same_path:
                    self._log.info("Adding partition to same path")
                    store.add_partition(path=dedup_store_path,
                                        media_agent=ddb_ma_machine.machine_name)
                else:
                    part_dir = ddb_ma_machine.join_path(dedup_store_path,
                                                        f"partition{idx}")
                    if not ddb_ma_machine.check_directory_exists(part_dir):
                        ddb_ma_machine.create_directory(part_dir)

                    self._log.info("Adding partition in new directory for the dedup store")
                    store.add_partition(path=part_dir,
                                        media_agent=ddb_ma_machine.machine_name)

            except Exception as ex:
                self._log.warning("Some error during recreation of dedup path - %s", str(ex))

        store.refresh()
        self._log.info(f"Successfully added {num_partitions} to SIDB Store {store.store_name}")

    def update_ddb_settings(self, storage_policy_name, copy_name, **kwargs):
        """
        Update DDB settings for a storage policy copy

        Args:
            storage_policy_name (str): The name of the storage policy.
            copy_name (str): The name of the storage policy copy.
            **kwargs: Additional keyword arguments for configuring DDB settings.

            Keyword Args:
                enable_sw_compression (int): Enable software compression.
                    Values: 0 -> Disable, 1 -> Enable, 2 -> No Change
                enable_transactional_ddb (int): Enable transactional DDB.
                    Values: 0 -> Disable, 1 -> Enable, 2 -> No Change
                oldest_eligible_archive_time (int): To set the number of days to not deduplicate against objects older
                                                    than n days.

        Returns:
            None

        """
        enable_sw_compression = kwargs.get('enable_sw_compression', 2)
        enable_transactional_ddb = kwargs.get('enable_transactional_ddb', 2)
        oldest_eligible_archive_time = kwargs.get('oldest_eligible_archive_time', 0)

        self._log.info(f"Updating DDB settings for storage policy {storage_policy_name} and copy {copy_name}")

        request_json = {
            "App_UpdateStoragePolicyCopyReq":
                {
                    "storagePolicyCopyInfo":
                        {
                            "StoragePolicyCopy":
                                {
                                    "copyName": copy_name,
                                    "storagePolicyName": storage_policy_name
                                },
                            "DDBPartitionInfo":
                                {
                                    "sidbStoreInfo":
                                        {
                                            "sidbStoreFlags":
                                                {
                                                    "enableSWCompression": enable_sw_compression,
                                                    "enableTransactionalDDB": enable_transactional_ddb
                                                },
                                            "oldestEligibleObjArchiveTime": oldest_eligible_archive_time
                                        }
                                }
                        }
                }
        }

        response = self.commcell.qoperation_execute(request_json)
        if 'errorCode' in response:
            raise Exception(
                f"Updating DDB settings failed with error {response['errorMessage']}")
        if response['error']['errorCode']:
            raise Exception(f"{response['error']['errorMessage']}")
        self._log.info("Successfully updated DDB settings")


class MMHelper(object):
    """ Base clasee for media management helper functions"""

    def __init__(self, test_case_obj):
        """Initializes BasicOperations object

        Args:
            test_case_obj (object)  --  instance of the CVtestcase class

        """
        self.tcinputs = test_case_obj.tcinputs
        self.commcell = test_case_obj.commcell
        self.client = getattr(test_case_obj, '_client', None)

        self._log = logger.get_log()
        self.commserver_name = self.commcell.commserv_name
        self.id = test_case_obj.id
        self.csdb = test_case_obj.csdb
        self.agent = getattr(test_case_obj, '_agent')
        self.backupset_name = None
        self.subclient_name = None
        self.storage_policy_name = None
        self.library_name = None
        self.utility = OptionsSelector(self.commcell)
        if hasattr(test_case_obj, 'backupset_name'):
            self.backupset_name = test_case_obj.backupset_name
        if hasattr(test_case_obj, 'subclient_name'):
            self.subclient_name = test_case_obj.subclient_name
        if hasattr(test_case_obj, 'storage_policy_name'):
            self.storage_policy_name = test_case_obj.storage_policy_name
        if hasattr(test_case_obj, 'library_name'):
            self.library_name = test_case_obj.library_name

        self.content_path = self.tcinputs.get("ContentPath")

        if hasattr(test_case_obj, 'test_data_path') and self.content_path:
            self.content_path = test_case_obj.test_data_path

        self.is_windows_cs = not self.commcell.is_linux_commserv if self.commcell.is_linux_commserv is not None else None
        self.commserve_instance = ""
        self.instance_sep = ""

        if self.is_windows_cs:
            self.commserve_instance = "commvault"
            self.instance_sep = "\\"

        if 'SqlSaPassword' in self.tcinputs:
            dbpassword = self.tcinputs['SqlSaPassword']
            self.dbobject = MSSQL(self.commcell.commserv_hostname + self.instance_sep +
                                  self.commserve_instance,
                                  "sa", dbpassword, "CommServ", False, True)

    def unset_object_lock(self, storage_name):
        """
            This will unset the object lock on storage in CSDB

            Args:

                storage_name (str) - name of the storage to unset object lock

        """

        self._log.info("Unsetting object lock for storage %s", storage_name)
        command = "-sn setLibraryProperty -si %s -si archfilereadonly -si 0" % storage_name
        self._log.info("Executing Script - %s", command)
        self.commcell._qoperation_execscript(command)

    def set_bucket_lock(self, storage_name):
        """
           This will set the right flag for bucket lock in CSDB

           Args:

                storage_name (str) - name of the storage to set bucket lock

        """

        self._log.info("Setting bucket lock for storage %s", storage_name)
        command = "-sn setLibraryProperty -si %s -si EnableLibImmutable -si 1" % storage_name
        self._log.info("Executing Script - %s", command)
        self.commcell._qoperation_execscript(command)

    def update_mmpruneprocess(self, db_user, db_password, min_value=10, mmpruneprocess_value=60):
        """
        this function is to change the interval at which pruning happens

        Args:
            db_user     (str): CSDB username for commcell server
            db_password (str): CSDB password to update the config param value of prune interval
            min_value   (int): minimum threshold for pruning interval value in minutes
                if no value provided, value will revert to default 10
            mmpruneprocess_value (int): interval value in minutes after which pruning will occur
                If no value provided, value will revert to default 60

        """
        query = f"""update MMConfigs set value = {mmpruneprocess_value}, nMin = {min_value}
                                where name = 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS'"""
        self._log.info("QUERY: %s", query)
        self.execute_update_query(query, db_password, db_user)
        self._log.info("QUERY executed")

    def wait_for_job_state(self, _job, expected_state="completed", retry_interval=10, time_limit=30, hardcheck=True):
        """ Waits for the job to go into required state

            Args:
                _job              (str/int/obj)    -- Job id /Job object

                expected_state    (str/list)    -- Expected job id state. Default = completed.
                                                    suspended/killed/running/completed etc..
                                                    Can be a string OR list of job states
                                                    e.g
                                                    completed
                                                    ['waiting', 'running']

                retry_interval    (int)    -- Interval (in seconds) after which job state
                                                    will be checked in a loop. Default = 10

                time_limit        (int)    -- Time limit after which job status check shall be
                                                aborted if the job does not reach the desired
                                                 state. Default (in minutes) = 30

                hardcheck         (bool)   -- If True, function will exception out in case the job
                                                does not reaches the desired state.
                                              If False, function will return with non-truthy value

            Returns:
                True/False        (bool)   -- In case job reaches/does not reaches the desired
        """
        job_manager = JobManager(_job, self.commcell)
        return job_manager.wait_for_state(expected_state, retry_interval, time_limit, hardcheck)

    def wait_for_job_completion(self, job_obj, retry_interval=30, timeout=30):
        """
        Wait for the job completion

        Args:
            job_obj        (obj/int) -- Object of Job class OR job ID

            retry_interval (int) -- time interval in seconds to check the job status, default is 30 seconds

            timeout       (int) -- maximum time in minutes to wait for job completion, default is 30 minutes

        Returns:
            True/False    (bool) -- In case job reaches/does not reaches the desired
                                                state.

        Exception:
            Raise exception if job not completed successfully
        """

        job_manager = JobManager(job_obj, self.commcell)
        return job_manager.wait_for_state("completed", retry_interval, time_limit=timeout)

    def generate_automation_path(self, client_name, space_required=15000):
        """
        :param client_name: name of the client
        :param space_required: minimum space requirement on client
        :return: [ Machine class object, generated path for automation]
        """

        self._log.info(f"Creating machine object of [{client_name}]")
        client_machine_obj = Machine(client_name, self.commcell)
        self._log.info("Successfully created machine object")

        machine_drive = self.utility.get_drive(client_machine_obj, int(space_required))
        automation_path = machine_drive + "TestCase_" + str(self.id) + client_machine_obj.os_sep + "time_" + str(
            str(time.time())) + client_machine_obj.os_sep
        self._log.info(f"Generated file path : {automation_path}")

        return client_machine_obj, automation_path

    def run_backup(self, client_machine, subclient, content_path, scale_factor=1,
                   backup_type="FULL", size=1.0, delete_alternative=False):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups.
        if scalefactor in tcinput, creates factor times of backup data

        Args:
            client_machine (obj): client machine's object

            subclient (obj): object of subclient which will be backed up

            content_path (str): path where the data will be generated

            scale_factor (int): scaling multiple for the amount of data to be generated
                Default - 1

            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 1 GB

            delete_alternative (bool): to run a backup by deleting alternate content, set True
                Default - False

        Returns:
        (object) -- returns job object to backup job
        """
        additional_content = client_machine.join_path(content_path, 'generated_content')
        if not delete_alternative:
            # add content
            if client_machine.check_directory_exists(additional_content):
                client_machine.remove_directory(additional_content)
            # if scale test param is passed in input json, multiple size factor times and generate content
            if scale_factor:
                size = size * int(scale_factor)
            # calculate files
            files = (size * 1024 * 1024) / 10240
            client_machine.generate_test_data(additional_content, dirs=1, files=int(files), file_size=10240)
        else:
            files_list = client_machine.get_files_in_path(additional_content)
            self._log.info("deleting alternate content files...")
            for i, file in enumerate(files_list):
                if i & 2 == 0:
                    client_machine.delete_file(file)
        self._log.info("Running %s backup...", backup_type)
        job = subclient.backup(backup_type)
        self._log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self._log.info("Backup job completed.")
        return job

    def get_recall_wf_job(self, restore_job):
        """
        Get the active recall workflow job for the given restore job

        Args:
            restore_job (int) -- restore job id

        Returns:
            (int) -- recall workflow job id
        """
        query = f"""
                    SELECT JS.jobId
                    FROM JMJobStats JS WITH (NOLOCK),JMAdminJobInfoTable AJ WITH (NOLOCK), WF_Definition W WITH (NOLOCK)
                    WHERE JS.jobId=AJ.jobId
                    AND	AJ.workFlowId=W.WorkflowId
                    AND JS.opType=90
                    AND W.name= 'Cloud Storage Archive Recall'
                    AND CAST(
                    CAST(JS.xmlJobInfo AS xml).value('(/Workflow_StartWorkflow/@options)[1]', 'nvarchar(max)') AS xml
                            ).value('(/inputs/job_id/text())[1]', 'int') = {restore_job}
                    """
        self._log.info("QUERY: %s", query)
        for i in range(1, 4):
            self._log.info("Trying to get recall workflow job for restore job [%s] - attempt [%s]", restore_job, i)
            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            self._log.info("RESULT: %s", cur[0])
            if cur[0] != '':
                recall_wf_job = int(cur[0])
                self._log.info("Recall workflow job [%s] is triggered for restore job [%s]", recall_wf_job, restore_job)
                return recall_wf_job
            self._log.info("No running Recall workflow job found yet, retry after [%s] sec", (i * 20))
            time.sleep(i * 20)
        raise Exception("No running Recall workflow job found for restore job [{0}]".format(restore_job))

    def get_drive_pool_id(self, tape_id):
        """
        Get drivepool id

        Args:
            tape_id   (str)   --  Tape library ID

        Returns:
            DrivePool id of the given Tape library

        """
        self.csdb.execute(
            """select *
            from MMDrivePool
            where MasterPoolId =
            (select MasterPoolId
            from MMMasterPool
            where LibraryId = {0})
            """.format(str(tape_id)))
        drive_pool_id = str(self.csdb.fetch_one_row()[0])
        return drive_pool_id

    def get_spare_pool_id(self, tape_id):
        """
        get sparepool id

        Args:
            tape_id   (str)   --  Tape library ID

        Returns:
                SparePool id of the given Tape library

        """
        self.csdb.execute(
            """select *
            from MMSpareGroup
            where LibraryId = {0}
            """.format(str(tape_id)))
        spare_pool_id = str(self.csdb.fetch_one_row()[0])
        return spare_pool_id

    def get_copy_id(self, sp_name, copy_name):
        """
        get copy id

         Args:
            sp_name     (str) --  Storage policy name

            copy_name   (str) -- Storage policy copy name

        Returns:
                Copy id for the given storage policy/copy

        """
        self.csdb.execute(
            """ SELECT AGC.id
                FROM archgroup AG
                    INNER JOIN archgroupcopy AGC ON AG.id = AGC.archgroupid
                WHERE AG.name ='{0}' AND AGC.name = '{1}'
            """.format(sp_name, copy_name))
        copy_id = self.csdb.fetch_one_row()
        return copy_id[0]

    def get_mount_path_id(self, mountpath_name):
        """
        Get MountPathId from MountPathName

        Agrs:
            mountpath_name (str)  --  Mountpath name

        Returns:
            Mountpath Id for the given Mountpath name
        """

        query = """ SELECT	MountPathId
                    FROM	MMMountPath 
                    WHERE	MountPathName = '{0}'""".format(mountpath_name)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            value = int(cur[0])
            return value
        self._log.error("No entries present")
        raise Exception("Invalid MountPathName")

    def get_device_controller_id(self, mountpath_id, media_agent_id):
        """
        Get device controller id from mountpath id and media agent id
        Args:
            mountpath_id (int)  --  mountpath Id

            media_agent_id (int) -- media agent Id

        Returns:
            Device Controller id for the given mountpath Id
        """
        query = """ SELECT	MDC.DeviceControllerId
                    FROM	MMDeviceController MDC
                    JOIN	MMMountPathToStorageDevice MPSD
                            ON	MDC.DeviceId = MPSD.DeviceId
                    JOIN	MMMountPath MP
                            ON	MPSD.MountPathId = MP.MountPathId
                    WHERE	MP.MountPathId = {0} AND
                            MDC.ClientId = {1} """.format(mountpath_id, media_agent_id)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            return int(cur[0])
        self._log.error("No entries present")
        raise Exception("Invalid MountPathId or ClientId")

    def get_device_id(self, mountpath_id):
        """
        Get the device id for the given mountpath id
            Args:
             mountpath_id(int)   -   Mountpath Id

            Returns:
                int    --  device id
        """

        query = """SELECT	DeviceId
                  FROM	MMMountPathToStorageDevice
                  WHERE	MountPathId = {0}""".format(mountpath_id)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return int(cur[0])
        raise Exception("Unable to fetch device id")

    def get_media_location(self, media_name):
        """
            Get media location Id
            Args:
                media_name (str) : BarCode of the media
            Returns:
                Slot Id of the Media
        """

        query = f"""SELECT	SlotId
                    FROM	MMSlot MS
                    JOIN	MMMedia MM
                            ON MM.MediaId = MS.MediaId
                    WHERE	MM.BarCode = '{media_name}'"""

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return int(cur[0])
        raise Exception("Unable to fetch media location")

    def get_device_path(self, mountpath_id, client_id):
        """
        Get Device Path from MountpathId
        Agrs:
            mountpath_id (int)  --  Mountpath Id
        Returns:
            Device Path for the given Mountpath Id
        """
        query = """ SELECT	MDC.Folder
                    FROM	MMDeviceController MDC
                    JOIN	MMMountPathToStorageDevice MPSD
                            ON	MDC.DeviceId = MPSD.DeviceId
                    JOIN	MMMountPath MP
                            ON	MPSD.MountPathId = MP.MountPathId
                    WHERE	MP.MountPathId = {0} AND
                            MDC.ClientId = {1} """.format(mountpath_id, client_id)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            return cur[0]
        self._log.error("No entries present")
        raise Exception("Invalid MountPathId or ClientId")

    def get_device_access_type(self, mountpath_id, media_agent):
        """
        To get the device access type for the given mountpath id and mediaagent name
            Args:
             mountpath_id(int)   -   Mountpath Id

             media_agent(str)    -   MediaAgent Name

            Returns:
                int    --  device access type
        """

        query = """SELECT	MDC.DeviceAccessType
                    FROM	MMDeviceController MDC
                    JOIN	MMMountPathToStorageDevice MPSD
                            ON	MDC.DeviceId = MPSD.DeviceId
                    JOIN	APP_Client Cli
                            ON	MDC.ClientId = Cli.id
                    WHERE	MPSD.MountPathId = {0}
                            AND	Cli.name = '{1}'""".format(mountpath_id, media_agent)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return int(cur[0])
        raise Exception("Unable to fetch device access type")

    def remove_content(self, test_data_path, client_machine, num_files=None, suppress_exception=False):
        """
        Deletes subclient data

        Args:
            test_data_path  (str)   --  path where the subclient backup content is present

            client_machine  (obj)   --  object for the client machine on which subclient is present

            num_files       (int)   --  Number of files to be deleted
            Default : None [all files to be deleted]

            suppress_exception (bool) -- suppress cleanup failure Exception and treat as soft failure
        Returns:
            Number of files deleted
        """
        try:
            list_of_files = client_machine.get_files_in_path(test_data_path)
            if num_files is None:
                num_files = len(list_of_files)
                self._log.info("Deleting all files")
                client_machine.remove_directory(test_data_path)
            else:
                self._log.info("Deleting {0} files".format(str(num_files)))
                for c in range(0, num_files):
                    client_machine.delete_file(list_of_files[c])
            return num_files
        except Exception as exe:
            if suppress_exception:
                self._log.warning("Error during deletion. Exception suppressed: {%s}", str(exe))
            else:
                raise Exception(str(exe))

    def get_archive_file_size(self, copy_id, job_id=None):
        """
        Gets sum of archive file size on a copy/for a job

        Args:
            copy_id  (str)   --  storage policy copy id

            job_id   (str)   --  job id
            Default : None

        Returns:
            sum of archive file size

        """
        if job_id is None:
            query = """select sum(physicalSize)
                    from archChunkMapping
                    where archCopyId = {0} and jobid in
                        (select distinct jobid
                        from jmjobdatastats
                        where archgrpcopyid = {0})""".format(str(copy_id))
        else:
            query = """select sum(physicalSize)
                                from archChunkMapping
                                where archCopyId = {0} and jobid = {1})""".format(copy_id, job_id)
        self._log.info("Running query : \n{0}".format(query))
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def set_opt_lan(self, value, server_name, user, password, client_id):
        """ Modifies Optimize for concurrent LAN backups option on the MA

            Args:
                value       (str)   -- Disable/Enable

                server_name (str)   -- SQL server name

                user        (str)   -- username for the SQL

                password    (str)   -- password for SQL (from registry)

                client_id   (str)   -- client machine ID

                e.g:
                    mmhelper_obj.set_opt_lan("Enable","######",
                    "sa", "######", "2")

            Raises:
                SDKException:
                    if input is incorrect
        """
        if value.lower() == "disable":
            operation = "&~"
        elif value.lower() == "enable":
            operation = "|"
        else:
            raise Exception("Input is not correct")
        query = """ UPDATE MMHost
                SET Attribute = Attribute {0} 32
                WHERE ClientId = {1}""".format(operation, client_id)
        self._log.info("Running query : \n{0}".format(query))
        # As Linux CS does not have any instance name, if user has provided instance name as commvault
        # strip off the instance name and use only server_name
        if not self.is_windows_cs:
            sql_server_name, sql_instance = server_name.split('\\')
            server_name = sql_server_name

        mssql = MSSQL(server_name, user, password, "CommServ")
        mssql.execute(query)

    def get_global_param_value(self, param_name):
        """ gets param value from gxglobalparam table
        Args:
            param_name   (str)   --  global parameter name

        Returns:
            (int)   param value set in DB
        """

        query = """select value
                    from gxglobalparam
                    where name = '{0}'""".format(param_name)
        self._log.info("Running query : \n{0}".format(query))
        self.csdb.execute(query)
        if not self.csdb.fetch_one_row()[0]:
            return 0
        return int(self.csdb.fetch_one_row()[0])

    def get_jobs_picked_for_aux(self, auxcopy_job_id):
        """ gets number of jobs picked by an auxcopy job
        Args:
            auxcopy_job_id   (str)   --  global parameter name

        Returns:
            (int)   number of the jobs picked by auxcopy job

        """
        query = """SELECT COUNT(DISTINCT BackupJobID)
            FROM ArchChunkToReplicate
            WHERE AdminJobID = {0}""".format(auxcopy_job_id)
        self._log.info("Running query : \n{0}".format(query))
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def get_to_be_copied_jobs(self, copy_id):
        """gets number of jobs in to-be-copied state for a copy
        Args:
            copy_id   (str)   --  copy id

        Returns:
            (int)   count of the jobs picked by auxcopy job

        """
        query = """ select count( distinct jobId)
                    from JMJobDataStats
                    where status in (101,102,103)
                    and archGrpCopyId = {0}""".format(copy_id)
        self._log.info("Running query : \n{0}".format(query))
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def move_job_start_time(self, job_id, reduce_days=1):
        """
        runs script to change job time based on number of days in arguments
        Args:
            job_id (int) -- Job ID that needs to be moved with time
            reduce_days (int) -- number of days to reduce the job time

        Return:
            (Bool) -- True/False
        """
        self._log.info("Moving job {0} to {1} day(s) behind".format(job_id, reduce_days))
        sql_script = """
        DECLARE @curCommCellId INTEGER
        SET @curCommCellId = 0

        DECLARE @curJobId INTEGER
        SET @curJobId = {0}

        DECLARE @i_days INTEGER
        SET @i_days = {1}

        SELECT @curCommCellId = commcellId
        FROM JMBkpStats
        where jobId = @curJobId

        UPDATE JMBkpStats
        SET servStartDate = servStartDate - (@i_days *24* 3600),
        servEndDate = servEndDate - (@i_days* 24* 3600)
        WHERE jobId = @curJobId
        AND commCellId = @curCommCellId
        """.format(job_id, reduce_days)
        retcode = self.execute_update_query(sql_script)
        if retcode:
            return True
        raise Exception("failed to run the script to move job time")

    def get_ma_using_hostname(self, hostname):

        """
        Returns a MediaAgent object of the specified media agent hostname.

        Args:
            hostname (str)  --  hostname of the media agent machine

        Returns:
            object - instance of the cvpysdk MediaAgent class for the given media agent name

        Raises:
            SDKException
                if no media agent exists with the given hostname
        """

        query = f"""SELECT name
                            FROM APP_CLIENT
                            WHERE net_hostname='{hostname}'
                    """

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        query_res = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", query_res)

        client_name = query_res[0]

        if (client_name == ''):
            raise Exception(f"{hostname} is a invalid hostname")

        return MediaAgent(self.commcell, client_name)

    def retire_media_agent(self, ma_name, force=False):
        """
        Retires the MA role of the media agent if theirs exists a MA by given name

        Args:
            ma_name (str)  --  name of the media agent
            force (bool)   --  If you want to force retire the MA role

        Returns:
            returns False -> if no MA by given name exist
            returns True ->  if MA role retired successfully
        """

        if self.commcell.media_agents.has_media_agent(ma_name):
            self.commcell.media_agents.delete(ma_name, force)
            self._log.info(f"Media Agent [{ma_name}] retired successfully")
            return True
        else:
            self._log.info(f"Media Agent [{ma_name}] doesn't exist")
            return False

    def retire_client(self, client_name, wait_for_complete=True):
        """
        Uninstalls the CommVault Software, releases the license and deletes the client if it exists.

        Args:
            client_name (str)  --  name of the client to be deleted
            wait_for_complete (bool) -- wait for the retire job to complete

        Returns:
            returns False -> if client doesn't exist
            returns True ->  if wait_for_complete is True & if retire job is successful
            returns Job obj -> if client exist but wait_for_complete is False
            returns None -> if client exist but wait_for_complete is False and no job is created to retire the client

        Raises:
            SDKException
                if retire fails

        """
        if self.commcell.clients.has_client(client_name):
            job_obj = Client(self.commcell, client_name).retire()

            # sometimes no job_obj is returned in cases like when their's a client with no data and not reachable
            # in such cases CS retires the client without creating a job

            if (job_obj is None):
                self._log.info(f"Client [{client_name}] retired successfully")
                return None
            elif wait_for_complete:
                self._log.info(f"Retire job started for client [{client_name}]")
                self.wait_for_job_completion(job_obj)
                self._log.info(f"Client [{client_name}] retired successfully")
                # Refresh the clients list in comcell object to update the clients list
                self.commcell.clients.refresh()
                return True
            else:
                self._log.info(f"Client [{client_name}] retire job started and Job ID = [{job_obj.job_id}]")
                return job_obj
        else:
            self._log.info(f"Client [{client_name}] doesn't exist")
            return False

    def execute_update_query(self, query, db_password=None, db_user=None):
        """
        Executes update query on CSDB
        Args:
            query (str) -- update query that needs to be run on CSDB
            db_password (str)   -- sa password for CSDB login
            db_user (str)   -- username for CSDB login

        Return:
            Response / exception
        """
        if not db_user:
            db_user = "sa"
        try:
            if 'SqlSaPassword' in self.tcinputs and db_password is None:
                db_password = self.tcinputs['SqlSaPassword']

            self.dbobject = MSSQL(self.commcell.commserv_hostname + self.instance_sep +
                                  self.commserve_instance,
                                  db_user, db_password, "CommServ", False, True)
            response = self.dbobject.execute(query)
            if response.rows is None:
                return bool(response.rowcount == 1)
            return response

        except Exception as err:
            raise Exception("failed to execute query {}".format(err))

    def execute_stored_proc(self, stored_proc_name, param=None, timeout=None, use_set_nocount=False):
        """
        Executes stored procedure on CSDB
        Args:
            stored_proc_name (str)  --  name of stored procedure that needs to be run on CSDB

            param (tuple)           --  tuple of parameters for stored proc

            timeout (int or double) --  number of seconds before exception is thrown

            use_set_nocount (bool)  --  Required when calling an SP which returns some data back
                                        This will also eliminate the "Previous SQL was not a query" errors
        Return:
            Exception or return a tuple with response and time taken

        Example:
            execute_stored_proc("TestStoredProc", (4,2,), 7)
                                     --  Executes the procedure CommServ.dbo.TestStoredProc with
                                         parameters 4 and 2 and has a timeout set for 7 seconds
        """
        try:
            db_password = commonutils.get_cvadmin_password(self.commcell)
            self.dbobject = MSSQL(self.commcell.commserv_hostname + self.instance_sep +
                                  self.commserve_instance,
                                  'sqladmin_cv', db_password, "CommServ", False)
            if param is None or param == ():
                exec_string = f"exec CommServ.dbo.{stored_proc_name}"
            else:
                if not isinstance(param, tuple):
                    raise Exception("Incorrect input value for parameter <param> : Tuple expected")
                exec_string = f"exec {stored_proc_name} ?" + ", ?" * (len(param) - 1)

            # Required when calling an SP which returns some data back
            # This will also eliminate the "Previous SQL was not a query" errors
            if use_set_nocount:
                exec_string = 'SET NOCOUNT ON; ' + exec_string

            self._log.info("complete stored procedure call : %s & parameters : %s", exec_string, str(param))
            start_time = time.time()
            response = self.dbobject.execute_stored_procedure(exec_string, param)
            end_time = time.time()
            if response.rows is None:
                response = bool(response.rowcount == 1)

            time_taken = end_time - start_time
            self._log.info("Stored procedure took %s seconds to execute", time_taken)
        except Exception as err:
            raise Exception("failed to execute query {}".format(err))

        if timeout:
            if time_taken > timeout:
                raise Exception(f"Stored procedure took {time_taken} seconds. Exceeded timeout of {timeout} seconds.")
        return response, time_taken

    def cleanup(self):
        """
        deletes backupset, storage policy
        """
        self._log.info("********* cleaning up BackupSet, StoragePolicy ***********")
        self.agent.backupsets.delete(self.backupset_name)
        self.commcell.storage_policies.delete(self.storage_policy_name)

    def validate_copy_prune(self, copy_name):
        """
        verifies if a copy exits or deleted
        Args:
            copy_name (str) -- copy name to verify if deleted

        Return:
             (Bool) True if copy is deleted
             (Bool) False if copy exists
        """
        self.sp = self.commcell.storage_policies.get(self.storage_policy_name)
        if self.sp.has_copy(copy_name):
            self._log.info("Copy exists! ")
            return False
        self._log.info("Copy doesnt exist!")
        return True

    def validate_job_prune(self, job_id, copy_id=None):
        """
        Validates if a job is aged by checking table entries
        Args:
            job_id (int) -- job id to check for aged
            copy_id (int) -- copy id needed for the job
                            if copy_id exist use new query else old one.

        Return:
            (Bool) True/False
        """
        if copy_id:
            jmdatastats_exists = self.validate_jmdatastats(job_id, copy_id)
            (archfile_exists, archfile_id) = self.validate_archfile(job_id)
            (archchunkmapping_exists, archchunkmapping_values) = self.validate_archchunkmapping(job_id, copy_id)
        else:
            jmdatastats_exists = self.validate_jmdatastats(job_id)
            (archfile_exists, archfile_id) = self.validate_archfile(job_id)
            (archchunkmapping_exists, archchunkmapping_values) = self.validate_archchunkmapping(job_id)
        if (jmdatastats_exists and archfile_exists and archchunkmapping_exists):
            self._log.info("Job {0} is not aged!".format(job_id))
            return False
        self._log.info("Job {0} is aged!".format(job_id))
        return True

    def validate_jmdatastats(self, job_id, copy_id=None):
        """
        Validate if a job id exists in table jmdatastats
        Args:
            job_id (int) -- backup job id to check in table
            copy_id (Int) -- we can pass copy id to check for particular copy.
                            if copy_id : then use new query else old one

        Return:
            (int) agedTime
            (int) agedBy
            (int) disabled flag for the jobid
        """
        if copy_id:
            query = """select agedTime, agedBy, disabled&256 from JMJobDataStats where jobId = {0} 
            and archGrpCopyId = {1}""".format(job_id, copy_id)
        else:
            query = """select agedTime, agedBy, disabled&256 from JMJobDataStats where jobId = {0}""".format(job_id)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(cur))
        if cur != ['']:
            values = [int(x) for x in cur]
            if values[0] > 0 and values[1] > 0 and values[2] == 256:
                return False
        self._log.info("no entries present")
        return True

    def validate_archfile(self, job_id):
        """
        Validate if archfile entry for job id is exists
        Args:
            job_id (int) -- job id to check in table

        Return:
            (Bool) True with archfileid if exists
            (Bool) False if entry not present
        """
        query = """select id from ArchFile where jobid = {0}""".format(job_id)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self._log.info("RESULT: {0}".format(cur[0]))
        if cur[0] != ['']:
            values = [int(x) for x in cur[0]]
            if values:
                return True, values
        self._log.info("no entries present")
        return False, 0

    def validate_archfilecopy(self, archfile_id, copy_id):
        """
        validate if archfilecopy entry for job id exists
        Args:
            archfile_id (int) -- archfile id to check in table
            copy_id (int) -- copy id to check in table

        Return:
            (Bool) True if entries exist
            (Bool) False if entries doesnt exist
        """
        query = """select 1 from archFileCopy where archFileId = {0} and archCopyId = {1}
                """.format(archfile_id, copy_id)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: {0}".format(cur[0]))
        if cur[0] != ['']:
            value = int(cur[0])
            if value:
                return True
        self._log.info("no entries present")
        return False

    def validate_archchunkmapping(self, job_id, copy_id=None):
        """
        Validate if archchunkmapping entry for job id exists
        Args:
            job_id (int) -- job id to check in table
            copy_id (int) -- copy id of the job to validate for
                            if copy_id : then use new query else old one

        Return:
            (Bool) True if entries exist
            (Bool) False if entries doesnt exist
        """
        if copy_id:
            query = """select archFileId, archChunkId from archchunkmapping where jobId = {0} and archCopyId = {1}
                """.format(job_id, copy_id)
        else:
            query = """select archFileId, archChunkId from archchunkmapping where jobId = {0}""".format(job_id)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self._log.info("RESULT: {0}".format(cur))
        if cur != [['']]:
            values = [[int(y) for y in x] for x in cur]
            if values:
                return True, values
        self._log.info("no entries present")
        return False, 0

    def validate_job_retentionflag(self, job_id, retention_flag):
        """
        Validate if extended retention flag is set for a job id
        Args:
            job_id (int) -- Job id to check for retention flags
            retention_flag (str) -- retention flag to check for job id

        Return:
            (Bool) True/False
        """
        mapping = {
            "EXTENDED_ALLFULL": 2,
            "EXTENDED_WEEK": 4,
            "EXTENDED_MONTH": 8,
            "EXTENDED_QUARTER": 16,
            "EXTENDED_HALFYEAR": 32,
            "EXTENDED_YEAR": 64,
            "MANUALLY_PIN": 128,
            "EXTENDED_GRACE_WEEK": 256,
            "EXTENDED_GRACE_MONTH": 512,
            "EXTENDED_GRACE_QUARTER": 1024,
            "EXTENDED_GRACE_HALFYEAR": 2048,
            "EXTENDED_GRACE_YEAR": 4098,
            "EXTENDED_CANDIDATE_WEEK": 8192,
            "EXTENDED_CANDIDATE_MONTH": 16384,
            "EXTENDED_CANDIDATE_QUARTER": 32768,
            "EXTENDED_CANDIDATE_HALFYEAR": 65536,
            "EXTENDED_CANDIDATE_YEAR": 131072,
            "EXTENDED_HOUR": 262144,
            "EXTENDED_DAY": 524288,
            "EXTENDED_CANDIDATE_HOUR": 1048576,
            "EXTENDED_CANDIDATE_DAY": 2097152,
            "EXTENDED_GRACE_HOUR": 4194304,
            "EXTENDED_GRACE_DAY": 8388608,
            "EXTENDED_LAST_JOB": 16777216,
            "EXTENDED_FIRST": 33554432
        }
        value = mapping[retention_flag]
        query = """select retentionFlags&{0} from JMJobDataStats where jobid = {1}
                and dataType = 2""".format(value, job_id)
        self._log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self._log.info("RESULT: {0}".format(cur[0]))
        if int(cur[0][0]) == value:
            return True
        self._log.info("flag not present")
        return False

    def setup_environment(self):
        """
        get testcase object and setup library, non dedupe storage policy, backupset and subclient

        Returns:
            (object)    -- disk library object
            (object)    -- storage policy object
            (object)    -- backupset object
            (object)    -- subclient object
        """
        disk_library = self.configure_disk_library()
        storage_policy = self.configure_storage_policy()
        backupset = self.configure_backupset()
        subclient = self.configure_subclient()
        return disk_library, storage_policy, backupset, subclient

    def configure_disk_library(self,
                               library_name=None,
                               ma_name=None,
                               mount_path=None,
                               username="", password=""):
        """
        Create a new disk library if not exists
        Args:
            library_name (str)  -- library name to create

            ma_name (str)       -- MA name to use for library

            mount_path (str)    -- path to create mount path for library

            username (str)      -- username to access unc mp

            password (str)      -- password to access unc mp

        Return:
            (object)    -- disk library object
        """
        # config disk library
        if library_name is None:
            library_name = self.library_name
        if ma_name is None:
            ma_name = self.tcinputs["MediaAgentName"]
        if mount_path is None:
            mount_path = self.tcinputs["MountPath"]
        self._log.info("check library: %s", library_name)
        if not self.commcell.disk_libraries.has_library(library_name):
            self._log.info("adding Library...")
            disk_library = self.commcell.disk_libraries.add(library_name,
                                                            ma_name,
                                                            mount_path,
                                                            username=username, password=password)
            self._log.info("Library Config done.")
            return disk_library
        disk_library = self.commcell.disk_libraries.get(library_name)
        self._log.info("Library exists!")
        return disk_library

    def configure_disk_mount_path(self, disk_library, mount_path, media_agent, **kwargs):
        """ Adds a mount path [local/remote] to the disk library

               Args:
                   disk_library  (object) --  instance of disk library to add the mountpath to

                   mount_path  (str)   -- Mount path which needs to be added to disklibrary.
                                         This could be a local or remote mount path on mediaagent

                   media_agent (str)   -- MediaAgent on which mountpath exists

                   \*\*kwargs  (dict)  --  Optional arguments

                    Available kwargs Options:

                       username    (str)   -- Username to access the mount path

                       password    (str)   -- Password to access the mount path

               Returns:
                   None
        """
        username = kwargs.get('username', '')
        password = kwargs.get('password', '')
        self._log.info("Adding MountPath to Disk Library: %s", disk_library.library_name)
        disk_library.add_mount_path(mount_path, media_agent, username, password)
        self._log.info("MountPath Configuration Done.")

    def configure_cloud_library(self, library_name, media_agent, mount_path, username, password='', server_type='',
                                saved_credential_name='', proxy_password=''):
        """
        Adds a new Cloud Library to the Commcell.

            Args:
                library_name (str)        --  name of the new cloud library to add

                media_agent  (str/object) --  name or instance of media agent to add the library to

                mount_path   (str)        --  cloud container or bucket

                username     (str)        --  username to access mountpath in the format <ServiceHost>//<AccountName>
                                              Eg: s3.us-west-1.amazonaws.com//MyAccessKeyID

                password     (str)        --  password to access the mount path

                server_type   (str)       --  provide cloud library server type

                saved_credential_name (str) -- name of saved credentials
                                                if saved credentials are username used be given in the format
                                                <ServiceHost>//__CVCRED__
                                                Eg: s3.us-west-1.amazonaws.com//__CVCRED__

                proxy_password (str) -- password of proxy server

            Returns:
                object - instance of the disk library class, if created successfully
        """
        server_type_dict = mediaagentconstants.CLOUD_SERVER_TYPES
        if not server_type.lower() in server_type_dict:
            raise Exception('Invalid server type specified')
        server_type = server_type_dict[server_type.lower()]
        self._log.info("check library: %s", library_name)
        if not self.commcell.disk_libraries.has_library(library_name):
            self._log.info("adding Library...")
            cloud_library = self.commcell.disk_libraries.add(library_name, media_agent, mount_path, username, password,
                                                             server_type, saved_credential_name,
                                                             proxy_password=proxy_password)
            self._log.info("Library Config done.")
            return cloud_library
        cloud_library = self.commcell.disk_libraries.get(library_name)
        self._log.info("Library exists!")
        return cloud_library

    def configure_cloud_mount_path(self, cloud_library, mount_path, media_agent, username, password, server_type):
        """ Adds a mount path to the cloud library

            Args:
                cloud_library (object)  -- instance of cloud library

                mount_path  (str)   -- cloud container or bucket.

                media_agent (str)   -- MediaAgent on which mount path exists

                username    (str)   -- Username to access the mount path in the format <Service Host>//<Account Name>
                Eg: s3.us-west-1.amazonaws.com//MyAccessKeyID. For more information refer http://documentation.commvault.com/commvault/v11/article?p=97863.htm

                password    (str)   -- Password to access the mount path

                server_type  (str)   -- provide cloud library server type
        """
        server_type_dict = mediaagentconstants.CLOUD_SERVER_TYPES
        if not server_type.lower() in server_type_dict:
            raise Exception('Invalid server type specified')
        server_type = server_type_dict[server_type.lower()]
        self._log.info("Adding MountPath to Cloud Library: %s", cloud_library.library_name)
        cloud_library.add_cloud_mount_path(mount_path, media_agent, username, password, server_type)
        self._log.info("MountPath Configuration Done.")

    def configure_storage_policy(self,
                                 storage_policy_name=None,
                                 library_name=None,
                                 ma_name=None,
                                 storage_pool_name=None,
                                 dr_sp=None, retention_period=5):
        """
        creates a new storage policy if not exists
        Args:
            storage_policy_name (str)   --  storage policy name to create storage policy

            library_name (str)          --  library to use for creating standalone storage policy

            ma_name (str)               --  mediaagent to use for creating standalone storage policy

            storage_pool_name(str)      --  storage pool to use for creating dependent storage policy

            dr_sp (bool)                -- if True creates dr storage policy
                                           if False (or None) creates data protection policy

            retention_period(int)       --  time period in days to retain (default - 5)

        Return:
            (object)    -- storage policy object
        """
        if storage_policy_name is None:
            storage_policy_name = self.storage_policy_name
        self._log.info("checking if storage policy [%s] already exists: ", storage_policy_name)
        if not self.commcell.storage_policies.has_policy(storage_policy_name):
            self._log.info("Adding storage policy[%s]...", storage_policy_name)
            if storage_pool_name:
                is_dedupe_storage_pool = False
                storage_pool = self.commcell.storage_pools.get(storage_pool_name)
                if storage_pool.storage_pool_type == StoragePoolType.DEDUPLICATION:
                    is_dedupe_storage_pool = True
                storage_policy = self.commcell.storage_policies.add(storage_policy_name,
                                                                    global_policy_name=storage_pool_name,
                                                                    global_dedup_policy=is_dedupe_storage_pool,
                                                                    retention_period=retention_period)
                self._log.info("Storage pool [%s] dependent storage policy [%s] created successfully.",
                               storage_pool_name, storage_policy_name)
                return storage_policy
            if library_name is None:
                library_name = self.library_name
            if ma_name is None:
                ma_name = self.tcinputs["MediaAgentName"]
            storage_policy = self.commcell.storage_policies.add(storage_policy_name,
                                                                library_name,
                                                                ma_name,
                                                                None, None, 1,
                                                                dr_sp=dr_sp)
            self._log.info("Standalone storage policy [%s] created successfully.", storage_policy_name)
            return storage_policy
        self._log.info("Storage policy exists!")
        storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        return storage_policy

    def configure_air_gap_protect_pool(self, storage_pool_name, media_agent, storage_type, storage_class, region_name,
                                       ddb_ma=None, ddb_path=None, wait_for_online_status=False):
        """
            Adds a new air_gap_protect storage pool to commcell

                Args:
                    storage_pool_name   (str)       --  name of new storage pool to add

                    media_agent         (str/object)--  name or instance of media agent

                    storage_type        (str)        -- name of the cloud vendor (str, eg - "Microsoft Azure storage") (same as UI)

                    storage_class       (str)        -- storage class (str, eg - "Hot","Cool") (same as UI)

                    region_name (str)      --  name of the geographical region for storage (same as in UI)

                    ddb_ma (str)               -- DDB Media Agent name for Storage pool

                    ddb_path(str)              -- Path for DDB

                    wait_for_online_status (bool) -- to wait until Air Gap Protect storage is fully configured (default-False)

            Return:
                list   -- storage pool and its library object
        """

        self._log.info("checking if storage pool [%s] exists", storage_pool_name)
        if not self.commcell.storage_pools.has_storage_pool(storage_pool_name):
            self._log.info("adding air_gap_protect storage pool [%s]...", storage_pool_name)
            storage_pool_obj = self.commcell.storage_pools.add_air_gap_protect(storage_pool_name=storage_pool_name,
                                                                               media_agent=media_agent,
                                                                               storage_type=storage_type,
                                                                               storage_class=storage_class,
                                                                               region_name=region_name,
                                                                               ddb_ma=ddb_ma, dedup_path=ddb_path)

            self._log.info("air_gap_protect storage pool [%s] created successfully", storage_pool_name)
        else:
            self._log.info("air_gap_protect storage pool [%s] already exists.", storage_pool_name)
            storage_pool_obj = self.commcell.storage_pools.get(storage_pool_name)
        library_details = storage_pool_obj.storage_pool_properties["storagePoolDetails"]["libraryList"][0]['library']
        library_obj = self.commcell.disk_libraries.get(library_details["libraryName"])
        if wait_for_online_status:
            self.wait_for_online_status_air_gap_protect(air_gap_protect_obj=storage_pool_obj)
        return storage_pool_obj, library_obj

    def configure_storage_pool(self, storage_pool_name, mount_path, media_agent, ddb_ma=None, ddb_path=None, **kwargs):
        """
            creates a new dedupe or non-dedupe storage pool
            Args:
                storage_pool_name (str)   -- storage pool name to create storage pool

                mount_path (str)          -- mountpath to use for creating storage pool

                media_agent (str)          -- Media Agent name for Storage pool

                ddb_ma (str)               -- DDB Media Agent name for Storage pool

                ddb_path(str)              -- Path for DDB

            **kwargs:
                username        (str)       --  username to access the mountpath

                password        (str)       --  password to access the mountpath

                credential_name (str)       --  name of the credential as in credential manager

                cloud_vendor_name (str)     --  name of the cloud vendor (required for cloud storage pool)

            Return:
                list   -- storage pool and its library object

        """
        self._log.info("checking if storage pool [%s] exists", storage_pool_name)
        if not self.commcell.storage_pools.has_storage_pool(storage_pool_name):
            self._log.info("adding storage pool [%s]...", storage_pool_name)
            username = kwargs.get('username', None)
            password = kwargs.get('password', None)
            saved_credential = kwargs.get('credential_name', None)
            cloud_vendor = kwargs.get('cloud_vendor_name', None)
            if cloud_vendor:
                server_type_dict = mediaagentconstants.CLOUD_SERVER_TYPES
                if cloud_vendor.lower() not in server_type_dict:
                    raise Exception('Invalid server type specified')
                server_type = server_type_dict[cloud_vendor.lower()]
            else:
                server_type = None
            storage_pool_obj = self.commcell.storage_pools.add(storage_pool_name, mount_path, media_agent, ddb_ma,
                                                               ddb_path, username=username, password=password,
                                                               credential_name=saved_credential,
                                                               cloud_server_type=server_type)
            self._log.info("storage pool [%s] created successfully", storage_pool_name)
        else:
            self._log.info("storage pool [%s] already exists.", storage_pool_name)
            storage_pool_obj = self.commcell.storage_pools.get(storage_pool_name)
        library_details = storage_pool_obj.storage_pool_properties["storagePoolDetails"]["libraryList"][0]['library']
        library_obj = self.commcell.disk_libraries.get(library_details["libraryName"])
        return storage_pool_obj, library_obj

    def delete_storage_pool(self, storage_pool_name):
        """
        Deletes the storage pool if it exists

        Args:
            storage_pool_name (str)   --  storage pool name to delete

        Return:
            returns False -> if storage pool doesn't exist
            returns True -> if storage pool deleted succesfully

        Raises:
            SDK Exception
                if storage pool deletion fails
        """

        if (self.commcell.storage_pools.has_storage_pool(storage_pool_name)):
            self.commcell.storage_pools.delete(storage_pool_name)
            self._log.info(f"Storage pool [{storage_pool_name}] deleted successfully.")
            return True
        else:
            self._log.info(f"Storage pool [{storage_pool_name}] doesn't exist.")
            return False

    def delete_storage_policy(self, storage_policy_name):
        """
        Deletes the storage policy if it exists

        Args:
            storage_policy_name (str)   --  storage policy name to delete

        Return:
            returns False -> if storage policy doesn't exist
            returns True -> if storage policy deleted succesfully

        Raises:
            SDK Exception
                if storage policy deletion fails
        """

        if (self.commcell.storage_policies.has_policy(storage_policy_name)):
            self.commcell.storage_policies.delete(storage_policy_name)
            self._log.info(f"Storage policy [{storage_policy_name}] deleted successfully.")
            return True
        else:
            self._log.info(f"Storage policy [{storage_policy_name}] doesn't exist.")
            return False

    def enable_worm_storage_lock(self, storage_pool, retain_days):
        """
        Enable storage WORM lock on storage pool

        Args:
            storage_pool (str/StoragePool) -- storage pool to enable WORM

            retain_days (int) -- number of days of retention on WORM copy.

        Return:
            None
        """
        if isinstance(storage_pool, str):
            storage_pool = self.commcell.storage_pools.get(storage_pool)
        self._log.info("Enabling WORM on storage pool [%s]", storage_pool.storage_pool_name)
        # check if WORM is already enabled
        if storage_pool.is_worm_storage_lock_enabled:
            self._log.info("WORM is already enabled on storage pool [%s]", storage_pool.storage_pool_name)
        storage_pool.enable_worm_storage_lock(retain_days)
        self._log.info("WORM enabled on storage pool [%s]", storage_pool.storage_pool_name)

    def get_copy_store_seal_frequency(self, copy_obj):
        """Gets the store seal frequency for the copy

        Args:
            copy_obj (object) -- copy object for which store seal frequency is needed

        Returns:
            dict -- store seal frequency for the copy
                    Eg: {'size': 0, 'days': 2, 'months': 0}
        """
        self._log.info("Getting store seal frequency for the copy [%s]", copy_obj.copy_name)
        seal_frequency_dict = copy_obj.get_store_seal_frequency()
        self._log.info("Store seal frequency for the copy [%s] is: %s", copy_obj.copy_name, seal_frequency_dict)
        return seal_frequency_dict

    def configure_backupset(self,
                            backupset_name=None,
                            agent=None):
        """
        Creates a new backupset if not exits
        Args:
            backupset_name (str)   -- backupset name to create

        Return:
            (object)    -- Backupset object
        """
        # config backupset
        if backupset_name is None:
            backupset_name = self.backupset_name
        if agent is None:
            agent = self.agent
        self._log.info("check BS: %s", backupset_name)
        if not agent.backupsets.has_backupset(backupset_name):
            self._log.info("adding Backupset...")
            backupset = agent.backupsets.add(backupset_name)
            self._log.info("Backupset config done.")
            return backupset
        self._log.info("Backupset exists!")
        backupset = agent.backupsets.get(backupset_name)
        return backupset

    def configure_subclient(self,
                            backupset_name=None,
                            subclient_name=None,
                            storage_policy_name=None,
                            content_path=None,
                            agent=None):
        """
        Gets or creates the subclient using the config parameters

        Args:
            storage_policy_name (str)   -- storage policy name to associate with storage policy

            subclient_name (str)        -- subclient name to create

            backupset_name (str)        -- backupset name to create subclient under it

            content_path (str / list)   -- content(s) to add to subclient

        Return:
             (object)   -- Subclient object
        """
        # config subclient
        if backupset_name is None:
            backupset_name = self.backupset_name
        if subclient_name is None:
            subclient_name = self.subclient_name
        if storage_policy_name is None:
            storage_policy_name = self.storage_policy_name
        if content_path is None:
            content_path = self.content_path
        if agent is None:
            agent = self.agent
        self._log.info("check SC: %s", subclient_name)
        self._log.info("creating backupset object: " + backupset_name)
        self._backupset = agent.backupsets.get(backupset_name)
        if not self._backupset.subclients.has_subclient(subclient_name):
            self._log.info("adding Subclient...")
            self._subclient = self._backupset.subclients.add(subclient_name,
                                                             storage_policy_name)
        else:
            self._log.info("Subclient exists!")
        self._log.info("creating subclient object: %s", subclient_name)
        self._subclient = self._backupset.subclients.get(subclient_name)
        self._log.info("setting subclient content to: %s", [content_path])

        # add subclient content
        if not content_path or isinstance(content_path, str):
            self._subclient.content = [content_path]
        elif isinstance(content_path, list):
            self._subclient.content = content_path
        else:
            raise Exception(f"Invalid type for content_path: {type(content_path)}")

        # required when subclient exists but policy was deleted
        self._subclient.storage_policy = storage_policy_name

        self._log.info("Subclient config done.")
        return self._subclient

    def configure_secondary_copy(self,
                                 sec_copy_name,
                                 storage_policy_name=None,
                                 library_name=None,
                                 ma_name=None,
                                 global_policy_name=None,
                                 retention_period=30):
        """
        Creates a new secondary copy if doesnt exist
        Args:
            sec_copy_name: secondary copy name to create

            storage_policy_name (str)   -- storage policy name to create secondary copy

            library_name (str)          -- library to use for creating secondary copy

            ma_name (str)               -- MA name to use for library

            global_policy_name (str)    -- global storage policy to use for creating secondary copy

            retention_period (int)      -- days to retain data (default - 30)

        Return:
            (object)    -- secondary copy object
        """
        if storage_policy_name is None:
            storage_policy_name = self.storage_policy_name
        if library_name is None and global_policy_name is None:
            library_name = self.library_name
        if ma_name is None and global_policy_name is None:
            ma_name = self.tcinputs["MediaAgentName"]
        # create secondary copy
        self.sp = self.commcell.storage_policies.get(storage_policy_name)
        self._log.info("check secondary copy: %s", sec_copy_name)
        if not self.sp.has_copy(sec_copy_name):
            self._log.info("adding secondary copy...")
            self.sp.create_secondary_copy(sec_copy_name, library_name, ma_name, global_policy=global_policy_name,
                                          retention_days=retention_period)
            self._log.info("Secondary copy config done.")
            self.sec_copy = self.sp.get_copy(sec_copy_name)
            return self.sec_copy
        self._log.info("secondary copy exists!")
        self.sec_copy = self.sp.get_copy(sec_copy_name)
        return self.sec_copy

    def create_uncompressable_data(self, client, path, size, num_of_folders=1, file_size=0):
        """
        Creates unique uncompressable data

        Args:
            client  --  (str)   -- Client name on which data needs to be created

            path    --  (str)   --  Path where data is to be created

            size    --  (float) --  Data in GB to be created for each folder
                                    (restrict to one decimal point)

            num_of_folders -- (int) -- Number of folders to generate, each with given size

            file_size      -- (int) -- Size of Files to be generated in KB, Default: 0(Random Size)
        Returns:
              (boolean)
        """
        options_selector = OptionsSelector(self.commcell)
        return options_selector.create_uncompressable_data(client, path, size, num_of_folders, file_size=file_size)

    def execute_select_query(self, query):
        """ Executes CSDB select query

        Args:
            query (str) -- select query that needs to be run on CSDB

        Return:
            query response
        """
        self._log.info("Running query : \n{0}".format(query))
        self.csdb.execute(query)
        db_response = self.csdb.fetch_all_rows()
        self._log.info("RESULT: {0}".format(db_response))
        return db_response

    def unload_drive(self, library_name, drive_name):
        """
        Unloads the drive on the library given
        Args:
                library_name(str) -- Tape Library Name

                drive_name(str)   -- Drive Name
        """
        self._log.info("Unloading Drive %s on %s ", drive_name, library_name)
        self.commcell.execute_qcommand(f"qdrive unload -l '{library_name}' -dr '{drive_name}'")

    def remove_autocopy_schedule(self, storage_policy_name, copy_name):
        """
        Removes association with System Created Automatic Auxcopy schedule on the given copy
        Args:
                storage_policy_name (str)   -- storage policy name

                copy_name           (str)   --  copy name
        """
        if self.commcell.schedule_policies.has_policy('System Created Autocopy schedule'):
            auxcopy_schedule_policy = self.commcell.schedule_policies.get('System Created Autocopy schedule')
            association = [{'storagePolicyName': storage_policy_name, 'copyName': copy_name}]
            auxcopy_schedule_policy.update_associations(association, 'exclude')

    def ransomware_protection_status(self, client_id):
        """
        This function checks the state of ransomware protection

        Args:

            client_id(str) - ID of the client whose ransomware protection status you want to
                        know.

        Returns:

            True - if ransonware protection is enabled

            False - if ransomware protection is disabled
        """
        attrname = "'enableDLP'"
        version = str(self.commcell.clients.get(int(client_id)).service_pack)
        if int(version[:2]) >= 26:
            attrname = "'enableransomware'"

        query = f"""
                select  attrVal
                from    APP_ClientProp
                where   componentNameId={client_id} 
                and attrName = {attrname}
                """
        self._log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        result = int(self.csdb.fetch_one_row()[0])
        if result == 1:
            status = True
        elif result == 0:
            status = False
        return status

    def ransomware_driver_loaded(self, media_agent_name):
        """
        This function checks if the cvdlp driver is loaded or not
        on any of the possible volume under any instance.
        (Like - CVDLP.Encryption, CVDLP.Shredding)
        by executing cmd line fltmc instances command.

        Args:
            media_agent_name(str)   -- name of the media agent machine on
                                       which driver loaded to be checked.

        Returns:
                (bool)  -   True if the cvdlp driver is currently loaded
                            False if the cvdlp driver is currently not loaded

        """
        media_agent_machine = Machine(media_agent_name, self.commcell)
        if media_agent_machine.os_info.lower() != 'windows':
            raise Exception("Works for Windows OS only")

        cvdlp_driver_loaded = False
        output = media_agent_machine.execute_command("fltmc instances")
        for sub_list in output.formatted_output:
            if "CVDLP" in set(sub_list):
                cvdlp_driver_loaded = True
                self._log.info("cvdlp driver is loaded")
                break
        return cvdlp_driver_loaded

    def uncheck_high_latency(self, client):
        """
        It will uncheck the high latency option for client side cache
        Prevent unintentional enabling of high latency setting when using
        client side cache.
        Useful while writing certain testcases.
            - will mention if high latency option is not set
            - will mention if unchecking high latency option

        Args:
            client - client object for which you want to uncheck high latency

        Returns:
            None

        """
        self._log.info("checking for high latency optimisation option")
        query = """ select attrVal
                    from APP_ClientProp
                    where componentNameId={0}
                    and attrName='Optimize for High Latency Networks'""".format(client.client_id)
        self._log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()[0]
        if len(result) == 0:
            self._log.info("high latency option has not been set")
        elif int(result) == 1:
            self._log.info("high latency option has not been unchecked")
            # disable high latency for client side dedupe using q command
            xml = """<App_SetClientPropertiesRequest>
                    <association>
                    <entity>
                    <clientName>{0}</clientName>
                    </entity>
                    </association>
                    <clientProperties>
                    <clientProps>
                    <deDuplicationProperties>
                    <enableHighLatencyOptimization>False</enableHighLatencyOptimization>
                    </deDuplicationProperties>
                    </clientProps>
                    </clientProperties>
                    </App_SetClientPropertiesRequest>""".format(client.client_name)
            self._log.info("Running q command using xml for disabling high latency optimisation on client %s",
                           client.client_name)
            self.commcell.qoperation_execute(xml)
        self._log.info("High latency option is unchecked")

    def add_storage_pool_using_existing_library(self, storage_pool_name, library_name, media_agent, ddb_ma=None, dedup_path=None):
        """
                Adds a new storage pool to commcell using existing library

                Args:
                    storage_pool_name   (str)       --  name of new storage pool to add

                    library_name        (str)       --  library to be used while creating the storage pool

                    media_agent         (str/object)--  name or instance of media agent

                    ddb_ma              (list<str/object>/str/object)   --  list of (name of name or instance)
                                                                                or name or instance of dedupe media agent
                    dedup_path          (list<str>/str)       --  list of paths or path where the DDB should be stored


                Returns:
                    StoragePool object if creation is successful

                Raises:
                    Exception if creation is unsuccessful
                """
        return self.commcell.storage_pools.add(storage_pool_name, '', media_agent, ddb_ma, dedup_path, library_name = library_name)

    def submit_data_aging_job(self,
                              copy_name=None,
                              storage_policy_name=None,
                              is_granular=False,
                              include_all=True,
                              include_all_clients=False,
                              select_copies=False,
                              prune_selected_copies=False,
                              schedule_pattern=None):
        """
        This is a wrapper on run_data_aging function from commcell.py
        extra addition here is checking if data aging job is already running.
        If we see running job in csdb
        we will wait for 5 min for it to finish.
        (for a max period of 30min for existing job to finish else fail to launch new data aging job)

        Args:
            same args as needed in the main run_data_aging function from commcell.py
            copy_name   - (str)           name of the copy on which you want to run data aging.
            storage_policy_name - (str)   name of the storage policy on which you want to run data aging.
            is_granular - (bool)          If you want to run data aging on selected specific data.
            include_all - (bool)          If you want to run data aging over all data.
            include_all_clients - (bool)  If you need to age data for specific clients,
                                          set Include All Client to false.
            select_copies - (bool)        If you need to age data in specific storage policy copies.
            prune_selected_copies - (bool) This will prune the select copies in relation to above option.
            schedule_pattern    - (dict)   If needed mention the schedule pattern to be
                                           merged with the task request.

        Returns:
            job object

        Raises:
            Exception
                if the existing data aging job does not finish in the 30 min interval.
        """

        query = """ select  count(*) 
                    from    JMAdminjobInfoTable
                    where   opType=10"""
        self._log.info("EXECUTING QUERY %s", query)
        repeated = 0
        while True:
            self._log.info("check if there is an existing data aging job running")
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()[0]
            if result != '0' and repeated < 6:
                self._log.info("there is an existing data aging job running")
                self._log.info("wait for 5 mins")
                time.sleep(300)
                repeated += 1
            elif result == '0':
                self._log.info("no data aging job is running")
                self._log.info("launch data aging ")
                break
            elif repeated >= 6:
                raise Exception("existing data aging job did not finish in 30 min: check manually")

        data_aging_job = self.commcell.run_data_aging(copy_name, storage_policy_name, is_granular, include_all,
                                                      include_all_clients, select_copies, prune_selected_copies,
                                                      schedule_pattern)
        return data_aging_job

    def get_drive_pool(self, csdb, tape_library_name):
        """
        Returns the DrivePool(s) of the tape library

                    Args:
                        csdb (object)  --  CSDB database object
                        tape_library_name (string) - Name of the tape library

                    Returns:
                        dict (MediaAgent ID, DrivePool name) - dict of the DrivePool ID and name
        """

        query = "select dp.ClientId,dp.DrivePoolName from MMDrivePool dp  WITH (NOLOCK), MMMasterPool mp  WITH (NOLOCK), MMLibrary l  WITH (NOLOCK) where dp.MasterPoolId = mp.MasterPoolId and mp.LibraryId = l.LibraryId and l.AliasName='" + tape_library_name + "'"
        csdb.execute(query)
        rows = csdb.fetch_all_rows()
        drive_pools = {}
        for dp in rows:
            drive_pools[dp[0]] = dp[1]
        return drive_pools

    def get_master_pool(self, csdb, tape_library_name):
        """
            Returns the master pool of the tape library

                    Args:
                        csdb --  CSDB database object
                        tape_library_name (string) - Name of the tape library

                    Returns:
                        dict(MasterPool ID, MasterPool name) - dict of MasterPool ID and name
        """

        query = "select MasterPoolId, MasterPoolName from MMMasterPool mp  WITH (NOLOCK), mmlibrary l  WITH (NOLOCK) where mp.LibraryId=l.LibraryId and l.AliasName='{0}'".format(
            tape_library_name)

        csdb.execute(query)
        rows = csdb.fetch_all_rows()
        master_pools = {}
        for mp in rows:
            master_pools[mp[0]] = mp[1]
        return master_pools

    def update_mmconfig_param(self, param_name, nmin, value, **kwargs):
        """
        Update MM Config parameter value.

        Args:
            param_name  (str)   -   name of the MMConfig paramater
            nmin        (int)   -   minimum value of the parameter
            value       (int)   -   value to be set
            \*\*kwargs  (dict)  -  Optional arguments
            nmax        (int)   - maximum value of the parameter
        """
        nmax = kwargs.get('nmax', '')
        if nmax == '':
            query = f"update mmconfigs set nmin={nmin}, value={value} where name='{param_name}'"
        else:
            query = f"update mmconfigs set nmin={nmin}, nmax={nmax}, value={value} where name='{param_name}'"
        self._log.info("QUERY: %s", query)
        sql_password = commonutils.get_cvadmin_password(self.commcell)
        self.execute_update_query(query, sql_password, "sqladmin_cv")

    def enable_global_encryption(self, cipher=None, kms_name=None):
        """
        Enable Global Encryption settings on Commcell

        Args:
            cipher      (str)   -   represents the encryption algorithm and key length
                                    e.g. "AES_256"
                                    Use None to keep existing

                                    Supported ciphers:
                                    BLOWFISH_{128, 256}
                                    GOST_256
                                    AES_{128, 256}
                                    TWOFISH_{128, 256}
                                    SERPENT_{128, 256}
                                    DES3_192

            kms_name    (str)   -   The Key Management Server to use
                                    e.g. "Built-in"
                                    Use None to keep existing
        """
        config_list = [
            {"name": "DefaultEncryptionModeForPrimaryCopy", "value": "8388608"},
            {"name": "DefaultEncryptionModeForSecondaryCopy", "value": "8388608"},
            {"name": "DefaultDirectMediaAccessForNewCopies", "value": "1"},
            {"name": "PreventChangesToEncryptionSettings", "value": "1"},
            {"name": "PreventChangesToHardwareEncryptionSettings", "value": "0"},
            {"name": "DefaultHardwareEncryption", "value": "0"},
        ]
        if cipher is not None:
            config_cipher = {"name": "DefaultEncryptionForNewCopies", "value": cipher}
            config_list.append(config_cipher)

        if kms_name is not None:
            config_kms = {"name": "DefaultKeyProviderForNewCopies", "value": kms_name}
            config_list.append(config_kms)

        self.commcell._set_gxglobalparam_value(config_list)

    def disable_global_encryption(self):
        """Disable Global Encryption settings on Commcell"""

        config_list = [
            {"name": "DefaultEncryptionModeForPrimaryCopy", "value": "1048576"},
            {"name": "DefaultEncryptionModeForSecondaryCopy", "value": "1048576"},
            {"name": "PreventChangesToEncryptionSettings", "value": "0"},
            {"name": "PreventChangesToHardwareEncryptionSettings", "value": "0"},
            {"name": "DefaultHardwareEncryption", "value": "0"},
        ]
        self.commcell._set_gxglobalparam_value(config_list)

    def getDeletedAFcount(self, storeID):
        """
        get the count for entries belonging to a particular store in mmdeletedAF.

        Args:
            storeID     - (int)
                          SIDB store ID for which entries in mmdeletedAF are to be checked.

        Returns:
            result      - (int)
                          count of entries for SIDBStoreID in MMDeletedAF table

        """
        query = f"select count(*) from MMDeletedAF where SIDBStoreId ={storeID} and CommCellId=2"
        self._log.info("EXECUTING QUERY: %s", query)
        self.csdb.execute(query)
        result = int(self.csdb.fetch_one_row()[0])
        return result

    def get_chunks_for_job(self, job_id, copy_id=None, afile_type=None, log_query=False, order_by=0):
        """Fetches the Details of Chunks Created by the Job

            Args:
                job_id  (str or int): Id of the Job

                copy_id (str or int): Id of the Copy

                afile_type (int)    : Type of AFs to be filtered

                log_query (bool)    : (True/False)Log the query used

                order_by  (int)     : Refer to enum below
            Returns:
                (list): List of Details of Chunks created by given job
                Ex: [['A:\MP1', 'XYZBARCODE', 'V_123', '123']]
        """
        order_by_enum = {1: 'AC.id', 2: 'AC.id Desc', 3: 'AF.id', 4: 'AF.id Desc',
                         5: 'ACM.physicalSize', 6: 'ACM.physicalSize Desc', 7: 'ACM.archCopyId',
                         8: 'ACM.archCopyId desc', 9: 'MP.MountPathId', 10: 'MP.MountPathId Desc',
                         11: 'MV.VolumeId', 12: 'MV.VolumeId Desc'}

        afile_type = f'and AF.fileType = {afile_type}' if afile_type else ''
        copy_id = f'and ACM.archCopyId = {copy_id}' if copy_id else ''
        order_by = f'order by {order_by_enum[order_by]}' if order_by else ''
        query = f'''select
                    Folder, MP.MountPathName, MV.VolumeName, AC.id
                from
                    archFile AF, archChunkMapping ACM, archChunk AC, MMVolume MV, MMMountPath MP,
                    MMMountPathToStorageDevice MSD, MMDeviceController MDC
                where
                    AF.jobId = {job_id}
                    {afile_type}
                    and AF.id = ACM.archFileId
                    {copy_id}
                    and ACM.archChunkId = AC.id
                    and AC.volumeId = MV.VolumeId
                    and MV.CurrMountPathId = MP.MountPathId
                    and MP.MountPathId = MSD.MountPathId
                    and MSD.DeviceId = MDC.DeviceId
                {order_by}'''
        if log_query:
            self._log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        query_results = self.csdb.fetch_all_rows()
        self._log.info('Chunks for Job-%s: %s', job_id, str(query_results))
        return query_results

    def get_bad_chunks(self, store_id=None, job_id=None, log_chunks=False):
        """Get chunks from archChunkDDBDrop which were marked bad

        Args:
            store_id (int or str): Store ID filter to get bad chunks of provided store only

            job_id (int or str): Job ID filter to get chunks marked bad by provided job only

            log_chunks (bool): True/False whether or not to log the details of chunks
        Returns:
            (list): A List of [chunkId,storeId,jobId] that were marked bad
        """
        self._log.info("checking for bad chunks marked on store[%s] by job[%s]", store_id, job_id)
        if store_id:
            store_id = f"SIDBStoreId = {store_id}"
        if job_id:
            job_id = f"reserveInt = {job_id}"

        # query formatting: add 'where' clause if either of store or job ids were provided
        # then add 'and' clause if both store and job ids were provided
        query = f"""select archChunkId, SIDBStoreId, reserveInt
                from archChunkDDBDrop WITH (NOLOCK)
                {'where' if (store_id or job_id) else ''}
                {store_id if store_id else ''}{' and ' if (store_id and job_id) else ''}{job_id if job_id else ''}"""
        self._log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        if not result[0][0]:
            result = []  # no entries returned case
        self._log.info("RESULT (Bad chunks count): %s", len(result))
        if log_chunks:
            self._log.info("[[archChunkId, SIDBStoreId, jobId]]: %s", str(result))
        return result

    def get_source_ma_id_for_auxcopy(self, job_id):
        """
        Get id of the source media agent of an aux copy job
        Args:
            job_id (int) -- aux copy job id to query the table
        Return:
            (list) -- list of ids of the source media agent
        """
        query = f"""
        SELECT Distinct(SrcMAId)
        FROM HistoryDB.dbo.archJobStreamStatusHistory WITH (NOLOCK)
        WHERE JobId = {job_id}
        """
        self._log.info(f"Executing Query: {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        source_media_agent = [int(x[0]) for x in res]
        self._log.info(f"RESULT: Source Media Agent ID: {source_media_agent} for job ID: {job_id}")
        return source_media_agent

    def set_encryption(self, storage_policy_copy_object):
        """
        This method is to set encryption using random Cipher and key length.
        Please use SDK method StoragePolicyCopy.set_encryption_properties() to set encryption with provided Cipher and length.

        Args:
            storage_policy_copy_object (Object) - Object of StoragePolicyCopy class
        """
        self._log.info(
            f"Setting encryption on copy[{storage_policy_copy_object.copy_name}] of Storage Policy/Pool [{storage_policy_copy_object.storage_policy.storage_policy_name}]")
        enc_list = ["Blowfish", "TwoFish", "Serpent", "AES", "DES", "GOST"]
        enc_key = [128, 256]

        enc_cipher = random.choice(enc_list)
        enc_length = None
        if enc_cipher == "DES":
            enc_length = 192  # DES supports only 192 key length
        elif enc_cipher == "GOST":
            enc_length = 256  # GOST supports only 256 key length
        else:
            enc_length = random.choice(enc_key)

        self._log.info(f"Selected Cipher is [{enc_cipher}] and key length is [{enc_length}]")
        storage_policy_copy_object.set_encryption_properties(re_encryption=True,
                                                             encryption_type=enc_cipher,
                                                             encryption_length=enc_length)
        self._log.info("Successfully set the encryption")

    def get_mount_path_name(self, library_id):
        """
        returns unique mount path name on the library.

        Args:
            library_id     (str): library id of the library mountpath is created on.
        Returns:
            mount path name (list): list of unique mount path names on library.
        """
        query = f"""
        select MP.MountPathName from MMMountPath MP
        where MP.LibraryId = {library_id}
        """
        self._log.info(f"Executing Query: {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        mount_paths = [x[0] for x in res]
        self._log.info(f"Mount Path: {mount_paths}")
        return mount_paths

    def restart_mm_service(self):
        """ Restarts the Media Manager service """
        self._log.info("Restarting Media Manager service")
        if 'windows' in self.commcell.commserv_client.os_info.lower():
            self._log.info(f"Platform Detected : {self.commcell.commserv_client.os_info}")
            self.commcell.commserv_client.restart_service("GXMLM(Instance001)")
        elif 'unix' in self.commcell.commserv_client.os_info.lower():
            self._log.info(f"Platform Detected : {self.commcell.commserv_client.os_info}")
            self.commcell.commserv_client.restart_service("MediaManager")
        self._log.info("Restart completed")

    def edit_mountpath_properties(self,
                                  mountpath,
                                  library_name,
                                  media_agent,
                                  **kwargs):
        """
        Edit the properties of a mount path for a storage library.

        Args:
            mountpath (str): The mount path to edit.
            library_name (str): The name of the storage library.
            media_agent (str): The name of the media agent.
            **kwargs: Additional keyword arguments to customize the mount path properties.

        Keyword Args:
            num_writers_for_mp (str): The number of writers for the mount path.
                                      Range 1 to 999.

            reserve_space_mb (str): The total amount of free space that must be available at all times when the system
                                    writes data to the mount path.

            reserv_space_for_silo_restores (str): The amount of space to reserve for silo restores.
                    Values: 0 -> disables space reservation for SILO restores.
                            1 -> enables space reservation for SILO restores.

            enable_pruning_of_aged_data (str): Flag to enable pruning of aged data.
                    Values: 0 -> disables pruning of aged data.
                            1 -> enables pruning of aged data.

            use_dp_settings_for_pruning (str): Flag to use DP settings for pruning.
                    Values: 0 -> pruning request is sent to any MediaAgent that has access to the library
                            1 -> the pruning request is sent to only the MediaAgents associated with the data paths
                            in the storage policy copy.


        Returns:
            None

        """
        num_writers_for_mp = kwargs.get('num_writers_for_mp', "-2")
        reserve_space_mb = kwargs.get('reserve_space_mb', "")
        reserv_space_for_silo_restores = kwargs.get('reserv_space_for_silo_restores', "2")
        enable_pruning_of_aged_data = kwargs.get('enable_pruning_of_aged_data', "2")
        use_dp_settings_for_pruning = kwargs.get('use_dp_settings_for_pruning', "2")
        self._log.info(f"Editing mountpath properties for library: {library_name} and mountpath: {mountpath}")
        request_json = {
            "EVGui_ConfigureStorageLibraryReq":
                {
                    "library": {
                        "opType": 8,
                        "mediaAgentName": media_agent,
                        "libraryName": library_name,
                        "mountPath": mountpath
                    },
                    "libNewProp": {
                        "numOfWritersForMountpath": num_writers_for_mp,
                        "reserveSpaceInMB": reserve_space_mb,
                        "resrvSpaceForSiloRestores": reserv_space_for_silo_restores,
                        "enablePruningOfAgedData": enable_pruning_of_aged_data,
                        "useDPSettingsForPruning": use_dp_settings_for_pruning
                    }
                }
        }

        self.commcell.qoperation_execute(request_json)
        self._log.info("Successfully modified mountpath properties ")

    def __change_archGroupCopyUpgTrigger_state(self, action, sql_username=None, sql_password=None):
        """
            disables/enables trigger ArchGroupCopyUpgTrigger on table archgroupcopy

            Args:

                action : DISABLE/ENABLE

                sql_username: username for connecting to csdb (mandatory in case of Tenant Admin)

                sql_password: password for connecting to csdb (mandatory in case of Tenant Admin)

        """

        query = """{0} TRIGGER ArchGroupCopyUpgTrigger ON archgroupcopy""".format(action)

        if sql_username and sql_password:
            self.utility.update_commserve_db(query=query, user_name=sql_username, password=sql_password)
        else:
            self.utility.update_commserve_db(query=query)

    def validate_trigger_status(self, trigger_name, table_name, disabled=False):
        """
            validates whether the trigger is disabled or not on a table

            Args:

                trigger_name: name of the trigger

                table_name: name of the table to which trigger is associated

                disabled: False (by default), true (to check if enabled)

        """

        query = """SELECT t.name AS trigger_name, t.is_disabled FROM sys.triggers t JOIN sys.tables tbl ON
                    t.parent_id = tbl.object_id WHERE tbl.name = '{1}' and t.name = '{0}'
                """.format(trigger_name, table_name)

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)

        if disabled:
            if cur[1] == 'true':
                self._log.info(f"****{trigger_name} got disabled successfully****")
            else:
                raise Exception(f"Error: {trigger_name} does not got disabled. Check logs for details")

        else:
            if cur[1] == 'false':
                self._log.info(f"****{trigger_name} got enabled successfully****")
            else:
                raise Exception(f"Error: {trigger_name} does not got enabled. Enable it manually and check "
                                "logs for details")

    def __unset_compliance_lock_flags(self, copy_id):
        """
            updates the primary and dependent copy lock flags

            Args:
                copy_id : id of the copy

        """

        worm_copy_flag = 16777216
        override_retention_flag = 2048
        auxcopy_policy_flag = 1
        host_global_dedup_store_flag = 268435456
        global_storage_policy_flag = 4096

        self._log.info("***** Updating the flags of primary copy ******")
        update_primary_query = """UPDATE  archGroupCopy SET  flags = flags & ~({0}) WHERE Id = {1}
                                  AND (flags & ({0})) <> 0""".format(worm_copy_flag, copy_id)

        response = self.utility.update_commserve_db(query=update_primary_query)
        self._log.info(f"Result: {response.rowcount} rows got updated")

        self._log.info("***** Updating the dependent copy flags *****")
        update_dep_copy = """UPDATE AGC_Dep
                            SET flags = (AGC_Dep.flags & ~({0}))
                            FROM archGroupCopy AGC_Dep
                            INNER JOIN archGroup AG_Dep WITH(READUNCOMMITTED) ON AGC_Dep.archGroupId = AG_Dep.id
                            INNER JOIN archCopyToGlobalPolicy G WITH (READUNCOMMITTED) ON G.copyId = AGC_Dep.Id
                            INNER JOIN archGroupCopy AGC_Global WITH (READUNCOMMITTED) ON AGC_Global.archGroupId = G.globalPolicyId
                            WHERE AGC_Dep.flags & ({0}) > 0
                            AND AGC_Dep.extendedFlags & {2} = 0
                            AND AGC_Dep.isSnapCopy = 0
                            AND AGC_Global.Id = {1} AND
                            ((AGC_Global.extendedFlags & {3} ) <> 0 OR
                            (AGC_Global.dedupeFlags & {4} ) <> 0 OR
                            (AGC_Global.extendedFlags & {5} ) <> 0 )""".format(worm_copy_flag, copy_id,
                                                                               override_retention_flag,
                                                                               auxcopy_policy_flag,
                                                                               host_global_dedup_store_flag,
                                                                               global_storage_policy_flag)

        response = self.utility.update_commserve_db(query=update_dep_copy)
        self._log.info(f"Result: {response.rowcount} rows got updated")

    def check_copy_association_to_AGP(self, copy_id):
        """
            check whether copy is associated to AGP (Air Gap Protect) or not

            Args:
                copy_id : id of the copy

            Returns:
                bool (True/False)

        """

        remote_host_metallic_start = 400
        remote_host_metallic_end = 499
        query = """SELECT 1
                 FROM archGroupCopy AGC WITH (READUNCOMMITTED)
                 INNER JOIN MMDataPath MD WITH (READUNCOMMITTED) ON MD.CopyId = AGC.id
                 INNER JOIN MMDrivePool MDP WITH (READUNCOMMITTED) ON MDP.DrivePoolId = MD.DrivePoolId
                 INNER JOIN MMMountPath MP WITH (READUNCOMMITTED) ON MP.MasterPoolId = MDP.MasterPoolId
                 INNER JOIN MMMountPathToStorageDevice MS WITH (READUNCOMMITTED) ON MS.MountPathId = MP.MountPathId
                 INNER JOIN MMDevice D WITH (READUNCOMMITTED) ON MS.DeviceId = D.DeviceId
                 WHERE (D.DisplayDeviceTypeId BETWEEN {0} AND {1}) AND AGC.id = {2}""".format(
            remote_host_metallic_start,
            remote_host_metallic_end,
            copy_id)

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)
        if cur[0] and int(cur[0]) == 1:
            self._log.info("***** Copy is associated to AGP Pool *****")
            return True

        self._log.info("***** Copy is not associated to AGP Pool *****")
        return False

    def can_disable_compliance_lock(self, copy_id):
        """
            method to check whether the copy is eligible to disable compliance lock or not

            Args:
               copy_id: id of the copy

            Returns:
                bool (True/False)

        """

        worm_copy_flag = 16777216
        override_retention_flag = 2048

        self._log.info("Checking if, copy id is enabled with compliance lock or not")
        query = """SELECT 1 FROM archGroupCopy WHERE id = {0} AND (flags & {1} = 0)""".format(copy_id, worm_copy_flag)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)

        if cur[0] and int(cur[0]) == 1:
            self._log.info("Error: Copy id is NOT enabled with compliance lock")
            return False
        self._log.info("Copy id is enabled with compliance lock")

        self._log.info("Checking if, compliance lock can be disabled on copy directly or not")
        query = """ SELECT 1 FROM archGroupCopy AGC WITH (READUNCOMMITTED)
                    INNER JOIN archCopyToGlobalPolicy ACGP WITH (READUNCOMMITTED) ON AGC.id = ACGP.copyId
                    INNER JOIN archGroup Global WITH (READUNCOMMITTED) ON ACGP.globalPolicyId = Global.id
                    INNER JOIN archGroupCopy GlobalCopy WITH (READUNCOMMITTED) ON Global.defaultCopy = GlobalCopy.id
                    WHERE AGC.id = {0} AND (AGC.extendedFlags & {1} = 0)
                    AND (GlobalCopy.flags & {2}> 0) """.format(copy_id, override_retention_flag, worm_copy_flag)

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)

        if cur[0] and int(cur[0]) == 1:
            self._log.info("Error: Copy is using storage pool worm setting. Please disable using storage pool copy")
            return False

        self._log.info("Compliance lock can be disabled on copy directly")
        return True

    def _set_worm_mmtask_within_24_hours(self, copy_id):
        """
            Making an entry in MMTASK table to set worm within 24 hours

            Args:
                copy_id - id of the copy

        """

        mmGetSetMMTask_INSERT = 0
        mmTaskType_to_enable_compliance_lock = 10
        query = """DECLARE @copyXml XML
                    DECLARE @now BIGINT = dbo.GetUnixTime(GETUTCDATE())
                    DECLARE @MMTaskDetailsCleanup_ResetWormCopyToRegularCopy TABLE(TaskId int, TaskType int, metaData XML, retryCount int)
                    SELECT @copyXml = (SELECT {0} AS '@copyId' FOR XML PATH('CvEntities_StoragePolicyCopyEntity'), TYPE)
                    DECLARE @pauseTillTime BIGINT = @now + 60 * ISNULL((SELECT value FROM GXGlobalParam WITH (READUNCOMMITTED)
                    WHERE name ='ReEnableWORMOnMRRCopyIntervalInMins'), (24 * 60) /*24 hours*/)

                    INSERT INTO @MMTaskDetailsCleanup_ResetWormCopyToRegularCopy
                    EXEC dbo.MMGetSetMMTask {1}, 0, {2}, @copyXml, @pauseTillTime """.format(copy_id,
                                                                                             mmGetSetMMTask_INSERT,
                                                                                             mmTaskType_to_enable_compliance_lock)

        response = self.utility.update_commserve_db(query=query)
        self._log.info(f"{response.rowcount} rows got inserted.")

    def _disable_compliance_lock_via_api(self, copy_id):
        """
             method to disable compliance lock via api

            Args:
                copy_id: id of the copy

        """
        query = """SELECT AG.name as StoragePolicyName , AGC.name as CopyName
                    FROM archGroupCopy AGC INNER JOIN archGroup AG
                    ON AGC.archGroupId = AG.id AND AGC.id = {0}""".format(copy_id)

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)

        storage_policy_name = cur[0]
        copy_name = cur[1]
        storage_policy_obj = self.commcell.storage_policies.get(storage_policy_name=storage_policy_name)
        copy_obj = storage_policy_obj.get_copy(copy_name=copy_name)
        self._log.info(f"*****Disabling compliance lock on copy {copy_name} defined on {storage_policy_name}*****")
        copy_obj.disable_compliance_lock()
        self._log.info(f"*****Disabled compliance lock on copy{copy_name} defined on {storage_policy_name}*****")

    def _disable_compliance_lock_via_db_query(self, copy_id, sql_username=None, sql_password=None):
        """
            method to disable compliance lock via db query

            Args:
                copy_id: id of the copy

                sql_username: username for connecting to csdb (mandatory in case of Tenant Admin)

                sql_password: password for connecting to csdb (mandatory in case of Tenant Admin)

        """

        self._log.info("***** Disabling Trigger ArchGroupCopyUpgTrigger *****")
        self.__change_archGroupCopyUpgTrigger_state(action='DISABLE', sql_username=sql_username,
                                                    sql_password=sql_password)
        self.validate_trigger_status(disabled=True, trigger_name='ArchGroupCopyUpgTrigger',
                                     table_name='archGroupCopy')

        self._log.info("***** Updating the flags to unset compliance lock *****")
        self.__unset_compliance_lock_flags(copy_id)

        self._log.info("***** Enabling Trigger ArchGroupCopyUpgTrigger *****")
        self.__change_archGroupCopyUpgTrigger_state(action='ENABLE')
        self.validate_trigger_status(trigger_name='ArchGroupCopyUpgTrigger', table_name='archGroupCopy')

        self._log.info("***** Checking if copy is associated to AGP pool *****")
        if self.check_copy_association_to_AGP(copy_id=copy_id):
            self._log.info("***** Making an entry in MMTASK table to set worm within 24 hours *****")
            self._set_worm_mmtask_within_24_hours(copy_id=copy_id)

    def disable_compliance_lock(self, copy_id, sql_username=None, sql_password=None):
        """
            method to unset compliance lock

            Args:

                copy_id: id of the copy

                sql_username: username for connecting to csdb (mandatory in case of Tenant Admin)

                sql_password: password for connecting to csdb (mandatory in case of Tenant Admin)

        """

        self._log.info("Checking if, copy id exist or not")
        query = """SELECT * from archGroupCopy where id = {0}""".format(copy_id)
        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)
        if not cur[0]:
            raise Exception("Raising error: Copy id does not exist. Provide valid copy Id")

        if self.can_disable_compliance_lock(copy_id=copy_id):
            self._log.info("Copy Id is eligible for disabling compliance lock")
            cs_oem_id = int(self.commcell.commserv_oem_id)
            # check whether CS is a commvault OEM or Metallic OEM
            if cs_oem_id == 1:
                self._log.info("*******Provided CS is a Commvault OEM*******")
                self._disable_compliance_lock_via_db_query(copy_id=copy_id, sql_username=sql_username,
                                                           sql_password=sql_password)

            else:
                self._log.info("*******Provided CS is a Metallic OEM*******")
                self._disable_compliance_lock_via_api(copy_id=copy_id)

        else:
            raise Exception("Raising error: Copy Id passed is NOT eligible for disabling compliance lock.")

    def wait_for_online_status_air_gap_protect(self, air_gap_protect_obj, wait_time=2, total_attempts=15):
        """Waits until Air Gap Protect storage is fully configured; i.e.; Status changes to 'Online'

            Args:
                air_gap_protect_obj     (object) - air gap protect storage pool object

                wait_time               (int)   - Number of minutes to wait before next attempt

                total_attempts          (int)   - Total number of attempts before raising error

            Raises:
                Exception   - if status not changed to online in specified attempts
        """

        air_gap_protect_obj.refresh()
        status = air_gap_protect_obj.storage_pool_properties["storagePoolDetails"]["libraryList"][0]['status']
        self._log.info('status: %s' % status)
        for attempt in range(0, total_attempts):

            if "ready" in status.lower():
                break

            self._log.info('Attempt: [%s/%s]; Waiting for %s minutes' % (attempt + 1, total_attempts, wait_time))
            time.sleep(60 * wait_time)

            air_gap_protect_obj.refresh()
            status = air_gap_protect_obj.storage_pool_properties["storagePoolDetails"]["libraryList"][0]['status']
            self._log.info('status: %s' % status)

        else:
            raise Exception('Failed to validate status after %s attempts' % total_attempts)

        self._log.info('Air Gap Protect storage is online [took: %s attempt(s)]' % attempt)


class CloudLibrary(object):
    '''Class for representing CloudLibrary'''

    def __init__(self, libraryname, libraryinfo):
        '''Class for representing CloudLibrary
        Args:
                libraryname  (str)         --  name of the cloud library
                libraryinfo  (dictionary)   --  dictionary containing library information

            Returns:
                None

            Raises:
                None
        '''
        self.libraryname = libraryname
        self.loginname = libraryinfo.get("loginName", "")
        self.secret_accesskey = libraryinfo.get("password", "")
        self.servertype = libraryinfo.get("serverType", "")
        self.mountpath = libraryinfo.get("mountPath", "")

    @staticmethod
    def cleanup_entities(commcell, log, entity_config):
        '''Method to cleanup commcell entities

        Args:
            entity_config (dict)   -- Dictionary containing the entity(s) as key,
                                        and value(s) as a list of the entities to delete.
        Returns:
            dictonary with failed entities

        Raises Exception:
            - If failed to delete any entity
        '''

        try:
            log.info("Start deleting entities configured")
            failed_entities = {"storagepolicy": [], "library": []}

            if 'storagepolicy' in entity_config:
                storageobj = commcell.policies.storage_policies
                storagepolies = entity_config['storagepolicy']

                for policy in storagepolies:
                    try:
                        storageobj.delete(policy)
                        log.info("successfully deleted SP {}".format(policy))
                    except Exception as err:
                        log.error(err)
                        failed_entities["storagepolicy"].append(policy)

            if 'library' in entity_config:
                storageobj = commcell.disk_libraries
                libraries = entity_config['library']

                for library in libraries:
                    try:
                        storageobj.delete(library)
                        log.info("successfully deleted library {}".format(library))
                    except Exception as err:
                        log.error(err)
                        failed_entities["library"].append(policy)

            return failed_entities

        except Exception as excp:
            raise Exception("Failed in cleanup_enties function with error {}".format(excp))


class PowerManagement(object):
    """" Class for power management helper functions"""

    def __init__(self, test_case_o=None):
        """
                init of PowerManagement  class

                Args:
                    test_case_o -- (Object) -- object of the TestCase class
        """
        self.log = logger.get_log()
        self.test_case_obj = test_case_o

    def configure_cloud_mediaagent(self, pseudo_client_name, ma_obj):
        """
                Setup and configure cloud MediaAgent

                Args:
                    psudo_client_name -- (str) -- To be used as cloud controller for the MediaAgent
                    ma_obj -- (MediaAgent class object) -- MediaAgent class Object of the MA to configure
        """

        self.log.info("Verifying power management configurations of MediaAgent [%s] ", ma_obj._media_agent_name)
        if ma_obj._is_power_mgmt_supported:
            self.log.info("Power Management supported")
            if ma_obj._is_power_management_enabled:
                self.log.info("Power management is enabled")
                if ma_obj._power_management_controller_name == pseudo_client_name:
                    self.log.info("MA is using correct cloud controller[%s] ", pseudo_client_name)
                else:
                    self.log.info("MA is not using correct cloud controller. Correcting that")
                    ma_obj.enable_power_management(pseudo_client_name)
            else:
                self.log.info("Power management is not enabled. Enabling that")
                ma_obj.enable_power_management(pseudo_client_name)
        else:
            raise Exception('Power management is not supported on MediaAgent ' + ma_obj._media_agent_name)

    def power_off_media_agents(self, list_of_media_agent_objects):
        """
        Power-off multiple MediaAgents simultaneously

                    Args:
                        list_of_media_agent_objects (list)  --  List of MediaAgent objects

                    Raises:
                           If number of MediaAgent object passed is less than 2
        """
        if type(list_of_media_agent_objects) != list:
            raise Exception(
                "A List of MediaAgent objects expected. At least 2 MediaAgent objects require. Use ma_obj.power_off() instead")

        thread_pool = []
        for media_agent in list_of_media_agent_objects:
            power_thread = threading.Thread(target=media_agent.power_off)
            self.log.info("Starting power-off thread. MediaAgent : {0}".format(media_agent._media_agent_name))
            power_thread.start()
            thread_pool.append(power_thread)

        self.log.info("Waiting for all MediaAgents to power-off")

        for power_thread in thread_pool:
            power_thread.join()

        self.log.info("All power-off thread(s) exited. Checking the status of each MA")

        for media_agent in list_of_media_agent_objects:
            if media_agent.current_power_status != "Stopped":
                self.log.error("The expected power status is not achieved within expected time. MediaAgent [%s]",
                               media_agent._media_agent_name)
                raise Exception('The expected power status is not achieved within expected time')
            else:
                self.log.info("MediaAgent [%s] is powered-off successfully", media_agent._media_agent_name)

        self.log.info("All MediaAgents are powered-off successfully")

    def power_on_media_agents(self, list_of_media_agent_objects):
        """
        Power-on multiple MediaAgents simultaneously

                    Args:
                        list_of_media_agent_objects (list)  --  List of MediaAgent objects

                    Raises:
                           If number of MediaAgent object passed is less than 2
        """
        if type(list_of_media_agent_objects) != list:
            raise Exception(
                "A List of MediaAgent objects expected. At least 2 MediaAgent objects require. Use ma_obj.power_on() instead")

        thread_pool = []
        for media_agent in list_of_media_agent_objects:
            power_thread = threading.Thread(target=media_agent.power_on)
            self.log.info("Starting power-on thread. MediaAgent : {0}".format(media_agent._media_agent_name))
            power_thread.start()
            thread_pool.append(power_thread)

        self.log.info("Waiting for all MediaAgents to power-on")

        for power_thread in thread_pool:
            power_thread.join()

        self.log.info("All power-on thread(s) exited. Checking the status of each MA")

        for media_agent in list_of_media_agent_objects:
            if media_agent.current_power_status != "Online":
                self.log.error("The expected power status is not achieved within expected time. MediaAgent [%s]",
                               media_agent._media_agent_name)
                raise Exception('The expected power status is not achieved within expected time')
            else:
                self.log.info("MediaAgent [%s] is powered-on successfully", media_agent._media_agent_name)

        self.log.info("All MediaAgents are powered-on successfully")

    def get_time_to_power_off(
            self, media_agent_id=None, last_activity_time=None, log_check_retry=5
    ):
        """
        This method fetches time to power-off from log
        :param media_agent_id: ID MediaAgent
        :param last_activity_time: last activity time of this MediaAgent. The log line will check checked after this time
        :param log_check_retry: number of rety count to check the log
        :return: returns the time remaining to power-off fetcjed from log
        """
        self.log.info("Fetching time to power off from log")
        if media_agent_id is None or media_agent_id.isnumeric() is not True:
            raise Exception("Invalid MediaAgent ID")

        if self.test_case_obj is None:
            self.log.error("Require test case class object")
            raise Exception("Require test case class object")

        matched_line = None

        dedupe_helper = DedupeHelper(self.test_case_obj)

        while matched_line is None and log_check_retry > 0:
            self.log.info(
                "Will wait for 2 minutes so that cloud MA idle time count down starts"
            )
            time.sleep(120)

            ptrn = f"MLMCloudVMManagement::SendPowerOFFReqToCloudVMs() - Cloud VM[{media_agent_id}] will power off after"
            date_ptrn = f"^[0-9]+\s+[A-Za-z0-9]+\s+(\d+)\/(\d+)\s(\d+):(\d+):(\d+) #* MLMCloudVMManagement::SendPowerOFFReqToCloudVMs\(\) - Cloud VM\[{media_agent_id}\] will power off after \[(\d+)\] mins\."

            self.log.info("Searching for the following pattern for idle time log line")
            self.log.info(ptrn)
            (matched_line, matched_string) = dedupe_helper.parse_log(
                self.test_case_obj.commcell.commserv_name,
                "MediaManager.log",
                ptrn,
                escape_regex=True,
                single_file=True,
            )

            if matched_line is not None:
                self.log.info("Following are the matched lines")
                for l in matched_line:
                    self.log.info(l)

                self.log.info("Searching for the following pattern")
                self.log.info(date_ptrn)
                self.log.info("Searching on the following line")
                self.log.info(matched_line[len(matched_line) - 1])
                res = re.search(date_ptrn, matched_line[len(matched_line) - 1])
                # time_to_off = re.search(r'(?:[, ])after \[(\d+)\]', matched_line[len(matched_line) - 1])

                if last_activity_time is not None:
                    self.log.info("Checking if the log line is after last activity time")
                    log_datetime = datetime(
                        int(datetime.now().year),
                        int(res.group(1)),
                        int(res.group(2)),
                        int(res.group(3)),
                        int(res.group(4)),
                        int(res.group(5)),
                        0,
                    )

                    if log_datetime > last_activity_time:
                        self.log.info(
                            "Validated that the log line is after the last activity."
                        )
                        return res.group(6)
                    else:
                        matched_line = None
                        self.log.info(
                            "Log line is NOT after the last activity time, will try to fetch the log again"
                        )
                        continue
                return res.group(6)
            log_check_retry = log_check_retry - 1

        raise Exception("Log line not found to get the time to power-off")

    def date_time_diff(self, first_datetime, second_date_time, format="m"):
        """
        Finds the difference between two dates in minutes or seconds
        :param first_datetime: datetime class object of first date time
        :param second_date_time: datetime object of second date time
        :param format: response will be in minutes if passed "m" else it will response in second. Default is in minutes
        :return: returns the difference between two dates in minutes or seconds
        """
        c = first_datetime - second_date_time
        if format == "m":
            return c.total_seconds() / 60
        else:
            return c.total_seconds()

    def verify_power_off_idle_time(
            self,
            media_agent_obj,
            last_activity_time=None,
            power_off_fail_tolerance=2,
            max_wait_minute=60,
    ):
        """
        This method verifies the idle time for power managed MA.
        :param media_agent_obj:
        :param last_activity_time:
        :param power_off_fail_tolerance:
        :param max_wait_minute:
        :return:
        """
        self.log.info("Started MediaAgent idle time validation")
        validation_started_on = datetime.now()
        res_csdb = None

        if not media_agent_obj.is_power_management_enabled:
            self.log.info("Power management is not enabled on this MediaAgent")
            raise Exception(
                f"Idle time verification failed as power management is not enabled on MediaAgent [{media_agent_obj.name}]"
            )

        while True:
            self.log.info(70 * "*")
            self.log.info(
                "**************** Starting idle time validation cycle ****************"
            )
            self.log.info(70 * "*")
            time_to_off = self.get_time_to_power_off(media_agent_obj.media_agent_id, last_activity_time)
            sleep_time = int(time_to_off) + 3
            self.log.info(
                f"Time to power-off is {time_to_off} minutes. Sleeping for {sleep_time} minutes"
            )
            time.sleep(sleep_time * 60)

            self.log.info("Checking if any power-off request submitted")

            sql_q = f"select top 1 ReqStartTime from MMVMPowerMgmtReq WITH(NOLOCK) where HostId={media_agent_obj.media_agent_id} and Flags&8=8 order by ReqStartTime desc"
            self.log.info("Executing the following query")
            self.log.info(sql_q)

            self.test_case_obj.csdb.execute(sql_q)

            req_start_time = None

            req_start_time = None if self.test_case_obj.csdb.fetch_one_row()[0] is [''] else \
                self.test_case_obj.csdb.fetch_one_row()[0]

            self.log.info(f"Power-off request start time ( as per DB): {datetime.fromtimestamp(int(req_start_time))}")

            if req_start_time == "" or req_start_time is None or (
                    validation_started_on > datetime.fromtimestamp(int(req_start_time))
            ):
                self.log.info(
                    f"No power-off request submitted after starting this validation on {validation_started_on}"
                )
            else:
                self.log.info(
                    f"Verified. Power-off request submitted after starting this validation on {validation_started_on}"
                )
                self.log.info("Waiting for MediaAgent to power-off")
                media_agent_obj.wait_for_power_status("Stopped")
                self.log.info("MediaAgent power-off completed successfully")
                if last_activity_time != None:
                    self.log.info(
                        f"Power-off submitted after {self.date_time_diff(first_datetime=datetime.fromtimestamp(int(req_start_time)), second_date_time=last_activity_time, format='m')} minutes from the last activity"
                    )
                    return True

            self.log.info(
                str(
                    f"Validation Time till now: {self.date_time_diff(datetime.now(), validation_started_on)}"
                )
            )
            self.log.info(f"Retry Count: {power_off_fail_tolerance}")
            if (
                    power_off_fail_tolerance > 0
                    or self.date_time_diff(datetime.now(), validation_started_on)
                    < max_wait_minute
            ):
                self.log.info(
                    f"Either power-off retry count or max wait time remaining, will continue validation"
                )
                power_off_fail_tolerance = power_off_fail_tolerance - 1
            else:
                self.log.info(
                    "MediaAgent not powered-off within max retry count and max wait time."
                )
                raise Exception(
                    "MediaAgent not powered-off within max retry count and max wait time."
                )

    def validate_powermgmtjobtovmmap_table(self, jobid, media_agent_id, csdb):
        """
        Validate the entry on MMPowerMgmtJobToVMMap table for the job and MediaAgent

            Args:
                        jobid --  Job ID that powered-on / powered-off the MediaAgent
                        media_agent_id -- MediaAgent ID that is powered-on / powered-off
                        csdb -- CSDB object to execute the query

        """
        self.log.info(
            "Validating entry on table MMPowerMgmtJobToVMMap for job {0} and host id {1}".format(jobid, media_agent_id))
        query = """select count(*)  
                from MMPowerMgmtJobToVMMap 
                where hostid={0} 
                and entityid={1}
                """.format(media_agent_id, jobid)

        csdb.execute(query)
        count = csdb.fetch_one_row()[0]
        self.log.info(
            "{0} entries found on table MMPowerMgmtJobToVMMap for job {1} and host id {2}".format(count, jobid,
                                                                                                  media_agent_id))
        if int(count) < 1:
            raise Exception(
                "Validation Failed. No entry found on table MMPowerMgmtJobToVMMap for job {0} and host id {1}".format(
                    jobid, media_agent_id))

        self.log.info("Successfully validated table MMPowerMgmtJobToVMMap for job {0} and host id {1}".format(jobid,
                                                                                                              media_agent_id))
