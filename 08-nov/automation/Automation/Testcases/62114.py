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

    run()           --  Run function of this test case

    verify_job()    --  Verifies file indexing, guest files browse, restore and backup afiles

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase

from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper

from Indexing.validation.vsa_features import VSAFeatures


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
        self.name = 'Indexing - VSA - File Indexing - Win VM - Win proxy'
        self.tcinputs = {
            'RestoreClient': None,
            'RestorePath': None,
            # 'ForceFull': None,
            # 'Debug': None
        }

        self.auto_subclient = None
        self.idx_vsa = None

    def setup(self):
        """Setup function of this test case"""

        auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
        auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
        self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

        self.idx_vsa = VSAFeatures(self.auto_subclient, self)

        if not self.idx_vsa.is_file_indexing_enabled():
            raise Exception('File indexing is not enabled, please enable on the subclient')

        self.idx_vsa.initialize_vms()

        self.idx_vsa.set_gf_restore_options(self.tcinputs.get('RestoreClient'), self.tcinputs.get('RestorePath'))

    def run(self):
        """Run function of this test case

            Steps:
                0) Create and edit testdata before every backup job
                1) Run FULL backup
                2) Verify if file indexing job ran
                3) Verify if RFC, file indexing afiles are created for all the VMs
                4) Verify guest files browse and restore results
                5) Run INC backup
                6) Repeat steps 2 to 4
                7) Run SFULL
                8) Repeat steps 2 to 4
                9) Run INC

        """
        try:

            self.log.info('********** Adding testdata files **********')
            self.idx_vsa.create_guest_files()

            if self.subclient.last_backup_time == 0 or self.tcinputs.get('ForceFull', False):
                self.log.info('***** This is a new subclient, running FULL backup *****')
                self.log.info('********** Running FULL backup **********')
                backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
                backup_options.backup_type = 'FULL'

                self.auto_subclient.backup(backup_options, skip_discovery=True)
                full_job = self.auto_subclient.backup_job
                self.verify_job(full_job)

            self.log.info('********** Running INCREMENTAL 1 backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'

            self.auto_subclient.backup(backup_options, skip_discovery=True)
            inc1_job = self.auto_subclient.backup_job
            self.verify_job(inc1_job)

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'SYNTHETIC_FULL'
            backup_options.incr_level = ''

            self.auto_subclient.backup(backup_options, skip_discovery=True)
            sfull1_job = self.auto_subclient.backup_job
            self.verify_job(sfull1_job)

            self.log.info('********** Editing testdata files **********')
            self.idx_vsa.edit_guest_files()

            self.log.info('********** Running INCREMENTAL 2 backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'

            self.auto_subclient.backup(backup_options, skip_discovery=True)
            inc2_job = self.auto_subclient.backup_job
            self.verify_job(inc2_job)

            self.log.info('********** Browse & Restore from previous cycle [%s] **********', inc1_job.job_id)
            self.idx_vsa.verify_gf_browse_restore({
                'job_id': inc1_job.job_id
            })

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if self.tcinputs.get('Debug', False):
                self.log.info(self.idx_vsa.vms)
                self.log.info(self.idx_vsa.all_jobs)

    def verify_job(self, job_obj):
        """Verifies file indexing, guest files browse, restore and backup afiles

            Args:
                job_obj         (obj)       --      The parent job object

            Raises:
                Exception on verification failure

        """

        self.log.info('Starting verification for job [%s]', job_obj.job_id)

        # Verify if file indexing job ran
        if job_obj.backup_level.lower() != 'synthetic full':
            self.idx_vsa.verify_file_indexing_job()
        else:
            self.log.info('***** Skipping file indexing check for Synthetic full job since it is inline *****')

        # Verify backup afiles
        self.idx_vsa.verify_vm_afiles(job_obj)

        # Record the guest files for all the VMs
        self.idx_vsa.record_guest_files(job_obj)

        # Verifies guest file browse and restore
        self.idx_vsa.verify_gf_browse_restore()