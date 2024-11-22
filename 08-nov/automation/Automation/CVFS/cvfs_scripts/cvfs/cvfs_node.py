"""This module is used to represent the cvfs node, its properties and functions."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import RLock

from .connections import SSHConnection
from .cvfs_constants import CVFSConstants


class CVFSNode:
    """This class is used to represent the cvfs node."""

    def __init__(
        self,
        hostname,
        connection_pool_size=CVFSConstants.CONNECTION_POOL_SIZE,
        user_name=CVFSConstants.SSH_USER,
        key_filename=CVFSConstants.SSH_KEYPATH,
    ):
        """Initialize the CVFSNode object with the provided parameters.

        Args:
            hostname (str): The hostname of the cvfs node.
            connection_pool_size (int): The size of the SSH connection pool.
                default: CVFSConstants.CONNECTION_POOL_SIZE
            user_name (str): The username to connect to the cvfs node.
                default: CVFSConstants.SSH_USER
            key_filename (str): The path to the SSH private key file.
                default: CVFSConstants.SSH_KEYPATH
        """
        self.__hostname = hostname
        self._user_name = user_name
        self._key_filename = key_filename
        self._connection_pool_size = connection_pool_size
        self.__log = logging.getLogger(__name__)
        self.__lock = RLock()
        self.__connection_pool_size = connection_pool_size
        self._ssh_connection = None
        self._interfaces = {}
        self.__mount_to_disk_map = {}  # /hedvig/d3 -> sda
        self.__os_name = None
        self.__os_version = None
        self.__init_node_info()

    @property
    def hostname(self):
        """Return the hostname of the cvfs node."""
        return self.__hostname

    @property
    def os_name(self):
        """Return the OS name of the cvfs node."""
        return self.__os_name

    @property
    def os_version(self):
        """Return the OS version of the cvfs node."""
        return self.__os_version

    def execute_command(self, cmd, cmd_args="", check_return_code=False):
        """This method is used to execute the command on the cvfs node.

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

        exit_code = -1

        cmd = f"{cmd} {cmd_args}"
        output = self._ssh_connection.exec_command(cmd)
        self.__log.debug(
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
        exit_code = output.return_code
        if check_return_code and exit_code != 0:
            self.__log.error(
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

    def collect_aggregate_net_perf(self, cvfs_nodes):
        """This method is used to collect the aggregate network performance stats by running iperf server.

        Args:
            cvfs_nodes (list): List of other CVFSNode objects where iperf clients will be started.
        Returns:
            dict -  dictionary containing the aggregate network throughput for all networks in mbps.
                    {
                        "bond1": {
                            "sender_mbps": 10000.00,
                            "receiver_mbps": 10000.00
                        }
                        "bond2": {
                            "sender_mbps": 10000.00,
                            "receiver_mbps": 10000.00
                        }
                    }
        """
        cvfs_nodes_except_self = []
        # assert that only cvfs nodes are passed
        for cvfs_node in cvfs_nodes:
            assert isinstance(cvfs_node, CVFSNode), (
                f"Invalid object {cvfs_node} in cvfs_nodes. "
                "Only CVFSNode objects are allowed."
            )
            if cvfs_node.hostname != self.__hostname:
                cvfs_nodes_except_self.append(cvfs_node)
        self.__log.info(
            "Collecting aggregate network performance stats with sevrver on %s and clients %s",
            self.__hostname,
            cvfs_nodes_except_self,
        )
        result_dict = {}
        # use futures to run the iperf clients in parallel
        for interface_item in self._interfaces.items():
            interface_type = interface_item[0]
            interface = interface_item[1]
            result_dict[interface_type] = {
                "interface": interface,
                "sender_mbps": 0.0,
                "receiver_mbps": 0.0,
            }
            iperf_ports = []
            try:
                iperf_ports = self.__start_iperf_servers(
                    interface, len(cvfs_nodes_except_self)
                )
                with ThreadPoolExecutor(
                    max_workers=len(cvfs_nodes_except_self)
                ) as executor:
                    futures = [
                        executor.submit(
                            self.__collect_stats_parallel,
                            cvfs_node,
                            interface_type,
                            port,
                        )
                        for cvfs_node, port in zip(cvfs_nodes_except_self, iperf_ports)
                    ]
                    stats = [future.result() for future in futures]
                    for stat in stats:
                        # client stats are reversed as the server is on the cvfs node
                        result_dict[interface_type]["sender_mbps"] += stat[
                            "receiver_mbps"
                        ]
                        result_dict[interface_type]["receiver_mbps"] += stat[
                            "sender_mbps"
                        ]
                    # round off the values to 2 decimal places
                    result_dict[interface_type]["sender_mbps"] = round(
                        result_dict[interface_type]["sender_mbps"], 2
                    )
                    result_dict[interface_type]["receiver_mbps"] = round(
                        result_dict[interface_type]["receiver_mbps"], 2
                    )

            except Exception as e:
                self.__log.error(
                    "Failed to collect aggregate network performance stats: %s", e
                )
                self.__kill_iperf_servers(iperf_ports)
                raise e
        return result_dict

    def find_disk_by_mount_point(self, mount_point, refresh=True):
        """This method is used to find the disk name given its mount point.

        Args:
            mount_point (str): Mount point of the disk.
        Returns:
            str -   name of the disk
        """
        if refresh:
            self.__initialize_mount_to_disk_map()

        with self.__lock:
            if mount_point in self.__mount_to_disk_map:
                return self.__mount_to_disk_map[mount_point]
        raise ValueError(f"No disk found with mount point: {mount_point}")

    def find_disk_by_uuid(self, target_uuid):
        """This method is used to find the disk name given its uuid.
        Args:
            UUID of the disk.
        Returns:
            String - name of the disk

        """

        command = CVFSConstants.BLKID_COMMAND
        output = self.execute_command(command, check_return_code=True)

        for line in output.stdout.splitlines():
            if target_uuid in line:
                disk_name = line.split(":")[0]
                return disk_name

        # If no matching UUID is found, raise a custom exception
        raise ValueError(f"No disk found with UUID: {target_uuid}")

    def trigger_disk_failure(self, mount_point):
        """This method is used to trigger the disk failure for the given mount point.
        Args:
            mount_point (str): Mount point of the disk.
        Returns:
            None
        """
        self.__log.info(
            "Attempting to find disk for mount point: %s on host: %s",
            mount_point,
            self.__hostname,
        )

        # Find the disk name for the given mount point
        disk_name = self.find_disk_by_mount_point(mount_point)
        self.__log.info(
            "Disk mapped: %s for mount point: %s on host: %s",
            disk_name,
            mount_point,
            self.__hostname,
        )

        # Form the command to fail the disk
        command = CVFSConstants.SCSI_DELETE_CMD.format(disk_name)
        self.__log.warning(
            "Executing disk failure command on %s: %s", self.__hostname, command
        )
        output = self.execute_command(
            command, check_return_code=True
        )  # Exception handled in execute_command
        self.__log.info("Disk failure command executed successfully: %s", output.stdout)

    def enable_disks(self):
        """This method is used to enable the failed disks on the node."""
        command = f"sh {CVFSConstants.ENABLE_DRIVES_SCRIPT}"
        # To enable the failed disks , running the enables_drives.sh on the node
        self.__log.info("Enabling drives on the node!")
        output = self.execute_command(command, check_return_code=True)
        self.__log.info("Enabling drives successful: %s", output.stdout)

    def manage_services(self, service_name, operation):
        """
        This method is used to manage the services on the node.
        Args:
            service_name (str): Name of the service to be managed.
                                Valid values are in CVFSConstants.SERVICES
            operation (str): Operation to be performed on the service.
                                Valid values are in CVFSConstants.SYSTEMCTL_OPERATIONS for Hedvig services
                                and CVFSConstants.COMMVAULT_OPERATIONS for Commvault service
        Returns:
            str -   stdout of the operation
        Raises:
            ValueError: If the service name or operation is invalid.
            AssertionError: If the return code of the command is not 0.

        """
        self.__log.info(
            "Managing service: %s on node: %s with operation: %s",
            service_name,
            self.__hostname,
            operation,
        )
        if not service_name in CVFSConstants.SERVICES:
            raise ValueError(f"Invalid service name: {service_name}")
        if service_name == CVFSConstants.COMMVAULT_SERVICE:
            if not operation in CVFSConstants.COMMVAULT_OPERATIONS:
                raise ValueError(
                    f"Invalid operation: {operation} for Commvault service"
                )
            command = f"{CVFSConstants.COMMVAULT_SERVICE} {operation}"
            return self.execute_command(command, check_return_code=True).stdout
        if not operation in CVFSConstants.SYSTEMCTL_OPERATIONS:
            raise ValueError(
                f"Invalid operation: {operation} for {service_name} service"
            )
        command = CVFSConstants.SYSTEMCTL_CMD.format(operation, service_name)
        return self.execute_command(command, check_return_code=True).stdout

    def pause_selinux_protection(self):
        """
        This method is used to pause the selinux protection on the node.
        """
        self.__log.info("Pausing selinux protection on node: %s", self.__hostname)
        command = CVFSConstants.SELINUX_PAUSE_PROTECTION_CMD
        self.execute_command(command, check_return_code=True)

    def resume_selinux_protection(self):
        """
        This method is used to resume the selinux protection on the node.
        """
        self.__log.info("Resuming selinux protection on node: %s", self.__hostname)
        command = CVFSConstants.SELINUX_RESUME_PROTECTION_CMD
        self.execute_command(command, check_return_code=True)

    def wipe_pages_node(self):
        """
        This method is used to wipe the pages metadata on the node.
        """
        self.__log.info("Wiping pages node: %s", self.__hostname)
        # Stopping the pages service
        self.manage_services(
            CVFSConstants.HEDVIG_PAGES_SERVICE, CVFSConstants.STOP_OPERATION
        )
        # Pausing the protection before wiping the pages node
        self.pause_selinux_protection()
        # Wiping the pages node
        self.execute_command(CVFSConstants.WIPE_NVME_CMD, check_return_code=True)
        # resuming the protection after the NVME drives are wiped
        self.resume_selinux_protection()

    def __init_node_info(self):
        """
        This method is used to initialize the cvfs node information
        """
        self._ssh_connection = SSHConnection(
            host=self.__hostname,
            username=self._user_name,
            key_filename=self._key_filename,
            max_connections=self.__connection_pool_size,
        )
        self.__initialize_interfaces()
        self.__initialize_mount_to_disk_map()
        self.__initialize_os_info()

    def __initialize_os_info(self):
        """This method is used to initialize the OS information."""
        self.__log.info("Initializing OS information for %s", self.__hostname)
        output = self.execute_command(
            CVFSConstants.GET_OS_NAME_CMD, check_return_code=True
        )
        self.__os_name = output.stdout.strip()
        output = self.execute_command(
            CVFSConstants.GET_OS_VERSION_CMD, check_return_code=True
        )
        self.__os_version = output.stdout.strip()
        self.__log.info(
            "Hostname: %s OS information: %s %s",
            self.__hostname,
            self.__os_name,
            self.__os_version,
        )

    def __initialize_mount_to_disk_map(self):
        """This method is used to initialize the mount to disk map."""
        self.__log.info("Initializing mount to disk map for %s", self.__hostname)
        lines = (
            self.execute_command(
                CVFSConstants.LS_BLK_DISK_COMMAND, check_return_code=True
            )
            .stdout.strip()
            .splitlines()
        )
        for line in lines:
            parts = line.split()
            if len(parts) < 2:
                continue
            disk_name = parts[0]
            mount_point = parts[1]
            with self.__lock:
                self.__mount_to_disk_map[mount_point] = disk_name
        with self.__lock:
            self.__log.info("Mount to disk map: %s", self.__mount_to_disk_map)

    def __initialize_interfaces(self):
        """This method is used to initialize the network interfaces."""
        # Get the network interfaces for all network types
        self.__log.info("Initializing network interfaces for %s", self.__hostname)
        for network_type in CVFSConstants.NETWORK_TYPES:
            interface_name = self.__get_network_interface(network_type)
            if interface_name is not None and interface_name != "":
                interface_ip = self.__get_network_interface_ip(interface_name)
                self._interfaces[network_type] = {
                    "name": interface_name,
                    "ip": interface_ip,
                }
        self.__log.info(
            "Network interfaces initialized successfully for %s", self.__hostname
        )
        self.__log.info("Network interfaces: %s", self._interfaces)

    def __get_network_interface(self, network_type):
        """This method is used to get the network interface for the provided network type.

        Args:
            network_type (str): Network type from CVFSConstants.NETWORK_TYPES.
        Returns:
            str -   network interface name
        """
        assert network_type in CVFSConstants.NETWORK_TYPES, (
            f"Invalid network type {network_type}. "
            f"Allowed network types: {CVFSConstants.NETWORK_TYPES}"
        )
        self.__log.info("Getting network interface for %s", network_type)
        cmd = CVFSConstants.GET_NWINT_CMD.format(network_type)
        output = self.execute_command(cmd, check_return_code=True)
        interface_name = output.stdout.strip()
        self.__log.info("Network interface for %s: %s", network_type, interface_name)
        return interface_name

    def __get_network_interface_ip(self, interface_name):
        """This method is used to get the IP address of the provided network interface.

        Args:
            interface_name (str): Network interface name.
        Returns:
            str -   IP address of the network interface
        """
        self.__log.info("Getting IP address for interface %s", interface_name)
        cmd = CVFSConstants.GET_NWINT_IP_CMD.format(interface_name)
        output = self.execute_command(cmd, check_return_code=True)
        return output.stdout.strip()

    def __start_iperf_servers(self, interface, count):
        """This method is used to start the iperf server on the cvfs node.

        Args:
            interface (str): Network interface on which the iperf server should be started.
            count (int): Number of iperf servers to start.
        Raises:
            OSError: If the iperf server is not started successfully.

        Returns:
            list -  list of ports which the iperf servers are started
                    [port1, port2, ...]
        """
        self.__log.info("Starting iperf servers on %s", self.__hostname)
        iperf_ports = []
        used_ports = self.__get_used_ports()
        port_start = CVFSConstants.IPERF_PORT_START
        port_end = CVFSConstants.IPERF_PORT_END
        for _ in range(count):
            free_port = None
            for port in range(port_start, port_end):
                if port not in used_ports:
                    free_port = port
                    break
            if free_port is None:
                raise OSError("No free port available to start iperf server")
            port_start = free_port + 1
            cmd = CVFSConstants.START_IPERF_SERVER_CMD.format(
                interface["ip"], free_port
            )
            self.execute_command(cmd, check_return_code=True)
            self.__log.info("iperf server started on %s:%s", interface, free_port)
            iperf_ports.append(free_port)
        return iperf_ports

    def _start_collect_iperf_client_stats(  # pylint: disable=unused-private-member
        self, interface, server_interface, server_port
    ):
        """This method is used to start the iperf client to collect the network stats.

        Args:
            interface (dict): Interface of the iperf client.
            server_interface (dict): Interface of the iperf server.
            server_port (int): Port of the iperf server.
        Returns:
            dict -  dictionary containing the iperf client stats
                    {
                        "sender_mbps": 10000.00,
                        "receiver_mbps": 10000.00
                    }
        """
        self.__log.info(
            "Starting iperf client on %s to collect stats from %s:%s",
            interface["ip"],
            server_interface["ip"],
            server_port,
        )
        cmd = CVFSConstants.START_IPERF_CLIENT_CMD.format(
            server_interface["ip"], interface["ip"], server_port
        )
        end_json = json.loads(
            self.execute_command(cmd, check_return_code=True).stdout.strip()
        )["end"]
        self.__log.debug("iperf client end stats: %s", end_json)
        sender_mbps = end_json["sum_sent"]["bits_per_second"] / 1000000
        receiver_mbps = end_json["sum_received"]["bits_per_second"] / 1000000
        return {"sender_mbps": sender_mbps, "receiver_mbps": receiver_mbps}

    def __get_used_ports(self):
        """This method is used to get the list of used ports on the cvfs node.

        Returns:
            list -  list of used ports
        """
        self.__log.debug("Getting used ports on %s", self.__hostname)
        ports = []
        for port_str in self.execute_command(
            CVFSConstants.GET_USED_PORTS_CMD, check_return_code=True
        ).stdout.split():
            try:
                ports.append(int(port_str))
            except ValueError:
                continue
        self.__log.debug("Used ports: %s", ports)
        return ports

    def __kill_iperf_servers(self, iperf_ports):
        """This method is used to kill the iperf servers.

        Args:
            iperf_ports (list): List of iperf ports.
        """
        for port in iperf_ports:
            cmd = CVFSConstants.KILL_IPERF_SERVER_ON_PORT_CMD.format(port)
            self.__log.info("killing iperf server on %s:%s", self.__hostname, port)
            self.execute_command(cmd, check_return_code=False)

    def __collect_stats_parallel(self, cvfs_node, interface_type, port):
        """This method is used to collect the stats in parallel.

        Args:
            cvfs_node (object): CVFSNode object.
            interface_type (str): Interface type.
            port (int): Port number.
        Returns:
            dict -  dictionary containing the iperf client stats
                    {
                        "sender_mbps": 10000.00,
                        "receiver_mbps": 10000.00
                    }
        """
        assert isinstance(cvfs_node, CVFSNode), (
            f"Invalid object {cvfs_node} in cvfs_node. "
            "Only CVFSNode objects are allowed."
        )
        return cvfs_node._start_collect_iperf_client_stats(  # pylint: disable=protected-access
            cvfs_node._interfaces[interface_type],  # pylint: disable=protected-access
            self._interfaces[interface_type],
            port,
        )

    def __str__(self):
        """Return the string representation of the CVFSNode object."""
        return self.__hostname

    def __repr__(self):
        """Return the string representation of the CVFSNode object."""
        return self.__str__()
