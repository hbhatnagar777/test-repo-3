# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over
     backupset and storage policy from the previous run

    run_backup_job() -- for running a backup job of given type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


This testcase verifies if the client side dedupe is
taking place or not, uses client side cache with 2 splits
in the dedupe store, also uses high latency option
(makes sure that deduplication is taking place
entirely on the client.)

Prerequisites: None

input json file arguments required:

    "47072":{
            "ClientName": "name of the client machine without as in commserve",
            "AgentName": "File System",
            "MediaAgentName": "name of the media agent as in commserve"
            }

Design steps:
1. create resources and generate data
2. enable encryption on client
3. enable client side dedupe with cache
    3.1 enable high latency option
4. run two backup jobs
    4.1 FOR EACH BACK UP JOB WE HAVE THE FOLLOWING CHECKS
    4.2 client side dedupe enabled (query / log check)
    4.3 cache db enabled for client (query / log check)
    4.4 compression enabled (log check)
    4.5 signature generation algorithm being used (query / log check)
    4.6 compression being done on client (log check )
    4.7 encryption enabled (query / log check)
    4.8 CV single instance enabled / is target storage policy a dedupe storage policy
    4.9 check if high latency option for slow networks is enabled

    5. signatures processed and skipped validation
        5.1 signatures processed count
        5.2 signatures found in cache
        5.3 signatures found in DDB
        5.4 get application size
        5.5 size_compressed == size_transferred ?

    6. Did dedupe occur? comparing primary and secondary objects
7. Run an incremental job
8. Run a SynthFull job
9. Synthfull job validation by checking for new
 primary objects = 0, secondary objects > 0
