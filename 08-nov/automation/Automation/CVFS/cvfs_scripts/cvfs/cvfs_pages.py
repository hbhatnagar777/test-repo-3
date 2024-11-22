""" This module is used to represent the pages node, its properties and functions.
    Refer qbserver.thrift, qbpages.thrift, qbcommon.thrift in hedvig/cvfs respository for the thrift definitions.
    """

import logging

from .connections import ThriftConnection
from .cvfs_constants import CVFSConstants
from .cvfs_hblock import HBlockNode
from .cvfs_node import CVFSNode


class PagesNode(CVFSNode):
    """This class is used to represent the pages node."""

    def __init__(
        self,
        hostname,
        connection_pool_size=CVFSConstants.CONNECTION_POOL_SIZE,
        user_name=CVFSConstants.SSH_USER,
        key_filename=CVFSConstants.SSH_KEYPATH,
    ):
        """Initialize the PagesNode object with the provided parameters.

        Args:
            hostname (str): The hostname of the pages node.
            connection_pool_size (int): The size of the SSH and Thrift connection pool.
                default: CVFSConstants.CONNECTION_POOL_SIZE
            user_name (str): The username to connect to the pages node.
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
        self.__pages_thrift_client = ThriftConnection(
            host=self.hostname,
            port=CVFSConstants.PAGES_THRIFT_PORT,
            module_name=CVFSConstants.PAGES_THRIFT_WRAPPER_MODULE,
            module_path=CVFSConstants.THRIFT_WRAPPER_PATH,
            max_connections=connection_pool_size,
        )
        self.__log.info("PagesNode object created for host: %s", self.hostname)

    def describe_vdisk(self, vdisk_name):
        """Get the vdisk description for the given vdisk name.
        Args:
            vdisk_name (str): The name of the vdisk.
        Returns:
            (VDiskInfo object): The vdisk information. Refer qbpages.thrift.
        """
        self.__log.debug(
            "Getting vdisk description for vdisk: %s on pages node: %s",
            vdisk_name,
            self.hostname,
        )
        return self.__pages_thrift_client.describeVDisk(vdisk_name)

    def list_dir_items(self, inode, vdisk_name, vdisk_info=None):
        """List the directory items for the given inode and vdisk name.
        Args:
            inode (int): The inode of the directory.
            vdisk_name (str): The name of the vdisk.
            vdisk_info (VDiskInfo object): The vdisk information. Refer qbpages.thrift.
                default: None
        Returns:
            list: List of TFileInfo objects.
            [
                TFileInfo(
                    inode=385629,
                    filename='file1',
                    fileattr=HedvigFSAttr(
                        inode=385629,
                        blkSize=65536,
                        nblocks=0,
                        mode=33188,
                        nlink=1,
                        size=5,
                        atime=1713016747146976962,
                        ctime=1713016746979610558,
                        mtime=1713016747146976962,
                        vdisk=1,
                        uid=0,
                        gid=0,
                        dev=65090,
                        rdev=0,
                        generationNbr=2,
                        deleted=0,
                        mctrId=566,
                        mntLocation='hostname.com:9999',
                        dedupDiskName=None,
                        immutable=0,
                        duInode=0,
                        versionCounter=1,
                        isVersioningEnabled=False)
                    isDir=False
                ),
                ...
            ]
        """
        self.__log.debug(
            "Listing directory items for inode: %s, vdisk: %s on pages node: %s",
            inode,
            vdisk_name,
            self.hostname,
        )
        if vdisk_info is None:
            vdisk_info = self.describe_vdisk(vdisk_name)
        query = ""
        tfile_info_output = []
        while True:
            tfile_infos = self.ls_plus_paginate(inode, vdisk_name, query, vdisk_info)
            if tfile_infos is None or len(tfile_infos) == 0:
                return tfile_info_output
            tfile_info_output.extend(tfile_infos)
            query = tfile_infos[-1].filename

    def get_file_attrs_for_filer(self, inode, vdisk_name):
        """Get the file attributes for the given inode and vdisk name.
        Args:
            inode (int): The inode of the file.
            vdisk_name (str): The name of the vdisk.
        Returns:
            object: The file attributes.
                    HedvigFSAttr(
                        inode=385629,
                        blkSize=65536,
                        nblocks=0,
                        mode=33188,
                        nlink=1,
                        size=5,
                        atime=1713016747146976962,
                        ctime=1713016746979610558,
                        mtime=1713016747146976962,
                        vdisk=1,
                        uid=0,
                        gid=0,
                        dev=65090,
                        rdev=0,
                        generationNbr=2,
                        deleted=0,
                        mctrId=566,
                        mntLocation='hostname.com:9999',
                        dedupDiskName=None,
                        immutable=0,
                        duInode=0,
                        versionCounter=1,
                        isVersioningEnabled=False)
        """
        self.__log.debug(
            "Getting file attributes for inode: %s, vdisk: %s on pages node: %s",
            inode,
            vdisk_name,
            self.hostname,
        )
        return self.__pages_thrift_client.getFileAttributesForFiler(inode, vdisk_name)

    def get_list_of_pages_nodes(self):
        """Get the list of pages nodes.
        Returns:
            list: List of PagesNode objects.
        """
        self.__log.info("Getting list of pages nodes")
        pages_nodes = []
        for hostname in self.__pages_thrift_client.getListOfPages():
            pages_nodes.append(
                PagesNode(
                    hostname,
                    connection_pool_size=self._connection_pool_size,
                    user_name=self._user_name,
                    key_filename=self._key_filename,
                )
            )
        self.__log.debug("Pages nodes: %s", pages_nodes)
        return pages_nodes

    def ls_plus_paginate(self, parent_inode, vdisk_name, query, vdisk_info):
        """Get list of TFileInfo objects for items directly under given parent_inode.
        Specify the file_name to start the pagination. if query is empty, it will start from the beginning.
        Maximum number of items returned is 1000.
        Args:
            parent_inode (int): The inode of the parent directory.
            vdisk_name (str): The name of the vdisk.
            vdisk_info (VDiskInfo object): The vdisk information. Refer qbpages.thrift.
            query (str): The query to specify the file_name to start the pagination.
        Returns:
            list: List of TFileInfo objects.
            [
                TFileInfo(
                    inode=385629,
                    filename='file1',
                    fileattr=HedvigFSAttr(
                        inode=385629,
                        blkSize=65536,
                        nblocks=0,
                        mode=33188,
                        nlink=1,
                        size=5,
                        atime=1713016747146976962,
                        ctime=1713016746979610558,
                        mtime=1713016747146976962,
                        vdisk=1,
                        uid=0,
                        gid=0,
                        dev=65090,
                        rdev=0,
                        generationNbr=2,
                        deleted=0,
                        mctrId=566,
                        mntLocation='hostname.com:9999',
                        dedupDiskName=None,
                        immutable=0,
                        duInode=0,
                        versionCounter=1,
                        isVersioningEnabled=False)
                    isDir=False
                ),
                ...
            ]
        """
        return self.__pages_thrift_client.lsPlusPaginate(
            parent_inode, vdisk_name, query, vdisk_info
        )

    def get_all_spm_ids(self):
        """This method is used to get all the SPM ids.

        Args:
            None
        Returns: List
            [
                {
                    "storage_id": 'd290377280b6326feafea52cb584d09f',
                    "spm_id": '47661F49-4A56-4A55-90D5-273378ADCA46',
                    "host_name": "cvfsvm4.devemc.commvault.com",
                    "spool_id": 1,
                    "start_time": 1727684575406,
                    "status": 'COMPLETED',
                },
                ...
            ]
        """
        spm_ids_list = []
        spm_ids_dict = self.__pages_thrift_client.getSPMIds()
        for key, status in spm_ids_dict.items():
            components = key.split("$")
            extracted_storage_id = components[0]
            extracted_spmid = components[1]
            extracted_hostname = components[2]
            extracted_spool_id = components[3]
            extracted_timestamp = components[4]
            spm_ids_list.append(
                {
                    "storage_id": extracted_storage_id,
                    "spm_id": extracted_spmid,
                    "host_name": extracted_hostname,
                    "spool_id": int(extracted_spool_id),
                    "start_time": int(extracted_timestamp),
                    "status": status,
                }
            )

    def get_all_rebalance_ids(self):
        """
        This method is used to get all the rebalance ids.

        Args:
            None
        Returns: List
            [
                {
                    "RebalanceId": sub_key,
                    "FromStoragePool": source_pool,
                    "ToStoragePool": target_pool,
                    "Sender": rbl_status.sender,
                    "CtrsNeeded": rbl_status.ctrsNeeded,
                    "CtrsReceived": rbl_status.ctrsReceived,
                    "CtrsReadReady": rbl_status.ctrsReadReady,
                    "IsComplete": rbl_status.isComplete,
                    "CtrsDeleted": rbl_status.ctrsDeleted,
                },
                ...
            ]
        """
        raise NotImplementedError

    def get_cluster_name(self):
        """Returns the cluster name

        Args:
            None

        Returns:
            String: The name of cluster
        """
        cluster_name = self.__pages_thrift_client.getClusterName()
        return cluster_name

    def get_hblock_nodes(self):
        """Return the list of HBlockNode objects.

        Returns:
            list: List of HBlockNode objects.
        """
        self.__log.info("Getting HBlock nodes from pages node: %s", self.hostname)
        hblock_nodes = []
        for storage_id in self.__get_hblock_storage_ids():
            hostname = self.__get_end_point_for_storage_id(storage_id).hostname
            hblock_nodes.append(
                HBlockNode(
                    hostname,
                    connection_pool_size=self._connection_pool_size,
                    user_name=self._user_name,
                    key_filename=self._key_filename,
                )
            )
        self.__log.debug("HBlock nodes: %s", hblock_nodes)
        return hblock_nodes

    def __get_hblock_storage_ids(self):
        """Get the list of storage ids of the hblock nodes.
        Returns:
            list: List of storage ids in str format.
        """
        self.__log.info("Getting HBlock storage ids from pages node: %s", self.hostname)
        storage_ids = self.__pages_thrift_client.getHBlockStorageIds()
        self.__log.debug("HBlock storage ids: %s", storage_ids)
        return storage_ids

    def __get_end_point_for_storage_id(self, storage_id):
        """Get the end point for the given storage id.

        Args:
            storage_id (str): The storage id.
        Returns:
            object: Location.
                Location(
                    hostname='hostname.com',
                    port=9999,
                )
        """
        self.__log.debug(
            "Getting end point for storage id: %s on pages node: %s",
            storage_id,
            self.hostname,
        )
        end_point = self.__pages_thrift_client.getEndPointForStorageId(storage_id)
        self.__log.info("End point for storage id: %s", end_point)
        return end_point

    def __get_blk_read_locations(  # pylint: disable=unused-private-member
        self, vdisk_name, blkids, blk_size=CVFSConstants.BLOCK_SIZE_64KB
    ):
        """Get the block read locations for the given vdisk name and block ids.
        Args:
            vdisk_name (str): The name of the vdisk.
            blkids (list): The list of block ids.
            blk_size (int): The block size.
                default: CVFSConstants.BLOCK_SIZE_64KB
        Returns:
            list: list of BlockMutationInfo objects
                [
                    BlockMutationInfo(
                        blkId=119545,
                        dedupBlkId=-1,
                        timestamp=8589949660,
                        dedupTimestamp=-1,
                        version=1,
                        locations=0,
                        failedLocations=0,
                        vDiskName=None),
                    BlockMutationInfo(
                        blkId=119546,
                        dedupBlkId=-1,
                        timestamp=8589949660,
                        dedupTimestamp=-1,
                        version=1,
                        locations=0,
                        failedLocations=0,
                        vDiskName=None)
                ]
        """
        self.__log.debug(
            "Getting block read locations for vdisk: %s, blkids: %s on pages node: %s",
            vdisk_name,
            blkids,
            self.hostname,
        )
        return self.__pages_thrift_client.getBlkReadLocations(
            vdisk_name, blk_size, blkids
        )

    def __get_blk_failed_locations(  # pylint: disable=unused-private-member
        self, vdisk_name, blkids, blk_size=CVFSConstants.BLOCK_SIZE_64KB
    ):
        """
        Get the block failed locations for the given vdisk name and block ids.
        Args:
            vdisk_name (str): The name of the vdisk.
            blkids (list): The list of block ids.
            blk_size (int): The block size.
                default: CVFSConstants.BLOCK_SIZE_64KB

        Returns:
            list: list of FailedBlockMutationInfo objects
                [
                    FailedBlockMutationInfo(
                        blkId=119545,
                        timestamp=8589949660,
                        locations=0,
                        failedLocations=0,
                        ),
                    FailedBlockMutationInfo(
                        blkId=119545,
                        timestamp=8589949660,
                        locations=0,
                        failedLocations=0,
                        ),
                ]
        """
        self.__log.debug(
            "Getting block failed locations for vdisk: %s, blkids: %s on pages node: %s",
            vdisk_name,
            blkids,
            self.hostname,
        )
        return self.__pages_thrift_client.getBlkFailedLocations(
            vdisk_name, blk_size, blkids
        )
