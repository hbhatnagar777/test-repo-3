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
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of RHEV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.failure_msg = ''
        self.ind_status = True
        self.name = 'VSA RHEV Incr Backup and Restore Cases with Unix Proxy and Windows MA'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            auto_subclient.validate_inputs("linux", "windows")
            self.tc_utils.run_backup(self,
                                     backup_type='INCREMENTAL',
                                     msg='Streaming Incremental Backup')
            self.tc_utils.run_guest_file_restore(self)
            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True)
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=True)

        except Exception:
            pass

        finally:
            try:
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options)
                auto_subclient.post_restore_clean_up(self.tc_utils.vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
