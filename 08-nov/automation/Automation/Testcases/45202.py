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
    backupset and storage pool,plan from the previous run

    run_full_backup_job() -- for running a full backup job


    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


this test case will check if client side dedupe with no cache is working or not

prerequisites: None

the testcase will change the following settings but
they will be reverted after the test case finishes its run:
    1. client side dedupe will be set to enable.
    2. use of client side cache will be set to off.


inputs required for the testcase:
            "MediaAgentName"
            "mount_path": path where the data is to be stored
            "dedup_path": path where dedup store to be created [for linux MediaAgents, User must explicitly provide a
                                                                dedup path that is inside a Logical Volume.
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



from AutomationUtils import constants , machine
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
        self.name = "Client side dedupe no cache enabled case"
        self.tcinputs = {
            "MediaAgentName": None
        }

        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.subclient_ob = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.storage_assigned_ob = None
        self.plan_name = None
        self.plan_ob = None
        self.storage_pool_name = None
        self.agent = None
        self.plan_type = None

    def setup(self):
        """assign values to common variables"""
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        self.plan_type = "Server"

        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.client.client_name)

        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.plan_name = "{0}_Plan{1}".format(str(self.id), suffix)
        self.storage_pool_name = "{0}_SP{1}".format(str(self.id), suffix)

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

        # check if library name, mount path
        # and dedup path are user defined

        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        # create the required resources for the testcase
        # get the drive path with required free space

        drive_path_client = self.opt_selector.get_drive(self.client_machine)
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        # creating testcase directory,
        # mount path, content path, dedup store path
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
        else:
            if not self.is_user_defined_lib:
                self.mount_path = self.media_agent_machine.join_path(
                    self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
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

    def previous_run_clean_up(self):
        """delete the resources from previous run """
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

    def run_full_backup_job(self):
        """run a full backup job"""
        self.log.info("Starting backup job")
        job = self.subclient_ob.backup("FULL")
        self.log.info("Backup job: %s", job.job_id)
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

            # create the required resources for the testcase
            dict_nw_transfer = {}
            dict_prim = {}
            dict_sec = {}

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

            # enable encyption
            self.log.info("Enabling encryption on client")
            self.client.set_encryption_property(
                "ON_CLIENT", key="4", key_len="256")
            self.log.info("Enabling encryption on client: Done")

            # turn client side dedupe on
            # turn use of cache off
            self.log.info("Enabling client side dedupe with no cache")
            self.client.set_dedup_property("clientSideDeduplication",
                                           "ON_CLIENT",
                                           client_side_cache=False)
            self.log.info("Enabling client side dedupe with no cache: Done")

            # for twice run
            # Run FULL backup
            self.log.info("Running full backup...")
            for iterator in range(1, 3):
                job = self.run_full_backup_job()

                # do the checks
                log_file = "clBackup.log"
                config_strings_clbackup = ['[isClientSideDedupEnabled - yes]',
                                           '[CacheDBSize - 0 MB]',
                                            'sigScheme[4]',
                                            'compressWhere[0]',
                                            'encType[2]',
                                            'CVSingleInstTarget[1]']
                error_flag = []
                self.log.info("*************** Validations ****************")
                self.log.info("CASE 1: check if the"
                              " client side Deduplication is enabled ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[0], job.job_id)

                query = """
                        SELECT      attrVal
                        FROM        APP_Client, APP_ClientProp
                        WHERE       APP_Client.name='{0}'
                        AND         APP_ClientProp.componentNameId = APP_Client.id
                        AND         attrName='Enable Deduplication'
                        AND         APP_ClientProp.modified = 0
                """.format(self.client.client_name)
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)

                result = int(self.csdb.fetch_one_row()[0])
                # 1 stands for
                # de duplication enabled on client

                if matched_line or (result == 1):
                    self.log.info("Result: Pass")
                else:
                    self.log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[0]]

                self.log.info("CASE 2: check if the "
                              "client side Cache is disabled ")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[1], job.job_id)

                query = """
                                SELECT      attrVal
                                FROM        APP_Client, APP_ClientProp
                                WHERE       APP_Client.name='{0}'
                                AND         APP_ClientProp.componentNameId = APP_Client.id
                                AND         attrName='Enable Client Signature Cache'
                                AND         APP_ClientProp.modified = 0
                        """.format(self.client.client_name)
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)

                result = int(self.csdb.fetch_one_row()[0])
                # 0 stands for client side cache being disabled

                if matched_line or (result == 0):
                    self.log.info("Result: Pass")
                else:
                    self.log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[1]]

                self.log.info("CASE 3: IS SIGNATURE SCHEMA 4?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[2], job.job_id)
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
                                   config_strings_clbackup[2]]

                self.log.info("CASE 4: IS COMPRESSION ON CLIENT?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[3], job.job_id)

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
                                   config_strings_clbackup[3]]

                self.log.info("CASE 5: IS ENCRYPTION TYPE ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[4], job.job_id)
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
                    """.format(self.plan_name)
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
                                   config_strings_clbackup[4]]

                self.log.info("CASE 6: IS CV SINGLE INSTANCE ENABLED?")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_name, log_file, config_strings_clbackup[5], job.job_id)
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
                                   config_strings_clbackup[5]]


                self.log.info(
                    "CASE 7: -------------------"
                    "Validating: Network transfer Bytes -----------------  ")
                # client to ma flow
                # first backup job, all new data,
                # generate signatures, since first
                # backup job then MA not seen the
                # signatures earlier, send alot of data to MA (signatures + unique blocks)
                # second backup job signatures generated
                # at client, no cache at client, since MA seen the signatures
                # earlier, not unique MA will tell the client,
                # 100% dedupe, then send only the signatures
                # thus data sent after the second backup job will be
                # lesser than the data sent after the first
                # backup job
                network_bytes = int(self.dedup_helper.get_network_transfer_bytes(
                    job.job_id))
                self.log.info("Network transferred bytes: %d", network_bytes)
                dict_nw_transfer[iterator] = network_bytes
                if iterator == 2 and dict_nw_transfer[iterator]\
                        < dict_nw_transfer[iterator - 1]:
                    self.log.info("Network transfer rate validation: Pass")
                else:
                    if iterator == 1:
                        self.log.info("validation will be done"
                                      " at the end of next iterator")
                    else:
                        self.log.error(
                            "Network transfer bytes validation: Fail")
                        error_flag += ["Network transfer bytes validation: Fail"]

                self.log.info("CASE 8: Did Dedupe Occur correctly ?"
                              " comparing the primary and secondary objects "
                              "in the Dedup store ")
                primary_objects_count = self.dedup_helper.get_primary_objects(
                    job.job_id)
                self.log.info("Primary objects: %s", str(primary_objects_count))
                dict_prim[iterator] = primary_objects_count
                secondary_objects_count = self.dedup_helper.get_secondary_objects(
                    job.job_id)
                self.log.info(
                    "Secondary objects: %s",
                    str(secondary_objects_count))
                dict_sec[iterator] = secondary_objects_count

                # now if in second iteration then we check second iter
                # backup sec equals first iter backup primary
                # and vice versa
                if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1]\
                        and dict_prim[iterator] == dict_sec[iterator - 1]:
                    self.log.info("Dedupe validation: Pass")
                else:
                    if iterator == 1:
                        self.log.info("validation will be done"
                                      " at the end of next iteration")
                    else:
                        self.log.error("Dedupe validation: Fail")
                        error_flag += ["Dedupe validation: Fail"]

            if error_flag:
                # if the list is not empty
                # then error was there, fail the test case
                self.log.error(error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute'
                                ' test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all the items for this testcase"""

        try:

            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            # set the deduplication back to default
            self.log.info("setting client deduplication to default: "
                          "Use storage policy settings ")
            self.client.set_dedup_property(
                "clientSideDeduplication", "USE_SPSETTINGS")
            self.log.info("setting client deduplication to default"
                          " Use storage policy settings: Done")

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
