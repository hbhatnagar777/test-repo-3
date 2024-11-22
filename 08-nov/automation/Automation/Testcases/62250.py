# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils,VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of DRS Settings for VMware"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMWARE - Backup and Restore of DRS Settings"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            auto_subclient = self.tc_utils.sub_client_obj

            backedup_vm_drs_settings = {}
            for vm in auto_subclient.vm_list:
                backedup_vm_drs_settings.update({vm: auto_subclient.hvobj.VMs[vm].get_drs_settings()})
                self.log.info("DRS Settings for VM", vm, ":", backedup_vm_drs_settings.get(vm))

            self.tc_utils.run_backup(self)
            VirtualServerUtils.decorative_log("Deleting Source VMs")
            try:
                for each_vm in auto_subclient.vm_list:
                    auto_subclient.hvobj.VMs[each_vm].delete_vm()
            except Exception as err:
                self.log.exception("Exception while cleaning up VMs: " + str(err))
                raise err

            self.tc_utils.run_virtual_machine_restore(self, in_place=True, validation=False)

            restored_vm_drs_settings = {}
            for vm in auto_subclient.vm_list:
                restored_vm_drs_settings.update({vm: auto_subclient.hvobj.VMs[vm].get_drs_settings()})

            for vm in auto_subclient.vm_list:
                if backedup_vm_drs_settings.get(vm) != restored_vm_drs_settings.get(vm):
                    raise Exception("DRS Settings of source VM and restored VM did not match")
            self.log.info("Verified the restored VM DRS settings with source VM")

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string += '<br>' + str(exp) + '<br>'
            self.ind_status = False

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored VM cleanup was not completed")
            if not self.ind_status:
                self.result_string += self.failure_msg
                self.status = constants.FAILED
