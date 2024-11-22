# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                --  initialize TestCase class

    setup()                   --  setup function of this test case

    previous_run_cleanup()    --  for deleting the left over
                                  backupset and storage policy
                                  from the previous run

    run_full_backup_job()     --  for running a full backup job

    create_resources()        --  creates library, storage policy, backupset, and subclient, and returns the resources

    run_first_backup()        --  for running an initial backup job

    get_cloud_size()          --  for getting volume size of volumes in a cloud library

    run_second_backup()       --  for running a second backup job which is smaller than the first

    delete_first_backup()     --  for deleting the first backup job

    run_pruning_validation()  --  verify if the deleted job files have been moved to MMdeletedAF

    validate_dp_settings_pruning_flag()  --  sets the mp_pruning_property in csdb depending on input
    
    get_library_name()        --  returns the name of the library of the storage pool
    
    validate_datapath_pruner_ma_flag()  --  validates if the datapath pruner ma is set correctly
    
    get_mp_id_for_library()   --  gets the mountpath id for the library
    
    validate_datapath_pruner_ma_is_used()  --  validates if the datapath pruner ma is used
    
    unset_preferred_cloud_pruner_flag()  --  unsets the preferred cloud pruner flag
    
    run_cloud_library_pruning()  --  runs the cloud library pruning process
    
    run_defrag_on_cloud_pool()  --  runs defragmentation on the cloud pool
    
    enable_select_ma_for_pruning_on_mp()  --  enables Select MA for pruning on MP feature on cloud mount path

    run()                           --  run function of this test case

    tear_down()               --  tear down function of this test case

This testcase verifies if cloud library is correctly performing micro pruning operations and drilling holes is working
as expected

input json file arguments required:

        "70648": {
                "ClientName": "client name",
                "AgentName": "File System",
                "MediaAgentName": "ma name",
                "ExpectedDeletedRecords": "8000",
                "cloud_library_name": "lib name",
                "dedup_path": path where dedup store to be created (optional),
                "CloudMountPath": "cloud mount path",
                "AccessKeyAuthTypeUsername": "username in the format <Service Host>//<Access Key ID>",
                "CredentialName": "Credential name for access key auth type",
                "CloudMountPath": "The cloud mount path name for the cloud library",
                "CloudVendor": "Cloud Vendor Name, for S3 -> 's3 compatible storage' "
                "MPShareMA1": "mmdedup35_2",
                "MPShareMA2": "bbcs7"
                }
        dedup_path is an optional parameter and needs to be provided only when Media Agent is Unix. All S3 details are
        optional.
        This case creates a new cloud storage pool with every run. Ideally use Pure(s3 compatible storage)
        for this case.
        For CloudVendor info, refer to mediagentconstants.py
        MPShareMA MAs are added as mount paths to the cloud library so they need to be unique from the above
                MediaAgentName


Design Steps:
1.	Create resources
2.  Enable Select MA for pruning on MP feature on cloud mount path
3.  Verify flag (256) is set in MMMountPath table for default MA
3.  Verify flag (64) is set in mmdatapath table for default MA
4.  Run cloud library pruning
    a.	Content: numerous files with random data
        amounting to 1 gb ~ roughly 180 files (total)
        2.1 Disable mark and sweep
    b.	Subclient level: data reader streams : 1
    c.	First backup job , get the sidb id,
        archfiles., chunks -> first backup job
    d.	Delete every alternate file
    e.	Second backup job
    f.	Delete first backup job
    g.	MMdeleted AF check
    h.	Change mm prune process interval to 2 min
    i. Run data aging job -> job should complete sucessfully
5.  Validate MA used for data aging job is the pruner MA

