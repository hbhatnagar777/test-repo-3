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
from AutomationUtils import constants
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA  backup
    and Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA AZURE V2 Full Streaming Backup and Restore"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONAZURE,
                                                          self.features_list.DATAPROTECTION)



    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self,
                                     backup_type="FULL",
                                     collect_metadata=False,
                                     msg='AZURE V2 STREAMING Full Backup')
            try:
                auto_subclient.post_backup_validation(validate_cbt=True, skip_snapshot_validation=False)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            # CHILD LEVEL RESTORES

            self.tc_utils.run_guest_file_restore(self,
                                                 child_level=True,
                                                 msg='GuestFile restore from CHILD level from STREAMING Backup')




            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      child_level=True,
                                                      msg='FULL VM out of Place restores from CHILD level from STREAMING backup')

        except Exception:
            pass

        finally:
            try:
                if auto_subclient and self.tc_utils.backup_options:
                    auto_subclient.cleanup_testdata(self.tc_utils.backup_options)
                    auto_subclient.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                         status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass

            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
