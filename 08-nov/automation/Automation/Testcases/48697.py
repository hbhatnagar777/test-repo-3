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
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
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
        \\%Music%
        \\%Pictures%
        \\%Videos%

         03. Create some test data under the well-known folders.

         04. Run incremental backup or full backup if this is first job for the subclient.

         05. Perform Migration Assistant (referred to as MA from here on) content validation if applicable.

         06. Perform addition and modification of test data under well-known folders.

         07. Run an Incremental Backup before synthetic full.

         08. Perform addition and modification of test data under well-known folders and AppData folder.

         09. Run an incremental backup.

         10. Perform both regular FS backup validation and MA validation.

         11. Perform a sync. restore of the backed up data to the destination client.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Migration Assistance For Laptop Clients - Basic Acceptance"
        self.show_to_user = True
        self.tcinputs = {
            "StoragePolicyName": None,
            "SourceClient": None,
            "SourceProfile": None,
            "DestinationClient": None,
            "DestinationProfile": None
        }

        self.storage_policy = None
        self.wait_time = None
        self.retain_days = None
        self.should_wait = None
        self.verify_dc = None
        self.ma_helper = None
        self.src_machine = None
        self.dst_client = None
        self.bset_name = None
        self.cleanup_run = None
        self.RETAIN_DAYS = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.ma_helper = MigrationAssistantHelper(self)
        self.ma_helper.populate_migration_assistant_inputs(self)

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize test case inputs
            self.log.info(self.__doc__)

            self.log.info("01. Create backupset as default backupset for this testcase if it doesn't exist.")
            self.bset_name = '_'.join(("backupset", str(self.id)))
            self.ma_helper.create_default_backupset(self.bset_name)

            self.log.info("02. Set following monikers as content for the default subclient of the default backupset "
                          r"\%Desktop%"
                          r"\%Documents%"
                          r"\%Music%"
                          r"\%Pictures%"
                          r"\%Videos%")

            self.subclient = self.backupset.subclients.get('default')
            self.ma_helper.update_subclient(self.storage_policy,
                                            ["\\%Desktop%", "\\%Music%", "\\%Pictures%", "\\%Videos%", "\\%Documents%"])

            self.log.info("03. Create some test data under the well-known folders.")
            suffix = "full_incr1"
            self.ma_helper.generate_test_data_for_ma(self.src_machine, suffix)

            self.log.info("04. Run incremental backup or full backup if this is the first job for subclient.")
            job_full_inc1 = self.ma_helper.run_backup_verify()[0]

            self.log.info("05. Perform both regular FS and MA content validation if applicable.")
            if job_full_inc1.backup_level.upper() == "FULL":
                self.ma_helper.ma_restore_verify(job_full_inc1, suffix, ma_validation_flag=True)
            else:
                self.ma_helper.ma_restore_verify(job_full_inc1, suffix, ma_validation_flag=False)

            self.log.info("06. Perform addition and modification of test data under well-known folders.")
            suffix = "incr2"
            self.ma_helper.generate_test_data_for_ma(self.src_machine, suffix, add_incr=True)

            self.log.info("07. Run an Incremental Backup before Synthetic Full.")
            self.ma_helper.run_backup(backup_level="Synthetic_full",
                                      incremental_backup=True, incremental_level="BEFORE_SYNTH")[0]

            self.log.info("08. Perform addition and modification of test data under well-known folders.")
            suffix = "incr3"
            self.ma_helper.generate_test_data_for_ma(self.src_machine, suffix, add_incr=True)

            self.log.info("10. Run an incremental backup.")
            job_inc3 = self.ma_helper.run_backup(backup_level="Incremental")

            self.log.info("11. Perform both regular FS backup validation and MA validation.")
            self.ma_helper.ma_restore_verify(job_inc3[0], suffix, ma_validation_flag=True)

            self.log.info("12. Perform a sync. restore of the backed up data to the destination client.")
            job_sync_restore1 = self.ma_helper.run_sync_restore(self.dst_client)

            if job_sync_restore1.summary['status'].upper() == "COMPLETED":
                self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
                self.status = constants.PASSED
            else:
                self.log.info("***TEST CASE FAILED***")
                self.status = constants.FAILED

            # DELETING TEST DATASET & BACKUPSET
            if self.cleanup_run:
                self.ma_helper.cleanup_run_for_ma()
            else:
                self.ma_helper.cleanup_run_for_ma(self.RETAIN_DAYS)

        except Exception as excp:
            error_message = "Failed with error: {}".format(str(excp))
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED
