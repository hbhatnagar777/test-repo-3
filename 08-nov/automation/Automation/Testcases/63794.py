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
        "source_sc": "SC",
        "Storage Policy": "SP32AzureScaleSP"
    }

Pre-requisite to run test case:
*   If test data on guest vm has to reside in path {guest_test_data_folder}\\TestData\\{test_data}
*  test_data_path in input has to be specified and should be path of folder test_data on controller
"""
import random
import time
from datetime import datetime
import threading
from AutomationUtils.cvtestcase import CVTestCase, constants
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Scale Test for Azure"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure Scale Test - Subclient with Large VMs"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''
        self.hvobj = None
        self.tcinputs = {"Storage Policy": None,
                         "guest_test_data_folder": None,
                         "test_data_path": None,
                         "vm_configs": None,
                         "source_sc": None,
                         "snapshot_rg": None}
        self.deployed_vms = []
        self.failed_vms = []
        self.source_auto_sc = None
        self.auto_sub_client = None

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

    def full_vm_restore(self):
        """Validates full vm restore on VMs
        """
        try:
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_sub_client, self)
            vm_restore_options.data_set = self.tcinputs["test_data_path"]
            vm_restore_options.backup_folder_name = self.tcinputs["guest_test_data_folder"]
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            for vm_ in self.auto_sub_client.vm_list:
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

    def file_restores(self):
        """Validates file restore on vms
        """
        try:
            threads = list()
            for vm_ in self.auto_sub_client.vm_list:
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
                customSnapshotResourceGroup=self.tcinputs.get("snapshot_rg")
            )
            return sc_obj
        except Exception as err:
            self.log.error(f"Exception in create vm group {err}")
            raise err

    def delete_deployed_vm(self, vm):
        """Deletes the vm
           Args:
               vm  (str): vm name

        """
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
                while len(vm_delete_thread) >= 4:
                    self.log.info(f"VM delete thread full {vm_delete_thread}")
                    time.sleep(120)
                    vm_delete_thread = [thread for thread in vm_delete_thread if thread.is_alive()]
                try:
                    self.commcell.clients.delete(vm_, True)
                except Exception as vm_err:
                    self.log.warning(f'Delete vm client {vm_} failed with error {vm_err}')
            for thread in vm_delete_thread:
                thread.join()
            try:
                for vm in self.source_auto_sc.vm_list:
                    if vm not in self.hvobj.VMs:
                        self.hvobj.VMs = vm
                    self.log.info(f"Deleting VM {vm}")
                    self.hvobj.VMs[vm].clean_up()
            except Exception as src_vm_err:
                self.log.warning(f"Error while deleting source VM {src_vm_err}")
            try:
                if not self.failed_vms:
                    self.auto_sub_client.subclient._backupset_object. \
                        subclients.delete(self.auto_sub_client.subclient_name)
                else:
                    self.log.warning("Skipping subclient clean up")
            except Exception as sc_err:
                self.log.warning(f'Delete subclient {self.auto_sub_client.subclient}'
                                 f' failed with error {sc_err}')

        except Exception as err:
            self.log.warning(f"Exception in clean up: {err}. resources need cleaned up manually")

    def deploy_scale_vms(self, vm_count=4):
        """ Deploys VMs in Azure with given count
            Args:
                    vm_count            (int):  Number of VMs to deploy
        """
        try:
            total_vm_count = 0
            vm_configs = self.tcinputs["vm_configs"]
            for count in range(vm_count):
                vm_config = random.choice(vm_configs)
                available_os = [os.replace("Image", "") for os in vm_config if "Image" in os]
                vm_os = random.choice(available_os)
                vm_props = {
                    "vm_name": f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}" +
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
                vm_props["vmSize"] = self.tcinputs.get("vmSize", "Standard_DS3_v2")
                deployed_vm = self.hvobj.create_vm_from_image(vm_props)
                total_vm_count += 1
                self.deployed_vms.append(deployed_vm)

        except Exception as err:
            self.log.error(f"Error while creating VMs {err}")
            raise err

    def run_inplace_restore(self, sc_obj):
        """ Runs InPlace restore for source subclient
            Args:
                sc_obj  (obj): subcleint object

        """
        job = sc_obj.full_vm_restore_in_place(overwrite=True,
                                              power_on=False)
        self.log.info(f"Started inplace restore job {job.job_id}")
        if not job.wait_for_completion():
            raise Exception(
                "Restore Job failed with error: " + job.delay_reason
            )
        if "errors" in job.status:
            raise Exception("Restore Job completed with one or more errors")
        self.log.info("InPlace Restore Job successful")

    def copy_attach_disk(self, no_of_disk=12):
        """ Deploys VMs in Azure with given count
            Args:
                no_of_disk  (int):  Number of disks to copied and attached per VM
        """
        for each_vm in self.deployed_vms:
            self.hvobj.VMs = each_vm
            destination_vm = self.hvobj.VMs[each_vm]
            src_vm = None
            for vm in self.source_auto_sc.vm_list:
                self.hvobj.VMs = vm
                if self.hvobj.VMs[vm].guest_os == destination_vm.guest_os:
                    self.log.info(f"Using {vm} as source to copy data disk"
                                  f" for destination vm {each_vm}")
                    src_vm = self.hvobj.VMs[vm]
                    break
            if not src_vm:
                self.log.error(f"No matching source vm os : "
                               f"{destination_vm.guest_os} found for {each_vm}")
                self.failure_msg += f"No matching source vm os : " \
                                    f"{destination_vm.guest_os} found for {each_vm}"
                continue
            for disk in src_vm.disk_info:
                if disk != "OsDisk":
                    data_disk_id = src_vm.disk_info[disk]
                    break
            else:
                self.log.info(f"No data disk found in {src_vm.name}")
                self.failure_msg += f"No data disk found in {src_vm.name}"
                continue
            disk_id_list = []
            for i in range(no_of_disk):
                name, disk_id = src_vm.hvobj. \
                    copy_managed_disk(
                    self.tcinputs.get('disk_resource_group',
                                      destination_vm.resource_group_name),
                    data_disk_id, f"{each_vm}_data-disk_{i + 1}", src_vm.region)
                disk_id_list.append(disk_id)
            time.sleep(120)
            destination_vm.attach_disks(disk_id_list)
            time.sleep(60)
            if destination_vm.guest_os == 'Windows':
                destination_vm.update_vm_info('All', True, True)
                destination_vm.machine.set_all_disks_online()
                destination_vm.update_vm_info('All', True, True)

            else:
                destination_vm.update_vm_info(prop='Basic', force_update=True)

    def power_off_vms(self):
        """Power off deployed VMs"""
        self.hvobj.update_hosts()
        for vm_ in self.deployed_vms:
            self.hvobj.VMs[vm_].power_off(skip_wait_time=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            source_sc = self.tcinputs.get("source_sc")
            src_sc = self.auto_backupset.backupset.subclients.get(source_sc)
            self.run_inplace_restore(src_sc)
            self.hvobj.update_hosts()
            self.source_auto_sc = VirtualServerHelper. \
                AutoVSASubclient(self.auto_backupset,
                                 src_sc)
            self.deploy_scale_vms(self.tcinputs.get('vm_count', 4))
            time.sleep(180)
            self.hvobj.update_hosts()
            self.copy_attach_disk(self.tcinputs.get('no_of_disk_to_copy', 12))
            sc_obj = self.create_vm_group()

            self.auto_sub_client = VirtualServerHelper. \
                AutoVSASubclient(self.auto_backupset,
                                 sc_obj)
            self.power_off_vms()
            backup_options = OptionsHelper.BackupOptions(self.auto_sub_client)
            backup_options.backup_type = "FULL"
            VirtualServerUtils.decorative_log("Backup(FULL)")
            self.auto_sub_client.backup(backup_options, skip_discovery=True)
            self.log.info("%(boundary)s %(message)s %(boundary)s",
                          {'boundary': "-" * 25,
                           'message': "INCREMENTAL Backup"})
            backup_options.backup_type = "INCREMENTAL"
            VirtualServerUtils.decorative_log("Backup(INCREMENTAL)")
            self.auto_sub_client.backup(backup_options, skip_discovery=True)
            VirtualServerUtils.decorative_log("File Restore")
            self.file_restores()
            VirtualServerUtils.decorative_log("Full Vm Restore")
            self.full_vm_restore()

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp) + self.failure_msg
            self.status = constants.FAILED

        finally:
            if self.failure_msg:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
            self.log.info("%(boundary)s %(message)s %(boundary)s",
                          {'boundary': "-" * 25,
                           'message': "Clean up"})
            self.clean_up()


class FileRestoreThread(threading.Thread):
    """Class for running backups"""

    def __init__(self, auto_vsa_sc, tc_inputs, vm):
        super().__init__()
        self.auto_vsa_sc = auto_vsa_sc
        self.tc_inputs = tc_inputs
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
            file_restore_options.data_set = self.tc_inputs["test_data_path"]
            file_restore_options.backup_folder_name = self.tc_inputs["guest_test_data_folder"]
            file_restore_options.skip_block_level_validation = True
            file_restore_options.restore_path = file_restore_options.client_machine.join_path(
                file_restore_options.restore_path, f"{self.vm}_File_Restore")
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
            auto_sub_client.guest_file_restore(file_restore_options, discovered_client=self.vm)
        except Exception as err:
            self.exception = err
