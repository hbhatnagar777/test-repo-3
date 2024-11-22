"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating : Web Routing - All Service Commcell Registrations

Input Example:

    NOTE: ALL INPUTS ARE OPTIONAL, WILL BE FETCHED FROM multicommcellconstants.py
          self.commcell MUST ALWAYS BE ROUTER

    tcinputs:
        avoid_cases (str)   -   comma seperated list of cases to avoid testing registration
                                (see WebRoutingHelper.registration_cases)
        retry_cases (int)   -   number of times to retry each registration case on failure
        for other inputs see WebRoutingHelper config options

"""
import json
import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.web_routing_helper import WebRoutingHelper


class TestCase(CVTestCase):
    """Router testcase"""

    def __init__(self):
        """ init method"""
        super(TestCase, self).__init__()
        self.retries = None
        self.avoid_cases = None
        self.web_routing_helper = None
        self.name = "Web Routing - All Service Commcell Registrations"
        self.tcinputs = {}
        self.results = {}

    def setup(self):
        self.web_routing_helper = WebRoutingHelper(self.commcell, **self.tcinputs)
        self.web_routing_helper.master_roles = ['ad_user']
        self.avoid_cases = [case.strip() for case in (self.tcinputs.get('avoid_cases') or '').split(',')]
        self.retries = int(self.tcinputs.get('retry_cases') or 1)

    def run(self):
        self.status = constants.PASSED
        for case in WebRoutingHelper.registration_cases:
            if case in self.avoid_cases:
                self.log.info(f">>>> SKIPPING CASE {case}")
                self.results[case] = 'SKIPPED'
            else:
                self.log.info(f">>>> STARTING CASE {case}")
                for _ in range(self.retries):
                    try:
                        self.web_routing_helper.registration_test(case)
                        self.results[case] = 'PASSED'
                        break
                    except Exception as exp:
                        self.log.error(f">> Got Exception: {exp}\n{traceback.format_exc()}")
                        self.results[case] = str(exp)
                        self.status = constants.FAILED

        self.result_string = json.dumps(self.results, indent=4)
        self.log.info(self.result_string)
