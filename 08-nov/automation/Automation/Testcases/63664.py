# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from AutomationUtils.idautils import CommonUtils

from Reports.utils import TestCaseUtils



class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode] - Laptop summary tile from setting page validation"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode] - Laptop summary tile from setting page validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.idautils = None
        self.utility = None
        self.edgeHelper_obj = None
        self.edgemain_obj = None
        self.machine_object= None
        self.client_data= None
        self._sla_status = None
        self.laptop_obj = None
        self.client_name = None
        self.subclient_obj = None

    def setup(self):
        """Initializes objects required for this testcase"""
        self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
        self.utility = OptionsSelector(self.commcell)
        self.idautils = CommonUtils(self)
        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        
        self.admin_console.login(self.tcinputs["Edge_username"],
                                 self.tcinputs["Edge_password"])

        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.machine_object = self.utility.get_machine_object(
                self.tcinputs['Machine_host_name'], self.tcinputs['Machine_user_name'], self.tcinputs['Machine_password']
            )
        self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
        self.edgeHelper_obj.enduser = self.tcinputs["Edge_username"]
        self.edgeHelper_obj.machine_object = self.machine_object
        self.edgeHelper_obj.client_name = self.tcinputs["Client_name"]
        self.subclient_obj = self.idautils.get_subclient(self.tcinputs["Client_name"])


    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.edgeHelper_obj.validate_settings_page_summary_tile( plan_name=self.tcinputs["Default_Plan"],
                                                                    options=self.tcinputs["osc_options"])
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

