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


Input Example:
 {
        "ClientName":"client1",
        "InstanceName" : "azure resource manager",
        "test_data_path": "C:\\TestData\\time",
        "AgentName" : "Virtual Server",
        "BackupsetName" : "defaultBackupSet",
        "vm_configs" : [{"ResourceGroup": "RG3", "StorageAccount": "SP", "Region": "East US 2",
         "subnet_id": "/subscriptions/{sub_id}}/resourceGroups/RG/providers/Microsoft.Network/
         virtualNetworks/dev-sapna-exproute-vnet12/subnets/dev1",
        "WindowsImage": "/subscriptions/{sub_id}/resourceGroups/RG/
        providers/Microsoft.Compute/images/win-img"}],
        "vm_prefix" : "Scale",
        "guest_test_data_folder": "backup",
        "Resourcegroup": "Restore_RG",
        "Storageaccount" : "RestoreSP",
        "Tags": {
            "TestPerformed": "ScaleTest",
            "Owner": "VSA"
        },
        "vm_count" : 1,
        "Storage Policy": "SP32AzureScaleSP",
        "restore_vm_count": 2
    }

Pre-requisite to run test case:
* If test data on guest vm has to reside in path {guest_test_data_folder}\\TestData\\{test_data}
*  test_data_path in input has to be specified and should be path of folder test_data on controller
"""
import random
import time
import threading
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils
from datetime import datetime


class TestCase(CVTestCase):
    """Class for executing Scale Test for Azure with 100 VMs in one Subclient"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure Scale Test - Single subclient case"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''
        self.hvobj = None
        self.tcinputs = {"Storage Policy": None,
                         "guest_test_data_folder": None,
                         "test_data_path": None,
                         "vm_configs": None
                         }
        self.deployed_vms = []
        self.failed_vms = []
        self.hvobj = None

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            self.auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            self.auto_client = VirtualServerHelper.AutoVSAVSClient(self.auto_commcell, self.client)
            self.auto_instance = VirtualServerHelper.AutoVSAVSInstance(self.auto_client,
                                                                       self.agent, self.instance)
            self.auto_backupset = VirtualServerHelper.AutoVSABackupset(
                self.auto_instance, self.backupset)
            self.hvobj = self.auto_instance.hvobj

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            raise exp

    def full_vm_restore(self, vm_count=5):
        """Validates full vm restore on random vms
          Args:
                    vm_count            (int):  Number of VMs to perform restore

        """
        try:
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_sub_client, self)
            vm_restore_options.data_set = self.tcinputs["test_data_path"]
            vm_restore_options.backup_folder_name = self.tcinputs["guest_test_data_folder"]
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_list = [*set(random.choices(self.auto_sub_client.vm_list, k=vm_count))]
            for vm_ in vm_list:
                try:
                    vm_restore_options.advanced_restore_options = {}
                    self.auto_sub_client.virtual_machine_restore(vm_restore_options,
                                                                 discovered_client=vm_)
                    try:
                        self.auto_sub_client.post_restore_clean_up(vm_restore_options, True, True,
                                                                   source_vm_list=[vm_])
                    except Exception as post_rst_err:
                        self.log.warning(f"Post restore cleanup failed {post_rst_err}")
                except Exception as err:
                    self.log.warning(f"Full VM restore validation failed "
                                     f"for {vm_} with error : {err}")
                    self.failed_vms.append(vm_)
                    self.failure_msg += f"Full VM restore validation failed for {vm_}"
                    try:
                        self.auto_sub_client.post_restore_clean_up(vm_restore_options, True, False,
                                                                   source_vm_list=[vm_])
                    except Exception as post_rst_err:
                        self.log.warning(f"Post restore cleanup failed {post_rst_err}")
        except Exception as err:
            self.log.error(f"Error in Full VM restore {err}")
            self.failure_msg += f"Error in Full VM restore {err}"

    def file_restores(self, vm_count=5):
        """Validates file restore on random vms
          Args:
                    vm_count            (int):  Number of VMs to perform restore
        """
        try:
            vm_list = [*set(random.choices(self.auto_sub_client.vm_list, k=vm_count))]
            threads = list()
            for vm_ in vm_list:
                restore_thread = FileRestoreThread(self.auto_sub_client, self.tcinputs, vm_)
                restore_thread.start()
                threads.append(restore_thread)
            for thread in threads:
                thread.join()
                if thread.exception:
                    self.log.warning(f"File restore validation failed for {thread.vm} with error : {thread.exception}")
                    self.failed_vms.append(thread.vm)
                    self.failure_msg += f"File restore validation failed for {thread.vm}"
        except Exception as err:
            self.log.error(f"Error in file restore {err}")
            self.failure_msg += f"Error in file restore {err}"

    def create_vm_group(self):
        """Creates subclient with content as deployed VMs"""
        try:
            self.hvobj.update_hosts()
            vmg_content = []
            for vm_ in self.deployed_vms:
                temp_json = {
                    "display_name": vm_,
                    "equal_value": True,
                    'allOrAnyChildren': True,
                    "type": 10
                }
                vmg_content.append(temp_json)
            subclient_content = [{'allOrAnyChildren': False, 'content': vmg_content}]
            if f"TC_{self.id}".lower() in self.backupset.subclients.all_subclients:
                self.backupset.subclients.delete(f"TC_{self.id}".lower())
            sc_obj = self.auto_backupset.backupset.subclients.add_virtual_server_subclient(
                f"TC_{self.id}", subclient_content,
                storage_policy=self.tcinputs["Storage Policy"],
                customSnapshotResourceGroup=self.tcinputs.get("snapshot_rg", None)
            )
            return sc_obj
        except Exception as err:
            self.log.error(f"Exception in create vm group {err}")
            raise err

    def delete_deployed_vm(self, vm):
        """Deletes the vm"""
        try:
            self.log.info(f"Cleaning up vm {vm}")
            self.hvobj.VMs[vm].clean_up()
        except Exception as err:
            self.log.warning(f"Clean up of {vm} or its resources failed with {err}")

    def clean_up(self):
        """Cleans up deployed vms and subclient"""
        try:
            VirtualServerUtils.decorative_log("Clean up")
            vm_delete_thread = []
            time.sleep(180)
            self.hvobj.update_hosts()
            for vm_ in self.deployed_vms:
                if vm_ not in self.hvobj.VMs:
                    self.hvobj.VMs = vm_
                if vm_ in self.failed_vms:
                    self.log.info(f"Skipping cleanup for vm {vm_}")
                    self.hvobj.VMs[vm_].power_off(skip_wait_time=True)
                    continue
                thread = threading.Thread(target=self.delete_deployed_vm, args=(vm_,))
                thread.start()
                vm_delete_thread.append(thread)
                while len(vm_delete_thread) >= 20:
                    self.log.info(f"VM delete thread full {vm_delete_thread}")
                    time.sleep(120)
                    vm_delete_thread = [thread for thread in vm_delete_thread if thread.is_alive()]
                try:
                    self.commcell.clients.delete(vm_, True)
                except Exception as vm_err:
                    self.log.warning(f'Delete vm client {vm_} failed with error {vm_err}')
            try:
                if not self.failed_vms:
                    self.auto_sub_client.subclient._backupset_object. \
                        subclients.delete(self.auto_sub_client.subclient_name)
                else:
                    self.log.warning("Skipping subclient clean up")
            except Exception as sc_err:
                self.log.warning(f'Delete subclient {self.auto_sub_client.subclient}'
                                 f' failed with error {sc_err}')
            for thread in vm_delete_thread:
                thread.join()
        except Exception as err:
            self.log.warning(f"Exception in clean up: {err}. resources need cleaned up manually")

    def deploy_scale_vms(self, vm_count=50):
        """ Deploys VMs in Azure with given count
            Args:
                    vm_count            (int):  Number of VMs to deploy per client
        """
        try:
            total_vm_count = 0
            vm_configs = self.tcinputs["vm_configs"]
            for count in range(vm_count):
                vm_config = random.choice(vm_configs)
                available_os = [os.replace("Image", "") for os in vm_config if "Image" in os]
                vm_os = random.choice(available_os)
                vm_props = {
                    "vm_name": f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}"+
                               f"-{str(total_vm_count + 1)}-{vm_os[:3]}",
                    "resourceGroup": vm_config.get('ResourceGroup'),
                    "location": vm_config.get('Region', 'East US 2').replace(" ", "").lower(),
                    "vm_os": vm_os.lower(),
                    "tags": dict(self.tcinputs.get('Tags')),
                    "nic_props": {
                        "nic_name": f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}" +
                                    f"-nic-{str(total_vm_count + 1)}-{vm_os[:3]}",
                        "subnet_id": vm_config.get("subnet_id"),
                        "resourceGroup": vm_config.get('ResourceGroup')
                    },
                    "image_id": vm_config.get(vm_os + 'Image')
                }
                vm_props["tags"].update({"createdAt": datetime.now().strftime("%d-%m-%Y %H:%M:%S")})
                vm_props["vmSize"] = self.tcinputs.get("vmSize", "Standard_B1s")
                try:
                    deployed_vm = self.hvobj.create_vm_from_image(vm_props)
                except Exception as vm_err:
                    self.log.warning(f"Vm deployment for " + f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}" +
                                     f"-{str(total_vm_count + 1)}-{vm_os[:3]}" + f" with error {vm_err}")
                    continue
                total_vm_count += 1
                self.deployed_vms.append(deployed_vm)
            return total_vm_count
        except Exception as err:
            self.log.error(f"Error while creating VMs {err}")
            raise err

    def power_off_vms(self):
        """Power off deployed VMs"""
        self.hvobj.update_hosts()
        for vm_ in self.deployed_vms:
            self.hvobj.VMs[vm_].power_off(skip_wait_time=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            VirtualServerUtils.decorative_log(f"Deploy Scale VMs")
            total_vm = self.deploy_scale_vms(self.tcinputs.get('vm_count', 100))
            time.sleep(240)
            if total_vm < (self.tcinputs.get('vm_count', 100)/2):
                raise Exception("Deployed vm count is less than half the excepted vm count")
            sc_obj = self.create_vm_group()
            time.sleep(240)
            self.auto_sub_client = VirtualServerHelper. \
                AutoVSASubclient(self.auto_backupset,
                                 sc_obj)
            self.power_off_vms()
            backup_options = OptionsHelper.BackupOptions(self.auto_sub_client)
            backup_options.backup_type = "FULL"
            VirtualServerUtils.decorative_log(f"Backup(FULL)")
            self.auto_sub_client.backup(backup_options, skip_discovery=True)
            backup_options.backup_type = "INCREMENTAL"
            VirtualServerUtils.decorative_log(f"Backup(INCREMENTAL)")
            self.auto_sub_client.backup(backup_options, skip_discovery=True)
            self.commcell.clients.refresh()
            VirtualServerUtils.decorative_log(f"File Restore")
            self.file_restores(self.tcinputs.get('restore_vm_count', 5))
            VirtualServerUtils.decorative_log(f"Full VM Restore")
            self.full_vm_restore(self.tcinputs.get('restore_vm_count', 5))

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp) + self.failure_msg
            self.status = constants.FAILED

        finally:
            if self.failure_msg:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
            self.clean_up()