10. Remove the resources created for this testcase.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
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
        self.name = "This is client side dedupe with cache case with 2 splits with high latency"
        self.tcinputs = {
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
        self.opt_selector = None
        self.testcase_path = None
        self.client_machine = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.backup_set = None
        self.subclient_ob = None
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
        """Setup function of this test case"""
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        self.plan_type = "Server"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

    def previous_run_clean_up(self):
        """deletes the items from the previous run"""
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


            # deleting storage pool
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
            job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job")
        job = self.subclient_ob.backup(job_type)
        self.log.info("Backup job: %s", str(job.job_id))
        self.log.info("job type: %s", job_type)
        if not job.wait_for_completion():
            raise Exception("Job {0} Failed with {1}".format(job.job_id, job.delay_reason))

        self.log.info("job %s complete", job.job_id)
        return job

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()

            dict_prim = {}
            dict_sec = {}
            dict_nw_transfer = {}
            skipped_signatures_across_jobs = []
            # create the required resources for the testcase
            # get the drive path with required free space

            drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
            drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)

            # creating testcase directory, mount path, content path, dedup
            # store path
            self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
            self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

            self.mount_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "mount_path")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

            self.content_path = self.client_machine.join_path(
                self.testcase_path_client, "content_path")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory already exists")
                self.client_machine.remove_directory(self.content_path)
                self.log.info("existing content deleted- so it doesn't interfere with dedupe")
            self.client_machine.create_directory(self.content_path)
            self.log.info("content path created")

            #  create storage pool
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

            # Disabling schedule policy from plan
            self.plan_ob.schedule_policies['data'].disable()

            # create backupset
            self.log.info(f"Creating Backupset [{self.backupset_name}]")
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)
            self.log.info(f"Backupset created [{self.backupset_name}]")

            # generate the content
            if self.mm_helper.create_uncompressable_data(self.client_machine, self.content_path, 0.3, 1):
                self.log.info("generated content for subclient %s", self.subclient_name)

            self.log.info(f"Creating subclient [{self.subclient_name}]")

            # Adding Subclient to Backupset
            self.subclient_ob = self.backup_set.subclients.add(self.subclient_name)
            self.log.info(f"Added subclient to backupset [{self.subclient_name}]")
            self.log.info("Adding plan to subclient")

            # Associating plan and content path to subclient
            self.subclient_ob.plan = [self.plan_ob, [self.content_path]]

            self.log.info("Added content and plan to subclient")

            self.subclient_ob.data_readers = 4
            self.subclient_ob.allow_multiple_readers = True

            # creating two partitions
            self.dedup_engines_obj = DeduplicationEngines(self.commcell)
            if self.dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
                self.dedup_engine_obj = self.dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = self.dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = self.dedup_engine_obj.get(dedup_store[0])
            self.log.info(
                f"Storage pool created with one partition. Adding 2nd partition for pool {self.storage_pool_name}")
            self.store_obj.add_partition(self.dedup_store_path, self.tcinputs['MediaAgentName'])

            self.log.info("added split for the dedup store")

            # enable encyption
            self.log.info("enabling encryption on client")
            self.client.set_encryption_property("ON_CLIENT", key="4", key_len="256")
            self.log.info("enabling encryption on client: Done")

            # enabling client side dedupe with cache and high latency optimization
            self.log.info("enabling client side dedupe with cache and high latency")
            self.client.set_dedup_property("clientSideDeduplication", "ON_CLIENT", True, 8192, True)
            self.log.info("Changing client properties: Done")


            # Run FULL backup
            self.log.info("Running full backup...")
            for iterator in range(1, 3):
                job = self.run_backup_job("FULL")

                self.log.info("*********************************** Validations ***************************************")
                error_flag = []
                log_file = 'cvd.log'
                config_strings_cvd = [
                    r'HandleLaunchAndGetPortReq.*?copy \[%s\]' % self.storage_assigned_ob.copy_id
                ]
                self.log.info('MA Validation 1: SIDB(DDB-MA) is connected from DM MA but not Client')
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.tcinputs.get('MediaAgentName'), log_file, config_strings_cvd[0], escape_regex=False)
                if matched_line:
                    for line in matched_line:
                        if (self.client.client_name in line) or (self.tcinputs.get('MediaAgentName') not in line):
                            self.log.error("result: Failed. Connection request source to SIDB is not as expected:\n"
                                           "LogLine: %s", line)
                            error_flag += ["result: Failed. Connection request source to SIDB is not as expected"]
                            break
                    if not error_flag:
                        self.log.info('result: Pass')
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find log line: " + config_strings_cvd[0]]

                log_file = "clBackup.log"
                config_strings_clbackup = [
                    'sigWhere[3]',
                    'Cache-DB lookup - Yes',
                    'Compress-enabled - Yes',
                    'sigScheme[4]',
                    'compressWhere[0]',
                    'encType[2]',
                    'CVSingleInstTarget[1]',
                    'EnabledOptimzedForLatency - Yes']

                self.log.info("CASE 1: IS CLIENT SIDE DEDUPE ENABLED?")

                query = """
                        SELECT      attrVal
                        FROM        APP_Client, APP_ClientProp
                        WHERE       APP_Client.name='{0}'
                        AND         APP_ClientProp.componentNameId = APP_Client.id
                        AND         attrName='Enable Deduplication'
                        AND         APP_ClientProp.modified = 0
                        """.format(self.client.client_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 1:  # 1 stands for de duplication enabled on client
                    self.log.info("query returned: Client side dedup is enabled")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[0], job.job_id)
                if matched_line or (result == 1):
                    self.log.info("result: PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[0]]

                self.log.info("CASE 2: IS CACHE DB ENABLED?")

                query = """
                        SELECT      attrVal
                        FROM        APP_Client, APP_ClientProp
                        WHERE       APP_Client.name='{0}'
                        AND         APP_ClientProp.componentNameId = APP_Client.id
                        AND         attrName='Enable Client Signature Cache'
                        AND         APP_ClientProp.modified = 0
                        """.format(self.client.client_name)

                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 1:  # 1 stands for client side cache being enabled
                    self.log.info("query returned: Client side cache is enabled")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[1], job.job_id)
                if matched_line or (result == 1):
                    self.log.info("result: PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[1]]

                self.log.info("CASE 3: IS COMPRESSION ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[2], job.job_id)
                if matched_line:
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[2]]

                self.log.info("CASE 4: IS SIGNATURE SCHEMA 4?")
                query = """
                        SELECT      SignatureType
                        FROM        IdxSIDBStore,archGroupCopy,archGroup
                        WHERE       archGroup.name='{0}'
                        AND         archGroup.id = archGroupCopy.archGroupId
                        AND         archGroupCopy.SIDBStoreId = IdxSIDBStore.SIDBStoreId
                        """.format(self.plan_ob.storage_policy.storage_policy_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 4:
                    self.log.info("query returned: Signature generation is being used")

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[3], job.job_id)
                if matched_line or (result == 4):
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[3]]

                self.log.info("CASE 5: IS COMPRESSION ON CLIENT?")

                query = """ SELECT  compressWhere
                            FROM    archPipeConfig,APP_Application
                            WHERE   APP_Application.subclientName = '{0}'
                            AND     archPipeConfig.appNumber = APP_Application.id""".format(self.subclient_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 0:
                    self.log.info("query returned source side compression on client is active")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[4], job.job_id)
                if matched_line or (result == 0):
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[4]]

                self.log.info("CASE 6: IS ENCRYPTION TYPE ENABLED?")
                encrypted = False
                query = """
                        SELECT      attrVal
                        FROM        APP_Client, APP_ClientProp
                        WHERE       APP_Client.name='{0}'
                        AND         APP_ClientProp.componentNameId = APP_Client.id
                        AND         attrName='Encryption Settings'
                        AND         APP_ClientProp.modified = 0
                """.format(self.client.client_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 1:
                    # 1 stands for encryption enabled, 2 stands for no encryption
                    encrypted = True
                    self.log.info("query returned: encryption enabled from client level")

                # 0 stands for using storage policy settings for encryption
                if result == 0:
                    self.log.info("query returned: using storage policy settings for encryption")
                    enc_type = [2, 3, 4, 5, 6, 8]
                    query = """
                        SELECT      encType
                        FROM        archGroup,archGroupCopy
                        WHERE       archGroup.name = '{0}'
                        AND         archGroup.id = archGroupCopy.archGroupId
                        """.format(self.plan_ob.storage_policy.storage_policy_name)
                    self.csdb.execute(query)

                    result = int(self.csdb.fetch_one_row()[0])
                    self.log.info(f"QUERY OUTPUT : {result}")
                    if result in enc_type:
                        encrypted = True
                        self.log.info("query returned: encryption being used ")

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[5], job.job_id)
                if matched_line or encrypted:
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[5]]

                self.log.info("CASE 7: IS CV SINGLE INSTANCE ENABLED?")
                query = """
                    SELECT      sum(primaryObjects)+sum(secondaryObjects) as total_objects
                    FROM        archFile,archFileCopyDedup
                    WHERE       archfile.jobId = {0}
                    AND         archFile.id = archFileCopyDedup.archFileId
                """.format(job.job_id)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                if result > 0:
                    self.log.info("query returned: Backup job used deduplication ")

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[6], job.job_id)
                if matched_line or (result > 0):
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[6]]

                self.log.info("CASE 8: is optimised for high latency enabled ?")
                query = """
                        SELECT      attrVal
                        FROM        APP_Client, APP_ClientProp
                        WHERE       APP_Client.name='{0}'
                        AND         APP_ClientProp.componentNameId = APP_Client.id
                        AND         attrName='Optimize for High Latency Networks'
                        AND         APP_ClientProp.modified = 0
                        """.format(self.client.client_name)
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])

                # csdb verification
                # 0 means high latency optimisation is disabled
                # 1 means high latency optimisation is enabled
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[7], job.job_id)
                if matched_line or (result == 1):
                    self.log.info("result: PASS")
                    self.log.info("optimised for high latency network - Yes")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[6]]

                if error_flag:
                    # if the list is not empty then error was there, fail the
                    # test case
                    self.log.info(error_flag)
                    raise Exception("testcase settings validation failed")

                self.log.info("*** Signature processed/skipped validations ***")
                error_flag = []
                total_sig_processed = 0
                found_in_cache_sig = 0
                found_in_ddb_count = 0

                self.log.info("CASE 1: SIGNATURE PROCESSED COUNT")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Signatures processed', job.job_id)
                if matched_line:
                    for line in matched_line:
                        total_sig_processed += int(line.split('-')[2].split(']')[0].strip())
                    self.log.info("Total Signatures processed = %d", total_sig_processed)
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find line: 'signature processed'"]

                self.log.info("CASE 2: SIGNATURE FOUND IN CACHE COUNT")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Found in cache', job.job_id)
                if matched_line:
                    for line in matched_line:
                        found_in_cache_sig += int(line.split("-")[6].split("]")[0].strip())
                    self.log.info("Found in cache %s", found_in_cache_sig)
                    # 4196 sig for each stream will be skipped to insert CLDB during 1st backup due to OOS fix
                    # we are not hard coding it in tc here for 4196 sig less. we just check for less than total sig.
                    if (iterator == 1 and found_in_cache_sig == 0) or (
                            iterator == 2 and 0 < found_in_cache_sig <= total_sig_processed):
                        self.log.info("result :PASS")
                    else:
                        self.log.error("result: Failed")
                        error_flag += ["Signatures count isn't as expected(0 <= cached <= total)"]
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find line: 'Found in cache'"]

                self.log.info("CASE 3: SIGNATURE FOUND IN DDB COUNT=0: Signatures not found in cache will be skipped")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Found in DDB', job.job_id)
                if matched_line:
                    for line in matched_line:
                        found_in_ddb_count += int(line.split("-")[7].split("]")[0].strip())
                    if found_in_ddb_count == 0:
                        self.log.info("found in DDB count %d", found_in_ddb_count)
                        self.log.info("result :PASS")
                    else:
                        self.log.info("found in DDB count non zero %s", str(found_in_ddb_count))
                        self.log.info("result:Failed")
                        error_flag += ["found in DDB count is non zero "]
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + 'Found in DDB']

                total_compressed_size = 0
                total_transferred_size = 0
                total_discarded_size = 0

                self.log.info("CASE 4: IS SIZE COMPRESSED == SIZE TRANSFERRED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-processed', job.job_id)
                if matched_line:
                    for line in matched_line:
                        total_compressed_size += int(line.split("-")[5].split(" ")[1])
                    self.log.info("compressed_size %d(%f GB)", total_compressed_size,
                                  total_compressed_size/(1024**3))

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-New Data-', job.job_id)
                if matched_line:
                    for line in matched_line:
                        total_transferred_size += int(line.split("-")[9].split("]")[0].split(" ")[1])
                    self.log.info("transferred_size %d(%f GB)", total_transferred_size,
                                  total_transferred_size/(1024**3))

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-Discarded', job.job_id)
                if matched_line:
                    for line in matched_line:
                        total_discarded_size += int(line.split("-")[7].split("]")[0].split(" ")[1])
                    self.log.info("discarded_size %d(%f GB)", total_discarded_size,
                                  total_discarded_size/(1024**3))

                # in 1st iteration all data will be transferred(size-new-data).
                # in 2nd iteration some data will be discarded(sig. found in cache)
                # and some data will be transferred(skipped signatures)
                if (iterator == 1 and total_compressed_size == total_transferred_size) or (
                        iterator == 2 and total_discarded_size != total_compressed_size
                        and total_compressed_size != total_transferred_size):
                    self.log.info("result :PASS")
                else:
                    self.log.error("result: Fail")
                    error_flag += ["failed in check: Size-Compressed == Size-Transferred"]

                self.log.info(r"CASE 5: DID DEDUPE OCCUR? 2nd BACKUP SHOULD HAVE 0 PRIMARY OBJECTS")
                data = int(self.dedup_helper.get_primary_objects(job.job_id))
                self.log.info("Primary Objects :%d", data)
                data1 = int(self.dedup_helper.get_secondary_objects(job.job_id))
                self.log.info("Secondary Objects :%d", data1)
                dict_prim[iterator] = data
                dict_sec[iterator] = data1
                if iterator == 2 and dict_sec[iterator] == dict_prim[iterator-1] \
                        and dict_prim[iterator] == dict_sec[iterator - 1]:
                    self.log.info("Dedupe validation:SUCCESS")
                else:
                    if iterator == 1:
                        self.log.info("validation will be done at the end of next iterator")
                    else:
                        self.log.error("Dedupe validation:FAILED")
                        error_flag += ["failed to validate Dedupe"]

                # checking for high latency optimised
                # for the first backup job, no signature will be
                # found in the cache, this means all the signatures will
                # be unique, since we had high latency enabled it will
                # not ask the media agent by sending the signatures
                # thus we will skip sending all the signatures and
                # send the data, SKIPPED ALL SIGNATURES
                # for the second backup job, we have the same data
                # and all the signatures will be present in the
                # client side local cache, this means it will not
                # need to ask media agent about the new signatures and
                # it will simply send signatures for entry in the
                # secondary table SKIPPED 0
                # the key idea is - high latency optimisation
                # leads to one way
                # client to media agent communication

                self.log.info("****** CASE 6:CHECKING FOR HIGH LATENCY OPTIMISED BY FINDING SIGNATURES COUNT *********")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Skipped-', job.job_id)
                if matched_line:
                    skipped_signatures = 0
                    for line in matched_line:
                        skipped_signatures += int(line.split("-")[10].split("]")[0].strip())
                    skipped_signatures_across_jobs.append(skipped_signatures)
                    # we need first job skipped signatures to be equal to the
                    # total signatures and in 2nd job few signatures (4196*streams count) will be skipped due to OOS fix
                    self.log.info("skipped signatures %d", skipped_signatures)
                    if(iterator == 1 and skipped_signatures_across_jobs[0] == total_sig_processed) or\
                            (iterator == 2
                             and skipped_signatures_across_jobs[1] == total_sig_processed-found_in_cache_sig):
                        self.log.info("for job %d", iterator)
                        self.log.info("total signatures %s", total_sig_processed)
                        self.log.info("result: PASS")
                    else:
                        self.log.info("result: failed: entries don't match as expected")
                        error_flag += ["entries don't match as expected"]
                else:
                    self.log.info("result: failed: skipped entries not found")
                    error_flag += ["skipped entries not found"]

                self._log.info("-------- validating: N/W TRANSFER BYTES -----------")
                network_bytes = int(self.dedup_helper.get_network_transfer_bytes(job.job_id))
                self.log.info("Network transferred bytes: %d", network_bytes)
                dict_nw_transfer[iterator] = network_bytes
                if iterator == 2 and dict_nw_transfer[iterator] < dict_nw_transfer[iterator - 1]:
                    self._log.info("Network transfer rate validation: PASS")
                else:
                    if iterator == 1:
                        self.log.info("validation will be done at the end of next iterator")
                    else:
                        self.log.error("Network transfer bytes validation: Fail")
                        error_flag += ["Network transfer bytes validation: Fail"]

                if error_flag:
                    # if the list is not empty then error was there, fail the
                    # test case
                    self.log.info(error_flag)
                    raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

def tear_down(self):
    """delete all the resources for this testcase"""
    self.log.info("Tear down function of this test case")
    try:

        self.log.info("*********************************************")
        self.log.info("restoring defaults")

        # disable client side dedupe and high latency
        self.log.info("setting client deduplication to default: Use storage policy settings ")
        self.client.set_dedup_property("clientSideDeduplication", "ON_CLIENT", True, 8192, False)
        self.client.set_dedup_property("clientSideDeduplication", "USE_SPSETTINGS")
        self.client.set_dedup_property("clientSideDeduplication", "OFF")
        self.log.info("setting client deduplication to default Use storage policy settings: Done")

        # set the encryption back to default
        self.log.info("setting encryption to default: Use SP settings")
        self.client.set_encryption_property("USE_SPSETTINGS")
        self.log.info("setting encryption to default Use SP Settings: Done")

        # delete the generated content for this testcase
        # machine object initialised earlier
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("Deleted the generated data.")
        else:
            self.log.info("Content directory does not exist.")

        self.previous_run_clean_up()
        self.log.info("clean up successful")

    except Exception as exp:
        self.log.info("clean up not successful")
        self.log.info("ERROR: %s",  exp)
