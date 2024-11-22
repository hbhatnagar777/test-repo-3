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

Example Input :
{
    "Clients_config": "[{'AZUREDEVS_V2':[{'ResourceGroup': 'Nischith-RG3',
    'StorageAccount': 'vishalsalocked', 'Region': 'East US 2', 'subnet_id':
    '/subscriptions/{sub_id}/resourceGroups/RG/providers/Microsoft.Network
    virtualNetworks/dev/subnets/dev',
    'WindowsImage': '/subscriptions/{sub_id}/resourceGroups/rg-scale/providers/
    Microsoft.Compute/images/win-img'}]}, ,
    {'AZDEVS2':[{'ResourceGroup': 'RG2', 'StorageAccount': 'sa1', 'Region':
    'East US 2', 'subnet_id': '/subscriptions/{sub_id2}/resourceGroups/RG/
    providers/Microsoft.Network/virtualNetworks/dev2/subnets/dev','WindowsImage':
     '/subscriptions/{sub_id2}/resourceGroups/rg-scale/providers
     /Microsoft.Compute/images/win-img'}]}]",
    "InstanceName" : "azure resource manager",
    "test_data_path": "C:\\TestData\\time",
    "guest_test_data_folder": "backup",
    "AgentName" : "Virtual Server",
    "BackupsetName" : "defaultBackupSet",
    "Resourcegroup": "RG_Restore",
    "Storageaccount" : "sa1",
    "vm_prefix" : "Scale",
    "Tags": {
        "TestPerformed": "ScaleTest"
    },
    "Storage Policy": "AzureScaleSP",
    "vm_count" : 5
}

Pre-requisite to run test case:
* If test data on guest vm has to reside in path {guest_test_data_folder}\\TestData\\{test_data}
* test_data_path in input has to be specified and should be path of folder test_data on controller
"""
import random
import time
from datetime import datetime
import threading
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Scale Test for Azure with multiple clients"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure Scale Test - Multi subscription and multi subclient case"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.clients = {}
        self.ind_status = True
        self.failure_msg = ''
        self.tcinputs = {"Clients_configs": None,
                         "Storage Policy": None,
                         "guest_test_data_folder": None,
                         "test_data_path": None}

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            for client in eval(self.tcinputs.get("Clients_configs")):
                client_name = list(client.keys())[0]
                commcell_client = self.commcell.clients.get(client_name)
                auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, commcell_client)
                agent = commcell_client.agents.get(self.tcinputs["AgentName"])
                instance = agent.instances.get("azure resource manager")
                auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                      agent,
                                                                      instance)

                self.clients[client_name.lower()] = {"auto_instance": auto_instance,
                                                     "vm_configs": client[client_name],
                                                     "failed_backup_sc_list": [],
                                                     "skip_cleanup_vm_list": [],
                                                     "skip_cleanup_sc_list": []}

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception

    def deploy_scale_vms(self, vms_per_client=5):
        """ Deploys VMs in Azure
            Args:
                    vms_per_client            (int):  Number of VMs to deploy per client

        """
        try:
            total_vm_count = 0
            for client in self.clients:
                self.log.info(f"Deploying VMs for client {client}")
                self.clients[client]['deployed_vms'] = list()
                vm_configs = self.clients.get(client)["vm_configs"]
                for count in range(vms_per_client):
                    vm_config = random.choice(vm_configs)
                    available_os = [os.replace("Image", "") for os in vm_config if "Image" in os]
                    vm_os = random.choice(available_os)
                    vm_props = {
                        "vm_name": f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}-" +
                                   f"{str(total_vm_count + 1)}-{vm_os[:3]}",
                        "resourceGroup": vm_config.get('ResourceGroup'),
                        "location": vm_config.get('Region', 'East US 2').replace(" ", "").lower(),
                        "vm_os": vm_os.lower(),
                        "tags": dict(self.tcinputs.get('Tags')),
                        "nic_props": {
                            "nic_name": f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}-" +
                                        f"nic-{str(total_vm_count + 1)}-{vm_os[:3]}",
                            "subnet_id": vm_config.get("subnet_id"),
                            "resourceGroup": vm_config.get('ResourceGroup')
                        },
                        "image_id": vm_config.get(vm_os + 'Image')
                    }
                    vm_props["tags"].update({
                        "createdAt": datetime.now().strftime("%d-%m-%Y %H:%M:%S")})
                    vm_props["vmSize"] = self.tcinputs.get("vmSize", "Standard_B1s")
                    try:
                        deployed_vm = self.clients.get(client).get("auto_instance"). \
                            hvobj.create_vm_from_image(vm_props)
                    except Exception as vm_err:
                        self.log.warning(f"Vm deployment for " + f"{self.tcinputs.get('vm_prefix', 'Scale-autoVM')}" +
                                         f"-{str(total_vm_count + 1)}-{vm_os[:3]}" + f" with error {vm_err}")
                        continue
                    self.clients[client]['deployed_vms'].append(deployed_vm)
                    total_vm_count += 1
                self.log.info(f"Successfully deployed VMs :{self.clients[client]['deployed_vms']}")
            return total_vm_count

        except Exception as err:
            self.log.error(f"Error while creating VMs {err}")
            self.failure_msg += f"Error while creating VMs {err}"
            return total_vm_count

    def create_vm_groups(self):
        try:
            sc_count = 0
            for client in self.clients:
                self.log.info(f"Creating vm_groups for client {client}")
                self.clients[client]["auto_instance"].hvobj.update_hosts()
                sc_obj_list = []
                backupset = self.clients.get(client).get("auto_instance"). \
                    vsa_instance.backupsets.get("defaultBackupSet")
                auto_backupset = VirtualServerHelper.AutoVSABackupset(
                    self.clients.get(client).get("auto_instance"),
                    backupset)
                vm_list = self.clients[client]['deployed_vms']
                vm_cnt = 0
                while vm_cnt < len(vm_list):
                    vmg_content = []
                    content_cnt = random.randint(1, 3)
                    for VM in vm_list[vm_cnt: vm_cnt + content_cnt]:
                        temp_json = {
                            "display_name": VM,
                            "equal_value": True,
                            'allOrAnyChildren': True,
                            "type": 10
                        }
                        vmg_content.append(temp_json)
                    subclient_content = [{'allOrAnyChildren': False, 'content': vmg_content}]
                    if f"TC_{self.id}_{sc_count}".lower() in auto_backupset.backupset.subclients.all_subclients:
                        auto_backupset.backupset.subclients.delete(f"TC_{self.id}_{sc_count}".lower())
                    sc_obj = auto_backupset.backupset.subclients.add_virtual_server_subclient(
                        f"TC_{self.id}_{sc_count}", subclient_content,
                        storage_policy=self.tcinputs["Storage Policy"],
                        customSnapshotResourceGroup=self.tcinputs.get("snapshot_rg", None)
                    )
                    sc_obj_list.append(sc_obj)
                    self.log.info(f"Created subclient {f'TC_{self.id}_{sc_count}'} with"
                                  f" content {vm_list[vm_cnt: vm_cnt + content_cnt]}")
                    sc_count += 1
                    vm_cnt += content_cnt
                time.sleep(60)
                self.clients[client]['sc_obj_list'] = sc_obj_list
                auto_sc_list = []
                for sc in sc_obj_list:
                    try:
                        auto_sc = VirtualServerHelper.AutoVSASubclient(auto_backupset, sc)
                        auto_sc_list.append(auto_sc)
                    except Exception as err:
                        self.log.err(f"Error {err}creating AutoVSASubclient object for {sc.name}"
                                     f" Test Case will fail!")
                        self.failure_msg += f"Error creating AutoVSASubclient object for {sc.name}"
                        self.clients[client]["skip_cleanup_sc_list"].append(sc.name)
                        self.clients[client]["skip_cleanup_vm_list"] += vm_list
                self.clients[client]['auto_subclient_list'] = auto_sc_list
        except Exception as err:
            self.log.error(f"Exception in create vm group {err}")
            self.failure_msg += f"Exception in create vm group {err}"
            raise Exception

    def perform_backup(self, backup_type="FULL"):
        """Runs backup on all subclients
           Args:
            backup_type  (str): Backup type
        """
        try:
            sc_obj_list = [sc_obj for client in self.clients for sc_obj
                           in self.clients[client]['auto_subclient_list']]
            threads = list()
            for sc in sc_obj_list:
                backup_thread = BackupThread(sc, backup_type)
                backup_thread.start()
                threads.append(backup_thread)
            for thread in threads:
                thread.join()
                if thread.exception:
                    client_name = thread.sub_client_obj.auto_vsaclient.vsa_client_name.lower()
                    self.log.error(
                        f"Backup for subclient {thread.sub_client_obj.subclient_name}"
                        f" of client {client_name} failed"
                        f" skipping restore validations and cleanup for the subclient")
                    self.clients[client_name]["skip_cleanup_sc_list"] \
                        .append(thread.sub_client_obj.subclient_name)
                    self.clients[client_name]["skip_cleanup_vm_list"] += \
                        thread.sub_client_obj.vm_list
                    self.failure_msg += f"Backup failed for subclient " \
                                        f"{thread.sub_client_obj.subclient_name};"
        except Exception as err:
            self.log.error(f"Error performing backups : {err}")
            self.failure_msg += "Error while performing backup. Please check logs ;"

    def delete_deployed_vm(self, hvobj, vm):
        """Deletes Vm
        Args:
            hvobj  (object): hypervisor object
            vm     (str):  vm name

        """
        try:
            self.log.info(f"Cleaning up vm {vm}")
            hvobj.VMs[vm].clean_up()
        except Exception as err:
            self.log.warning(f"Clean up of {vm} or its resources failed with {err}")

    def power_off_all_vm(self):
        """Power off deployed VMs"""
        for client in self.clients:
            hvobj = self.clients[client]['auto_instance'].hvobj
            hvobj.update_hosts()
            for vm in self.clients[client].get('deployed_vms', []):
                if vm not in hvobj.VMs:
                    hvobj.VMs = vm
                hvobj.VMs[vm].power_off(skip_wait_time=True)

    def clean_up(self):
        """Cleans up deployed vms and subclient"""
        try:
            vm_delete_thread = []
            VirtualServerUtils.decorative_log("Clean up")
            time.sleep(180)
            for client in self.clients:
                hvobj = self.clients[client]['auto_instance'].hvobj
                hvobj.update_hosts()
                for vm in self.clients[client].get('deployed_vms', []):
                    if vm not in hvobj.VMs:
                        hvobj.VMs = vm
                    if vm in self.clients[client]['skip_cleanup_vm_list']:
                        self.log.info(f"Skipping cleanup for vm {vm}")
                        hvobj.VMs[vm].power_off(skip_wait_time=True)
                        continue
                    thread = threading.Thread(target=self.delete_deployed_vm, args=(hvobj, vm,))
                    thread.start()
                    vm_delete_thread.append(thread)
                    while len(vm_delete_thread) >= 10:
                        self.log.info(f"VM delete thread full {vm_delete_thread}")
                        time.sleep(120)
                        vm_delete_thread = [thread for thread in vm_delete_thread
                                            if thread.is_alive()]
                    try:
                        self.commcell.clients.delete(vm, True)
                    except Exception as vm_err:
                        self.log.warning(f'Delete vm client {vm} failed with error {vm_err}')
                for sc in self.clients[client].get('sc_obj_list', []):
                    try:
                        if sc.name.lower() in self.clients[client]['skip_cleanup_sc_list']:
                            self.log.info(f"Skipping subclient cleanup for {sc}")
                            continue
                        sc._backupset_object.subclients.delete(sc.name)
                    except Exception as sc_err:
                        self.log.warning(f'Delete vm client {sc.name} failed with error {sc_err}')
            for thread in vm_delete_thread:
                thread.join()
        except Exception as err:
            self.log.warning(f"Clean up failed with error : {err}. "
                             f"resources need cleaned up manually")

    def full_vm_restore(self, sc_obj_list):
        """Validates file restore on random vms
            Args:
                sc_obj_list           (list):  lis of sub client obj
        """
        try:
            for sc_obj in sc_obj_list:
                self.log.info(f"Performing full vm restore for subclient {sc_obj.subclient_name}")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(sc_obj, self)
                vm_restore_options.data_set = self.tcinputs["test_data_path"]
                vm_restore_options.backup_folder_name = self.tcinputs["guest_test_data_folder"]
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                for vm in sc_obj.vm_list:
                    try:
                        vm_restore_options.advanced_restore_options = {}
                        sc_obj.virtual_machine_restore(vm_restore_options, discovered_client=vm)
                        try:
                            sc_obj.post_restore_clean_up(vm_restore_options, True, True,
                                                         source_vm_list=[vm])
                        except Exception as post_rst_err:
                            self.log.warning(f"post restore cleanup failed {post_rst_err}")

                    except Exception as err:
                        self.log.error(f"Full restore validation failed for {vm} with err : {err}")
                        self.clients[sc_obj.auto_vsaclient.
                        vsa_client_name]["skip_cleanup_sc_list"].append(sc_obj.subclient_name)
                        self.clients[sc_obj.auto_vsaclient.
                        vsa_client_name]["skip_cleanup_vm_list"].append(vm)
                        self.failure_msg += f"Full restore validation failed for {vm};"
                        try:
                            sc_obj.post_restore_clean_up(vm_restore_options, True, False,
                                                         source_vm_list=[vm])
                        except Exception as post_rst_err:
                            self.log.warning(f"post restore cleanup failed {post_rst_err}")
        except Exception as err:
            self.log.error(f"Error in Full VM restore {err}")
            self.failure_msg += f"Error in Full VM restore {err}"

    def file_restores(self, sc_obj_list):
        """Validates file restore on random vms
            Args:
                sc_obj_list           (list):  lis of sub client obj
        """
        try:
            for sc_obj in sc_obj_list:
                self.log.info(f"Performing file restore for subclient {sc_obj.subclient_name}")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(sc_obj)
                file_restore_options.data_set = self.tcinputs["test_data_path"]
                file_restore_options.backup_folder_name = self.tcinputs["guest_test_data_folder"]
                file_restore_options.skip_block_level_validation = True

                for vm_ in sc_obj.vm_list:
                    try:
                        sc_obj.hvobj.VMs[vm_].update_vm_info(prop="All", os_info=True)
                        if not sc_obj.hvobj.VMs[vm_].drive_list:
                            retry = 5
                            while retry >= 0 and not sc_obj.hvobj.VMs[vm_].drive_list:
                                time.sleep(60)
                                self.log.info("Unable get drive list retrying")
                                sc_obj.hvobj.VMs[vm_].get_drive_list()
                                retry -= 1
                            if not sc_obj.hvobj.VMs[vm_].drive_list:
                                self.log("Unable to get drive details skipping VM from file restore.")
                                sc_obj.hvobj.VMs[vm_].power_off(skip_wait_time=True)
                                continue
                        sc_obj.guest_file_restore(file_restore_options, discovered_client=vm_)
                    except Exception as err:
                        self.log.error(f"File restore validation failed for {vm_}")
                        self.clients[sc_obj.auto_vsaclient.
                        vsa_client_name]["skip_cleanup_sc_list"].append(sc_obj.subclient_name)
                        self.clients[sc_obj.auto_vsaclient.
                        vsa_client_name]["skip_cleanup_vm_list"].append(vm_)
                        self.log.error(f"File {err}")
                        self.failure_msg += f"File restore validation failed for {vm_};"
        except Exception as err:
            self.log.error(err)
            self.failure_msg += f"Error in File restore validation {err}"

    def run(self):
        """Main function for test case execution"""

        try:

            self.init_tc()
            VirtualServerUtils.decorative_log(f"Deploy Scale VMs")
            deployed_vm_count = self.deploy_scale_vms(self.tcinputs.get("vm_count", 25))
            if deployed_vm_count < self.tcinputs.get("vm_count", 25):
                raise Exception(f"Only {deployed_vm_count} Vms were deployed Test case will fail")
            time.sleep(240)
            VirtualServerUtils.decorative_log(f"Create VM Groups")
            self.create_vm_groups()
            VirtualServerUtils.decorative_log(f"Powering off all VMs")
            self.power_off_all_vm()
            VirtualServerUtils.decorative_log(f"Backup(FULL)")
            self.perform_backup()
            VirtualServerUtils.decorative_log("Backup(INCREMENTAL)")
            self.perform_backup("INCREMENTAL")
            self.commcell.clients.refresh()
            sc_list = [sc for client in self.clients for sc in
                       self.clients[client].get('auto_subclient_list', [])
                       if sc.subclient_name not in
                       self.clients[client].get("skip_cleanup_sc_list", [])]
            if sc_list:
                sc_list = [*set(random.choices(sc_list, k=4))]
                VirtualServerUtils.decorative_log(f"File Restores")
                self.file_restores(sc_list)
                VirtualServerUtils.decorative_log(f"Full vm restore")
                self.full_vm_restore(sc_list)
            if self.failure_msg:
                raise Exception(self.failure_msg)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp) + self.failure_msg
            self.status = constants.FAILED

        finally:
            self.clean_up()


class BackupThread(threading.Thread):
    """Class for running backups"""

    def __init__(self, sub_client_obj, backup_type="FULL"):
        super().__init__()
        self.sub_client_obj = sub_client_obj
        self.backup_type = backup_type
        self.exception = None

    def run(self):
        try:
            backup_options = OptionsHelper.BackupOptions(self.sub_client_obj)
            backup_options.backup_type = self.backup_type
            self.sub_client_obj.log.info(f"Started backup thread {self.ident} "
                                         f"for sub client :{self.sub_client_obj.subclient_name}"
                                         f" in client : "
                                         f"{self.sub_client_obj.auto_vsaclient.vsa_client_name}")
            self.sub_client_obj.backup(backup_options, skip_discovery=True)

        except Exception as err:
            self.exception = err
