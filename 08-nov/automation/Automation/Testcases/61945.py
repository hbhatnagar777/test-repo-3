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

    vsasnap_template_v2_disk_attach()   -- Template to Perform Snap backup, backup copy and disk
                                           attach Restore opertaions for VSA V2 client

    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Disk restores from Snap using Parent.
        4. Attach disk restores from Snap using Parent.
        5. Disk restores from Tape using Parent.
        6. Attach disk restores from Tape using Parent.
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMWARE Full Snap backup
    and disk attach Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Automation : VSA V2 - Vmware Intellisnap test case for Disk attach Restore Cases for : {0}"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''
        self.tcinputs = {}


    def run(self):
        """Main function for test case execution"""

        try:
            self.name = self.name.format(self.tcinputs["snap_engine"])
            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self, advance_options={
                             'create_backup_copy_immediately': True,
                             'backup_copy_type': 'USING_LATEST_CYLE'},
                             backup_method='SNAP',
                             msg='v2 Full Snap Backup')
            try:
                self.tc_utils.run_disk_restore(self, overwrite=True, browse_from_snap=True, msg='Disk restores from Snap using Parent')
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)
            try:
                self.tc_utils.run_attach_disk_restore(self, overwrite=True, browse_from_snap=True, msg='Attach disk restores from Snap using Parent')
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)
            try:
                self.tc_utils.run_disk_restore(self, overwrite=True, browse_from_backupcopy=True, msg='Disk restores from Tape using Parent')
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)
            try:
                self.tc_utils.run_attach_disk_restore(self, overwrite=True, browse_from_backupcopy=True, msg='Attach disk restores from Tape using Parent')
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if not self.ind_status:
                    self.result_string = self.failure_msg
                    self.status = constants.FAILED
                else:
                    self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
