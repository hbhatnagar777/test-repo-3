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

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanagement_validator import JobManagementValidator


class TestCase(CVTestCase):
    """ Class for validating total running time feature at commcell level"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Validation] : [Total running time at commcell level]"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            tc = ServerTestCases(self)
            validator = JobManagementValidator(self)
            validator.validate(features=['job_total_running_time_commcell'])
        except Exception as excp:
            tc.fail(excp)