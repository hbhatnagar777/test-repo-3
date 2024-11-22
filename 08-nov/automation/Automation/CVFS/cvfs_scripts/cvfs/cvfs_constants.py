"""This module contains all the constants used by the modules in cvfs package."""


class CVFSConstants:  # pylint: disable=too-few-public-methods
    """This class contains all the constants used in the script."""

    # Java Constants
    SSTABLE_DUMP_CLASS_NAME = "SSTableDumpCustom"
    SSTABLE_DUMP_JAVA_SRC = """
package com.quexascale.quexablock.utils;
import java.io.IOException;
import com.quexascale.quexablock.common.QuexaBlockHelper;
import com.quexascale.quexablock.io.SSTable;
import com.quexascale.quexablock.io.SSTableNameParser;
public class {SSTABLE_DUMP_CLASS_NAME} {
    public static void main(String[] args)
    {
        if (args.length == 0)
        {
            System.out.println("usage: SSTableDump <SSTableFiles>");
            return ;
        }
		for (int i = 0; i < args.length; ++i) {
			try
			{
				String sstable = args[i];
				String container = SSTableNameParser.getContainer(sstable);
				boolean compressed = false;
				if (QuexaBlockHelper.isMetaContainerVDisk(container))
					compressed = SSTable.isCompressedMetaCtr(sstable);
				else
					compressed = SSTable.isCompressed(sstable);

				SSTable ssTable = new SSTable(args[i], compressed, true);
				ssTable.dump(System.out);
			} catch (Exception e)
			{
				// TODO Auto-generated catch block
				e.printStackTrace();
                System. exit(1);
			}
		}
		System. exit(0);
    }
}
"""

    # CVFS Constants
    SPM_PATH = "/usr/local/hedvig/scripts/spm"
    THRIFT_WRAPPER_PATH = "/usr/local/hedvig/thrift"
    HBLOCK_THRIFT_WRAPPER_MODULE = "hedvig.service.QuexaBlockServer"
    PAGES_THRIFT_WRAPPER_MODULE = "hedvig.pages.service.QuexaBlockDiscoveryServer"
    SPM_MODULE = "spmcommon"
    PAGES_THRIFT_PORT = 15000
    HBLOCK_THRIFT_PORT = 8000
    HBLOCK_SERVICE_NAME = "QuexaBlockService"
    NFS_FILE_PREFIX = "NFSFILE_"
    RF3_SECONDARY_FOR_EC_PREFIX = "RF3SecondaryForEC"
    NFS_FILE_RF3_SECONDARY_FOR_EC_PREFIX = (
        f"{NFS_FILE_PREFIX}{RF3_SECONDARY_FOR_EC_PREFIX}"
    )
    RPC_TIMEOUT_IN_MS = 30000
    PAGES_QUERY_BATCH_SIZE = 1000
    FILE_ATTRS_CACHE_SIZE = 1000000  # 1M
    BLOCK_SIZE_64KB = 65536  # 64KB
    ROOT_INODE = 1
    HEDVIG_DATA_MOUNT_PREFIX = "/hedvig/d"

    # SSH Constants
    SSH_USER = "root"
    SSH_KEYPATH = "/root/.ssh/id_rsa"

    # Connection Pool Constants
    CONNECTION_POOL_SIZE = 4

    # HSX Constants
    NWTYPE_CFG_PATH = (
        "/etc/CommVaultRegistry/Galaxy/Instance001/MediaAgent/.hyperscalenw.cfg"
    )
    CVSECURITY_SCRIPT = "/opt/commvault/MediaAgent/cvsecurity.py"

    # Network Constants
    NETWORK_TYPES = [
        "commServeRegistration",
        "storagePool",
        "management",
        "dataProtection",
    ]
    IPERF_PORT_START = 5201
    IPERF_PORT_END = 5300

    # Node Commands
    GET_NWINT_CMD = "grep -w \"{}\" /etc/CommVaultRegistry/Galaxy/Instance001/MediaAgent/.hyperscalenw.cfg | awk '{{print $1}}'"  # pylint: disable=line-too-long
    GET_NWINT_IP_CMD = (
        "ip addr show {} | grep -w \"inet\" | awk '{{print $2}}'| cut -d'/' -f1"
    )
    GET_USED_PORTS_CMD = "ss -tunlp | awk {'print $5'} | awk -F: '{print $NF}'"
    MKDIR_CMD = "mkdir -p {}"
    START_IPERF_SERVER_CMD = "iperf3 -s --bind {} -p {}  -1 -D"
    START_IPERF_CLIENT_CMD = "iperf3 -c {} --bind {} -p {} --json"
    KILL_IPERF_SERVER_ON_PORT_CMD = (
        "ps -aef | grep -w iperf3 | grep -w {} | awk '{{print $2}}' | xargs kill -9"
    )
    GET_JAVA_PID_FROM_CLASSNAME_CMD = "jps | grep -w {} | awk '{{print $1}}'"
    GET_JAVA_HOME_PID_CMD = (
        "cat /proc/{}/environ | tr '\\0' '\\n' | grep JAVA_HOME | sed 's/JAVA_HOME=//'"
    )
    CHECK_OS_CMD = "grep NAME /etc/os-release"
    GET_OS_NAME_CMD = (
        """grep "^NAME=" /etc/os-release | awk -F "=" {'print $2'} | sed 's/"//g'"""
    )
    GET_OS_VERSION_CMD = (
        """grep "^VERSION=" /etc/os-release | awk -F "=" {'print $2'} | sed 's/"//g'"""
    )
    SCSI_DELETE_CMD = "echo 1 > /sys/block/{}/device/delete"

    # Manage services commands

    HEDVIG_PAGES_SERVICE = "hedvigpages"
    HEDVIG_HPOD_SERVICE = "hedvighpod"
    HEDVIG_HBLOCK_SERVICE = "hedvighblock"
    HEDVIG_FSC_SERVICE = "hedvigfsc"
    COMMVAULT_SERVICE = "commvault"
    SERVICES = [
        HEDVIG_PAGES_SERVICE,
        HEDVIG_HPOD_SERVICE,
        HEDVIG_HBLOCK_SERVICE,
        HEDVIG_FSC_SERVICE,
        COMMVAULT_SERVICE,
    ]
    START_OPERATION = "start"
    STOP_OPERATION = "stop"
    STATUS_OPERATION = "status"
    RESTART_OPERATION = "restart"
    ENABLE_OPERATION = "enable"
    DISABLE_OPERATION = "disable"
    LIST_OPERATION = "list"

    SYSTEMCTL_OPERATIONS = [
        START_OPERATION,
        STOP_OPERATION,
        STATUS_OPERATION,
        RESTART_OPERATION,
        ENABLE_OPERATION,
        DISABLE_OPERATION,
    ]
    SYSTEMCTL_CMD = "systemctl {} {}"
    COMMVAULT_OPERATIONS = [
        START_OPERATION,
        STOP_OPERATION,
        RESTART_OPERATION,
        STATUS_OPERATION,
        LIST_OPERATION,
    ]

    # Cluster CLI Commands
    START_CLI_SCRIPT = "/usr/local/hedvig/scripts/start-cli.sh"
    REPLACE_NVME_CMD = (
        "/opt/hedvig/bin/hv_deploy --replace_hsx_nvme {} --cluster_name {}"
    )
    RHEL_CMD_PREFIX = '{} -c "{}"'
    ROCKY_CMD = "{}; {}"
    CHECK_FIXDISK_FIXED_CMD = f"echo -e 'fix -s\nquit' | {START_CLI_SCRIPT}"
    BLKID_COMMAND = "blkid"
    LS_BLK_DISK_COMMAND = "lsblk | grep disk | awk '{print $1,$7}'"
    WIPE_NVME_CMD = (
        "rm -rf /mnt/d3/data/* /mnt/d4/data/* /mnt/d2/commitlog/* /mnt/d5/data/*"
    )
    ENABLE_DRIVES_SCRIPT = "/usr/local/hedvig/scripts/spm/enable_drives.sh"
    SEARCH_STRING_FOR_FIXDISK_FIXED_SUCCESS = "Fixdisk Fixed"
    SU_ADMIN_CMD = "su - admin"
    EXPORT_HVPUBKEY_CMD = "export HV_PUBKEY=1"
    SELINUX_PAUSE_PROTECTION_CMD = f"{CVSECURITY_SCRIPT} pause_protection"
    SELINUX_RESUME_PROTECTION_CMD = f"{CVSECURITY_SCRIPT} resume_protection"

    # log configuration
    LOG_FORMAT = "%(asctime)s [%(process)d] [%(thread)d] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s"
    LOG_PATH = "/var/log/commvault/Log_Files/cvfs_python_scripts"
    LOGGING_SUPPRESS_MODULES = ["paramiko"]

    # APP or TEMP directory
    APP_TEMP_DIR = "/ws/ddb/cvfs_python_scripts"

    # File Constants
    DEFAULT_ENCODING = "utf-8"

    # Miscellaneous
    THREAD_SLEEP_TIME = 60  # 60 seconds
