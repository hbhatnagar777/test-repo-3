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

    previous_run_cleanup() -- for deleting the left over backupset and storage policy from the previous run

    create_common_items() -- creates items which are to be left behind,
                            there are common resources which
                            can be used by other ddb backup testcases too
                            they will act as default placeholders for ddb subclient

    create_resources()      -- creates the required resources/ defines
                                paths for this testcase

    create_content_sc() --  This function creates separate content for a specific subclient.
                                            It will associate the content to the subclient.

    ddb_subclient_load() -- load the DDB subclient for running DDB backups

    verifications() -- This function will ensure that the behaviour is as expected.

    job_completion_wait() -- make sure that the job is completed.

    sidb_is_up() -- check if sidb2 process is up for the DDB.

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase verifies DDB backup windows + ransomware protection + clbackup write error case.

input json file arguments required:

    "62715": {
        "ClientName": "",
        "AgentName": "File System",
        "MediaAgentName": ""
        "dr_path_regkey": "related to DR path",
        "ddb_path_regkey": "related to DDB path"
    }

    "library_name": name of the Library to be reused
    "dedup_path": path where dedup store to be created
    "num_subclients_TC": number of subclients you want to have in TC
                        default = 1

    note --
        ***********************************
        if library_name_given then reuse_library
        else it will auto_generate_library_path

        if dedup_path_given -> use_given_dedup_path
        else it will auto_generate_dedup_path
        ***********************************
