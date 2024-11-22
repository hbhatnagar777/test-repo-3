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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_auxcopy_job()   --  runs auxcopy job for all copies

    run_restore_job()   --  runs restore job for a given copy precedence

    verify_encryption_type()    --  verify encryption type from CSDB for a given copy

    update_encryption_key() --  updates encryption keys for archfiles of a given copy


Prerequisites: None

Input JSON:

"51030": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "pool_name": "<name of the storage pool to be reused>" (optional argument),
        "pool_name2": "<name of the second storage pool to be reused>" (optional argument),
        "pool_name3": "<name of the third storage pool to be reused>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. Allocate resources
2. set encryption on primary copy of plan
3. create a secondary copy
4. set re-encrypt on secondary with GOST
5. create a tertiary copy with secondary copy as source
6. run two full backups
7. run first auxcopy job in parallel
8. validate encryption key from CSDB
9. update encryption key for secondary in AFC table
10. run auxcopy from secondary to tertiary
11. verify that the auxcopy job fails
12. run a restore job from secondary with copy preference as 2
13. verify that the restore job fails
14. deallocate all resources

"""
import time
from time import sleep
from AutomationUtils import constants, commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


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
        self.name = "Negative case for restore & aux failure with enc key manipulation in CSDB"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path_copy1 = None
        self.dedup_store_path2 = None
        self.dedup_store_path_copy2 = None
        self.dedup_store_path3 = None
        self.dedup_store_path_copy3 = None
        self.content_path = None
        self.restore_path = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.sidb_id = None
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
        self.storage_pool2 = None
        self.storage_pool3 = None
        self.pool_name = None
        self.pool_name2 = None
        self.pool_name3 = None
        self.pool = None
        self.pool2 = None
        self.pool3 = None
        self.plan = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy = None
        self.tertiary_copy = None
        self.secondary_pool_copy = None
        self.tertiary_pool_copy = None
        self.is_user_defined_global_pool = False
        self.is_user_defined_dedup = False
        self.enc_type_blowfish = "BlowFish"
        self.enc_type_gost = "GOST"
        self.enc_type_aes = "AES"
        self.enc_len_128 = 128
        self.enc_len_256 = 256
        self.enc_type_id = 11

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("pool_name") and self.tcinputs.get("pool_name2") \
                and self.tcinputs.get("pool_name3"):
            self.is_user_defined_global_pool = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent)[:] + "_" + str(self.client.client_name)[:]

        self.plan_name = "{0}_Plan{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)

        self.client_machine, self.testcase_path_client = self.mm_helper.generate_automation_path(self.client.client_name, 25*1024)
        self.media_agent_machine, self.testcase_path_media_agent = self.mm_helper.generate_automation_path(self.tcinputs['MediaAgentName'], 25*1024)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")

        if self.is_user_defined_global_pool:
            self.pool_name = self.tcinputs["pool_name"]
            self.pool = self.commcell.storage_pools.get(self.pool_name)
            self.pool_name2 = self.tcinputs["pool_name2"]
            self.pool2 = self.commcell.storage_pools.get(self.pool_name2)
            self.pool_name3 = self.tcinputs["pool_name3"]
            self.pool3 = self.commcell.storage_pools.get(self.pool_name3)

        else:
            self.pool_name = "{0}_pool{1}".format(str(self.id), suffix)
            self.pool_name2 = self.pool_name + '2'
            self.pool_name3 = self.pool_name + '3'

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        self.dedup_store_path1 = self.dedup_store_path + '1'
        self.dedup_store_path_copy1 = self.dedup_store_path + 'Copy1'

        self.dedup_store_path2 = self.dedup_store_path + '2'
        self.dedup_store_path_copy2 = self.dedup_store_path + 'Copy2'

        self.dedup_store_path3 = self.dedup_store_path + '3'
        self.dedup_store_path_copy3 = self.dedup_store_path + 'Copy3'

        # sql connections
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)

    def new_content(self, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        returns None
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

        if self.client_machine.check_directory_exists(self.restore_path):
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("restore_path deleted")
        else:
            self.log.info("restore_path does not exist.")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.backup_set = self.agent.backupsets.get(self.backupset_name)
            self.subclient = self.backup_set.subclients.get(self.subclient_name)
            if self.backup_set.subclients.has_subclient(self.subclient_name):
                self.subclient.plan = None
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.plans.has_plan(self.plan_name):
            self.commcell.plans.delete(self.plan_name)
            self.log.info("plan deleted")
        else:
            self.log.info("plan does not exist.")

        if not self.is_user_defined_global_pool:
            # here the storage pool is automatically created by pool and therefore has the same name as pool.
            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.commcell.storage_pools.delete(self.pool_name)
                self.log.info("pool deleted")
            else:
                self.log.info("pool does not exist.")

            if self.commcell.storage_pools.has_storage_pool(self.pool_name2):
                self.commcell.storage_pools.delete(self.pool_name2)
                self.log.info("pool 2 deleted")
            else:
                self.log.info("pool 2 does not exist.")

            if self.commcell.storage_pools.has_storage_pool(self.pool_name3):
                self.commcell.storage_pools.delete(self.pool_name3)
                self.log.info("pool 3 deleted")
            else:
                self.log.info("pool 3 does not exist.")

        self.commcell.storage_pools.refresh()
        self.log.info("clean up successful")

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.error("previous run clean up ERROR")
            raise Exception(f"ERROR:{exp}")

    def allocate_resources(self):
        """creates all necessary resources for testcase to run"""
        # create dedupe store paths
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path1):
            self.log.info("store path 1 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path1)
            self.log.info("store path 1 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path2):
            self.log.info("store path 2 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path2)
            self.log.info("store path 2 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path3):
            self.log.info("store path 3 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path3)
            self.log.info("store path 3 created")

        if not self.is_user_defined_global_pool:
            self.log.info("creating pool1")
            self.pool = self.commcell.storage_pools.add(self.pool_name, self.mount_path, self.media_agent, [self.media_agent, self.media_agent], [self.dedup_store_path1, self.dedup_store_path_copy1])
            self.log.info("created pool1")
            self.log.info("creating pool2")
            self.pool2 = self.commcell.storage_pools.add(self.pool_name2, self.mount_path + '2', self.media_agent, [self.media_agent, self.media_agent], [self.dedup_store_path2, self.dedup_store_path_copy2])
            self.log.info("created pool2")
            self.log.info("creating pool3")
            self.pool_name3 = self.pool_name3
            self.pool3 = self.commcell.storage_pools.add(self.pool_name3, self.mount_path + '3', self.media_agent, [self.media_agent, self.media_agent], [self.dedup_store_path3, self.dedup_store_path_copy3])
            self.log.info("created pool3")

        # create dependent plan
        self.log.info("Creating plan")
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)

        # disabling the schedule policy
        self.log.info('Disabling the schedule policy')
        self.plan.schedule_policies['data'].disable()

        # add backupset
        self.log.info(f"Adding the backup set [{self.backupset_name}]")
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info(f"Backup set Added [{self.backupset_name}]")

        # add subclient
        self.log.info(f"Adding the subclient set [{self.subclient_name}]")
        self.subclient = self.backup_set.subclients.add(self.subclient_name)
        self.log.info(f"Subclient set Added [{self.subclient_name}]")

        # Add plan and content to the subclient
        self.log.info("Adding plan to subclient")
        self.subclient.plan = [self.plan, [self.content_path]]
        self.subclient.enable_backup()

        # create primary copy object for storage policy
        self.primary_copy = self.plan.storage_policy.get_copy(copy_name="primary")

        # create secondary copy for storage policy
        self.plan.add_storage_copy(self.plan_name + '_secondary', self.pool_name2)
        self.secondary_copy = self.plan.storage_policy.get_copy(self.plan_name + '_secondary')

        # Remove Association with System Created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.plan_name + "_secondary")

        # add data to subclient content
        self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=1)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

        # set enc on primary copy BlowFish 128
        self.primary_copy.set_encryption_properties(re_encryption=True, encryption_type=self.enc_type_blowfish, encryption_length=self.enc_len_128)

        # set re-encrypt on secondary as GOST 256
        self.secondary_pool_copy = self.commcell.storage_policies.get(self.pool_name2).get_copy("Primary")
        self.secondary_pool_copy.set_encryption_properties(re_encryption=True, encryption_type=self.enc_type_gost, encryption_length=self.enc_len_256)

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        self.log.info(f"starting {job_type} backup job...")
        job = self.subclient.backup(backup_level=job_type)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info(f"Backup job: {job.job_id} completed successfully")

        return job.job_id

    def run_aux_copy(self):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:

        returns job id(int)
        """
        self.log.info("starting auxcopy job...")
        job = self.plan.storage_policy.run_aux_copy(media_agent=self.media_agent)
        self.log.info(f"AuxCopy Job[{job.job_id}] started")
        sleep(60)
        for iterator in range(1, 5):
            if job.state.lower() == "completed":
                break
            elif job.state.lower() == "pending":
                self.log.info(f"Job is in pending state with JPR: {job.pending_reason}. Killing the job")
                job.kill()
                raise Exception(job.pending_reason)
            else:
                sleep(120)

        if job.state.lower() != "completed":
            self.log.info(f"Job is not completed. JPR: {job.pending_reason}. Killing the job")
            job.kill()
            raise Exception(job.pending_reason)

        self.log.info(f"auxcopy job: {job.job_id} completed successfully")
        return job.job_id

    def run_restore_job(self):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:

        returns job id(int)
        """
        self.log.info("starting restore job...")
        job = self.subclient.restore_out_of_place(self.client.client_name,
                                                  self.restore_path,
                                                  [self.content_path],
                                                  copy_precedence=2)

        sleep(60)
        for iterator in range(1, 5):
            if job.state.lower() == "completed":
                break
            elif job.state.lower() == "pending":
                job.kill()
                raise Exception(job.pending_reason)
            else:
                sleep(120)

        if job.state.lower() != "completed":
            job.kill()
            raise Exception(job.pending_reason)

        self.log.info(f"restore job: {job.job_id} completed successfully")
        return job.job_id

    def verify_encryption_type(self, copy, encryption_type):
        """
        checks if the copy encryption and user specified encryption type match

            Args:
                copy        (instance)      copy object
                encryption_type    (str)           encryption type

        returns Boolean
        """
        flag = False
        copy_id = copy.get_copy_id()
        query = f"""select distinct encKeyType from archFileCopy
                    where archfileid  in (select id from archFile where filetype = 1)
                    and  archCopyId = {copy_id}"""
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)

        if len(self.csdb.rows) > 1:
            self.log.error(f"more than one enctype returned by query : {self.csdb.rows}")
            raise Exception("more than one enctype returned..")

        enc_key = int(self.csdb.fetch_one_row()[0])
        self.log.info("enctype retrieved from CSDB : %d", enc_key)

        if encryption_type == self.enc_type_gost and enc_key == self.enc_type_id:
            flag = True
        else:
            self.log.error(f"expected enctype was : {self.enc_type_id}")

        return flag

    def update_enc_key(self, copy, key):
        """
        updates encryption key for archfiles of given copy

            Args:
                copy        (instance)      copy object
                key         (int)           value to be set for key
        """
        query = f"update ArchEncKeys set encKey = {key} where archCopyId ={copy.copy_id}"
        self.log.info(f"Executing Query: {query}")
        self.mm_helper.execute_update_query(query, self.sql_password, "sqladmin_cv")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # checking if dedup enabled
            if self.primary_copy.is_dedupe_enabled():
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception(f"dedup not enabled on storage policy {self.plan.storage_policy.storage_policy_name}")

            # run two full backups
            job1 = self.run_backup("Full")
            time.sleep(60)
            job2 = self.run_backup("Full")
            time.sleep(60)

            # run first auxcopy
            aux_copy1 = self.run_aux_copy()

            # validate enc in DB via CSDB
            secondary_copy = self.plan.storage_policy.get_copy(self.plan_name + "_secondary")
            if self.verify_encryption_type(copy=secondary_copy, encryption_type="GOST"):
                self.log.info("PASSED for Dedupe GOST Re-Encryption")
            else:
                self.log.error("FAILED for Dedupe GOST Re-Encryption")
                raise Exception("Enc type mismatch for secondary copy..")

            # update enc key for job in AFC table
            self.log.info("Update Enc key")
            self.update_enc_key(copy=self.pool2, key=12345678)

            # create tertiary copy for storage policy
            self.log.info("Creating the tertiary copy")
            self.plan.add_storage_copy(self.plan_name + '_tertiary', self.pool_name3)
            self.tertiary_copy = self.plan.storage_policy.get_copy(self.plan_name + '_tertiary')

            # removing copy from autocopy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.plan_name + "_tertiary")

            # setting secondary copy as source for tertiary copy
            self.tertiary_copy.source_copy = self.secondary_copy.copy_name

            # setting re-encrypt on tertiary copy with AES 256
            pool3_copy = self.commcell.storage_policies.get(self.pool_name3).get_copy("Primary")
            # pool3_copy.set_encryption_properties(re_encryption=True, encryption_type="AES", encryption_length=256)
            self.mm_helper.set_encryption(pool3_copy)

            # run auxcopy from secondary to tertiary
            # verify that job fails
            error_flag = False
            try:
                aux_copy2 = self.run_aux_copy()
                self.log.error("Auxcopy succeeded when it shouldn't have..")
            except Exception as exp:
                reason = \
                    "Data is encrypted. Decryption initialization failed."
                str(exp).find(reason)
                if str(exp).find(reason) != -1:
                    self.log.info(f"Auxcopy job failed as expected with exception {exp}")
                    error_flag = True
                else:
                    self.log.error(f"Auxcopy failed due to other reasons.. {exp}")
            finally:
                if not error_flag:
                    raise Exception("Auxcopy job completed unexpectedly\\ failed due to unexpected issues..")

            # run restore from secondary with preference as copy 2
            # verify that restore fails
            error_flag = False
            try:
                restore_1 = self.run_restore_job()
                self.log.error("Restore succeeded when it shouldn't have..")
            except Exception as exp:
                reason = "Failed to fetch correct restore encryption key.Error[Key unwrapping failed: unknown method.]"
                if str(exp).find(reason) != -1:
                    self.log.info(f"Restore job failed as expected with exception {exp}")
                    error_flag = True
                else:
                    self.log.error(f"Restore failed due to other reasons.. {exp}")
            finally:
                if not error_flag:
                    raise Exception("Restore job completed unexpectedly\\ failed due to unexpected issues..")

            self.log.info("All Validations Completed.. Testcase executed successfully..")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Test Case Completed. Starting Cleanup")
        try:
            self.log.info("Starting cleanup")
            self.deallocate_resources()
        except Exception as exe:
            self.log.warning(f"Cleanup Failed. You might need to cleanup Manually. Error: {exe}")
