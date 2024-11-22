# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–
"""File for performing NFS objectstore pruning related operations

NFSPrunerHelper is the class defined in this file.

NFSPrunerHelper: Class for providing common functions for pruning tests

NFSPrunerHelper:
    __init__()                --  initialize instance of the NFSPrunerHelper

    update_pruner_timeout()   -- Update disk cache pruner timeout for
    3dfns objectstore

    remove_pruner_timeout_reg() -- remove disk cache pruner timeout
    for 3dfns objectstore

    verify_pruner_completed()  --  verify disk cache pruner finished processing

    get_high_watermark()    -- get currently configured high level
    watermark for NFS objectstore

    update_high_watermark() -- update high level watermark for NFS objectstore

    calculate_test_data_size() -- calculate the data to be written by
    optimizing the high water mark

    write_data_dev_zero() -- write data using zero device to disk

    verify_watermark_restored() -- verify watermark is restored for nfs disk cache
"""
import time

from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector


class NFSPrunerHelper:
    """NFS objectstore pruner class to perform common operations for pruning testss"""

    def __init__(self, tc_obj):
        """Initialize instance of the NFSPrunerHelper class..

            Args:
                tc_obj   (instance)     -- test case instance which shoould have
                commcell and nfs_server instance

            Returns:
                object - instance of the NFSPrunerHelper class

            Raises:
                Exception:
                    if any error occurs in the initialization
        """
        self.commcell = tc_obj.commcell
        self.nfs_server_machine_obj = tc_obj.nfs_server_obj.nfs_serv_machine_obj
        self.log = logger.get_log()
        self.utils = OptionsSelector(self.commcell)
        self.commcell.refresh()
        self.nfs_server_obj = tc_obj.nfs_server_obj

    def update_pruner_timeout(self, timeout='2', restart_services=False):
        """Update disk cache pruner timeout for 3dfns objectstore..
            Args:
                timeout   (str)     -- value for disk cache pruner time out

                restart_services (str) -- restart CV services on NFS server

            Returns:
                None
        """
        self.log.info("updating disk cache pruner timeout to %s", timeout)
        self.nfs_server_machine_obj.create_registry(
            '3Dfs',
            'DiskCachePrunerTimeout',
            timeout)

        if restart_services:
            self.log.info("restarting CV services on NFS server client")
            self.nfs_server_machine_obj.client_object.restart_services()

            self.log.info("sleep for 2 minutes to allow ganesha to export shares")
            time.sleep(2*60)

    def remove_pruner_timeout_reg(self, restart_services=False):
        """remove disk cache pruner timeout for 3dfns objectstore..

            Args:
                restart_services (str) -- restart CV services on NFS server

            Returns:
                None
        """
        self.log.info("remove disk cache pruner timeout from registry")
        self.nfs_server_machine_obj.remove_registry(
            '3Dfs',
            'DiskCachePrunerTimeout')

        if restart_services:
            self.log.info("restarting CV services on NFS server client")
            self.nfs_server_machine_obj.client_object.restart_services()

            self.log.info("sleep for 2 minutes to allow ganesha to export shares")
            time.sleep(2 * 60)

    def verify_pruner_completed(self, time_stamp, max_attempt=5):
        """verify disk cache pruner finished processing..

            Args:
                time_stamp   (datetime)  -- timestamp used to match the expected
                string in logs. Expected pattern: mm/yy HH:MM:SS

                max_attempt  (int)  -- maximum attempts used to match string
                in logs

            Returns:
                None
        """
        pruner_success_message = "reached low watermark|no more pruning candidates"
        self.nfs_server_obj.parse_3dnfs_logs(pruner_success_message,
                                             time_stamp,
                                             max_attempt)

    def get_high_watermark(self, tc_obj):
        """get currently configured high level watermark for NFS objectstore..

            Args:
                tc_obj   (instance)     -- test case instance which should have
                csdb initialized

            Returns:
                str - currently configured high level watermark

            Raises:
                Exception:
                    if it is unable to find watermark
        """
        self.log.info("getting objectstore high level watermark")

        query_pattern = ("select IdxCache.AgeingPercentDiskspace from IdxCache "
                         "inner join IdxAccessPath "
                         "on IdxCache.IdxCacheId = IdxAccessPath.IdxCacheId "
                         "where IdxCache.IdxCacheType = 3 and IdxAccessPath.ClientId={0}")
        query = query_pattern.format(self.nfs_server_machine_obj.client_object.client_id)

        self.log.info("executing query %s", query)
        tc_obj.csdb.execute(query)
        results = tc_obj.csdb.fetch_all_rows()
        self.log.info("high water mark results %s", results)
        if not bool(results):
            raise Exception("unable to find nfs server high water mark")
        self.log.debug("high level watermark configured %s", results[0][0])
        return results[0][0]

    def update_high_watermark(self, new_watermark):
        """update high level watermark for NFS objectstore..

            Args:
                new_watermark   (int)     -- new watermark to set in CSDB

            Returns:
                None

            Raises:
                Exception:
                    if it is unable set in CSDB
        """
        self.log.info("updating objectstore high level watermark")
        query_pattern = ("update IdxCache SET IdxCache.AgeingPercentDiskspace = {0} "
                         "FROM IdxCache "
                         "inner join IdxAccessPath "
                         "on IdxCache.IdxCacheId = IdxAccessPath.IdxCacheId "
                         "where IdxCache.IdxCacheType = 3 and IdxAccessPath.ClientId={1}")
        query = query_pattern.format(new_watermark,
                                     self.nfs_server_machine_obj.client_object.client_id)

        self.log.info("executing query %s", query)
        self.utils.update_commserve_db(query)

        self.log.info("restarting CV services on NFS server client")
        self.nfs_server_machine_obj.client_object.restart_services()

        self.log.info("sleep for 2 minutes to allow ganesha to export shares")
        time.sleep(2*60)

    def calculate_test_data_size(self, nfs_cache_disk_path, tc_obj):
        """calculate the data to be written with optimizing the high water mark

            Args:
                nfs_cache_disk_path   (str)  -- NFS cache disk partition name

                tc_obj                (obj)  -- test case instances

            Returns:
                tuple - (data to be written to hit high watermark,
                         new optimized high watermark)

            Raises:
                Exception:
                    if it is unable calculate the data to be written
        """
        min_high_watermark = 30
        high_watermark_percent = int(self.get_high_watermark(tc_obj))
        disk_details = self.nfs_server_machine_obj.get_storage_details()

        if nfs_cache_disk_path not in disk_details:
            raise Exception("given nfs cache disk %s is not available. storage details "
                            "available %s" % (nfs_cache_disk_path, disk_details))

        cache_disk_details = disk_details[nfs_cache_disk_path]
        self.log.debug("NFS cache disk details %s", cache_disk_details)

        total_disk_space_gb = int(cache_disk_details['total'])/1024
        available_disk_space_gb = int(cache_disk_details['available'])/1024

        # min HWM is 30 so min data to write is 30% of total space
        min_data_size = min_high_watermark * 0.01 * total_disk_space_gb

        self.log.info("calculating minimum possible data to be written to test pruning")
        new_high_watermark_percent = high_watermark_percent
        while True:
            high_watermark_space = new_high_watermark_percent * 0.01 * total_disk_space_gb
            disk_space_already_used = total_disk_space_gb - available_disk_space_gb
            data_to_be_written = high_watermark_space - disk_space_already_used

            if data_to_be_written <= min_data_size:
                break

            new_high_watermark_percent -= 10

        data_to_be_written += 6
        self.log.info("Data to be written:%sGB, new HWM:%s" % (
            int(data_to_be_written),
            new_high_watermark_percent))

        return int(data_to_be_written), new_high_watermark_percent

    def write_data_dev_zero(self, write_path, data_size):
        """writing unique data to objectstore are slower than writing to disk directly.
           so in order to run test faster this method allows 'zero' data to be written
           directly to nfs cache disk which is much faster.
           It writes 'data_size' number of 1GB files to given test path..

            Args:
                write_path   (str)     -- mount path of nfs cache disk

                data_size        (int)     -- data size in GB to be written
                to nfs cache directory

            Returns:
                (path) - directory path where data is created in nfs cache mount volume

            Raises:
                Exception:
                    if it is unable create data
        """
        self.log.info("creating data directly to NFS cache"
                      "data size:%sGB, cache mount path:%s" % (data_size, write_path))
        data_path = self.nfs_server_machine_obj.join_path(write_path,
                                                          "tmp_data")
        if not self.nfs_server_machine_obj.check_directory_exists(data_path):
            self.log.info("creating directory %s", data_path)
            self.nfs_server_machine_obj.create_directory(data_path)

        cmd_pattern = "dd if=/dev/zero of={0} bs=1GB count=1"
        for i in range(data_size):
            file_path = self.nfs_server_machine_obj.join_path(data_path,
                                                              "file"+str(i))
            cmd = cmd_pattern.format(file_path)
            self.log.debug("running command %s", cmd)
            output = self.nfs_server_machine_obj.execute_command(cmd)
            if output.exit_code:
                raise Exception("error creating test file")

        return data_path

    def verify_watermark_restored(self, watermark_perc, nfs_cache_disk_path):
        """verify watermark is restored for nfs disk cache..

            Args:
                watermark_perc   (int)     -- currently configured watermark

                nfs_cache_disk_path (path) -- nfs disk name where cache path
                is mounted

            Returns:
                None

            Raises:
                Exception:
                    if disk used space above watermark
        """
        self.log.info("verifying watermark is restored for NFS cache directory")

        cache_disk_details = \
            self.nfs_server_machine_obj.get_storage_details()[nfs_cache_disk_path]
        self.log.debug("NFS cache disk details %s", cache_disk_details)

        total_disk_space_gb = int(cache_disk_details['total'])/1024
        available_disk_space_gb = int(cache_disk_details['available'])/1024
        watermark_space = int(watermark_perc * 0.01 * total_disk_space_gb)
        disk_space_used = \
            (cache_disk_details['total'] - cache_disk_details['available'])/1024

        self.log.info("disk_space_used:%sGB, watermark threshold:%s" %
                      (disk_space_used, watermark_space))
        if disk_space_used > watermark_space+1:
            raise Exception("water mark is not restored")

        self.log.info("water mark is restored")

    def verify_watermark_crossed(self, watermark_perc, nfs_cache_disk_path):
        """verify watermark is restored for nfs disk cache..

            Args:
                watermark_perc   (int)     -- currently configured watermark

                nfs_cache_disk_path (path) -- nfs disk name where cache path
                is mounted

            Returns:
                None

            Raises:
                Exception:
                    if disk used space above watermark
        """
        self.log.info("verifying watermark is crossed for NFS cache directory")

        cache_disk_details = \
            self.nfs_server_machine_obj.get_storage_details()[nfs_cache_disk_path]
        self.log.debug("NFS cache disk details %s", cache_disk_details)

        total_disk_space_gb = int(cache_disk_details['total'])/1024
        available_disk_space_gb = int(cache_disk_details['available'])/1024
        watermark_space = int(watermark_perc * 0.01 * total_disk_space_gb)

        disk_space_used = \
            (cache_disk_details['total'] - cache_disk_details['available'])/1024

        self.log.info("disk space used:%sGB, watermark threshold:%s" %
                      (disk_space_used, watermark_space))
        if disk_space_used < watermark_space:
            raise Exception("water mark is not crossed")

        self.log.info("water mark is crossed")
