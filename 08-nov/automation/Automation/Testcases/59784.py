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
        self.name = "VSA Hyper-V DIFFERENTIAL Snap Backup and Restore Cases for v2 indexing"
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
            self.tc_utils.run_backup(self, backup_type="DIFFERENTIAL",
                                     backup_method="SNAP",
                                     collect_metadata=False,
                                     collect_metadata_for_bkpcopy=False,
                                     advance_options=_adv,
                                     msg='v2 Hyper-V Snap DIFFERENTIAL Backup')

            if self.tcinputs.get('check_cbt', True):
                auto_subclient.post_backup_validation(validate_cbt=True, skip_snapshot_validation=True)
            restore_browse_ma, snap_proxy = None, None
            if "restore_browse_ma" in self.tcinputs:
                restore_browse_ma = self.tcinputs["restore_browse_ma"]
            if "snap_proxy" in self.tcinputs:
                snap_proxy = self.tcinputs["snap_proxy"]

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            browse_from_snap=True,
                                            unconditional_overwrite=True,
                                            restore_browse_ma=restore_browse_ma,
                                            snap_proxy=snap_proxy,
                                            msg='FULL VM out of place restore from parent ')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            restore_browse_ma=None,
                                            snap_proxy=None,
                                            power_on_after_restore=True,
                                            browse_from_snap=False,
                                            browse_from_backup_copy=True,
                                            unconditional_overwrite=True,
                                            child_level=False,
                                            msg='FULL VM out of Place restore from backup copy parent level')

            browse_ma, fbr_ma = None, None
            if "Browse_MA" in self.tcinputs:
                browse_ma = self.tcinputs["Browse_MA"]
            if "FBRMA" in self.tcinputs:
                fbr_ma = self.tcinputs["FBRMA"]

            self.tc_utils.run_guest_file_restore(self,
                                                 browse_from_snap=True,
                                                 browse_ma=browse_ma,
                                                 fbr_ma=fbr_ma,
                                                 child_level=True,
                                                 msg='Guest Files restores from Child')
            disk_browse_ma, snap_proxy = None, None
            if "disk_browse_ma" in self.tcinputs:
                disk_browse_ma = self.tcinputs["disk_browse_ma"]
            if "snap_proxy" in self.tcinputs:
                snap_proxy = self.tcinputs["snap_proxy"]
            self.tc_utils.run_disk_restore(self,
                                           browse_from_snap=True,
                                           disk_browse_ma=disk_browse_ma,
                                           snap_proxy=snap_proxy,
                                           child_level=True,
                                           msg='disk restores from Child')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            browse_from_snap=True,
                                            unconditional_overwrite=True,
                                            snap_proxy=snap_proxy,
                                            restore_browse_ma=restore_browse_ma,
                                            child_level=True,
                                            msg='FULL VM out of Place restores from Child')

            if "Inplace" in self.tcinputs and self.tcinputs["Inplace"].lower() == 'true':

                self.tc_utils. \
                    run_virtual_machine_restore(self,
                                                in_place_overwrite=True,
                                                power_on_after_restore=True,
                                                browse_from_snap=True,
                                                unconditional_overwrite=True,
                                                snap_proxy=snap_proxy,
                                                child_level=True,
                                                msg='FULL VM  In Place restores from Child')

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