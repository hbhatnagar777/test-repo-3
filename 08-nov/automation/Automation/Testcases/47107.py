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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over
     backupset and storage policy from the previous run

    run_backup_job() -- for running a backup job of given type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase checks if client side dedupe is working
or not with cache enabled on client, default size of cache
1024 is used for the purpose of this case with
no splits in dbb and cloud library support.

Prerequisites: None

Input format:
    "MediaAgentName": "name of the media agent as in commserve",
    "CloudLib"  yes or no whether you want to
                create a cloud library or disk library
                    * enter the cloud library credentials
                    if you want to create a cloud library
                      in the input file for the testcase
                "S3Region": None,
                "S3CloudBucket": None,
                "S3AccessKey":None,
                "S3SecretKey":None,
                "CloudVendor":None,
    "dedup_path": path where dedup store to be created [for linux MediaAgents, User must explicitly
                                            provide a dedup path that is inside a Logical Volume.
                                            (LVM support required for DDB)]

    note --
                ***********************************
                if dedup_path_given -> use_given_dedup_path
                else it will auto_generate_dedup_path

                for CloudVendor, refer to mediagentconstants.py
                ***********************************

Design steps:
1. create resources and generate data
2. enable encryption on client
3. enable client side dedupe with cache
4. run two backup jobs
    4.1 FOR EACH BACK UP JOB WE HAVE THE FOLLOWING CHECKS
    4.2 client side dedupe enabled (query / log check)
    4.3 cache db enabled for client (query / log check)
    4.4 compression enabled (log check)
    4.5 signature generation algorithm being used (query / log check)
    4.6 compression being done on client (log check )
    4.7 encryption enabled (query / log check)
    4.8 CV single instance enabled / is target storage policy a dedupe storage policy

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
signatures encountered - count should be 0,
 primary objects = 0, secondary objects > 0
