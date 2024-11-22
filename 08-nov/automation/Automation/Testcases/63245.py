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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing VSA Azure Auto SCale validation for
    suspend and resume"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure Auto Scale Validation os suspend and resume case"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.result_string = ''
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""
        try:
            self.tc_utils.initialize(self)
            self.tc_utils.run_auto_scale_validation(self,
                                                    backup_type="FULL",
                                                    suspend_and_resume=True)

        except Exception as err:
            self.log.error(err)
            self.result_string = str(err)
            self.status = constants.FAILED
            self.failure_msg = str(err)

