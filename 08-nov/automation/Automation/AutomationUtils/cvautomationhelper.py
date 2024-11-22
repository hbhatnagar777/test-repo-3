# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for CVAutomation related operations

TCRunThread: Class for running thread for running a testcase

TCRunThread:
    __init__() :                            Initialize the TCRunThread class
    run() :                                 Runs the program in a thread

read_json() :                               Method to read and return a json a dictionary
run_testcase_in_multiple_controllers() :    Method to run a testcase in multiple controllers
"""
import json
import os
import threading
from typing import Dict

from AutomationUtils import logger
from AutomationUtils.machine import Machine
import sys

AUTOMATION_PATH = os.getcwd()
log = logger.get_log()


class TCRunThread(threading.Thread):
    def __init__(self, controller_obj, path):
        """Initializes the TCRunThread class"""
        threading.Thread.__init__(self)
        self.controller_obj = controller_obj
        self.path = path
        self.log = logger.get_log()

    def run(self):
        """ Method to run programs in a thread """
        delimiter = "\\"
        if 'linux' in sys.platform.lower():
            delimiter = "/"
        self.controller_obj.copy_from_local(f"{AUTOMATION_PATH}{delimiter}trigger.json", f"{self.path}")
        self.log.info(f"Successfully copied {AUTOMATION_PATH}{delimiter}trigger.json to {self.path}")

        command = rf'python "{self.path}\CVAutomation.py" --inputJSON "{self.path}\trigger.json"'
        out = self.controller_obj.execute_command(command)
        self.log.info(f"{self.controller_obj.machine_name}\t{out.output}\t{out.exception}")


def read_json(path: str) -> Dict:
    """Method to read and return a json a dictionary

        Args:
            path (str): path for the json file

        Returns:
            json_data (dict): json data as dictionary
    """
    with open(path, 'r') as jsonfile:
        json_data = json.load(jsonfile)

    log.info(f"Read JSON from file {path}: {json_data}")

    return json_data


def _create_trigger_json(inputJSON: dict) -> str:
    """
    Method to create a new json to trigger testcase in the child controller machines

    Args:
        inputJSON: input JSON to be used to extract the information from

    Returns:
        (str): path for the json file created
    """
    testset_info = inputJSON.get('testsets', None)

    for itr in testset_info:
        childTC_input = {}
        testcases = testset_info[itr].get("testCases")
        for testcase in testcases:
            TC = testcases[testcase]
            for input in TC:
                if input == "testcase_info":
                    childTC_input[TC[input]["testcaseID"]] = TC[input]["inputs"]

        inputJSON['testsets'][itr]['testCases'] = childTC_input

    log.info(f"Created trigger.json locally with content: {inputJSON}")

    trigger_json_file_name = "trigger.json"
    with open(trigger_json_file_name, "w") as outfile:
        json.dump(inputJSON, outfile)

    if '\\' in AUTOMATION_PATH:
        path = os.getcwd() + "\\" + trigger_json_file_name
    else:
        path = os.getcwd() + "/" + trigger_json_file_name

    return path


def run_testcase_in_multiple_controllers(machines: list[dict], inputJSONpath: str) -> None:
    """
    Method to run a testcase in multiple controllers

    Args:
        machines (list[dict]):  list of machines objects to run the cases on
        Eg. machines : [
                        {
                            "machine_name": "machinename.domainname.com",
                            "username": "domain\\username",
                            "password": "secret@passowrd",
                            "path": "D:\\Path_To_Automation\\Automation"
                        },
                        {
                            "machine_name": "123.345.567.889",
                            "username": "administrator",
                            "password": "secret@passowrd",
                            "path": "D:\\Path_To_Automation\\Automation"
                        }
                    ]
        inputJSONpath (str):    path for the input json file

    NOTE:
        Please make sure that controller machines are reachable and machine objects can be created.

        If you are facing issues with creating machine object, check the following things on the controller
        machine and the machine you are trying to connect:

            1. You should be running python interpreter with administrator privilege
            2. Firewalls must be turned off
            3. Check if Remote services(such as Remote desktop services, remote desktop configuration) are running
                in services.msc
            4. Check if netlogon is running under services.msc
            5. Run "winrm quickconfig" in powershell once.
            6. Run "powershell.exe Set-ExecutionPolicy RemoteSigned -Force" in powershell.
    """
    inputjson = read_json(inputJSONpath)
    trigger_json_path = _create_trigger_json(inputjson)

    controller_list = []
    for machine in machines:
        temp = {}
        machine_name = machine["machine_name"]
        username = machine["username"]
        password = machine["password"]
        path = machine["path"]
        controller_obj = Machine(machine_name=machine_name, username=username, password=password)
        temp["obj"] = controller_obj
        temp["name"] = machine_name
        temp["path"] = path

        controller_list.append(temp)

    controller_thread_list = []
    for machine in controller_list:
        temp_thread = TCRunThread(machine["obj"], machine['path'])
        controller_thread_list.append(temp_thread)

    for thrd in controller_thread_list:
        log.info(f"Starting testcase execution on controller: {thrd.controller_obj.machine_name}")
        thrd.start()

    for thrd in controller_thread_list:
        thrd.join()

    log.info("Finished executing testcases on all the machines")
