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
    __init__()                          --  initialize TestCase class
    setup()                             --  setup function of this test case
    run()                               --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.AdditionalSettings import AdditionalSettings
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.AdditionalSettingsHelper import AdditionalSettingsHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Additional Settings - Add CommCell settings"
        self.tcinputs = {
            "PredefinedIntKey": None,
            "PredefinedIntKeyValue": None,
            "PredefinedBooleanKey": None,
            "PredefinedBooleanKeyValue": None,
            "CustomStringKey": None,
            "CustomStringKeyValue": None,
            "CustomStringValueType": None,
            "CustomStringKeyCategory": None,
            "CustomBooleanKey": None,
            "CustomBooleanKeyValue": None,
            "CustomBooleanValueType": None,
            "CustomBooleanKeyCategory": None
        }
        self.index_server_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.plan_name = None
        self.commcell_password = None
        self.data_source_name = None
        self.project_name = None
        self.inventory_name = None
        self.classifier_name = None
        self.ca_helper = None
        self.additional_settings = None
        self.rtable = None

    def setup(self):
        """Setup function of this test case

           The keys to be added in this testcase must not be already present in the setup.

        """
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.commcell.commcell_username,
                                          password=self.commcell_password)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.log.info('Logged in through web automation')
        self.additional_settings = AdditionalSettings(self.admin_console)
        self.rtable = Rtable(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:
            self.settings_helper_obj = AdditionalSettingsHelper(self.admin_console)
            self.admin_console.navigator.navigate_to_additional_settings()

            # Add Pre-defined Integer Commcell key
            self.log.info("Starting to add the first Pre-defined Commcell key")
            self.settings_helper_obj.add_predefined_commcell_key(column='Name',
                                                                 key_name=self.tcinputs['PredefinedIntKey'],
                                                                 key_value=self.tcinputs['PredefinedIntKeyValue'],
                                                                 key_comment="Added by automation 62999",
                                                                 key_isBooleanKey=False)
            self.log.info("Added the first Pre-defined Commcell key successfully")

            # Add Pre-defined Boolean Commcell key
            self.log.info("Starting to the second Pre-defined Commcell key")
            self.settings_helper_obj.add_predefined_commcell_key(column='Name',
                                                                 key_name=self.tcinputs['PredefinedBooleanKey'],
                                                                 key_value=self.tcinputs['PredefinedBooleanKeyValue'],
                                                                 key_comment="Added by automation 62999",
                                                                 key_isBooleanKey=True)
            self.log.info("Added the second Pre-defined Commcell key successfully")

            # Add Custom String Commcell key
            self.log.info("Starting to add the first Custom  Commcell key")
            self.settings_helper_obj.add_custom_commcell_key(column='Name',
                                                             key_name=self.tcinputs['CustomStringKey'],
                                                             key_value=self.tcinputs['CustomStringKeyValue'],
                                                             key_comment="Added by automation 62999",
                                                             key_valueType=self.tcinputs['CustomStringValueType'],
                                                             key_category=self.tcinputs['CustomStringKeyCategory'])
            self.log.info("Added the first Custom  Commcell key successfully")

            # Add Custom Boolean Commcell key
            self.log.info("Starting to add the second Custom Commcell key")
            self.settings_helper_obj.add_custom_commcell_key(column='Name',
                                                             key_name=self.tcinputs['CustomBooleanKey'],
                                                             key_value=self.tcinputs['CustomBooleanKeyValue'],
                                                             key_comment="Added by automation 62999",
                                                             key_valueType=self.tcinputs['CustomBooleanValueType'],
                                                             key_category=self.tcinputs['CustomBooleanKeyCategory'])
            self.log.info("Added the second Custom Commcell key successfully")

            self.log.info("Testcase PASSED.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
