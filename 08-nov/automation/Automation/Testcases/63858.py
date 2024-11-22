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

    vsasnap_template_v2_disk_attach()   -- Template to Perform Snap backup, backup copy and revert
                                           Restore opertaions for VSA V2 client

    Steps:
        1. Snap Backup of VM coming from a particular NetApp array
        2. Backup copy of that VM.
        3. inplace revert restore from Snap using Parent.
        4. verify vm restore

"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMWARE Full Snap backup
    and revert Restore from NetApp nfs datastore - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Automation : Intellisnap VMWare Revert restore from NetApp NFS datastore : {0}"
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
                             'create_backup_copy_immediately': False,
                             'backup_copy_type': 'USING_LATEST_CYLE'},
                             backup_method='SNAP',
                             msg='v2 Full Snap Backup')
            try:
                self.tc_utils.run_virtual_machine_restore(self, in_place_overwrite=True,
                                                          browse_from_snap=True,
                                                          revert=True,
                                                          power_on_after_restore=True,
                                                          msg='inplace revert restore from Snap using Parent')
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
