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

    previous_run_cleanup() -- for deleting the left over backupset
    and storage policy from the previous run

    run_full_backup_job()   --  run a full backup job

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


this test case will check if client side dedupe with no cache is working or not,
having 2 partitions in the dedupe store and this all should be in pipeline data transfer mode.

prerequisites: None

the testcase will change the following settings but
they will be reverted after the test case finishes its run:
    1. client side dedupe will be set to enable.
    2. use of client side cache will be set to off.
    3. for data transfer pipeline mode will be turned on.

inputs required for the testcase:
            "45038":{
            "MediaAgentName": "Name of Media Agent",
            "library_name": "name of the Library to be reused",
            "mount_path": "path where the data is to be stored",
            "dedup_path": "path where dedup store to be created"
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

Design Steps:
1.	Resources
2.	Client side dedupe on, cache off, pipeline mode on
3.	Over two backup jobs
4.	Check in clbackup log
5.	Client side dedup enabled (log + query)
6.	Client Cache not enabled (log size 0, query)
7.	Network transfer bytes (first > second)
8.	Dedup occur or not
"""


from AutomationUtils import constants, cvhelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
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
        self.name = "Client side dedupe case with no cache case having 2 splits in pipeline mode"

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
        self.client_machine = None
        self.media_agent_machine = None
        self.testcase_path = None
        self.password = None
        self.media_agent_client_id = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.backup_set = None
        self.subclient_ob = None
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.plan_name = None
        self.storage_pool_name = None
        self.storage_assigned_ob = None
        self.plan_ob = None
        self.dedup_engines_obj = None
        self.dedup_engine_obj = None
        self.store_obj = None

    def setup(self):
        """Setup function of this test case"""
        # check if mount path and dedup path,library_name are user defined

        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.client.client_name)

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = Machine(
            self.tcinputs["MediaAgentName"], self.commcell)
        self.media_agent_client_id = str(self.commcell.clients.get(self.tcinputs["MediaAgentName"])._get_client_id())

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

            # create the required resources for the testcase
            # get the drive path with required free space

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        # creating testcase directory, mount path, content path, dedup
        # store path
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
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

        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("old content path deleted")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

    def previous_run_clean_up(self):
        """delete the resources from previous run"""
        self.log.info("********* previous run clean up started **********")
        try:

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset.")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Backupset deleted.")

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Plan exists, deleting that")
                self.commcell.plans.delete(self.plan_name)
                self.log.info("Plan deleted.")

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"pool[{self.storage_pool_name}] exists, deleting that")
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info("pool primary deleted.")

            self.log.info("********* previous run clean up ended **********")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_full_backup_job(self):
        """function for running full backup job"""
        self.log.info("Starting backup job")
        job = self.subclient_ob.backup("FULL")
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Job {0} Failed with {1}".
                            format(job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)
        return job

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()
            dict_prim = {}  # to be used later for comparing primary
            # /secondary objects
            dict_sec = {}
            dict_nw_transfer = {}  # to be used later for network
            # transfer bytes verification

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

            # creating two partitions
            self.dedup_engines_obj = DeduplicationEngines(self.commcell)
            if self.dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
                self.dedup_engine_obj = self.dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = self.dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.storage_assigned_ob = self.dedup_engine_obj.get(dedup_store[0])
            self.log.info(
                f"Storage pool created with one partition. Adding 2nd partition for pool {self.storage_pool_name}")
            self.storage_assigned_ob.add_partition(self.dedup_store_path, self.tcinputs['MediaAgentName'])

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
            self.subclient_ob = self.backup_set.subclients.add(self.subclient_name)
            self.log.info(f"Added subclient to backupset [{self.subclient_name}]")
            self.log.info(f"{type(self.plan_name)}, {type(self.content_path)}")
            self.log.info("Adding plan to subclient")
            self.subclient_ob.plan = [self.plan_ob, [self.content_path]]

            self.log.info("Added content and plan to subclient")

            # turn client side dedupe on
            # turn use of cache off
            self.log.info("enabling client side dedupe with no cache")
            self.client.set_dedup_property(
                "clientSideDeduplication",
                "ON_CLIENT",
                client_side_cache=False)
            self.log.info("enabling client side dedupe with no cache: Done")

            # turn pipeline mode on
            cs_machine_obj = Machine(self.commcell.commserv_client)
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
                job = self.run_full_backup_job()
                # do the checks
                log_file = "clBackup.log"
                config_strings_clbackup = ['[isClientSideDedupEnabled - yes]',
                                           '[CacheDBSize - 0 MB]',
                                           'Using default pipeline mode [Pipeline] for [Bkp] pipe']
                error_flag = []
                self.log.info("*************** Validations ****************")
                self.log.info(
                    "CASE 1: check if the client side Deduplication is enabled ")
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
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)

                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == 1:        # 1 stands for de duplication enabled on client
                    self.log.info(
                        "query returned: Client side dedup is enabled")

                if matched_line or (result == 1):
                    self.log.info("Result: Pass")
                else:
                    self.log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[0]]

                self.log.info(
                    "CASE 2: check if the client side Cache is disabled ")
                (matched_line, matched_string) = self.dedup_helper.\
                    parse_log(self.client.client_hostname, log_file,
                              config_strings_clbackup[1], job.job_id)

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
                if result == 0:  # 0 stands for client side cache being disabled
                    self.log.info(
                        "query returned: Client side cache is disabled")

                if matched_line or (result == 0):
                    self.log.info("Result: Pass")
                else:
                    self.log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[1]]


                self.log.info("CASE 3: -- Checking from logs if "
                              "pipeline mode has been activated")
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[2], job.job_id)

                if matched_line:
                    self.log.info("Result: Pass _ Pipeline mode has been activated")
                else:
                    self.log.error("Result: Failed")
                    error_flag += ["failed to find: " +
                                   config_strings_clbackup[2]]


                self.log.info(
                    "CASE 4: ------------------"
                    "-Validating: Network transfer Bytes -----------------  ")
                # client to ma flow
                # first backup job, all new data, generate signaturesult,
                # since first backup job then MA not seen the
                # signatures earlier, send alot of data to MA
                # (signatures + unique blocks)
                # second backup job signatures generated at client,
                # no cache at client, since MA seen the signature
                # earlier, not unique MA will tell the client,
                # 100% dedupe, then send only the signatures
                # thus data sent after the second backup job
                # will be lesser than the data sent after the first
                # backup job

                network_bytes = self.dedup_helper.get_network_transfer_bytes(
                    job.job_id)
                self.log.info("Network transferred bytes: " + network_bytes)
                dict_nw_transfer[iterator] = network_bytes
                self.log.info("%s = %s" %
                              (iterator, dict_nw_transfer[iterator]))
                if iterator == 2 and int(dict_nw_transfer[iterator])\
                        < int(dict_nw_transfer[iterator - 1]):
                    self.log.info("Network transfer Bytes validation: Pass")
                else:
                    if iterator == 1:
                        self.log.info(
                            "validation will be done at the end of next iterator")
                    else:
                        self.log.error(
                            "Network transfer bytes validation: Fail")
                        error_flag += ["Network transfer bytes validation: Fail"]

                self.log.info("CASE 5: Did Dedupe Occur correctly "
                              "? comparing the primary and secondary objects "
                              "in the Dedup store ")
                primary_objects_count = int(self.dedup_helper.get_primary_objects(job.job_id))
                self.log.info("Primary objects: %d", primary_objects_count)
                dict_prim[iterator] = primary_objects_count
                secondary_objects_count = int(self.dedup_helper.get_secondary_objects(job.job_id))
                self.log.info("Secondary objects: %d", secondary_objects_count)
                dict_sec[iterator] = secondary_objects_count

                # now if in second iteration then we check second
                # iter backup sec equals first iter backup primary
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

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.info(error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.resultant_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            # set the deduplication back to default
            self.log.info("setting client deduplication to default:"
                          " Use storage policy settings ")
            self.client.set_dedup_property("clientSideDeduplication",
                                           "USE_SPSETTINGS")
            self.log.info("setting client deduplication to default"
                          " Use storage policy settings: Done")

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
            # self.client_machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data")
            else:
                self.log.info("Content directory does not exist.")

            # run the previous_run_cleanup again to delete the backupset,
            # plan, storage pool after running the case
            self.previous_run_clean_up()

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)

