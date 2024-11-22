"""
Main file  for declaring all constants needed for  VSA Automation
"""

import os
from enum import Enum
from AutomationUtils import constants

APP_TYPE = 106
Ip_regex = "(^169\.)"
AppName = "VIRTUAL SERVER"
PROBLEMATIC_TESTDATA_FOLDER = "ProblematicData"
AutomationAppType = "Q_VIRTUAL_SERVER"
PseuDoclientPropList = 'Virtual Server Host', 'Virtual Server User'
vm_pattern_names = {'[OS]': 'GuestOS',
                    '[DNS]': 'server_name',
                    '[DS]': 'Datastore',
                    '[VM]': 'vm_name',
                    '[HN]': 'server_clientname',
                    '[Tag]': 'tag',
                    '[TagCategory]': 'tagcategory',
                    '[VMName]': 'vm_name',
                    '[Virtual Machine]': 'vm_name'}

filter_type_mapping = {
    "gcp": {
        "server": "zone",
        "datacenter": "region"
    },

    "azure stack": {
        "datastore": "storage_account",
        "tagcategory": "tag_name",
        "tag": "tag_value",
        "server": "resource_group"
    },

    "hyper-v": {
        "server": ""
    },

    "azure resource manager": {
        "tagcategory": "tag_name",
        "tag": "tag_value",
        "datacenter": "location",
        "server": "resource_group"
    }

}

JM_Failure_Reason = {
    'DiskFilter': 'All disks were filtered'}

content_types = {'Virtual Machine': "[VM]", '1': "[HN]", 'Tag': "[Tag]", 'TagCategory': "[TagCategory]"}
disk_count_command = "(get-disk | select number, size).count"

attr_name = ('Virtual Server User', 'Virtual Server Password', 'Amazon Center Access Key',
             'Amazon Center Secret Key', 'Virtual Server Host', 'Azure Subscription Id', 'Azure Tenant Id',
             'Oracle Cloud Infrastructure Tenancy Id', 'Oracle Cloud Infrastructure User Id',
             'Oracle Cloud Infrastructure Finger Print', 'Oracle Cloud Infrastructure Private File Name',
             'Oracle Cloud Infrastructure Private Key Password', 'Oracle Cloud Infrastructure Region Name',
             'Virtual Server Credential Assoc Id', 'Amazon Admin Instance Id', 'Alibaba Cloud Access Key',
             'Alibaba Cloud Secret Key')

pruning_constants = {"min_percentage_limit": 10, "min_available_limit": 100000}

# This options_mapping is meant to act as a bridge between
# OptionsHelper classes VirtualServerHelper classes.
# The keys represent destination attributes in OptionsHelper, that need to be populated.
# And the values represent the source attributes in VirtualServerHelper.

options_mapping = {'overwrite': 'unconditional_overwrite',
                   'in_place': 'full_vm_in_place',
                   'power_on': 'power_on_after_restore',
                   'restoreAsManagedVM': 'managed_vm',
                   'createPublicIP': 'create_public_ip',
                   'Resource_Group': 'resource_group',
                   'volume_type': 'volumetype',
                   'av_zone': 'availability_zone',
                   'security_groups': 'security_group',
                   'Storage_account': 'storage_account',
                   '_browse_ma_client_name': '_browse_ma',
                   'dest_client_hypervisor': 'restore_destination_client',
                   'host': 'destination_host',
                   'datastore': 'destination_datastore',
                   'disk_filters': 'vm_group_disk_filters'}

backup_options_mapping = {'backup_job': 'backup_job_obj'}

WINDOWS_ATTACH_DISK_FOR_OCI_INSTANCE = os.path.join(
    constants.AUTOMATION_UTILS_PATH, 'Scripts', 'WINDOWS', 'AttachDisksOci.ps1')

AZURE_RESOURCE_MANAGER_URL = "https://management.azure.com/"

AZURE_API_VERSION = "?api-version=2021-08-01"

AZURE_AUTO_VM_CONFIG = {'tags': {'vm': {'all_vm': False, 'validate': True},
                                 'nic': {'all_vm': False, 'validate': True},
                                 'disk': {'all_vm': False, 'all_disk': True, 'validate': True},
                                 'validate': True,
                                 'all_tags': True},
                        'disk_encryption': {'disk_encryption_type': 'EncryptionAtRestWithCustomerKey',
                                            'all_disk': True, 'validate': False},
                        'availability_zone': {'all_vm': False, 'validate': True},
                        'proximity_placement_group': {'all_vm': False, 'validate': True},
                        'vm_encryption_info': {'all_vm': False, 'validate': False}
                        }

