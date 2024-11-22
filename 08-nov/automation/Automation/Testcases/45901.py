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
    backupset and storage policy from the previous run

    run_backup_job() -- for running a backup job depending on argument

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

basic idea of the test case:
Checking whether media agent side deduplication is taking place
or not with SDT mode off (pipeline mode)

validations used:
1. Sigwhere: whether deduplication at media agent or not
2. Client dedup: should be disabled
3. Sig scheme: whether any signature generation algorithm used or not
4. Compression: is on or not
5. Encryption
6. CvSingleinst: whether the backup job is having dedup enabled or not at run time
7. Network transfer bytes
8. Did dedupe occur correctly


input json file arguments required:

            "45901" :{
            "ClientName": "name of the client machine without as in commserve",
            "AgentName": "File System",
            "MediaAgentName": "name of the media agent as in commserve"
            }
"""

from AutomationUtils import constants, machine, cvhelper
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
        self.name = "media agent side deduplication is taking place or not with SDT mode off (pipeline mode)"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None

        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
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
        self.backup_set = None
        self.subclient_ob = None
        self.media_agent_client_id = None
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.password = None
        self.storage_pool_ob = None
        self.plan_name = None
        self.storage_pool_name = None
        self.storage_assigned_ob = None
        self.plan_ob = None

    def setup(self):
        """assign values to variables for testcase"""
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.tcinputs["ClientName"], self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)
        self.media_agent_client_id = str(self.commcell.clients.get(self.tcinputs["MediaAgentName"])._get_client_id())

        # check if mount path and dedup path,library_name are user defined

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

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)

        # creating testcase directory, mount path, content path, dedup
        # store path
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)

        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"],
                                                                 self.id)
        else:
            if not self.is_user_defined_lib:
                self.mount_path = self.media_agent_machine.join_path(
                    self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.tcinputs["ClientName"])


        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)

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
            job_type                (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job type: %s", job_type)
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

            # create the required resources for the testcase
            # get the drive path with required free space

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
            self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type="Server",
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

            # turn pipeline mode on
            cs_machine_obj = machine.Machine(self.commcell.commserv_client)
            encrypted_pass = cs_machine_obj.get_registry_value(
                r"Database", "pAccess")
            self.password = cvhelper.format_string(
                self._commcell, encrypted_pass).split("_cv")[1]
            self.mm_helper.set_opt_lan("disable", self.commcell.commserv_hostname +
                                       "\\commvault", "sqladmin_cv",
                                       self.password, self.media_agent_client_id)
            # sdt mode turned off
            self.log.info("pipeline mode turned on")
            self.log.info("set up of the environment for "
                          "the testcase is completed")


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
                    'Using default pipeline mode [Pipeline] for [Bkp] pipe']

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
                    self.log.error("Result: Failed")
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
                    self.log.error("Result: Failed")
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
                    self.log.error("Result: Failed")
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
                    self.log.error("Result: Failed")
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
                    self.log.error("Result: Failed")
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
                    self.log.error("Result: Failed")
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
                        self.log.error(
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
                        self.log.error("Dedupe validation: Fail")
                        error_flag += ["Dedupe validation: Fail"]

                self.log.info("CASE 9: -- Checking from logs if "
                              "SDT mode has been DEACTIVATED "
                              "or pipeline mode activated")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[6], job.job_id)

                if matched_line:
                    self.log.info("Result: Pass _ SDT mode has been DEACTIVATED")
                else:
                    self.log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[6]]

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.error(error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes all items of the testcase"""
        try:

            self.log.info("*********************************************")
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

            # set the data transfer settings to default:
            # using optimised for concurrent LAN connections
            self.log.info("setting the data transfer "
                          "settings to default: using optimised "
                          "for concurrent LAN connections")
            self.mm_helper.set_opt_lan(
                "enable",
                self.commcell.commserv_hostname +
                "\\commvault",
                "sqladmin_cv",
                self.password,
                self.media_agent_client_id)
            self.log.info("setting the data transfer"
                          " settings to default: Done")

            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")


            # run the previous_run_cleanup again to delete the backupset,
            # plan, storage pool after running the case
            self.previous_run_clean_up()

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)

