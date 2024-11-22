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

    init_tc()       -- Initial configuration for the test case using command center

    _get_mountpath_id() --  To get first mountpath id on specified library

    _get_sourceaccesspath() -- Get source and dest access path from most recent ddb move for provided ma

    _validate_partitions() -- Validate partitions moved as expected after DDB Move job

    _get_substoreids() -- Get substore ids by querying IdxSIDBstore table based on provided path

    clean_test_environment() --  To perform cleanup operation before setting the environment and
                                 after testcase completion

    setup()         --  setup function of this test case

    configure_tc_environment() -- Create storage pool, storage policy and associate to subclient

    run_backups() -- Run backups on subclients based on number of jobs required

    run_backup() -- Runs backup by generating new content to get unique blocks for dedupe backups

    perform_ddb_move() -- Method to perform DDB move operation in Command Center using selenium webdriver

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample Input:
    "64487": {
          "ClientName": "Name of Client Machine",
          "AgentName": "File System",
          "Source_MediaAgent": "Name of source MA machine",
          "Destination_MediaAgent": "Name of destination MA machine where DDB needs to move to",
          Optional arguments:
                "source_dedup_path": DDB path on source MA
                "target_dedup_path": DDB path on destination MA
                "mount_path": Library mount path on source MA
          "ConfigureTCEnv": true/false (default:true)
           Note: If ConfigureTCEnv is 'false' -> DDB move occurs based on only on source and dest MAs;
                 Source and dest paths are obtained from last ddb move operation on source MA where these
                 paths are reversed.

        }

