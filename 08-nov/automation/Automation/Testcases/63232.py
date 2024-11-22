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
    __init__()                      --  initialize TestCase class

    setup()                         --  sets up the variables required for running the testcase

    run()                           --  run function of this test case

    tear_down()                     --  tears down function

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestCaseInitFailure
from MetallicRing.Core.config_reader import ConfigReader


class TestCase(CVTestCase):
    """Class For executing metallic ring automation"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.config_reader = None
        self.job_controller = None
        self.name = "Class for executing metallic ring automation"

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.log.info("Setting up Config Reader module")
            self.config_reader = ConfigReader()
            self.config_reader.read_and_update_config_files()
            from MetallicRing.Core.job_controller import JobController
            self.job_controller = JobController()
            self.log.info("Job controller module initialized")
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.log.info("Starting the ring automation task")
            self.job_controller.start_task()
            self.log.info("Ring automation task complete")
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """tears down function for cleaning up the entries if any present"""
        try:
            if self.status != constants.FAILED:
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.info("Test case execution failed")
            handle_testcase_exception(self, exp)
