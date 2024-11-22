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

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""

import time
import json
import random
from queue import Queue
from cvpysdk.job import Job
from threading import Thread
from datetime import datetime, timedelta
from AutomationUtils.machine import Machine
from Laptop.laptophelper import LaptopHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.vmoperations import HyperVOperations
from AutomationUtils import logger, database_helper, config
from AutomationUtils.options_selector import OptionsSelector
from Install.installer_utils import get_latest_recut_from_xml
from Install.installer_constants import REMOTE_FILE_COPY_LOC, UNIX_REMOTE_FILE_COPY_LOC, DEFAULT_DRIVE_LETTER


class TestCase(CVTestCase):
    """Testcase : Multiple parallel install of laptop clients"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Parallel Registration of Multiple Clients"
        self.config_json = None
        self.log = None
        self.tcinputs = {}
        self.hyperV = None
        self.client_info_dict = {}
        self.local_machine = None
        self.db_creds = {}
        self.client_type = None
        self.mssql = None
        self.commserve_machine = None
        self.options_selector = None
        self.current_sp = None
        self.current_recut = None
        self.laptop_helper = None
        self.install_kwargs = {}
        self.wait_before_reg = None
        self.laptopinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.hyperV = HyperVOperations(self.config_json.Laptop.Install.HyperVHostname,
                                       self.config_json.Laptop.Install.HyperVUser,
                                       self.config_json.Laptop.Install.HyperVPasswd)
        self.log = logger.get_log()
        self.local_machine = Machine()
        self.client_type = 'laptop'
        self.current_sp = 0
        self.current_recut = 0
        self.options_selector = OptionsSelector(self.commcell)
        self.commserve_machine = self.options_selector.get_machine_object(machine=self.commcell.commserv_hostname)
        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_client_activation': True
        }

    def initialize_mssql_db(self):
        """
            Initialize MSSQL DB connection for executing DB queries
        """
        try:
            server = self.db_creds['db_server']
            if not self.commcell.is_linux_commserv:
                server = server + "\\commvault"
            self.mssql = database_helper.MSSQL(server=server, user=self.db_creds['db_username'],
                                               password=self.db_creds['db_password'], database='CommServ')
            self.log.info("DB Connection Successful")
            return True
        except Exception as exp:
            self.log.error("Failed to initialize DB connection with error {0}".format(exp))
            return False

    def extract_datetime_from_log_line(self, log_line):
        """
            Extracts date and time from log lines
        """
        time_tokens = [int(t) for t in log_line[3].split(":")]
        date_tokens = [int(t) for t in log_line[2].split("/")]
        current_time = datetime.now()
        return current_time.replace(day=date_tokens[1], month=date_tokens[0],
                                    hour=time_tokens[0], minute=time_tokens[1], second=time_tokens[2])

    def install_client(self, q):
        while True:
            client_info = q.get()
            self.laptopinputs = {}
            laptop_helper = LaptopHelper(self)
            self.laptopinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            cs_sp = self.commcell.commserv_version
            cs_recut, _ = get_latest_recut_from_xml(cs_sp)
            self.laptopinputs["Machine_host_name"] = client_info['client_hostname']
            self.laptopinputs["Machine_client_name"] = client_info['client_name']
            self.laptopinputs["Machine_user_name"] = client_info['client_username']
            self.laptopinputs["Machine_password"] = client_info['client_password']
            self.laptopinputs["Plan"] = "Laptop plan"
            self.laptopinputs["Skip_RDP_Users"] = self.client_info_dict['install_creds']['username']
            self.install_kwargs["client_groups"] = ["Laptop plan clients"]
            self.install_kwargs["check_num_of_devices"] = False
            if self.client_info_dict['install_creds']['authcode'] != '':
                self.laptopinputs['register_authcode'] = self.client_info_dict['install_creds']['authcode']
                self.install_kwargs['authcode'] = self.client_info_dict['install_creds']['authcode']
            else:
                self.laptopinputs['Activation_User'] = self.client_info_dict['install_creds']['username']
                self.laptopinputs['Activation_Password'] = self.client_info_dict['install_creds']['password']
            if cs_sp > self.current_sp and cs_recut > self.current_recut:
                self.current_sp = cs_sp
                self.current_recut = cs_recut
                custompkg_kwargs = {
                    'servicePack': cs_sp,
                    'SP_revision': cs_recut
                }
                self.laptop_helper.create_custom_package(custompackage_kwargs=custompkg_kwargs)
            self.log.info("Installing Laptop")
            laptop_helper.install_laptop(self.laptopinputs, {}, self.install_kwargs)
            self.log.info("Install Laptop Done")
            current_date = datetime.now()
            client_name = client_info['client_name']
            client_machine = Machine(client_info['client_hostname'], username=client_info['client_username'],
                                     password=client_info['client_password'])
            reg_result = "In Progress"
            client_processing_time, cs_processing_time = '-', '-'
            client_request_send_time, client_response_receive_time, cs_response_send_time = '', '', ''
            cs_request_receive_time = ''
            client_os = client_machine.os_info.lower()
            client_id = None
            client_obj = None
            db_query = r"""USE WFENGINE; INSERT INTO {} (Date, Client, ClientType, OS, RegistrationTime, 
                        CSProcessingTime, RegRequestTime, RegResponseTime, CSRequestReceiveTime, CSResponseSendTime, Result) 
                        values ('{}', '{}', '{}', '{}','{}', '{}', '{}', '{}', '{}', '{}', '{}') """.format(
                self.db_creds['db_table'], current_date.strftime('%Y-%m-%d %H:%M:%S'), client_name, self.client_type,
                client_os, client_processing_time, cs_processing_time, client_request_send_time,
                client_response_receive_time, cs_request_receive_time, cs_response_send_time, reg_result)
            self.log.info(f"Query to update {self.db_creds['db_table']} table : \n{db_query}")
            self.mssql.execute(query=db_query)
            try:
                self.log.info("Refreshing Client List on the CS")
                self.commcell.refresh()
                try:
                    client_obj = self.commcell.clients.get(client_name)
                    client_id = client_obj.client_id
                    self.log.info(f"Client ID for Client {client_name} is {client_id}")
                    client_os = client_obj.os_info.split('  --  ')[1] + " " + client_obj.os_info.split(' ')[0]
                    reg_result = "Passed"
                except Exception as exp:
                    self.log.info(f"Unable to retrieve client ID of {client_name} error: {exp}")
                    reg_result = "Failed"

                if client_id is not None:
                    retry = 0
                    while retry < 3:
                        try:
                            log_file = client_machine.join_path(client_obj.log_directory, "CvInstallClient.log")
                            pattern = ['Operationtype=\"0\"']
                            output = client_machine.find_lines_in_file(log_file, pattern)[0].split()
                            process_id = output[1]
                            client_request_send_time = self.extract_datetime_from_log_line(output)
                            pattern = [f"{process_id} .* XML Response"]
                            output = client_machine.find_lines_in_file(log_file, pattern)[0].split()
                            client_response_receive_time = self.extract_datetime_from_log_line(output)

                            log_file = self.commserve_machine.join_path(client_obj.log_directory, "CvInstallMgr.log")
                            pattern = [f"Start to get auto register client Info for client \\[{client_name}]"]
                            output = self.commserve_machine.find_lines_in_file(log_file, pattern)[0].split()
                            process_id = output[1]
                            pattern = [f"{process_id} .* clientName=\"{client_name}\""]
                            output = self.commserve_machine.find_lines_in_file(log_file, pattern)[0].split()
                            cs_request_receive_time = self.extract_datetime_from_log_line(output)

                            pattern = [f"Add client for {client_name} with id \\[{str(client_id)}]succeeded"]
                            output = self.commserve_machine.find_lines_in_file(log_file, pattern)[0].split()
                            process_id = output[1]
                            pattern = [f"{process_id} .* XML Response .* clientId=\"{client_id}\" "
                                       f"clientName=\"{client_name}\""]
                            output = self.commserve_machine.find_lines_in_file(log_file, pattern)[0].split()
                            cs_response_send_time = self.extract_datetime_from_log_line(output)
                        except Exception as exp:
                            retry += 1
                            if retry >= 3:
                                raise Exception(exp)
                            time.sleep(20)
                        else:
                            retry = 3
                    client_processing_time = int((client_response_receive_time -
                                                  client_request_send_time).total_seconds())
                    self.log.info("Client %s installed in %s seconds", client_name, str(client_processing_time))
                    cs_processing_time = int((cs_response_send_time - cs_request_receive_time).total_seconds())

                    db_query = r"""USE WFENGINE; UPDATE {} SET [OS] = '{}', [RegistrationTime] = '{}', 
                                [CSProcessingTime] = '{}', [RegRequestTime] = '{}', [RegResponseTime] = '{}', 
                                [CSRequestReceiveTime] = '{}', [CSResponseSendTime] = '{}', [Result] = '{}' 
                                WHERE [Date] = '{}' AND [Client] = '{}'""".format(
                        self.db_creds['db_table'], client_os,
                        f"{client_processing_time}s", f"{cs_processing_time}s",
                        client_request_send_time.strftime('%Y-%m-%d %H:%M:%S'),
                        client_response_receive_time.strftime('%Y-%m-%d %H:%M:%S'),
                        cs_request_receive_time.strftime('%Y-%m-%d %H:%M:%S'),
                        cs_response_send_time.strftime('%Y-%m-%d %H:%M:%S'), reg_result,
                        current_date.strftime('%Y-%m-%d %H:%M:%S'), client_name)
                    self.log.info(f"Query to update {self.db_creds['db_table']} table : \n{db_query}")
                    self.mssql.execute(query=db_query)
                    wait_time = datetime.now() + timedelta(minutes=10)
                    self.log.info("Waiting for backup job to start")
                    while datetime.now() < wait_time:
                        db_query = f"select jobid from JMBkpJobInfo where applicationId in " \
                                   f"(select id from APP_Application where clientId = {client_id})"
                        self.csdb.execute(db_query)
                        if self.csdb.fetch_all_rows()[0][0] != '':
                            job_id = int(self.csdb.fetch_all_rows()[0][0])
                            job_obj = Job(self.commcell, job_id)
                            self.log.info(f"Backup Job started with Job ID {job_id}")
                            job_obj.wait_for_completion(60)
                            self.log.info("Backup Job finished")
                            break
                else:
                    raise Exception(f"Unable to retrieve client ID of {client_name} Client registration failed.")
            except Exception as exp:
                self.log.error(exp)
                reg_result = "Failed"
                db_query = r"""USE WFENGINE; UPDATE {} SET [OS] = '{}', [Result] = '{}' 
                            WHERE [Date] = '{}' AND [Client] = '{}'""".format(
                    self.db_creds['db_table'], client_os, reg_result,
                    current_date.strftime('%Y-%m-%d %H:%M:%S'), client_name)
                self.mssql.execute(query=db_query)
            finally:
                q.task_done()
                laptop_helper.cleanup_clients(self.laptopinputs, delete_client=True)
                if not self.local_machine.check_file_exists(
                        self.local_machine.join_path(DEFAULT_DRIVE_LETTER, "stop_run.txt")):
                    q.put(client_info)

    def normal_client_reg(self):
        if self.client_info_dict['install_creds']['authcode'] != '':
            self.laptopinputs['register_authcode'] = self.client_info_dict['install_creds']['authcode']
        else:
            self.laptopinputs['Activation_User'] = self.client_info_dict['install_creds']['username']
            self.laptopinputs['Activation_Password'] = self.client_info_dict['install_creds']['password']
        q = Queue()
        for client in self.client_info_dict['normal_clients']:
            q.put(client)
        for _ in range(len(self.client_info_dict['normal_clients'])):
            worker = Thread(target=self.install_client, args=(q,))
            worker.setDaemon(True)
            worker.start()
        q.join()

    def run(self):
        """Run function of this test case"""
        jfile = open(self.config_json.Install.json_path)
        """
        Contents of json
        {
            "decoupled_clients":
            [
                {
                    "client_name": "",
                    "client_hostname": "",
                    "client_username": "",
                    "client_password": ""
                }
            ],
            "normal_clients":
            [
                {
                    "client_name": "",
                    "client_hostname": "",
                    "client_username": "",
                    "client_password": ""
                }
            ],
            "install_creds":
                {
                    "username": "",
                    "password": "",
                    "authcode": ""
                },
            "base_directory_windows": "",
            "base_directory_unix": "",
            "db_creds":
                {
                    "db_table": "",
                    "db_server": "",
                    "db_username": "",
                    "db_password": ""
                },
            "thread_count" : "5"
        }
        """
        self.client_info_dict = json.load(jfile)
        self.db_creds = self.client_info_dict['db_creds']
        self.log.info("Initializing DB connection")
        retry_db = 5
        attempts = 0
        while attempts < retry_db:
            result = self.initialize_mssql_db()
            if result:
                break
            attempts += 1
            self.log.info(f"Retrying DB connection {attempts}/{retry_db-1}")
        # t1 = Thread(target=self.decoupled_client_reg)
        # t2 = Thread(target=self.normal_client_reg)
        # t1.start()
        # t2.start()
        # t1.join()
        # t2.join()
        self.normal_client_reg()

    def tear_down(self):
        """Tear down function of this test case"""
        pass