These negative scenarios will added in phase 2:
6.  Unset preferred cloud pruner flag
7.  Run data aging job -> job should fail as pruner MA is not set -> Validate JPR
8.  Run cloud defrag job -> job should fail as pruner MA is not set -> Validate JPR
"""

import time
from cvpysdk import deduplication_engines
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper
from MediaAgents import mediaagentconstants
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Select MA for pruning on MP feature Validation Case"

        self.tcinputs = {
            "MediaAgentName": None,
            "ExpectedDeletedRecords": None
        }
        self.library_name = None
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.storage_policy_id = None
        self.sidb_id = None
        self.substore_id = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_dedup = False
        self.is_user_defined_lib = False
        self.pruner_ma_id = None
        self.cloud_storage_pool_name = None
        self.copy_id = None
        self.storage_pool = None
        self.disk_library = None

    def setup(self):
        """sets up the variables to be used in testcase"""

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)

        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cloud_storage_pool_name = \
            f"cloud_storage_pool_{self.id}_{self.tcinputs['ClientName']}_{self.tcinputs['MediaAgentName']}"

        suffix = str(self.tcinputs["MediaAgentName"]) + \
            '_' + str(self.tcinputs["ClientName"])

        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

        # create the required resources for the testcase
        # get the drive path with required free space
        drive_path_client = self.opt_selector.get_drive(
            self.client_machine, 25 * 1024)
        drive_path_media_agent = self.opt_selector.get_drive(
            self.media_agent_machine, 25 * 1024)
        self.testcase_path_media_agent = f"{drive_path_media_agent}{self.id}"

        # creating testcase directory, mount path, content path, dedup
        # store path

        self.testcase_path_client = f"{drive_path_client}{self.id}"

        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info(
                "existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error(
                "LVM enabled dedup path must be input for Unix MA!..")
            raise Exception(
                "LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        self.storage_policy_name = f"{self.id}_SP{suffix}"
        self.backupset_name = f"{self.id}_BS{suffix}"
        self.subclient_name = f"{self.id}_SC{suffix}"

    @test_step
    def clean_up_tc_env(self):
        """Cleanup TC environment"""
        self.log.info("********* Cleaning up TC environment **********")
        try:
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

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(
                    self.storage_policy_name)
                self.log.info(f"Storage policy {self.storage_policy_name} deleted")
            else:
                self.log.info("storage policy does not exist.")

            # Delete cloud storage pool
            if self.commcell.storage_pools.has_storage_pool(self.cloud_storage_pool_name):
                self.log.info(
                    f"Deleting Storage Pool: {self.cloud_storage_pool_name}")
                self.commcell.storage_pools.delete(self.cloud_storage_pool_name)
                self.log.info(f"Deleted Storage Pool: {self.cloud_storage_pool_name}")
            else:
                self.log.info(f"Storage Pool: {self.cloud_storage_pool_name} does not exist")
            self.log.info("Clean up successful")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_full_backup_job(self):
        """
            run a full backup job

            Returns:
                an object of running full backup job
        """
        self.log.info("Starting backup job")
        job = self.subclient.backup("FULL")
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            if job.status.lower() == "completed":
                self.log.info("job %s complete", job.job_id)
            else:
                raise Exception(
                    f"Job {job.job_id} Failed with {job.delay_reason}")
        return job

    @test_step
    def create_resources(self):
        """
            create resources for testcase

            Returns:
                list of files in defined client path that need to backed up
        """
        self.storage_pool = self.commcell.storage_pools.add(self.cloud_storage_pool_name,
                                                            self.tcinputs["CloudMountPath"],
                                                            self.tcinputs["MediaAgentName"],
                                                            self.tcinputs["MediaAgentName"],
                                                            self.dedup_store_path,
                                                            username=self.tcinputs["AccessKeyAuthTypeUsername"],
                                                            password="",
                                                            credential_name=self.tcinputs["CredentialName"],
                                                            cloud_server_type=mediaagentconstants.CLOUD_SERVER_TYPES[
                                                                self.tcinputs['CloudVendorName']])

        # getting disk library object
        self.library_name = self.get_library_name()
        self.disk_library = self.commcell.disk_libraries.get(self.library_name)
        self.disk_library.mount_path = self.tcinputs["CloudMountPath"]
        self.disk_library.mediaagent = self.tcinputs["MediaAgentName"]

        self.disk_library.share_mount_path(new_media_agent=self.tcinputs["MPShareMA2"],
                                           new_mount_path=self.tcinputs["CloudMountPath"],
                                           credential_name=self.tcinputs["CredentialName"],
                                           username=self.tcinputs["AccessKeyAuthTypeUsername"],
                                           password="",
                                           access_type=6)
        self.disk_library.share_mount_path(new_media_agent=self.tcinputs["MPShareMA1"],
                                           new_mount_path=self.tcinputs["CloudMountPath"],
                                           credential_name=self.tcinputs["CredentialName"],
                                           username=self.tcinputs["AccessKeyAuthTypeUsername"],
                                           password="",
                                           access_type=6)

        # create SP
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            storage_policy_name=self.storage_policy_name,
            storage_pool_name=self.cloud_storage_pool_name,
            is_dedup_storage_pool=True)

        # use the storage policy object
        # from it get the storage policy id
        # get the sidb store id and sidb sub store id
        return_list = self.dedup_helper.get_sidb_ids(
            self.storage_policy.storage_policy_id, "Primary")
        self.sidb_id = int(return_list[0])
        self.substore_id = int(return_list[1])

        # disable mark and sweep
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(
            self.commcell)
        if dedup_engines_obj.has_engine(self.storage_policy_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(
                self.storage_policy_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info(
                    "Disabling Garbage Collection on DDB Store == %s", dedup_store[0])
                store_obj.enable_garbage_collection = False

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(
            self.backupset_name, self.agent)
        self.log.info("Backup set created")

        # generate unique random data for the testcase
        # factor of 0.00028 helps to ensure minimum number of records
        # which are deleted after pruning
        data_size = int(self.tcinputs["ExpectedDeletedRecords"]) * 0.00028
        if self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                     self.content_path,
                                                     float("{0:.1f}".format(data_size)), 1):
            self.log.info("generated unique data for subclient")
        else:
            raise Exception("couldn't generate unique data")

        content_files = sorted(
            self.client_machine.get_files_in_path(self.content_path))
        content_size = self.client_machine.get_folder_size(self.content_path)
        self.log.info(
            f'number of source content files before first backup: {len(content_files)}')
        self.log.info(
            f'size of source content path before first backup: {content_size}')
        # got the files to be loaded to the subclient

        # create subclient
        self.log.info("check SC: %s", self.subclient_name)
        if not self.backup_set.subclients.has_subclient(self.subclient_name):
            self.subclient = self.backup_set.subclients.add(
                self.subclient_name, self.storage_policy_name)
            self.log.info("created subclient %s", self.subclient_name)
        else:
            self.log.info("subclient %s exists", self.subclient_name)
            self.subclient = self.backup_set.subclients.get(
                self.subclient_name)

        # add subclient content
        self.log.info(
            "add all the generated files as content to the subclient")
        self.subclient.content = content_files
        # set the subclient data reader / streams to one
        self.log.info("set the data readers for subclient %s to 1",
                      self.subclient_name)
        self.subclient.data_readers = 1

        if self.media_agent_machine.check_registry_exists('MediaAgent', 'DedupDrillHoles'):
            self.log.info("DeduprillHoles registry key found on MA")
            ma_client = self.commcell.clients.get(
                self.tcinputs.get("MediaAgentName"))
            self.log.info(
                "Deleting DedupDrillHoles Additional Setting on MA Client from CS side")
            ma_client.delete_additional_setting(
                "MediaAgent", "DedupDrillHoles")
            self.log.info("Deleting DedupDrillHoles Registry key from MA")
            self.media_agent_machine.remove_registry(
                'MediaAgent', value='DedupDrillHoles')
            self.log.info(
                "Successfully removed DedupDrillHoles setting from MA")
        # use the default storage policy block size 128 kb

        return content_files

    def get_library_name(self):
        """
            returns the name of the library of the storage pool
        """
        query = f"""select  distinct lib.aliasname
                    from    mmlibrary lib with (nolock),
                            mmmasterpool mpl with (nolock),
                            mmdrivepool dpl with (nolock), 
                            mmdatapath dp with (nolock), 
                            archgroupcopy agc with (nolock),
                            archgroup ag with (nolock)
                    where   mpl.libraryid = lib.libraryid
                            and dpl.MasterPoolId = mpl.masterpoolid 
                            and dp.drivepoolid = dpl.drivepoolid
                            and agc.id = dp.CopyId
                            and ag.id = agc.archGroupId
                            and ag.name = '{self.cloud_storage_pool_name}'
                """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        return self.csdb.fetch_one_row()[0]

    def run_first_backup(self):
        """
            runs initial backup job

            Returns:
                tuple that contains results from the backup job    
        """
        # run the first backup job
        first_job = self.run_full_backup_job()

        query = """SELECT    archchunkid
                    FROM      archchunkmapping
                    WHERE     archfileid
                    IN       ( SELECT    id
                                FROM      archfile 
                                WHERE     jobid={0} 
                                AND       filetype=1)""".format(first_job.job_id)
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        chunks_first_job = []
        for i in range(len(res)):
            chunks_first_job.append(int(res[i][0]))
        self.log.info("got the chunks belonging to the first backup job")
        self.log.info("Chunks are: %s", chunks_first_job)

        query = f"""SELECT    id
                    FROM      archFile
                    WHERE     jobId={first_job.job_id}"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        arch_files_first_job = []
        for i in range(len(res)):
            arch_files_first_job.append(int(res[i][0]))
        self.log.info("got the archfiles belonging to the first backup job")
        self.log.info("Archfiles are:%s", arch_files_first_job)

        return (first_job, arch_files_first_job, chunks_first_job)

    def run_second_backup(self, content_files):
        """
            runs second backup job

            Args:
                content_files (list)  --  list of files to be backed up

            Returns:
                volume size of volumes in the cloud library
        """
        temp_files = []
        # change the content on the subclient for the second backup job
        for i in range(0, len(content_files), 2):
            temp_files.append(content_files[i])
        content_files = temp_files
        self.log.info(
            f'number of source content files before second backup: {len(content_files)}')
        self.log.info(
            "deleted every alternate file from the content files list ")
        self.log.info(
            "maximises the chance of drill hole taking place while pruning ")

        # add the modified content files list to subclient
        self.log.info(
            "MODIFIED content files list added as content to the subclient")
        self.subclient.content = content_files

        # run the second backup job
        self.run_full_backup_job()

    def delete_first_backup(self, first_job):
        """
            deletes the first backup job

            Args:
                first_job (obj)  --  first backup job object
        """
        # delete the first backup job
        storage_policy_copy = self.storage_policy.get_copy("Primary")
        # because only copy under storage policy was created above
        storage_policy_copy.delete_job(first_job.job_id)
        self.log.info("deleted the first backup job: id %s",
                      str(first_job.job_id))

        # after deletion of job, the archFiles should be moved to
        # MMdeletedAF table
        self.log.info("sleeping for 30 seconds")
        time.sleep(30)

    def run_pruning_validation(self, expected_to_fail=False):
        """
            verify if the deleted job files have been moved to MMdeletedAF

            Args:
                expectedToFail (bool) -- flag indicating whether the job is expected to fail

        """
        self.log.info("===================================="
                      "===============================================")

        self.mm_helper.update_mmconfig_param(
            'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 0, 2)

        self.log.info("mmprune process interval set to two minute")

        self.log.info("waiting... to trigger MM Prune Process")

        self.log.info("Initiating Data Aging Job")

        job = self.mm_helper.submit_data_aging_job(
            copy_name="Primary",
            storage_policy_name=self.storage_policy_name,
            is_granular=True,
            include_all=False,
            include_all_clients=True,
            select_copies=True,
            prune_selected_copies=True)

        self.log.info("Data Aging job: %s", str(job.job_id))
        if expected_to_fail:
            if job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.error(
                        f"Job {job.job_id} completed, but was expected to fail")
                    raise Exception(
                        f"Job {job.job_id} completed, but was expected to fail")
                else:
                    self.log.info(
                        f"Job {job.job_id} Failed as expected with JPR: {job.delay_reason}")
        else:
            if job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info(F"job {job.job_id} completed")
                else:
                    self.log.eror(
                        f"Job {job.job_id} failed, but was expected to complete")
                    raise Exception(
                        f"Job {job.job_id} Failed with {job.delay_reason}")

    @test_step
    def validate_dp_settings_pruning_flag(self, mp_id):
        """
        sets the mp_pruning_property in csdb depending on input

            Args:
                mp_id       (int/str)       id of mountpath
                value       (Boolean)       whether to enable or disable property

        returns None
        """
        query = f"SELECT  Attribute&256 " \
                f"FROM MMMountPath " \
                f"Where mountpathid={mp_id}"

        self.log.info(f"Executing query: {query}")
        self.csdb.execute(query)
        flag = self.csdb.fetch_one_row()[0]
        if flag != '256':
            self.log.error(f"Attribute flag not set for mountpath: {mp_id}")
            raise Exception(
                "Attribute flag not set as expected, failing case!")
        else:
            self.log.info(
                f"Success: 256 Attribute flag set on mountpath: {mp_id}")

    def get_mp_id_for_library(self):
        """
        gets the mountpath id for the library

            Args:
                library_name       (str)       name of the library

        returns mountpath id
        """
        query = f"SELECT mountpathid from MMMountPath where libraryid in " \
                f"(SELECT libraryid from MMLibrary where aliasname = '{self.library_name}')"
        self.log.info(f"Executing query: {query}")
        self.csdb.execute(query)
        mp_id = self.csdb.fetch_one_row()[0]
        self.log.info(f"Query output-> MPid: {mp_id}")
        return mp_id

    @test_step
    def validate_datapath_pruner_ma_flag(self, copy_id):
        """
        validates if the datapath pruner ma is set correctly

            Args:
            copy_id       (int)       id of the copy

        returns None
        """
        query = f"""SELECT HostClientId
                FROM MMDataPath
                where copyid = {copy_id} and flag&64<>0"""
        self.log.info(f"Executing query: {query}")
        self.csdb.execute(query)
        self.pruner_ma_id = self.csdb.fetch_one_row()[0]
        if self.pruner_ma_id != '':
            self.log.info(
                f"Pruner MA flag set on Host Client id: {self.pruner_ma_id}")
            return self
        self.log.error("No MA with flag enabled")
        raise Exception("Pruner MA flag not set on datapath")

    @test_step
    def run_cloud_library_pruning(self, content_files, expected_to_fail=False):
        """
        Runs the cloud library pruning process.

        This method performs the following steps:
        1. Runs the first backup and retrieves the first job, archived files, and chunks.
        2. Runs the second backup and retrieves the initial size.
        3. Deletes the first backup job.
        4. Runs validation checks on the archive files, chunks, CSDB, and physical size.
        5. Runs the restore job.

        Args:
            content_files (list): A list of content files to be used in the pruning process.

            expected_to_fail (bool): A flag to indicate if the pruning process is expected to fail.
                                     True if the job is expected to fail; False otherwise.
        """
        first_result = self.run_first_backup()

        first_job = first_result[0]

        self.run_second_backup(content_files)

        self.delete_first_backup(first_job)

        self.run_pruning_validation(expected_to_fail)

    @test_step
    def validate_datapath_pruner_ma_is_used(self, copy_id):
        """
        validates if the datapath pruner ma is used

            Args:
            pruner_ma_id       (int)       id of the pruner ma

        returns None
        """
        query = f"""SELECT DISTINCT reserveInt 
                    FROM HistoryDB..MMDeletedAFPruningLogs 
                    WHERE copyid = {copy_id}"""
        self.log.info(f"Executing query: {query}")
        self.csdb.execute(query)
        ma_id = self.csdb.fetch_all_rows()
        if len(ma_id) > 1:
            raise Exception("Multiple pruner MAs used! Failing this case.")

        if ma_id[0][0] == self.pruner_ma_id:
            self.log.info(
                "Expected Datapath Pruner MA is used for data aging.")
        else:
            self.log.error(f"Expected Datapath Pruner MA is not used for data aging ->"
                           f"Expected MA id: {self.pruner_ma_id}, Used MA id: {ma_id}")
            raise Exception("Expected Datapath Pruner MA is not used")

    def unset_preferred_cloud_pruner_flag(self):
        """
        unsets the preferred cloud pruner flag

            Args:
                mp_id       (int/str)       id of mountpath

        returns None
        """
        query = f"UPDATE MMDataPath set flag = flag&~64 " \
                f"where copyid = {self.copy_id} and HostClientId = {self.pruner_ma_id}"
        self.log.info(
            f"Disabling Preferred Cloud Pruner flag on, HostClientId: {self.pruner_ma_id} ")
        self.log.info(f"Executing query: {query}")
        self.opt_selector.update_commserve_db(query)

    def get_active_files_store(self):
        """Returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(
            self.storage_policy_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def run_defrag_on_cloud_pool(self):
        """
        Runs defragmentation on the cloud pool.

        Returns:
            None
        """
        store = self.get_active_files_store()
        space_reclaim_job = store.run_space_reclaimation(
            clean_orphan_data=False,
            use_scalable_resource=self.tcinputs.get("UseScalable", True))

        if not space_reclaim_job.wait_for_completion():
            if space_reclaim_job.status.lower() == "completed":
                self.log.eror(
                    f"DDB Space reclaim Job {space_reclaim_job.job_id} completed, but was expected to fail")
                raise Exception(f"DDB Space reclaim Job {space_reclaim_job.job_id} completed,"
                                f"but was expected to fail")
            else:
                self.log.info(
                    f"DDB Space reclaim Job {space_reclaim_job.job_id} Failed as expected"
                    f"with JPR: {space_reclaim_job.delay_reason}")

        if not space_reclaim_job.wait_for_completion():
            self.log.info(f"Failed to run DDB Space reclaim(Job Id: {space_reclaim_job.job_id})"
                          f"with error: {space_reclaim_job.delay_reason}")
    
    @test_step
    def enable_select_ma_for_pruning_on_mp(self, mp_id):
        """
        Enables Select MA for pruning on MP feature on cloud mount path

        Args:
            mp_id (str): The ID of the mount path.

        Returns:
            None
        """
        self.log.info(f"Enabling Select MA for pruning on MP feature, MPid: {mp_id} ")
        self.mm_helper.edit_mountpath_properties(mountpath=self.disk_library.mount_path,
                                                 library_name=self.disk_library.name,
                                                 media_agent=self.disk_library.mediaagent,
                                                 use_dp_settings_for_pruning=1)

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_up_tc_env()

            content_files = self.create_resources()
            self.copy_id = self.storage_pool.copy_id
            policy_copy_id = self.storage_policy.get_copy("Primary").copy_id
            mp_id = self.get_mp_id_for_library()

            self.log.info(
                "Case 1: Basic test scenario to validate preferred datapath pruner MA functionality")
            self.enable_select_ma_for_pruning_on_mp(mp_id)
            
            self.validate_dp_settings_pruning_flag(mp_id)
            
            self.validate_datapath_pruner_ma_flag(copy_id=self.copy_id)
            
            self.run_cloud_library_pruning(
                content_files, expected_to_fail=False)

            # sleep for 5 mins so pruner process interval kicks in and 2nd sweep adds entries to MMDeletedAFPruningLogs
            self.log.info("Sleeping for 5 mins so pruner process interval kicks in and 2nd sweep"
                          " adds entries to MMDeletedAFPruningLogs")
            time.sleep(300)

            self.validate_datapath_pruner_ma_is_used(policy_copy_id)

            self.log.info("Case 1 validated successfully")

            # Below additional cases will be included at a later time
            '''self.log.info("Case 2: Negative test scenario -> unsetting preferred cloud pruner flag")
            self.unset_preferred_cloud_pruner_flag()

            self.log.info("Case 2a: run data aging job -> it should fail since there is no pruner MA set")
            error_flag = self.run_cloud_library_pruning(content_files, expected_to_fail=True)

            self.log.info("Case 2b: run cloud defrag job -> it should fail since there is no pruner MA set")
            self.run_defrag_on_cloud_pool()'''

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all objects created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.mm_helper.update_mmconfig_param(
                'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
            self.mm_helper.update_mmconfig_param(
                'MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 60)
            self.log.info("Performing unconditional cleanup")
            self.clean_up_tc_env()

        except Exception as exp:
            self.log.info("Clean up not successful")
            self.log.info("ERROR:%s", exp)
