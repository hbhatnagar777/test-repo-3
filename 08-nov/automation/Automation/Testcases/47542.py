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

    new_content()       -- generates data of specified size in given directory

    deallocate_resources()      -- deallocates all the resources created for testcase environment

    allocate_resources()        -- allocates all the necessary resources for testcase environment

    previous_run_cleanup()      -- for deleting the left over backupset and storage policy from the previous run

    run_backup_job()        -- for running a backup job of given type

    is_dedupe_enabled()     -- checks if the storage policy has dedupe enabled

    verify_logs()       -- checks whether backward referncing is enabled from the SIDBEngine log

    verify_arch_file_sidb_keys()  --  archFileSIDBKeys records for archFileId(s) in sealed store are copied to new store

    set_store_priming()     -- sets store priming property to enabled/disabled for a given copy

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase checks whether DDB Priming occurs or not.

Prerequisites: None

Input JSON:

"47542": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "gdsp_name": "<name of gdsp to be reused>" (optional argument),
        "library_name": "<name of the Library to be reused>" (optional argument),
        "mount_path": "<path where the data is to be stored>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. initialize resources
2. enable store priming on sp copy
3. run a full backup
4. case 1: store priming before sealing
    i. check if backward referencing is enabled from logs
    ii. check if backward reference store is zero from logs
        if zero priming did not occur continue
        else stop testcase execution
5. seal the active store
6. run a second full backup
7. case 2: store priming after sealing
    i. check if backward referencing is enabled from logs
    ii. check if backward reference store is zero from logs
        if zero priming did not occur stop testcase execution
        else if backward reference store id = sealed store id
            priming did occur
            testcase execution successful
