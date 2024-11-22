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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

import sys
from logging import exception

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Application.Exchange.ExchangeMailbox.msgraph_helper import CVEXMBGraphOps
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Web.AdminConsole.Office365Pages.constants import ExchangeOnline, O365Region
from Web.Common.exceptions import CVWebAutomationException
import re


class TestCase(CVTestCase):
    """
    Metallic Discovery filter verification
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic Discovery filter verification"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.app_type = None
        self.users = None
        self.app_name = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)
        self.machine = None

    def setup(self):
        self.exmbclient_object = ExchangeMailbox(self)
        self.msgraph_helper = CVEXMBGraphOps(self.exmbclient_object)

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['tenantUsername'],
                                 self.inputJSONnode['commcell']['tenantPassword'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs['Name']
        self.discovery_filter_value=self.tcinputs["discoveryFilter"]
        self.edit_discovery_filter_value=self.tcinputs["editFilter"]
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(
            self.admin_console, self.app_type, is_react=True)

    def verify_discovery_filter_count(self,discovery_filter):
        """
        Verify the mailboxes count in discovery panel
        Args:
            discovery_filter(dict) - discovery filter attribute and attribute value
        """
        self.admin_console.access_tab(self.office365_obj.constants.OVERVIEW_TAB.value)
        self.office365_obj.__click_discovery_stats()
        self.office365_obj.get_discovery_stats()
        details = self.office365_obj.get_discovery_panel_data()
        for attribute_name in discovery_filter:
            filtered_groups = []
            if attribute_name in ["displayName","mail"] or "extension_" in attribute_name:
                group_result=self.msgraph_helper.get_all_groups()
                filtered_groups=[group["displayName"] for group in group_result if attribute_name in group and group[attribute_name] is not None and re.search(discovery_filter[attribute_name],group[attribute_name])]

            user_result = self.msgraph_helper.get_all_member_users()
            if "extensionAttribute" in attribute_name:
                filtered_users = [user["displayName"] for user in user_result if
                                  attribute_name in user["onPremisesExtensionAttributes"] and
                                  user["onPremisesExtensionAttributes"][attribute_name] is not None and re.search(
                                      discovery_filter[attribute_name],
                                      user["onPremisesExtensionAttributes"][attribute_name])]
            else:
                filtered_users= [user["displayName"] for user in user_result if attribute_name in user and user[attribute_name] is not None and re.search(discovery_filter[attribute_name], user[attribute_name])]
            total_mailboxes=len(filtered_users)+len(filtered_groups)

            if int(details["Number of mailboxes discovered"])!=total_mailboxes:
                raise Exception("Number of mailboxes discovered is not matching azure")
            self.log.info("Number of mailboxes discovered is matched with azure")


    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    is_express_config=False,
                                                    app_id=self.tcinputs['azureAppKeyID'],
                                                    dir_id=self.tcinputs['azureTenantName'],
                                                    app_secret=self.tcinputs['azureAppKeySecret'],
                                                    discovery_filter=True,
                                                    discovery_filter_value=self.discovery_filter_value)
            self.app_name = self.office365_obj.get_app_name()
            self.office365_obj.access_office365_app(self.app_name)
            self.verify_discovery_filter_count(discovery_filter=self.discovery_filter_value)
            for discovery_values in self.edit_discovery_filter_value:
                self.admin_console.access_tab(self.office365_obj.constants.CONFIGURATION.value)
                self.office365_obj.__edit_discovery_filter_value(discovery_filter_value=discovery_values)
                self.verify_discovery_filter_count(discovery_filter=discovery_values)

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)