"""
This script is used to print the file system tree of the given CVFS Filer VDisk

Usage:
    python cvfs_net_perf_report.py --vdisk_name <vdisk_name> --output_file <output_file>
Requirements:
    --> The script should be run on any of the pages node with pages service up and running.
    --> The script should be run with root privileges.
"""

import argparse
import logging
import os
import socket
import sys
from collections import deque
from threading import Condition, RLock, Thread
from time import sleep, time

from cvfs.cvfs_collections import FileWriter, ThreadSafeSet
from cvfs.cvfs_constants import CVFSConstants
from cvfs.cvfs_helper import CVFSHelper
from cvfs.cvfs_pages import PagesNode


class Worker(Thread):
    """
    This class is used to create a worker thread to traverse FS tree and put details in given outputfile.
    """

    def __init__(
        self,
        pages_node,
        vdisk_name,
        vdisk_info,
        folder_inode_queue,
        folder_inode_queue_condition,
        inode_set,
        output_file,
    ):
        """Initialize the Worker object with the provided parameters.
        Args:
            pages_node (PagesNode): The PagesNode object to get the folder details.
            vdisk_name (str): The name of the VDisk whose file system tree needs to be printed.
            vdisk_info (VDiskInfo object): The vdisk information. Refer qbpages.thrift.
            folder_inode_queue (Queue): Queue containing the folder inodes to be processed.
            folder_inode_queue_condition (Condition): Condition object to synchronize access to the folder_inode_queue.
            inode_set (cvfs_collections.ThreadSafeSet): Thread safe set to store all the inodes.
            output_file (cvfs_collections.FileWriter): The output file where the file system tree will be printed.
        """
        super().__init__()
        self.__pages_node = pages_node
        self.__vdisk_name = vdisk_name
        self.__vdisk_info = vdisk_info
        self.__folder_inode_queue = folder_inode_queue
        self.__folder_inode_queue_condition = folder_inode_queue_condition
        self.__inode_set = inode_set
        self.__output_file = output_file
        self.__stop = False
        self.__idle = False
        self.__graceful_stop = False
        self.__processed_count = 0
        self.__processing_time = 0.0
        self.__lock = RLock()
        self.__log = logging.getLogger(__name__)

    @property
    def stop(self):
        """Get the stop flag."""
        with self.__lock:
            return self.__stop

    @stop.setter
    def stop(self, stop):
        """Set the stop flag."""
        with self.__lock:
            self.__stop = stop

    def is_idle(self):
        """Check if the worker thread is idle."""
        with self.__lock:
            return self.__idle

    def is_graceful_stop(self):
        """Check if the worker thread has stopped gracefully."""
        with self.__lock:
            return self.__graceful_stop

    def get_processed_count(self):
        """Get the number of inodes processed by the worker thread."""
        with self.__lock:
            return self.__processed_count

    def get_processing_time(self):
        """Get the processing time of the worker thread."""
        with self.__lock:
            return self.__processing_time

    def get_processing_speed(self):
        """Get the processing speed of the worker thread."""
        with self.__lock:
            if self.__processing_time == 0:
                return -1
            return self.__processed_count / self.__processing_time

    def log_counter(self):
        """Log the processed count, processing time and processing speed of the worker thread."""
        self.__log.info("Processed %d inodes", self.get_processed_count())
        self.__log.info("Processing time: %f seconds", self.get_processing_time())
        self.__log.info("Processing speed: %f inodes/sec", self.get_processing_speed())

    def run(self):
        """Run the worker thread to traverse FS tree and put details in output file."""
        self.__log.info("Worker thread started.")
        while not self.stop:
            folder_inode = None
            with self.__folder_inode_queue_condition:
                while len(self.__folder_inode_queue) == 0 and not self.stop:
                    with self.__lock:
                        self.__idle = True
                    self.__log.debug("Waiting for inode in queue.")
                    self.__folder_inode_queue_condition.wait()
                if self.stop:
                    break
                self.__log.debug("Getting inode from queue.")
                folder_inode = self.__folder_inode_queue.pop()
                self.__log.debug("Got inode from queue.")
                with self.__lock:
                    self.__idle = False
            self.__log.debug("Processing inode: %s", folder_inode)
            self.__traverse_folder(folder_inode)
        with self.__lock:
            self.__graceful_stop = True
        self.__log.info("Worker thread stopped.")

    def __traverse_folder(self, folder_inode):
        """Traverse the folder and put details in output file."""
        self.__log.debug("Getting folder details for inode: %s", folder_inode)
        query = ""
        while True:
            try:
                start_counter = time()
                tfile_infos = self.__pages_node.ls_plus_paginate(
                    folder_inode, self.__vdisk_name, query, self.__vdisk_info
                )
                end_counter = time()
            except Exception as e:  # pylint: disable=broad-except
                self.__log.error("Error getting folder details: %s", e)
                raise e
            self.__log.debug("Updating time counters.")
            with self.__lock:
                self.__processing_time += end_counter - start_counter
            self.__log.debug("Updated time counters.")
            if tfile_infos is None or len(tfile_infos) == 0:
                break
            query = tfile_infos[-1].filename
            for tfile_info in tfile_infos:
                if tfile_info.inode in self.__inode_set:
                    continue
                self.__log.debug("Adding inode: %s to set", tfile_info.inode)
                self.__inode_set.add(tfile_info.inode)
                self.__log.debug("Added inode: %s to set", tfile_info.inode)
                self.__log.debug("Writing file info to output file.")
                formatted_line = (
                    f"{tfile_info.inode}\t"
                    f"{tfile_info.filename},"
                    f"{tfile_info.fileattr.blkSize},"
                    f"{tfile_info.fileattr.nblocks},"
                    f"{tfile_info.fileattr.mode},"
                    f"{tfile_info.fileattr.nlink},"
                    f"{tfile_info.fileattr.size},"
                    f"{tfile_info.fileattr.atime},"
                    f"{tfile_info.fileattr.ctime},"
                    f"{tfile_info.fileattr.mtime},"
                    f"{tfile_info.fileattr.uid},"
                    f"{tfile_info.fileattr.gid},"
                    f"{tfile_info.fileattr.deleted},"
                    f"{tfile_info.fileattr.mctrId},"
                    f"{tfile_info.fileattr.immutable},"
                    f"{tfile_info.fileattr.duInode},"
                    f"{tfile_info.fileattr.versionCounter},"
                    f"{tfile_info.fileattr.isVersioningEnabled},"
                    f"{tfile_info.isDir}\n"
                )
                self.__output_file.write(formatted_line)
                self.__log.debug("Wrote file info to output file.")
                self.__log.debug("Updating processed count.")
                with self.__lock:
                    self.__processed_count += 1
                self.__log.debug("Updated processed count.")
                self.__log.debug("tfile_info: %s", tfile_info)
                if tfile_info.isDir:
                    self.__log.debug("Adding inode: %s to queue", tfile_info.inode)
                    with self.__folder_inode_queue_condition:
                        self.__folder_inode_queue.appendleft(tfile_info.inode)
                        self.__folder_inode_queue_condition.notify_all()
                    self.__log.debug("Added inode: %s to queue", tfile_info.inode)


