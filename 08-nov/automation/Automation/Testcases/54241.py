# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.migration_assistant_helper import MigrationAssistantHelper


class TestCase(CVTestCase):
    """Class for executing
        Migration Assistance For Laptop Clients - Basic Acceptance
        This test will perform the following steps.

         01. Create backupset as default backupset for this
        testcase if it doesn't already exist.

         02. Define the following list monikers as content for the default subclient of the default backupset.
        \\%Desktop%
        \\%Documents%
        \\%MigfrationAssistant%
         03. Run incremental backup or full backup if this is first job for the subclient.

         05. Perform Migration Assistant (referred to as MA from here on) content validation if applicable.

         06. Perform addition and modification of test data under well-known folders.

         07. Add filter as \\%MigfrationAssistant%

         08. Perform addition and modification of test data under well-known folders and AppData folder.

         09. Run an incremental backup after synthfull and check whether MA files are not backedup.

         10. Perform incremental backup and check whether no MA files area gain backedup.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MigrationAssistant Moniker backup validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.DATAPROTECTION
        self.runid = None
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None

    def setup(self):
        """Setup function of this test case"""
        client_name = self.tcinputs['ClientName']
        self.ma_helper = MigrationAssistantHelper.create_MigrationAssistantHelper_object(self, machine_name=client_name,
                                                                                         commcell_object=self._commcell)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        self.helper = FSHelper(self)
        #FSHelper.populate_tc_inputs(self, mandatory=False)
        #MigrationAssistantHelper.populate_migration_assistant_inputs(self)
        try:
            # Initialize test case inputs
            self.log.info("Started executing %s testcase", str(self.id))
            machine = Machine(client_name, self._commcell)

            from AutomationUtils.config import get_config
            client = get_config().Laptop.UserCentricClient.ClientName
            client = client_name if not client else client
            subclient_obj  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)

            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")

            if machine.os_info in 'UNIX':
                subclient_content = ['/%Documents%', '/%Desktop%', '/%MigrationAssistant%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%"]
            else:
                subclient_content = [r'\%Documents%', r'\%Desktop%', r'\%MigrationAssistant%']
                filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%"]

            subclient_obj.content = subclient_content
            subclient_obj.filter_content = filter_content

            log.info('Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")

            job_obj._initialize_job_properties()
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed".format(job_obj.job_id))

            log.info('Job triggered for new subclient content case')

            log.info('Run a synthfull job')
            job_obj = subclient_obj.backup("Synthetic_full")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("SynthFUll Backup job {0} completed.".format(job_obj.job_id))

            log.info('Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed.".format(job_obj.job_id))

            log.info('Verify whether backup had all Migration assistant files backedup or not')

            result, diff = self.ma_helper.perform_ma_validation(backup_level="Incremental")
            if not result:
                raise Exception("there are some MA files awhich are not backedup : {0}".format(diff))

            log.info("Verify whether migration assistant files are not backedup again in the next incremental")

            log.info('Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job completed.")
            log.info("Verify whether  Migration assistant files are not backedup again")

            if job_obj.num_of_files_transferred > 0:
                raise Exception("Job backedup MA files again")

            log.info("job didnt backup MA files again")

            log.info("Add Migration Assistant in filter and check whether MA files are not backedup")

            if self.slash_format in '/':
                subclient_content = ['/%Documents%', '/%Desktop%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%", "/%MigrationAssistant%"]
            else:
                subclient_content = [r'\%Documents%', r'\%Desktop%']
                filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%", r'\%MigrationAssistant%', "*.drivedownload"]

            subclient_obj.content = subclient_content
            subclient_obj.filter_content = filter_content

            log.info('Run a synthfull job')

            job_obj = subclient_obj.backup("Synthetic_full")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job completed.")

            log.info('Run an incremental job which should not backup MA files')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job completed.")

            if job_obj.num_of_files_transferred > 0:
                raise Exception("Job backedup MA files again")

            log.info("job didnt backup MA files again")

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
