# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Ring Routing: Reseller Overview Page and Sync [UI]

This testcase verifies the 6 synced properties panels in overview page for an associated reseller
    Data Encryption
    Autodiscovery
    Operators
    Contacts
    Tags

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed


TestCase Inputs:
    {
        "reseller": str             -   (Optional) will test on existing reseller if given, 
                                        reseller will be created otherwise
        "laptop_plan": str          -   (Required) to bypass guided setup redirections
        "exclusions": str           -   (Optional) will skip testing for personas given 
                                        ex: 'MSP as Operator, Tenant Admin, 
                                            'Tenant User, MSP without Operator'
        "property_exclusions": str  -   (Optional) panel names to ignore if missing
                                        default is 'all'
                                        ex: "dlp,autodiscovery,operators,contacts,tags,themes,all"
        "default_password": str     -   (Optional) default password to use for all company users, 
                                        will use random password otherwise
        "edit_dict": dict           -   (Optional) what panels to edit for what personas,
                                        default is None, no panels will be edited for any persona.
                                        ex: {persona_name: "panels comma seperated", ...}
    }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.ring_routing_helper import RingRoutingHelperUI
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.edit_dict = {}
        self.prop_exclusions = ''
        self.exclusions = ''
        self.ring_routing_helper = None
        self.reseller = None
        self.name = "Ring Routing: Reseller Overview Page and Sync [UI]"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            "laptop_plan": None
        }

    def setup(self):
        self.reseller = self.tcinputs.get('reseller')
        self.exclusions = self.tcinputs.get('exclusions', '')
        self.prop_exclusions = self.tcinputs.get('property_exclusions', '') + ',themes'
        self.edit_dict = eval(self.tcinputs.get('edit_dict', '{}'))

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword']
        )
        self.ring_routing_helper = RingRoutingHelperUI(
            self.admin_console, self.commcell,
            self.inputJSONnode['commcell']['commcellPassword'],
            company=self.reseller,
            plan=self.tcinputs['laptop_plan'],
            company_password=self.tcinputs.get('default_password')
        )
        if not self.reseller:
            self.ring_routing_helper.setup_reseller()
        else:
            self.ring_routing_helper.setup_existing_companies()
        self.ring_routing_helper.setup_company_user()

    def run(self):
        personas = {
            'Tenant Admin': self.ring_routing_helper.use_tenant_admin,
            'Tenant User': self.ring_routing_helper.use_tenant_user,
            'MSP without operator': self.ring_routing_helper.use_msp_admin,
            'MSP as Operator': lambda: self.ring_routing_helper.use_msp_admin(as_operator_of='reseller')
        }
        self.ring_routing_helper.use_tenant_admin()
        if not self.reseller:
            self.log.info("No existing reseller given, creating new reseller and skipping tenant user's validation")
            self.exclusions += ",Tenant User"
        try:
            for persona in personas:
                if persona in self.exclusions:
                    self.log.info(f"****** SKIPPING TEST FOR {persona} ******")
                    continue
                self.log.info(f"****** VALIDATING TEST FOR {persona} ******")
                personas[persona]()
                self.admin_console.close_popup()
                self.ring_routing_helper.validate_sync_properties(
                    exclusions=self.prop_exclusions,
                    edit_list=self.edit_dict.get(persona, '')
                )

                self.log.info(f"****** VALIDATION SUCCESSFUL FOR {persona} ******")
            self.log.info("******** ALL TESTS PASSED ********")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.reseller:
                self.ring_routing_helper.clean_up()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

