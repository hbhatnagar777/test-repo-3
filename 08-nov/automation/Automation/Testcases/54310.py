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

from VirtualServer.VSAUtils import VirtualServerHelper
from VirtualServer.VSAUtils.blr import BLRHelper


class TestCase(CVTestCase):
    """Class for executing live mount"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "BLR Live Replication Validation"
        self.blr_helper = None
        self.hypervisor = None
        self.vm = None
        self.tcinputs = {
            "vmname": "string",
            "policy": "string",
            "plan": "string"
        }

    def setup(self):
        auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
        auto_instance.hvobj.VMs = self.tcinputs['vmname']
        self.hypervisor = auto_instance.hvobj
        self.vm = self.hypervisor.VMs[self.tcinputs['vmname']]
        self.vm.update_vm_info(prop="All")

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_blr_pair()
            for _ in range(3):
                self.blr_helper.write_temp_data(1, 1, 10)
                self.boot_vm_and_validate(test_boot=True)
            self.boot_vm_and_validate(test_boot=False)
            self.blr_helper.cleanup_test_data()
        except Exception as exp:
            self.log.exception(f'Testcase failed with exception:{exp}')
            self._result_string = str(exp)
            self._status = constants.FAILED
            raise Exception("Testcase failed") from exp

    def create_blr_pair(self):
        """Creates a BLR Pair"""
        self.blr_helper = BLRHelper(self.hypervisor, self.vm, self.backupset, self.subclient)
        self.blr_helper.create_blr_pair(self.tcinputs["policy"], self.tcinputs["plan"])

    def boot_vm_and_validate(self, test_boot):
        """Boots the VM and validates content and deletes the VM as well

        Args:
            test_boot    (bool):  Whether to boot vm in test mode

        """
        boot_vm = self.blr_helper.get_boot_vm(test_boot)
        self.vm.machine.compare_folders(
            boot_vm.machine,
            self.blr_helper.test_data_path,
            self.blr_helper.test_data_path)
        boot_vm.delete_vm()
