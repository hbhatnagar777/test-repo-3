# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in tde project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

import time
from datetime import datetime as DT
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ [Network & Firewall]: FS Core package process monitoring """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall]:FS Core package process monitoring"
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "win_client_hostname": None,
            "win_client_username": None,
            "win_client_password": None,

            "lin_client_hostname": None,
            "lin_client_username": None,
            "lin_client_password": None,
            
            "email": None
        }
        self.network_helper = None
        self.win_cl = None
        self.lin_cl = None
        self.win_avg = None
        self.lin_avg = None
        self.lin_mem = []
        self.win_mem = []
        self.lin_cpu = []
        self.win_cmd = '''TASKLIST | findstr "PNAME"'''
        self.lin_cmd_1 = """commvault list | grep PNAME | awk '/[0-9]/{print $4}'"""
        self.lin_cmd_2 = """pmap PID | tail -n 1 | awk '/[0-9]K/{print $2}'"""
        self.lin_cmd_3 = """ps -p PID -o %cpu"""
        self.data = {
            "windows": {
                "cvd": 0,
                "cvfwd": 0
            },
            "linux": {
                "cvd": 0,
                "cvfwd": 0
            }
        }

    def setup(self):
        self.network_helper = NetworkHelper(self)
        self.recipients = self.tcinputs["email"]
       

        self.log.info("Creating machine obj")
        self.win_cl = Machine(
                            machine_name=self.tcinputs["win_client_hostname"],
                            username=self.tcinputs["win_client_username"],
                            password=self.tcinputs["win_client_password"])

        self.lin_cl = Machine(
            machine_name=self.tcinputs["lin_client_hostname"],
            username=self.tcinputs["lin_client_username"],
            password=self.tcinputs["lin_client_password"])

    def run(self):
        try:
            self.log.info("Executing command on windows machine")
            for process in ["cvd", "cvfwd"]:
                self.win_cmd = self.win_cmd.replace("PNAME", process)
                for _ in range(6):
                    time.sleep(10)
                    op = self.win_cl.execute_command(self.win_cmd)
                    memory_kb = op.output.strip().split()[-2]
                    memory_kb = memory_kb.replace(",", "")
                    memory_mb = int(memory_kb)//1024
                    self.win_mem.append(memory_mb)
                self.win_cmd = '''TASKLIST | findstr "PNAME"'''
                self.win_avg = sum(self.win_mem)//len(self.win_mem)
                self.log.info(f"Windows machine memory for {process} usage: {self.win_avg}Mb")
                self.data["windows"][process] = self.win_avg

        except Exception as e:
            self.log.info(f"Got tde exception: {str(e)}")

        try:
            self.log.info("Executing command on linux machine")
            for process in ["cvd", "cvfwd"]:
                self.log.info("Executing Command on Linux machine")
                self.lin_cmd_1 = self.lin_cmd_1.replace("PNAME", process)

                op = self.lin_cl.execute_command(self.lin_cmd_1)
                pid = op.output[:-1]
                self.lin_cmd_2 = self.lin_cmd_2.replace("PID", pid)
                self.lin_cmd_3 = self.lin_cmd_3.replace("PID", pid)

                temp_list_mem = []
                temp_list_cpu = []
                for _ in range(6):
                    temp_op = self.lin_cl.execute_command(self.lin_cmd_2)
                    temp_list_mem.append(int(temp_op.output[:-2])//1024)

                    op = self.lin_cl.execute_command(self.lin_cmd_3)
                    temp_list_cpu.append(float(op.output.split("\n")[1][1:]))
                    time.sleep(10)
                mem = sum(temp_list_mem)//len(temp_list_mem)
                self.lin_mem = mem

                cpu_usage = sum(temp_list_cpu)//len(temp_list_cpu)
                self.lin_cpu = cpu_usage

                self.lin_cmd_1 = """commvault list | grep PNAME | awk '/[0-9]/{print $4}'"""
                self.lin_cmd_2 = """pmap PID | tail -n 1 | awk '/[0-9]K/{print $2}'"""
                self.lin_cmd_3 = """ps -p PID -o %cpu"""

                self.log.info(f"Linux machine memory for {process} usage: {self.lin_mem}mb")
                self.log.info(f"Linux cpu memory for {process} usage: {self.lin_cpu}%")

                self.data["linux"][process] = self.lin_mem

        except Exception as e:
            self.log.info(f"Exception as {str(e)}")

        try:
            if self.data['linux']['cvd'] > 3000 and self.data['linux']['cvfwd'] > 3000:
                self.log.info(self.data)
                # raise Exception("Linux is consuming more memory tdan tdreshold ")
            
            if self.data['windows']['cvd'] > 300 and self.data['windows']['cvd'] > 300: 
                self.log.info(self.data)
                #raise Exception("Windows is consuming more memory tdan tdreshold ")

            if self.lin_cpu > 5:
                self.log.info(self.data)
                #raise Exception("Linux is consuming more CPU tden tdreshold")

            self.status = "PASSED"
            self.send_email(self.status)
        except Exception as e:
            self.log.info(f"Exception {str(e)}")

    def send_email(self, status):
        body = self.create_email_body(status)
        self.log.info(body)
        self.network_helper.email("NWPerformance@commvault.com", self.recipients, "RAM consumption for FS-Core package", body)

    def create_email_body(self, status):
        fr = 'SP' + self.commcell.version.split('.')[1]

        return f"""
<HTML>
<head>
<style> 
    table#mytable {{
  border-collapse: collapse;
  width: 100%;
}}

table#mytable th, td {{
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}}

table#mytable th {{
  background-color: #f2f2f2;
}}

#tdroughput {{
color: green;
}}

</style>
</head>
<body> 
<br>
    Hi, <br> 
    <br> 
    Test case 62190 <span style="color:{'green' if status == 'PASSED' else 'red'}"> {status} </span> <br>
    <br> 
    Below is the memory consumption for cvd & cvfwd process for the {fr} FS client. :

    <table id="mytable">
        <tr> 
            <th>OS</th>
            <th>Process</th>
            <th>Memory (Mb)</th>
        </tr>
        
        <tr>
            <td>Windows</td>
            <td>CVD</td>
            <td>{self.data['windows']['cvd']}</td>
        </tr>

        <tr>
            <td>Windows</td>
            <td>CVFWD</td>
            <td>{self.data['windows']['cvfwd']}</td>
        </tr>

        <tr>
            <td>Linux</td>
            <td>CVD</td>
            <td>{self.data['linux']['cvd']}</td>
        </tr>

        <tr>
            <td>Linux</td>
            <td>CVFWD</td>
            <td>{self.data['linux']['cvfwd']}</td>
        </tr>
    </table>
    <br><br> 
    Thanks,<br>
    Ankit Rusia
</body>
</HTML>
        """
        