from VirtualServer.VSAUtils.VMHelpers.AzureVM import AzureVM


def source_vm_options(source_vm, drvm_options):
    # For source VM options, the source VM is always AzureVM
    disk_dict = {}
    reverse_lun_map = {disk_name: disk_lun for disk_lun, disk_name in source_vm.disk_lun_dict.items()}
    for disk_name in source_vm.disk_dict:
        disk_dict[disk_name] = {
            "uri": source_vm.disk_dict[disk_name],
            "size": source_vm.disk_size_dict[disk_name],
            "sku": source_vm.disk_sku_dict[reverse_lun_map[disk_name]]['storageAccountType'] if source_vm.managed_disk else None,
            "isManaged": source_vm.managed_disk,
            "lun": reverse_lun_map[disk_name]
        }

    return {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "disks": disk_dict,
        "nicCount": source_vm.nic_count,
        "resourceGroup": source_vm.resource_group_name,
        "region": source_vm.region,
        "availabilityZone": source_vm.availability_zone,
        "vmSize": source_vm.vm_size,
        "virtualNetworks": [nic.get('subnet_uri') for nic in source_vm.nic_details],
        "networkSecurityGroups": [nic.get('nsg_uri') for nic in source_vm.nic_details],
        "createPublicIp": [bool(nic.get('public_ip_uri')) for nic in source_vm.nic_details],
        "restoreAsManagedVM": source_vm.managed_disk,
    }


def destination_vm_options(source_vm, vm_options, recovery_target):
    vm_name = vm_options.get('advancedRestoreOptions', {}).get('newName', '')
    resource_group_name = vm_options.get('advancedRestoreOptions', {}).get('esxHost')
    storage_account_name = vm_options.get('advancedRestoreOptions', {}).get('Datastore')
    restore_managed_vm = vm_options.get('advancedRestoreOptions', {}).get('restoreAsManagedVM', False)

    disk_dict = {}
    # If VM is restore as managed, send disk type, size, SKU information to VSA layers for validation
    if restore_managed_vm:
        if vm_options.get('advancedRestoreOptions', {}).get('volumeType') != 'Auto':
            # If disk type is not Auto, take disk type from override options
            disk_type = vm_options.get('advancedRestoreOptions', {}).get('volumeType')
        else:
            # If disk type is Auto and source VM is Azure, set disk type to None
            # This is because we will match disk types for each disk
            # If disk type is Auto and source VM is not Azure, all disks should be standard HDD
            disk_type = None

        if isinstance(source_vm, AzureVM):
            # If source VM is Azure, pass down disk size, SKU and type
            # Disk URI is missing, since we cannot get the disk URLs pre-emptively. So, we will pass down metadata only
            # and then look at all disks attached to VM
            # For managed VM with
            reverse_lun_map = {disk_name: disk_lun for disk_lun, disk_name in source_vm.disk_lun_dict.items()}
            for disk_name in source_vm.disk_dict:
                # If disk type is None, that means that Auto select disk is selected
                # so disk SKU for each disk is passed
                # Otherwise, disk_type contains the disk information
                if disk_type is None:
                    disk_sku = (source_vm.disk_sku_dict.get(disk_name, {})
                                .get('storageAccountType', AzureVM.DISK_SKU_NAMES["Standard HDD"]))
                else:
                    disk_sku = disk_type
                disk_dict[disk_name] = {
                    "uri": None,
                    "size": source_vm.disk_size_dict[disk_name],
                    "sku": disk_sku,
                    "isManaged": restore_managed_vm,
                    "lun": reverse_lun_map[disk_name]
                }
        else:
            # If source VM is non-Azure, pass only SKU and type
            # Disk URI is missing, since we cannot get the disk URLs pre-emptively. So, we will pass down metadata only
            # and then look at all disks attached to VM
            # Disk size validations requires a common interface to get disk sizes in GB for all vendors
            for disk_idx in range(source_vm.disk_count):
                # When disk type is Auto for cross-hypervisor, disk is Standard HDD
                if disk_type is None:
                    disk_sku = AzureVM.DISK_SKU_NAMES["Standard HDD"]
                else:
                    disk_sku = disk_type
                if disk_idx == 0:
                    disk_dict["OsDisk"] = {
                        "uri": None,
                        "size": None,
                        "sku": disk_sku,
                        "isManaged": restore_managed_vm,
                        "lun": disk_idx - 1
                    }
                else:
                    disk_dict[f"DataDisk_{disk_idx}"] = {
                        "uri": None,
                        "size": None,
                        "sku": disk_sku,
                        "isManaged": restore_managed_vm,
                        "lun": disk_idx - 1
                    }
    if not restore_managed_vm or vm_options.get('deployVmWhenFailover', False):
        # If VM is unmanaged or DVDF, send the disk information for DVDF blobs
        # This is because the DVDF and the DRVM disks have the same blobs in case of unmanaged VMs
        storage_account_url = f'https://{storage_account_name.lower()}.blob.core.windows.net/vhds/'
        base_name = f'{resource_group_name.lower()}-{vm_name.lower()}'
        for disk_idx in range(source_vm.disk_count):
            if disk_idx == 0:
                # OS disk(first disk) doesn't have any suffix index. eg: rgname-vmname.vhd
                disk_dict[base_name + '.vhd'] = {
                    "uri": storage_account_url + base_name + '.vhd',
                    "size": None,
                    "sku": None,
                    "isManaged": False,
                    "lun": disk_idx - 1
                }
            else:
                # All data disks have suffix index. eg: rgname-vmname-2.vhd
                disk_dict[base_name + f'-{disk_idx}.vhd'] = {
                    "uri": storage_account_url + base_name + f'-{disk_idx}.vhd',
                    "size": None,
                    "sku": None,
                    "isManaged": False,
                    "lun": disk_idx - 1
                }

    return {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "disks": disk_dict,
        "nicCount": 1,
        "resourceGroup": resource_group_name,
        "region": vm_options.get('advancedRestoreOptions', {}).get('datacenter'),
        "availabilityZone": (vm_options.get('advancedRestoreOptions', {}).get('availabilityZones')
                             if vm_options.get('advancedRestoreOptions', {}).get('availabilityZones') != 'Auto'
                             else (source_vm.availability_zone if isinstance(source_vm, AzureVM) else None)
                             ),
        "vmSize": (vm_options.get('advancedRestoreOptions', {}).get('vmSize')
                   if vm_options.get('advancedRestoreOptions', {}).get('vmSize') != 'Auto'
                   else (source_vm.vm_size if isinstance(source_vm, AzureVM) else None)
                   ),
        "virtualNetworks": ([nic.get('subnetId')
                             for nic in vm_options.get('advancedRestoreOptions', {}).get('nics', [{}])
                             if nic.get('subnetId')]
                            or ([nic.get('subnet_uri') for nic in source_vm.nic_details]
                                if isinstance(source_vm, AzureVM) else None)),
        "networkSecurityGroups": ([nsg.get('groupId')
                                   for nsg in vm_options.get('advancedRestoreOptions', {}).get('securityGroups', [{}])
                                   if nsg.get('groupId')]
                                  or ([nic.get('nsg_uri') for nic in source_vm.nic_details]
                                      if isinstance(source_vm, AzureVM) and source_vm.nic_details else None)),
        "createPublicIp": [vm_options.get('advancedRestoreOptions', {}).get('createPublicIp', False)],
        "restoreAsManagedVM": restore_managed_vm,
    }


