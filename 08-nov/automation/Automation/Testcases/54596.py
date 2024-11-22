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

    delete_job()    --  deletes the specified job

    verify_logs()   --  checks logs for encryption

    run_auxcopy_job()   --  runs auxcopy job for all copies

    run_restore_job()   --  runs restore job for a given copy precedence

    verify_encryption_type()    --  verify encryption type from CSDB for a given copy

    delete_encryption_key() --  removes encryption key for a given copy

    validate_plan_properties() -- Validates default properties of the plan.


Prerequisites: None

Input JSON:

"54596": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "global_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "global_pool_name2": "<name of the second storage pool to be reused>" (optional argument),
        "global_pool_name3": "<name of the third storage pool to be reused>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. Allocate resources
2. set encryption on primary copy of sp
3. create a secondary copy
4. run two full backups
5. run first auxcopy job in parallel
6. running first auxcopy and validating enc key in DB for AFC, AEK & AFSK tables
7. delete first backup and run data aging
8. Deleting row in ArchEncKeysTable and running aux to tertiary copy
9. creating tertiary copy: secsource with sec copy as source
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
        self.name = "Client Encryption Feature Acceptance Case with negative case included"
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
        self.global_pool_name = None
        self.global_pool_name2 = None
        self.global_pool_name3 = None
        self.global_pool = None
        self.global_pool2 = None
        self.global_pool3 = None
        self.plan = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy = None
        self.tertiary_copy = None
        self.is_user_defined_storpool = False
        self.is_user_defined_global_pool = False
        self.is_user_defined_dedup = False
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name") and self.tcinputs.get("storage_pool_name2") \
                and self.tcinputs.get("storage_pool_name3"):
            self.is_user_defined_storpool = True
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

        self.client_machine, self.testcase_path_client = self.mm_helper.generate_automation_path(
            self.client.client_name, 25 * 1024)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")

        self.media_agent_machine, self.testcase_path_media_agent = self.mm_helper.generate_automation_path(self.tcinputs['MediaAgentName'], 25*1024)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_storpool:
            self.global_pool_name = self.tcinputs["global_pool_name"]
            self.global_pool = self.commcell.storage_pools.get(self.global_pool_name)
            self.global_pool_name2 = self.tcinputs["global_pool_name2"]
            self.global_pool2 = self.commcell.storage_pools.get(self.global_pool_name2)
            self.global_pool_name3 = self.tcinputs["global_pool_name3"]
            self.global_pool3 = self.commcell.storage_pools.get(self.global_pool_name3)

        else:
            self.global_pool_name = "{0}_global_pool{1}".format(str(self.id), suffix)
            self.global_pool_name2 = self.global_pool_name + '2'
            self.global_pool_name3 = self.global_pool_name + '3'

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
        self.commcell.storage_pools.refresh()

        if not self.is_user_defined_global_pool:
            # here the storage pool is automatically created by global_pool and therefore has the same name as global_pool.
            if self.commcell.storage_pools.has_storage_pool(self.global_pool_name):
                self.commcell.storage_pools.delete(self.global_pool_name)
                self.log.info("global_pool deleted")
            else:
                self.log.info("global_pool does not exist.")

            if self.commcell.storage_pools.has_storage_pool(self.global_pool_name + '2'):
                self.commcell.storage_pools.delete(self.global_pool_name + '2')
                self.log.info("global_pool 2 deleted")
            else:
                self.log.info("global_pool 2 does not exist.")

            if self.commcell.storage_pools.has_storage_pool(self.global_pool_name + '3'):
                self.commcell.storage_pools.delete(self.global_pool_name + '3')
                self.log.info("global_pool 3 deleted")
            else:
                self.log.info("global_pool 3 does not exist.")
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
            raise Exception(f"ERROR: {exp}")

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

        # create global_pool if not provided
        if not self.is_user_defined_global_pool:
            self.log.info("creating global_pool1")
            self.global_pool = self.commcell.storage_pools.add(self.global_pool_name, self.mount_path, self.media_agent,
                                                        [self.media_agent, self.media_agent], [self.dedup_store_path1, self.dedup_store_path_copy1])
            self.log.info("created global_pool1")

            self.log.info("creating global_pool2")
            self.global_pool2 = self.commcell.storage_pools.add(self.global_pool_name2, self.mount_path + '2', self.media_agent,
                                                         [self.media_agent, self.media_agent], [self.dedup_store_path2, self.dedup_store_path_copy2])
            self.log.info("created global_pool2")

            self.log.info("creating global_pool3")
            self.global_pool3 = self.commcell.storage_pools.add(self.global_pool_name3, self.mount_path + '3', self.media_agent,
                                                         [self.media_agent, self.media_agent], [self.dedup_store_path3, self.dedup_store_path_copy3])
            self.log.info("created global_pool3")

        # create plan
        self.log.info("Creating plan")
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.global_pool_name)

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

        # create primary copy object for plan
        self.primary_copy = self.plan.storage_policy.get_copy(copy_name="primary")

        # create secondary copy for plan
        self.plan.add_storage_copy(self.plan_name + '_secondary', self.global_pool_name2)
        self.secondary_copy = self.plan.storage_policy.get_copy(self.plan_name + '_secondary')

        # Remove Association with System Created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.plan_name + "_secondary")

        # add data to subclient content
        self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=1)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

        global_pool1_copy = self.commcell.storage_policies.get(self.global_pool_name).get_copy('Primary')
        global_pool1_copy.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)

        # set re-encrypt on secondary as GOST 256
        global_pool2_copy = self.commcell.storage_policies.get(self.global_pool_name2).get_copy('Primary')
        global_pool2_copy.set_encryption_properties(re_encryption=True, encryption_type="GOST", encryption_length=256)

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

    def delete_job(self, job_id, copy):
        """
        deletes all jobs whose job ids are passed as argument

            Args:
                job_id        (str)         job id of job to be deleted
                copy          (instance)    instance of copy object

        returns None
        """
        self.log.info(f"deleting job {job_id} ...")
        copy.delete_job(job_id)

    def run_aux_copy(self):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:

        returns job id(int)
        """
        self.log.info("starting auxcopy job...")
        job = self.plan.storage_policy.run_aux_copy(media_agent=self.media_agent)

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
        self.log.info(f"Restore Job [{job.job_id}] started")
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

    def verify_encryption(self, encryption_type):
        """
        checks if the copy encryption and user specified encryption type match

            Args:
                encryption_type        (str)           encryption type

        returns Boolean
        """
        self.log.info("CASE 1:  verify encryption type per copy from ArchFileCopy table")
        copy_id = self.secondary_copy.get_copy_id()
        query = f"""select distinct encKeyType from archFileCopy
                            where archfileid  in (select id from archFile where filetype = 1)
                            and  archCopyId = {copy_id}"""
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)

        if len(self.csdb.rows) > 1:
            self.log.error(f"more than one enctype returned by query : {self.csdb.rows}")

        encryption_type_afc = int(self.csdb.fetch_one_row()[0])

        self.log.info("enctype retrieved from CSDB : %d", encryption_type_afc)

        if encryption_type == "GOST" and encryption_type_afc != 11:
            self.log.error("encryption validation failed against ArchFileCopy table.. expected enctype was : 11")
            return False
        self.log.info("verified encryption type against ArchFileCopy table..")

        self.log.info("CASE 2:  verify encryption type per copy from ArchEncKeys table")
        copy_id = self.global_pool2.copy_id
        query = f"""select encKeyType from ArchEncKeys where clientId = {int(self.client.client_id)} 
                    and archCopyId = {copy_id}"""
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)

        if len(self.csdb.rows) > 1:
            self.log.error(f"more than one enctype returned by query : {self.csdb.rows}")
            raise Exception("more than one enctype returned..")

        self.log.info(self.csdb.fetch_one_row())

        encryption_type_aek = int(self.csdb.fetch_one_row()[0])

        self.log.info("enctype retrieved from CSDB : %d", encryption_type_aek)

        if encryption_type == "GOST" and encryption_type_aek != 11:
            self.log.error("encryption validation failed against ArchEncKeys table.. expected enctype was : 11")
            return False
        self.log.info("verified encryption type against ArchEncKeys table..")

        self.log.info("CASE 3:  verify encryption key is empty in ArchFileSidbKeys table")
        copy_id = self.primary_copy.get_copy_id()
        query = f"""select encKey from archFileSIDBKeys
                where archfileid  in (select id from archFile where filetype = 1) and  archCopyId = {copy_id}"""
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)

        if len(self.csdb.rows) > 1:
            self.log.error(f"more than one enctype returned by query : {self.csdb.rows}")
            raise Exception("more than one enctype returned..")

        encryption_key = self.csdb.fetch_one_row()[0]

        self.log.info(f"enctype retrieved from CSDB : {encryption_key}")

        if encryption_type == "GOST" and encryption_key != '':
            self.log.error("encryption validation failed against ArchFileSidbKeys table.. expected key was : ''")
            return False
        self.log.info("verified encryption key against ArchFileSidbKeys table..")

        self.log.info("encryption type and key have been validated against AFC, AEK, and AFSK tables..")
        return True

    def delete_encryption_key(self, copy):
        """
        deletes row from ArchEncKeys for the given copy

            Args:
                copy        (instance)      copy object
        """
        copy_id = copy.copy_id
        query = f"""delete from ArchEncKeys where clientId = {int(self.client.client_id)} and archCopyId = {copy_id}"""
        self.log.info(f"Executing Query: {query}")
        self.mm_helper.execute_update_query(query, self.sql_password, "sqladmin_cv")

    def validate_plan_properties(self):
        """ Validates default properties of the plan """
        primary_copy = self.plan.storage_policy.get_copy("Primary")

        self.log.info("Primary copy retention details")
        copy_retention_details = primary_copy.copy_retention
        if 'days' in copy_retention_details and 'cycles' in copy_retention_details:
            self.log.info(f"Retention Period {copy_retention_details.get('days')} days, {copy_retention_details.get('cycles')} cycles")
        else:
            self.log.info("copy retention details are not set")

        self.log.info("Check if data aging is enabled or not.")
        retention_rules = primary_copy._copy_properties.get('retentionRules')
        retention_flags = retention_rules.get("retentionFlags")
        data_aging_enabled = retention_flags.get("enableDataAging")
        if data_aging_enabled:
            self.log.info(f"Data aging is enabled.")
        else:
            self.log.info("Data aging disabled.")

        self.log.info("checking if extended retention rules are set or not")
        copy_retention_rules = primary_copy.extended_retention_rules
        if copy_retention_rules[0] == False and copy_retention_rules[1] == False and copy_retention_rules[2] == False:
            self.log.info("All the copy retention rules are OFF")
        else:
            if copy_retention_rules[0]:
                self.log.info("Retention Rule 1 are set")
            if copy_retention_rules[1]:
                self.log.info("Retention Rule 2 are set")
            if copy_retention_rules[2]:
                self.log.info("Retention Rule 3 are set")

        self.log.info("checking if DASHFull is enabled or not")
        is_dedupe_dashfull_enabled = primary_copy.copy_dedupe_dash_full
        if is_dedupe_dashfull_enabled:
            self.log.info(f"DashFull is Enabled")
        else:
            self.log.info("DashFull is disabled")

        self.log.info("checking if Copy client side dedupe is enabled or not")
        client_side_dedup_enabled = primary_copy.copy_client_side_dedup
        if client_side_dedup_enabled:
            self.log.info(f"Client side dedupe is enabled.")
        else:
            self.log.info(f"Client side dedupe is disabled.")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            self.validate_plan_properties()

            # checking if dedup enabled
            if self.primary_copy.is_dedupe_enabled():
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception(f"dedup not enabled on plan {self.plan_name}")

            # run two full backups
            job1 = self.run_backup("Full")
            time.sleep(60)
            job2 = self.run_backup("Full")
            time.sleep(60)

            # run first auxcopy
            self.run_aux_copy()

            # validating enc key in DB for AFC, AEK & AFSK tables
            if self.verify_encryption(encryption_type="GOST"):
                self.log.info("PASSED for Dedupe GOST Re-Encryption")
            else:
                self.log.error("FAILED for Dedupe GOST Re-Encryption")
                raise Exception("Enc type mismatch for secondary copy..")

            # delete first backup and run data aging
            self.delete_job(job_id=job1, copy=self.secondary_copy)
            self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                 storage_policy_name=self.plan.storage_policy.storage_policy_name,
                                                 is_granular=True,
                                                 include_all_clients=True)

            # Deleting row in ArchEncKeysTable and running aux to tertiary copy
            self.delete_encryption_key(copy=self.global_pool2)

            # create tertiary copy for storage policy
            self.plan.add_storage_copy(self.plan_name + '_tertiary', self.global_pool_name3)
            self.tertiary_copy = self.plan.storage_policy.get_copy(self.plan_name + '_tertiary')

            # removing copy from autocopy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name,
                                                    self.plan_name + "_tertiary")

            # setting secondary copy as source for tertiary copy
            self.tertiary_copy.source_copy = self.secondary_copy.copy_name

            # setting re-encrypt on tertiary copy with AES 256
            global_pool3_copy = self.plan.storage_policy.get_copy(self.plan_name + '_tertiary')
            # global_pool3_copy.set_encryption_properties(re_encryption=True, encryption_type="AES", encryption_length=256)
            self.mm_helper.set_encryption(global_pool3_copy)

            # run restore from secondary with preference as copy 2
            # verify that restore fails and chunks are marked bad
            try:
                self.run_restore_job()
                error = "Restore succeeded when it shouldn't have.."
                self.log.error(error)
                self.status = constants.FAILED
                self.result_string += error
            except Exception as exp:
                self.log.info(f"Restore job failed as expected with exception {exp}")
            engine = self.commcell.deduplication_engines.get(self.global_pool_name2, 'Primary')
            store_id = engine.all_stores[0][0]
            query = f'''select archChunkId, SIDBStoreId from archChunkDDBDrop
                    where SIDBStoreId = {int(store_id)}'''
            self.log.info(f"Executing Query: {query}")
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            self.log.info(f"Result: {rows}")
            if len(rows) > 0 and rows[0] != ['']:
                self.log.info("Chunks are marked bad as expected")
            else:
                error = "Chunks are not marked bad"
                self.log.error(error)
                self.status = constants.FAILED
                self.result_string += error
            # run auxcopy from secondary to tertiary
            # verify that job fails
            try:
                self.run_aux_copy()
                error = "Auxcopy succeeded when it shouldn't have.."
                self.log.error(error)
                self.status = constants.FAILED
                self.result_string += error
            except Exception as exp:
                self.log.info(f"Auxcopy job failed as expected with exception {exp}")

            self.log.info("All Validations Completed.. Testcase executed successfully..")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Test Case Completed. Starting Cleanup")
        try:
            self.deallocate_resources()
        except Exception as exe:
            self.log.warning(f"Cleanup Failed. You might need to cleanup Manually. Error: {exe}")
