# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Spool Copy basic case


Steps:
    1.  Clean previous run config if present
    2.  Create Library, non-dedupe SP, Backupset and Subclient if not exists
    3.  Set retention to 0 day, 0 cycle on primary (Spool copy)
    4.  Set retention to 1 day, 0 cycle on secondary copy
    5.  Run full backup J1
    6.  Move J1 timestamp to one day behind
    7.  Run incremental backup I1
    8.  Validation: J1 & I1 should not be aged
    9.  Run Auxcopy job A1
    10. Run Data aging DA1
    11. Validation: J1 & I1 should be aged
    12. Clean up on success run


TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


User should have the following permissions:
        [Execute Workflow] permission on [Execute Query] workflow


Sample Input:
"53971": {
    "ClientName": "Name of Client",
    "AgentName": "File System",
    "MediaAgentName": "Name of a MediaAgent",
    *** optional ***
    "dedupe_path": "LVM enabled path for Unix SecondaryCopyMediaAgent",
}


NOTE:
    1. LVM enabled folder must be supplied for Unix MA. Dedupe paths will be created inside this folder.
"""

from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    # Minimum free space required on the machine
    FREE_SPACE_REQUIRED = 25*1024

    def __init__(self):
        """ Initializes test case class object

            Properties to be initialized:
                name        (str)       --  name of this test case

                tcinputs    (dict)      --  test case inputs with input name as dict key
                                            and value as input type
        """
        super(TestCase, self).__init__()

        self.name = "Spool copy basic case"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

        self.ma_name = None

        self.client_machine = None
        self.ma_machine = None
        self.ma_drive = None

        self.content_path = None
        self.mount_path = None
        self.dedupe_path = None

        self.storage_pool_name = None

        self.backupset_name = None
        self.subclient_name = None
        self._subclient = None

        self.storage_policy_name = None
        self.storage_policy = None
        self.sec_copy_name = None
        self._primary_copy = None
        self._secondary_copy = None

        self.dedupe_copy_config = {
            'storage_policy': None,
            'copy_name': None,
            'library_name': None,
            'media_agent_name': None,
            'partition_path': None,
            'ddb_media_agent': None,
        }

        self.mm_helper = None
        self.dedupe_helper = None

    def setup(self):
        """Setup function of this test case"""

        self.ma_name = self.tcinputs["MediaAgentName"]

        self.client_machine = machine.Machine(self.client.client_name, self.commcell)
        self.ma_machine = machine.Machine(self.ma_machine, self.commcell)

        options_selector = OptionsSelector(self.commcell)
        client_drive = options_selector.get_drive(self.client_machine, self.FREE_SPACE_REQUIRED)
        self.ma_drive = options_selector.get_drive(self.ma_machine, self.FREE_SPACE_REQUIRED)

        self.content_path = self.client_machine.join_path(client_drive, f'test_{self.id}', 'Content')
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)

        self.mount_path = self.ma_machine.join_path(self.ma_drive, f'test_{self.id}', "MP(%s)")
        if not self.ma_machine.check_directory_exists(self.mount_path % 1):
            self.log.info("Creating mountpath directory [%s]", self.mount_path % 1)
            self.ma_machine.create_directory(self.mount_path % 1)
        if not self.ma_machine.check_directory_exists(self.mount_path % 2):
            self.log.info("Creating mountpath directory [%s]", self.mount_path % 2)
            self.ma_machine.create_directory(self.mount_path % 2)

        if 'unix' in self.ma_machine.os_info.lower():
            if 'dedupe_path' not in self.tcinputs:
                self.log.error('LVM enabled dedup path must be supplied for Unix MA')
                raise ValueError('LVM enabled dedup path must be supplied for Unix MA')

            self.dedupe_path = self.ma_machine.join_path(self.tcinputs["dedupe_path"], "DDB(%s)")
        else:
            self.dedupe_path = self.ma_machine.join_path(self.ma_drive, f'test_{self.id}', 'DDB(%s)')

        self.storage_pool_name = f"{self.id}_disk(%s)_ma({self.ma_name})"

        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'

        self.storage_policy_name = str(self.id) + '_SP'
        self.sec_copy_name = str(self.id) + "_SEC"

        self.dedupe_copy_config.update({
            # 'storage_policy': None,       # Instance of storage_policy object, Set during configure_resources phase
            'copy_name': self.sec_copy_name,
            # 'library_name': None,         # Retrieved from storage pool, Set during configure_resources phase
            'media_agent_name': self.ma_name,
            'partition_path': self.dedupe_path % 2,
            'ddb_media_agent': self.ma_name,
        })

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def configure_resources(self):
        """
        Configure resources required for running this case.
        """
        self.log.info("Creating Dedupe Disk Storage [%s] with Mount path [%s] and DDB path [%s]",
                      self.storage_pool_name % 1,
                      self.mount_path % 1,
                      self.dedupe_path % 1)
        self.mm_helper.configure_storage_pool(self.storage_pool_name % 1, self.mount_path % 1, self.ma_name,
                                              self.ma_name, self.dedupe_path % 1)
        self.log.info("Storage pool [%s] created successfully.", self.storage_pool_name % 1)

        self.log.info("Creating Disk Storage [%s] with Mount path [%s]", self.storage_pool_name % 2,self.mount_path % 2)
        _, lib = self.mm_helper.configure_storage_pool(self.storage_pool_name % 2, self.mount_path % 2, self.ma_name)
        self.log.info("Storage pool [%s] created successfully.", self.storage_pool_name % 2)
        self.dedupe_copy_config['library_name'] = lib.library_name

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
            self.storage_policy_name,
            storage_pool_name=self.storage_pool_name % 1,
            is_dedup_storage_pool=True
        )
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)
        self.dedupe_copy_config['storage_policy'] = self.storage_policy

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 1)
        self._subclient = self.mm_helper.configure_subclient(self.backupset_name,
                                                             self.subclient_name,
                                                             self.storage_policy_name,
                                                             self.content_path)
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_cleanup()
            self.configure_resources()

            # self._secondary_copy = self.mmhelper.configure_secondary_copy(self.sec_copy_name)
            self._secondary_copy = self.dedupe_helper.configure_dedupe_secondary_copy(**self.dedupe_copy_config)

            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.sec_copy_name)
            # update retention to 1 day, 0 cycle
            self.log.info("setting secondary copy retention: 1 day, 0 cycle")
            self._secondary_copy.copy_retention = (1, 0, 1)

            # update primary to spool copy
            self.log.info("setting primary copy retention to 0 day, 0 cycle (Spool copy)")
            self._primary_copy = self.storage_policy.get_copy('Primary')
            self._primary_copy.copy_retention = (0, 0, 0)

            # disable managed disk space
            self._primary_copy.copy_retention_managed_disk_space = False

            # Creating Content
            self.log.info("Creating content for subclient")
            self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 1)

            # Run FULL backup
            self.log.info("Running full backup...")
            job = self._subclient.backup("FULL")
            self.log.info("Backup job: " + str(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job.delay_reason))
            self.log.info("Backup job completed.")
            backup_job = job.job_id

            # Run Incr backup
            self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 1)
            self.log.info("Running incr backup...")
            incrjob = self._subclient.backup("incremental")
            self.log.info("Incremental job: " + str(incrjob.job_id))
            if not incrjob.wait_for_completion():
                raise Exception("Failed to run Incr backup with error: {0}".format(incrjob.delay_reason))
            self.log.info("Incremental Backup job completed.")
            incr_job = incrjob.job_id

            # run data aging
            da_job = self.commcell.run_data_aging('Primary', self.storage_policy_name)
            self.log.info("data aging job: " + str(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception("Failed to run data aging with error: {0}".format(da_job.delay_reason))
            self.log.info("Data aging job completed.")

            self.log.info("VALIDATION: backup job not yet aged")
            # validate backup
            self.log.info("Validating full backup...")
            retcode = self.mm_helper.validate_job_prune(backup_job, self._primary_copy.copy_id)
            if not retcode:
                self.log.info("Validation success")
            else:
                raise Exception("Backup job {0} is not expected to age".format(backup_job))
            # validate incr
            self.log.info("Validating incr backup...")
            retcode = self.mm_helper.validate_job_prune(incr_job, self._primary_copy.copy_id)
            if not retcode:
                self.log.info("Validation success")
            else:
                raise Exception("Incr job {0} is not expected to age".format(backup_job))

            # Run aux copy
            self.log.info("Running Auxcopy job...")
            aux_job = self.storage_policy.run_aux_copy(self.sec_copy_name, self.ma_name, False, 0)
            self.log.info("Auxcopy job: " + str(aux_job.job_id))
            if not aux_job.wait_for_completion():
                raise Exception("Failed to run Auxcopy with error: {0}".format(aux_job.delay_reason))

            # run data aging
            da_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                          storage_policy_name=self.storage_policy_name,
                                                          is_granular=True, include_all=False,
                                                          include_all_clients=True,
                                                          select_copies=True, prune_selected_copies=True)
            self.log.info("data aging job: " + str(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception("Failed to run data aging with error: {0}".format(da_job.delay_reason))
            self.log.info("Data aging job completed.")

            self.log.info("VALIDATION: backup, incr job should be aged")
            # validate backup
            self.log.info("Validating full backup...")
            retcode = self.mm_helper.validate_job_prune(backup_job, self._primary_copy.copy_id)
            if retcode:
                self.log.info("Validation success")
            else:
                raise Exception("Backup job {0} did not age".format(backup_job))
            # validate incr
            self.log.info("Validating incr backup...")
            retcode = self.mm_helper.validate_job_prune(incr_job, self._primary_copy.copy_id)
            if retcode:
                self.log.info("Validation success")
            else:
                raise Exception("Incr job {0} did not age".format(backup_job))

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def previous_run_cleanup(self):
        """delete previous run items"""
        self.log.info("********* previous run clean up **********")
        try:
            self.log.info("Deleting Content Path, if exists")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory exists")
                self.client_machine.remove_directory(self.content_path)
                self.log.info("existing content deleted")

            # Delete backup set
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting storage policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted storage policy: %s", self.storage_policy_name)

            # Delete storage pool
            self.log.info("Deleting storage pool: %s, if exists" % self.storage_pool_name % 1)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name % 1):
                self.commcell.storage_pools.delete(self.storage_pool_name % 1)
                self.log.info("Deleted storage pool: %s" % self.storage_pool_name % 1)

            # Delete storage pool
            self.log.info("Deleting storage pool: %s, if exists" % self.storage_pool_name % 2)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name % 2):
                self.commcell.storage_pools.delete(self.storage_pool_name % 2)
                self.log.info("Deleted storage pool: %s" % self.storage_pool_name % 2)
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def tear_down(self):
        """Tear down function of this test case"""
        # cleanup
        try:
            self.log.info("********* cleaning up ***********")
            self.previous_run_cleanup()
        except Exception as e:
            self.log.info("something went wrong while cleanup.")
            pass
