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

import ast

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.CompanyHelper import CompanyMain

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for companies test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test Companies in AdminConsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.comp_obj = None
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            'plans': None,
            'update_plans': None,
            'active_directory': None}

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.comp_obj = CompanyMain(self.admin_console, self.csdb)

            self.comp_obj.plans = self.tcinputs['plans'].split(',')

            self.log.info("Created company object successfully. Now adding a company")
            self.comp_obj.add_new_company()

            self.log.info("Created company, Now validating it")
            self.comp_obj.validate_company()

            self.comp_obj.plans = self.tcinputs['update_plans'].split(',')
            self.comp_obj.contact_name = "abc, def"
            self.comp_obj.primary_site = "abcdef.com"
            self.comp_obj.active_directory = ast.literal_eval(self.tcinputs['active_directory'])
            self.comp_obj.operators = {'add': {'Test1': 'Tenant Operator'},
                                       'remove': None}

            for plan in self.comp_obj.plans:
                query = "select subType from App_Plan where name= '{0}'".format(plan)
                self.csdb.execute(query)
                sub_type = self.csdb.fetch_one_row()
                sub_type_str = ''.join(sub_type)
                if sub_type_str == '33554437':
                    self.comp_obj.server_default_plan = plan
                elif sub_type_str == '33554439':
                    self.comp_obj.laptop_default_plan = plan

            self.log.info("Initial validation completed. Editing Company Tiles")
            self.comp_obj.edit_company_details()

            self.log.info("Editing Completed. Re-validating")
            self.comp_obj.validate_company()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:

            self.comp_obj.delete_existing_company()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
