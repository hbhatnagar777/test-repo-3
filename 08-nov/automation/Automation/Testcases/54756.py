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
    """ Class for validating queue schedule jobs and queue jobs if conflicting job active features"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Validation] : [Queue jobs if conflicting job active, Queue schedule jobs] features ."""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            tc = ServerTestCases(self)
            validator = JobManagementValidator(self)
            validator.validate(features=['queue_jobs_if_conflicting_job_active', 'queue_schedule_jobs'])
        except Exception as excp:
            tc.fail(excp)




