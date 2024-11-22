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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of RHEV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA RHEV Incremental Backup and Restore Cases using Windows Proxy and Unix Media Agent"
        self.product = self.products_list.VIRTUALIZATIONRHEV
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = backup_options = None
            self.log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            auto_subclient.validate_inputs("windows", "linux")

            VirtualServerUtils.decorative_log(" Incremental Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("Files restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                if "browse_ma" in self.tcinputs:
                    file_restore_options.browse_ma = self.tcinputs["browse_ma"]
                if "fbr_ma" in self.tcinputs:
                    file_restore_options.fbr_ma = self.tcinputs["fbr_ma"]
                auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM in Place restores")
                vm_restore_options.in_place_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
