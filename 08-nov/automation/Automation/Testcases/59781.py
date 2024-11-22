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
from AutomationUtils import constants
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA  backup
    and Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Hyper-V differential Backup and Restore Cases for v2 indexing"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self,
                                     backup_type="SYNTHETIC_FULL",
                                     run_incr_before_synth=False,
                                     run_incremental_backup="BEFORE_SYNTH",
                                     collect_metadata=False,
                                     msg='v2 Streaming synthetic Backup Hyper-V')

            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=False,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      msg='FULL VM out of place restore from parent ')

            browse_ma, fbr_ma = None, None
            if "FBRMA" in self.tcinputs:
                fbr_ma = self.tcinputs["FBRMA"]
            if "Browse_MA" in self.tcinputs:
                browse_ma = self.tcinputs["Browse_MA"]

            self.tc_utils.run_guest_file_restore(self,
                                                 browse_ma=browse_ma,
                                                 fbr_ma=fbr_ma,
                                                 child_level=True,
                                                 msg='Guest Files restores from Child')
            self.tc_utils.run_disk_restore(self, child_level=True,
                                           msg='disk restores from Child')

            self.tc_utils.\
                run_virtual_machine_restore(self,
                                            in_place_overwrite=False,
                                            power_on_after_restore=True,
                                            unconditional_overwrite=True,
                                            child_level=True,
                                            msg='FULL VM out of Place restores from Child')

        except Exception as err:
            self.log.error(err)
            self.result_string = err
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.set_content_details()
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
