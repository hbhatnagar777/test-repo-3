"""This module is used to represent the hblock node, its properties and functions.
    Refer qbserver.thrift, qbpages.thrift, qbcommon.thrift in hedvig/cvfs respository for the thrift definitions.
"""

import logging

from .connections import ThriftConnection
from .cvfs_constants import CVFSConstants
from .cvfs_node import CVFSNode


class HBlockNode(CVFSNode):
    """This class is used to represent the hblock node."""

    def __init__(
        self,
        hostname,
        connection_pool_size=CVFSConstants.CONNECTION_POOL_SIZE,
        user_name=CVFSConstants.SSH_USER,
        key_filename=CVFSConstants.SSH_KEYPATH,
    ):
        """Initialize the HBlockNode object with the provided parameters.
        Args:
            hostname (str): The hostname of the hblock node.
            connection_pool_size (int): The size of the Thrift and SSH connection pool.
                default: CVFSConstants.CONNECTION_POOL_SIZE
            user_name (str): The username to connect to the hblock node.
                default: CVFSConstants.SSH_USER
            key_filename (str): The path to the SSH private key file.
                default: CVFSConstants.SSH_KEYPATH
        """
        super().__init__(
            hostname=hostname,
            connection_pool_size=connection_pool_size,
            user_name=user_name,
            key_filename=key_filename,
        )

        self.__log = logging.getLogger(__name__)
        self.__hblock_thrift_client = ThriftConnection(
            host=self.hostname,
            port=CVFSConstants.HBLOCK_THRIFT_PORT,
            module_name=CVFSConstants.HBLOCK_THRIFT_WRAPPER_MODULE,
            module_path=CVFSConstants.THRIFT_WRAPPER_PATH,
            max_connections=connection_pool_size,
        )
        self.__log.info("HBlockNode object created for host: %s", self.hostname)

    def get_secondary_rf3_container_paths_map(self):
        """Get the RF3 container paths for the secondary RF3 containers.
        Returns:
            dict: The dictionary containing the disk mount paths and the RF3 container paths.
                {
                    '/hedvig/d3': [
                        '/hedvig/d3/data/NFSFILE_RF3SecondaryForECCVLTBackup000dhxpool186_482',
                        '/hedvig/d3/data/NFSFILE_RF3SecondaryForECCVLTBackup000dhxpool186_749',
                        ...
                    ],
                    '/hedvig/d4': [
                        '/hedvig/d4/data/NFSFILE_RF3SecondaryForECCVLTBackup000dhxpool186_482',
                        '/hedvig/d4/data/NFSFILE_RF3SecondaryForECCVLTBackup000dhxpool186_749',
                        ...
                    ],
                }
        """
        self.__log.info(
            "Getting secondary RF3 container paths from hblock node: %s", self.hostname
        )
        disk_rf3_container_paths_map = {}
        for storage_pool_info in self.__get_storage_pool_details():
            mount_path = list(storage_pool_info.diskInfo.keys())[0]
            disk_rf3_container_paths_map[mount_path] = []
            for container in storage_pool_info.containers:
                if not container.startswith(
                    CVFSConstants.NFS_FILE_RF3_SECONDARY_FOR_EC_PREFIX
                ):
                    continue
                disk_rf3_container_paths_map[mount_path].append(
                    f"{mount_path}/data/{container.replace('$', '_')}"
                )
        return disk_rf3_container_paths_map

    def get_ss_table_dump(self, ss_table_file):
        """Get the SSTable dump for the provided SSTable file.
        Args:
            ss_table_file (str): The SSTable file path.
        Returns:
            str: The SSTable dump.
        """
        self.__log.info("Getting SSTable dump for the file: %s", ss_table_file)
        ss_table_file = ss_table_file.replace("$", "\\$")
        return self.execute_command(f"ls -lh {ss_table_file}").stdout

    def __get_storage_pool_details(self):
        """Get the storage pool details of the hblock node.
        Returns:
            list: StoragePoolInfo
                [
                    StoragePoolInfo(
                        name='1339df17cb04dc22dcf799607a2c7cb0$1',
                        totalCapacity=13998382645247,
                        totalSpaceUsed=6981523578880,
                        containers=[
                            '__ecBackingVDisk_NFSFILE_CVLTBackup000dhxpool186$482',
                            'NFSFILE_RF3SecondaryForECCVLTBackup000dhxpool186$749',
                            ...
                            ],
                        status=False,
                        diskInfo={'/hedvig/d3': 'ok'},
                        percentageUsedSpace=49.873783111572266,
                        containerCount=61,
                        storagePoolCount=0,
                        location=None
                        ),
                    StoragePoolInfo(
                        name='1339df17cb04dc22dcf799607a2c7cb0$2',
                        totalCapacity=13998382645247,
                        totalSpaceUsed=6981523578880,
                        containers=[
                            '__ecBackingVDisk_NFSFILE_CVLTBackup000dhxpool186$482',
                            'NFSFILE_RF3SecondaryForECCVLTBackup000dhxpool186$749',
                            ...
                            ],
                        status=False,
                        diskInfo={'/hedvig/d4': 'ok'},
                        percentageUsedSpace=49.873783111572266,
                        containerCount=61,
                        storagePoolCount=0,
                        location=None
                        ),

                ]

        """
        self.__log.info(
            "Getting storage pool details from hblock node: %s", self.hostname
        )
        details = self.__hblock_thrift_client.getStoragePoolDetails()
        self.__log.debug("Storage pool details: %s", details)
        return details