10. Remove the resources created for this testcase.
"""


from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils import mahelper



class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "client side dedupe with no splits in dbb and cloud library support"

        self.tcinputs = {
            "MediaAgentName": None,
            "cloudlib": None,
            "S3Region": None,
            "S3CloudBucket": None,
            "S3AccessKey": None,
            "S3SecretKey": None,
            "CloudVendor": None
        }

        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
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
        self.is_user_defined_dedup = False
        self.storage_pool_name = None
        self.storage_assigned_ob = None
        self.plan_ob = None
        self.plan_name = None
        self.plan_type = None


    def setup(self):
        """Setup function of this test case"""
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.client.client_name)
        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.plan_type = "Server"

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        # create the required resources for the testcase
        # get the drive path with required free space

        drive_path_client = self.opt_selector.get_drive(
            self.client_machine)
        drive_path_media_agent = self.opt_selector.get_drive(
            self.media_agent_machine)

        # creating testcase directory, mount path, content path, dedup
        # store path
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        self.mount_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "mount_path")
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
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

        self.restore_path = self.client_machine.join_path(
            self.testcase_path_client, "restore_path")
        if self.client_machine.check_directory_exists(self.restore_path):
            self.log.info("restore path directory already exists")
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("existing restore path deleted")
        self.client_machine.create_directory(self.restore_path)
        self.log.info("restore path created")

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up started **********")
        try:
            # deleting Backupset
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset.")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Backupset deleted.")

            # deleting disk library
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted")
            else:
                self.log.info("Library does not exist.")

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
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))

        self.log.info("job %s complete", job.job_id)
        return job

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()

            dict_prim = {}
            dict_sec = {}

            # create the required resources for the testcase

            # create library
            # the library creation can be disk or cloud
            if self.tcinputs["cloudlib"].lower() == "yes":
                # by default amazon s3 cloud
                self.library = self.mm_helper.configure_cloud_library(
                    self.library_name,
                    self.tcinputs["MediaAgentName"],
                    self.tcinputs["S3CloudBucket"],
                    self.tcinputs["S3Region"] +
                    "//" +
                    self.tcinputs["S3AccessKey"],
                    self.tcinputs["S3SecretKey"],
                    self.tcinputs["CloudVendor"])
            elif self.tcinputs["cloudlib"].lower() == "no":
                self.library = self.mm_helper.configure_disk_library(
                    self.library_name, self.tcinputs["MediaAgentName"], self.mount_path)
            else:
                raise ValueError("Proper inputs for "
                                 "Library creation not given")

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
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.content_path, 0.5, 1):
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

            # enable encyption
            self.log.info("enabling encryption on client")
            self.client.set_encryption_property(
                "ON_CLIENT", key="4", key_len="256")
            self.log.info("enabling encryption on client: Done")

            # enabling client side dedupe with cache
            self.log.info("enabling client side dedupe with cache")
            self.client.set_dedup_property(
                "clientSideDeduplication", "ON_CLIENT", True, 1024)
            self.log.info("enabling client side cache: Done")

            # Run FULL backup
            self.log.info("Running full backup...")
            for iterator in range(1, 3):
                job = self.run_backup_job("FULL")

                self.log.info("*************** Validations ****************")
                log_file = "clBackup.log"
                config_strings_clbackup = [
                    'sigWhere[3]',
                    'Cache-DB lookup - Yes',
                    'Compress-enabled - Yes',
                    'sigScheme[4]',
                    'compressWhere[0]',
                    'encType[2]',
                    'CVSingleInstTarget[1]']
                error_flag = []
                self.log.info("CASE 1: IS CLIENT SIDE DEDUPE ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[0], job.job_id)

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
                if result == 1:  # 1 stands for de duplication enabled on client
                    self.log.info(
                        "query returned: Client side dedup is enabled")

                if matched_line or (result == 1):
                    self.log.info("result: Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[0]]

                self.log.info("CASE 2: IS CACHE DB ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[1], job.job_id)

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

                if result == 1:  # 1 stands for client side cache being enabled
                    self.log.info(
                        "query returned: Client side cache is enabled")

                if matched_line or (result == 1):
                    self.log.info("result: Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[1]]

                self.log.info("CASE 3: IS COMPRESSION ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[2], job.job_id)
                if matched_line:
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[2]]

                self.log.info("CASE 4: IS SIGNATURE SCHEMA 4?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[3], job.job_id)
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

                if result == 4:
                    self.log.info(
                        "query returned: Signature generation is being used")
                if matched_line or (result == 4):
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[3]]

                self.log.info("CASE 5: IS COMPRESSION ON CLIENT?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[4], job.job_id)

                query = """ SELECT  compressWhere
                            FROM    archPipeConfig,APP_Application
                            WHERE   APP_Application.subclientName = '{0}'
                            AND     archPipeConfig.appNumber = APP_Application.id""".format(self.subclient_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])

                if result == 0:
                    self.log.info("query returned source side"
                                  " compression on client is active")

                if matched_line or (result == 0):
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[4]]

                self.log.info("CASE 6: IS ENCRYPTION TYPE ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[5], job.job_id)
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
                if result == 1:
                    # 1 stands for encryption enabled, 2 stands for no encryption
                    encrypted = True
                    self.log.info(
                        "query returned: encryption enabled from client level")

                # 0 stands for using storage policy settings for encryption
                if result == 0:
                    self.log.info(
                        "query returned: using storage policy settings for encryption")
                    enc_type = [2, 3, 4, 5, 6, 8]
                    query = """
                        SELECT      encType
                        FROM        archGroup,archGroupCopy
                        WHERE       archGroup.name = '{0}'
                        AND         archGroup.id = archGroupCopy.archGroupId
                    """.format(self.plan_ob.storage_policy.storage_policy_name)
                    self.csdb.execute(query)

                    result = int(self.csdb.fetch_one_row()[0])
                    if result in enc_type:
                        encrypted = True
                        self.log.info("query returned: encryption being used ")

                if matched_line or encrypted:
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[5]]

                self.log.info("CASE 7: IS CV SINGLE INSTANCE ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[6], job.job_id)
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
                    self.log.info(
                        "query returned: Backup job used deduplication ")

                if matched_line or (result > 0):
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[6]]

                if error_flag:
                    # if the list is not empty then error was there, fail the
                    # test case
                    self.log.info(error_flag)
                    raise Exception("testcase settings validation failed")

                # signature result processed and skipped validation
                self.log.info(
                    "*** Signature processed/skipped validations ***")
                error_flag = []

                self.log.info("CASE 1: SIGNATURE PROCESSED COUNT")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Signatures processed', job.job_id)
                if matched_line:
                    signature_processed = matched_line[0].split(
                        "-")[2].split("]")[0]
                    total_sig_processed = signature_processed
                    self.log.info(
                        "Signature processed =" +
                        signature_processed)
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + 'signature processed']

                self.log.info("CASE 2: SIGNATURE FOUND IN CACHE COUNT")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Found in cache', job.job_id)
                if matched_line:
                    signature_processed = matched_line[0].split(
                        "-")[6].split("]")[0]
                    found_in_cache_sig = signature_processed
                    self.log.info(
                        "Signature processed %s", total_sig_processed)
                    self.log.info("matched %s", found_in_cache_sig)

                    if (iterator == 1 and int(signature_processed) == 0) or (
                            iterator == 2 and int(found_in_cache_sig) == int(total_sig_processed)):
                        self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + 'Found in cache']

                # first run nothing present in dedup store,
                # no entries in cache and ddb
                # second run, since all entries in cache
                # no need to be found in ddb, if found in ddb means some issue
                # with cache that it couldn't find that particular entry in
                # cache

                self.log.info("CASE 3: SIGNATURE FOUND IN DDB COUNT")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Found in DDB', job.job_id)
                if matched_line:
                    found_in_ddb_count = int(
                        matched_line[0].split("-")[7].split("]")[0])
                    if found_in_ddb_count == 0:
                        self.log.info(
                            "found in DDB count %d",
                            found_in_ddb_count)
                        self.log.info("result :Pass")
                    else:
                        self.log.info(
                            "found in DDB count non zero %s",
                            str(found_in_ddb_count))
                        self.log.info("result:Failed")
                        error_flag += ["found in DDB count is non zero "]
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + 'Found in DDB']

                self.log.info("CASE 4: GET APPLICATION SIZE")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-Application', job.job_id)
                if matched_line:
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Failed")
                    error_flag += ["failed to find: " + 'Size-Application']

                self.log.info(
                    "CASE 5: IS SIZE COMPRESSED == SIZE TRANSFERRED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-processed', job.job_id)
                if matched_line:
                    compressed_size = matched_line[0].split(
                        "-")[5].split(" ")[1]
                    total_compressed_size = compressed_size
                    self.log.info("compressed_size %s", compressed_size)

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-New Data-', job.job_id)
                if matched_line:
                    transferred_size = matched_line[0].split(
                        "-")[9].split("]")[0].split(" ")[1]
                    total_transferred_size = transferred_size
                    self.log.info("transferred_size %s", transferred_size)

                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, 'Size-Discarded', job.job_id)
                if matched_line:
                    discarded_size = matched_line[0].split(
                        "-")[7].split("]")[0].split(" ")[1]
                    total_discarded_size = discarded_size
                    self.log.info("discarded_size %s", discarded_size)

                if (iterator == 1 and total_compressed_size == total_transferred_size) or (
                        iterator == 2 and total_discarded_size == total_compressed_size):
                    self.log.info("result :Pass")
                else:
                    self.log.error("result: Fail")
                    error_flag += ["failed in check: Size-Compressed == Size-Transferred"]

                self.log.info(
                    r"CASE 6: DID DEDUPE OCCUR? 2nd BACKUP SHOULD HAVE 0 PRIMARY OBJECTS")
                data = int(self.dedup_helper.get_primary_objects(job.job_id))
                self.log.info("Primary Objects :%d", data)
                data1 = int(self.dedup_helper.get_secondary_objects(job.job_id))
                self.log.info("Secondary Objects :%d", data1)
                dict_prim[iterator] = data
                dict_sec[iterator] = data1
                if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1] \
                        and dict_prim[iterator] == dict_sec[iterator - 1]:
                    self.log.info("Dedupe validation:SUCCESS")
                else:
                    if iterator == 1:
                        self.log.info(
                            "validation will be done at the end of next iterator")
                    else:
                        self.log.error("Dedupe validation:FAILED")
                        error_flag += ["failed to validate Dedupe"]

                if error_flag:
                    # if the list is not empty then error was there, fail the
                    # test case
                    self.log.info(error_flag)
                    raise Exception("testcase failed")

            # restore
            self.log.info("running restore job")
            restorejob = self.subclient_ob.restore_out_of_place(
                self.client.client_name, self.restore_path, [
                    self.content_path], True, True)
            self.log.info("restore job: " + restorejob.job_id)
            if not restorejob.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        restorejob.delay_reason))
            self.log.info("restore job completed")

            self.log.info("VERIFYING IF THE RESTORED FILES ARE SAME OR NOT")
            restored_files = self.client_machine.get_files_in_path(
                self.restore_path)
            self.log.info("Comparing the files using MD5 hash")
            if len(restored_files) == len(content_files):
                restored_files.sort()
                for original_file, restored_file in zip(
                        content_files, restored_files):
                    if not self.client_machine.compare_files(
                            self.client_machine, original_file, restored_file):
                        self.log.info("Result: Fail")
                        raise ValueError("The restored file is "
                                         "not the same as the original content file")
            self.log.info("All the restored files "
                          "are same as the original content files")
            self.log.info("Result: Pass")

            # adding more content before running incremental backup
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name,
                    self.client_machine.join_path(self.content_path, "Additional_data"), 0.3, 1):
                self.log.info(
                    "added more content for subclient %s", self.subclient_name)
            self.subclient_ob.content = [self.content_path]

            # incremental before synth full
            incr_job = self.run_backup_job("incremental")

            # synth full
            synthfull_job = self.run_backup_job("Synthetic_full")

            # synth full backup validation

            self.log.info(
                "VALIDATING SYNTHFULL JOB: PRIMARY OBJECTS IN CSDB SHOULD BE 0")
            data = self.dedup_helper.get_primary_objects(synthfull_job.job_id)
            self.log.info("Primary Objects :" + str(data))
            if str(data) == "0":
                self.log.info("result: Pass")
            else:
                self.log.error("result: Fail")
                raise Exception(
                    "Failed in synthfull job validation"
                )
            self.log.info(
                "VALIDATING SYNTHFULL JOB: SECONDARY OBJECTS IN CSDB SHOULD BE GREATER THAN 0")
            data = self.dedup_helper.get_secondary_objects(
                synthfull_job.job_id)
            self.log.info("Secondary Objects :" + str(data))
            if str(data) == "0":
                self.log.error("result: Fail")
                raise Exception(
                    "Failed in synthfull job validation"
                )

            else:
                self.log.info("result: Pass")

        except Exception as exp:
            self.log.error(
                'Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        "delete all the resources for this testcase"
        self.log.info("Tear down function of this test case")
        try:

            self.log.info("*********************************************")
            self.log.info("restoring defaults")

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
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            # delete mount path and dedup path
            self.media_agent_machine.remove_directory(self.dedup_store_path)
            self.client_machine.remove_directory(self.mount_path)

            # run the previous_run_cleanup again to delete the backupset,
            # plan, storage pool after running the case
            self.previous_run_clean_up()

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
