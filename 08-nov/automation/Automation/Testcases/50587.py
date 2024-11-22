# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of Plans in Admin console.

functions over,
1. Creation of plans based on different criteria's passed as
   arguments to the test case and base files.
2. Validates if the plans are created successfully and the values are
   retained correctly.
3. Deletes the plans created & verified in above steps.

Pre-requisites :
1. Index Server should be configured, if using Edge Drive Feature for Laptop Plam.
2. Primary and secondary storage pools should be configured.
"""

import ast
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ Basic Acceptance test for Plans """

    def __init__(self):
        """ Initializing the Test case file """

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test Plans in AdminConsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.utils = TestCaseUtils(self)
        self.plan_obj = None
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            'plan_name': None,
            'primary_storage': None,
            'secondary_storage': None,
            'media_agent': None
        }

    def run(self):
        """ Run method for test case file """
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            self.log.info("Creating the login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("login successful")

            self.plan_obj = PlanMain(self.admin_console)

            self.plan_obj.plan_name = ast.literal_eval(self.tcinputs['plan_name'])
            self.plan_obj.storage['pri_storage'] = self.tcinputs['primary_storage']
            self.plan_obj.storage['sec_storage'] = self.tcinputs['secondary_storage']
            self.plan_obj.media_agent = self.tcinputs['media_agent']

            self.plan_obj.add_plan()
            self.log.info("Plans Creation completed. validating plans...")

            self.plan_obj.validate_plans()
            self.log.info("Plans validation completed. deleting plans...")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:

            self.plan_obj.delete_plans()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
