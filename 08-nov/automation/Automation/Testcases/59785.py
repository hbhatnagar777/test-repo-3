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
        self.name = "VSA Hyper-V Snap Synthetic Backup and Restore Cases for v2 indexing"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            _adv = {"create_backup_copy_immediately": True}
            self.tc_utils.run_backup(self, backup_type="SYNTHETIC_FULL",
                                     run_incr_before_synth=False,
                                     run_incremental_backup="BEFORE_SYNTH",
                                     backup_method="SNAP",
                                     collect_metadata=False,
                                     collect_metadata_for_bkpcopy=False,
                                     advance_options=_adv,
                                     msg='v2 Hyper-V Snap - Synthetic Backup')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            browse_from_snap=False,
                                            browse_from_backup_copy=True,
                                            unconditional_overwrite=True,
                                            restore_browse_ma=None,
                                            snap_proxy=None,
                                            msg='FULL VM out of place restore from parent ')

            self.log.info("%(boundary)s %(message)s %(boundary)s",
                          {'boundary': "-" * 25,
                           'message': "Restores from Backup Copy"})
            browse_ma, fbr_ma = None, None
            if "Browse_MA_for_backup_copy" in self.tcinputs:
                browse_ma = self.tcinputs["Browse_MA_for_backup_copy"]
            if "FBRMA" in self.tcinputs:
                fbr_ma = self.tcinputs["FBRMA"]

            self.tc_utils.run_guest_file_restore(self,
                                                 browse_from_snap=False,
                                                 fbr_ma=fbr_ma,
                                                 browse_from_backup_copy=True,
                                                 browse_ma=browse_ma,
                                                 child_level=True,
                                                 msg='Guest Files restores from Child')

            self.log.info("Sleeping for 12 min for snap un-mount")
            time.sleep(720)

            self.tc_utils.run_disk_restore(self,
                                           restore_browse_ma=None,
                                           snap_proxy=None,
                                           disk_browse_ma=None,
                                           browse_from_snap=False,
                                           browse_from_backup_copy=True,
                                           child_level=True,
                                           msg='disk restores from Child')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            restore_browse_ma=None,
                                            snap_proxy=None,
                                            power_on_after_restore=True,
                                            browse_from_snap=False,
                                            browse_from_backup_copy=True,
                                            unconditional_overwrite=True,
                                            child_level=True,
                                            msg='FULL VM out of Place restores from Child')
            if "Inplace" in self.tcinputs and self.tcinputs["Inplace"].lower() == 'true':
                self.tc_utils. \
                    run_virtual_machine_restore(self,
                                                in_place_overwrite=True,
                                                power_on_after_restore=True,
                                                browse_from_backup_copy=True,
                                                browse_from_snap=False,
                                                unconditional_overwrite=True,
                                                child_level=True,
                                                msg='FULL VM  In Place restores from Child')

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
