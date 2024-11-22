# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of identity servers (domains) page in Admin console.

functions over,
1. Creation of AD based on criteria passed as
   arguments to the test case and base files.
2. Validates if the AD is created successfully and the values are
   retained correctly.
3. Edits the AD details and re-validates against the user inputs.
4. Removes the AD.
5. Also validates filters in listing page.

TestCase:
    __init__()      --  Method to initialize TestCase class

    run()           --  Method to run the functionality of this test case

    tear_down()     --  Method to do cleanup and close open processes

Options (All AD details):
    {
    ------- AD details for creation ----------------
        "domain_name": "",
        "netbios_name": "",
        "domain_username": "",
        "domain_password": "",
        "user_group": "",
        "local_group": "",
    ------- AD details for updation ---------------
        "modified_domain_name": "",
        "modified_domain_username": "",
        "modified_domain_password": "",
        "proxy_client_value": "",
    ------- test case param -----------------------
        "negative_test": 'true'/'false' (if False, will avoid executing negative test scenarios)
        "table_validation_attempts":    number of retries for validating users table
                                        default: 1,
                                        give 0 to skip table validation
    }

Alternatively:
    CONFIG.Security.LDAPs.Active_Directory can have the initial AD details
    CONFIG.Security.LDAPs.Active_Directory2 can have the edited AD details

"""

import traceback
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper import domain_helper
from Reports.utils import TestCaseUtils

_CONFIG = get_config()


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test - CommCell level AD Domain CRUD Validation in CC"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.browser = None
        self.admin_console = None
        self.domains_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {}

    def setup(self):
        self.domain_name = self.tcinputs.get('netbios_name') or \
                           _CONFIG.Security.LDAPs.Active_Directory.NETBIOSName
        if self.commcell.domains.has_domain(self.domain_name):
            self.log.info(f"Deleting domain part of pre-requisite: {self.domain_name}")
            self.commcell.domains.delete(self.domain_name)

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.identity_server_helper = IdentityServersMain(admin_console=self.admin_console, commcell=self.commcell,
                                                          csdb=self.csdb)

    def run(self):
        errors = []

        # TABLE DB VALIDATIONS
        retries = int(self.tcinputs.get('table_validation_attempts', 1))

        for attempt in range(retries):
            try:
                self.identity_server_helper.validate_listing_company_filter()
                break
            except Exception as exp:
                self.log.error(exp)
                self.log.error(traceback.format_exc())
                if attempt == retries - 1:
                    errors.append(f"Error during identity server listing company filter attempt {attempt}: {exp}")

        # CRUD
        try:
            self.domains_obj = domain_helper.DomainHelper(self.admin_console)
            self.domains_obj.domain_name = self.tcinputs.get('domain_name') or \
                                           _CONFIG.Security.LDAPs.Active_Directory.DomainName
            self.domains_obj.netbios_name = self.tcinputs.get('netbios_name') or \
                                            _CONFIG.Security.LDAPs.Active_Directory.NETBIOSName
            self.domains_obj.domain_username = self.tcinputs.get('domain_username') or \
                                               _CONFIG.Security.LDAPs.Active_Directory.UserName
            self.domains_obj.domain_password = self.tcinputs.get('domain_password') or \
                                               _CONFIG.Security.LDAPs.Active_Directory.Password
            self.domains_obj.user_group = self.tcinputs.get("user_group") or \
                                          _CONFIG.Security.LDAPs.Active_Directory.UserGroupsToImport[0].externalgroup
            self.domains_obj.local_group = self.tcinputs.get("local_group") or ["master"]

            self.log.info("***** Adding a domain*****")
            self.domains_obj.add_domain(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("***** Validating the domain*****")
            self.domains_obj.validate_domain()

            self.log.info("***** Editing a domain*****")
            self.domains_obj.domain_name = self.tcinputs.get('modified_domain_name') or \
                                           _CONFIG.Security.LDAPs.Active_Directory2.DomainName
            self.domains_obj.domain_username = self.tcinputs.get('modified_domain_username') or \
                                               _CONFIG.Security.LDAPs.Active_Directory2.UserName
            self.domains_obj.domain_password = self.tcinputs.get('modified_domain_password') or \
                                               _CONFIG.Security.LDAPs.Active_Directory2.Password
            self.domains_obj.proxy_client = True
            self.domains_obj.proxy_client_value = self.tcinputs.get('proxy_client_value') or \
                                                  self.commcell.commserv_name
            self.domains_obj.edit_domain(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("***** Validating the domain*****")
            self.domains_obj.validate_domain()
            self.log.info("***** Deleting the domain *****")
            self.domains_obj.delete_domain()
        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during AD CRUD: {exp}")

        if errors:
            self.log.info(">>>>>>> TESTCASE FAILED! <<<<<<<<<")
            self.status = constants.FAILED
            self.result_string = '\n'.join(errors)

    def tear_down(self):
        """ To clean-up the test case environment created """
        if self.commcell.domains.has_domain(self.domain_name):
            self.log.info(f"Deleting domain part of clean up {self.domain_name}")
            self.commcell.domains.delete(self.domain_name)

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
