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

    run()           --  run function of this test case

Inputs:

    Hostname          -- Full hostname of the machine

    Username          -- Username to login to the machine

    Password          -- Password for the machine

    JSONPath          -- Full path of the local JSON file to be copied to the remote machine

"""

import os
import sys
import json

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class to perform admin console validation on different browsers"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express Trial - Execute testcases on remote machine"
        self.trial_file = None
        self.contents = None

        self.tcinputs = {
            "Hostname": None,
            "Username": None,
            "Password": None,
            "JSONPath": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                machine = Machine()
                self.trial_file = machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
                self.contents = json.loads(machine.read_file(self.trial_file))
                assert self.contents['status'] == 'passed'
            except Exception as err:
                self.log.error(err)
                self.status = constants.SKIPPED
                return

            # To create machine class object
            remote_machine = Machine(
                self.tcinputs.get('Hostname'),
                username=self.tcinputs.get('Username'),
                password=self.tcinputs.get('Password')
            )
            self.log.info('Machine class object created successfully')

            automation_directory = remote_machine.get_registry_value('Automation', 'CVAUTOPATH')

            # To delete the Automation directory and copy the one from controller
            if remote_machine.check_directory_exists(automation_directory):
                remote_machine.remove_directory(automation_directory)
            remote_machine.copy_from_local(
                os.path.dirname(sys.modules['__main__'].__file__),
                remote_machine.get_registry_value('Base', 'dGALAXYHOME'),
                raise_exception=True
            )
            self.log.info('Successfully copied the Test Automation package to the remote machine')
            temp_directory = remote_machine.join_path(automation_directory, 'Temp')
            run_automation = remote_machine.join_path(automation_directory, 'CVAutomation.py')
            json_file = remote_machine.join_path(
                temp_directory,
                os.path.split(self.tcinputs.get('JSONPath'))[1])

            self.log.info('Automation directory: "%s"', automation_directory)
            self.log.info('Temp directory: "%s"', temp_directory)
            self.log.info('Automation Execution file: "%s"', run_automation)
            self.log.info('Json File: "%s"', json_file)

            # To remove Temp directory if exists
            if remote_machine.check_directory_exists(temp_directory):
                remote_machine.remove_directory(temp_directory)
                self.log.info('Successfully removed directory %s', temp_directory)

            # To create Temp directory on the machine
            remote_machine.create_directory(temp_directory)
            self.log.info(
                'Successfully created Temp directory in path "%s"',
                temp_directory)

            # To copy the JSON file to the remote machine
            remote_machine.copy_from_local(self.tcinputs.get('JSONPath'), temp_directory, raise_exception=True)
            self.log.info('Successfully copied the JSON file')

            output = remote_machine.execute_command(f"py '{run_automation}' -json '{json_file}'")

            if output.exception:
                raise Exception(f'Failed to Launch testcase with Error: "{output.exception}"')

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
