# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix AHV STREAMING CBT validation and " \
                    "Restore Cases using Windows proxy and Unix MA"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.webconsole = None
        self.report = None
        self.test_individual_failure_message = None

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            auto_subclient.validate_inputs("windows", "unix")

            log.info("Set CBT status on the subclient")
            value = auto_subclient.subclient.cbtvalue
            if not value:
                auto_subclient.subclient.cbtvalue = 1

            try:
                log.info(
                    "-" * 25 + " Full Backup " + "-" * 25)

                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_method = "REGULAR"
                backup_options.backup_type = "FULL"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            self.log.info(
                "-" * 25 + " CBT validation " + "-" * 25)
            auto_subclient.verify_cbt_backup("FULL", "Streaming")

            try:
                log.info(
                    "-" * 25 + " 1st Incremental Backup " + "-" * 25)

                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_method = "REGULAR"
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            self.log.info(
                "-" * 25 + " CBT validation " + "-" * 25)
            auto_subclient.verify_cbt_backup("INCREMENTAL", "Streaming")

            try:
                log.info(
                    "-" * 25 + " 2nd Incremental Backup " + "-" * 25)

                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_method = "REGULAR"
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            self.log.info(
                "-" * 25 + " CBT validation " + "-" * 25)
            auto_subclient.verify_cbt_backup("INCREMENTAL", "Streaming")

            log.info("---------------------Restores------------------------")

            try:
                log.info(
                    "-" * 15 + " FULL VM out of Place restores from Streaming " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
