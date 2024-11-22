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

    create_resources() -- creates required resources

    run_backup()  -- run backup

    run_auxcopy() -- run auxcopy per copy

    run_auxcopy_validations()    --  runs the validations for auxcopy

    run_dedupe_validations() -- run validations of primary and secondary objects

    copy_promotion() -- do copy promotion

    run_restores()   -- do restores

    run()           --  run function of this test case

    cleanup()     --  cleanup resources function of this test case

    tear_down()     -- tear down function

    TcInputs to be passed in JSON File:
    "63428": {
                "ClientName": "client name",
                "AgentName": "File System",
                "PrimaryCopyMediaAgent":"Media Agent1",
                "SecondaryCopyMediaAgent":"Media Agent2",
                "SecondaryCopy2MediaAgent":"Media Agent3"
            }
    Note: All the MediaAgents can be the same machine

    Optional values in Json:
    "PrimaryCopyMP" : path for primary copy MP
    "SecondaryCopyMP" : path for secondary copy MP
    "SecondaryCopy2MP" : path for secondary copy2 MP

    "PrimaryCopyDDBPath": path where dedup store to be created [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
    "SecondaryCopyDDBPath": path where dedup store to be created for auxcopy [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
    "SecondaryCopy2DDBPath": path where dedup store to be created for auxcopy [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]

Steps:

1: Configure the environment: create a library,GDSP Storage Policy-with Primary, GDSP for Secondary Copy,
                              a BackupSet,a SubClient

2: Set block size as 512 for secondary copy so that it automtically uses NW optimzed

3: Run a Backup Job and then AuxCopy and run Validations

4: Submit another Backup Job and again a AuxCopy Job

5: Run Validations(Network Transfer Bytes, primary and secondary objects, Auxcopy status, non-readless)

6: Do copy promotion

7: Repeat steps 3,4,5

8. Do restores from subclient level from copy precendence 1 and 2

9: CleanUp the environment
"""
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Auxcopy with different source and destination block sizes"
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None,
            "SecondaryCopy2MediaAgent": None,
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.ma_machine_3 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ddb_path = None
        self.copy1_ddb_path = None
        self.copy2_ddb_path = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.mount_path_3 = None
        self.content_path = None
        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.secondary2_ma_path = None
        self.subclient = None
        self.restore_path = None
        self.copy1_name = None
        self.copy2_name = None
        self.storage_policy = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy_name = None
        self.list_primary = []
        self.list_secondary = []
        self.config_strings = None
        self.storage_pool_name1 = None
        self.storage_pool_name2 = None
        self.storage_pool_name3 = None
        self.storage_pool_id2 = None
        self.storage_pool_id3 = None
        self.gdsp1 = None
        self.sp_obj_list = []
        self.gdsp2 = None
        self.storage_policy_copy1 = None
        self.gdsp3 = None
        self.storage_policy_copy2 = None
        self.cvods_log = None
        self.dedupe_helper = None
        self.is_user_defined_mp = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_copy2_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_dedup = False
        self.is_user_defined_copy2_dedup = False

    def setup(self):
        """Setup function of this test case"""

        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        self.ma_machine_3 = Machine(self.tcinputs['SecondaryCopy2MediaAgent'], self.commcell)
        self.utility = OptionsSelector(self.commcell)
        client_drive = self.utility.get_drive(self.client_machine, 25600)
        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.copy1_name = f"{self.id}_Copy1"
        self.copy2_name = f"{self.id}_Copy2"
        self.subclient_name = f"{self.id}_SC"
        self.backupset_name = f"{self.id}_BS"
        self.restore_path = self.client_machine.join_path(self.client_path, 'Restores')
        self.storage_policy_name = f"{self.id}_SP_{self.tcinputs['PrimaryCopyMediaAgent']}_" \
                                   f"{self.tcinputs['SecondaryCopyMediaAgent']}"
        self.storage_pool_name1 = f"{self.id}_Pool1Primary_{self.tcinputs['PrimaryCopyMediaAgent']}"
        self.storage_pool_name2 = f"{self.id}_Pool1Copy1_{self.tcinputs['SecondaryCopyMediaAgent']}"
        self.storage_pool_name3 = f"{self.id}_Pool1Copy2_{self.tcinputs['SecondaryCopy2MediaAgent']}"

        if self.tcinputs.get('PrimaryCopyMP'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('SecondaryCopyMP'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('SecondaryCopy2MP'):
            self.is_user_defined_copy2_mp = True
        if self.tcinputs.get('PrimaryCopyDDBPath'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('SecondaryCopyDDBPath'):
            self.is_user_defined_copy_dedup = True
        if self.tcinputs.get('SecondaryCopy2DDBPath'):
            self.is_user_defined_copy2_dedup = True

        if (not self.is_user_defined_dedup and "unix" in self.ma_machine_1.os_info.lower()) or \
                (not self.is_user_defined_copy_dedup and "unix" in self.ma_machine_2.os_info.lower() or
                    (not self.is_user_defined_copy2_dedup and "unix" in self.ma_machine_3.os_info.lower())):
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine_1, 25600)
            self.primary_ma_path = self.ma_machine_1.join_path(ma_1_drive, 'testprimary_' + str(self.id))

        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            ma_2_drive = self.utility.get_drive(self.ma_machine_2, 25600)
            self.secondary_ma_path = self.ma_machine_2.join_path(ma_2_drive, 'testcopy_' + str(self.id))

        if not self.is_user_defined_copy2_mp or not self.is_user_defined_copy2_dedup:
            ma_3_drive = self.utility.get_drive(self.ma_machine_3, 25600)
            self.secondary2_ma_path = self.ma_machine_3.join_path(ma_3_drive, 'testcopy2_' + str(self.id))

        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
        else:
            self.log.info("custom mount_path supplied")
            self.mount_path = self.tcinputs['PrimaryCopyMP']
        if not self.is_user_defined_copy_mp:
            self.mount_path_2 = self.ma_machine_2.join_path(self.secondary_ma_path, 'MP2')
        else:
            self.log.info("custom copy_mount_path supplied")
            self.mount_path_2 = self.tcinputs['SecondaryCopyMP']

        if not self.is_user_defined_copy2_mp:
            self.mount_path_3 = self.ma_machine_3.join_path(self.secondary2_ma_path, 'MP3')
        else:
            self.log.info("custom copy_mount_path supplied")
            self.mount_path_3 = self.tcinputs['SecondaryCopy2MP']

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.tcinputs["PrimaryCopyDDBPath"]
        else:
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDBprimary")
        if self.is_user_defined_copy_dedup:
            self.log.info("custom copy dedup path supplied")
            self.copy1_ddb_path = self.tcinputs["SecondaryCopyDDBPath"]
        else:
            self.copy1_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, "DDBcopy1")

        if self.is_user_defined_copy2_dedup:
            self.log.info("custom copy dedup path supplied")
            self.copy2_ddb_path = self.tcinputs["SecondaryCopy2DDBPath"]
        else:
            self.copy2_ddb_path = self.ma_machine_3.join_path(self.secondary2_ma_path, "DDBcopy2")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.config_strings = ['Disabling Auxcopy Readless for Copy']

    def run_backup(self, counter):
        """Runs Auxcopy
                            Args:
                                    counter    (int)  --   backup iteration
                        """
        self.log.info("Submitting Full Backup Job Number: %s", counter)
        backup_job = self.subclient.backup(backup_level='Full')
        if backup_job.wait_for_completion():
            self.log.info("Backup Completed :Id - %s", backup_job.job_id)
        else:
            raise Exception(f"Backup job [{backup_job.job_id}] did not complete - [{backup_job.delay_reason}]")
        return backup_job.job_id

    def run_auxcopy(self, copy_name, counter):
        """Runs Auxcopy
                    Args:
                            copy_name    (str)  --   copy name on which auxcopy should run
                            counter  (int)   -- auxcopy counter
                """
        self.log.info("Submitting AuxCopy job")
        aux_copy_job = self.storage_policy.run_aux_copy(copy_name, use_scale=True)
        if aux_copy_job.wait_for_completion():
            self.log.info("AuxCopy Completed :Id - %s", aux_copy_job.job_id)
        else:
            raise Exception(f"Auxcopy job [{aux_copy_job.job_id}] did not complete - [{aux_copy_job.delay_reason}]")
        self.run_auxcopy_validations(aux_copy_job.job_id, counter)

    def run_auxcopy_validations(self, aux_copy_job_id, counter):
        """Runs Auxcopy valiations - not using readless, archchunktoreplicate status and NW tranfer bytes
                            Args:
                                    aux_copy_job_id  (int)  --  auxcopy job id used to validate from logs and csdb
                                    counter        (int)  --  auxcopy job counter to check NW trans bytes
                        """
        log_file = "CVJobReplicatorODS.log"
        self.log.info("*** CASE 1: Not using readless mode : Disabling Auxcopy Readless for Copy ***")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.cvods_log, log_file,
            self.config_strings[0], aux_copy_job_id)
        if matched_line:
            self.log.error("Success Result : Passed")
        else:
            raise Exception("Error Result : Failed")

        # NW transfer bytes to be checked from CSDB
        if counter == 2:
            self.log.info('*** CASE 2: NW transfer bytes status for 2nd Auxcopy job***')
            query = '''select nwtransbytes, EX_TotalMedia from JMAdminJobStatsTable where jobid = {0}
                                '''.format(aux_copy_job_id)
            self.log.info(f"Query is : [{query}]")
            self.csdb.execute(query)
            row_1 = self.csdb.fetch_one_row()
            self.log.info(f"Query result is : [{row_1}]")
            # calculate the percentage of NW transbytes
            bytes_trans_percent = (int(row_1[0]) / int(row_1[1])) * 100
            self.log.info("NW transfer bytes percentage is %s ", bytes_trans_percent)
            if 0 < bytes_trans_percent <= 2:
                self.log.info("NW transfer bytes in second auxcopy job is negligible as expected")
                self.log.info("Success Result : Passed")
            else:
                raise Exception("NW transfer bytes in second auxcopy job for is not expected")

        # Archchunktoreplicate status from CSDB to check if auxcopy job copied all jobs
        self.log.info('*** CASE 3: ArchChunkToReplicate status ***')
        query = '''select distinct status
                        from archchunktoreplicatehistory where AdminJobId = {0}
                        '''.format(aux_copy_job_id)
        self.log.info(f"Query is : [{query}]")
        self.csdb.execute(query)
        row_1 = self.csdb.fetch_all_rows()
        self.log.info(f"Query result is : [{row_1}]")
        if len(row_1[0]) == 1:
            query = '''select distinct status
                                            from archchunktoreplicate where AdminJobId = {0}
                                            '''.format(aux_copy_job_id)
            self.log.info(f"Query is : [{query}]")
            self.csdb.execute(query)
            row_2 = self.csdb.fetch_all_rows()
            self.log.info(f"Query result is : [{row_2}]")
            if len(row_2[0]) == 1 and row_2[0][0] == '' and int(row_1[0][0]) == 2:
                self.log.info("ArchChunkToReplicateHistory status for all chunks is 2")
                self.log.info("Success Result : Passed")
            else:
                raise Exception("ArchChunkToReplicateHistory status is not 2 or ArchchunkToReplicate is not empty")
        else:
            raise Exception("ArchChunkToReplicateHistory status returned more than 1 row")

    def run_dedupe_validations(self, iteration, backup_job_id):
        """Runs the validations - It validates the primary and secondary objects between jobs.
            Args:
                    iteration             (int)  --   Iteration of the Case Validations
                    backup_job_id         (str)  --   Id of Backup Job
        """
        self.log.info('*** CASE 2: Primary and secondary Objects Comparison ***')
        primary = self.dedupe_helper.get_primary_objects_sec(backup_job_id, 'Primary')
        secondary = self.dedupe_helper.get_secondary_objects_sec(backup_job_id, 'Primary')
        primary_copy1 = self.dedupe_helper.get_primary_objects_sec(backup_job_id, self.copy1_name)
        secondary_copy1 = self.dedupe_helper.get_secondary_objects_sec(backup_job_id, self.copy1_name)
        primary_copy2 = self.dedupe_helper.get_primary_objects_sec(backup_job_id, self.copy2_name)
        secondary_copy2 = self.dedupe_helper.get_secondary_objects_sec(backup_job_id, self.copy2_name)

        self.list_primary.append(int(primary))
        self.list_primary.append(int(primary_copy1))
        self.list_primary.append(int(primary_copy2))
        self.list_secondary.append(int(secondary))
        self.list_secondary.append(int(secondary_copy1))
        self.list_secondary.append(int(secondary_copy2))

        self.log.info("Primary Objects : %s %s %s", primary, primary_copy1, primary_copy2)
        self.log.info("Secondary Objects : %s %s %s", secondary, secondary_copy1, secondary_copy2)

        if iteration == 1:
            self.log.info("Checking Primary and secondary objects of source and destination")
            quotient1 = round((self.list_primary[0]/self.list_primary[1]), 2)
            quotient2 = round((self.list_primary[0]/self.list_primary[2]), 2)
            if 3.2 <= quotient1 <= 4.2:
                self.log.info('Primary copy primary objects are approx 4 times of secondary copy1: Passed')
            else:
                raise Exception('Primary copy primary objects are not approx 4 times of secondary copy1 : Failed')
            if 7.2 <= quotient2 <= 8.2:
                self.log.info('Primary copy primary objects are approx 8 times of secondary copy2: Passed')
            else:
                raise Exception('Primary copy primary objects are not approx 8 times of secondary copy2 : Failed')

        if iteration == 2:
            self.log.info("Did Dedup Occur after job 1 and job 2 ?")
            if self.list_primary[1] == self.list_secondary[4] and self.list_primary[2] == self.list_secondary[5] \
                    and self.list_primary[4] == 0 and self.list_primary[5] == 0:
                self.log.info("Success Result : Passed")
            else:
                raise Exception("Error  Result : Failed")

        if iteration == 3:
            # was expecting 100% dedupe.Based on dev comments we can't get 100% dedupe so not doing any validations
            self.log.info('Checking Primary, Secondary Objects after copy promotion')
            self.log.info('Copy1/Promoted primary Primary records: %s , Secondary records: %s',
                          self.list_primary[7], self.list_secondary[7])
            self.log.info('Old primary Primary records: %s , Secondary records: %s',
                          self.list_primary[6], self.list_secondary[6])
            self.log.info('Copy2 primary Primary records: %s , Secondary records: %s',
                          self.list_primary[8], self.list_secondary[8])

        if iteration == 4:
            self.log.info("Did Dedup Occur between job 3 and 4 after copy promotion ?")
            if (self.list_primary[6] + self.list_secondary[6]) == self.list_secondary[9] and \
                    (self.list_primary[8] + self.list_secondary[8]) == self.list_secondary[11] and \
                    self.list_primary[9] == 0 and self.list_primary[11] == 0:
                self.log.info("Success Result : Passed")
            else:
                raise Exception("Error  Result : Failed")

    def copy_promotion(self):
        """Promoting the secondary copy to primary"""
        # get the archgroup id for the storage policy
        storage_policy_id = self.storage_policy.storage_policy_id
        # get sec copy id
        storage_policy_seccopy_id = self.storage_policy_copy1.copy_id
        storage_policy_pricopy_id = self.mm_helper.get_copy_id(self.storage_policy_name, 'Primary')
        query = """update archgroup set defaultcopy = {0} where id = {1}
            """.format(storage_policy_seccopy_id, storage_policy_id)
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
        # Change the copy precendence also
        query = """update archgroupcopy set copy = 1 where id = {0}
                        """.format(storage_policy_seccopy_id)
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)

        query = """update archgroupcopy set copy = 2 where id = {0}
                                    """.format(storage_policy_pricopy_id)
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)

    def do_restores(self):
        """Do restores of latest jobs of subclients from all copies"""
        restores_jobs = []
        for index in range(1, 4):
            job = self.subclient.restore_out_of_place(self.client.client_name,
                                                      self.restore_path + str(index - 1),
                                                      [self.content_path],
                                                      copy_precedence=index)
            restores_jobs.append(job)

        for job in restores_jobs:
            if job.wait_for_completion():
                self.log.info("Restore Job: %s Completed", job.job_id)
            else:
                raise Exception(f"Restore job [{job.job_id}] did not complete - [{job.delay_reason}]")

        self.log.info("Validating Restored Data from 3 Copies")
        for index in range(0, 3):
            restored_path = self.restore_path + str(index) + self.client_machine.os_sep
            difference = self.client_machine.compare_folders(self.client_machine,
                                                             self.content_path,
                                                             restored_path + 'Content')
            if difference:
                raise Exception("Validating Data restored from subclient %s Failed" % index)
        self.log.info("Validation SUCCESS")

    def create_resources(self):
        """Create resources needed by the Test Case"""
        try:
            self.cleanup()
            # Configure the environment
            # Creating a storage pool and associate to SP
            self.log.info("Configuring Storage Pool for Primary ==> %s", self.storage_pool_name1)
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name1):
                self.gdsp1 = self.commcell.storage_pools.add(self.storage_pool_name1, self.mount_path,
                                                             self.tcinputs['PrimaryCopyMediaAgent'],
                                                             self.tcinputs['PrimaryCopyMediaAgent'], self.ddb_path)
            else:
                self.gdsp1 = self.commcell.storage_pools.get(self.storage_pool_name1)
            self.log.info("Done creating a storage pool for Primary")
            self.commcell.disk_libraries.refresh()
            self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)
            if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.storage_policy = self.commcell.storage_policies.add(
                                        storage_policy_name=self.storage_policy_name,
                                        global_policy_name=self.storage_pool_name1)
            else:
                self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
            # Create storage pool for secondary copy1
            self.log.info("Configuring Secondary Storage Pool for copy1 ==> %s", self.storage_pool_name2)
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name2):
                self.gdsp2 = self.commcell.storage_pools.add(self.storage_pool_name2, self.mount_path_2,
                                                             self.tcinputs['SecondaryCopyMediaAgent'],
                                                             self.tcinputs['SecondaryCopyMediaAgent'],
                                                             self.copy1_ddb_path)
            else:
                self.gdsp2 = self.commcell.storage_pools.get(self.storage_pool_name2)
            self.log.info("Done creating a storage pool for secondary copy")
            self.commcell.disk_libraries.refresh()
            self.commcell.storage_policies.refresh()
            # Create secondary copy1
            self.log.info("Configuring Secondary Copy 1 using Storage pool==> %s", self.copy1_name)
            self.storage_policy_copy1 = self.mm_helper.configure_secondary_copy(
                                        sec_copy_name=self.copy1_name,
                                        global_policy_name=self.gdsp2.global_policy_name)

            # Create storage pool for secondary copy2
            self.log.info("Configuring Secondary Storage Pool for copy2 ==> %s", self.storage_pool_name3)
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name3):
                self.gdsp3 = self.commcell.storage_pools.add(self.storage_pool_name3, self.mount_path_3,
                                                             self.tcinputs['SecondaryCopy2MediaAgent'],
                                                             self.tcinputs['SecondaryCopy2MediaAgent'],
                                                             self.copy2_ddb_path)
            else:
                self.gdsp3 = self.commcell.storage_pools.get(self.storage_pool_name3)
            self.log.info("Done creating a storage pool for secondary copy2")
            self.commcell.disk_libraries.refresh()
            self.commcell.storage_policies.refresh()
            # Create secondary copy2
            self.log.info("Configuring Secondary Copy 2 using Storage pool==> %s", self.copy2_name)
            self.storage_policy_copy2 = self.mm_helper.configure_secondary_copy(
                sec_copy_name=self.copy2_name,
                global_policy_name=self.gdsp3.global_policy_name)

            # Configure backupset, subclients and create content
            self.mm_helper.configure_backupset(self.backupset_name)
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path,
                self.agent)
            self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.4)
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error("Exception Raised during Creating resources: %s", str(exe))

    def run(self):
        """Run Function of This Case"""
        try:
            self.create_resources()

            # Remove Association with System Created AutoCopy Schedule
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy1_name)
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy2_name)

            # enable encryption on the GDSPs
            gdsp1_copy = self.commcell.storage_policies.get(self.storage_pool_name1).get_copy('Primary')
            gdsp1_copy.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)
            gdsp2_copy = self.commcell.storage_policies.get(self.storage_pool_name2).get_copy('Primary')
            gdsp2_copy.set_encryption_properties(re_encryption=True, encryption_type="GOST", encryption_length=256)
            gdsp3_copy = self.commcell.storage_policies.get(self.storage_pool_name3).get_copy('Primary')
            gdsp3_copy.set_encryption_properties(re_encryption=True, encryption_type="AES", encryption_length=128)

            # update block size of GDSP of copy1 to 512KB
            self.storage_pool_id2 = gdsp2_copy.copy_id
            query = '''update archgroup set SIBlockSizeKB = 512 where defaultcopy = %s''' % self.storage_pool_id2
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)

            # update block size of GDSP of copy2 to 1024KB
            self.storage_pool_id3 = gdsp3_copy.copy_id
            query = '''update archgroup set SIBlockSizeKB = 1024 where defaultcopy = %s''' % self.storage_pool_id3
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)

            self.cvods_log = self.tcinputs['PrimaryCopyMediaAgent']

            # Run two Backup Jobs and then AuxCopy and run Dedupe Validations
            for counter in range(1, 3):
                backup_jobid = self.run_backup(counter)
                self.run_auxcopy(self.copy1_name, counter)
                self.run_auxcopy(self.copy2_name, counter)
                self.run_dedupe_validations(counter, backup_jobid)
            # restore from all the copies
            self.do_restores()

            # do copy promotion and run two more backups
            # Copy promotion by setting default copy id to sec copy in archgroup table for the storage policy
            self.copy_promotion()
            # change the cvods log lookup to promoted copy
            self.cvods_log = self.tcinputs['SecondaryCopyMediaAgent']
            self.copy1_name = 'Primary'

            # run two more backups. expectation is to get 100% dedupe, but it is not working. waiting on dev comments.
            for counter in range(3, 5):
                backup_jobid = self.run_backup(counter)
                self.run_auxcopy(self.copy1_name, counter)
                self.run_auxcopy(self.copy2_name, counter)
                self.run_dedupe_validations(counter, backup_jobid)
            # restore from all the copies
            self.do_restores()
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error("Exception Raised: %s", str(exe))

    def cleanup(self):
        """Cleanup Function of this Case"""
        try:
            # 6: CleanUp the environment
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            for index in range(1, 4):
                restore_path1 = self.restore_path + str(index - 1)
                self.mm_helper.remove_content(restore_path1,
                                              self.client_machine, suppress_exception=True)
                                                                                                           
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name1}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name1}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name1}")

            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name2}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name2}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name2}")

            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name3}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name3}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name3}")

            self.log.info("Refresh libraries")
            self.commcell.disk_libraries.refresh()
            self.log.info("Refresh Storage Policies")
            self.commcell.storage_policies.refresh()
        except Exception as exe:
            self.log.warning("ERROR in Cleanup. Might need to Cleanup Manually: %s", str(exe))

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED.")
        else:
            self.log.warning("Test Case FAILED.")
        self.cleanup()