Steps:
    1. Configure test case environment
        a. Create storage pool with multiple (randomly generated between 2 and 5) partitions
        b. Create storage policy
        c. Create backupset, subclient and content path
    2. Generate data in content path and run multiple backups
    3. Perform DDB move operation on source MA
        a. Configure Command Center environment and open browser
        b. Get source and destination DDB paths either by
            -> creating these resources when 'ConfigureTCEnv' json input is set to True
            -> Identifying paths from last DDB move operation on provided source MA
        c. Navigate to Infrastructure -> Media Agents -> source MA agent page in CC
        d. Go to 'Configuration' tab
        e. Search for source DDB path -> access action button -> click 'Move'
        f. Set dest MA and dest DDB path in Move DDB dialog -> Save -> DDB move job initiates
    4. Validate number of partitons before and after move match
    5. Validate the susbtores before DDB move and susbtores after move match
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from AutomationUtils.machine import Machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.MediaAgentHelper import MediaAgentHelper
from pathlib import Path
import random
import time


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Admin Console - DDB Move Case"
        self.browser = None
        self.admin_console = None
        self.mmhelper = None
        self.dedup_helper = None
        self.ma_helper = None
        self.client_machine = None
        self.content_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.tcinputs = {
            "Source_MediaAgent": None,
            "Destination_MediaAgent": None
        }
        self.subclient_obj_list = []
        self.backup_job_list = []
        self.utility = None
        self.source_ma_machine = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.ddb_path = None
        self.source_ma = None
        self.dest_ma = None
        self.source_ma_machine = None
        self.dest_ma_machine = None
        self.target_ddb_path = None
        self.ma_path = None
        self.dest_ma_path = None
        self.storage_pool = []
        self.storage_policy_list = []
        self.content_path_list = []
        self.mount_path = None
        self.is_configure_tc_env = True
        self.is_user_defined_target_dedup = False

    def _get_sourceaccesspath(self, source_ma):
        """
        Get source and dest access path from most recent ddb move for provided ma
            Args:
                source_ma (str)  --  source media agent

            Returns:
                Source and target paths for DDB move
        """
        query = f"""SELECT id
                    FROM App_Client
                    WHERE name like '{source_ma}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        clientid = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", clientid)
        query = f"""SELECT DDBSourcePath,DDBTargetPath from MMDataTransferStreamToFiles
                    WHERE transferstreamid in 
                    (SELECT top 1 TransferId
                    FROM MMDataTransferStreams
                    WHERE SourceMAClientId = '{int(clientid[0])}'
                    ORDER BY TransferId desc)"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        sourcepath = cur[1]
        targetpath = cur[0]
        ran = random.randint(1, 10)
        tpath = Path(targetpath)
        tpath_drive = tpath.drive
        destpath = tpath_drive + "\\DDB_move" + str(ran)
        if sourcepath != [''] and targetpath != ['']:
            return sourcepath, destpath
        self.log.error("No entries present")
        raise Exception("Invalid Accesspath.")

    def _validate_partitions(self,
                             before_move,
                             after_move,
                             num_part):
        """
        Validate partitions moved as expected after DDB Move job
            Args:
                before_move (list[str])  --  List of partitions before ddb move
                after_move (list[str])   --  List of partitions after ddb move
                num_part (int)           --  Number of partitions moved

            Returns:
         """
        self.log.info(f"Partitions before DDB move: {before_move}")
        self.log.info(f"Partitions after DDB move: {after_move}")
        if int(num_part) != len(before_move):
            self.log.error(f"Number of partitions do not match, From UI: {num_part}, From DB: {len(before_move)}")
            raise Exception("Number of partitions mismatch")
        for i in range(0, int(num_part)):
            if before_move[i][0] != after_move[i][0]:
                self.log.error(f"Partition id does not match, Before:{before_move[i][0]}, After: {after_move[i][0]}")
                raise Exception("Partition id mismatch")
        self.log.info("Partitions before and after move validated")

    def _get_substoreids(self, path):
        """
        Get substore ids by querying IdxSIDBstore table based on provided path
            Args:
                path (str) -- path to get associated substoreids

            Returns:
                substores (list) -- list of substores associated to provided path
        """
        query = f"""SELECT SubStoreId
                    FROM IdxSIDBSubStore where
                    IdxAccessPathid in (SELECT IdxAccessPathId
                                        FROM IdxAccessPath
                                        WHERE path like '{path}')
                    ORDER BY substoreid desc """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        substores = self.csdb.fetch_all_rows()
        self.log.info("RESULT-> substores: %s", substores)
        if substores != ['']:
            return substores
        self.log.error("No entries present")
        raise Exception("Invalid Accesspath.")

    def init_tc(self):
        """Initial configuration for the test case using command center"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.mmhelper = MMHelper(self)
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.source_ma = self.tcinputs['Source_MediaAgent']
        self.dest_ma = self.tcinputs['Destination_MediaAgent']
        self.source_ma_machine = Machine(self.source_ma, self.commcell)
        self.dest_ma_machine = Machine(self.dest_ma, self.commcell)
        # Inputs from User
        if 'ConfigureTCEnv' in self.tcinputs:
            self.is_configure_tc_env = self.tcinputs.get('ConfigureTCEnv')

        self.content_path = self.tcinputs.get("content_path")

        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('source_dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('target_dedup_path'):
            self.is_user_defined_target_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.source_ma_machine, size=20 * 1024)
            self.ma_path = self.source_ma_machine.join_path(ma_1_drive, 'test_' + str(self.id))

        if not self.is_user_defined_mp:
            self.mount_path = self.source_ma_machine.join_path(self.ma_path, "MP")
        else:
            self.mount_path = self.source_ma_machine.join_path(
                self.tcinputs['mount_path'], 'test_' + self.id, 'MP')

        if not self.is_user_defined_dedup and "unix" in self.source_ma_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_target_dedup and "unix" in self.dest_ma_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_dedup:
            self.log.info("custom source dedup path supplied")
            self.ddb_path = self.source_ma_machine.join_path(self.tcinputs["source_dedup_path"],
                                                             'test_' + self.id, "DDBs")
        else:
            self.ddb_path = self.source_ma_machine.join_path(self.ma_path + "_DDBs")

        self.log.info(f"Source DDB path : {self.ddb_path}")

        if self.is_user_defined_target_dedup:
            self.target_ddb_path = self.dest_ma_machine.join_path(self.tcinputs["target_dedup_path"],
                                                                  'test_' + self.id, "DDB" + '_'
                                                                  + str(random.randint(1, 5)))
        else:
            ma_2_drive = self.utility.get_drive(self.dest_ma_machine, size=20 * 1024)
            self.dest_ma_path = self.dest_ma_machine.join_path(ma_2_drive,
                                                               'test_' + str(self.id))
            # creating unique folders for case stability in case old paths are not cleanup up from DB on time
            self.target_ddb_path = self.dest_ma_machine.join_path(self.dest_ma_path, "DDB" + '_'
                                                                  + str(random.randint(1, 5)))

        self.log.info(f"Target DDB path : {self.target_ddb_path}")

        # names of various entities
        self.backupset_name = f"bkpset_tc_{self.id}"
        self.subclient_name = f"subc_tc_{self.id}"
        self.storage_policy_name = f"sp_tc_{self.id}"
        self.storage_pool_name = f"storage_pool_tc_{self.id}"
        self.dedup_helper = DedupeHelper(self)

    @test_step
    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:
            self.log.info("** STEP: Cleaning up test environment **")

            if self.content_path_list:
                if self.client_machine.check_directory_exists(self.content_path_list[-1]):
                    self.log.info("Deleting already existing content directory [%s]", self.content_path_list[-1])
                    self.client_machine.remove_directory(self.content_path_list[-1])

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy: %s", self.storage_policy_name)
                sp_obj = self.commcell.storage_policies.get(self.storage_policy_name)
                sp_obj.reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info("deleting storage pool: %s", self.storage_pool_name)
                self.commcell.storage_pools.delete(self.storage_pool_name)

            self.commcell.refresh()

            self.log.info("cleanup completed")

        except Exception as excp:
            self.log.warning(f"***Failure in Cleanup with error {excp}***")

    @test_step
    def configure_tc_environment(self):
        """Create storage pool, storage policy and associate to subclient"""
        if self.is_configure_tc_env:
            self.log.info("** STEP: Configuring Testcase environment **")
            self.storage_pool, self.storage_policy_list, self.content_path_list, self.subclient_obj_list \
                = self.dedup_helper.configure_mm_tc_environment(
                  self.source_ma_machine,
                  self.source_ma,
                  self.mount_path,
                  self.ddb_path,
                  random.randint(2, 5))
        else:
            self.log.info("Using existing DDB path on source MA for DDB move operation")

    @test_step
    def run_backups(self, num_jobs):
        """
        Run backups on subclients based on number of jobs required
        param:
            num_jobs (int)  : number of backup jobs to run
        """
        if self.is_configure_tc_env:
            for _ in range(1, num_jobs + 1):
                self.run_backup()
        else:
            self.log.info("Not running backups as existing DDB path on source MA is used for DDB move operation")

    def run_backup(self, backup_type="FULL", size=1.0):
        """
        This function runs backup by generating new content to get unique blocks for dedupe backups
        Args:
            backup_type (str): type of backup to run
            size (float): size of backup content to generate

        Returns:
            job (object) -- returns job object to backup job
        """
        # add content
        self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"],
                                                 self.content_path_list[-1], size)
        self._log.info("Running %s backup...", backup_type)
        job = self.subclient_obj_list[-1].backup(backup_type)
        self._log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self._log.info("Backup job completed.")
        return job

    @test_step
    def perform_ddb_move_and_validate(self):
        """
        Method to perform DDB move operation in Command Center using selenium webdriver
        """
        self.init_tc()
        self.ma_helper = MediaAgentHelper(self.admin_console)
        # if no DDB path is provided by user, then identify paths based on last DDB move on source MA
        if not self.is_configure_tc_env:
            sourcepath, destpath = self._get_sourceaccesspath(self.source_ma)
        else:
            sourcepath = self.ddb_path
            destpath = self.target_ddb_path
        before_move = self._get_substoreids(sourcepath)
        num_of_partitions = self.ma_helper.get_num_partitions_for_path(self.source_ma, sourcepath)
        self.ma_helper.move_ddb_path(self.source_ma, self.dest_ma,
                                     sourcepath, destpath)
        # wait for move job to complete
        self.log.info("Waiting 200s for Move DDB job to complete")
        time.sleep(200)
        after_move = self._get_substoreids(destpath)
        self.log.info(f'Number Of Partitions={num_of_partitions[0]}')
        self._validate_partitions(before_move, after_move, num_of_partitions[0])

    def run(self):
        """
        Main function for test case execution
        """
        try:
            self.clean_test_environment()
            self.configure_tc_environment()
            self.run_backups(random.randint(2, 5))
            self.perform_ddb_move_and_validate()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear Down Function of this Case"""
        try:
            self.clean_test_environment()

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")
