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
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("VSA Amazon Tenant Account: Synthetic Full backup and Full VM restore from "
                     "snap and backup copy - post Synth Full(multi proxy, multi guest, "
                     "Windows MA)")
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONAMAZON,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self, msg='Synthfull backup',
                                     advance_options={"create_backup_copy_immediately": True},
                                     backup_method='SNAP',
                                     backup_type='SYNTHETIC_FULL')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            browse_from_snap=True,
                                            power_on_after_restore=True,
                                            unconditional_overwrite=True,
                                            msg='Full VM out of place restore from snap')

            self.tc_utils.run_attach_disk_restore(self,
                                                  browse_from_snap=True,
                                                  msg='Attach Disk restore from parent - Snap')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            browse_from_snap=False,
                                            browse_from_backup_copy=True,
                                            msg='Full VM out of place restore from backup copy')

            self.tc_utils.run_attach_disk_restore(self,
                                                  browse_from_snap=False,
                                                  browse_from_backup_copy=True,
                                                  msg='Attach Disk restore from parent - Backup Copy')

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   True, self.tcinputs.get('DeleteRestoredVM', True))
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED