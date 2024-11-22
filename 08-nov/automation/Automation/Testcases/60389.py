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
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils import VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA  backup
    and Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA AZURE V2 Full Snap Backup and Backup copy and Restores"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONAZURE,
                                                          self.features_list.DATAPROTECTION)



    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            _adv = {"create_backup_copy_immediately": True}
            self.tc_utils.run_backup(self,
                                     backup_type="FULL",
                                     backup_method="SNAP",
                                     collect_metadata=False,
                                     collect_metadata_for_bkpcopy=False,
                                     advance_options=_adv,
                                     msg='AZURE V2 Snap Full Backup')
            try:
                auto_subclient.post_backup_validation(validate_cbt=True, skip_snapshot_validation=False)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            # CHILD LEVEL RESTORES


            self.tc_utils.run_guest_file_restore(self,
                                                 browse_from_snap=True,
                                                 child_level=True,
                                                 msg='GuestFile restore from CHILD level from SNAP Backup')



            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      browse_from_snap=True,
                                                      unconditional_overwrite=True,
                                                      child_level=True,
                                                      msg='FULL VM out of Place restores from CHILD level from SNAP backup')




            self.tc_utils.run_guest_file_restore(self,
                                                 browse_from_snap=False,
                                                 browse_from_backup_copy=True,
                                                 child_level=True,
                                                 msg='GuestFile restore from CHILD level from BACKUPCOPY')



            self.tc_utils.run_virtual_machine_restore(self,
                                                      browse_from_snap=False,
                                                      browse_from_backup_copy=True,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      child_level=True,
                                                      msg='FULL VM out of Place restores from CHILD level from BACKUPCOPY')


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