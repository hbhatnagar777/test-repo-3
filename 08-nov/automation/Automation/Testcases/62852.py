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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)
from Server.Network.networkhelper import NetworkHelper
from FileSystem.FSUtils.fshelper import FSHelper


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
        self.name = "TEST_CASE_NAME"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self._network = None
        self.dedupehelper = None
        self.mmhelper = None
        self.helper = None
        self.storage_policy_name = None
        self.primary_lib_name = None
        self.mountpath = None
        self.partition_path = None
        self.ma_machine = None
        self.client_machine = None
        self.backupset_name = None
        self.subclient_name = None
        self.test_path = None
        self.slash_format = None

    def setup(self):
        """Setup function of this test case"""
        self._network = NetworkHelper(self)
        self.helper = FSHelper(self)
        FSHelper.populate_tc_inputs(self, mandatory=False)
        self.primary_lib_name = "Automated_Lib_{}".format(self.id)
        self.storage_policy_name = "Automated_SP_{}".format(self.id)
        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.ma_machine = Machine(self.tcinputs["MediaAgentName"], self.commcell)
        options_selector = OptionsSelector(self.commcell)
        timestamp_suffix = options_selector.get_custom_str()
        ma_drive = options_selector.get_drive(self.ma_machine, size=40 * 1024)
        self.mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')
        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                        'DDB_%s' % timestamp_suffix)
        self.backupset_name = "backupset_" + self.id
        self.subclient_name = "subclient_" + self.id

    def cleanup(self):
        # Delete backupset
        self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("Deleted BackupSet: %s", self.backupset_name)

        time.sleep(60)
        # Delete Storage Policy
        self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

        # Delete Storage Policy
        self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

        # Delete Library
        self.log.info("Deleting primary copy library: %s if exists", self.primary_lib_name)
        if self.commcell.disk_libraries.has_library(self.primary_lib_name):
            self.commcell.disk_libraries.delete(self.primary_lib_name)
            self.log.info("Deleted library: %s", self.primary_lib_name)

    def clear_test_data(self):
        # Delete Test Data
        self.log.info("Deleting Test Data if exists")
        self.client_machine.remove_directory(self.test_path)
        self.log.info("Test Data cleared")

    def create_storage_policy(self):
        # Create library for primary copy
        primary_lib_obj = self.mmhelper.configure_disk_library(self.primary_lib_name,
                                                               self.tcinputs['MediaAgentName'], self.mountpath)

        # Create storage policy
        sp_obj = self.mmhelper.configure_storage_policy(self.storage_policy_name, primary_lib_obj,
                                                        self.tcinputs['MediaAgentName'])

        # Set retention of 0-day & 1-cycle on primary copy
        self.log.info("Setting Retention: 0-days and 1-cycle on Primary Copy")
        sp_primary_obj = sp_obj.get_copy("Primary")
        retention = (0, 1, -1)
        sp_primary_obj.copy_retention = retention

        return sp_obj, sp_primary_obj

    def setup_backupset_subclient(self):
        # Create BackupSet
        self.helper.create_backupset(self.backupset_name, delete=True)

        # Create Subclient
        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy_name, allow_multiple_readers=True,
                                     content=[self.test_path], delete=True)

    def add_data(self, cycle):
        path = self.client_machine.join_path(self.test_path, "Incr" + str(cycle))
        self.client_machine.create_directory(path, force_create=True)
        self.client_machine.generate_test_data(file_path=path, files=1, file_size=5,
                                               zero_size_file=False)
        self.log.info("Data generated.")

    def run(self):
        """Run function of this test case"""
        try:
            if self.client_machine.check_directory_exists(self.test_path):
                self.clear_test_data()

            sp_obj, sp_primary_obj = self.create_storage_policy()

            base_path = self.client_machine.join_path(self.test_path, "Full")
            self.client_machine.generate_test_data(file_path=base_path, files=10, file_size=5,
                                                   dirs=1, zero_size_file=False)
            self.setup_backupset_subclient()

            backup_jobs = []
            last_synthfull_job = None

            # Run 3 cycles of backups -> Full, Incr, SynthFull
            for i in range(1, 4):
                self.log.info("Starting Cycle {}".format(i))
                if i == 1:
                    job = self.helper.run_backup(backup_level="Full", wait_to_complete=True)[0]
                    backup_jobs.append(job.job_id)
                    self.log.info("Full Backup ended.")
                self.add_data(i)
                job = self.helper.run_backup(backup_level="Incremental", wait_to_complete=True)[0]
                backup_jobs.append(job.job_id)
                self.log.info("Incremental Backup ended, starting Synthetic Full Backup")
                last_synthfull_job = self.helper.run_backup(backup_level="Synthetic_full", wait_to_complete=True)[0]
                self.log.info("Synthetic Full Backup has ended.")
                self.log.info("Cycle {} has ended".format(i))

            self.log.info("Jobs that should be pruned: {}".format(backup_jobs[:-1]))
            self.log.info("Running Data aging...")
            da_job = self.commcell.run_data_aging('Primary', sp_obj.storage_policy_name)
            self._log.info("data aging job: {0}".format(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging with error: {0}".format(da_job.delay_reason)
                )
            self._log.info("Data aging job completed. wait for 10 min")
            time.sleep(600)
            count = 0
            self.log.info("All Jobs to verify %s" % backup_jobs)

            for job in backup_jobs:
                self.log.info("Jobs to verify %s" % job)
                retcode = self.mmhelper.validate_job_prune(job, sp_primary_obj.copy_id)
                if retcode and count <= 2:
                    self.log.info("Job {} pruned successfully".format(job))
                elif not retcode and count <= 2:
                    self.log.info("Job {} was not pruned, but should have been pruned".format(job))
                    raise Exception("Pruning did not happen for job id {0}".format(job))
                elif retcode and count == 3:
                    self.log.info("Job {} was pruned, but should not have been pruned".format(job))
                    raise Exception("Pruning did happen for job id {0}, but should not have happened".format(job))
                elif not retcode and count == 3:
                    self.log.info("Job {} was not pruned as expected".format(job))
                count += 1

            self.log.info("All Job Pruning Validation succeeded.")

            tmp_path = ""
            if self.applicable_os == "WINDOWS":
                tmp_path = "C:\\TempPath"
            else:
                tmp_path = "root/Documents/temppath"
            self.helper.run_restore_verify(slash_format=self.slash_format,
                                           data_path=self.test_path,
                                           tmp_path=tmp_path,
                                           data_path_leaf="Data",
                                           job=last_synthfull_job)
            self.log.info("Test Case Succeeded.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.clear_test_data()
        self.cleanup()