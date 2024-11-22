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

    verify_logs()   --  verify encryption setting from logs

    run_auxcopy_job()   --  runs auxcopy job for all copies

    run_restore_job()   --  runs restore job for a given copy precedence

    verify_encryption_type()    --  verify encryption type from CSDB for a given copy

    get_mmconfig_for_infini_DDB()   --  checks if infiniDDB is enabled or not

This testcase checks various encryption options for auxcopy with recopy operation and changing encryption options.

Prerequisites: None

Input JSON:

"50424": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. allocate necessary resources
2. set encryption to Blowfish 256 on client
3. set Blowfish 256 enc on primary copy
4. set reencryption on copy1 with GOST, 256
5. set store in plain text on copy2
6. set store in plain text with network encryption SERPENT, 128 on copy3
7. set Preserve enc mode as in source on copy4
8. run two full backups
9. check mmconfig for infiniDDB config value: if true run dash_copy else run old aux_copy
10.validate network only encryption option on copy3
11.picking jobs on copy1 for recopy
12.update encryption on copy1 to store as plaintext
13.running aux copy
14.validate copy encryption
15.picking jobs for recopy on copy2
16.Preserve enc mode as in source on copy2
17.running aux copy
18.validation of enc option which should be PASSTHRU blowfish from source
19.picking jobs for recopy on copy3
20.setting reencryption on copy 3 to DES3 192
21.running aux copy
22.validation of enc option
23.picking jobs for recopy on copy4
24.Store in plain text with N/W enc TWOFISH 256 on copy 4
25.running aux copy
26.validation of enc option
27.run restores from all copies
28.picking jobs on copy1 for recopy
29.update encryption on copy1 to preserve source encryption
30.running aux copy
31.validation of enc option
32.picking jobs for recopy on copy2
33.enc option PASSTHRU with N/w encryption AES 128 on copy2
34.running aux copy
35.validation of enc option PASSTHRU with N/w encryption AES 128
36.picking jobs for recopy on copy3
37.setting reencryption on copy 3 to Serpent 128
38.running aux copy
39.validation of enc option
40.picking jobs for recopy on copy4
41.Store in plain text on copy 4
42.running aux copy
43.validation of enc option which should be PASSTHRU blowfish from source
44.run restores from all copies
45.deallocate resources


"""
from time import sleep
from time import time
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
        self.name = "All Encryption options verification on dedupe copies with recopy & change option Case"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.storage_pool_name = None
        self.storage_pool_name2 = None
        self.storage_pool_name3 = None
        self.library_name = None
        self.storage_policy_name = None
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
        self.library = None
        self.library2 = None
        self.library1 = None
        self.library3 = None
        self.library4 = None
        self.gdsp_name = None
        self.gdsp = None
        self.gdsp1 = None
        self.gdsp2 = None
        self.gdsp3 = None
        self.gdsp4 = None
        self.copy1 = None
        self.copy2 = None
        self.copy3 = None
        self.copy4 = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy = None
        self.tertiary_copy = None
        self.is_user_defined_dedup = False
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent)[::-1] + "_" + str(self.client.client_name)[::-1]

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

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, self.id)

        self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        self.testcase_path_media_agent = self.media_agent_machine.join_path(drive_path_media_agent, self.id)

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.dedup_store_path = self.tcinputs.get("dedup_path")
            self.log.info("custom dedup path supplied : %s", self.dedup_store_path)
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
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("storage policy deleted")
        else:
            self.log.info("storage policy does not exist.")

        # here the storage pool is automatically created by gdsp and therefore has the same name as gdsp.
        if self.commcell.storage_policies.has_policy(self.gdsp_name):
            self.commcell.storage_policies.delete(self.gdsp_name)
            self.log.info("gdsp deleted")
        else:
            self.log.info("gdsp does not exist.")

        if self.commcell.storage_policies.has_policy(self.gdsp_name + '1'):
            self.commcell.storage_policies.delete(self.gdsp_name + '1')
            self.log.info("gdsp 1 deleted")
        else:
            self.log.info("gdsp 1 does not exist.")

        if self.commcell.storage_policies.has_policy(self.gdsp_name + '2'):
            self.commcell.storage_policies.delete(self.gdsp_name + '2')
            self.log.info("gdsp 2 deleted")
        else:
            self.log.info("gdsp 2 does not exist.")

        if self.commcell.storage_policies.has_policy(self.gdsp_name + '3'):
            self.commcell.storage_policies.delete(self.gdsp_name + '3')
            self.log.info("gdsp 3 deleted")
        else:
            self.log.info("gdsp 3 does not exist.")

        if self.commcell.storage_policies.has_policy(self.gdsp_name + '4'):
            self.commcell.storage_policies.delete(self.gdsp_name + '4')
            self.log.info("gdsp 4 deleted")
        else:
            self.log.info("gdsp 4 does not exist.")

        self.commcell.disk_libraries.refresh()

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
        # create dedupe store paths
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '0'):
            self.log.info("store path 0 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '0')
            self.log.info("store path 0 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '1'):
            self.log.info("store path 1 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '1')
            self.log.info("store path 1 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '2'):
            self.log.info("store path 2 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '2')
            self.log.info("store path 2 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '3'):
            self.log.info("store path 3 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '3')
            self.log.info("store path 3 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '4'):
            self.log.info("store path 4 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '4')
            self.log.info("store path 4 created")

        # create library if not provided
        self.library = self.mm_helper.configure_disk_library(
            self.library_name, self.media_agent, self.mount_path)
        self.library1 = self.mm_helper.configure_disk_library(
            self.library_name + '1', self.media_agent, self.mount_path + '1')
        self.library2 = self.mm_helper.configure_disk_library(
            self.library_name + '2', self.media_agent, self.mount_path + '2')
        self.library3 = self.mm_helper.configure_disk_library(
            self.library_name + '3', self.media_agent, self.mount_path + '3')
        self.library4 = self.mm_helper.configure_disk_library(
            self.library_name + '4', self.media_agent, self.mount_path + '4')

        # create gdsp if not provided
        self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
            global_storage_policy_name=self.gdsp_name,
            library_name=self.library_name,
            media_agent_name=self.media_agent,
            ddb_path=self.dedup_store_path + '0',
            ddb_media_agent=self.media_agent)
        self.gdsp1 = self.dedup_helper.configure_global_dedupe_storage_policy(
            global_storage_policy_name=self.gdsp_name + '1',
            library_name=self.library_name + '1',
            media_agent_name=self.media_agent,
            ddb_path=self.dedup_store_path + '1',
            ddb_media_agent=self.media_agent)
        self.gdsp2 = self.dedup_helper.configure_global_dedupe_storage_policy(
            global_storage_policy_name=self.gdsp_name + '2',
            library_name=self.library_name + '2',
            media_agent_name=self.media_agent,
            ddb_path=self.dedup_store_path + '2',
            ddb_media_agent=self.media_agent)
        self.gdsp3 = self.dedup_helper.configure_global_dedupe_storage_policy(
            global_storage_policy_name=self.gdsp_name + '3',
            library_name=self.library_name + '3',
            media_agent_name=self.media_agent,
            ddb_path=self.dedup_store_path + '3',
            ddb_media_agent=self.media_agent)
        self.gdsp4 = self.dedup_helper.configure_global_dedupe_storage_policy(
            global_storage_policy_name=self.gdsp_name + '4',
            library_name=self.library_name + '4',
            media_agent_name=self.media_agent,
            ddb_path=self.dedup_store_path + '4',
            ddb_media_agent=self.media_agent)

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

        # create secondary copy for storage policy
        self.copy1 = self.mm_helper.configure_secondary_copy(
            sec_copy_name=self.storage_policy_name + "_1",
            storage_policy_name=self.storage_policy_name,
            ma_name=self.media_agent,
            global_policy_name=self.gdsp1.storage_policy_name)
        self.copy2 = self.mm_helper.configure_secondary_copy(
            sec_copy_name=self.storage_policy_name + "_2",
            storage_policy_name=self.storage_policy_name,
            ma_name=self.media_agent,
            global_policy_name=self.gdsp2.storage_policy_name)
        self.copy3 = self.mm_helper.configure_secondary_copy(
            sec_copy_name=self.storage_policy_name + "_3",
            storage_policy_name=self.storage_policy_name,
            ma_name=self.media_agent,
            global_policy_name=self.gdsp3.storage_policy_name)
        self.copy4 = self.mm_helper.configure_secondary_copy(
            sec_copy_name=self.storage_policy_name + "_4",
            storage_policy_name=self.storage_policy_name,
            ma_name=self.media_agent,
            global_policy_name=self.gdsp4.storage_policy_name)

        # Remove Association with System Created AutoCopy Schedule
        for iterator in range(1, 5):
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name,
                                                    self.storage_policy_name + "_" + str(iterator))

        # add data to subclient content
        self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=0.1)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

        # set encryption to Blowfish 256 on client
        self.client.set_encryption_property("ON_CLIENT", "BlowFish", "256")

        # set enc on primary copy
        self.gdsp.get_copy("Primary_Global").set_encryption_properties(re_encryption=True,
                                                                       encryption_type="BlowFish",
                                                                       encryption_length=256)

        # setting reencryption on copy1 with GOST, 256

        self.gdsp1.get_copy("Primary_Global").set_encryption_properties(re_encryption=True, encryption_type="GOST",
                                                                        encryption_length=256)

        # setting store in plain text on copy2
        self.gdsp2.get_copy("Primary_Global").set_encryption_properties(plain_text=True)

        # setting store in plain text with network encryption SERPENT, 128 on copy3
        self.gdsp3.get_copy("Primary_Global").set_encryption_properties(plain_text=True, network_encryption=True,
                                                                        encryption_type="Serpent",
                                                                        encryption_length=128)

        # setting Preserve enc mode as in source on copy4
        self.gdsp4.get_copy("Primary_Global").set_encryption_properties(preserve=True)

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        self.log.info("starting %s backup job...", job_type)
        job = self.subclient.backup(backup_level=job_type)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

    def run_aux_copy(self, use_scalable_resource_allocation=True):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:
                use_scalable_resource_allocation    boolean     enable/disable scalable resource allocation

        returns job id(int)
        """
        self.log.info("starting auxcopy job...")
        job = self.storage_policy.run_aux_copy(media_agent=self.media_agent,
                                               use_scale=use_scalable_resource_allocation)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run auxcopy job[Id: %s] with error: %s" % (job.job_id, job.delay_reason)
            )
        self.log.info("auxcopy job: %s completed successfully", job.job_id)
        return job.job_id

    def run_restore_job(self, copy_precedence):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:
                copy_precedence     int     copy precedence to be followed

        returns job id(int)
        """
        self.log.info("starting restore job...")
        job = self.subclient.restore_out_of_place(self.client.client_name,
                                                  self.restore_path,
                                                  [self.content_path],
                                                  copy_precedence=copy_precedence)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job[%s] with error: [%s]" % (job.job_id, job.delay_reason)
            )
        self.log.info("restore job: %s completed successfully", job.job_id)

        return job.job_id

    def get_mmconfig_for_infini_DDB(self):
        """
        checks whether infiniDDB parameter in mmconfig is set or not

        returns integer[0/1]
        """
        query = "select value from MMConfigs where name = 'MMS2_CONFIG_ENABLE_INFINI_STORE'"
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        config_value = int(self.csdb.fetch_one_row()[0])
        self.log.info("Result: %s", config_value)
        return config_value

    def verify_encryption_type(self, copy, encryption_type, encryption_length):
        """
        checks if the copy encryption and user specified encryption type match

            Args:
                copy            (instance)      copy object
                encryption_type        (str)           encryption type
                encryption_length         (int)           encryption length

        returns Boolean
        """
        enc_dict = {
            ("GOST", 256): 11,
            ("TwoFish", 128): 8,
            ("TwoFish", 256): 9,
            ("BlowFish", 128): 2,
            ("BlowFish", 256): 3,
            ("DES3", 192): 10,
            ("AES", 128): 4,
            ("AES", 256): 5,
            ("Serpent", 128): 6,
            ("Serpent", 256): 7,

        }
        flag = False
        copy_id = copy.get_copy_id()
        query = f"""select distinct encKeyType from archFileCopy
                    where archfileid  in (select id from archFile where filetype = 1)
                    and  archCopyId = {copy_id}"""
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)

        if len(self.csdb.rows) > 1:
            self.log.error("more than one enctype returned by query : %s", str(self.csdb.rows))
            raise Exception("more than one enctype returned..")

        enc_key_type = int(self.csdb.fetch_one_row()[0])
        self.log.info("enctype retrieved from CSDB : %d", enc_key_type)

        if enc_dict[(encryption_type, encryption_length)] == enc_key_type:
            flag = True
        else:
            self.log.error("expected enctype was : %d", enc_dict[(encryption_type, encryption_length)])

        return flag

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
                raise Exception(f"dedup not enabled on storage policy {self.storage_policy_name}")

            # run two full backups
            job1 = self.run_backup("Full")
            job2 = self.run_backup("Full")

            # check mmconfig for infiniDDB config value
            # run auxcopy accordingly
            if self.get_mmconfig_for_infini_DDB():
                self.log.info("InfiniDDB enabled.. running new aux")
                aux1 = self.run_aux_copy()
            else:
                self.log.info("InfiniDDB disabled.. running old aux")
                aux1 = self.run_aux_copy(use_scalable_resource_allocation=False)

            ##########################################################################
            self.log.info("Validations on COPY 3")

            # verify encryption settings from logs
            try:
                # validating network only encryption option on copy3
                self.log.info("CASE 1:  verify encryption key used network only encryption to decrypt on CVD  ")
                matched_line, matched_string = self.dedup_helper.parse_log(client=self.media_agent,
                                                                           log_file="CVD.log",
                                                                           regex='128-bit Serpent enc. key',
                                                                           jobid=aux1,
                                                                           single_file=False)
                if matched_line:
                    self.log.info("SUCCESS  Result :Pass for enc Key Type CVD validation of NetworkOnly option")
                else:
                    self.log.error("ERROR   Result:Fail")
                    # raise Exception("validating network only encryption option on copy3 via logs failed..")

                self.log.info(
                    "CASE 2:  verify encKeyfetch call used to decrypt on CVD when Network only option is enabled ")
                matched_line, matched_string = self.dedup_helper.parse_log(client=self.media_agent,
                                                                           log_file="CVD.log",
                                                                           regex='Retrieving encryption keys',
                                                                           jobid=aux1,
                                                                           single_file=False)
                if matched_line:
                    self.log.info("SUCCESS  Result :Pass for fetchKey validation in CVD of NetworkOnly option")
                else:
                    self.log.error("ERROR   Result:Fail")
                    # raise Exception("validating network only encryption option on copy3 via logs failed..")
            except Exception as exp:
                raise Exception(f"error while parsing logs : {str(exp)}")

            ##########################################################################
            # picking jobs on copy1 for recopy, updating enc options, running aux, running restore and log validation
            # and db validation for each copy below
            self.copy1.recopy_jobs(job1)
            self.copy1.recopy_jobs(job2)

            # update encryption on copy1 to store as plaintext
            self.gdsp1.get_copy("Primary_Global").set_encryption_properties(plain_text=True)

            # running aux copy
            aux2 = self.run_aux_copy()

            self.log.info("Validations on COPY 1")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy1, encryption_type="GOST", encryption_length=256):
                self.log.info("PASSED for Dedupe GOST Re-Encryption")
            else:
                self.log.error("FAILED for Dedupe GOST Re-Encryption")
                raise Exception("Enc type mismatch for copy 1..")

            ##########################################################################
            # picking jobs for recopy on copy2
            self.copy2.recopy_jobs(job1)
            self.copy2.recopy_jobs(job2)

            # Preserve enc mode as in source on copy2
            self.gdsp2.get_copy("Primary_Global").set_encryption_properties(preserve=True)

            # do logfile validation of enc option which should be PASSTHRU
            # as no encryption is enabled on copy2 but it will use blowfish from source
            # running aux copy
            aux3 = self.run_aux_copy()

            self.log.info("Validations on COPY 2")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy2, encryption_type="BlowFish", encryption_length=256):
                self.log.info("PASSED for PASSTHRU (BLOWFISH) Encryption")
            else:
                self.log.error("FAILED for PASSTHRU (BLOWFISH) Encryption")
                raise Exception("Enc type mismatch for copy 2..")

            ##########################################################################
            # picking jobs for recopy on copy3
            self.copy3.recopy_jobs(job1)
            self.copy3.recopy_jobs(job2)

            # setting reencryption on copy 3 to DES3 192
            self.gdsp3.get_copy("Primary_Global").set_encryption_properties(re_encryption=True, encryption_type="DES3",
                                                                            encryption_length=192)

            # running aux copy
            aux4 = self.run_aux_copy()

            self.log.info("Validations on COPY 3")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy3, encryption_type="DES3", encryption_length=192):
                self.log.info("PASSED for Re-enc (DES3-192) Encryption")
            else:
                self.log.error("FAILED for Re-enc (DES3-192) Encryption")
                raise Exception("Enc type mismatch for copy 3..")

            ##########################################################################
            # picking jobs for recopy on copy4
            self.copy4.recopy_jobs(job1)
            self.copy4.recopy_jobs(job2)

            # Store in plain text with N/W enc TWOFISH 256 on copy 4
            self.gdsp4.get_copy("Primary_Global").set_encryption_properties(plain_text=True, network_encryption=True,
                                                                            encryption_type="TwoFish",
                                                                            encryption_length=256)

            # running aux copy
            aux5 = self.run_aux_copy()

            self.log.info("Validations on COPY 4")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy4, encryption_type="BlowFish", encryption_length=256):
                self.log.info("PASSED for Network Only (Source: BLOWIFSH 256) Encryption")
            else:
                self.log.error("FAILED for Network Only (Source: BLOWIFSH 256) Encryption")
                raise Exception("Enc type mismatch for copy 4..")

            ##########################################################################
            # run restores from all copies
            for copy_iter in range(2, 6):
                self.run_restore_job(copy_precedence=copy_iter)
                self.log.info("restore job from copy %d completed successfully..", copy_iter - 1)

            # ********************************************************************************************************

            # picking jobs on copy for recopy once again, updating enc options,
            # running new aux(scalable resource allocation), running restore
            # and log validation and db validation for each copy below

            ##########################################################################
            # picking jobs on copy1 for recopy, updating enc options, running aux, running restore and log validation
            # and db validation for each copy below
            self.copy1.recopy_jobs(job1)
            self.copy1.recopy_jobs(job2)

            # update encryption on copy1 to preserve source encryption
            self.gdsp1.get_copy("Primary_Global").set_encryption_properties(preserve=True)

            # running aux copy
            aux2 = self.run_aux_copy()

            self.log.info("Validations on COPY 1")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy1, encryption_type="GOST", encryption_length=256):
                self.log.info("PASSED for PASSTHRU (Source: GOST 256) Encryption")
            else:
                self.log.error("FAILED for PASSTHRU (Source: GOST 256) Encryption")
                raise Exception("Enc type mismatch for copy 1..")

            ##########################################################################
            # picking jobs for recopy on copy2
            self.copy2.recopy_jobs(job1)
            self.copy2.recopy_jobs(job2)

            # enc option PASSTHRU with N/w encryption AES 128 on copy2
            self.gdsp2.get_copy("Primary_Global").set_encryption_properties(plain_text=True, network_encryption=True,
                                                                            encryption_type="AES",
                                                                            encryption_length=128)

            # validation of enc option PASSTHRU with N/w encryption AES 128
            # as no encryption is enabled on copy2 but it will use blowfish from source
            aux3 = self.run_aux_copy()

            self.log.info("Validations on COPY 2")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy2, encryption_type="BlowFish", encryption_length=256):
                self.log.info("PASSED for Network Only (Source: BLOWIFSH 256) Encryption")
            else:
                self.log.error("FAILED for Network Only (Source: BLOWIFSH 256) Encryption")
                raise Exception("Enc type mismatch for copy 2..")

            ##########################################################################
            # picking jobs for recopy on copy3
            self.copy3.recopy_jobs(job1)
            self.copy3.recopy_jobs(job2)

            # setting reencryption on copy 3 to Serpent 128
            self.gdsp3.get_copy("Primary_Global").set_encryption_properties(re_encryption=True,
                                                                            encryption_type="Serpent",
                                                                            encryption_length=128)

            # running aux copy
            aux4 = self.run_aux_copy()

            self.log.info("Validations on COPY 3")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            # due to deduplication the chunks written by the first auxcopy job with DES3 192 encryption will be
            # referenced by the new auxcopy job(ArchFiles are the same), therefore though we have re-encrypt set here
            # to Serpent 128, since we are referring the old chunks the enctype will be 10 i.e, DES3 192
            if self.verify_encryption_type(copy=self.copy3, encryption_type="DES3", encryption_length=192):
                self.log.info("PASSED for Re-enc (DES3-192) Encryption")
            else:
                self.log.error("FAILED for Re-enc (DES3-192) Encryption")
                raise Exception("Enc type mismatch for copy 3..")

            ##########################################################################
            # picking jobs for recopy on copy4
            self.copy4.recopy_jobs(job1)
            self.copy4.recopy_jobs(job2)

            # Store in plain text on copy 4
            self.gdsp4.get_copy("Primary_Global").set_encryption_properties(plain_text=True)

            # running aux copy
            aux5 = self.run_aux_copy()

            self.log.info("Validations on COPY 4")

            self.log.info("CASE 1:  verify encryption type per copy from AFC table ")
            if self.verify_encryption_type(copy=self.copy4, encryption_type="BlowFish", encryption_length=256):
                self.log.info("PASSED for Network Only (Source: BLOWIFSH 256) Encryption")
            else:
                self.log.error("FAILED for Network Only (Source: BLOWIFSH 256) Encryption")
                raise Exception("Enc type mismatch for copy 4..")

            ##########################################################################
            # run restores from all copies
            for copy_iter in range(2, 6):
                self.run_restore_job(copy_precedence=copy_iter)
                self.log.info("restore job from copy %d completed successfully..", copy_iter - 1)

            ##########################################################################
            self.log.info("All Validations Completed.. Testcase executed successfully..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Test Case [%s]. Starting the cleanup.", self.status)
        try:
            self.deallocate_resources()
        except Exception as exe:
            self.log.warning("Cleanup Failed with error, Might need to cleanup manually: %s", exe)
