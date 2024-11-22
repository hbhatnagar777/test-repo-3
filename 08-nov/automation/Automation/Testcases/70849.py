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
from VirtualServer.VSAUtils.VMHelpers.VmwareVM import VmwareVM


class TestCase(CVTestCase):
    """Class for executing validation for adding SCSI controllers on VMware proxy"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validating extra SCSI controllers are added during HotAdd backup"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(
            self,
            self.products_list.VIRTUALIZATIONVMWARE,
            self.features_list.DATAPROTECTION,
        )

    def create_vmware_client(self, proxy_client):
        """Function to create VMware client object for VM"""

        try:
            self.log.info(f"Creating VMware client object for VM: {proxy_client}")
            content = self.tc_utils.sub_client_obj.hvobj.connection.RetrieveContent()
            vm = None

            for datacenter in content.rootFolder.childEntity:
                if hasattr(datacenter, "vmFolder"):
                    vm_folder = datacenter.vmFolder
                    vm_list = vm_folder.childEntity
                    for entity in vm_list:
                        if (
                            isinstance(entity, self.tc_utils.sub_client_obj.hvobj.vim.VirtualMachine)
                            and entity.name == proxy_client
                        ):
                            vm = entity
                            break
            return vm
        except Exception as exp:
            self.log.error(f"Failed with error: {exp}")
            raise exp

    def run(self):
        """Main function for test case execution"""

        try:
            self.tc_utils.initialize(self)

            self.log.info(f"Fetching subclient level proxy.")
            try: 
                proxy_client = self.tc_utils.sub_client_obj.subclient.subclient_proxy[0]
            except Exception:
                self.log.error("No proxy found at subclient level.")
            self.log.info(f"Proxy client found at subclient level: {proxy_client}")

            vm = self.create_vmware_client(proxy_client)
            vmware_vm_obj = VmwareVM(self.tc_utils.sub_client_obj.hvobj, proxy_client)
            
            self.log.info("Checking if proxy and backup VMs reside on same ESX host.")
            try:
                proxy_status, proxy_host, proxy_datastore = self.tc_utils.sub_client_obj.hvobj.find_vm(proxy_client)
                for backup_vm in self.tc_utils.sub_client_obj.vm_list:
                    source_vm_status, source_vm_host, source_vm_datastore = self.tc_utils.sub_client_obj.hvobj.find_vm(backup_vm)
                    assert proxy_host == source_vm_host
            except:
                self.log.error("Proxy client is not present in the same ESX host as source VMs.")
                self.log.error("Please used a different proxy or source VMs to use HotAdd mode during backup.")
            self.log.info("Proxy and backup VMs reside on same ESX host.")

            self.log.info("Fetching transport mode set on the subclient.")
            if self.tc_utils.sub_client_obj.get_transport_mode() != "hotadd":
                raise Exception("Transport mode is not HotAdd.")

            scsi_controllers = vmware_vm_obj.get_scsi_controllers()
            self.log.info(f"Number of SCSI controllers before backup: {len(scsi_controllers)}")
            if len(scsi_controllers) != 1:
                self.log.info("Proxy client have more than 1 SCSI controllers.")
                vmware_vm_obj.delete_scsi_controllers(scsi_controllers)
            
            self.tc_utils.run_backup(self, msg="Streaming Full Backup")

            scsi_controllers = vmware_vm_obj.get_scsi_controllers()
            self.log.info(f"Number of SCSI controllers after backup: {len(scsi_controllers)}")
            if len(scsi_controllers) != 4:
                raise Exception("Proxy client does not have 4 SCSI controllers.")

            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      msg='FULL VM out of Place restores')

        except Exception as exp:
            self.log.error(f"Failed with error: {exp}")
            self.ind_status = False

        except Exception as exp:
            self.log.error(f"Failed with error: {exp}")
            self.ind_status = False

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(
                    self.tc_utils.backup_options
                )
                self.tc_utils.sub_client_obj.post_restore_clean_up(
                    self.tc_utils.vm_restore_options, status=self.ind_status
                )
            except Exception:
                self.log.warning(
                    "Testcase and/or Restored vm cleanup was not completed"
                )
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
