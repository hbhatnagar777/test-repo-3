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
    """Class for executing Basic acceptance Test of XEN backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "XEN Full Backup disk filtering"
        self.product = self.products_list.VIRTUALIZATIONXEN
        self.feature = self.features_list.DATAPROTECTION
        self.status_ind = True
        self.failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("Validating Disk Filtering disks")
                auto_subclient.validate_disk_filtering()
            except Exception as exp:
                self.status_ind = False
                self.failure_message += str(exp)

            try:
                VirtualServerUtils.decorative_log("Out of place full vm restore")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                VirtualServerUtils.set_inputs(self.tcinputs, vm_restore_options)
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.status_ind = False
                self.failure_message += str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.status_ind:
                self.result_string = self.failure_message
                self.status = constants.FAILED
