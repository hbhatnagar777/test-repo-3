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
from VirtualServer.VSAUtils import VsaTestCaseUtils, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and cross Vcenter Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'AHV- Full Snap/backup copy and Cross Cluster Restore'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONNUTANIX,
                                                          self.features_list.DATAPROTECTION,
                                                          tcinputs={'DestinationClient': None})
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            if not VirtualServerUtils.cross_client_restore_pre_validation(self):
                raise Exception("Source and destination Vcenters are Same")
            self.tc_utils.run_backup(self,
                                     advance_options={
                                         'create_backup_copy_immediately': True,
                                         'backup_copy_type': 'USING_LATEST_CYLE'},
                                     backup_method='SNAP')
            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      in_place_overwrite=False,
                                                      unconditional_overwrite=True,
                                                      browse_from_snap=False,
                                                      browse_from_backup_copy=True
                                                      )
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
