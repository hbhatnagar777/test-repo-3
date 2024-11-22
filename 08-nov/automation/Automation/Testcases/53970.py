# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
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

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Data aging basic case"
        self.tcinputs = {
            "MediaAgentName": None,
            "MountPath": None,
            "ContentPath": None,
            "SqlSaPassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))

            self._log.info(self.name)
            self.library_name = str(self.id) + "_lib"
            self.storage_policy_name = str(self.id) + "_SP"
            self.backupset_name = str(self.id) + "_BS"
            self.subclient_name = str(self.id) + "_SC"
            # initialize MMHelper class
            mmhelper = MMHelper(self)
            try:
                mmhelper.cleanup()
            except Exception as e:
                self._log.info("error while cleanup - ignoring")
                pass

            (self.library,
             self.storage_policy,
             self._backupset,
             self._subclient) = mmhelper.setup_environment()

            # update retention to 1 day, 0 cycle
            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.copy_retention = (1, 0, 1)
            self.copy.copy_retention_managed_disk_space = False

            # Run FULL backup
            self._log.info("--------- Day 1 -----------")
            self._log.info("Running full backup...")
            job = self._subclient.backup("FULL")
            self._log.info("Backup job: " + str(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(job.delay_reason)
                )
            self._log.info("Backup job completed.")
            backup_job = job.job_id

            # Run the script to move backup to 1 day
            mmhelper.move_job_start_time(backup_job, 1)

            self._log.info("--------- Day 2 -----------")
            # Run Incr backup
            self._log.info("Running incr backup...")
            incrjob = self._subclient.backup("incremental")
            self._log.info("Incremental job: " + str(incrjob.job_id))
            if not incrjob.wait_for_completion():
                raise Exception(
                    "Failed to run Incr backup with error: {0}".format(incrjob.delay_reason)
                )
            self._log.info("Incremental Backup job completed.")
            incr_job = incrjob.job_id

            # run data aging
            da_job = self.commcell.run_data_aging('Primary', self.storage_policy_name)
            self._log.info("data aging job: " + str(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging with error: {0}".format(da_job.delay_reason)
                )
            self._log.info("Data aging job completed.")

            # validate
            self._log.info("VALIDATION: backup job not yet aged")
            retcode = mmhelper.validate_job_prune(backup_job, self.copy.copy_id)
            if not retcode:
                self._log.info("Validation success")
            else:
                raise Exception(
                    "Backup job {0} is not expected to age".format(backup_job)
                )

            # Run script to move job time to 1 day
            mmhelper.move_job_start_time(backup_job, 1)
            mmhelper.move_job_start_time(incr_job, 1)
            self._log.info("--------- Day 3 -----------")
            # run data aging
            da_job = self.commcell.run_data_aging('Primary', self.storage_policy_name)
            self._log.info("data aging job: " + str(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging with error: {0}".format(da_job.delay_reason)
                )
            self._log.info("Data aging job completed.")

            # validate
            self._log.info("VALIDATION: backup job should be aged")
            retcode = mmhelper.validate_job_prune(backup_job, self.copy.copy_id)
            if retcode:
                self._log.info("Validation success")
            else:
                raise Exception(
                    "Backup job {0} did not age".format(backup_job)
                )

            # cleanup
            try:
                self._log.info("********* cleaning up ***********")
                mmhelper.cleanup()
            except Exception as e:
                self._log.info("something went wrong while cleanup.")
                pass

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        pass
