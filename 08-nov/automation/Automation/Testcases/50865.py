# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Note regarding sql credentials :

    In order to ensure security,
    sql credentials have to be passed to the TC via config.json file under CoreUtils/Templates

    populate the following fields in config file as required,
    "SQL": {
        "Username": "<SQL_SERVER_USERNAME>",
        "Password": "<SQL_SERVER_PASSWORD>"
    }

    At the time of execution the creds will be automatically fetched by TC.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    new_content()       -- generates data of specified size in given directory

    deallocate_resources()      -- deallocates all the resources created for testcase environment

    allocate_resources()        -- allocates all the necessary resources for testcase environment

    previous_run_cleanup()      -- for deleting the left over backupset and storage policy from the previous run

    get_active_files_store()    --  get store object to be used for adding more partitions etc

    run_backup_job()        -- for running a backup job of given type

    fetch_chunk()   --  return a list of chunk id, volume id pairs for a given job id

    delete_job()       -- deletes all the jobs whose job ids are given in argument list

    run_data_aging()    --  run granular data aging job for the given copy

    get_deleted_af_ids()      -- gets the count of mmdeleteaf entries for a given store

    chunk_exist()   --  does an exist check on supplied chunk directories

    check_error_codes()     -- checks whether all entries in mmdeleteaf contain the user specified error code

    add_op_window_for_pruning() -- adds pruning blackout window

    modify_op_window()  -- modifies existing pruning blackout window

    delete_op_window()  -- deletes pruning blackout window

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase check whether Op Window for Pruning functions as expected.

Prerequisites: None

Input JSON:

"50865": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "mount_path": "<path where the data is to be stored>" (optional argument),
        "matimezone": "pytz timezone of the linux mediaagent" (only applicable to linux ma), ex: US/Eastern, can get
        full list of available timezones by typing pytz.all_timezones (after importing pytz)
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. run two full backups
2. set op window for pruning on ma with starttime 1 hour before current time and endtime 1 hour after current time
3. verify data pruning op window added correctly with registry check and csdb
4. set pruneprocessinterval to 2 mins temporarily
5. delete the 2 jobs on the store
6. get list of AFs in mmdeletedaf from pruning
7. sleep to wait for 10 min prune process interval, otherwise mm will block next pruning request
8. run data aging
9. verify mmdeletedaf af list is same as it was before dataaging
11. run data forecast report
12. verify AFs in mmdeletedaf get updated with the op window failureerrorcode (65128)
13. edit data pruning op window so starttime is 2 hours after current time and endtime is 3 hours after current time
14. verify data pruning op window modified correctly with csdb
15. sleep to wait for 3 min prune process interval
16. run data aging
17. check for mmdeletedaf entries being removed
18. delete data pruning op window
19. verify its gone from app_opwindowrule table and registry
20. set pruneprocessinterval back to 60 mins

