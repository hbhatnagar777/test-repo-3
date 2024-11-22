# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    execute_sim_calls()     --  Executes simultaneous SIM calls on multiple instances through threading and queues

    time_analyzer()         --  Extracts registration and configuration times from CS CvInstallMgr.log file for all
                                instances and compares them with preconfigured time values for each

    run()                   --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from AutomationUtils.windows_machine import WindowsMachine
from datetime import datetime
from AutomationUtils.machine import Machine
from Install.sim_call_helper import SimCallHelper
from Install.installer_constants import REMOTE_FILE_COPY_LOC
import queue
import threading
import re


class TestCase(CVTestCase):
    """Testcase : Laptop Parallel Registration Script"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Parallel Registration of Multiple Clients"
        self.config_json = None
        self.log = None
        self.tcinputs = {
            'No_of_Clients': None,
            'Machine_host_name': None,
            'Machine_user_name': None,
            'Machine_password': None,
            'registration_threshold': None,
            'configuration_threshold': None
        }
        self.sim_caller = None
        self.no_of_clients = None
        self.local_machine = None
        self.xml_file_path = None
        self.results = {}

    def setup(self):
        """Setup function of this test case"""
        self.sim_caller = SimCallHelper(self.commcell)
        self.log = logger.get_log()
        self.no_of_clients = self.tcinputs.get('No_of_Clients') if self.tcinputs.get('No_of_Clients') else 10
        self.xml_file_path = REMOTE_FILE_COPY_LOC
        self.local_machine = Machine()
        self.xml_file_path = self.local_machine.join_path(self.xml_file_path, "request_xmls")

    def execute_sim_calls(self, q, i):
        """
        Executes simultaneous SIM calls on multiple instances through threading and queues
            Args:
                    q (Queue): Queue representing SIM calls to be executed on multiple instances
                    i (int): Representing the instance for which to execute the SIM call
            Returns:
                    None
        """
        while True:
            task = q.get()
            sim_request = f"SimReq{i + 1}"
            xml_path = self.local_machine.join_path(self.xml_file_path, f"{sim_request}.xml")
            xml_output_path = self.local_machine.join_path(self.xml_file_path, f"{sim_request}_output.xml")
            self.sim_caller.execute_sim_call(xml_path, xml_output_path, i + 1)
            self.results[sim_request] = datetime.now()
            q.task_done()
            self.log.info(f"Thread #{i + 1} is executing {sim_request} in the queue.")

    def time_analyzer(self):
        """
        Extracts registration and configuration times from CS CvInstallMgr.log file for all instances and compares them
        with preconfigured time values for each
            Raises:
                Exception: Configuration times more than the threshold
                Exception: Registration time more than the threshold
        """
        N = self.no_of_clients
        cs_machine = WindowsMachine(self.tcinputs['Machine_host_name'], username=self.tcinputs["Machine_user_name"],
                                    password=self.tcinputs["Machine_password"], commcell_object=self.commcell)
        raw_log_config_times = cs_machine.get_logs_for_job_from_file(job_id=None, log_file_name="CvInstallMgr.log",
                                                                     search_term="Successfully configured client")
        raw_log_registration_times = cs_machine.get_logs_for_job_from_file(job_id=None, log_file_name=
            "CvInstallMgr.log", search_term="Client registration completed in")
        filter_log_config_times = raw_log_config_times.split('\r\n')[-N - 1:-1]
        filter_log_registration_times = raw_log_registration_times.split('\r\n')[-N - 1:-1]
        config_times_regex = re.compile(r'\[(\d)\] seconds')
        config_times = [int(config_times_regex.search(line).group(1)) for line in filter_log_config_times]
        registration_times_regex = re.compile(r'completed in \[(.*)\] seconds')
        registration_times = [int(registration_times_regex.search(line).group(1)) for line in
                              filter_log_registration_times]
        for i in range(N):
            self.log.info(f"Configuration time for client {i + 1} = {config_times[i]} seconds")
            self.log.info(f"Registration time for client {i + 1} = {registration_times[i]} seconds")
        config_time_check = all(t <= int(self.tcinputs['configuration_threshold']) for t in config_times)
        if not config_time_check:
            raise Exception("Configuration taking more time than threshold")
        registration_time_check = all(t <= int(self.tcinputs['registration_threshold']) for t in registration_times)
        if not registration_time_check:
            raise Exception("Registration taking more time than threshold")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Execute Simcalls in parallel")
            q = queue.Queue()
            for i in range(1, int(self.no_of_clients) + 1):
                worker = threading.Thread(target=self.execute_sim_calls, args=(q, i,), daemon=True)
                worker.start()
            for j in range(int(self.no_of_clients)):
                q.put(j)
            q.join()
            self.time_analyzer()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
