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

Inputs:

    Hostname          -- Full hostname of the Virtual machine

    Username          -- Username to login to the virtual machine

    Password          -- Password for the virtual machine


**Note** Requires trials.txt file for testcase execution if not case is skipped

"""

import json

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class to perform user registration from Admin console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express trial - User Registration"
        self.trial_file = None
        self.contents = None
        self.options = None

        self.tcinputs = {
            "Hostname": None,
            "Username": None,
            "Password": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.options = OptionsSelector(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                machine = Machine()
                self.trial_file = machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
                self.contents = json.loads(machine.read_file(self.trial_file))
                assert self.contents['status'] == 'passed'
                self.contents['status'] = 'failed'
            except Exception as err:
                self.log.error(err)
                self.status = constants.SKIPPED
                return

            remote_machine = Machine(
                self.tcinputs.get('Hostname'),
                username=self.tcinputs.get('Username'),
                password=self.tcinputs.get('Password')
            )
            self.log.info('Machine class object created successfully')

            # To select drive with enough space
            self.log.info('Selecting drive on the machine based on space available')
            drive = self.options.get_drive(machine, size=50)
            if drive is None:
                raise Exception(f"Insufficient space on machine {machine.machine_name}")
            self.log.info('selected drive: %s', drive)

            # Directory to copy the registration script
            temp_directory = machine.join_path(drive, 'commvault_trial')
            script = remote_machine.join_path(constants.CVTRIALS_DIRECTORY, 'register_existing_user.py')

            # To remove Temp directory if exists
            if remote_machine.check_directory_exists(temp_directory):
                remote_machine.remove_directory(temp_directory)
                self.log.info('Successfully removed directory %s', temp_directory)

            # To create Temp directory on the machine
            remote_machine.create_directory(temp_directory)
            self.log.info(
                'Successfully created Automation Temp directory in path "%s"',
                temp_directory)

            # To copy the python file to the remote machine
            remote_machine.copy_from_local(script, temp_directory, raise_exception=True)
            script = machine.join_path(temp_directory, 'register_existing_user.py')
            self.log.info('Successfully copied the script file to location: "%s"', script)

            driver = machine.join_path(constants.AUTOMATION_DIRECTORY, 'CompiledBins', 'chromedriver.exe')

            # To copy the chrome driver to remote machine
            remote_machine.copy_from_local(driver, temp_directory, raise_exception=True)
            driver = machine.join_path(temp_directory, 'chromedriver.exe')
            self.log.info('Successfully copied chrome driver to location: "%s"', driver)

            # To install selenium on the remote_machine
            output = remote_machine.execute_command('py -m pip install selenium')
            if "Successfully installed" or "already satisfied" in output.formatted_output:
                self.log.info('Successfully installed selenium on machine: "%s"', remote_machine.machine_name)
            else:
                raise Exception(f'Failed to install selenium on machine {remote_machine.machine_name}')

            url = self.contents.get('URL')
            username = self.contents.get('Commvault ID')
            password = self.contents.get('Password')
            activation_code = self.contents.get('Activation Code')
            command = f"py '{script}' '{driver}' '{url}' '{username}' '{password}' '{activation_code}'"
            self.log.info("Command: %s", command)

            output = remote_machine.execute_command(command)

            if 'successful' in output.formatted_output:
                self.log.info('Registration successful')
                self.contents['status'] = "passed"
            elif output.exception:
                raise Exception(output.exception)
            else:
                if 'Registration failed:' in output.formatted_output:
                    raise Exception(output.formatted_output.split('Registration failed:')[1])
                else:
                    raise Exception(output.formatted_output)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            with open(self.trial_file, 'w') as file:
                file.write(json.dumps(self.contents))
