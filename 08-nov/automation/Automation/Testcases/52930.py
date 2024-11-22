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
    """Class for executing Basic acceptance Test of Vmware Full Snap backup and Restore test case
    without metadata collection"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Differential Snap Backup, Backup Copy and Restore Cases"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:

            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self,
                                     advance_options={
                                         'create_backup_copy_immediately': True,
                                         'backup_copy_type': 'USING_LATEST_CYLE'},
                                     msg='Differential Snap Backup and Backup copy',
                                     backup_type='DIFFERENTIAL',
                                     backup_method='SNAP')
            self.tc_utils.run_guest_file_restore(self,
                                                 browse_from_snap=True)
            self.tc_utils.run_disk_restore(self,
                                           browse_from_snap=True)
            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      browse_from_snap=True
                                                      )
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=True)
            self.tc_utils.run_guest_file_restore(self,
                                                 browse_from_snap=False,
                                                 browse_from_backup_copy=True)
            self.tc_utils.run_disk_restore(self,
                                           browse_from_snap=False,
                                           browse_from_backup_copy=True)
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=False,
                                                      unconditional_overwrite=True,
                                                      browse_from_snap=False,
                                                      browse_from_backup_copy=True
                                                      )
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=True)

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
