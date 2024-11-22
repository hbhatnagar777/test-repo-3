# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AD.ad import ADPage, ADClientsPage
from Web.AdminConsole.Hub.constants import HubServices, ADTypes
from Application.AD import adpowershell_helper
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic AD Multi-attribute acceptance Test:
    Basic Validation for Metallic AD Multi-attribute restore
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_AD_Multi_attribute_Basic_Acceptance"
        self.browser = None
        self.adminconsole = None
        self.navigator = None
        self.service = None
        self.app_type = None
        self.utils = TestCaseUtils(self)
        self.domain = None
        self.adpage = None
        self.adclientspage = None
        self.subclient = None
        self.client_name = None
        self.attributes = None
        self.ad_ps_helper = None
        self.server = None
        self.user = None
        self.username = None
        self.values = None
        self.modified_values = None

    @TestStep()
    def perform_backup(self, backuptype):
        """Performs backup for the client
        Args:
            backuptype(str) : backup type
        """
        self.log.info(f"Navigating to active directory")
        self.navigator.navigate_to_activedirectory()
        self.log.info(f"Backing up the GPO for the subclient")
        self.adclientspage.select_client(self.client)
        self.adminconsole.wait_for_completion()
        self.adpage.backup(backuptype=backuptype)
        self.log.info(f"{backuptype} Backup is completed")

    @TestStep()
    def perform_restore(self):
        """Performs restore for the AD client"""
        self.log.info(f"Navigating to active directory")
        self.navigator.navigate_to_activedirectory()
        self.adclientspage.switch_to_app()
        self.adclientspage.select_client(self.client)
        self.log.info("Starting to restore the GPO")
        self.adpage.restore(entity_names=self.username, attributes=self.attributes)
        self.log.info("Restore completed successfully")

    @TestStep()
    def set_attributes_values(self, values=None):
        """Sets the attribute value of a user
        Args:
            values(list) : Values of the attributes to be set
        """
        for attribute in self.attributes:
            self.ad_ps_helper.attribute_operations(entity_name=self.user,
                                                   attribute=attribute, op_type="SET_ATTRIBUTE",
                                                   value=values[self.attributes.index(attribute)] if values else None)

    @TestStep()
    def get_attributes_values(self, attribute):
        """Gets the attribute value of a user
        Args:
            attribute(list) : Attributes of the user to be fetched
        """
        result = self.ad_ps_helper.attribute_operations(entity_name=self.user,
                                                        attribute=attribute,
                                                        op_type="GET_ATTRIBUTE", value=None)
        return result

    @TestStep()
    def attribute_restore_validation(self):
        """Validates the multi-attribute restore"""
        for attribute in self.attributes:
            fetched_value = self.get_attributes_values(attribute)
            if fetched_value != self.values[self.attributes.index(attribute)]:
                raise Exception(f'Attribute {attribute} is not restored correctly.')
        self.log.info("Multi-attribute test case verified successfully.")

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.domain = self.tcinputs['Domain']
        self.browser.open()
        self.log.info("Opening the browser")
        username = self.inputJSONnode['commcell']['commcellUsername']
        password = self.inputJSONnode['commcell']['commcellPassword']
        self.adminconsole = AdminConsole(self.browser,
                                         self.inputJSONnode['commcell']['webconsoleHostname'])
        self.adminconsole.login(username, password)
        self.log.info("Logging in to Command Center")
        self.navigator = self.adminconsole.navigator
        self.adpage = ADPage(self.adminconsole, self.commcell)
        self.adclientspage = ADClientsPage(self.adminconsole)
        self.service = HubServices.ad
        self.app_type = ADTypes.ad
        self.client = self.tcinputs['ClientName']
        self.attributes = self.tcinputs['Attributes'].split(",")
        self.values = self.tcinputs['Values'].split(",")
        self.modified_values = self.tcinputs['ModifiedValues'].split(",")
        self.ad_ps_helper = adpowershell_helper.ADPowerShell(self.adpage, self.server,
                                                             ad_username=username, ad_password=password)
        self.user = self.tcinputs['UserIdentity']
        self.username = self.tcinputs['Username']

    def run(self):
        """Main function for test case execution"""
        try:
            self.set_attributes_values(self.values)

            self.perform_backup("Incremental")

            self.set_attributes_values(self.modified_values)

            self.perform_restore()

            self.attribute_restore_validation()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Tear down process")
        if self.status == constants.PASSED:
            self.log.info("Testcase completed successfully")
            self.log.info("Modifying values for next run")
            self.set_attributes_values()
        else:
            self.log.info("Testcase failed")
        AdminConsole.logout_silently(self.adminconsole)
        Browser.close_silently(self.browser)
