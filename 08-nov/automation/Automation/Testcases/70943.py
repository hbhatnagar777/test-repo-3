"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating : Web Routing - Reverse Sync

Input Example:

    NOTE: ALL INPUTS ARE OPTIONAL, WILL BE FETCHED FROM multicommcellconstants.py
          self.commcell MUST ALWAYS BE ROUTER

    tcinputs:
        see WebRoutingHelper init config options

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.web_routing_helper import WebRoutingHelper


class TestCase(CVTestCase):
    """Router testcase"""

    def __init__(self):
        """ init method"""
        super(TestCase, self).__init__()
        self.web_routing_helper = None
        self.name = "Web Routing - Reverse Sync"
        self.tcinputs = {}

    def setup(self):
        self.web_routing_helper = WebRoutingHelper(self.commcell, **self.tcinputs)

    def run(self):
        self.web_routing_helper.refresh_test(auto_sync=True)
