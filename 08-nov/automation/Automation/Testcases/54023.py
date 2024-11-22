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

    Hostname        -- Full hostname of the machine

    Username        -- username to access the machine

    Password        -- Password to access tha machine

    VirtualMachines -- Virtual machines to add the the VM group

    **Note** VirtualMachines is comma separated

**Note** Requires trials.txt file for testcase execution if not case is skipped

"""

import json

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from CVTrials.trial_helper import TrialHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for configuring virtualization and starting first backup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express - configure virtualization"
        self.helper = None
        self.browser = None
        self.driver = None
        self.trial_file = None
        self.contents = None

        # To create local machine object
        self.machine = Machine()
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            "Hostname": None,
            "Username": None,
            "Password": None,
            "VirtualMachines": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.helper = TrialHelper(self)

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

            # To make list all the virtual machines
            virtual_machines = self.tcinputs.get('VirtualMachines').split(',')

            # To configure virtualization and to run VSA backup
            self.helper.configure_virtualization(
                url=self.contents.get('URL'),
                commcell_username=self.contents.get('Commvault ID'),
                commcell_password=self.contents.get('Password'),
                hostname=self.tcinputs.get('Hostname'),
                machine_username=self.tcinputs.get('Username'),
                machine_password=self.tcinputs.get('Password'),
                group_name='Commvaultone',
                virtual_machines=virtual_machines
            )

            # To store basic SDK object details
            self.contents['Client'] = self.tcinputs.get('Hostname')
            self.contents['Agent'] = 'Virtual Server'
            self.contents['Instance'] = 'VMWare'
            self.contents['Backupset'] = 'defaultBackupSet'
            self.contents['Subclient'] = 'Commvaultone'

            self.contents['status'] = "passed"

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            with open(self.trial_file, 'w') as file:
                file.write(json.dumps(self.contents))

    def tear_down(self):
        """To clean-up the test case environment created"""
        # To close the browser
        Browser.close_silently(self.browser)