class CVFSPrintFSTree:
    """
    This class is used to print the file system tree of the given CVFS Filer VDisk.
    """

    def __init__(self):
        """Initialize the CVFSPrintFSTree object with the provided parameters."""
        self.__args = None
        self.__quiet = False
        self.__debug = False
        self.__vdisk_name = None
        self.__output_file = None
        self.__workers = []
        self.__thread_count_per_page = CVFSConstants.CONNECTION_POOL_SIZE
        self.__folder_inode_queue = deque()
        self.__folder_inode_queue_condition = Condition()
        self.__parse_args()
        self.__name = os.path.basename(__file__)
        self.__log_level = "DEBUG" if self.__debug else "INFO"
        self.__log_file = CVFSHelper.init_basic_logger(
            module_name=self.__name, log_level=self.__log_level
        )
        self.__log = logging.getLogger(__name__)
        if not self.__quiet:
            print(f"Initalizing the script {self.__name}")
            print(f"Please check Logfile: {self.__log_file} for detailed progress.")
        self.__log.info("*** %s Initializing ***", self.__name)
        self.__log.info("Initializing cvfs pages node for the local machine.")
        self.__local_hostname = socket.gethostname()
        self.__pages_node = PagesNode(
            self.__local_hostname, connection_pool_size=self.__thread_count_per_page
        )

    def __parse_args(self):
        """Parse the command line arguments."""
        # create an ArgumentParser object
        parser = argparse.ArgumentParser(
            description="This script is used to print the file system tree of the given CVFS Filer VDisk."
        )
        # create an argument
        parser.add_argument(
            "--vdisk_name",
            help="The name of the VDisk whose file system tree needs to be printed.",
            required=True,
        )

        parser.add_argument(
            "--output_file",
            help="The output file where the file system tree will be printed.",
            required=True,
        )

        parser.add_argument(
            "--debug",
            help="Enable debug logging.",
            action="store_true",
        )

        parser.add_argument(
            "--quiet",
            help="Print only the network performance stats.",
            action="store_true",
        )

        parser.add_argument(
            "--threads_per_page_node",
            help="Number of threads per page node.",
            type=int,
            default=CVFSConstants.CONNECTION_POOL_SIZE,
        )
        # parse the arguments from standard input
        self.__args = parser.parse_args()
        self.__vdisk_name = self.__args.vdisk_name
        self.__output_file = FileWriter(self.__args.output_file)
        self.__debug = self.__args.debug
        self.__quiet = self.__args.quiet
        self.__thread_count_per_page = self.__args.threads_per_page_node

    def run(self):
        """Run the network performance tests.
        Returns:
            int - The return code.
                    0 - if success.
                    any other value - If any error occured.
        """
        if not self.__quiet:
            print(
                "Starting to retrieve the FS tree. Results will be printed on the specified output file when done."
            )
        folder_inode_queue = self.__folder_inode_queue
        inode_set = ThreadSafeSet()
        vdisk_info = self.__pages_node.describe_vdisk(self.__vdisk_name)
        self.__log.info("Starting all the worker threads.")
        for page_node in self.__pages_node.get_list_of_pages_nodes():
            for _ in range(self.__thread_count_per_page):
                worker = Worker(
                    pages_node=page_node,
                    vdisk_name=self.__vdisk_name,
                    vdisk_info=vdisk_info,
                    folder_inode_queue=folder_inode_queue,
                    folder_inode_queue_condition=self.__folder_inode_queue_condition,
                    inode_set=inode_set,
                    output_file=self.__output_file,
                )
                self.__workers.append(worker)
                worker.start()
        with self.__folder_inode_queue_condition:
            folder_inode_queue.appendleft(CVFSConstants.ROOT_INODE)
            self.__folder_inode_queue_condition.notify_all()
        while True:
            sleep(CVFSConstants.THREAD_SLEEP_TIME)
            self.__log.info("Check the status of all threads.")
            self.update_counters()
            self.check_thread_crash()
            if self.is_processing_done():
                self.check_thread_crash()
                self.stop_workers()
                break
        self.__log.info("All worker threads stopped.")
        self.__output_file.close()
        self.__log.info("Output file %s closed.", self.__output_file)
        self.__log.info("Script completed successfully.")
        print(f"FS tree printed successfully on file {self.__args.output_file}")
        return 0

    def update_counters(self):
        """Update the counters for the worker threads."""
        self.__log.info("Updating the counters for all worker threads.")
        total_processed_count = 0
        for worker in self.__workers:
            worker.log_counter()
            total_processed_count += worker.get_processed_count()
        self.__log.info("Total processed inodes: %d", total_processed_count)

    def check_thread_crash(self):
        """Check if any worker thread has crashed."""
        self.__log.info("Checking if any worker thread has crashed.")
        for worker in self.__workers:
            if not worker.is_alive() and not worker.is_graceful_stop():
                self.__log.error("Worker thread crashed.")
                self.stop_workers()
                raise RuntimeError("Atleast one thread Crashed.")
        self.__log.info("No worker thread has crashed.")

    def stop_workers(self):
        """Stop the worker threads."""
        self.__log.info("Stopping the worker threads.")
        for worker in self.__workers:
            try:
                worker.stop = True
            except Exception as e:  # pylint: disable=broad-except
                self.__log.error("Error stopping worker thread: %s", e)
        with self.__folder_inode_queue_condition:
            self.__folder_inode_queue_condition.notify_all()
        for worker in self.__workers:
            try:
                worker.join()
            except Exception as e:  # pylint: disable=broad-except
                self.__log.error("Error joining worker thread: %s", e)
        self.__log.info("All worker threads stopped.")

    def is_processing_done(self):
        """Check if the processing of the worker threads is done."""
        self.__log.info("Checking if processing is done.")
        with self.__folder_inode_queue_condition:
            if len(self.__folder_inode_queue) != 0:
                self.__log.info("Processing is not done.")
                return False
            for worker in self.__workers:
                if not worker.is_idle():
                    self.__log.info("Processing is not done.")
                    return False
        self.__log.info("Processing is done.")
        return True


if __name__ == "__main__":
    sys.exit(CVFSPrintFSTree().run())
