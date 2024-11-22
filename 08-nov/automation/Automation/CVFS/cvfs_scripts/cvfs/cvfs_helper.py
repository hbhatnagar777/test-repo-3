""" 
This file contains the helper functions for the cvfs package.
"""

import logging
import os
import subprocess
import threading
from time import time

from .cvfs_constants import CVFSConstants
from .cvfs_node import CVFSNode
from .output_formatter import UnixOutput


class CVFSHelper:
    """This class contains all the helper modules used in the cvfs package."""

    _basic_log = None
    _log_file = None

    @staticmethod
    def execute_command_locally(cmd, cmd_args="", check_return_code=False):
        """This method is used to execute the command locally and return the output.

        Args:
            cmd (str): Command to be executed.
            cmd_args (str): arguments to be passed to the command.
                default: ""
            check_return_code (bool): Flag to check the return code of the command.
                default: False
        Returns:
            object  -   instance of UnixOutput class
        Raises:
            AssertionError: If check_return_code is True and the return code of the command is not 0.
        """
        log = logging.getLogger(__name__)
        log.debug("Executing command: %s %s", cmd, cmd_args)
        if cmd_args is not None and cmd_args != "":
            cmd = f"{cmd} {cmd_args}".strip()
        process = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        output = UnixOutput(
            process.returncode, process.stdout.decode(), process.stderr.decode()
        )
        log.debug(
            "Command completed: %s %s\n"
            "with return code: %s\n"
            "output: %s\n"
            "error: %s",
            cmd,
            cmd_args,
            output.return_code,
            output.stdout,
            output.stderr,
        )
        if check_return_code and output.return_code != 0:
            log.error(
                "Command failed: %s %s\n"
                "with return code: %s\n"
                "output: %s\n"
                "error: %s",
                cmd,
                cmd_args,
                output.return_code,
                output.stdout,
                output.stderr,
            )
            raise AssertionError(f"Command failed: {cmd} {cmd_args}")
        return output

    @staticmethod
    def init_basic_logger(
        module_name,
        log_level=logging.INFO,
        log_dir=CVFSConstants.LOG_PATH,
        log_format=CVFSConstants.LOG_FORMAT,
    ):
        """This method is used to get the logger object.

        Args:
            module_name (str): Path of the log file.
            log_level (str): Log level.
        Returns:
            str  -   log file path
        """
        if CVFSHelper._basic_log is None:
            # assert that log_dir is not a file
            assert not os.path.isfile(
                log_dir
            ), f"log_dir {log_dir} should be a directory"
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = os.path.join(log_dir, f"{module_name}.log")
            logging.basicConfig(
                filename=log_file_path, level=log_level, format=log_format
            )
            CVFSHelper._basic_log = logging.getLogger(__name__)
            CVFSHelper._basic_log.info("Logger initialized successfully")
            CVFSHelper._log_file = log_file_path
            # supress the logging for modules defined in CVFSConstants.LOGGING_SUPPRESS_MODULES
            for suppress_module in CVFSConstants.LOGGING_SUPPRESS_MODULES:
                logging.getLogger(suppress_module).setLevel(logging.WARNING)

        else:
            CVFSHelper._basic_log.warning("Logger already initialized")
        return CVFSHelper._log_file

    @staticmethod
    def get_name_time_pid_tid_str(name="", seperator="_"):
        """This method is used to get the name_time_pid_tid string.

        Args:
            name (str): Name to be appended to the string.
                default: ""
            seperator (str): Seperator to be used in the string.
                default: "_"
        Returns:
            str  -   time_pid_tid
        """
        return f"{name}{seperator}{time()}{seperator}{os.getpid()}{seperator}{threading.current_thread().ident}"

    @staticmethod
    def get_hblock_spool_id_number_for_disk(mount_point):
        """This method is used to get the storage pool id number for the given mountpoint.

        Args:
            mount_point (str): Mount point of the disk
        Returns:
            int  -   spool id number for the given mountpoint
        """
        if mount_point.startswith(CVFSConstants.HEDVIG_DATA_MOUNT_PREFIX):
            d_number = int(mount_point.split(CVFSConstants.HEDVIG_DATA_MOUNT_PREFIX)[1])
            return d_number - 2
        raise ValueError(f"Unexpected mount point format: {mount_point}")

    @staticmethod
    def get_cvfs_node_objects(nodes):
        """
        Get the CVFS node object.
        Args:
            nodes (list): The list of node hostname.
        Returns:
            list: The list of CVFS node objects.
        """
        node_objects = []
        for node in nodes:
            node_objects.append(CVFSNode(node))
        return node_objects

    @staticmethod
    def get_nodes_network_perf_stats(nodes):
        """This method will do the following
        For all network interfaces
            --> Start an iperf server for each of the  nodes.
            --> Run iperf client for each of the nodes in parallel and get the aggregate througput.
        Args:
            nodes (list): List of CVFSNode objects.
        Returns:
            dict    -   Dictionary containing the network performance stats for each node.
                        {
                            "node1": {
                                "bond1": {
                                    "sender_mbps": 10000.00,
                                    "receiver_mbps": 10000.00
                                    }
                                "bond2": {
                                    "sender_mbps": 10000.00,
                                    "receiver_mbps": 10000.00
                                    }
                            },
                            "node2": {
                                "bond1": {
                                    "sender_mbps": 10000.00,
                                    "receiver_mbps": 10000.00
                                    }
                                "bond2": {
                                    "sender_mbps": 10000.00,
                                    "receiver_mbps": 10000.00
                                    }
                            }
                        }
        """
        log = logging.getLogger(__name__)
        log.info("Getting network performance stats for the nodes %s", nodes)
        network_perf_stats = {}
        for node in nodes:
            network_perf_stats[node.hostname] = (
                node.collect_aggregate_net_perf(  # pylint: disable=protected-access
                    nodes
                )
            )
        return network_perf_stats
