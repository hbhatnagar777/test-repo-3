# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# Sample inputs format {"days_old":"2"}.

"""TestCase to check older days files in the Reports folder"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Test case to check report files older days in the CommServe machine's Reports directory."""

    test_step = TestStep()

    def __init__(self):
        """
        Initializes the test case by setting up the name, CommServe machine reference, and the reports directory.
        """
        super(TestCase, self).__init__()
        self.name = "Check old report files"
        self.cs_machine = None
        self.reports_dir = None
        self.days_old = None

    def _init_tc(self):
        """
        Initial configuration for the test case, setting up the CommServe machine and Reports directory.
        """
        try:
            self.log.info("Setting up the test case environment.")
            if self.commcell is None:
                self.log.error("Commcell is not initialized.")
                raise CVTestCaseInitFailure("Commcell is not initialized.")

            # Determine OS type and select the appropriate machine class
            self.cs_machine = Machine(self.commcell.commserv_client)
            self.log.info(f"CS Machine: {self.cs_machine.machine_name}")
            self.reports_dir = self.cs_machine.join_path(self.commcell.commserv_client.install_directory, "Reports")
            self.log.info(f"Reports directory set to {self.reports_dir}")

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def check_old_files_in_reports(self):
        """
        Verify the older files in the reports directory.

        Raises:
            CVTestStepFailure: If files older days are found.
        """
        try:
            self.days_old = self.tcinputs['days_old']
            self.log.info(f"Checking for files older than {self.days_old} days in the Reports directory.")

            # Call the get_files_in_path function to check for files older days
            old_files = self.cs_machine.get_files_in_path(self.reports_dir, recurse=False, days_old=self.days_old)

            if old_files:
                self.log.error(f"Found {len(old_files)} file(s) older than {self.days_old} "
                               f"days in the Reports directory.")
                self.log.error(old_files)
                raise CVTestStepFailure(f"Test failed. Found files older than {self.days_old} days.")
            else:
                self.log.info(f"No files older than {self.days_old} days found in the Reports directory.")

        except Exception as exception:
            raise CVTestStepFailure(exception) from exception

    def run(self):
        """
        Run method for the test case. Sets up the environment and performs the file check.
        """
        try:
            # Set up the test case
            self._init_tc()

            # Check for old files in the Reports directory
            self.check_old_files_in_reports()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.log.info("Test case execution completed.")