"""
import calendar
from time import sleep
from datetime import datetime, date
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils import config
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "OP Pruning Window Case"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.client_group = None
        self.client_group_name = None
        self.client_group_id = None
        self.mount_path = None
        self.dedup_store_path_base = None
        self.content_path = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.sidb_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.sql_username = None
        self.sql_password = None
        self.media_agent = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_pool = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.midnight_timestamp_int = None
        self.starttime = None
        self.endtime = None
        self.rule_id = None
        self.store_obj = None
        self.partition_paths = None

    def setup(self):
        """Setup function of this test case"""

        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent)[:] + "_" + str(self.client.client_name)[:]

        self.client_group_name = "{0}_CG{1}".format(str(self.id), suffix)
        self.storage_pool_name = "{0}_POOL{1}".format(str(self.id), suffix)
        self.storage_policy_name = "{0}_SP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_machine = Machine(self.media_agent, self.commcell)

        # create client content path
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        # create mediaagent mountpath
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)
        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
        else:
            self.mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, "mount_path")

        # create mediaagent dedup path
        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path_base = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path_base = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")
        self.partition_paths = []
        self.partition_paths.append(self.media_agent_machine.join_path(self.dedup_store_path_base, "partition_0"))

        # sql connections
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

    def new_content(self, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        returns None
        """
        if self.client_machine.check_directory_exists(dir_path):
            self.client_machine.remove_directory(dir_path)
        self.client_machine.create_directory(dir_path)
        self.opt_selector.create_uncompressable_data(client=self.client_machine,
                                                     size=dir_size,
                                                     path=dir_path)

    def deallocate_resources(self):
        """
        removes all resources allocated by the Testcase
        """
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")
        if self.commcell.client_groups.has_clientgroup(self.client_group_name):
            self.commcell.client_groups.delete(self.client_group_name)
            self.log.info("client group deleted")
        else:
            self.log.info("client group does not exist")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("storage policy deleted")
        else:
            self.log.info("storage policy does not exist.")

        if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.commcell.storage_pools.delete(self.storage_pool_name)
            self.log.info("storage pool deleted")
        else:
            self.log.info("storage pool does not exist.")

        self.commcell.disk_libraries.refresh()

        self.log.info("clean up successful")

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.error("previous run clean up ERROR")
            raise Exception("ERROR:%s", exp)

    def allocate_resources(self):
        """creates all necessary resources for testcase to run"""

        # create storage pool

        self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mount_path,
                                                            self.media_agent, self.media_agent, self.partition_paths[0])
        self.log.info(f'successfully configured storage pool - {self.storage_pool_name}')

        # create dependent storage policy
        self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.storage_pool_name,
                                                                 media_agent=self.media_agent,
                                                                 global_policy_name=self.storage_pool_name,
                                                                 dedup_media_agent=self.media_agent,
                                                                 dedup_path=self.partition_paths[0])

        # adding second partition to the ddb store
        self.get_active_files_store()
        for partition in range(1, 2):
            self.partition_paths.append(self.media_agent_machine.join_path(self.dedup_store_path_base,
                                                                           f'partition_{partition}'))
            self.store_obj.add_partition(self.partition_paths[partition], self.media_agent)
            self.log.info(f'successfully added partition {partition}')

        # disable MS
        self.store_obj.enable_garbage_collection = False

        # create backupset and subclient
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name,
                                                             self.agent)
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name,
                                                            self.subclient_name,
                                                            self.storage_policy_name,
                                                            self.content_path,
                                                            self.agent)

        # create primary copy object for storage policy
        self.primary_copy = self.storage_policy.get_copy(copy_name="primary")
        self.sidb_id = \
            self.dedup_helper.get_sidb_ids(copy_name="primary", sp_id=self.storage_policy.storage_policy_id)[0]

        # add data to subclient content
        self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=1.0)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

        # creating and setting client_group
        self.client_group = self.commcell.client_groups.add(self.client_group_name, [self.media_agent])
        query = f"select id from app_clientgroup where name like '{self.client_group_name}'"
        self.log.info(f"QUERY: {query} ")
        self.csdb.execute(query)
        self.client_group_id = self.csdb.fetch_one_row()[0]
        self.log.info(f"QUERY OUTPUT : {self.client_group_id}")

    def get_active_files_store(self):
        """returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

            Returns:
                job id  (int)
        """
        self.log.info("starting %s backup job...", job_type)
        job = self.subclient.backup(backup_level=job_type)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

    def fetch_chunk(self, job_id):
        """
        return a list of chunk id, volume id pairs for a given job id

            Args:
                job_id - (int) - job id
            Returns:
                result (list of a list of strings)
        """

        query = f"select id,volumeid from archchunk where id in " \
                f"(select archchunkid from archchunkmapping where archfileid in " \
                f"(select id from archfile where jobid={str(job_id)} and filetype=1))"
        self.log.info(f"QUERY: {query} ")
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {result}")
        return result

    def delete_job(self, job_list):
        """
        deletes all jobs whose job ids are passed as argument

            Args:
                job_list        (list/iterator)     list of job ids of jobs to be deleted
            returns:
                none
        """
        if not job_list:
            self.log.error("no jobs specified for deletion!")
            return

        for job in job_list:
            self.log.info("deleting job %s ...", job)
            self.primary_copy.delete_job(job)

    def run_data_aging(self, copy_name, sp_name):
        """
        Run data aging job

            args:
                copy_name   (str)   copy name to run granular data aging on
                sp_name     (str)   sp name to run granular data aging on
            returns:
                none
        """
        data_aging_job = self.mm_helper.submit_data_aging_job(copy_name=copy_name, storage_policy_name=sp_name,
                                                              is_granular=True, include_all=False,
                                                              include_all_clients=True,
                                                              select_copies=True, prune_selected_copies=True)
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

    def get_deleted_af_ids(self, sidb_store_id):
        """
        returns the count of deletedaf entries in MMDeleteaf for given store

            Args:
                sidb_store_id       (str)       store_id

            returns:
                afids(set), count(int) of such entries
        """
        query = f"select archfileid from MMDeletedaf where SIDBStoreId = {sidb_store_id}"
        self.log.info(f"QUERY: {query} ")
        self.csdb.execute(query)
        af_list = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {af_list}")
        afids = {x[0] for x in af_list}
        count = len(afids)
        return afids, count

    def chunk_exist(self, chunklist, chunk_should_exist):
        """
        performs physical exists check for the given chunk id

            Args:
                    chunklist           (list)   list of a list of chunkid and volumeid pairing strings
                    chunk_should_exist (boolean)  this is the mode the method should run in.  If true, we check
                                                  and fail if any chunks dont exist.  If false, we check and fail if
                                                  any chunks do exist.
            returns:
                    chunk_exists (bool)
        """

        # Get Mountpath ID
        self.log.info("Fetching MountPathname for the mount path in library %s", self.storage_pool_name)
        query = f"select mountpathname from mmmountpath where libraryid = " \
                f"( select LibraryId from mmlibrary where aliasname = '{self.storage_pool_name}')"
        self.log.info(f"QUERY: {query} ")
        self.csdb.execute(query)
        mountpath_name = self.csdb.fetch_one_row()
        self.log.info(f"MountPathName = {mountpath_name[0]}")
        os_sep = self.media_agent_machine.os_sep

        if chunk_should_exist:
            chunk_exists = True
            for i in range(len(chunklist)):
                chunk_id = chunklist[i][0]
                volume_id = chunklist[i][1]
                chunk_to_validate = f"{self.mount_path}{os_sep}{mountpath_name[0]}{os_sep}CV_MAGNETIC{os_sep}" \
                                    f"V_{volume_id}{os_sep}CHUNK_{chunk_id}"
                if not self.media_agent_machine.check_directory_exists(chunk_to_validate):
                    self.log.info(f'chunk {chunk_id} does not exist on disk')
                    chunk_exists = False
                else:
                    self.log.info(f'chunk {chunk_id} exists on disk')
        else:
            chunk_exists = False
            for i in range(len(chunklist)):
                chunk_id = chunklist[i][0]
                volume_id = chunklist[i][1]
                chunk_to_validate = f"{self.mount_path}{os_sep}{mountpath_name[0]}{os_sep}CV_MAGNETIC{os_sep}" \
                                    f"V_{volume_id}{os_sep}CHUNK_{chunk_id}"
                if self.media_agent_machine.check_directory_exists(chunk_to_validate):
                    self.log.info(f'chunk {chunk_id} exists on disk')
                    chunk_exists = True
                else:
                    self.log.info(f'chunk {chunk_id} does not exists on disk')
        return chunk_exists

    def check_error_codes(self, sidb_store_id, error_code):
        """
        checks whether the specified error codes have been set for all entries of a given store in MMDeleteAF table

            Args:
                sidb_store_id       (int/str)       store id of store whose entries are to be checked
                error_code          (int/str)       error code to be checked in MMDeleteAF table
            returns:
                none

        """
        query = f"select failureerrorcode from mmdeletedaf where sidbstoreid ={sidb_store_id} and status != 2"
        self.log.info(f"QUERY: {query} ")
        self.csdb.execute(query)
        error_codes = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {error_codes}")
        for code in error_codes:
            if int(code[0]) != error_code:
                self.log.error(f"error code mismatch.. unexpected error code {code[0]}..")
                raise Exception("unexpected failure error codes found...")

        self.log.info(f"error codes for mmdeleteaf entries match with {error_code}... expected result")

    def add_op_window_for_pruning(self, clientgroupid, starttime, endtime, startdate, enddate):
        """
        creates a new operation window rule for the given clientgroup

            Args:
                clientgroupid   (int/str)   id of clientgroup
                starttime       (int/str)   start time in unix epoch time
                endtime         (int/str)   end time in unix epoch time
                startdate       (str)       start date for rule
                enddate         (str)       end date for rule
            returns:
                none

        """
        xml = f"""<Api_AddOperationWindowReq>
                  <entity clientId="0" clientGroupId="{clientgroupid}"/>
                  <operationWindow endDate="{enddate}" name="OP1" ruleEnabled="1" ruleId="0" startDate="{startdate}">
                        <operations val="131072"/>
                                <dayTime startTime="{starttime}" endTime="{endtime}">
                                <dayOfWeek val="1"/>
                                <dayOfWeek val="2"/>
                                <dayOfWeek val="3"/>
                                <dayOfWeek val="4"/>
                                <dayOfWeek val="5"/>
                                <dayOfWeek val="6"/>
                                <dayOfWeek val="0"/>
                                </dayTime>
                  </operationWindow>
                  </Api_AddOperationWindowReq>"""

        self.log.info("creating op window...")
        self.commcell.qoperation_execute(xml)
        self.log.info("op window created successfully..")

    def modify_op_window(self, clientgroupid, starttime, endtime, startdate, enddate, ruleid):
        """
        modifies operation window rule for the given clientgroup

                    Args:
                        clientgroupid   (int/str)   id of clientgroup
                        starttime       (int/str)   start time in unix epoch time
                        endtime         (int/str)   end time in unix epoch time
                        startdate       (str)       start date for rule
                        enddate         (str)       end date for rule
                        ruleid          (int/str)   id of the rule to be modified
                    returns:
                        none

                """
        xml = f"""<Api_UpdateOperationWindowReq>
              <entity clientId="0" clientGroupId="{clientgroupid}"/>
              <operationWindow endDate="{enddate}" name="OP1" ruleEnabled="1" ruleId="{ruleid}" startDate="{startdate}">
                    <operations val="131072"/>
                            <dayTime startTime="{starttime}" endTime="{endtime}">
                            <dayOfWeek val="1"/>
                            <dayOfWeek val="2"/>
                            <dayOfWeek val="3"/>
                            <dayOfWeek val="4"/>
                            <dayOfWeek val="5"/>
                            <dayOfWeek val="6"/>
                            <dayOfWeek val="0"/>
                            </dayTime>
              </operationWindow>
              </Api_UpdateOperationWindowReq>"""

        self.log.info("modifying op window...")
        self.commcell.qoperation_execute(xml)
        self.log.info("op window modified successfully..")

    def delete_op_window(self, clientgroupid, starttime, endtime, startdate, enddate, ruleid):
        """
        deletes operation window rule for the given clientgroup

                            Args:
                                clientgroupid   (int/str)   id of clientgroup
                                starttime       (int/str)   start time in unix epoch time
                                endtime         (int/str)   end time in unix epoch time
                                startdate       (str)       start date for rule
                                enddate         (str)       end date for rule
                                ruleid          (int/str)   id of the rule to be modified
                            Returns:
                                    None
        """
        xml = f"""<Api_DeleteOperationWindowReq>
              <entity clientId="0" clientGroupId="{clientgroupid}"/>
              <operationWindow endDate="{enddate}" name="OP1" ruleEnabled="1" ruleId="{ruleid}" startDate="{startdate}">
                    <operations val="131072"/>
                            <dayTime startTime="{starttime}" endTime="{endtime}">
                            <dayOfWeek val="1"/>
                            <dayOfWeek val="2"/>
                            <dayOfWeek val="3"/>
                            <dayOfWeek val="4"/>
                            <dayOfWeek val="5"/>
                            <dayOfWeek val="6"/>
                            <dayOfWeek val="0"/>
                            </dayTime>
              </operationWindow>
              </Api_DeleteOperationWindowReq>"""

        self.log.info("deleting op window...")
        self.commcell.qoperation_execute(xml)
        self.log.info("op window deleted successfully..")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # set pruning thread time interval
            self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password,
                                                 min_value=2, mmpruneprocess_value=2)

            # run two full backups
            job_id1 = self.run_backup("FULL")
            job_id2 = self.run_backup("FULL")

            # fetch chunk id and path for each backup for later exists checks
            chunklist_job1 = self.fetch_chunk(job_id1)
            chunklist_job2 = self.fetch_chunk(job_id2)

            # set op window for pruning on ma with start time 1 hour before current time and end time 1 hour
            # after current time
            if "unix" in self.media_agent_machine.os_info.lower():
                matimezone = self.tcinputs["MAtimezone"]
                strnow = self.media_agent_machine.current_time(timezone_name=matimezone).strftime('%H:%M:%S')
            else:
                strnow = self.media_agent_machine.current_localtime().strftime('%H:%M:%S')
            parts = strnow.split(":")
            now_seconds = int(parts[0]) * (60 * 60) + int(parts[1]) * 60 + int(parts[2])
            self.starttime = now_seconds
            self.endtime = now_seconds + 3600
            self.log.info("starttime: %s", str(self.starttime))
            self.log.info("endtime: %s", str(self.endtime))
            today = date.today()
            midnight = datetime.combine(today, datetime.min.time())
            midnight_tuple = midnight.timetuple()
            midnight_timestamp = calendar.timegm(midnight_tuple)
            self.midnight_timestamp_int = ('%.15f' % midnight_timestamp).rstrip('0').rstrip('.')
            self.log.info("start and end date: %s", str(self.midnight_timestamp_int))

            self.add_op_window_for_pruning(startdate=self.midnight_timestamp_int, enddate=self.midnight_timestamp_int,
                                           starttime=self.starttime, endtime=self.endtime,
                                           clientgroupid=self.client_group_id)

            # retrieving rule id from CSDB
            self.log.info("retrieving rule id from CSDB")
            query = f"select id from app_opwindowrule where clientgroupid ={self.client_group_id}"
            self.log.info(f"QUERY: {query} ")
            self.csdb.execute(query)
            self.rule_id = self.csdb.fetch_one_row()[0]
            self.log.info(f"QUERY OUTPUT for ruleid: {self.rule_id}")

            # verify data pruning op window added correctly with registry and csdb
            # checking registry on MA
            reg_key = self.media_agent_machine.join_path("Machines", self.media_agent, "PruningControl",
                                                         "MediaAgentPruningOperationWindow", self.rule_id)

            if self.media_agent_machine.check_registry_exists(reg_key, "OpWindow_1"):
                self.log.info("registry entry corresponding to opwindow found on MA..")
            else:
                self.log.error("registry entry corresponding to opwindow not found on MA..")
                raise Exception("registry not set for opwindow on MA..")

            # checking CSDB for rule entry
            query = f"select optype from app_opwindowrule where id = {self.rule_id}"
            self.log.info(f"QUERY: {query} ")
            self.csdb.execute(query)
            optype = self.csdb.fetch_one_row()[0]
            self.log.info(f"QUERY OUTPUT : {optype}")
            if optype != '131072':
                self.log.error("wrong apptype for data pruning op window")
                raise Exception("Incorrect app type set for op window...")
            self.log.info("apptype is correctly set for data pruning op window")

            # delete the 2 jobs on the store
            self.delete_job([job_id1, job_id2])

            # get list of AFs in mmdeletedaf from pruning
            sleep(10)
            afids_1, afid_count1 = self.get_deleted_af_ids(sidb_store_id=self.sidb_id)

            # run data aging
            self.run_data_aging(copy_name='Primary', sp_name=self.storage_policy_name)

            # verify mmdeletedaf af list is same as it was before dataaging
            pruned = False
            iterations = 1
            while not pruned and iterations <= 2:
                afids_2, afid_count2 = self.get_deleted_af_ids(sidb_store_id=self.sidb_id)
                if afids_2 != afids_1 or afid_count1 != afid_count2:
                    pruned = True
                else:
                    self.log.info(f"pruning iteration {iterations}: afids in mmdeletedaf not changed, expected.")
                    iterations += 1
                    sleep(300)
            if pruned:
                self.log.error("number of AFs changed which may indicate pruning request was run during op window, "
                               "not expected")
                raise Exception(
                    "number of AFs changed which may indicate pruning request was run during op window, "
                    "not expected")
            else:
                self.log.info("SUCCESS - entries not pruned from mmdeletedaf while in blackout window")

            # verify chunks still exist on disk
            if not self.chunk_exist(chunklist_job1, chunk_should_exist=True):
                self.log.error(f'chunk for job {job_id1} is gone, fail case')
                raise Exception("chunk directory unexpectedly deleted while in pruning blackout window")
            else:
                self.log.info(f'chunks for job {job_id1} exist on disk still as expected')
            if not self.chunk_exist(chunklist_job2, chunk_should_exist=True):
                self.log.error(f'chunk for job {job_id2} is gone, fail case')
                raise Exception("chunk directory unexpectedly deleted while in pruning blackout window")
            else:
                self.log.info(f'chunks for {job_id2} exist on disk still as expected')

            # run data forecast report
            self.storage_policy.run_data_forecast()
            sleep(180)
            # verify AFs in mmdeletedaf get updated with the op window failureerrorcode (65128)
            self.check_error_codes(sidb_store_id=self.sidb_id, error_code=65128)

            # edit data pruning op window so starttime is 2 hours after current time
            # and endtime is 3 hours after current time
            if "unix" in self.media_agent_machine.os_info.lower():
                strnow = self.media_agent_machine.current_time(timezone_name=matimezone).strftime('%H:%M:%S')
            else:
                strnow = self.media_agent_machine.current_localtime().strftime('%H:%M:%S')
            parts = strnow.split(":")
            now_seconds = int(parts[0]) * (60 * 60) + int(parts[1]) * 60 + int(parts[2])
            self.starttime = now_seconds + 7200
            self.endtime = now_seconds + 10800
            self.log.info("starttime: %s", str(self.starttime))
            self.log.info("endtime: %s", str(self.endtime))
            self.modify_op_window(startdate=self.midnight_timestamp_int, enddate=self.midnight_timestamp_int,
                                  starttime=self.starttime, endtime=self.endtime,
                                  clientgroupid=self.client_group_id, ruleid=self.rule_id)

            # checking if rule has been modified in CSDB
            query = f"select endtime from app_opwindowrule where id = {self.rule_id}"
            self.log.info(f"QUERY: {query} ")
            self.csdb.execute(query)
            endtimedb = int(self.csdb.fetch_one_row()[0])
            self.log.info(f"QUERY OUTPUT : {endtimedb}")
            if endtimedb != self.endtime:
                self.log.error("pruning op window not changed from endtimedb: %d to enTime: %d ", endtimedb,
                               self.endtime)
                raise Exception("failed to modify op window..")
            self.log.info("data pruning op window successfully modified")

            # sleep to wait for 3 min prune process interval
            sleep(180)
            self.run_data_aging(copy_name='Primary', sp_name=self.storage_policy_name)

            sleep(300)

            # verify afids pruned from mmdeletedaf table
            pruned = False
            iterations = 1
            while not pruned and iterations <= 3:
                afids3, afid_count3 = self.get_deleted_af_ids(sidb_store_id=self.sidb_id)
                if afids3 == {''}:
                    pruned = True
                    self.log.info("mmdeleteaf entries removed, expected..")
                else:
                    iterations += 1
                    self.log.info(f"sleeping 5 mins before running pruning iteration {iterations}")
                    sleep(300)
            if iterations > 3:
                self.log.error(f'mmdeletedaf entries not removed for store {self.sidb_id}, not expected..')
                raise Exception("mmdeleteaf entries not removed, not expected..")
            else:
                self.log.info("SUCCESS - afids pruned from mmdleletedaf once outside of blackout window")

            # verify chunks physically pruned from disk
            prunedondisk = False
            iterations = 1
            while not prunedondisk and iterations <= 3:
                if self.chunk_exist(chunklist_job1, chunk_should_exist=False):
                    self.log.info(f"iteration: {iterations}, chunks still exist on disk, sleep 5 mins and retry")
                    iterations += 1
                    sleep(300)
                else:
                    prunedondisk = True
                    self.log.info(f'chunks from job {job_id1} deleted from disk still as expected')
            if iterations > 3:
                self.log.error(f'chunk from job {job_id1} is still present on disk, fail case')
                raise Exception("chunk directory unexpectedly exists on disk while out of pruning blackout window")

            prunedondisk = False
            iterations = 1
            while not prunedondisk and iterations <= 3:
                if self.chunk_exist(chunklist_job2, chunk_should_exist=False):
                    self.log.info(f"iteration: {iterations}, chunks still exist on disk, sleep 5 mins and retry")
                    iterations += 1
                    sleep(300)
                else:
                    prunedondisk = True
                    self.log.info(f'chunks from job {job_id2} deleted from disk still as expected')
            if iterations > 3:
                self.log.error(f'chunk from job {job_id2} is still present on disk, fail case')
                raise Exception("chunk directory unexpectedly exists on disk while out of pruning blackout window")

            # delete data pruning op window
            self.delete_op_window(startdate=self.midnight_timestamp_int, enddate=self.midnight_timestamp_int,
                                  starttime=self.starttime, endtime=self.endtime,
                                  clientgroupid=self.client_group_id, ruleid=self.rule_id)

            # verify its gone from app_opwindowrule table
            query = f"select id from app_opwindowrule where clientgroupid = {self.client_group_id}"
            self.log.info(f"QUERY: {query} ")
            self.csdb.execute(query)
            self.rule_id = self.csdb.fetch_one_row()[0]
            self.log.info(f"QUERY OUTPUT : {self.rule_id}")
            if self.rule_id != "":
                raise Exception("op window not deleted, unexpected..")
            self.log.info("op window deleted successfully..")

            # verify the rule has been removed from MA registry
            if not self.media_agent_machine.check_registry_exists(reg_key, "OpWindow_1"):
                self.log.info("registry entry corresponding to opwindow removed from MA..")
            else:
                self.log.error("registry entry corresponding to opwindow not removed from MA..")
                raise Exception("registry for opwindow still present on MA..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        # delete data pruning op window
        self.delete_op_window(startdate=self.midnight_timestamp_int, enddate=self.midnight_timestamp_int,
                              starttime=self.starttime, endtime=self.endtime,
                              clientgroupid=self.client_group_id, ruleid=self.rule_id)

        # resetting default values for store pruning and pruning interval
        self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password)

        self.log.info("Performing unconditional cleanup")
        # removing initialized resources
        self.log.info("********* clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.error("clean up ERROR %s", exp)
