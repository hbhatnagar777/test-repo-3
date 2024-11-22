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

    HyperVHostname      -- Full hostname of the hyperv machine

    VMHostname          -- Full hostname of the Virtual machine

    HyperVUsername      -- Username to login to the hyperv

    HyperVPassword      -- Password for the hyperv machine

    VMUsername          -- Username to login to the virtual machine

    VMPassword          -- Password for the virtual machine

Optional Inputs:

    SoftwarePath        -- Full path of the commvault trial package


**Note** - Set the below 3 Registry keys under path specified and restart the machine before running this test case.

    Reg Key path: HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon

    Registries(REG_SZ)

        1. DefaultUserName: username (default user name which you want the machine to be logged in to)

        2. DefaultPassword: password (password for default user)

        3. AutoAdminLogon: 1

    PSEXEC is used for installation on the remote machine, it should be activated before run

    Requires trials.txt file for testcase execution if not case is skipped

"""

import json

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Install.install_helper import InstallHelper
from CVTrials.trial_helper import TrialHelper


class TestCase(CVTestCase):
    """Class for installing commvault trial software package"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "To install the Commvault Trial package downloaded from cloud"
        self.helper = None
        self.install = None
        self.trial_file = None
        self.contents = None
        self.machine = None

        self.tcinputs = {
            "HyperVHostname": None,
            "VMHostname": None,
            "HyperVUsername": None,
            "HyperVPassword": None,
            "VMUsername": None,
            "VMPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # To create a machine class object for the local machine
        self.machine = Machine()

        self.install = InstallHelper(self.commcell)
        self.helper = TrialHelper(self)

        # To Revert the VM to the fresh snap
        self.install.revert_snap(
            server_name=self.tcinputs.get('HyperVHostname'),
            username=self.tcinputs.get('HyperVUsername'),
            password=self.tcinputs.get('HyperVPassword'),
            vm_name=self.tcinputs.get('VMHostname').split('.')[0]
        )

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                self.trial_file = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
                self.contents = json.loads(self.machine.read_file(self.trial_file))
                assert self.contents['status'] == 'passed'
                self.contents['status'] = 'failed'
            except Exception as err:
                self.log.error(err)
                self.status = constants.SKIPPED
                return

            input_json = {
                "IsBootstrapper": True,
                "IsToDownload": False,
                "IsBootStrapMode": True,
                "SelectedOS": [
                    "WinX64"
                ],
                "CreateSelfExtracting": True,
            }

            # To install the commvault trial package
            self.helper.interactive_install_trial_package(
                hostname=self.tcinputs.get('VMHostname'),
                username=self.tcinputs.get('VMUsername'),
                password=self.tcinputs.get('VMPassword'),
                software_path=self.contents.get('SoftwarePath'),
                input_json=input_json
            )

            machine = Machine(
                machine_name=self.tcinputs.get('VMHostname'),
                username=self.tcinputs.get('VMUsername'),
                password=self.tcinputs.get('VMPassword')
            )
            url = machine.read_file(
                machine.join_path('C:', 'AUTOMATION_LOC', 'InteractiveInstall.log'),
                search_term='Admin Console URL: ')
            # Admin console URL
            try:
                url = url.split('Admin Console URL: ')[1].split('"')[0]
            except Exception:
                self.log.error('Not able to locate Admin console URL, please check Interactive install logs')
                raise Exception('Interactive install failed, please check the install logs')
            self.contents['URL'] = url
            self.contents['Commcell'] = self.tcinputs.get('VMHostname')
            self.contents['status'] = "passed"

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            with open(self.trial_file, 'w') as file:
                file.write(json.dumps(self.contents))
