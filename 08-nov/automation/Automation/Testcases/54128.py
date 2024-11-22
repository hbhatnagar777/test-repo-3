"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating : Web Routing - User Redirects

Input Example:

    NOTE: ALL INPUTS ARE OPTIONAL, WILL BE FETCHED FROM multicommcellconstants.py IF NOT GIVEN
          self.commcell MUST ALWAYS BE ROUTER

    tcinputs:
        method_preference   (str)   -   the method preferred to validate redirects UI, API or DB
        repeats             (int)   -   the number of repeats to make for API and DB calls to collect times
        methods             (int)   -   the list of methods to use to collect redirects ['UI', 'API', 'DB']
        for other inputs see WebRoutingHelper config options
"""
import os
import pandas as pd

from AutomationUtils import constants
from AutomationUtils.constants import TEMP_DIR
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.web_routing_helper import WebRoutingHelper


class TestCase(CVTestCase):
    """Router testcase"""

    def __init__(self):
        """ init method"""
        super(TestCase, self).__init__()
        self.web_routing_helper = None
        self.name = "Web Routing - User Redirects"
        self.tcinputs = {}

    def setup(self):
        self.web_routing_helper = WebRoutingHelper(self.commcell, **self.tcinputs)

    def run(self):
        redirect_summary, errors = self.web_routing_helper.validate_all_redirects(
            method_preference=self.tcinputs.get('method_preference') or 'UI',
            repeats=self.tcinputs.get('repeats') or 10,
            methods=self.tcinputs.get('methods')
        )
        excel_filepath = os.path.join(TEMP_DIR, 'webrouting_redirects_summary.xlsx')
        with pd.ExcelWriter(excel_filepath, engine='openpyxl') as writer:
            redirect_summary.to_excel(writer, sheet_name='Sheet1')
        if errors:
            for error in errors:
                self.log.error(error)
            self.status = constants.FAILED
        self.result_string = 'SUCCESS' if not errors else '\n'.join(errors)
        self.attachments = [excel_filepath]
