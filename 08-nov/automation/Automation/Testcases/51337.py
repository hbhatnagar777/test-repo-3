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

import re
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils import constants
import csv
import os


class ClientInfo:
    """Client Information Object Class """

    def __init__(self, id: int = 0, space: int = 0, time: int = 0, threashold: int = 0):
        self.id = int(id)
        self.space = int(space)
        self.time = int(time)
        self.threashold = int(threashold)


class TestCase(CVTestCase):
    """
    [Network]: Firewall Generation Calculation
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network]: Firewall Generation Calculation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "input": None,
            "server": None,
            "email": None,
            "SP": None,
        }

        self.server = None
        self.server_obj = None
        self.recipients = None
        self.input = None

        self.network_helper = None
        self.CVFWGEN_PATH = "cvfwgen.exe"
        self.cvfwgen_client_command = "cvfwgen.exe -ClientId {id} -Instance Instance001"
        self.pattern = r'Total time taken in seconds = \[(\d+)]'
        self.show_status = 'PASSED'
        self.csv_results = 'FwGeneration_Stats_51337.csv'

        self.client_info = []

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.log.info("Executing setup function")
            self.server = self.tcinputs["server"]
            self.recipients = self.tcinputs["email"]
            self.fr = self.tcinputs["SP"]
            self.input = self.tcinputs["input"]
            self.fill_data()
            self.log.info(f"Server Name: {self.server}")

            self.log.info("Creating server object")
            self.server_obj = self.commcell.clients.get(self.server)
            self.log.info("Server object created successfully")

            self.network_helper = NetworkHelper(self)

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def run(self):
        """Executing test case steps"""
        try:
            self.log.info("Executing test case steps")
            for client in self.client_info:
                self.execute_command(client)

            for client in self.client_info:
                client: ClientInfo = client
                if client.time > client.threashold:
                    self.show_status = 'FAILED'
                    break

            email = f'''
<html>
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
            Test case 51337 <span style="color:{'green' if self.show_status == 'PASSED' else 'red'}">{self.show_status}</span> on {self.fr} <br><br>
            For this test case we have staged the <b>M101 DB</b> on the <b>CVFW30.testlab.commvault.com</b>
            <br>For more infomation check FwConfigGen.log file.
        <br><br>
        Average time to generate firewall configuration on clients as per sized are mentioned below. 
        <br><br><br>
        <table id="mytable">
            <tr> 
                <th>Client Ids</th>
                <th>Size of FwConfig.txt</th>
                <th>Value</th>
                <th>Threshold</th>
            </tr>
            ''' + self.table_data() + f'''
        </table>
        <br><br>
        <span style="color:red">*Note:</span> The threshold values are manually calculated on the SP{self.fr} setup.  
    </body>
</html>
'''

            self.network_helper.email("NWPerformance@commvault.com", self.recipients,
                                      f"Firewall Generation Optimization 51337 {self.fr}", email)
            self.persist_data()

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def execute_command(self, client: ClientInfo):
        results = []
        cmd = self.cvfwgen_client_command.format(id=client.id)
        self.log.info(f"Executing: {cmd}")  
        op = self.server_obj.execute_command(cmd)
        if op[0] == 1:
            raise Exception(f"Failed to execute command. Please check winrm services and services on {self.server}")
        for _ in range(5):
            op = self.server_obj.execute_command(cmd)
            if op[0] == 1:
                raise Exception(f"Failed to execute command. Please check winrm services and services on {self.server}")

            self.log.info(f"Took {op[1]} for client ID {client.id}")
            result_group = re.search(self.pattern, op[1])
            results.append(int(result_group.group(1)))

        client.time = sum(results) / len(results)

    def persist_data(self):
        file_path = os.path.join(constants.AUTOMATION_DIRECTORY, "Server", "Network", "Stats")
        if not os.path.exists(file_path):
            os.mkdir(file_path)

        file_path = os.path.join(file_path, self.csv_results)
        file_exists = os.path.isfile(file_path)

        with open(file_path, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            if not file_exists:
                writer.writerow(['Client Ids', 'Size of FwConfig.txt (KB)', 'Value (Seconds)', 'Threshold (Seconds)'])
                for client in self.client_info:
                    client: ClientInfo = client
                    writer.writerow([client.id, client.space, client.time, client.threashold])

    def fill_data(self):
        file_path = self.input
        if not os.path.isfile(file_path):
            raise Exception(f"Input file does not exist on path {file_path}")

        try:
            with open(file_path, mode='r') as csv_file:
                csv_reader = csv.reader(csv_file)
                headers = next(csv_reader)
                self.validate_headers(headers)
                for line in csv_reader:
                    if len(line) == 3:
                        self.client_info.append(ClientInfo(id=line[0], space=line[1], threashold=line[2]))
        except Exception as e:
            self.log.info(f"Skipping line: {line}, exception: {e}")

    def validate_headers(self, headers):
        expected = ['Client ID', 'Size (KB)', 'Threshold']
        for given, needed in zip(headers, expected):
            if given.lower() != needed.lower():
                raise Exception(f"Headers missmatch. Expected headers: {expected}")

    def table_data(self):
        '''
            <tr>
                <td>22897, 1319</td>
                <td>50 KB</td>
                <td>{self.average_time[50]} Seconds</td>
                <td>{self.client_threashold_time[50]} Seconds</td>
            </tr>
        '''

        html_table = ''
        for client in self.client_info:
            client: ClientInfo = client
            html_table += f'''
<tr>
    <td>{client.id}</td>
    <td>{client.space} KB</td>
    <td>{client.time} Seconds</td>
    <td>{client.threashold} Seconds</td>
</tr>
'''
        return html_table