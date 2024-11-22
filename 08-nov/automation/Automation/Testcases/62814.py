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

import os
import time
import matplotlib
import warnings
from datetime import datetime
from matplotlib import pyplot as plt
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper

matplotlib.use('Agg')
warnings.simplefilter(action='ignore', category=FutureWarning)


class TestCase(CVTestCase):
    """
    [Network & Firewall] : Automate the test for memory growth of cvd and cvfwd
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Automate the test for memory growth of cvd and cvfwd"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "source": None,
            "dest": None,
            "threads": None,
            "connections": None,
            "email": None
        }
        self.memory_usage_before = []
        self.memory_usage_while = []
        self.memory_usage_after = []

        self.avg_memory_before = 0
        self.avg_memory_while = 0
        self.avg_memory_after = 0

        self.source = None
        self.dest = None
        self.source_machine = None
        self.dest_machine = None
        self.source_object = None
        self.dest_object = None
        self.threads = None
        self.connections = None
        self.recipients = None
        self.network_helper = None
        self.duration = None

        self.first_cvd = []
        self.second_cvd = []
        self.third_cvd = []

        self.first_cvfwd = []
        self.second_cvfwd = []
        self.third_cvfwd = []
        self.ticker_value = []

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.log.info(f"Process current directory : {os.getcwd()}")
            self.log.info(f"[+] Running setup function. [+]")
            self.source = self.tcinputs["source"]
            self.dest = self.tcinputs["dest"]
            self.threads = int(self.tcinputs["threads"])
            self.connections = int(self.tcinputs["connections"])
            self.recipients = self.tcinputs["email"]
            self.duration = int(self.tcinputs.get("duration", "60"))
            self.network_helper = NetworkHelper(self)

            self.log.info(f"[+] Creating client objects [+]")
            self.source_object = self.commcell.clients.get(self.source)
            self.dest_object = self.commcell.clients.get(self.dest)

            self.log.info(f"[+] Creating machine objects [+]")
            self.source_machine = Machine(self.source_object)
            self.dest_machine = Machine(self.dest_object)

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def run(self):
        """Run function of this test case"""
        self.log.info("Started executing testcase : %s", self.id)
        try:
            # Fetching and saving data for past 1 hour.
            self.log.info("Monitoring processes and collecting data for one hour before running the tool.")
            self.ticker_value.append(datetime.now().strftime("%H:%M:%S"))
            for _ in range(self.duration):
                self.first_cvd.append(self.get_memory("cvd"))
                self.first_cvfwd.append(self.get_memory("cvfwd"))
                time.sleep(60)

            # Run the tool to make numerous connections.
            self.ticker_value.append(datetime.now().strftime("%H:%M:%S"))
            self.make_connections(self.threads, self.connections)
            self.log.info(f"Waiting for connections to complete")
            self.collecting_data_while_tool_is_runing()
            self.log.info(f"Tool executed.")

            # Monitoring processes for another one hour.
            self.ticker_value.append(datetime.now().strftime("%H:%M:%S"))
            self.log.info("Monitoring processes and collecting data for another one hour.")
            for _ in range(self.duration):
                self.third_cvd.append(self.get_memory("cvd"))
                self.third_cvfwd.append(self.get_memory("cvfwd"))
                time.sleep(60)
            self.ticker_value.append(datetime.now().strftime("%H:%M:%S"))

            # Plotting and saving the graph's
            current_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
            cvd_plot = f"cvd_{current_time}.png"
            cvfwd_plot = f"cvfwd_{current_time}.png"
            self.log.info(f"Saving file {cvd_plot}, {cvfwd_plot}")
            self.plot_csv_data(self.first_cvd, self.second_cvd, self.third_cvd, cvd_plot, "Memory Trend Graph for CVD")
            self.plot_csv_data(self.first_cvfwd, self.second_cvfwd, self.third_cvfwd, cvfwd_plot, "Memory Trend Graph for CVFWD")

            # Sending email with attachments.
            file_names = (cvd_plot, cvfwd_plot)
            body = f'''
            <HTML>
            <head>
            <style>
            table, th, td {{
              border: 1px solid black;
              border-collapse: collapse;
            }}
            th, td {{
              padding: 5px;
              text-align: left;
            }}
            
            </style>
            </head>
            <BODY>
            Hi team,
            Attached is the report for the latest cvd and cvfwd memory consumption test on the windows clients {self.source} and {self.dest}.

            Test Details:
                - 30,000 connections were sent to cvfwd.
                - Memory consumption was monitored throughout the process.
                - The test ran for {round((datetime.strptime(self.ticker_value[2], "%H:%M:%S")-datetime.strptime(self.ticker_value[1], "%H:%M:%S")).seconds/60, 2)} minute(s)

                <br><br>
                <TABLE style="width:100%"> 
                    <caption style="caption-side: top; text-align: center; font-weight: bold;">
                        Observation for CVFWD Process   
                    </caption>
                    <tr>
                        <th> </th>
                        <th>Before executing the TestConnection tool</th>
                        <th>While making {self.threads * self.connections} connections</th>
                        <th>Post executing the TestConnection tool</th>
                    </tr>
                    <tr>
                        <td><b>Minimun (MegaBytes)</b></td>
                        <td>{min(self.first_cvfwd)} MB</td>
                        <td>{min(self.second_cvfwd)} MB</td>
                        <td>{min(self.third_cvfwd)} MB</td>
                    </tr>
                    <tr>
                        <td><b>Maximun (MegaBytes)</b></td>
                        <td>{max(self.first_cvfwd)} MB</td>
                        <td>{max(self.second_cvfwd)} MB</td>
                        <td>{max(self.third_cvfwd)} MB</td>
                    </tr>
                </table> 
                <BR>
                <table style="width:100%"> 
                    <caption style="caption-side: top; text-align: center; font-weight: bold;">
                        Observation for CVD Process 
                    </caption>
                    <tr>
                        <th></th>
                        <th>Before executing the TestConnection tool</th>
                        <th>While making {self.threads * self.connections} connections</th>
                        <th>Post executing the TestConnection tool</th>
                    </tr>
                    <tr>
                        <td><b>Minimun (MegaBytes)</b></td>
                        <td>{min(self.first_cvd)} MB</td>
                        <td>{min(self.second_cvd)} MB</td>
                        <td>{min(self.third_cvd)} MB</td>
                    </tr>
                    <tr>
                        <td><b>Maximun (MegaBytes)</b></td>
                        <td>{max(self.first_cvd)} MB</td>
                        <td>{max(self.second_cvd)} MB</td>
                        <td>{max(self.third_cvd)} MB</td>
                    </tr>
                </TABLE> 
            <BR>
            Thank you!
            </BODY>
            </HTML>'''

            self.network_helper.email("NWPerformanceTesting@commvault.com",
                                        self.recipients, " - cvd and cvfwd memory consumption",
                                        body, file_names)

            if max(self.third_cvd) > max(self.first_cvd)*1.25:
                self.status = 'FAILED'
        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def make_connections(self, threads, connections):
        """Making 100K connections to cvfwd"""
        cmd = "TestConnection.exe -host " + \
              f"{self.dest_object.client_hostname}*" + \
              f"{self.dest_object.client_name}*" + \
              f"{self.dest_object.network.tunnel_connection_port}" + \
              f"*0 -service JobControlCVD -threads {threads} -n {connections}"
        try:
            self.log.info(f"Executing below command on {self.source}: \n{cmd}\n")
            self.source_object.execute_command(cmd, wait_for_completion=False)
            op = self.source_object.execute_command('tasklist | findstr "TestConnection.exe"', wait_for_completion=True)
            if op[0] == 1:
                raise Exception("Failed to execute the above command")
            self.log.info("Successfully executed the command")
        except Exception as e:
            self.log.error('Failed to execute the above command with error: %s', e)

    def collecting_data_while_tool_is_runing(self, max_time=3):
        """This function will make sure that TestConnection.exe stopped"""
        cmd = 'tasklist | findstr "TestConnection.exe"'
        max_time /= 60
        while max_time:
            time.sleep(6)
            op = self.source_object.execute_command(cmd, wait_for_completion=True)
            if op[0] == 1:
                return
            self.second_cvd.append(self.get_memory("cvd"))
            self.second_cvfwd.append(self.get_memory("cvfwd"))
            self.log.info(f"[+] Waiting for TestConnection.exe to complete [+]")
            max_time -= 1
        return

    def get_memory(self, process):
        """This function will copy the resource monitor file from remote machine to local machine"""
        mem = self.dest_object.execute_command(
            f'tasklist /fi "imagename eq {process}.exe" /fo list |find "Mem Usage"')[1].split()[2].replace(",", "")
        return int(round(int(mem)/1024, 3))

    def plot_csv_data(self, first, second, third, name, title):
        """This function plot the desired graph."""
        first_x = range(0, len(first))
        second_x = range(first_x[-1] + 1, first_x[-1] + 1 + len(second))
        third_x = range(second_x[-1] + 1, second_x[-1] + 1 + len(third))

        f = plt.figure()
        f.set_figwidth(20)
        f.set_figheight(8)
        plt.subplots_adjust(left=0.05, right=0.99, top=0.9, bottom=0.1)
        plt.plot(first_x, first, color='b', label="Pre & Post making connections")
        plt.plot(second_x, second, color='r', label="While making connections")
        plt.plot(third_x, third, color='b')
        ticker_location = [
            0, len(first)-1,
            len(first)+len(second)-1,
            len(first)+len(second)+len(third)-1
        ]
        yticks_loc = [min(first+second+third),
                      max(first+second+third)]
        plt.ylim([yticks_loc[0] * 0.9, yticks_loc[1] * 1.1])
        plt.xticks(ticker_location, self.ticker_value)
        time_zone = self.source_object.timezone
        # time_zone = time_zone[time_zone.index('(') + 1:time_zone.index(')')]
        plt.xlabel(f"Time ({time_zone})  -> ")
        plt.ylabel("Memory in MB -> ")
        plt.title(title)
        plt.legend(loc='best')
        # plt.grid()
        if os.path.isfile(name):
            os.remove(name)
        plt.savefig(name, bbox_inches='tight')
        plt.clf()
        self.log.info(f"{name} saved successfully")
