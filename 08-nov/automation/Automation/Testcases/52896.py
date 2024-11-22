# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Oracle vm backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA OracleVM Incremental Backup and Restore Cases for v2"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONORACLEVM,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self, backup_type='INCREMENTAL',
                                     msg='v2 Streaming Incremental Backup')
            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            unconditional_overwrite=True,
                                            msg='FULL VM out of place restore from parent ')
            self.tc_utils.run_guest_file_restore(self,
                                                 child_level=True,
                                                 msg='Guest Files restores from Child')
            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            child_level=True,
                                            msg='FULL VM out of Place restores from Child')
        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