def test_failover_vm_options(source_vm, drvm_options, recovery_target):
    if drvm_options.get('createVmsDuringFailover', False):
        # If the group is warm site, the test failover VM disk is same type as set on target
        restore_managed_vm = recovery_target.restore_as_managed_vm
    else:
        # For hot site, disk is always managed
        restore_managed_vm = True

    if drvm_options.get('createVmsDuringFailover', False) and not restore_managed_vm:
        # When warm sync is enabled and restore as managed VM is False, disk type is None
        disk_type = None
    elif drvm_options.get('advancedRestoreOptions', {}).get('volumeType') != "Auto":
        # When disk type is not Auto on recovery target, take from recovery target
        disk_type = drvm_options.get('advancedRestoreOptions', {}).get('volumeType')
    else:
        # If disk type is not set on recovery target, the disk type is always standard HDD
        disk_type = AzureVM.DISK_SKU_NAMES["Standard HDD"]

    # TODO: Add support for cross-hypervisor
    disk_dict = {}
    reverse_lun_map = {disk_name: disk_lun for disk_lun, disk_name in source_vm.disk_lun_dict.items()}
    for disk_name in source_vm.disk_dict:
        disk_dict[disk_name] = {
            "uri": None,
            "size": source_vm.disk_size_dict[disk_name],
            "sku": disk_type,
            "isManaged": restore_managed_vm,
            "lun": reverse_lun_map[disk_name]
        }
    return {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "disks": disk_dict,
        "nicCount": 1,
        "resourceGroup": drvm_options.get('advancedRestoreOptions', {}).get('esxHost'),
        "region": drvm_options.get('advancedRestoreOptions', {}).get('datacenter'),
        "availabilityZone": drvm_options.get('advancedRestoreOptions', {}).get('availabilityZones'),
        "createPublicIp": [drvm_options.get('advancedRestoreOptions', {}).get('createPublicIp', False)],
        "restoreAsManagedVM": restore_managed_vm,
        "vmSize": recovery_target.test_vm_size,
        "virtualNetworks": [nic.get('subnetNames', [{}])[0].get('subnetId')
                            for nic in recovery_target._recovery_target_properties.get('networkInfo', [])],
        "networkSecurityGroups": [nic.get('groupId') for nic in
                                  drvm_options.get('advancedRestoreOptions', {}).get('securityGroups', [{}])],
    }
