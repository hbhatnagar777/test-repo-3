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

    tear_down()     --  tear down function of this test case

"""
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanagement_validator import JobManagementValidator
from Server.JobManager.jobmanagement_helper import JobManagementHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "[Validation] : [Job Priority, Agent level and client level]"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.tcinputs = {
            "ClientName": None,    # Windows Client
            "ClientName2":None      # Linux Client
        }
        self.server = None
        self.jm_helper = None
        self.restart_props = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("executing testcase")
        self.server = ServerTestCases(self)
        self.jm_helper = JobManagementHelper(self.commcell) 
        self.restart_props = self.jm_helper.get_restart_setting("File System and Indexing Based (Data Protection)")

    def run(self):
        """Run function of this test case"""
        try:
            self.server = ServerTestCases(self)
            validator = JobManagementValidator(self)
            validator.job_priority() 

        except Exception as exp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(exp, "test case failed in run function")

    def tear_down(self):
        self.jm_helper.modify_restart_settings([self.restart_props])
