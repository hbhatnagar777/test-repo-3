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

    previous_run_cleanup() -- for deleting the left over
    backupset and storage pool,plan from the previous run

    run_backup_job() -- for running a backup job depending on argument

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

basic idea of the test case:
Checking for a given block deduplication size 64kb,
whether the deduplication is taking place at the media agent or not

validations used:
1. Sigwhere: whether deduplication at media agent or not
2. Client dedup: should be disabled
3. Sig scheme: whether any signature generation algorithm used or not
4. Compression: is on or not
5. Encryption
6. CvSingleinst: whether the backup job is having dedup enabled or not at run time
7. Network transfer bytes
8. Did dedupe occur correctly
9. si block size is 64kb or not

input json file arguments required:

       "45825": {
        "ClientName": "name of the client machine without as in commserve",
        "AgentName": "File System",
        "MediaAgentName": "name of the media agent as in commserve",

         }
        [for linux MediaAgents, User must explicitly provide a dedup path that is inside a Logical Volume.
        (LVM support required for DDB)]

                        note --
                                ***********************************
                                if library_name_given then reuse_library
                                else:
                                    if mountpath_location_given -> create_library_with_this_mountpath
                                    else:
                                        auto_generate_mountpath_location
                                        create_library_with_this_mountpath

                                if dedup_path_given -> use_given_dedup_path
                                else it will auto_generate_dedup_path
                                ***********************************