VCLOUD_API_HEADER = {'Accept': 'application/*;version=39.0'}
VCLOUD_API_HEADER_JSON = {'Accept': 'application/*+json;version=39.0'}

"""str:  Attach secondary disks to oci vm """

constant_log = {
    'test_data_copy': 'Testdata copy failure on vm:%s on drive:%s'
}


def vcloud_vm_status(status_code):
    """
    Enum Function for status codes of vCloud VMs
    """
    vcloud_status_code = {
        -1: "Could not be created",
        0: "Unresolved",
        1: "Resolved",
        2: "Deployed",
        3: "Suspended",
        4: "Powered on",
        5: "Waiting for user input",
        6: "Unknown state",
        7: "Unrecognized state",
        8: "Powered off",
        9: "Inconsistent state",
        10: "Children do not all have the same status",
        11: "Upload initiated, OVF descriptor pending",
        12: "Upload initiated, copying contents",
        13: "Upload initiated , disk contents pending",
        14: "Upload has been quarantined",
        15: "Upload quarantine period has expired"
    }

    return vcloud_status_code[int(status_code)]


class hypervisor_type(Enum):
    """
    Enum class for declaring allt he Hypervior types
    """

    VIRTUAL_CENTER = "VMware"
    MS_VIRTUAL_SERVER = "Hyper-V"
    AZURE = "Azure"
    AZURE_V2 = "Azure Resource Manager"
    MICROSOFT_AZURE = "Microsoft Azure"
    Fusion_Compute = "FusionCompute"
    ORACLE_VM = "OracleVM"
    Alibaba_Cloud = "Alibaba Cloud"
    Oracle_Cloud_Classic = "Oracle Cloud"
    Google_Cloud = "Google Cloud Platform"
    OPENSTACK = "OpenStack"
    Azure_Stack = "Azure Stack"
    Rhev = "Red Hat Virtualization"
    AMAZON_AWS = "Amazon Web Services"
    ORACLE_CLOUD_INFRASTRUCTURE = "Oracle Cloud Infrastructure"
    Vcloud = "vCloud Director"
    Nutanix = "Nutanix AHV"
    Xen = "Xen"


class HypervisorDisplayName(Enum):
    """
    Enum class for Hypervisor display names on command center
    """
    VIRTUAL_CENTER = "VMware vCenter"
    MS_VIRTUAL_SERVER = "Microsoft Hyper-V"
    MICROSOFT_AZURE = "Microsoft Azure"
    Alibaba_Cloud = "Alibaba Cloud"
    ORACLE_CLOUD_INFRASTRUCTURE = "Oracle Cloud Infrastructure"
    AMAZON_AWS = "Amazon Web Services"
    Azure_Stack = "Microsoft Azure Stack"
    Google_Cloud = "Google Cloud Platform"
    OPENSTACK = "OpenStack"
    Rhev = "Red Hat Virtualization"
    Vcloud = "VMware Cloud Director"
    Nutanix = "Nutanix AHV"
    ORACLE_VM = "Oracle VM"
    XEN_SERVER = "Xen Server"
    FUSIONCOMPUTE = "Fusion Compute"


def on_premise_hypervisor(instance_name):
    """
    :param instance_name:  Instance name of the Instance need to be checked
    :return:
        True if the Hypervisor is on premise else false

    """
    vendor = {'vmware': True, 'hyper-v': True, 'azure resource manager': False, 'Azure': False,
              'fusioncompute': False, 'oraclevm': True, 'red hat virtualization': True,
              'amazon web services': False, 'openstack': False, 'nutanix ahv': False, 'alibaba cloud': False,
              'oraclecloud': False, 'google cloud platform': False,
              'oracle cloud infrastructure': False, 'vcloud director': True, 'xen': True, 'kubernetes': False}
    return vendor[instance_name]


def azure_cloud_hypervisor(instance_name):
    """
    :param instance_name:  Instance name of the Instance need to be checked
    :return:
        True if the Azure specific Hypervisor else false

    """
    vendor = {'vmware': False, 'hyper-v': False, 'azure resource manager': True,
              'Azure': True, 'fusioncompute': False, 'oraclevm': False, 'azure stack': True,
              'red hat virtualization': False, 'openstack': False, 'alibaba cloud': True,
              'oraclecloud': True, 'amazon web services': False, 'nutanix ahv': False,
              'google cloud platform': False, 'oracle cloud infrastructure': False, 'xen': False, 'kubernetes': False}

    return vendor[instance_name]


