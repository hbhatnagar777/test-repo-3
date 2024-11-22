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
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'v2: VSA VMWARE Full Backup and Ful vm restore with all disk provision option'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            if not self.tc_utils.sub_client_obj.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1'
                raise Exception(self.failure_msg)
            self.tc_utils.run_backup(self, msg='Streaming Backup')

            VirtualServerUtils.decorative_log("Validating if all types of disk are in the vms")
            disk_type_list = {'Thin', 'Thick Lazy Zero', 'Thick Eager Zero'}
            for vm in self.tc_utils.sub_client_obj.vm_list:
                _disks_type_vm = set(self.tc_utils.sub_client_obj.hvobj.VMs[vm].get_disk_provision.values())
                if disk_type_list.issubset(_disks_type_vm):
                    self.log.info("All 3 type of disks present in the vm {}".format(vm))
                else:
                    raise Exception("All Disks type not present in VM {}".format(vm))
            disk_type_list.add('Original')

            for disk_opt in disk_type_list:
                msg = 'FULL VM out of Place restore with disk option: {}'.format(disk_opt)
                self.tc_utils. \
                    run_virtual_machine_restore(self,
                                                power_on_after_restore=True,
                                                unconditional_overwrite=True,
                                                disk_option=disk_opt,
                                                msg=msg)

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
