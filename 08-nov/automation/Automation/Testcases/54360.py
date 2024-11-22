# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs:

    VMHostname          -- Full hostname of the Virtual machine

    VMUsername          -- Username to login to the virtual machine

    VMPassword          -- Password for the virtual machine

**Note** - Set the below 3 Registry keys under path specified and restart the machine before running this test case.

    Reg Key path: HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon

    Registries(REG_SZ)

        1. DefaultUserName: username (default user name which you want the machine to be logged in to)

        2. DefaultPassword: password (password for default user)

        3. AutoAdminLogon: 1

    PSEXEC is used for interactive download on the remote machine, it should be activated before run

    Requires trials.txt file for testcase execution if not case is skipped

"""

import json

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from CVTrials.trial_helper import TrialHelper


class TestCase(CVTestCase):
    """Class for validating commvault trial bootstrapper download"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express trial - Download using Interactive install"
        self.helper = None
        self.machine = None
        self.trial_file = None
        self.contents = None
        self.options = None
        self.tcinputs = {
            "VMHostname": None,
            "VMUsername": None,
            "VMPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.machine = Machine()
        self.options = OptionsSelector(self.commcell)
        self.helper = TrialHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                self.trial_file = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
                self.contents = json.loads(self.machine.read_file(self.trial_file))
                assert self.contents['status'] == 'passed'

            except Exception as err:
                self.log.error(err)
                self.status = constants.SKIPPED
                return

            machine = Machine(
                machine_name=self.tcinputs.get('VMHostname'),
                username=self.tcinputs.get('VMUsername'),
                password=self.tcinputs.get('VMPassword')
            )

            # To select drive with enough space
            self.log.info('Selecting drive on the machine based on space available')
            drive = self.options.get_drive(machine, size=50)
            if drive is None:
                raise Exception(f"Insufficient space on machine {machine.machine_name}")
            self.log.info('selected drive: %s', drive)

            # Directory to Download the latest code
            download_directory = machine.join_path(drive, 'commvault_trial_download')

            # To remove download directory if exists
            if machine.check_directory_exists(download_directory):
                machine.remove_directory(download_directory)
                self.log.info('Successfully removed directory %s', download_directory)

            # To create download directory on the machine
            machine.create_directory(download_directory)
            self.log.info(
                'Successfully created Commvault trial directory for download in path "%s"',
                download_directory)

            input_json = {
                "IsBootstrapper": True,
                "IsToDownload": True,
                "IsBootStrapMode": True,
                "SelectedOS": [
                    "WinX64"
                ],
                "CustomPackageDir": download_directory,
                "CreateSelfExtracting": True
            }

            # To install the commvault trial package
            self.helper.interactive_install_trial_package(
                hostname=self.tcinputs.get('VMHostname'),
                username=self.tcinputs.get('VMUsername'),
                password=self.tcinputs.get('VMPassword'),
                software_path=self.contents.get('SoftwarePath'),
                input_json=input_json
            )

            if "setup.exe" in str(machine.get_files_in_path(download_directory)):
                self.log.info('Trial interactive download validation successful')
            else:
                raise Exception('Trial interactive download validation failed')

            # To remove download directory if exists
            if machine.check_directory_exists(download_directory):
                machine.remove_directory(download_directory)
                self.log.info('Successfully removed directory %s', download_directory)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """To clean-up the test case environment created"""
        # To delete the Trial software package downloaded
        file_path = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'TrialPackage')
        if self.machine.check_directory_exists(file_path):
            self.machine.remove_directory(file_path)
            self.log.info('Successfully deleted the Trial package downloaded')
