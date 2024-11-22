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

**Note** Requires trials.txt file for testcase execution if not case is skipped

"""

import json

from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from cvpysdk.commcell import Commcell

from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for registering commvault trial package"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express Trial - Download and install Test Automation and PythonSDK package"
        self.trial_file = None
        self.contents = None
        self.machine = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.machine = Machine()

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

            commcell = Commcell(
                self.contents.get('Commcell'),
                self.contents.get('Commvault ID'),
                self.contents.get('Password')
            )

            self.log.info('Installing TestAutomation and PythonSDK package on the commcell')
            job = commcell.install_software(
                client_computers=[commcell.commserv_name],
                windows_features=[
                    WindowsDownloadFeatures.TEST_AUTOMATION.value,
                    WindowsDownloadFeatures.PYTHON_SDK.value
                ]
            )

            job = JobManager(job, commcell)
            install_helper = InstallHelper(commcell)

            try:
                job.wait_for_state(retry_interval=30, time_limit=120)
            except Exception:
                try:
                    commcell.commserv_client.is_ready
                except Exception:
                    install_helper.wait_for_services()
                    job.wait_for_state(retry_interval=30, time_limit=120)

            # To validate the job state
            job.validate_job_state('completed')

            self.log.info('TestAutomation and PythonSDK installed successfully')
            self.contents['status'] = "passed"

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            with open(self.trial_file, 'w') as file:
                file.write(json.dumps(self.contents))
