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
        self.name = "VSA GCP  FULL Snap Backup and Restore Cases for v2 indexing - Child"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONGCCLOUD,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:

            _ = self.tc_utils.initialize(self)
            _adv = {"create_backup_copy_immediately": True}
          
            
            self.tc_utils.run_backup(self, backup_type="FULL",
                                                      backup_method="SNAP",
                                                      advance_options=_adv,
                                                      msg='v2 GCP Snap Full Backup')

            self.tc_utils.sub_client_object.post_backup_validation(validate_cbt=False, skip_snapshot_validation=True)

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            browse_from_snap=True,
                                            unconditional_overwrite=True,
                                            browse_ma=self.tcinputs.get("restore_browse_ma"),
                                            child_level=True,
                                            msg='CHILD: Full VM Out-of-place restore from SNAP')
            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            browse_ma=None,
                                            snap_proxy=None,
                                            power_on_after_restore=True,
                                            browse_from_snap=False,
                                            browse_from_backup_copy=True,
                                            unconditional_overwrite=True,
                                            child_level=True,
                                            msg='CHILD: Full VM Out-of-place restore from BACKUP COPY')

            self.tc_utils.run_guest_file_restore(self,
                                              browse_from_snap=False,
                                              fbr_ma=self.tcinputs.get("fbr_ma"),
                                              browse_from_backup_copy=True,
                                              browse_ma=self.tcinputs.get("restore_browse_ma"),
                                              child_level=True,
                                              msg='CHILD: Guest Files restores from Child')

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