"""
# Design Steps:
# clean up previous run config, Create resources.
# load ddb subclient
# make sure ransomware protection enabled on MA
# create test case resources
# 	    create a common storage policy for DDB backup which can be left behind.
# 	    create lib, storage policy, backupset and subclient.
# run a dedupe backup (content size = 1GB) to add some entries in DDB. Wait for it to complete.
# run dedupe backups(content size = 1.5GB) on all the subclients, Default value is 1.
# check if sidb2 process is running on MA.
#     when sidb2 process is running, start a DDB backup job.
#
# run the verifications
#         validate if the DDB Backup job quiesced the ddb store for the dedupe backup job,
#             regex="Suspended the DDB, Quiesce Token"
#         check if quiescing happened for ddb in clbackup, f"Quiescing Engine [{str(self.sidb_id)}]"
#         check if write protect errors for state.xml file seen in clbackup
#         check if unquiescing call sent, find_string = "UnQuiescing SIDB engines"
#         check if lastsnapjobid is the same as previously run DDB backup job id
#         Try to create new folder inside dedup path
#
# run a regular recon to see if DDB backup done previously is usable
# 	    run a dedupe backup job.
# 	    when sidb2 process is up, kill it and start a regular recon job.
# 	    wait for the recon job to successfully complete.


import time
from AutomationUtils import constants, machine
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
        self.name = "DDB backup windows with ransomware protection enabled to check clbackup write error."

        self.tcinputs = {
            "MediaAgentName": None,
            "dr_path_regkey": None,
            "ddb_path_regkey": None
        }

        self.dedup_store_path = None
        self.mount_path = None
        self.content_path = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None

        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None

        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None

        self.client_machine = None
        self.media_agent_machine = None

        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.ddbbackup_subclient = None

        self.is_user_defined_lib = False
        self.is_user_defined_mount_path = False
        self.is_user_defined_dedup = False

        self.sidb_id = None
        self.substore_id = None
        self.num_subclients = None
        self.ddb_backup_job = None
        self.ma_name = None
        
    def setup(self):
        """sets up the variables to be used in testcase"""
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True

        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mount_path = True

        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs["MediaAgentName"]
        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.tcinputs["ClientName"])
        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = "{0}_lib{1}".format(str(self.id), suffix)
        self.storage_policy_name = "{0}_SP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)
        self.num_subclients = int(self.tcinputs.get("num_subclients_TC", "1"))

    def previous_run_clean_up(self):
        """
        delete previous run items

        Args:
            None

        Returns:
            None
        """

        self.log.info("********* previous run clean up **********")
        try:
            self.log.info("deleting backupset and SP of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            # in case the storage policy of this testcase gets associated to the DDB subclient
            # will cause error in clean up
            # create a new common policy - leave it behind - delete the
            # testcase storage policy

            # do this only if testcase storage policy is associated to the DDB
            # subclient
            self.ddb_subclient_load()
            if self.ddbbackup_subclient.storage_policy == self.storage_policy_name:
                self.log.info("testcase storage policy is associated to the DDB subclient:"
                              " trying to dis-associate it")
                self.create_common_items()

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("storage policy deleted")
            else:
                self.log.info("storage policy does not exist.")

            if not self.is_user_defined_lib:
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info("Library deleted")
                else:
                    self.log.info("Library does not exist.")

            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.info("clean up ERROR: %s", exp)

    def create_common_items(self):
        """
            creates items which are to be left behind, there are common resources which
            can be used by other ddb backup testcases too
            they will act as default placeholders for ddb subclient

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if error in re-associating storage policy of ddb subclient.
        """
        mount_path = self.media_agent_machine.join_path(self.tcinputs.get(
            "mount_path"), f"ddb_cases_common_files_{self.ma_name}", f"mount_path_common_lib_{self.ma_name}")
        dedup_store_path = self.media_agent_machine.join_path(self.tcinputs.get(
            "dedup_path"), f"ddb_cases_common_files_{self.ma_name}", f"dedup_path_common_sp_{self.ma_name}")

        # create common library
        self.mm_helper.configure_disk_library(
            f"common_lib_ddb_cases_{self.ma_name}", self.tcinputs.get("MediaAgentName"), mount_path)

        # create SP
        self.dedup_helper.configure_dedupe_storage_policy(
            f"common_sp_ddb_cases_{self.ma_name}", f"common_lib_ddb_cases_{self.ma_name}",
            self.tcinputs.get("MediaAgentName"), dedup_store_path)

        self.ddbbackup_subclient.storage_policy = f"common_sp_ddb_cases_{self.ma_name}"
        cleanup_backup_job = self.ddbbackup_subclient.backup("FULL")
        self.log.info("DDB Backup job: %s", str(cleanup_backup_job.job_id))
        if not cleanup_backup_job.wait_for_completion():
            raise Exception("Job {0} Failed with JPR: {1}".format(cleanup_backup_job.job_id,
                                                                  cleanup_backup_job.delay_reason))
        self.log.info("DDB Backup job %s complete", cleanup_backup_job.job_id)

    def create_resources(self):
        """
        creates the required resources/ defines paths for this testcase

        Args:
            None

        Returns:
            None

        """
        # create the required resources for the testcase
        # get the drive path with required free space
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, f'test_{self.id}')

        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        self.testcase_path_media_agent = self.media_agent_machine.join_path(drive_path_media_agent, f'test_{self.id}')

        # creating testcase directory, mount path, content path, dedup
        # store path
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if self.is_user_defined_mount_path:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
        else:
            # automatically create the mount path
            # this may be needed in case of clearing storage policy associated
            # with DDB backup subclient.
            self.mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        elif "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("This case is for Windows MA!..")
            raise Exception("This case is for Windows MA!..")
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                                       "dedup_store_path")

        # if user defined library exists don't create new else create new
        # library
        if self.commcell.disk_libraries.has_library(self.tcinputs.get("library_name", "library does not exist")):
            self.log.info("user defined library already exists - %s", self.tcinputs.get("library_name"))
            self.library = self.commcell.disk_libraries.get(self.tcinputs.get("library_name"))
        else:
            # create library
            self.library = self.mm_helper.configure_disk_library(
                library_name=self.library_name,
                ma_name=self.tcinputs["MediaAgentName"],
                mount_path=self.mount_path)

        # create storage policy
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            storage_policy_name=self.storage_policy_name,
            library_name=self.library_name, ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.dedup_store_path, ddb_ma_name=self.tcinputs.get("MediaAgentName"))

        # get the store and sub store ids of the DDB
        return_list = self.dedup_helper.get_sidb_ids(self.storage_policy.storage_policy_id, "primary")
        self.sidb_id = int(return_list[0])
        self.substore_id = int(return_list[1])

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)

        # create subclient list
        self.subclient = []
        for item in range(self.num_subclients):
            subc = self.mm_helper.configure_subclient(
                backupset_name=self.backupset_name,
                subclient_name=self.subclient_name + "_" + str(item),
                storage_policy_name=self.storage_policy_name)
            self.subclient.append(subc)

    def create_content_sc(self, size, subclient):
        """
        This function creates separate content for a specific subclient.
        It will associate the content to the subclient.
        Args:
            size - data needed in GB (float)
            subclient - subclient object

        Returns:
            None
        """

        if self.mm_helper.create_uncompressable_data(
                self.client.client_name, self.client_machine.join_path(self.content_path, subclient.name), size, 1):
            self.log.info("generated unique data for subclient: %s at location: %s",
                          subclient.name, self.client_machine.join_path(self.content_path, subclient.name))
        else:
            raise Exception("couldn't generate unique data")

        # add subclient content
        self.log.info("add all the generated files as content to the subclient: %s", subclient.name)
        subclient.content = [self.client_machine.join_path(self.content_path, subclient.name)]

    def ddb_subclient_load(self):
        """
        sets the ddb subclient variable from MA of our testcase

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if DDBBackup subclient does not exist.

        """
        # check if DDBBackup subclient exists, if it doesn't fail the testcase
        default_backup_set = self.commcell.clients.get(
            self.tcinputs.get("MediaAgentName")).agents.get("File System").backupsets.get("defaultBackupSet")

        if default_backup_set.subclients.has_subclient("DDBBackup"):
            self.log.info("DDBBackup subclient exists")
            self.ddbbackup_subclient = default_backup_set.subclients.get("DDBBackup")
            self.log.info(
                "Storage policy associated with the DDBBackup subclient is %s", self.ddbbackup_subclient.storage_policy)
        else:
            raise Exception("DDBBackup Subclient does not exist:FAILED")

    def verifications(self, jobs):
        """
        This function will ensure that the behaviour is as expected.
        checks-
            check if quiescing happened for ddb
            check if write protect errors for state.xml file seen - we should not see them
            check if unquiescing call sent

        Args:
            jobs - list of job objects

        Returns:
            error_flag - list of failures we see for the TC.

        Raises:
            Exceptions
                if no running SIDB2 process found for DDB
        """

        error_flag = []
        # check if sidb was interrupted in between
        # sidb engine log verification (MA)
        # log lines example
        # 15808 4324  03/03 16:01:17 ### 533-0-559-0 Quiesce          1648  Going to suspend DDB. Session [1]
        # 15808 4324  03/03 16:01:17 ### 533-0-559-0 Quiesce          1667  Suspended the DDB, Quiesce Token [1]

        self.log.info(
            "validate if the DDB Backup job quiesced the ddb store for the dedupe backup job")
        self.log.info("******************************************")
        found = False
        quiesced_ddb_store = []
        (matched_lines, matched_string) = self.dedup_helper.parse_log(
            self.tcinputs.get("MediaAgentName"),
            "SIDBEngine.log",
            regex="Suspended the DDB, Quiesce Token",
            escape_regex=True, single_file=False)

        common = str(self.sidb_id) + "-0-"
        for matched_line in matched_lines:
            if common in matched_line:
                found = True
                quiesced_ddb_store.append(matched_line)
        if found:
            self.log.info(
                "Result: Pass Quiescing took place for the DDB store of this testcase")
            self.log.info("line found sample: {%s}", quiesced_ddb_store[0])
        else:
            self.log.info("Result: Fail")
            self.log.error("while quiescing the DDB, engine was not suspended")
        self.log.info("******************************************")

        #   cl backup log verification of the MA
        #   43520 aca4  03/09 16:00:50 230732 QuiesceEngines: Quiescing Engine [532], Group [1],
        #   SubStore [558], Splits [2]
        #   43520 aca4  03/09 16:00:50 230732 QuiesceEngines: Engine [532], Group [1],
        #   Quiesce Success [true], Locked [true] iRet [0]

        self.log.info("******************************************")
        self.log.info("check if quiescing happened for ddb in clbackup")
        find_string = f"Quiescing Engine [{str(self.sidb_id)}]"
        (matched_lines, matched_string) = self.dedup_helper.parse_log(
            self.tcinputs.get("MediaAgentName"),
            "clBackup.log",
            regex=find_string,
            escape_regex=True, single_file=False, jobid=self.ddb_backup_job.job_id)

        if matched_lines:
            self.log.info("Result :Pass")
            self.log.info(matched_string)
        else:
            self.log.error("Result: Failed")
            error_flag += [f"failed to find: {find_string} in clbackup"]
        self.log.info("******************************************")

        #     cl backup log verification (MA)
        #     8816  1cd0  02/21 16:00:55 213227 QuiesceEngines: Engine [433], Group [0], SubStore [458],
        #     unable to open state file [C:\automation\some_path_name\MA\Storepath16\CV_SIDB\2\433\Split00]. iRet [-1]

        # 8816  1cd0  02/21 16:00:55 213227 Cannot open file
        # [C:\automation\some_path_name\MA\Storepath17\CV_SIDB\2\434\Split00\State.xml],
        # error=0xECCC000D:{CQiFile::Open(95)} + {CQiUTFOSAPI::open(77)/ErrNo.13.(Permission denied)-Open failed,
        # File=\\?\C:\automation\some_path_name\MA\Storepath17\CV_SIDB\2\434\Split00\State.xml,
        # OperationFlag=0xC002, PermissionMode=0x0}

        self.log.info("******************************************")
        self.log.info(
            "check if write protect errors for state.xml file seen in clbackup")
        find_string = "Permission denied"
        found = False

        (matched_lines, matched_string) = self.dedup_helper.parse_log(
            self.tcinputs.get("MediaAgentName"),
            "clBackup.log",
            regex=find_string,
            escape_regex=True, single_file=False, jobid=self.ddb_backup_job.job_id)

        if matched_lines:
            for matched_line in matched_lines:
                self.log.error(matched_line)
                if "State.xml" in matched_line:
                    found = True

        if found:
            self.log.error("Result: Failed")
            error_flag += ["state.xml is not accessible - permission denied"]
        elif matched_lines:
            error_flag += ["permission denied errors seen in clbackup log"]
        else:
            self.log.info("Result: Pass")
        self.log.info("******************************************")

        #   clbackup log on MA
        #   26096 3e00  02/28 16:02:19 220964 DDBBackupManager::UnquiesceAllSIDBStores(319) - UnQuiescing SIDB engines
        #   (fyi - Unquiesce call result we don't know - not logged)
        self.log.info("******************************************")
        self.log.info("check if unquiescing call sent")
        find_string = "UnQuiescing SIDB engines"

        (matched_lines, matched_string) = self.dedup_helper.parse_log(
            self.tcinputs.get("MediaAgentName"),
            "clBackup.log",
            regex=find_string,
            escape_regex=True, single_file=False, jobid=self.ddb_backup_job.job_id)

        if matched_lines:
            self.log.info("Result :Pass")
            self.log.info(matched_string)
        else:
            self.log.error("Result: Failed")
            self.log.error(f"we did not find: {find_string} in clbackup - unquiesce did not happen")
        self.log.info("******************************************")

        # wait for jobs to finish in case they are still running
        for job in jobs:
            self.job_completion_wait(job)

        self.log.info("******************************************")
        self.log.info("check if lastsnapjobid is the same as previously run DDB backup job id")
        query = "select LastSnapJobId from IdxSIDBSubStore where SIDBStoreId = {0}".format(self.sidb_id)
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        job_id = self.csdb.fetch_one_row()[0]
        self.log.info("Store{0}: LastSnapJobId {1}".format(self.sidb_id, job_id))
        if str(job_id) == str(self.ddb_backup_job.job_id):
            self.log.info("Result: Pass")
            self.log.info("last job is same as ddb backup job run in the TC")
        else:
            self.log.error("Result: Failed")
            error_flag += ["LastSnapJobID not updated in IdxSIDBSubstore table"]
        self.log.info("******************************************")

        self.log.info("sleep for 2 mins")
        time.sleep(120)

        self.log.info("******************************************")
        self.log.info("Try to create new folder inside dedup path")
        # remove the restart service part in actual TC - only for testing
        self.log.info("Restart the cvmountd service on MA and sleep for 20 seconds")
        ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        ma_client.restart_service("GXMMM(" + ma_client.instance + ")")
        time.sleep(20)

        # keep the wait time in actual TC
        # self.log.info("sleep for 35 mins")
        # time.sleep(35*60)
        try:
            # try to create a new folder there
            # when ransomware protection working properly, new folder should
            # not be created
            engine = self.commcell.deduplication_engines.get(self.storage_policy_name, 'Primary')
            store = engine.get(engine.all_stores[0][0])
            sub_store_path= store.all_substores[0][1]
            temp_direc = self.media_agent_machine.join_path(
                sub_store_path,
                f"z_{self.id}_test_direc_{str(time.time()).replace('.', '-')}")
            self.media_agent_machine.modify_ace('Everyone', temp_direc, 'Delete', 'Deny', remove=True, folder=True)
            self.log.info("Deny delete permission removed from %s", temp_direc)
            self.log.info("create new directory %s in dedup path", temp_direc)
            self.media_agent_machine.create_directory(temp_direc, force_create=True)

            # validate if creation of directory was successful
            if self.media_agent_machine.check_directory_exists(temp_direc):
                self.log.error("creation of directory was successful - this should not have occurred")
                error_flag += ["creation of directory in Dedup path was successful"]

        except Exception as exp:
            # creation should not be possible
            if "New-Item : The media is write protected" in str(exp):
                self.log.info("working as expected - creation of new directory %s inside dedup path location failed",
                              temp_direc)
        self.log.info("******************************************")

        return error_flag

    def job_completion_wait(self, job):
        """
            A wrapper to wait for job completion.
            Args:
                job - job object
            Returns:
                None
            Raises:
                raise exception if the job does not complete
        """
        if not job.wait_for_completion():
            raise Exception("Job {0} Failed with JPR: {1}".format(job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)

    def sidb_is_up(self):
        """
            Check if sidb2 process is up for the ddb
            Args:
                None
            Returns:
                list of running sidb processes
            Raises:
                raise exception if the sidb process is not running
        """

        count = 0
        running_sidb_list = []
        while not running_sidb_list:
            running_sidb_list = self.dedup_helper.is_sidb_running(
                engine_id=str(self.sidb_id),
                ddbma_object=self.commcell.clients.get(self.tcinputs.get("MediaAgentName")))
            time.sleep(1)
            count += 1

            if count == 240:
                self.log.error("did not find running SIDB2 process for DDB %d",
                               self.sidb_id)
                raise Exception("could not start sidb process"
                                " during backup job under 240 secs")
        return running_sidb_list

    def run(self):
        """Run function of this test case"""
        try:
            # clean up previous run config, Create resources.
            self.previous_run_clean_up()
            self.create_resources()

            # load ddb subclient
            self.ddb_subclient_load()

            # We are enabling ransomware protection if it is not enabled on the setup.
            protection_enabled = self.mm_helper.ransomware_protection_status(
                self.commcell.clients.get(self.tcinputs.get("MediaAgentName")).client_id)
            driver_loaded = self.mm_helper.ransomware_driver_loaded(
                self.commcell.clients.get(self.tcinputs.get("MediaAgentName")))

            if not (protection_enabled and driver_loaded):
                self.log.info("Enable ransomware protection on the MA")
                self.commcell.media_agents.get(self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
                time.sleep(10)
                self.log.info("Restart the cvmountd service on MA and sleep for 20 seconds")
                ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
                ma_client.restart_service("GXMMM(" + ma_client.instance + ")")
                time.sleep(20)
            else:
                self.log.info("Ransomware protection is working")

            self.log.info("checking for dr path regkey")
            if self.media_agent_machine.check_registry_exists(
                    'DLP', self.tcinputs.get('dr_path_regkey')):
                self.media_agent_machine.remove_registry(
                    'DLP', self.tcinputs.get('dr_path_regkey'))
                self.log.info("removed regkey from DLP!")

            self.log.info("checking for SIDBIdleTimeOut regkey")
            if self.media_agent_machine.check_registry_exists(
                    'MediaAgent', 'SIDBIdleTimeOut'):
                self.media_agent_machine.remove_registry(
                    'MediaAgent', 'SIDBIdleTimeOut')
                self.log.info("removed regkey SIDBIdleTimeOut from MediaAgent")

            self.log.info("checking for ddb path regkey")
            if self.media_agent_machine.check_registry_exists(
                    'DLP', self.tcinputs.get('ddb_path_regkey')):
                self.media_agent_machine.remove_registry(
                    'DLP', self.tcinputs.get('ddb_path_regkey'))
                self.log.info("removed regkey %s from DLP!", self.tcinputs.get('ddb_path_regkey'))

            self.media_agent_machine.create_registry(key='DLP', value=self.tcinputs.get('ddb_path_regkey'),
                                                     data="1e", reg_type='DWord')
            self.log.info("set the reg key %s to 30", self.tcinputs.get('ddb_path_regkey'))
            # 30 in hex is 1e

            # set SIDBIdleTimeOut to 304 seconds == 130 hex
            self.media_agent_machine.create_registry(key='MediaAgent', value='SIDBIdleTimeOut',
                                                     data='130', reg_type='DWord')
            self.log.info("set the reg key SIDBIdleTimeOut to 304 seconds")

            filler_sc = self.mm_helper.configure_subclient(
                backupset_name=self.backupset_name,
                subclient_name=f"{self.subclient_name}_filler_sc",
                storage_policy_name=self.storage_policy_name)
            self.create_content_sc(subclient=filler_sc, size=1.0)

            job = filler_sc.backup("FULL")
            self.log.info("Backup job id: %s", str(job.job_id))
            self.job_completion_wait(job)
            self.log.info("Job completed")

            jobs = []
            for subclient in self.subclient:
                self.log.info("set the data readers for subclient %s to 1", subclient.name)
                subclient.data_readers = 1
                self.create_content_sc(size=1.5, subclient=subclient)
                self.log.info("start dedupe jobs on subclients")
                job = subclient.backup("FULL")
                self.log.info("Backup job id: %s", str(job.job_id))
                jobs.append(job)

            if self.sidb_is_up():
                self.log.info("Start DDB backup job")
                self.ddb_backup_job = self.ddbbackup_subclient.backup("FULL")
                self.log.info("DDB backup job %s started", self.ddb_backup_job.job_id)
                # jobs.append(self.ddb_backup_job)
                self.job_completion_wait(self.ddb_backup_job)

            # (basically we want to coordinate ddb backup quiescing phase
            # with active sidb state of dedupe backup jobs [backup phase])
            #   so we should see overlap of time when sidb process is up and
            #   quiescing is taking place

            error_flag = self.verifications(jobs)

            if error_flag:
                # if the list is not empty then error was there, fail the
                # testcase
                self.log.info(error_flag)
                raise Exception(f"testcase failed: {error_flag}")

            # run a regular recon to see if DDB backup done previously is usable
            get_sidb_up_job = filler_sc.backup("FULL")
            self.log.info("Backup job id: %s", str(get_sidb_up_job.job_id))
            running_sidb_list = self.sidb_is_up()

            pid = []
            for pid_tuple in running_sidb_list:
                pid.append(pid_tuple[1])
                self.log.info("got the (groupnumber,pid,jobid) tuple: %s", pid_tuple)

            self.log.info("verified from OS PID list sidb"
                          " process is up for current DDB")

            # then kill the sidb process
            for process_id in pid:
                self.log.info("killing the sidb process for %d engine with pid %d",
                              self.sidb_id, process_id)
                self.media_agent_machine.kill_process(process_id=process_id)

            # resume the job, pass over exception
            try:
                time.sleep(30)
                self.log.info("resuming the backup job after killing sidb process")
                get_sidb_up_job.resume()
            except Exception:
                pass

            time.sleep(90)

            self.log.info("******************************************")
            self.log.info("run regular recon over the DDB")
            self.storage_policy.run_recon(
                copy_name="primary",
                sp_name=self.storage_policy_name,
                store_id=self.sidb_id,
                full_reconstruction=0)

            recon_job = self.dedup_helper.poll_ddb_reconstruction(
                sp_name=self.storage_policy_name, copy_name="primary")
            self.log.info("recon job was run: recon jobID - %s", recon_job.job_id)
            self.job_completion_wait(recon_job)

            # check if the job is a regular recon type job or not
            self.log.info(">>>>>Validation 1: is Regular recon job?")
            recon_type = self.dedup_helper.get_reconstruction_type(recon_job.job_id)
            if recon_type == "Regular Reconstruction":
                self.log.info("Result: Pass")            
                self.log.info("Recon job was a regular reconstruction job")
            else:
                self.log.error("Result: Failed")
                self.log.error("Recon job was not a regular reconstruction job")
                self.result_string = "Recon job was not a regular reconstruction job"

            self.log.info(
                ">>>>>Validation 2: check if LastSnapJobId is still the same as previously run DDB backup job id")
            self.log.info(
                "This will confirm that recon was indeed a regular recon and not a Full Recon because in case of Full Recon - LastSnapJobId is set to 0")
            query = "select LastSnapJobId from IdxSIDBSubStore where SIDBStoreId = {0}".format(self.sidb_id)
            self.log.info("Executing Query: %s", query)
            self.csdb.execute(query)
            job_id = self.csdb.fetch_one_row()[0]
            self.log.info("Store{0}: LastSnapJobId{1}".format(self.sidb_id, job_id))
            if str(job_id) == str(self.ddb_backup_job.job_id):
                self.log.info("Result: Pass")
                self.log.info("last job is same as ddb backup job run in the TC")
            else:
                self.log.error("Result: Failed")
                self.log.error("LastSnapjobId changed after recon job was run.")
                self.result_string += " LastSnapjobId changed after recon job was run."
            self.log.info("******************************************")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string += " "+str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all items created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            if self.media_agent_machine.check_registry_exists(
                    'MediaAgent', 'SIDBIdleTimeOut'):
                self.media_agent_machine.remove_registry(
                    'MediaAgent', 'SIDBIdleTimeOut')
                self.log.info("removed regkey SIDBIdleTimeOut from MediaAgent")

            if self.media_agent_machine.check_registry_exists(
                    'DLP', self.tcinputs.get('ddb_path_regkey')):
                self.media_agent_machine.remove_registry(
                    'DLP', self.tcinputs.get('ddb_path_regkey'))
                self.log.info("removed regkey %s from DLP!", self.tcinputs.get('ddb_path_regkey'))

            self.log.info("performing cleanup..")

            # delete the generated content for this testcase
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            self.previous_run_clean_up()

            if not self.is_user_defined_lib:
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info("Library deleted")
                else:
                    self.log.info("Library does not exist.")
            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR:%s", exp)