def instance_helper(instance_name):
    """

    Args:
        instance_name          (str): Name of the instance

    Returns:
                                (str): Helper of the instance
    """
    helper = {
        'vmware': 'VmwareHelper',
        'hyper-v': 'HyperVHelper',
        'azure resource manager': 'AzureHelper',
        'azure stack': 'AzureStackHelper',
        'fusioncompute': 'FusionComputeHelper',
        'oraclevm': 'OracleVMHelper',
        'oracle cloud': 'OracleCloudHelper',
        'google cloud platform': 'GoogleCloudHelper',
        'openstack': 'OpenStackHelper',
        'red hat virtualization': 'RedHatHelper',
        'amazon web services': 'AmazonHelper',
        'oracle cloud infrastructure': 'OciHelper',
        'vcloud director': 'VcloudHelper',
        'nutanix ahv': 'NutanixHelper',
        'alibaba cloud': 'AliCloudHelper',
        'xen': 'XenHelper',
        'Kubernetes': 'KubernetesHelper'

    }
    return helper.get(instance_name)


def instance_vmhelper(instance_name):
    """

    Args:
        instance_name          (str): Name of the instance

    Returns:
                                (str): VM Helper of the instance
    """
    vm_helper = {
        'vmware': 'VmwareVM',
        'hyper-v': 'HyperVVM',
        'azure resource manager': 'AzureVM',
        'azure stack': 'AzureStackVM',
        'fusioncompute': 'FusionComputeVM',
        'oraclevm': 'OracleVMVM',
        'oracle cloud': 'OracleCloudVM',
        'google cloud platform': 'GoogleCloudVM',
        'openstack': 'OpenStackVM',
        'red hat virtualization': 'RedHatVM',
        'amazon web services': 'AmazonVM',
        'oracle cloud infrastructure': 'OciVM',
        'vcloud director': 'VcloudVM',
        'nutanix ahv': 'NutanixVM',
        'alibaba cloud': 'AliCloudVM',
        'xen': 'XenVM'
    }
    return vm_helper.get(instance_name)


def is_dynamic_type(vm_name, vm_type):
    """
    check whether the VM string passed contain dynamic VM

    Args:
            vm_name: name of the VM eg: VM1, VM*
            vm_type  : Type of the Input like VM name, HostName

    Returns:
            Bool value based on dynamic or not
    """

    is_not_dynamic = False
    vm_name_type = ['9', '10']
    if vm_type in vm_name_type:
        if '*' not in vm_name:
            is_not_dynamic = True

    return is_not_dynamic


def is_windows(os_name):
    """
    check for the os in Windows or Unix flavours

    Args:
    os_name - Nmae of the OS

    returns:
            bool value based whether the OS is windows or not
    """
    return bool(os_name == "windows")


def get_live_browse_db_path(base_dir):
    """
    Get the db path for the live browse
    Args:
            base_dir - base directory where the contentstore is installed

    return:


    """

    return os.path.join(base_dir, "PseudoMount", "Persistent", "PseudoMountDB")


def get_live_browse_mount_path(base_dir, GUID, os_name):
    """
    Get the devices mount path for the live browse
    Args:
            base_dir            (str): base directory where the contentstore is installed

            GUID                (str): GUID of the VM browsed

            os_name             (str): OS of the VM

    return:
        devices mount path for the live browse

    """

    if os_name.lower() == "windows":
        return os.path.join(base_dir, "PseudoMount", "Persistent", "PseudoDevices", GUID)

    else:
        return "/opt/FBR/cvblk_mounts"


def get_linux_live_browse_mount_path(ma_machine, adr_id):
    """
    Get the devices mount path for the linux MA live browse
    Args:
            ma_machine          (obj): Machine object of the MA

            adr_id              (str): Attach disk request id for Live Browse

    return:
        devices mount path for the live browse

    """

    lsblk_output = ma_machine.execute_command('''lsblk | grep cvblk_mounts''')
    live_browse_mount_path = ""
    if adr_id in lsblk_output.output:
        lines = lsblk_output.output.strip().split('\n')
        for line in lines:
            if adr_id in line:
                wp = line.split(' ')[-1]  # will give whole path including mounted disk
                live_browse_mount_path = wp[:wp.find(adr_id)]  # extract parent path upto cvblk_mounts
                break
    return live_browse_mount_path


def get_folder_to_be_compared(folder_name, _driveletter, timestamp):
    """
    return the default folder restore path
    Args:
            FolderName - name of the folder
            _driveletter- drive letter where data was copied
            timestamp - timestamp used durnig copying data

    """

    if _driveletter is None:
        return "C:\\TestData\\{0}\\".format(folder_name)
    else:
        return os.path.join(_driveletter, "\\" + folder_name, "TestData", timestamp)