8. deallocate all resources
"""
import time

from AutomationUtils import constants, commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils.machine import Machine


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
        self.name = "Store Priming Case"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.gdsp_name = None
        self.storage_pool_name = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.gdsp_copy_id = None
        self.sidb_id = None
        self.substore_id = None
        self.sealed_store_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.sql_password = None
        self.media_agent = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_pool = None
        self.library = None
        self.gdsp = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.gdsp_copy = None
        self.primary_copy = None
        self.is_user_defined_storpool = False
        self.is_user_defined_gdsp = False
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("gdsp_name"):
            self.is_user_defined_gdsp = True
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent)[:] + "_" + str(self.client.client_name)[:]

        self.storage_policy_name = "{0}_SP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_machine = Machine(self.media_agent, self.commcell)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        drive_path_client = self.opt_selector.get_drive(
            self.client_machine)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")

        if self.is_user_defined_gdsp:
            self.gdsp_name = self.tcinputs["gdsp_name"]
            self.gdsp = self.commcell.storage_policies.get(self.gdsp_name)
        elif self.is_user_defined_storpool:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.gdsp_name = self.storage_pool.global_policy_name
            self.gdsp = self.commcell.storage_policies.get(self.gdsp_name)

        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent = self.opt_selector.get_drive(
            self.media_agent_machine)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

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

        # sql connections
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)

    def new_content(self, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        """
        if self.client_machine.check_directory_exists(dir_path):
            self.client_machine.remove_directory(dir_path)
        self.client_machine.create_directory(dir_path)
        self.opt_selector.create_uncompressable_data(client=self.client_machine,
                                                     size=dir_size,
                                                     path=dir_path)

    def deallocate_resources(self):
        """removes all resources allocated by the Testcase"""
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

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

        if not self.is_user_defined_gdsp:
            if self.commcell.storage_policies.has_policy(self.gdsp_name):
                self.commcell.storage_policies.delete(self.gdsp_name)
                self.log.info("GDSP deleted")
            else:
                self.log.info("GDSP does not exist.")

        if not self.is_user_defined_gdsp and not self.is_user_defined_storpool:
            # here the storage pool is automatically created by gdsp and therefore has the same name as gdsp.
            if self.commcell.storage_pools.has_storage_pool(self.gdsp_name):
                self.commcell.storage_pools.delete(self.gdsp_name)
                self.log.info("Storage pool deleted")
            else:
                self.log.info("Storage pool does not exist.")

        if not self.is_user_defined_mp:
            if self.media_agent_machine.check_directory_exists(self.mount_path):
                self.media_agent_machine.remove_directory(self.mount_path)
                self.log.info("mount path deleted")
            else:
                self.log.info("mount path does not exist.")

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
        # create library if not provided
        if not (self.is_user_defined_lib or self.is_user_defined_storpool or self.is_user_defined_gdsp):
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.media_agent, self.mount_path)

        # create gdsp if not provided
        if not self.is_user_defined_gdsp and not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent,
                ddb_path=self.dedup_store_path,
                ddb_media_agent=self.media_agent)

            # adding second partition to the ddb store
            self.gdsp_copy = self.gdsp.get_copy(copy_name="Primary_Global")
            self.gdsp_copy_id = self.gdsp_copy.storage_policy_id
            new_ddb_path = self.media_agent_machine.join_path(self.dedup_store_path, "partition2")
            self.sidb_id = \
                self.dedup_helper.get_sidb_ids(copy_name="Primary_Global", sp_id=self.gdsp.storage_policy_id)[0]
            self.gdsp.add_ddb_partition(copy_id=self.gdsp_copy_id,
                                        sidb_store_id=self.sidb_id,
                                        sidb_new_path=new_ddb_path,
                                        media_agent=self.media_agent)

        # create dependent storage policy
        self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.library_name,
                                                                 media_agent=self.media_agent,
                                                                 global_policy_name=self.gdsp_name,
                                                                 dedup_media_agent=self.media_agent,
                                                                 dedup_path=self.dedup_store_path)

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

        # Enable encryption at Storage Pool level
        self.mm_helper.set_encryption(self.gdsp_copy)

        # add data to subclient content
        self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=1.0)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        if job_type == "incremental":
            # add new data to subclient content path and run incremental backup
            self.mm_helper.run_backup(self.client_machine,
                                      self.subclient,
                                      self.client_machine.join_path(self.content_path, time.strftime("%H%M")),
                                      backup_type=job_type)
            return

        self.log.info("starting %s backup job...", job_type)
        job = self.subclient.backup(backup_level=job_type)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

    def is_dedupe_enabled(self, copy):
        """
        checks whether deduplication is enabled on the give storage policy copy

            Args:
                copy        (instance)       policy copy object

        returns Boolean
        """
        copy._get_copy_properties()
        dedupe_flags = copy._copy_properties.get('dedupeFlags').get('enableDeduplication')
        if dedupe_flags != 0:
            return True
        return False

    def verify_logs(self, sidb_id, substore_id, sealed_store_id=0):
        """checks whether backward referencing occurred

                Args:
                    sidb_id             (str/int)       store id
                    substore_id         (str/int)       substore id
                    sealed_store_id     (str/int)       sealed store id

                Raises Exception:
                    if log lines not found
                    if backward reference store id is 0 in logs

        Returns None"""
        if sealed_store_id == 0:
            self.log.info("store priming won't occur... no backward referencing will be done..")
        else:
            self.log.info("store priming will occur... backward referencing on sealed store..")

        reg_exp = rf"{sidb_id}-\d*-{substore_id}-\d*-(\d*|#) .* Enabled Backward referencing \[Yes\]"
        self.log.info("searching SIDBEngine.log using following regular expression : %s", reg_exp)
        matched_line, matched_string = self.dedup_helper.parse_log(client=self.media_agent,
                                                                   log_file="SIDBEngine.log",
                                                                   regex=reg_exp,
                                                                   escape_regex=False,
                                                                   single_file=False)
        if not matched_line:
            self.log.error("unable to find requested log line <<%s>>  in SIDBEngine.log..", reg_exp)
            raise Exception("log line not found in SIDBEngine.log..")

        reg_exp = rf"{sidb_id}-\d*-{substore_id}-\d*-(\d*|#) .* Backward referencing Store \[{sealed_store_id}\]"
        self.log.info("searching SIDBEngine.log using following regular expression : %s", reg_exp)
        matched_line, matched_string = self.dedup_helper.parse_log(client=self.media_agent,
                                                                   log_file="SIDBEngine.log",
                                                                   regex=reg_exp,
                                                                   escape_regex=False,
                                                                   single_file=False)
        if not matched_line:
            self.log.error("unable to find requested log line <<%s>>  in SIDBEngine.log..", reg_exp)
            raise Exception("log line not found in SIDBEngine.log..")

    def verify_arch_file_sidb_keys(self):
        """ Verify archFileSIDBKeys records for archFileId(s) in sealed store are copied to new store

            Raises:
                Exception           - If failed to fetch result from select query
                                    - If entries corresponding to sealed store archFileId(s) are missing from new store
                                    - If entries corresponding to sealed store archFileId(s) have mismatch in encKeyType
                                    - If entries corresponding to sealed store archFileId(s) have mismatch in encKeyId

            Returns:
                None
        """
        get_arch_file_ids = f"""
SELECT	archFileId
FROM	archFileSIDBKeys WITH (NOLOCK)
WHERE	SIDBStoreId = {self.sealed_store_id}
        AND		archCopyId = {self.primary_copy.copy_id}"""

        validation_query = f"""
SELECT	archFileId, SIDBStoreId, encKeyType, encKeyId
FROM	archFileSIDBKeys WITH (NOLOCK)
WHERE	archFileId IN ({get_arch_file_ids})
        AND		archCopyId = {self.primary_copy.copy_id}"""

        self.log.info("Performing archFileSIDBKeys validations after sealing Store:")

        priming_occurred = False
        mismatch_occurred = False
        rows_matched = []
        rows_not_present = []
        rows_not_matched = []

        results = self.mm_helper.execute_select_query(get_arch_file_ids)
        if results[0] == '':
            raise Exception("Did not receive any archFileId for sealed store!")

        results = self.mm_helper.execute_select_query(validation_query)
        if results[0] == '':
            raise Exception("Did not receive any result from select query!")

        sealed_store_records = {
            archFileId: [encKeyType, encKeyId]
            for [archFileId, SIDBStoreId, encKeyType, encKeyId] in results
            if SIDBStoreId == self.sealed_store_id
        }
        active_store_records = {
            archFileId: [encKeyType, encKeyId]
            for [archFileId, SIDBStoreId, encKeyType, encKeyId] in results
            if SIDBStoreId == self.sidb_id
        }

        for [archFileId, [encKeyType, encKeyId]] in sealed_store_records.items():
            self.log.info(f"Selecting archFileId {archFileId} from sealed store records")

            # Entries for jobs corresponding to sealed store are present in records for new store.
            self.log.info(f"... Checking if archFileId {archFileId} also present in active store records")
            if archFileId not in active_store_records:
                rows_not_present.append(archFileId)
                self.log.error(f"... Entry corresponding to {archFileId} from sealed store is missing from new store!")
                self.log.info("... Above error may occur due to archFileId not being referred by new jobs.")
                continue
            self.log.info(f"... archFileId {archFileId} present in both stores")

            priming_occurred = True

            # encKeyType for archFileId corresponding to sealed store should match
            self.log.info(f"... Checking if encKeyType {encKeyType} for archFileId {archFileId} matches")
            if encKeyType != active_store_records[archFileId][0]:
                mismatch_occurred = True
                rows_not_matched.append((archFileId, encKeyType, encKeyId))
                rows_not_matched.append((archFileId, *active_store_records[archFileId]))
                self.log.error(f"... Entry corresponding to archFileId {archFileId} have mismatch in encKeyType!")
                continue
            self.log.info(f"... encKeyType {encKeyType} for archFileId {archFileId} matches in both stores")

            # encKeyId for archFileId corresponding to sealed store should match
            self.log.info(f"... Checking if encKeyId {encKeyId} for archFileId {archFileId} matches")
            if encKeyId != active_store_records[archFileId][1]:
                mismatch_occurred = True
                rows_not_matched.append((archFileId, encKeyType, encKeyId))
                rows_not_matched.append((archFileId, *active_store_records[archFileId]))
                self.log.error(f"... Entry corresponding to archFileId {archFileId} have mismatch in encKeyId!")
                continue
            self.log.info(f"... encKeyId {encKeyId} for archFileId {archFileId} matches in both stores")

            rows_matched.append((archFileId, encKeyType, encKeyId))

        self.log.info("Following (archFileId, encKeyType, encKeyId) found in both stores: ")
        self.log.info(rows_matched)

        self.log.info("Following (archFileId, encKeyType, encKeyId) did not match in both stores: ")
        self.log.info(rows_not_matched)

        self.log.info("Following (archFileId) not present in new store: ")
        self.log.info(rows_not_present)

        if priming_occurred:
            if mismatch_occurred:
                raise Exception(f"Mis-matched (archFileId, encKeyType, encKeyId): {rows_not_matched}")
            else:
                self.log.info("Result: PASS")
        else:
            raise Exception("Not even a single archFileId was referred in new store records!")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # checking if dedup enabled
            if self.is_dedupe_enabled(copy=self.primary_copy):
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception(f"dedup not enabled on storage policy {self.storage_policy_name}")

            # getting store and substore ids
            store_ids = self.dedup_helper.get_sidb_ids(
                copy_name="primary", sp_id=self.storage_policy.storage_policy_id)
            self.sidb_id, self.substore_id = store_ids[0], store_ids[1]

            # enable store priming on primary copy at GDSP level
            self.gdsp_copy.store_priming = True
            if not self.gdsp_copy.store_priming:
                self.log.error("DDB store priming enabling failed..")
                raise Exception("failed to enable DDB store priming on copy..")
            self.log.info("DDB store priming enabled on copy..")

            # run backup job
            backup_cycle = ['full', 'incremental', 'incremental', 'synthetic_full']
            for backup_level in backup_cycle:
                self.run_backup(backup_level)

            # priming before sealing store
            self.log.info("CASE 1:  Priming Before Sealing store")

            # verify from logs
            self.verify_logs(sidb_id=self.sidb_id, substore_id=self.substore_id)
            self.log.info("backward referencing did not occur.. as expected..")
            self.log.info("Result :Pass")

            # seal store
            self.gdsp.seal_ddb("Primary_Global")

            # getting new store and substore ids
            self.sealed_store_id = self.sidb_id
            store_ids = self.dedup_helper.get_sidb_ids(
                copy_name="primary", sp_id=self.storage_policy.storage_policy_id)
            self.sidb_id, self.substore_id = store_ids[0], store_ids[1]

            # run full backup
            for backup_level in backup_cycle:
                self.run_backup(backup_level)

            # priming after sealing store
            self.log.info("CASE 2:  Priming After Sealing store")

            # verify from logs
            self.verify_logs(sidb_id=self.sidb_id, substore_id=self.substore_id,
                             sealed_store_id=self.sealed_store_id)
            self.log.info("Log lines found as expected..store priming [backward referencing] occurred..")
            self.log.info("Result :Pass")

            # Verify archFileSIDBKeys records for archFileId(s) in sealed store are copied to new store
            self.verify_arch_file_sidb_keys()

            self.gdsp_copy.store_priming = False
            if self.gdsp_copy.store_priming:
                self.log.error("DDB store priming disabling failed..")
                raise Exception("failed to disable DDB store priming on copy..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("********* clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.error("clean up ERROR %s", exp)
