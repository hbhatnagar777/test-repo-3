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
import random, inspect

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
        self.name = "Companies - Edit company properties"

        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.common_password = self.inputJSONnode['commcell']['commcellPassword']
        
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
        self.commcell.organizations.refresh()
        self.msp_orghelper_obj.cleanup_orgs('del automated')