class FileRestoreThread(threading.Thread):
    """Class for running backups"""

    def __init__(self, auto_vsa_sc, tcinputs, vm):
        super().__init__()
        self.auto_vsa_sc = auto_vsa_sc
        self.tcinputs = tcinputs
        self.vm = vm
        self.exception = None

    def run(self):
        try:
            self.auto_vsa_sc.log.info(f"Started restore thread {self.ident} for VM : {self.vm}")
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                self.auto_vsa_sc.auto_vsaclient,
                self.auto_vsa_sc.vsa_agent,
                self.auto_vsa_sc.vsa_agent.instances.get(self.auto_vsa_sc.auto_vsainstance.vsa_instance_name))
            auto_backupset = VirtualServerHelper.AutoVSABackupset(
                auto_instance,
                auto_instance.vsa_instance.backupsets.get(
                    self.auto_vsa_sc.auto_vsa_backupset.backupset.name))

            sc_obj = auto_backupset.backupset.subclients.get(self.auto_vsa_sc.subclient_name)

            auto_sub_client = VirtualServerHelper. \
                AutoVSASubclient(auto_backupset,
                                 sc_obj)
            auto_sub_client.backup_option = self.auto_vsa_sc.backup_option
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_sub_client)
            file_restore_options.data_set = self.tcinputs["test_data_path"]
            file_restore_options.backup_folder_name = self.tcinputs["guest_test_data_folder"]
            file_restore_options.skip_block_level_validation = True
            file_restore_options.restore_path = file_restore_options.client_machine.join_path(
                file_restore_options.restore_path, f"{self.vm}_File_Restore")
            auto_sub_client.hvobj.VMs[self.vm].update_vm_info(prop="All", os_info=True)
            if not auto_sub_client.hvobj.VMs[self.vm].drive_list:
                retry = 5
                while retry >= 0 and not auto_sub_client.hvobj.VMs[self.vm].drive_list:
                    time.sleep(60)
                    self.auto_vsa_sc.log.info("Unable get drive list retrying")
                    auto_sub_client.hvobj.VMs[self.vm].get_drive_list()
                    retry -= 1
                if not auto_sub_client.hvobj.VMs[self.vm].drive_list:
                    self.auto_vsa_sc.log("Unable to get drive details skipping VM.")
                    auto_sub_client.hvobj.VMs[self.vm].power_off(skip_wait_time=True)
                    return
            auto_sub_client.hvobj.VMs[self.vm].power_off(skip_wait_time=True)
            auto_sub_client.guest_file_restore(file_restore_options, discovered_client=self.vm)
        except Exception as err:
            self.exception = err
