# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
import datetime
import time

from AutomationUtils.machine import Machine
from AutomationUtils.cvautomationhelper import run_testcase_in_multiple_controllers

import threading

from Web.Common.page_object import handle_testcase_exception

epoch = time.time()
date = datetime.date.today()
formatted_date = date.strftime("%m_%d_%Y")


class SendPSFileThread(threading.Thread):
    """Class to contain thread function for sending powershell file to child controllers"""

    def __init__(self, controller_obj: Machine, path: str = None) -> None:
        """Initialized the SendPSFileThread class object

            Args:
                controller_obj (Machine): machine class object to push the script to
                path (str): path for automation location for child controller
        """
        threading.Thread.__init__(self)
        self.controller_obj = controller_obj
        self.log = logger.get_log()
        self.path = path

    def run(self) -> None:
        """Method to push powershell script to get system stats every 5 mins"""

        if not self.path:
            self.path = "C:\\Users\\Administrator\\Desktop"

        out = self.controller_obj.copy_from_local("Process_stats.ps1", f"{self.path}\\")
        self.log.info(out)
        out = self.controller_obj.execute_command(f"powershell.exe -File {self.path}\\Process_stats.ps1")
        self.log.info(out)


class GetCSVThread(threading.Thread):
    """Class to contain thread function to get generated system stats CSV from child controller"""

    def __init__(self, controller_obj: Machine, path: str = None, sharedpath: str = None) -> None:
        """Initializes GetCSVThread class object

            Args:
                controller_obj (Machine): machine class object to get the csv from controller
                path (str):
        """

        threading.Thread.__init__(self)
        self.log = logger.get_log()
        self.controller_obj = controller_obj
        self.path = path
        self.sharedpath_loc = sharedpath["path"]
        self.sharedpath_username = sharedpath["user"]
        self.sharedpath_password = sharedpath["password"]

    def run(self) -> None:
        drive_map = f'net use U: {self.sharedpath_loc} /user:{self.sharedpath_username} {self.sharedpath_password}' \
                    f' /persistent:yes;'
        move_cmd = f'Move-Item -Path "C:\\Users\\Administrator\\Desktop\\PerfStats\\{formatted_date}_stats.csv"' \
                   f' -Destination "U:\\{self.controller_obj.machine_name}_{formatted_date}.csv"'
        self.log.info(drive_map + move_cmd)
        out = self.controller_obj.execute_command(drive_map + move_cmd)
        self.log.info(f"{self.controller_obj.machine_name}\t{out.output}\t{out.exception}")
        out = self.controller_obj.execute_command('net use U: /delete')
        self.log.info(out)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self) -> None:
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Testcase to launch testcases on multiple controllers parallely"
        self.controller_obj_list = []  # for running automation cases
        self.controller_list = []
        self.infra_obj_list = []  # for CS/WS/WC
        self.infra_list = []
        self.tcinputs = {
            "sharedpath": {
                "path": "",
                "user": "",
                "password": ""
            },
            "controllers_info":
                [
                    {
                        "machine_name": "",
                        "username": "",
                        "password": "",
                        "path": ""
                    },
                    {
                        "machine_name": "",
                        "username": "",
                        "password": "",
                        "path": ""
                    }
                ],
            "inputJSONPath": "",
            "testcase_info": {
                "testcaseID": "",
                "inputs": {
                }
            }
        }

    def setup(self) -> None:
        """Setup function of this test case"""
        self.machine_dict = self.tcinputs["controllers_info"]
        for info in self.machine_dict:
            temp = {}
            self.shared_path = self.tcinputs['sharedpath']
            machine_name = info["machine_name"]
            username = info["username"]
            password = info["password"]
            path = info["path"]
            controller_obj = Machine(machine_name=machine_name, username=username, password=password)
            self.log.info(f"Machine object created successfully for machine: {machine_name}")
            temp["obj"] = controller_obj
            temp["name"] = machine_name
            temp["path"] = path

            if path:
                self.controller_obj_list.append(temp)
                self.controller_list.append(info)
            else:
                self.infra_obj_list.append(temp)
                self.infra_list.append(info)

    def run(self) -> None:
        """Run function of this test case"""
        try:
            machine_thread_list = []

            for machine in self.controller_obj_list:
                temp_thread = SendPSFileThread(machine['obj'], machine['path'])
                machine_thread_list.append(temp_thread)

            for machine in self.infra_obj_list:
                temp_thread = SendPSFileThread(machine['obj'])
                machine_thread_list.append(temp_thread)

            for sendps_thread in machine_thread_list:
                sendps_thread.start()
                self.log.info(
                    f"Starting thread to send powershell script to machine: {sendps_thread.controller_obj.machine_name}")

            for sendps_thread in machine_thread_list:
                sendps_thread.join()

            self.log.info("Finished sending powershell scripts to all machines")

            run_testcase_in_multiple_controllers(self.controller_list, self.tcinputs['inputJSONPath'])

            machine_thread_list = []
            for machine in self.controller_obj_list:
                temp_thread = GetCSVThread(machine['obj'], sharedpath=self.shared_path)
                machine_thread_list.append(temp_thread)

            for machine in self.infra_obj_list:
                temp_thread = GetCSVThread(machine['obj'], sharedpath=self.shared_path)
                machine_thread_list.append(temp_thread)

            for getcsv_thread in machine_thread_list:
                getcsv_thread.start()
                self.log.info(f"Starting thread to get csv from machine: {getcsv_thread.controller_obj.machine_name}")

            for getcsv_thread in machine_thread_list:
                getcsv_thread.join()

            self.log.info("Finished getting CSVs from the machines")

        except Exception as exp:
            handle_testcase_exception(self, exp)
