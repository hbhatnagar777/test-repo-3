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

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper,VirtualServerUtils
from AutomationUtils import logger, constants
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing virtual lab in isolated network from backup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Virtual Lab in Isolated network- from Backup"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self) :
        """Main function for test case execution"""
        try:

            VirtualServerUtils.decorative_log("Backup")
            auto_subclient = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self, msg='Streaming Full Backup')

            auto_commcell = auto_subclient.auto_commcell
            auto_client = auto_subclient.auto_vsaclient

            from cvpysdk.virtualmachinepolicies import VirtualMachinePolicies
            vmpolicy_name = self.tcinputs['VMPolicyName'].lower()
            lab_name = self.tcinputs['Lab_Name']
            vmpolicies = VirtualMachinePolicies(auto_commcell.commcell)
            vmpolicy = vmpolicies.get(vmpolicy_name)
            media_agent_name = vmpolicy.properties()['mediaAgent']['clientName']

            try:
                VirtualServerUtils.decorative_log("Adding registry key on mediagent")
                reg_key = 'VmExpiryCheckThreadWaitTimeMinutes'
                auto_subclient.add_registry_key(reg_key, media_agent_name, folder='EventManager',
                                                key_val=2)
            except Exception as exp:
                self.log.error("Failed with error: %s", str(exp))

            hvobj = self.tc_utils.live_mount_obj(vmpolicy, auto_commcell)
            try:
                VirtualServerUtils.decorative_log("Starting Virtual Lab")
                virtual_lab_job = auto_commcell.dev_test_virtual_lab_job(lab_name, isolated_network=True)
                VirtualServerUtils.decorative_log("Validate Virtual Lab job VM")
                VMs = []
                for each_vm in auto_subclient.hvobj.VMs:
                    VMs.append(each_vm)
                auto_client.virtual_lab_validation(source_vm_name=VMs, hvobj=hvobj, vmpolicy=vmpolicy,
                                                   mounted_network_name=None,
                                                   live_mount_job=virtual_lab_job, isolated_network=True,
                                                   virtual_lab=True)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)
            try:
                VirtualServerUtils.decorative_log("Removing registry key")
                reg_key = self.tcinputs.get("reg_key")
                auto_subclient.delete_registry_key(reg_key, media_agent_name)
            except Exception as exp:
                self.log.error("Failed with error: %s", str(exp))

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
        finally:
            try:
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.status = constants.FAILED
                self.result_string = self.failure_msg
