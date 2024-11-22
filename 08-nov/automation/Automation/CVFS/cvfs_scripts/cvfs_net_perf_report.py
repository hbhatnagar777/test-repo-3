"""
This script is used to generate the network performance report for the CVFS nodes.
This script will do the following:
    For all network interfaces
                --> Start an iperf server for each of the hblock nodes.
                --> Run iperf client for each of the hblock nodes in parallel and get the aggregate througput.

            Prints the network performance stats for each hblock node.:
                            {
                                "node1": {
                                    "commServeRegistration": {
                                        "interface": "bond1",
                                        "sender_mbps": 10000.00,
                                        "receiver_mbps": 10000.00
                                        }
                                    "storagePool": {
                                        "interface": "bond2",
                                        "sender_mbps": 10000.00,
                                        "receiver_mbps": 10000.00
                                        }
                                },
                                "node2": {
                                    "commServeRegistration": {
                                        "interface": "bond1",
                                        "sender_mbps": 10000.00,
                                        "receiver_mbps": 10000.00
                                        }
                                    "storagePool": {
                                        "interface": "bond2",
                                        "sender_mbps": 10000.00,
                                        "receiver_mbps": 10000.00
                                        }
                                }
                            }

Usage:
    python cvfs_net_perf_report.py 
Requirements:
    --> The script should be run on any of the pages node with pages service up and running.
    --> The script should be run with root privileges.
    --> Make sure that the iperf3 is installed on all the hblock nodes.
    --> Make sure that not much traffic is flowing through the network interfaces.
"""

import argparse
import json
import logging
import os
import socket
import sys

from cvfs.cvfs_helper import CVFSHelper
from cvfs.cvfs_pages import PagesNode


class CVFSNetPerfReport:
    """
    This class is used to generate the network performance report for the CVFS nodes.
    """

    def __init__(self):
        """Initialize the CVFSNetPerfReport object with the provided parameters."""
        self.__args = None
        self.__quiet = False
        self.__debug = False
        self.__nodes = None
        self.__name = os.path.basename(__file__)
        self.__log_level = "DEBUG" if self.__debug else "INFO"
        self.__log_file = CVFSHelper.init_basic_logger(
            module_name=self.__name, log_level=self.__log_level
        )
        self.__parse_args()
        if self.__nodes is None:
            self.__nodes = PagesNode(socket.gethostname()).get_hblock_nodes()
        self.__log = logging.getLogger(__name__)
        if not self.__quiet:
            print(f"Initalizing the script {self.__name}")
            print(f"Please check Logfile: {self.__log_file} for detailed progress.")
        self.__log.info("*** %s Initializing ***", self.__name)
        self.__log.info("Initializing cvfs pages node for the local machine.")

    def __parse_args(self):
        """Parse the command line arguments."""
        # create an ArgumentParser object
        parser = argparse.ArgumentParser(
            description="This script is used to generate the network performance report for the CVFS HBlock nodes."
        )
        # create an argument
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
            "--nodes",
            help="The list of nodes to run the network performance tests.",
            nargs="+",
            required=False,
        )
        # parse the arguments from standard input
        self.__args = parser.parse_args()
        self.__debug = self.__args.debug
        self.__quiet = self.__args.quiet
        if self.__args.nodes is not None:
            self.__nodes = CVFSHelper.get_cvfs_node_objects(self.__args.nodes)

    def run(self):
        """Run the network performance tests.
        Returns:
            int - The return code.
                    0 - If the network performance tests are successful.
                    any other value - If the network performance tests are unsuccessful.
        """
        if not self.__quiet:
            print(
                "Starting the network performance tests. Results will be printed on the console once done."
            )
        self.__log.info(
            "Starting the network performance tests on the nodes %s .",
            self.__nodes,
        )
        stats = CVFSHelper.get_nodes_network_perf_stats(self.__nodes)
        stats_json = json.dumps(stats, indent=4)
        self.__log.info(
            "Network performance stats for each hblock node: \n%s", stats_json
        )
        if self.__quiet:
            print(stats_json)
        else:
            # print the network performance stats in tabular format
            for node, node_stats in stats.items():
                print(f"Node: {node}")
                for test, test_stats in node_stats.items():
                    print(f"\t{test}:")
                    print(f"\tintf: {test_stats['interface']}")
                    print(f"\t\tSend: {test_stats['sender_mbps']} Mbps")
                    print(f"\t\tReceive: {test_stats['receiver_mbps']} Mbps")
        return 0


if __name__ == "__main__":
    sys.exit(CVFSNetPerfReport().run())