"""


from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper
from MediaAgents.MAUtils.mahelper import DeduplicationEngines


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
        self.name = "MA side dedup with block size 64kb"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.library_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.backup_set = None
        self.subclient_ob = None
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.storage_pool_ob = None
        self.plan_name = None
        self.storage_pool_name = None
        self.storage_assigned_ob = None
        self.plan_ob = None
        self.dedup_engines_obj = None
        self.dedup_engine_obj = None
        self.store_obj = None
        self.plan_type = None

    def setup(self):
        """assign values to variables for testcase"""
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        self.plan_type = "Server"
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.tcinputs["ClientName"], self.commcell)
        self.media_agent_machine = machine.Machine(self.tcinputs["MediaAgentName"], self.commcell)

        # check if library name, mount path
        # and dedup path are user defined

        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True


        self.backupset_name = '%s%s%s' % (str(self.id), '_BS_',
                                          str(self.tcinputs['MediaAgentName']))
        self.subclient_name = str(self.id) + "_SC"

        # create the required resources for the testcase
        # get the drive path with required free space

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
            self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs["library_name"]
        else:
            self.library_name = '%s%s%s' % (str(self.id), '_Lib_',
                                            str(self.tcinputs['MediaAgentName']))
            if not self.is_user_defined_mp:
                self.mount_path = self.media_agent_machine.join_path(
                    self.testcase_path_media_agent, "mount_path")
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"],
                                                                     self.id)
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"],
                                                                       self.id)
        else:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)

    def previous_run_clean_up(self):
        """deletes items from the previous run of the testcase"""
        self.log.info("********* previous run clean up started **********")
        try:
            # deleting Backupset
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset.")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Backupset deleted.")

            # deleting Plan
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Plan exists, deleting that")
                self.commcell.plans.delete(self.plan_name)
                self.log.info("Plan deleted.")


            # deleting Storage Pool
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"pool[{self.storage_pool_name}] exists, deleting that")
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info("pool primary deleted.")

            self.log.info("********* previous run clean up ended **********")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_backup_job(self, job_type):
        """running a backup job depending on argument
            job_type                (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job type: %s", job_type)
        job = self.subclient_ob.backup(job_type)
        self.log.info("Backup job: " + str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)
        return job

    def run(self):
        """Run function of this test case"""
        try:

            self.previous_run_clean_up()
            error_flag = []

            dict_nw_transfer = {}
            dict_prim = {}
            dict_sec = {}

            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory already exists")
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the existing content directory")

            # Create content path
            self.client_machine.create_directory(self.content_path)
            self.log.info("content path created")

            # create storage pool
            self.log.info(f"creating storage pool [{self.storage_pool_name}]")
            self.storage_assigned_ob = self.commcell.storage_pools.add(storage_pool_name=self.storage_pool_name,
                                                                mountpath=self.mount_path,
                                                                media_agent=self.tcinputs['MediaAgentName'],
                                                                ddb_ma=self.tcinputs['MediaAgentName'],
                                                                dedup_path=self.dedup_store_path)
            self.log.info(f"storage pool [{self.storage_pool_name}] created")

            # create plan
            self.log.info(f"creating plan [{self.plan_name}]")
            self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type=self.plan_type,
                                                   storage_pool_name=self.storage_pool_name)
            self.log.info(f"plan [{self.plan_name}] created")

            # creating two partitions
            self.dedup_engines_obj = DeduplicationEngines(self.commcell)
            if self.dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
                self.dedup_engine_obj = self.dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = self.dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = self.dedup_engine_obj.get(dedup_store[0])
            self.log.info(f"Storage pool created with one partition. Adding 2nd partition for pool {self.storage_pool_name}")
            self.store_obj.add_partition(self.dedup_store_path, self.tcinputs['MediaAgentName'])

            self.log.info("added split for the dedup store")

            # Disabling schedule policy from plan
            self.plan_ob.schedule_policies['data'].disable()

            # create backupset
            self.log.info(f"Creating Backupset [{self.backupset_name}]")
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)
            self.log.info(f"Backupset created [{self.backupset_name}]")

            # generate the content
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.content_path, 1, 1):
                self.log.info(
                    "generated content for subclient %s", self.subclient_name)

            content_files = sorted(
                self.client_machine.get_files_in_path(
                    self.content_path))
            # got the files to be loaded to the subclient

            self.log.info(f"Creating subclient [{self.subclient_name}]")

            # Adding Subclient to Backupset
            self.subclient_ob = self.backup_set.subclients.add(self.subclient_name)
            self.log.info(f"Added subclient to backupset [{self.subclient_name}]")
            self.log.info(f"{type(self.plan_name)}, {type(self.content_path)}")
            self.log.info("Adding plan to subclient")

            # Associating plan and content path to subclient
            self.subclient_ob.plan = [self.plan_ob, [self.content_path]]
            self.log.info("Added content and plan to subclient")

            # set data readers for subclient to 1
            self.log.info("set the data readers for subclient %s to 1",self.subclient_name)
            self.subclient_ob.data_readers = 1
            # set the block deduplication factor 64kb
            self.log.info("set the dedup block size to 64 kb")

            xml = """<App_UpdateStoragePolicyReq>
                        <StoragePolicy>
                        <storagePolicyName>{0}</storagePolicyName>
                        </StoragePolicy>
                        <sidbBlockSizeKB>64</sidbBlockSizeKB>
                     </App_UpdateStoragePolicyReq>""".format(self.plan_ob.storage_policy.storage_policy_name)
            self.commcell._qoperation_execute(xml)

            # enable encryption
            self.log.info("enabling encryption on client")
            self.client.set_encryption_property(
                "ON_CLIENT", key="4", key_len="256")
            self.log.info("enabling encryption on client: Done")
            # encryption key correlates to the position of the algorithm in the
            # GUI client properties

            # enable media agent side dedup since client side is default option
            self.log.info("disabling client side dedupe")
            self.client.set_dedup_property("clientSideDeduplication", "OFF")
            self.log.info("disabled client side dedupe: Done")

            # for twice run
            # Run FULL backup
            self.log.info("Running full backup...")
            for iterator in range(1, 3):
                job = self.run_backup_job("FULL")
                # do the checks

                log_file = "clBackup.log"
                config_strings_clbackup = [
                    'sigWhere[1]',
                    'isClientSideDedupEnabled - No',
                    'sigScheme[4]',
                    'compressWhere[0]',
                    'encType[2]',
                    'CVSingleInstTarget[1]',
                    'SI Block Size [64 KB]']
                error_flag = []
                self.log.info("*************** Validations ****************")
                self.log.info(
                    "CASE 1: check if the MA side Deduplication is enabled ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[0], job.job_id)

                # storage policy side verification from csdb not used
                if matched_line:
                    self.log.info("Result: Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[0]]

                self.log.info(
                    "CASE 2: check if the client side Deduplication is DISABLED ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[1], job.job_id)

                # check from client side in csdb

                query = """
                        SELECT      attrVal
                        FROM        APP_Client, APP_ClientProp
                        WHERE       APP_Client.name='{0}'
                        AND         APP_ClientProp.componentNameId = APP_Client.id
                        AND         attrName='Enable Deduplication'
                        AND         APP_ClientProp.modified = 0
                """.format(self.tcinputs["ClientName"])
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)

                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 2:        # 2 stands for de duplication disabled on client
                    self.log.info(
                        "query returned: Client side dedup is disabled")

                if matched_line or (result == 2):
                    self.log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[1]]

                self.log.info(
                    "CASE 3: check if any Signature generation "
                    "algorithm is being used signatureType"
                    "sigscheme ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[2], job.job_id)
                query = """
                        SELECT                 SignatureType
                        FROM                   IdxSIDBStore,archGroupCopy,archGroup
                        WHERE                  archGroup.name='{0}'
                        AND                    archGroup.id = archGroupCopy.archGroupId
                        AND                    archGroupCopy.SIDBStoreId = IdxSIDBStore.SIDBStoreId
                """.format(self.plan_ob.storage_policy.storage_policy_name)
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")

                if result == 4:
                    self.log.info(
                        "query returned: Signature generation is being used")
                if matched_line or (result == 4):
                    self.log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[2]]

                self.log.info(
                    "CASE 4: check if there is source side compression, here it will be client ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[3], job.job_id)

                query = """ SELECT  compressWhere
                            FROM    archPipeConfig,APP_Application
                            WHERE   APP_Application.subclientName = '{0}'
                            AND     archPipeConfig.appNumber = APP_Application.id""".format(self.subclient_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")

                if result == 0:
                    self.log.info("query returned source side"
                                  " compression on client is active")
                # software compression:
                #
                # on client 0
                # on mediaagent 1
                # use storage policy settings 2
                # off 4

                if matched_line or (result == 0):
                    self.log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[3]]

                self.log.info("CASE 5: check if encryption is enabled")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[4], job.job_id)

                encrypted = False
                query = """
                        SELECT           attrVal
                        FROM             APP_Client, APP_ClientProp
                        WHERE            APP_Client.name='{0}'
                        AND              APP_ClientProp.componentNameId = APP_Client.id
                        AND              attrName='Encryption Settings'
                        AND              APP_ClientProp.modified = 0
                """.format(self.tcinputs["ClientName"])
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)

                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 1:
                    # 1 stands for encryption enabled, 2 stands for no encryption
                    encrypted = True
                    self.log.info(
                        "query returned: encryption enabled from client level")

                # 0 stands for using storage policy settings for encryption
                elif result == 0:
                    self.log.info(
                        "query returned: using storage policy settings for encryption")
                    enc_type = [2, 3, 4, 5, 6, 8]
                    query = """
                            SELECT      encType
                            FROM        archGroup,archGroupCopy
                            WHERE       archGroup.name = '{0}'
                            AND         archGroup.id = archGroupCopy.archGroupId
                    """.format(self.plan_ob.storage_policy.storage_policy_name)
                    self.log.info("EXECUTING QUERY: %s", query)
                    self.csdb.execute(query)

                    result = int(self.csdb.fetch_one_row()[0])
                    self.log.info(f"QUERY OUTPUT : {result}")
                    if result in enc_type:
                        encrypted = True
                        self.log.info("query returned: encryption being used ")

                if matched_line or encrypted:
                    self.log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[3]]

                self.log.info(
                    "CASE 6: isCVSingleInstTarget, Target SP is Dedup SP ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[5], job.job_id)

                query = """
                    SELECT        sum(primaryObjects)+sum(secondaryObjects) as total_objects
                    FROM          archFile,archFileCopyDedup
                    WHERE         archfile.jobId = {0}
                    AND           archFile.id = archFileCopyDedup.archFileId
                """.format(job.job_id)
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")

                if result > 0:
                    self.log.info(
                        "query returned: Backup job used deduplication ")

                if matched_line or (result > 0):
                    self.log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[5]]

                self.log.info(
                    "CASE 7: ------------------"
                    "Validating: Network transfer Bytes -----------------  ")
                # client to ma flow
                network_bytes = self.dedup_helper.get_network_transfer_bytes(
                    job.job_id)
                self.log.info("Network transferred bytes: %s", network_bytes)
                dict_nw_transfer[iterator] = network_bytes
                if iterator == 2 and dict_nw_transfer[iterator] == dict_nw_transfer[iterator - 1]:
                    self.log.info("Network transfer rate validation: Pass")
                else:
                    if iterator == 1:
                        self.log.info(
                            "validation will be done at the end of next iterator")
                    else:
                        self._log.error(
                            "Network transfer bytes validation: Fail")
                        error_flag += ["Network transfer bytes validation: Fail"]

                self.log.info(
                    "CASE 8: Did Dedupe Occur correctly ?"
                    " comparing the primary and secondary objects "
                    "in the Dedup store ")
                primary_objects_count = self.dedup_helper.get_primary_objects(
                    job.job_id)
                self.log.info("Primary objects: %s", primary_objects_count)
                dict_prim[iterator] = primary_objects_count
                secondary_objects_count = self.dedup_helper.\
                    get_secondary_objects(job.job_id)
                self.log.info("Secondary objects: %s", secondary_objects_count)
                dict_sec[iterator] = secondary_objects_count

                # now if in second iteration then we check
                # second iter backup sec equals first iter backup primary
                # and vice versa
                if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1] \
                        and dict_prim[iterator] == dict_sec[iterator - 1]:
                    self.log.info("Dedupe validation: Pass")
                else:
                    if iterator == 1:
                        self.log.info(
                            "validation will be done at the end of next iteration")
                    else:
                        self._log.error("Dedupe validation: Fail")
                        error_flag += ["Dedupe validation: Fail"]

                self.log.info(
                    "CASE 9: check if block deduplication size is 64kb  ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[6], job.job_id)

                query = """
                            SELECT      SIBlockSizeKB
                            FROM        archGroup
                            WHERE       name='{0}'
                        """.format(self.plan_ob.storage_policy.storage_policy_name)
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])

                self.log.info(
                    "query returned: the block level deduplication factor is %d kb",
                    result)
                if matched_line or (result == 64):
                    self.log.info("Result :Pass")
                else:
                    self.log.error("Result: Failed")
                    raise ValueError("the block size is not 64kb")

            # checking for a synthetic full job
            # run the synthetic full job
            if self.mm_helper.create_uncompressable_data(
                    self.tcinputs['ClientName'], self.content_path, 0.2, 1):
                self.log.info("generated content for subclient %s", self.subclient_name)
            job = self.run_backup_job("Incremental")
            incr_primary_objects_count = self.dedup_helper.get_primary_objects(job.job_id)
            self.log.info("Primary objects: %s", incr_primary_objects_count)
            incr_secondary_objects_count = self.dedup_helper.get_secondary_objects(job.job_id)
            self.log.info("Secondary objects: %s", incr_secondary_objects_count)

            self.log.info("Case 10: checking Dedupe validation for Synthetic full Job")
            job = self.run_backup_job("Synthetic_full")
            self.log.info("Synthetic Full Backup job completed.")

            # verify the whether dedupe occurred
            primary_objects_count_synthetic_full = self.dedup_helper.get_primary_objects(job.job_id)
            secondary_objects_count_synthetic_full = self.dedup_helper.get_secondary_objects(job.job_id)

            # compare the objects with the first full backup job objects
            if int(secondary_objects_count_synthetic_full) == (int(dict_sec[2]) + int(incr_primary_objects_count)) \
                    and int(primary_objects_count_synthetic_full) == 0:
                self.log.info("Result: Pass")
            else:
                self.log.info("Result: Fail")
                error_flag += ["Dedupe Validation Synthetic Full Job Failed "]

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.error(error_flag)
                self.status = constants.FAILED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes all items of the testcase"""
        try:

            self.log.info("***************************  ******************")
            self.log.info("Restoring defaults")

            # set the encryption back to default
            self.log.info("setting encryption to default: Use SP settings")
            self.client.set_encryption_property("USE_SPSETTINGS")
            self.log.info(
                "setting encryption to default Use SP Settings: Done")

            # set the deduplication back to default
            self.log.info(
                "setting client deduplication to default: Use storage policy settings ")
            self.client.set_dedup_property(
                "clientSideDeduplication", "USE_SPSETTINGS")
            self.log.info(
                "setting client deduplication to default Use storage policy settings: Done")

            # delete the generated content for this testcase
            # machine object initialised earlier
            self.client_machine.remove_directory(self.content_path)
            self.log.info("Deleted the generated data")

            # run the previous_run_cleanup again to delete the backupset,
            # plan, storage pool after running the case
            self.previous_run_clean_up()
            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
