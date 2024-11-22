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

import time
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware Full Snap backup, backup copy and Agent less restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Agent less restore from Snap"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            VirtualServerUtils.set_inputs(self.tcinputs, backup_options)
            auto_subclient.backup(backup_options)

            VirtualServerUtils.decorative_log("Restore from Snap")
            try:
                VirtualServerUtils.decorative_log("Agentless file restore from Snap")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_from_snap = True
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.agentless_file_restore(file_restore_options)
            except Exception as exp:
                self.log.error("sleeping 12 minutes for cleanup of mounted snaps")
                time.sleep(720)
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            VirtualServerUtils.decorative_log("Restores from backup copy")

            try:
                VirtualServerUtils.decorative_log("Agentless file restore from backup copy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                auto_subclient.agentless_file_restore(file_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)


        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
                pass
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
