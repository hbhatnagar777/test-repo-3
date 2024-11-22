# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: verify RPO feature is enabled trough reg key

"""
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.JobManager.rpo_helper import RpoHelper
from Server.JobManager.rpo_constants import RPO_ADDITIONAL_SETTING_KEY


class TestCase(CVTestCase):
    """Class for executing verification test for RPO feature is enabled trough reg key"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "verify RPO feature is enabled trough reg key"
        self.tcinputs = {
            'ClientName': None,  # client name where subclient will be created
            'MediaAgent': None   # media agent where disk library is created
        }
        self.rpo_helper_obj = None
        self.server = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        # registry key is set in creating RPO helper object
        self.log.info("adding registry key %s for commcell", RPO_ADDITIONAL_SETTING_KEY)
        self.rpo_helper_obj = RpoHelper(self.commcell,
                                        self.tcinputs['ClientName'],
                                        self.tcinputs['MediaAgent'])
        self.server = ServerTestCases(self)

    def run(self):
        """Main function for test case execution"""
        try:
            if self.rpo_helper_obj.verify_rpo_is_enabled() == 0:
                raise Exception("RPO is disabled even after adding through reg key {0}".format(
                    RPO_ADDITIONAL_SETTING_KEY))
            else:
                self.log.info("RPO is enabled successfully from reg key %s",
                              RPO_ADDITIONAL_SETTING_KEY)
        except Exception as excp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.log.info("deleting registry key %s for commcell", RPO_ADDITIONAL_SETTING_KEY)
        self.commcell.delete_additional_setting('CommServe', RPO_ADDITIONAL_SETTING_KEY)