def BrowseFilters():
    """
    :return: Browse Filters for XML
    """
    return r"""&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;databrowse_Query type="0"
    queryId="0"&gt;&lt;dataParam&gt;&lt;sortParam ascending="1"&gt;&lt;sortBy val="38"
    /&gt;&lt;sortBy val="0" /&gt;&lt;/sortParam&gt;&lt;paging firstNode="0" pageSize="100"
    skipNode="0" /&gt;&lt;/dataParam&gt;&lt;/databrowse_Query&gt;"""


def filter_cv_tags(tags):
    """
    Filters out the Commvault generated Tags at source
    """
    filters = ['_GX_AMI_', '_COMMVAULT_GXMD_SNAP_', '_CV_REPLICATION_DISK_GUID_', '_GX_BACKUP_', 'CV_Integrity_Snap',
               'CV-SubclientId', 'Last Backup', 'CV-CreatedByJobId']
    for key in list(tags):
        if key in filters:
            tags.pop(key)
    return tags


class ServiceIds(Enum):
    """
    Using enum class create enumerations
    """
    Restart = 1
    Start = 2
    Stop = 3
    Suspend = 4


class ServiceOperationEntity(Enum):
    """
    Using enum class create enumerations
    """
    Co_ordinator = 1
    Worker = 2
    MA = 3
    Other = 4


class CommcellEntityIds(Enum):
    """
    Using enum class create enumerations
    """
    CLIENTSTATUS = 1
    BACKUPSETSTATUS = 2
    JOBSTATUS = 3


class CommcellEntity(Enum):
    """
    Using enum class create enumerations
    """
    Backupset = 1
    client = 2
    job = 3
    Other = 4


class DrOperation(Enum):
    """
        Using enum class create enumerations
        """
    PlannedFailover = 1
    UnplannedFailover = 2
    Failback = 3
    UndoFailover = 4


class LogFilesMapper(Enum):
    """ Mapping type of job with log file"""
    Backup = 'vsbkp.log'
    Restore = 'vsrst.log'


class SmbRestoreChecks(Enum):
    """
    Using enum class to create enumerations
    """
    smbsupportcheck = 1
    smbapproachcheck = 2
    vmwaretoolcheck = 3
    passwordcheck = 4
    performancecheck = 5


class RestoreType(Enum):
    """
    Using enum class to create enumerations
    """
    GUEST_FILES = 0
    FULL_VM = 1


class VMBackupType(Enum):
    """
    Using enum class to create enumerations
    """
    APP_CONSISTENT = 'File system and application consistent'
    CRASH_CONSISTENT = 'Crash consistent'
    INHERITED = 'Inherited from VM group'


class RestorePointConstants(Enum):
    """
    String to form restore point collections name and restore points name
    """
    COLLECTION_STRING = 'GX_BACKUP_RPC_'
    STREAMING_RESTOREPOINT = 'GX_BACKUP_RPT_'
    SNAP_RESTOREPOINT = 'GX_SNAP_RPT_'
    CRASH_CONSISTENT = 'CrashConsistent'
    APP_CONSISTENT_WIN = 'ApplicationConsistent'
    APP_CONSISTENT_LINUX = 'FileSystemConsistent'

common_web_restore_option_mapping = {
    'overwrite': 'unconditional_overwrite',
    'in_place': 'full_vm_in_place',
    'power_on': 'power_on_after_restore',
    '_browse_ma_client_name': '_browse_ma',
    'dest_client_hypervisor': 'restore_destination_client',
    'host': 'destination_host',
    'disk_filters': 'vm_group_disk_filters'}

hypervisor_vm_web_restore_option_mapping = {
    hypervisor_type.AZURE_V2.value.lower(): {
        'restoreAsManagedVM': 'managed_vm',
        'createPublicIP': 'create_public_ip',
        'Resource_Group': 'resource_group',
        'availability_zone': 'availability_zone',
        'security_groups': 'security_group',
        'Storage_account': 'storage_account',
        'subnet_id': 'network_interface',
        'region': 'region',
        'disk_option': 'disk_type',
        'disk_encryption_type': 'disk_encryption_type',
        'vm_size': 'vm_size',
        'vm_tags': 'vm_tags',
        'disk_tags': 'tags_validation',
        'azure_key_vault': 'azure_key_vault',
        'extensions': 'extensions'
    },
    hypervisor_type.VIRTUAL_CENTER.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Fusion_Compute.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.ORACLE_VM.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Alibaba_Cloud.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Oracle_Cloud_Classic.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Google_Cloud.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.OPENSTACK.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Azure_Stack.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Rhev.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.AMAZON_AWS.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Vcloud.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Nutanix.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    },
    hypervisor_type.Xen.value.lower(): {
        'volume_type': 'volumetype',
        'datastore': 'destination_datastore'
    }
}


