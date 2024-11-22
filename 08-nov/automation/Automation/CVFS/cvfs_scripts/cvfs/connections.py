"""
This module represents the abstract base class for managing all types of connections(ssh, thrift etc)
It provides a connection pool in a thread safe manner.
"""

import importlib
import logging
import sys
import threading
from abc import ABC, abstractmethod

import paramiko
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport

from .cvfs_constants import CVFSConstants
from .output_formatter import UnixOutput


class ConnectionPool(ABC):
    """
    ConnectionPool class is used to manage all types of connections(ssh, thrift etc)
    It provides a connection pool in a thread safe manner.
    """

    def __init__(self, max_connections=CVFSConstants.CONNECTION_POOL_SIZE):
        """
        Initialize the connection pool with the maximum number of connections.

        Args:
            max_connections: The maximum number of connections which are retained in the connection pool.
        """
        self.__max_connections = max_connections
        self.__connection_lock_tuples = []
        self.__lock = threading.RLock()
        self.__log = logging.getLogger(__name__)

    def _get_connection(self):
        """
        Get a connection from the connection pool.

        Returns:
            tuple: A connection object and a lock object.
        """
        with self.__lock:
            while len(self.__connection_lock_tuples) > 0:
                _connection_lock_tuple = self.__connection_lock_tuples.pop()
                if self._is_connection_alive(_connection_lock_tuple):
                    self.__log.debug(
                        "Reusing an existing connection from the pool %s",
                        _connection_lock_tuple,
                    )
                    return _connection_lock_tuple

            _connection_lock_tuple = self._create_connection()
            self.__log.debug("Returning a new connection %s", _connection_lock_tuple)
            return _connection_lock_tuple

    @abstractmethod
    def _create_connection(self):
        """
        Create a new connection. This method should be implemented by the subclass.

        Returns:
            tuple: A connection object and a lock object.
        """

    @abstractmethod
    def _is_connection_alive(self, connection_lock_tuple):
        """
        Check if the connection is alive. This method should be implemented by the subclass.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """

    @abstractmethod
    def _close_connection(self, connection_lock_tuple):
        """
        Close the connection. This method should be implemented by the subclass.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """

    def _release_connection(self, connection_lock_tuple):
        """
        Release the connection back to the connection pool.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """
        with self.__lock:
            if len(
                self.__connection_lock_tuples
            ) < self.__max_connections and self._is_connection_alive(
                connection_lock_tuple
            ):
                self.__log.debug(
                    "Releasing the connection back to the pool %s",
                    connection_lock_tuple,
                )
                self.__connection_lock_tuples.append(connection_lock_tuple)
            else:
                self.__log.debug("Closing the connection %s", connection_lock_tuple)
                self._close_connection(connection_lock_tuple)

    def __del__(self):
        """
        Close all the connections in the connection pool.
        """
        with self.__lock:
            for connection_lock_tuple in self.__connection_lock_tuples:
                self._close_connection(connection_lock_tuple)
            self.__connection_lock_tuples.clear()

    def __getattr__(self, item):
        """
        Get the attribute from the underlying connection object.
        This will tale care of function calls and attribute access in thread safe manner.

        Args:
            item: The attribute name.
        Returns:
            The attribute value.
        """
        connection_lock_tuple = self._get_connection()
        self.__log.debug(
            "Getting attribute %s from the connection, %s", item, connection_lock_tuple
        )
        try:
            with connection_lock_tuple[1]:
                attr = getattr(connection_lock_tuple[0], item)
                if callable(attr):

                    def wrapper(*args, **kwargs):
                        with connection_lock_tuple[1]:
                            try:
                                return attr(*args, **kwargs)
                            finally:
                                self._release_connection(connection_lock_tuple)

                    return wrapper
                self._release_connection(connection_lock_tuple)
                return attr
        except Exception as e:
            self._release_connection(connection_lock_tuple)
            raise e


