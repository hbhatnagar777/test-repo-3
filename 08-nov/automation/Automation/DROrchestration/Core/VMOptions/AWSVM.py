from VirtualServer.VSAUtils.VMHelpers.AmazonVM import AmazonVM


def format_vm_options(**kwargs):
    return {
        # Basic hardware
        "cpuCount": kwargs.get('cpu_count'),
        "memory": kwargs.get('memory'),
        "diskCount": kwargs.get('disk_count'),
        "nicCount": kwargs.get('nic_count'),

        # AWS - Instance details
        "availability_zone": kwargs.get('availability_zone'),
        "instanceType": kwargs.get('instance_type'),
        "instanceId": kwargs.get('instance_id'),

        # AWS - Network details
        "vpc": kwargs.get('vpc'),
        "subnet": kwargs.get('subnet'),
        "nic": kwargs.get('nic'),
        "security_groups": kwargs.get('security_groups'),

        # AWS - IAM Role
        "iam_role": kwargs.get('iam_role'),

        # AWS - DVDF
        "dvdf": kwargs.get('dvdf', True)
    }


def source_vm_options(source_vm, drvm_options):
    # Basic hardware
    cpu_count = source_vm.no_of_cpu
    memory = source_vm.memory
    disk_count = source_vm.disk_count
    nic_count = len([source_vm.nic]) if isinstance(source_vm.nic, str) else len(source_vm.nic)

    # AWS - Instance details
    availability_zone = source_vm.availability_zone
    instance_type = source_vm.ec2_instance_type
    instance_id = source_vm.guid

    # AWS - Network details
    vpc = next((tag.get('Value') for tag in source_vm.instance.vpc.tags if tag.get('Key') == 'Name'), source_vm.instance.vpc.id)
    subnet = next((tag.get('Value') for tag in source_vm.instance.subnet.tags if tag.get('Key') == 'Name'), source_vm.instance.subnet.id)
    nic = source_vm.nic
    security_groups = [sg.get('GroupName', None) for sg in source_vm.instance.security_groups]

    # AWS - IAM Role
    iam_role = source_vm.iam_role_id

    return format_vm_options(cpu_count=cpu_count, memory=memory, disk_count=disk_count,
                             nic_count=nic_count, availability_zone=availability_zone,
                             instance_type=instance_type, instance_id=instance_id,
                             vpc=vpc, subnet=subnet, nic=nic, security_groups=security_groups,
                             iam_role=iam_role)


def destination_vm_options(source_vm, vm_options, recovery_target):
    # Basic hardware
    cpu_count = None if vm_options.get('advancedRestoreOptions', {}).get('vmSize', None) else source_vm.no_of_cpu
    memory = None if vm_options.get('advancedRestoreOptions', {}).get('vmSize', None) else source_vm.memory
    disk_count = source_vm.disk_count
    nic_count = len(vm_options.get('advancedRestoreOptions', {}).get('nics', []))

    # AWS - Instance details
    availability_zone = vm_options.get('advancedRestoreOptions', {}).get('esxHost')
    instance_type = vm_options.get('advancedRestoreOptions', {}).get('vmSize', None)
    instance_id = vm_options.get('advancedRestoreOptions', {}).get('guid', None)

    # AWS - Network details
    _network = vm_options.get('advancedRestoreOptions', {}).get('nics', [{}])[0].get('networkDisplayName', '')
    vpc = _network.split("\\")[0]
    subnet = _network.split("\\")[1]
    nic = _network.split("\\")[2]
    security_groups = [sg.get('groupName', None) for sg in vm_options.get('advancedRestoreOptions', {}).get('securityGroups', [])]

    # AWS - IAM Role
    iam_role = vm_options.get('advancedRestoreOptions', {}).get('roleInfo', {}).get('id') \
        if vm_options.get('advancedRestoreOptions', {}).get('roleInfo', None) \
        else (source_vm.iam_role_id if hasattr(source_vm, 'iam') else None)

    # AWS - DVDF
    dvdf = vm_options.get('createVmsDuringFailover', True)

    return format_vm_options(cpu_count=cpu_count, memory=memory, disk_count=disk_count,
                             nic_count=nic_count, availability_zone=availability_zone,
                             instance_type=instance_type, instance_id=instance_id,
                             vpc=vpc, subnet=subnet, nic=nic, security_groups=security_groups,
                             iam_role=iam_role, dvdf=dvdf)


def test_failover_vm_options(source_vm, drvm_options, recovery_target):
    # AWS - Instance details
    availability_zone = drvm_options.get('advancedRestoreOptions', {}).get('esxHost')
    instance_type = drvm_options.get('advancedRestoreOptions', {}).get('testFailoverVmSize')
    instance_id = None

    # Basic hardware
    cpu_count = None if instance_type else source_vm.no_of_cpu
    memory = None if instance_type else source_vm.memory
    disk_count = source_vm.disk_count
    nic_count = len(drvm_options.get('advancedRestoreOptions', {}).get('testFailoverNics', []))

    # AWS - Network details
    _network = drvm_options.get('advancedRestoreOptions', {}).get('testFailoverNics', [{}])[0].get('networkDisplayName', '')
    vpc = _network.split("\\")[0]
    subnet = _network.split("\\")[1]
    nic = _network.split("\\")[2]
    security_groups = [sg.get('groupName', None) for sg in drvm_options.get('advancedRestoreOptions', {}).get('testFailoverSecurityGroups')]

    # AWS - IAM Role
    iam_role = drvm_options.get('advancedRestoreOptions', {}).get('roleInfo', {}).get('id') \
        if drvm_options.get('advancedRestoreOptions', {}).get('roleInfo', None) \
        else (source_vm.iam_role_id if hasattr(source_vm, 'iam') else None)

    return format_vm_options(cpu_count=cpu_count, memory=memory, disk_count=disk_count,
                             nic_count=nic_count, availability_zone=availability_zone,
                             instance_type=instance_type, instance_id=instance_id,
                             vpc=vpc, subnet=subnet, nic=nic, security_groups=security_groups,
                             iam_role=iam_role)
