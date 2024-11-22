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
from datetime import datetime

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Editing Server Plan Details in AdminConsole"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.plan_obj = None
        self.admin_console = None
        self.tcinputs = {
            'primary_storage': None
            }

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
            self.plan_obj = PlanMain(self.admin_console)
            date_time = datetime.today().strftime("%H_%M_%S")
            self.plan_obj.plan_name = {'server_plan': 'plan_'+date_time}
            self.plan_obj.storage['pri_storage'] = self.tcinputs['primary_storage']
            self.plan_obj.edit_server_plan_dict['edit_storage'] = {'Edit': True,
                                                                   'old_storage_name': "Primary",
                                                                   'new_storage_name': 'Storage_'+datetime.today()
                                                                   .strftime("%H_%M_%S"),
                                                                   'new_ret_period': '20'}

            # Creating the server plan
            self.plan_obj.add_plan()
            self.log.info('Added the plan successfully')

            # Editing the server plan
            self.plan_obj.edit_server_plan()
            self.log.info('Edited the plan successfully')

            # Validating the sever plan
            self.plan_obj.validate_plan_details()
            self.log.info('Plan details validated successfully')

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.plan_obj.delete_plans()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
