# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case

    Test Case:
            [Network & Firewall] : CvNetworkTestTool - Client & Server Mode

"""

import traceback
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Network.networkhelper import NetworkHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)   -  name of this test case
                applicable_os       (str)   —  applicable os for this test case
                product             (str)   —  applicable product for this test case
                features            (str)   —  qcconstants feature_list item
                show_to_user       (bool)   —  test case flag to determine if the test case is
                                                to be shown to user or not
                tcinputs            (dict)  -   test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : CvNetworkTestTool - Client & Server Mode"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "client_name": None,
            "unix_client_name": None
        }

        self.network_helper = None
        self.client_name = None
        self.commcell_ip = None
        self.machine_commcell = None
        self.unix_client_name = None

        # path to store server bat file
        self.server_bat_file = 'C:\\cvntesttool.bat'

    def setup(self):
        """Setup function of this test case"""
        try:
            self.log.info("Starting setup for Network Test Tool TestCase")
            self.network_helper = NetworkHelper(self)
            self.machine_commcell = Machine(self.commcell.commserv_name, self.commcell)
            cs_install_directory = self.commcell.clients.get(self.commcell.commserv_name).install_directory
            self.cs_machine_os = self.machine_commcell.os_info
            self.cs_command = self.machine_commcell.join_path(cs_install_directory, 'Base', 'CvNetworkTestTool')
            self.client_name = self.tcinputs['client_name']
            self.unix_client_name = self.tcinputs['unix_client_name']
            self.commcell_ip = self.machine_commcell.ip_address

            if not self.client_name:
                raise ValueError("Client name not provided in test case inputs")
            if not self.unix_client_name:
                raise ValueError("Unix client name not provided in test case inputs")

            self.log.info(
                f"Setup completed successfully. Client: {self.client_name}, Unix Client: {self.unix_client_name}")

        except Exception as exp:
            error_msg = f'Failed to setup test case. Error: {str(exp)}\n{traceback.format_exc()}'
            self.log.error(error_msg)
            self.result_string = error_msg
            self.status = constants.FAILED
            raise

    def run(self):
        self.log.info("*" * 10 + f" Started executing run function of testcase {self.id}" + "*" * 10)
        try:
            # DNS Lookup using hostname
            self.log.info("Performing DNS lookup using hostname")
            output = self.machine_commcell.execute_command(
                f'{self.cs_command} -lookup -hostname {self.commcell.clients.get(self.client_name).client_hostname}'
            ).output
            if 'DNS LOOKUP\t  : SUCCESS' not in output:
                raise Exception(f"DNS LOOKUP FAILED. Output: {output}")
            self.log.info("DNS lookup successful")

            # -servicecheck option
            self.log.info("Validating service check")
            output = self.machine_commcell.execute_command(f'{self.cs_command} -servicecheck').output
            self.validate_service_check(output)
            self.log.info("Service check validation successful")

            # -servicecheck -hostname target_machine
            self.log.info("Validating service check -hostname option")
            output = self.machine_commcell.execute_command(
                f'{self.cs_command} -servicecheck -hostname {self.commcell.clients.get(self.client_name).client_hostname}'
            ).output
            self.validate_service_check(output)
            self.log.info("Service check with hostname validation successful")

            # basic server client connection
            self.log.info("Validating basic server/client connection")
            output = self.network_helper.server_client_connection(self.client_name, self.server_bat_file)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info("Basic server/client connection validation successful")

            # server bindip with specified port
            self.log.info("Validating server/client connection with specified port")
            port_number = 23333
            output = self.network_helper.server_client_connection(self.client_name, self.server_bat_file,
                                                                  port_number=port_number)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info(f"Server/client connection validation with port {port_number} successful")

            # specifying option of buffer count and delay
            self.log.info("Validating interbufferdelay/buffercount options")
            buffer_count = 3000
            inter_buffer_delay = 1
            output = self.network_helper.server_client_connection(self.client_name, self.server_bat_file,
                                                                  inter_buffer_delay=inter_buffer_delay,
                                                                  buffer_count=buffer_count)
            self.validate_server_client(output, inter_buffer_delay, buffer_count)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info(
                f"Interbufferdelay/buffercount options validation successful. Buffer count: {buffer_count}, Delay: {inter_buffer_delay}")

            # firewalled connection
            self.log.info("Validating server/client with firewalled connection")
            output = self.network_helper.server_client_connection(self.client_name, self.server_bat_file,
                                                                  firewalled=True)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info("Firewalled connection validation successful")

            # UNIX CLIENT
            self.log.info("Validating cvnetworktesttool with UNIX Client")
            # basic server client connection
            self.log.info("Validating basic server/client connection for UNIX client")
            output = self.network_helper.server_client_connection(self.unix_client_name, self.server_bat_file,
                                                                  is_unix_client=True)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info("Basic server/client connection validation for UNIX client successful")

            # server bindip with specified port
            self.log.info("Validating server/client connection with specified port for UNIX client")
            port_number = 23333
            output = self.network_helper.server_client_connection(self.unix_client_name, self.server_bat_file,
                                                                  port_number=port_number,
                                                                  is_unix_client=True)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info(f"Server/client connection validation with port {port_number} for UNIX client successful")

            # specifying option of buffer count and delay
            self.log.info("Validating interbufferdelay/buffercount options for UNIX client")
            buffer_count = 3000
            inter_buffer_delay = 1
            output = self.network_helper.server_client_connection(self.unix_client_name, self.server_bat_file,
                                                                  inter_buffer_delay=inter_buffer_delay,
                                                                  buffer_count=buffer_count, is_unix_client=True)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info(
                f"Interbufferdelay/buffercount options validation for UNIX client successful. Buffer count: {buffer_count}, Delay: {inter_buffer_delay}")

            # Buffer Size
            self.log.info("Validating buffersize options for UNIX client")
            buffer_size = 100  # size in kb
            output = self.network_helper.server_client_connection(self.unix_client_name, self.server_bat_file,
                                                                  buffer_size=buffer_size,
                                                                  is_unix_client=True)
            self.validate_server_client(output)
            self.machine_commcell.kill_process('cvnetworktesttool')
            self.log.info(f"Buffersize options validation for UNIX client successful. Buffer size: {buffer_size}kb")

            # validate -help option
            self.log.info("Validating server/client -help options")
            help_command = 'cvnetworktesttool -{} -help'
            if self.cs_machine_os == 'UNIX':
                help_command = self.cs_command + ' -{} -help'
            # self.log.info(f"Server help command: {help_command.format('server')}")
            # Cannot uncomment these lines as the execute command in the linux is not working
            # server_help_output = self.machine_commcell.execute_command(help_command.format('server')).output
            # client_help_output = self.machine_commcell.execute_command(help_command.format('client')).output
            # self.validate_help_option(server_help_output, client_help_output)
            # self.log.info("Help options validation successful")
            #
            # self.log.info("*" * 10 + f" TestCase {self.id} successfully completed! " + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            error_msg = f'Failed to execute test case. Error: {str(exp)}\n{traceback.format_exc()}'
            self.log.error(error_msg)
            self.result_string = error_msg
            self.status = constants.FAILED
            raise

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info("Starting tear down process")
            if self.machine_commcell.check_file_exists(self.server_bat_file):
                self.machine_commcell.delete_file(self.server_bat_file)
                self.log.info(f"Deleted server bat file: {self.server_bat_file}")

            if self.machine_commcell.is_process_running("cvnetworktesttool"):
                self.machine_commcell.kill_process('cvnetworktesttool')
                self.log.info("Killed cvnetworktesttool process")

            self.log.info("Tear down completed successfully")
        except Exception as exp:
            error_msg = f'Failed to tear down test case. Error: {str(exp)}\n{traceback.format_exc()}'
            self.log.error(error_msg)
            self.result_string = error_msg
            self.status = constants.FAILED

    def validate_service_check(self, output):
        """ Validates the service check command

        Args:
            output: Output of service check command

        Raises:
            Exception if service check fails
        """
        services = {"Job Manager", 'Media & Library Manager', 'Application Manager', 'Commands Manager',
                    'Media Mount Manager', 'JobControlCVD', 'CDRSvc', 'FLRPort', 'Client Manager Service',
                    'Communications Service'}

        missing_services = [service for service in services if service not in output]
        if missing_services:
            raise Exception(
                f'SERVICE CHECK FAILED. The following services were not found: {", ".join(missing_services)}')


    def validate_server_client(self, output, inter_buffer_delay=None, buffer_count=None):
        """ Validates server/client connection output

        Args:
            output: Output of terminal
            inter_buffer_delay: inter buffer delay amount
            buffer_count: buffer count amount

        Raises:
            Exception for incorrect output
        """
        if inter_buffer_delay:
            if 'SendInterBuffDelay : {}'.format(inter_buffer_delay) not in output:
                raise Exception("Inter buffer delay error")
            if 'RecvInterBuffDelay : {}'.format(inter_buffer_delay) not in output:
                raise Exception("Inter buffer delay error")

        if buffer_count:
            if 'Buffers            : {}'.format(buffer_count) not in output:
                raise Exception("Buffer count error")

        if 'Status\t\t: Pass' not in output:
            raise Exception("CLIENT SERVER CHECK FAILED")

    def validate_help_option(self, server_help_output, client_help_output):
        """ Validating the help option of client/server commands

        Args:
            server_help_output: server help output
            client_help_output: client help output

        Raises:
            Exception if incorrect output
        """
        server_help_messsage = '\r\nServer Mode Usage:\r\n       [-BindIP <IP>] (Required) \r\n  ' \
                               '     [-SrvPort <PortNum>]\r\n       [-Log <LogFileName>]\r\n     ' \
                               '  [-Help]\r\n\r\n\r\n ' \
                               ' Press ESC to stop the server after it has started \r\n\r\n\r\n ' \
                               ' -BindIP\t\tThe ip address to bind to\r\n  -SrvPort <PortNum> ' \
                               '   The port number of Server. 25000 is default\r\n  -log <LogFileName>' \
                               '    Name of the log file including path (Optional) \r\n  -Help      ' \
                               '           Display this help screen\r\n'

        client_help_message = "\r\nClient Mode Usage:" \
                              "\r\n\t[-SrvHostName <IPAddr> | [-SrvHostName <HostName>]] (Required) " \
                              "\r\n\t[-SrvPort <PortNum>]" \
                              "\r\n\t[-SrvClientName <ClientName>]" \
                              "\r\n\t[-FirstBufferDelay <Delay>]" \
                              "\r\n\t[-InterBufferDelay <Delay>]" \
                              "\r\n\t[-BuffsizeClientToServer <BufSize>]" \
                              "\r\n\t[-BuffsizeServerToClient <BufSize>]" \
                              "\r\n\t[-BufferCount <count>]" \
                              "\r\n\t[-PingBufferSize <size in bytes>]" \
                              "\r\n\t[-PingBufferCount <Count>]" \
                              "\r\n\t[-PingTimeout <time in seconds>]" \
                              "\r\n\t[-Log <LogFileName>]" \
                              "\r\n\t[-Help]" \
                              "\r\n\r\n\r\n  Press ESC to stop the client after it has started " \
                              "\r\n\r\n\r\n  -SrvHostName <IPAddr>\tIP Address of the Server. Mandatory Parameter." \
                              "\r\n  -SrvPort <PortNum>\tThe port number of Server. 25000 is default" \
                              "\r\n  -SrvClientName <RemoteClientName> Server's Client name. Default is Empty" \
                              "\r\n  -FirstBufferDelay <Delay> Number of seconds to delay before sending or" \
                              "\r\n \t\t\t    receiving first buffer.0 seconds is default" \
                              "\r\n  -InterBufferDelay <Delay> Number of milli-seconds to delay before sending" \
                              "\r\n \t\t\t    or receiving each buffer.0 is default" \
                              "\r\n  -BuffsizeClientToServer <BufSize> The size of the buffer (KB) to transmit" \
                              "\r\n \t\t\t\t    from client to server.16 KB is default\r\n" \
                              "  -BuffsizeServerToClient <BufSize> The size of the buffer (KB) to transmit" \
                              "\r\n \t\t\t\t    from server to client.16 KB is default\r\n" \
                              "  -BufferCount<Count> Send/Recieve <Count> buffers of random data to/from" \
                              "\r\n \t\t      server. 10000 is default count" \
                              "\r\n  -log <LogFileName>   Name of the log file including path (Optional)" \
                              " \r\n  -Help                Display this help screen\r\n"

        # server
        if server_help_output != server_help_messsage:
            self.log.info(server_help_output)
            self.log.info("Here is the expected message \n\n")
            self.log.info(server_help_messsage)
            raise Exception("Server help message invalid")

        # client
        if client_help_output != client_help_message:
            raise Exception("Client help message invalid")
