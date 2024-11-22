# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import json

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.theme_helper import NavPrefsHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    BrowserFactory, Browser
)
from Web.Common.page_object import TestStep

"""
TestCase to validate Manage->Customization->navigation preference page in CC

tcinputs:
    'admin_password':       password for commcell sdk login passed earlier
    'default_password':     password for all persona entities,

    'msp_user':             msp_user persona's name to setup/reuse
    'company':              name of company to test on/create (for tenant personas),
    'company_alias':        alias name for company to create
    'tenant_admin':         tenant admin login name to create/reuse
    'tenant_user':          tenant user login name to create/reuse

    'nav_routes_json':      filepath with json response to GET getNavList.do?orgId=0 from browser network tab
    'max_thread':           number of thread to limit while testing personas in parallel
    'validate_load':        if True, will report error during page load like permission or alert toasts
    
    'num_navs':             number of navs to test [for enable and disable each]. default 5
    'avoid_nav_routes':     comma seperated nav routes to avoid testing. 
                            give using localization -> example: 'label.webconsole, label.manage/label.security'
                            default None
    'avoid_personas':       comma seperated personas to avoid testing. default None
"""


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.avoid_personas = None
        self.avoid_routes = None
        self.nav_prefs_helper = None
        self.relog = None
        self.name = "Basic acceptance test case for Navigation Preferences"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {}

    def run(self):
        """ Initial configuration for the test case. """
        if avoid_routes := self.tcinputs.get('avoid_nav_routes'):
            if isinstance(avoid_routes, str):
                avoid_routes = [r.strip() for r in avoid_routes.split(',')]
            self.avoid_routes = avoid_routes
        self.log.info(f">>> avoiding nav routes: {avoid_routes}")

        if avoid_personas := self.tcinputs.get('avoid_personas'):
            if isinstance(avoid_personas, str):
                avoid_personas = [p.strip() for p in avoid_personas.split(',')]
            self.avoid_personas = avoid_personas

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.nav_prefs_helper = NavPrefsHelper(
                self.commcell, self.admin_console,
                **self.tcinputs | {
                    'admin_password': self.inputJSONnode['commcell']['commcellPassword']
                }
            )
            self.nav_prefs_helper.setup_personas()
            persona_errors = self.nav_prefs_helper.test_nav_prefs(
                num_navs=int(self.tcinputs.get('num_navs') or 5),
                avoid_nav_routes=self.avoid_routes,
                avoid_personas=self.avoid_personas
            )
            result = {}
            self.status = constants.PASSED
            self.log.info("****** NAVPREFS TEST COMPLETED SUMMARY ******")
            for persona, errors in persona_errors.items():
                if not errors:
                    result[persona] = 'PASSED'
                    self.log.info(f"{persona} = PASSED!")
                else:
                    self.log.error(f"{persona} = FAILED!")
                    self.status = constants.FAILED
                    for error in errors:
                        self.log.error(error)
                    result[persona] = ["{:.40}".format(error) for error in errors]
                self.log.info("--------------------------------------------------")
            self.result_string = json.dumps(result, indent=4)
        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
