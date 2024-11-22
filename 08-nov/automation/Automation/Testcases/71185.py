# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for send logs HSX
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    tear_down()                     --  Tear down function of this test case
      
    parse_cluster_details()         -- Parses the cluster details output
      
    fail_test_case()                -- Prints failure reason, sets the result string
      
    run()                           --  run function of this test case
      

Sample input json
"71185": {
            "NodeName": "",
            "CSUser": "",
            "CSPassword": "",
            "CSSendLogsPath": ""
         }

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

class TestCase(CVTestCase):
    """Hyperscale test class for send logs HSX"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for 2x: Run and verify sendlogs job with HSX information"
        self.tcinputs = {
            "NodeName": "",
            "CSUser": "",
            "CSPassword": "",
            "CSSendLogsPath": ""
         }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""

        self.node_name = self.tcinputs['NodeName']
        self.cs_user = self.tcinputs['CSUser']
        self.cs_password = self.tcinputs['CSPassword']
        self.cs_send_logs_path = self.tcinputs['CSSendLogsPath']

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        
        self.rehydrator = Rehydrator(self.id)
        self.trigger_done = self.rehydrator.bucket('trigger_done')

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.warning("Test case failed")
            self.status = constants.FAILED

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

    def run(self):
        """ run function of this test case"""
        try:
            if not self.trigger_done.get(False):
                result, reason = self.hyperscale_helper.trigger_sendlogs(self.node_name, self.cs_send_logs_path)
                if not result:
                    return self.fail_test_case(reason + " | Failed to trigger send logs")
                self.trigger_done.set(True)
            
            self.hyperscale_helper.verify_sendlogs(self.cs_send_logs_path, self.commcell.commserv_hostname, self.cs_user, self.cs_password)

            self.successful = True
            self.log.info(f"Send logs automation and validation successful. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