preset_hypervisor_vm_restore_options = {
    hypervisor_type.AZURE_V2.value.lower(): {
        "vm_gen": "vm_gen",
        "proximity_placement_group": "proximity_placement_group",
        "vm_guid": "vm_guid"
    },
    hypervisor_type.VIRTUAL_CENTER.value.lower(): {},
    hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): {},
    hypervisor_type.AZURE.value.lower(): {},
    hypervisor_type.MICROSOFT_AZURE.value.lower(): {},
    hypervisor_type.Fusion_Compute.value.lower(): {},
    hypervisor_type.ORACLE_VM.value.lower(): {},
    hypervisor_type.Alibaba_Cloud.value.lower(): {},
    hypervisor_type.Oracle_Cloud_Classic.value.lower(): {},
    hypervisor_type.Google_Cloud.value.lower(): {},
    hypervisor_type.OPENSTACK.value.lower(): {},
    hypervisor_type.Azure_Stack.value.lower(): {},
    hypervisor_type.Rhev.value.lower(): {},
    hypervisor_type.AMAZON_AWS.value.lower(): {},
    hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower(): {},
    hypervisor_type.Vcloud.value.lower(): {},
    hypervisor_type.Nutanix.value.lower(): {},
    hypervisor_type.Xen.value.lower(): {}
}


def get_restore_option_mapping(instance_type):
    """
    Provides the combined available common web restore options and the hypervisor specific options.
    Args:
        instance_type (str): The hypervisor instance type (e.g., "Azure Resource Manager").

    Returns:
        dict: A dictionary containing the combined restore options for the specified instance type.
    """
    return {**common_web_restore_option_mapping,
            **hypervisor_vm_web_restore_option_mapping.get(instance_type.lower(), {})
            }


vsa_common_pre_backup_config_checks = {
    "min_proxy_os": {"count": 2, "os_list": ["windows", "unix"], "validate": True},
    "ma_os": {"count": 2, "os_list": ["unix", "windows"], "validate": False},
    "min_vm_count": {"count": 2, "validate": True},
    "min_vm_os": {"os_list": ["windows", "unix"], "validate": True},
    "min_disks_count": {"all_vm": True, "count": 2, "validate": True}
}

hypervisor_pre_backup_config_checks = {
    hypervisor_type.AZURE_V2.value.lower(): {
                        'tags': {
                            'vm': {'all_vm': False, 'validate': True},
                            'nic': {'all_vm': False, 'validate': True},
                            'disk': {'all_vm': False, 'all_disk': True, 'validate': True},
                            'validate': True,
                            'all_tags': True},
                        'multiple_disk_encryption': {'all_vm': False, 'validate': True},
                        'availability_zone': {'all_vm': False, 'validate': True},
                        'proximity_placement_group': {'all_vm': False, 'validate': True},
                        'vm_encryption_info': {'all_vm': False, 'validate': True},
                        'disk_in_multiple_rg': {'all_vm': False, 'validate': True},
                        'sku': {'all_vm': False, 'validate': True},
                        'disk_in_multiple_storage_account': {'all_vm': False, 'validate': True},
                        'generation': {'validate': True},
                        'extensions': {'all_vm': False, 'validate': True},
                        'multiple_vm_architecture': {'validate': True},
                        'multiple_security_type': {'validate': True},
                        'secure_boot': {'all_vm': False, 'validate': True},
                        "min_proxy_os": {"count": 2, "os_list": ["unix"],
                                         "validate": True},
                        "sys_assigned_identity": {"validate": True},
                        "usr_assigned_identity": {"validate": True},
                        "ma_os": {"count": 2, "os_list": ["unix"], "validate": True}

                        },
    hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): {
        "min_proxy_os": {"count": 2, "os_list": ["windows"], "validate": True}
    }

}


def get_pre_backup_validation_checks(instance_type):
    """
        Provides the combined common and hypervisor specific pre-backup configuration checks.
        Args:
            instance_type (str): The hypervisor instance type (e.g., "Azure Resource Manager").

        Returns:
            dict: A dictionary containing the combined restore options for the specified instance type.
    """
    return {**vsa_common_pre_backup_config_checks,
            **hypervisor_pre_backup_config_checks.get(instance_type.lower(), {})}
