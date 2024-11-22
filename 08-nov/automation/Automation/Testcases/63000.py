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
        self.name = "Additional Settings - Edit CommCell settings"
        self.tcinputs = {
            "PredefinedIntKey": None,
            "PredefinedIntKeyNewValue": None,
            "PredefinedBooleanKey": None,
            "PredefinedBooleanKeyNewValue": None,
            "CustomStringKey": None,
            "CustomStringKeyNewValue": None,
            "CustomStringNewValueType": None,
            "CustomStringKeyNewCategory": None,
            "CustomBooleanKey": None,
            "CustomBooleanKeyNewValue": None,
            "CustomBooleanNewValueType": None,
            "CustomBooleanKeyNewCategory": None
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

           Testcase 62999 must be executed before running this testcase so that he keys to be edited are already present

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

            # Edit Pre-defined Integer Commcell key
            self.log.info("Starting to edit the first Pre-defined Commcell key")
            self.settings_helper_obj.edit_predefined_commcell_key(column='Name',
                                                                  key_name=self.tcinputs['PredefinedIntKey'],
                                                                  key_value=self.tcinputs['PredefinedIntKeyNewValue'],
                                                                  key_comment="Edited by automation 63000",
                                                                  key_isBooleanKey=False)
            self.log.info("Edited the first Pre-defined Commcell key successfully.")

            # Edit Pre-defined Boolean Commcell key
            self.log.info("Starting to edit the second Pre-defined Commcell key")
            self.settings_helper_obj.edit_predefined_commcell_key(column='Name',
                                                                  key_name=self.tcinputs['PredefinedBooleanKey'],
                                                                  key_value=self.tcinputs['PredefinedBooleanKeyNewValue'],
                                                                  key_comment="Edited by automation 63000",
                                                                  key_isBooleanKey=True)
            self.log.info("Edited the second Pre-defined Commcell key successfully.")

            # Edit Custom String Commcell key
            self.log.info("Starting to edit the first Custom Commcell key")
            self.settings_helper_obj.edit_custom_commcell_key(column='Name',
                                                              key_name=self.tcinputs['CustomStringKey'],
                                                              key_value=self.tcinputs['CustomStringKeyNewValue'],
                                                              key_comment="Edited by automation 63000",
                                                              key_valueType=self.tcinputs['CustomStringNewValueType'],
                                                              key_category=self.tcinputs['CustomStringKeyNewCategory'])

            self.log.info("Edited the first Custom Commcell key successfully.")

            self.log.info("Testcase PASSED.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
