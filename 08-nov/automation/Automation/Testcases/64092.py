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
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_OneDrive_CustomCategories:
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_OneDrive_CustomCategories"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.app_type = None
        self.app_name = None
        self.custom_dict1 = None
        self.custom_dict2 = None
        self.custom_dict3 = None
        self.tenant_user_name = None
        self.tenant_password = None

        self.utils = TestCaseUtils(self)

    '''def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('o365-auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@onedrive{current_timestamp}.com')'''


    def setup(self):
        #self.create_tenant()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        #self.admin_console.login(self.tenant_user_name,
        #                         self.inputJSONnode['commcell']['commcellPassword'])
        self.tenant_user_name = self.tcinputs['tenant_user_name']
        self.tenant_password = self.tcinputs['tenant_password']
        self.admin_console.login(self.tenant_user_name,
                                 self.tenant_password)

        self.service = HubServices.office365
        self.app_type = O365AppTypes.onedrive
        #self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)

        self.navigator = self.admin_console.navigator

        #self.navigator.navigate_to_service_catalogue()
        #self.service_catalogue.start_office365_trial()
        self.navigator.navigate_to_office365()
        self.app_name = self.tcinputs['Name']
        self.custom_dict1 = self.tcinputs['custom_dict1']
        self.custom_dict2 = self.tcinputs['custom_dict2']
        self.custom_dict3 = self.tcinputs['custom_dict3']

        self.log.info("Creating an object for office365 helper")
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)

    def run(self):
        """Main function for test case execution"""
        try:
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'],plan=self.tcinputs['plan'])
            self.app_name = self.office365_obj.get_app_name()
            office365plan = self.tcinputs['office365plan']
            self.office365_obj.add_custom_category(self.custom_dict1, plan=office365plan)
            time.sleep(25)
            users = self.office365_obj.get_total_associated_users_count()
            if int(users) == 2:
                self.log.info("Custom category verified for display name contains and geo location not equal operation")
            else:
                raise Exception("Custom category failed for display name contains and geo location not equal operation")
            self.office365_obj.add_custom_category(self.custom_dict2, plan=office365plan)
            time.sleep(25)
            users = self.office365_obj.get_total_associated_users_count()
            if int(users) == 7:
                self.log.info("Custom category verified for display name regex and geo location equal operation")
            else:
                raise Exception("Custom category failed for display name regex and geo location equal operation")
            self.office365_obj.add_custom_category(self.custom_dict3, plan=office365plan)
            time.sleep(25)
            users = self.office365_obj.get_total_associated_users_count()
            if int(users) == 12:
                self.log.info("Custom category verified for SMTP regex and geo location equal operation")
            else:
                raise Exception("Custom category failed for SMTP regex and geo location equal operation")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        #self.hub_utils.deactivate_tenant(self.tenant_name)
        #self.hub_utils.delete_tenant(self.tenant_name)
