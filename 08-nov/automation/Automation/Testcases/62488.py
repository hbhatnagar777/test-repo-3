# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """
    [Network & Firewall] : Performance test tool 
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Performance test tool"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "server": None,
            "client1": None,
            "client2": None,
            "email": None
        }
        self.network_helper = None
        self.server = None
        self.client1 = None
        self.client2 = None
        self.server_machine = None
        self.client_machine = None
        self.server_object = None
        self.client1_object = None
        self.client2_object = None
        self.client_stream_cmd = None
        self.client_config_cmd = None
        self.server_instance = None
        self.client_instance = None
        self.connections = None
        self.server_cmd = None
        self.server_ip = None
        self.client_ip = None
        self.recipients = None
        self.tunnel = None
        self.stream = None
        self.max_time = None
        self.bufsize = None
        self.results = None
        self.machine_throughput = None

        # Protocols
        self.proto = ['http', 'https', 'httpsa', 'raw']

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.log.info(f"[+] Running setup function. [+]")
            self.server = self.tcinputs["server"]
            self.client1 = self.tcinputs["client1"]
            self.client2 = self.tcinputs["client2"]
            self.recipients = self.tcinputs["email"]

            # Default parameters
            self.tunnel = self.tcinputs.get("tunnel", 1)
            self.bufsize = self.tcinputs.get("bufsize", 65536)
            self.connections = self.tcinputs.get("connections", 1)
            self.max_time = self.tcinputs.get("maxTime", 300)

            self.log.info(f"[+] Creating client objects [+]")
            self.stream = [1, 8]
            self.server_object = self.commcell.clients.get(self.server)
            self.client1_object = self.commcell.clients.get(self.client1)
            self.client2_object = self.commcell.clients.get(self.client2)
            self.server_machine = Machine(self.server_object)
            self.client_machine = Machine(self.client1_object)
            self.server_ip = self.server_machine.ip_address
            self.client_ip = self.client_machine.ip_address
            self.client_instance = [self.client1_object.instance, self.client2_object.instance]
            self.results = {1: {self.client_instance[0]: {}, self.client_instance[1]: {}},
                            8: {self.client_instance[0]: {}, self.client_instance[1]: {}}}
            self.network_helper = NetworkHelper(self)
        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def run(self):
        self.log.info("Started executing testcase : %s", self.id)
        self.get_machine_throughput()
        for stream in self.stream:
            for client_instance in self.client_instance:
                for proto in self.proto:
                    self.execute_tool(client_instance, self.tunnel, stream, proto)

        for stream in self.stream:
            for proto in self.proto:
                if self.results[stream][self.client_instance[0]][proto] < self.results[stream][self.client_instance[0]][
                    proto] * 0.80:
                    self.send_email('FAILED')
                    raise Exception("Network throughput decrese by more than 25%")

        self.send_email('PASSED')

    def send_email(self, status):
        body = self.create_email_body(status)
        self.log.info(body)
        self.network_helper.email("NWPerformance@commvault.com", self.recipients, "CVFWD_TEST_TOOL Results", body)

    def create_email_body(self, status):
        ins_1_version = self.client1_object.service_pack
        ins_2_version = self.client2_object.service_pack

        body = f'''
<HTML>
<head>
<style> 
    #mytable {{
  font-family: Arial, Helvetica, sans-serif;
  border-collapse: collapse;

}}

#mytable td, #customers th {{
  border: 1px solid #ddd;
  padding: 8px;
  min-width: 100px;
}}


#mytable th {{
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: center;
  background-color: #04AA6D;
  color: white;
}}

#throughput {{
color: green;
}}

</style>
</head>
    <body>
    Hi, <br>
    <br>
    Test case 62488 <span style="color:{'green' if status == 'PASSED' else 'red'}"> {status} </span> <br>
    <br>
    Network throughput comparison between {ins_1_version} and {ins_2_version} by 
    executing CVFWD_test_* tool on {self.server} machine and {self.client1} machine. <br>
    Network throughput (Direct connection without tunnel) between the machine is <b id="throughput"> {self.machine_throughput}  MBPS </b>
    For this test, teamed 10GB NIC is been used with server IP {self.server_ip} and client IP {self.client_ip}. <br><br>

    <b id="throughput">Max network throughput: {self.machine_throughput} MBPS</b>
    <br><br>
     <table id="mytable">
        <tr> 
            <th>Parameter</th>
            <th>Value</th>
        </tr>
        <tr>
            <td> Protocol </td>
            <td> httpsa, https, http, raw</td>
        </tr>
        <tr>
            <td> connections </td>
            <td> 1</td>
        </tr>
        <tr>
            <td> Buffer size </td>
            <td>{self.bufsize}</td>
        </tr>
        <tr>
            <td> Time </td>
            <td>{self.max_time} Seconds</td>
        </tr>
     </table>
    <br>
    <br>
    <table id="mytable">
        <caption><b>Throughput with 1 stream</b></caption>
        <tr> 
            <th> </th>
            <th>SP-{ins_1_version}</th>
            <th>SP-{ins_2_version}</th>
        </tr>
        <tr>
            <td> httpsa </td>
            <td> {self.results[1]['Instance001']['httpsa']} MBPS</td>
            <td> {self.results[1]['Instance002']['httpsa']} MBPS</td>
        </tr>
        <tr>
            <td> https </td>
            <td> {self.results[1]['Instance001']['https']} MBPS</td>
            <td> {self.results[1]['Instance002']['https']} MBPS</td>
        </tr>
        <tr>
            <td> http </td>
            <td> {self.results[1]['Instance001']['http']} MBPS</td>
            <td> {self.results[1]['Instance002']['http']} MBPS</td>
        </tr>
        <tr>
            <td> raw </td>
            <td> {self.results[1]['Instance001']['raw']} MBPS</td>
            <td> {self.results[1]['Instance002']['raw']} MBPS</td>
        </tr>
    </table>
    <br><br>
    <table id="mytable">
        <caption><b>Throughput with 8 stream</b></caption>
        <tr> 
            <th> </th>
            <th>SP-{ins_1_version}</th>
            <th>SP-{ins_2_version}</th>
        </tr>
        <tr>
            <td> httpsa </td>
            <td> {self.results[8]['Instance001']['httpsa']} MBPS</td>
            <td> {self.results[8]['Instance002']['httpsa']} MBPS</td>
        </tr>
        <tr>
            <td> https </td>
            <td> {self.results[8]['Instance001']['https']} MBPS</td>
            <td> {self.results[8]['Instance002']['https']} MBPS</td>
        </tr>
        <tr>
            <td> http </td>
            <td> {self.results[8]['Instance001']['http']} MBPS</td>
            <td> {self.results[8]['Instance002']['http']} MBPS</td>
        </tr>
        <tr>
            <td> raw </td>
            <td> {self.results[8]['Instance001']['raw']} MBPS</td>
            <td> {self.results[8]['Instance002']['raw']} MBPS</td>
        </tr>
    </table>

    <br>  
    Thanks!
    </body>
</HTML>'''
        return body

    def execute_tool(self, client_instance, tunnel, stream, proto):
        # Below are the command need to be executed.
        self.client_stream_cmd = f'cvfwd_test_clnt.exe -vm {client_instance} -stream -server ' \
                                 f'"{self.server}:{self.server_ip}:testservice1" -tunnels {tunnel} ' \
                                 f'-connections {self.connections} -data -bufsize {self.bufsize} -maxtime {self.max_time} '

        self.client_config_cmd = f'cvfwd_test_clnt -vm {client_instance} -config -server ' \
                                 f'"{self.server}:{self.server_ip}:{self.server_object.network.tunnel_connection_port}"' \
                                 f' -routes 1 -streams {stream} -proto {proto}'
        self.server_cmd = f'cvfwd_test_svc -vm {self.server_instance} -svc testservice1'
        self.log.info(
            f"Going to run the below commands:\n{self.client_stream_cmd}\n{self.client_config_cmd}\n{self.server_cmd}")

        # Running tool for all the protocols.
        throughtput = self.get_throughput(self.client_config_cmd)
        self.results[stream][client_instance][proto] = throughtput

    def get_throughput(self, config_cmd):
        """
        This function runs the on remote machines.

            Args:
                Config_cmd  -- Configuration command to be run on remote machine

            Return:
                float       -- Maximum badthwidth acheived.

            Raises:
                Exception:
                    if any error occurred while executing the commands

        """
        op = self.client1_object.execute_command(config_cmd)
        if op[0] == 1:
            raise Exception(f"Failed to execute {config_cmd}")
        self.log.info(str(op))
        self.log.info("Restarting client CVFWD service")
        self.client1_object.restart_service('cvfwd')
        time.sleep(30)
        op = self.server_object.execute_command(self.server_cmd, wait_for_completion=False)
        if op[0] == 1:
            raise Exception(f"Failed to execute {self.server_cmd}")
        self.log.info(str(op))
        time.sleep(10)
        op = self.client1_object.execute_command(self.client_stream_cmd)
        if op[0] == 1:
            raise Exception(f"Failed to execute {self.client_stream_cmd}")
        self.log.info(str(op))
        self.log.info(op[1])
        numbers = [-1]
        for line in op[1].split('\n'):
            if 'MB/s' in line:
                idx = line.find(', ')
                numbers.append(float(line[idx + 2:idx + 7]))

        return max(numbers)

    def get_machine_throughput(self):
        """
        This function will calculate the throughput between 2 machines.
        Note*: iperf3.exe must be present between those 2 machines base folder.
        """
        iperf_server_cmd = "iperf3.exe -s"
        op = self.server_object.execute_command(iperf_server_cmd, wait_for_completion=False)
        if op[0] == 1:
            raise Exception(f"Failed to execute {iperf_server_cmd} in {self.server}")

        iperf_client_cmd = f'''iperf3.exe -c {self.server_ip} -n 99999999999 -l 504800 -f Mbytes | findstr /i "receiver" | findstr /i "Mbytes/sec" | for /f "tokens=7" %a in ('more') do @echo %a'''
        op = self.client1_object.execute_command(iperf_client_cmd)
        if op[0] == 1:
            raise Exception(f"Failed to execute {iperf_client_cmd} in {self.client1}")
        self.log.info(f"Throughput of machines using iperf3 is {op}")
        self.machine_throughput = round(float(op[1]))
        op = self.server_object.execute_command("taskkill /IM iperf3.exe /F", wait_for_completion=False)
        if op[0] == 1:
            raise Exception(f"Failed to execute 'taskkill /IM iperf3.exe /F' in {self.server}")
