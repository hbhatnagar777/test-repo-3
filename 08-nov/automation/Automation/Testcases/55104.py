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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Full Backup and File level Restore for Special configuration"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Checking the Details of the VM")
            auto_subclient.validate_inputs("", "", "windows")
            special_vm_drive = auto_subclient.validate_special_vm()
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.advance_options["testdata_size"] = (25000, 35000)
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options, special_vm_drive=special_vm_drive)

            try:
                VirtualServerUtils.decorative_log("Guest file restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.guest_file_restore(file_restore_options, special_vm_drive=special_vm_drive)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options, special_vm_drive)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED