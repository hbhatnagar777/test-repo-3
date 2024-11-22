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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Server.organizationhelper import OrganizationHelper
import inspect, copy

class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        This testcase verifies:
            1. Editing all the tiles present on organization details page
        """
        super(TestCase, self).__init__()
        self.name = "N Level Reseller - Companies - Edit company properties"

        self.tcinputs = {
            "reseller_level": 2
        }

    def setup(self):
        """Setup function of this test case"""
        common_password = self.inputJSONnode['commcell']['commcellPassword']
        self.original_commcell = copy.deepcopy(self.commcell)
        self.testcase_id = str(self.id)
        
        # configure n level reseller
        if self.tcinputs.get('reseller_level', 0) > 0:
            self.reseller_company_info = OrganizationHelper(self.commcell).configure_n_level_reseller_company(testcase_id=self.testcase_id,
                                                                                                              commcell=self.commcell,
                                                                                                              level=self.tcinputs['reseller_level'], 
                                                                                                              password=common_password)
            self.result_string = f'Testcase executed with {self.tcinputs["reseller_level"]} level reseller'
            
            # switch the testcase flow to reseller
            self.commcell = self.reseller_company_info['ta_loginobj']
            self.commcell.refresh()
        
        self.infos = OrganizationHelper(self.commcell).setup_company()
        self.log.info(f"Company Name : {self.infos['company_name']}")
        
        self.msp_orghelper_obj = OrganizationHelper(self.commcell, self.infos['company_name'])
        

    def run(self):
        """Run function of this test case"""
        try:
            failure_count = 0
            failed_functions = []
            self.commcell.refresh()
            
            functions = list()
            # getting all function objects that starts with validate_edit_
            for function_name, function_obj in inspect.getmembers(object= self.msp_orghelper_obj):
                if function_name == 'validate_edit_passkey': continue # skip this function
                if function_name.startswith('validate_edit_'): functions.append(function_obj)
            
            for function in functions:
                try:
                    function()
                except Exception as err:
                    self.log.info('[Exception] in [{}]: [{}]'.format(function.__name__,err))
                    failed_functions.append(function)

            # retry once more for failed functions
            exceptions_list = []
            self.log.info('Retrying failed functions...')
            self.commcell.refresh()
            for function in failed_functions:
                try:
                    function()
                except Exception as err:
                    exceptions_list.append(err)
                    self.log.info('[Exception] in [{}]: [{}]'.format(function.__name__,err))
                    failure_count += 1

            if failure_count != 0: raise Exception(f'Failure Count : {failure_count} -- Some Edits Failed. Please Check!. Exceptions : {exceptions_list}')

            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell = self.original_commcell # switch back to original commcell
        self.commcell.refresh()
        
        self.commcell.organizations.refresh()
        OrganizationHelper(self.commcell).cleanup_orgs(marker=self.testcase_id)
        OrganizationHelper(self.commcell).cleanup_orgs(marker='DEL Automated')