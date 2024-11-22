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

import random
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA VMWARE Incremental Backup and Restore Cases'
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
                                     backup_type='INCREMENTAL',
                                     msg='Streaming Incremental Backup')
            if self.tcinputs.get('parallel_runs', False):
                self.tc_utils.run_all_restores_in_parallel(self,
                                                           power_on_after_restore=True,
                                                           unconditional_overwrite=True,
                                                           disk_option=random.choice(
                                                               ['Original',
                                                                'Thick Lazy Zero',
                                                                'Thin',
                                                                'Thick Eager Zero'])
                                                           )
            else:
                self.tc_utils.run_guest_file_restore(self)
                self.tc_utils.run_disk_restore(self)
                self.tc_utils.run_attach_disk_restore(self)
                self.tc_utils.run_virtual_machine_restore(self,
                                                          power_on_after_restore=True,
                                                          unconditional_overwrite=True,
                                                          disk_option=random.choice(
                                                              ['Original',
                                                               'Thick Lazy Zero',
                                                               'Thin',
                                                               'Thick Eager Zero'])
                                                          )
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=True,
                                                      disk_option='Original')

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
