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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants
import time

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA VMWare Disk Level Validation test case"""

    def __init__(self):
        """Initialize the test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMWare Disk Level Validation"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

        self.vsa_subclient = None

        self.backup_options = None
        self.vm_restore_options = None

        self.source_vm = None
        self.restored_vm = None

        self.backup_success = None
        self.restore_success = None

        self.vm_list = None
        self.target_disks = None
        self.multiplier = None
        self.num_threads = None

        self.tcinputs = {
            "Multiplier": None,
            "NumThreads": None
        }

    def init_tc(self):

        self.vsa_subclient = self.tc_utils.initialize(self)

        self.backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)

        self.vm_restore_options = OptionsHelper.FullVMRestoreOptions(
            self.vsa_subclient, self)

        self.multiplier = self.tcinputs["Multiplier"]
        self.num_threads = self.tcinputs["NumThreads"]

    def run(self):
        try:
            self.init_tc()

            # Copying list of Sub-client VMs
            self.vm_list = self.vsa_subclient.hvobj.VMs.copy()

            # Get source vm esx and datastore
            vm_name = next(iter(self.vm_list))
            vm_obj = self.vsa_subclient.hvobj.VMs[vm_name]
            vm_obj.update_vm_info('All', True, True)
            vm_esx = vm_obj.esx_host
            vm_ds = vm_obj.datastore

            # Backing up the Sub-Client
            self.backup_options.set_disk_props = True
            self.backup_options.disk_props_dict = {
                "skip_os": "true",
                "read_only": "true",
                "offline": "false"
            }
            self.backup_options.validation = False
            self.backup_options.validation_skip_all = False
            self.vsa_subclient.backup(self.backup_options)

            # Restoring from the Sub-Client
            self.vm_restore_options.power_on_after_restore = True
            self.vm_restore_options.unconditional_overwrite = True
            self.vm_restore_options._datastore = vm_ds
            self.vm_restore_options._host = [vm_esx]
            self.vsa_subclient.virtual_machine_restore(self.vm_restore_options)
            self.log.info("Waiting for 10 minutes for the Restored VM to boot up")
            time.sleep(60 * 10)

            for vm in self.vm_list:

                # Restoring the Backed up Sub-Client
                source_vm_name = vm
                self.source_vm = self.vsa_subclient.hvobj.VMs[source_vm_name]

                # Get Restored VM Object
                restored_vm_name = "del" + source_vm_name
                vsa_instance = self.vsa_subclient.auto_vsainstance
                vsa_instance.hvobj.VMs = restored_vm_name
                self.restored_vm = vsa_instance.hvobj.VMs[restored_vm_name]

                # Check if VMs are online and accessible
                self.log.info("Waiting for VMs to boot")
                self.source_vm.wait_for_vm_to_boot()
                self.restored_vm.wait_for_vm_to_boot()

                # Get all restored disks
                self.restored_vm.get_all_disks_info()
                restored_disk_list = list(self.restored_vm.disk_dict.keys())

                # Get OS Disk Number
                os_disk = self.source_vm.get_os_disk_number()

                # Get Non-OS Disks from restored VM
                if len(restored_disk_list) > 1:
                    self.target_disks = [x for i, x in enumerate(restored_disk_list) if i != os_disk]
                    counter = 1
                    for disk in self.target_disks:
                        self.log.info("Target Disk " + str(counter) + " : " + disk)
                        counter += 1
                else:
                    raise Exception(
                        "Only OS disk attached to VM: " + self.restored_vm.vm_name)

                # Power off the the restored VM
                # Required to mount its non-OS disk to source VM
                self.restored_vm.power_off()
                time.sleep(60 * 2)

                # Mounting the restored VMs non-OS VMDKs to the source
                self.log.info("Mounting target disk to " + self.source_vm.vm_name)
                for disk in self.target_disks:
                    self.source_vm.mount_vmdk(disk)

                # Wait for reconfiguration to complete
                self.log.info("Waiting for VM reconfiguration")
                time.sleep(60)

                # Verify if Disks are mounted
                mounted = None
                mounted = self.source_vm.verify_vmdks_attached(self.target_disks)

                if mounted:
                    self.log.info(str(len(self.target_disks)) +
                                  " target disks successfully mounted to " +
                                  self.source_vm.vm_name)

                    # Run Disk Compare Script
                    self.source_vm.set_disk_props(self.backup_options.disk_props_dict)

                    self.source_vm.update_vm_info('All', True, True)
                    target_vm_machine = self.source_vm.machine
                    self.log.info("Running disk comparison")

                    output = self.source_vm.compare_disks(self.num_threads, self.multiplier)

                    # comp_res = output.output.split("\n", 1)[0].strip()
                    comp_res = output.strip()

                    if comp_res == "True":
                        self.log.info(
                            "Disk Comparison Successful. Please check logs.")
                    else:
                        raise Exception(
                            "Disk Comparison Failed. Please check logs.")

                    # If restored VM's vmdk mounted to source VM, unmount it
                    self.log.info("Unmounting target disks from " +
                                  self.source_vm.vm_name)
                    for disk in self.target_disks:
                        self.source_vm.unmount_vmdk(disk)
                    time.sleep(60)

                else:
                    raise Exception("Failed to mount target disks.")

        except Exception as exp:
            self.log.error(exp)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            # Reset Disk Properties
            reset_props_dict = {
                "skip_os": "true",
                "read_only": "false",
                "offline": "false"
            }

            for vm in self.vm_list:
                self.vm_list[vm].set_disk_props(reset_props_dict)

            self.vsa_subclient.cleanup_testdata(self.backup_options)

            # Unmount disks if any are left unmounted
            self.source_vm.get_all_disks_info()
            source_disks = list(self.source_vm.disk_dict.keys())
            leftover_disks = list(set(source_disks) & set(self.target_disks))
            if leftover_disks:
                for disk in leftover_disks:
                    self.source_vm.unmount_vmdk(disk)

        except Exception as exp:
            self.log.warning("Tear down was not completed.")
            self.status = constants.FAILED
