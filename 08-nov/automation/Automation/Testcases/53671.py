# Copyright Commvault Systems, Inc.
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
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Azure RM backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA AzureRM SYNTHETIC_FULL Backup and Restore Cases with CBT VAlidations"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        log = logger.get_log()

        try:
            log.info("Started executing %s testcase" % self.id)

            log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent,
                                                                  self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            log.info("Set CBT status on the subclient")
            value = auto_subclient.subclient.cbtvalue
            if not value:
                auto_subclient.subclient.cbtvalue = 1

            try:
                log.info(
                    "-" * 25 + " Backup " + "-" * 25)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "SYNTHETIC_FULL"
                backup_options.run_incremental_backup = "BEFORE_SYNTH"
                backup_options.advance_options["testdata_size"] = '150000'
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info("*" * 25 + " Perform CBT checks " + "*" * 25)
                auto_commcell.check_cbt_status(backup_options.backup_type, self.subclient)
                auto_subclient.create_ini_files()
                auto_subclient.get_changeid_from_metadata(backup_options.backup_type)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info(
                    "-" * 25 + " Files level restores " + "-" * 25)
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                if "FBRMA" in self.tcinputs:
                    fs_restore_options.fbr_ma = self.tcinputs["FBRMA"]
                if "Browse_MA" in self.tcinputs:
                    fs_restore_options.browse_ma = self.tcinputs["Browse_MA"]
                auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info(
                    "-" * 15 + " FULL VM out of Place restores" + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

                log.info("Azure Resources clean up")
                auto_subclient.post_restore_clean_up(vm_restore_options)


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