class SSHConnection(ConnectionPool):
    """
    SSHConnection class is used to manage the ssh connections.
    It provides a connection pool in a thread safe manner.
    """

    def __init__(
        self,
        host,
        username=None,
        key_filename=None,
        password=None,
        max_connections=CVFSConstants.CONNECTION_POOL_SIZE,
    ):
        """
        Initialize the SSHConnection object.

        Args:
            host: The hostname or IP address of the remote server.
            username: The username to use for the ssh connection.
                default: current local user
            key_filename: The private key file to use for the ssh connection.
                default: None
            password: The password to use for the ssh connection.
                default: None
            max_connections: The maximum number of connections which are retained in the connection pool.
                default: CVFSConstants.CONNECTION_POOL_SIZE
        """
        super().__init__(max_connections=max_connections)
        self.__host = host
        self.__username = username
        self.__password = password
        self.__key_filename = key_filename
        self.__log = logging.getLogger(__name__)

    def exec_command(
        self, command, bufsize=-1, timeout=None, get_pty=False, environment=None
    ):
        """
        Execute a command on the remote server.

        Args:
            command: The command to execute.
            bufsize: The buffer size.
                default: -1
            timeout: The timeout value.
                default: None
            get_pty: Get a pseudo-terminal.
                default: False
            environment: a dict of shell environment variables,
                        to be merged into the default environment that the remote command executes within.
                default: None
        Returns:
            object: cvfs.output_formatter.UnixOutput object.
                    It contains the stdout, stderr and return code of the command.
        """
        self.__log.debug("Executing command %s on %s", command, self.__host)
        connection_lock_tuple = self._get_connection()
        try:
            with connection_lock_tuple[1]:
                _, stdout, stderr = connection_lock_tuple[0].exec_command(
                    command, bufsize, timeout, get_pty, environment
                )
                output = stdout.read()
                error = stderr.read()
                while True:
                    while stdout.channel.recv_ready():
                        output = f"{output}{stdout.read()}"
                    while stderr.channel.recv_ready():
                        error = f"{error}{stderr.read()}"
                    if stdout.channel.exit_status_ready():
                        break
                exit_code = stdout.channel.recv_exit_status()
                return UnixOutput(exit_code, output.decode(), error.decode())
        finally:
            self._release_connection(connection_lock_tuple)

    def _create_connection(self):
        """
        Create a new ssh connection.

        Returns:
            tuple: A connection object and a lock object.
        """
        self.__log.debug("Creating a new ssh connection to %s", self.__host)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.__host,
            username=self.__username,
            password=self.__password,
            key_filename=self.__key_filename,
        )
        return ssh, threading.RLock()

    def _is_connection_alive(self, connection_lock_tuple):
        """
        Check if the ssh connection is alive.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """
        with connection_lock_tuple[1]:
            return connection_lock_tuple[0].get_transport().is_active()

    def _close_connection(self, connection_lock_tuple):
        """
        Close the ssh connection.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """
        with connection_lock_tuple[1]:
            self.__log.debug("Closing a ssh connection to %s", self.__host)
            connection_lock_tuple[0].close()


class ThriftConnection(ConnectionPool):
    """
    ThriftConnection class is used to manage the thrift connections.
    It provides a connection pool in a thread safe manner.
    """

    class ConnectionUnit:
        """
        ConnectionUnit class contains all the thrift connection properties encapsulated in a single object.
        """

        def __init__(self, socket, transport, protocol, client):
            """
            Initialize the ConnectionUnit object.

            Args:
                socket: The thrift socket object.
                transport: The thrift transport object.
                protocol: The thrift protocol object.
                client: The thrift client object.
            """
            self.__socket = socket  # pylint: disable=unused-private-member
            self.__transport = transport
            self.__protocol = protocol  # pylint: disable=unused-private-member
            self.__client = client

        def is_alive(self):
            """
            Check if the thrift connection is alive.

            Returns:
                bool: True if the connection is alive, False otherwise.
            """
            return self.__transport.isOpen()

        def close(self):
            """
            Close the thrift connection.
            """
            self.__transport.close()

        def __getattr__(self, item):
            """
            Get the attribute from the underlying client object.
            This will take care of function calls and attribute access.

            Args:
                item: The attribute name.
            Returns:
                The attribute value.
            """
            try:
                log = logging.getLogger(__name__)
                log.debug(
                    "Getting attribute %s from the thrift client on socket %s",
                    item,
                    self.__socket,
                )
                return getattr(self.__client, item)
            except AttributeError as exc:
                raise AttributeError(
                    f"Attribute {item} not found in the thrift client"
                ) from exc

    def __init__(
        self,
        host,
        port,
        module_name,
        module_path,
        max_connections=CVFSConstants.CONNECTION_POOL_SIZE,
    ):
        """
        Initialize the ThriftConnection object.

        Args:
            host: The hostname or IP address of the remote server.
            port: The port number of the thrift server.
            module: The module name of the thrift server.
            max_connections: The maximum number of connections which are retained in the connection pool.
                default: CVFSConstants.CONNECTION_POOL_SIZE
        """
        super().__init__(max_connections=max_connections)
        self.__host = host
        self.__port = port
        self.__module_name = module_name
        self.__module_path = module_path
        sys.path.append(self.__module_path)
        self.__module = importlib.import_module(self.__module_name)
        self.__log = logging.getLogger(__name__)

    def _create_connection(self):
        """
        Create a new thrift connection.

        Returns:
            tuple: A connection object and a lock object.
        """
        self.__log.debug(
            "Creating a new thrift connection to %s:%s with module_name %s and module_path %s",
            self.__host,
            self.__port,
            self.__module,
            self.__module_path,
        )
        socket = TSocket.TSocket(self.__host, self.__port, socket_keepalive=True)
        socket.setTimeout(CVFSConstants.RPC_TIMEOUT_IN_MS)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        transport.open()
        client = self.__module.Client(protocol)
        connection = ThriftConnection.ConnectionUnit(
            socket, transport, protocol, client
        )
        return connection, threading.RLock()

    def _is_connection_alive(self, connection_lock_tuple):
        """
        Check if the thrift connection is alive.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """
        with connection_lock_tuple[1]:
            return connection_lock_tuple[0].is_alive()

    def _close_connection(self, connection_lock_tuple):
        """
        Close the thrift connection.

        Args:
            connection_lock_tuple: A tuple of connection object and lock object.
        """
        with connection_lock_tuple[1]:
            self.__log.debug(
                "Closing a thrift connection to %s:%s with module %s",
                self.__host,
                self.__port,
                self.__module,
            )
            connection_lock_tuple[0].close()
