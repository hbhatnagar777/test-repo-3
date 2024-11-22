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
    """Class for executing Basic acceptance Test of VMware Synthfull backup and Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Synthful Backup and Restore Cases for v2 Indexing"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            if self.tcinputs.get('del_disk_delete', None):
                try:
                    self.tc_utils.sub_client_obj.disk_cleanup_before_backup()
                except Exception as ex:
                    self.ind_status = False
                    self.failure_msg = str(ex)
                    self.log.exception('Failing during disk cleanup before backup {}'. format(self.failure_msg))
            self.tc_utils.run_backup(self,
                                     backup_type='SYNTHETIC_FULL',
                                     msg='Streaming Synthetic Full Backup')

            if self.tcinputs.get('parallel_runs', False):
                self.tc_utils.run_all_restores_in_parallel(self,
                                                           restore_types=['disk_restore', 'attach_disk_restore',
                                                                          'virtual_machine_restore'],
                                                           power_on_after_restore=True,
                                                           unconditional_overwrite=True
                                                           )
                self.tc_utils.run_all_restores_in_parallel(self,
                                                           child_level=True
                                                           )
            else:
                self.tc_utils. \
                    run_virtual_machine_restore(self,
                                                power_on_after_restore=True,
                                                unconditional_overwrite=True,
                                                msg='FULL VM out of place restore from parent ')
                self.tc_utils.run_disk_restore(self, msg='Disk restores from Parent')
                self.tc_utils.run_attach_disk_restore(self, msg='Attach disk restores from Parent')

                self.tc_utils.run_guest_file_restore(self,
                                                     child_level=True,
                                                     msg='Guest Files restores from Child')
                self.tc_utils.run_disk_restore(self, child_level=True,
                                               msg='disk restores from Child')
                self.tc_utils.run_attach_disk_restore(self,
                                                      child_level=True,
                                                      msg='Attach disk restores from Child')
                self.tc_utils. \
                    run_virtual_machine_restore(self,
                                                child_level=True,
                                                msg='FULL VM out of Place restores from Child')

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