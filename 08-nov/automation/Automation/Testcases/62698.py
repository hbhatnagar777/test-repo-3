# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    run()                               --  Run function of this test case

    validate_radio_card()               --  Test step to validate if radio card can be clicked

    validate_fill_input()               --  Test step to validate if we can fill input

    validate_next()                     --  Test step to validate if we can click on next button

    validate_click_button()             --  Validate if we can click buttons

    validate_click_icon_button()        --  Validate if we can click on icon buttons

    validate_toggle()                   --  Test step to validate toggle related action

    validate_radio_button()             --  Test step to validate if radio button can be clicked

    validate_fill_input_by_id()         --  Validate if we can fill input using ID

    validate_cancel_button()            --  Validate clicking cancel button
"""


from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Components.panel import RDropDown
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import RModalDialog
import time

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
        self.name = "Integration of wizard component in command center"
        self.navigator = None
        self.config = get_config()
        self.time_string = str(time.time()).split(".")[0]
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator = self.admin_console.navigator
        self.rtable = Rtable(self.admin_console)
        self.wizard = Wizard(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.dropdown = RDropDown(self.admin_console)

    @test_step
    def validate_radio_card(self):
        """Test step to validate if radio card can be clicked"""
        self.wizard.select_radio_card("Use existing base plan")
        self.admin_console.check_if_entity_exists("xpath", "//*[@id='basePlanDropdown-chip-label']")

        self.wizard.select_radio_card("Create a new plan")

    @test_step
    def validate_fill_input(self):
        """Test step to validate if we can fill input"""
        text_input = "TestPlan" + self.time_string
        label = "Plan name"
        self.wizard.fill_text_in_field(label=label, text=text_input)

        if self.wizard.get_input_data(label=label) != text_input:
            raise CVTestStepFailure("The input filled and actual value doesn't match!")

    @test_step
    def validate_next(self):
        """Test step to validate if we can click on next button"""
        old_step = self.wizard.get_active_step()
        self.wizard.click_next()

        new_step = self.wizard.get_active_step()

        if old_step == new_step:
            raise CVTestStepFailure("The next button wasn't clicked successfully")

    @test_step
    def validate_click_button(self):
        """Validate if we can click buttons"""
        id = "storageDropdown"
        self.wizard.click_button("Add copy")
        dd_values = self.dropdown.get_values_of_drop_down(id)

        self.wizard.select_drop_down_values(values=[dd_values[0]], id=id)
        self.dialog.click_submit()

    @test_step
    def validate_click_icon_button(self):
        """Validate if we can click on icon buttons"""
        self.wizard.click_icon_button("Run incremental every 1 day(s) at 9:00 PM", "Edit")

        self.dialog.click_cancel()

    @test_step
    def validate_toggle(self):
        """Test step to validate toggle related action"""
        label = "Multi-region"
        if not self.wizard.is_toggle_enabled(label):
            self.wizard.enable_toggle(label)
            if not self.wizard.is_toggle_enabled(label):
                raise CVTestStepFailure(f"The toggle {label} wasn't enabled")

            self.wizard.disable_toggle(label)
        else:
            self.wizard.disable_toggle(label)
            if self.wizard.is_toggle_enabled(label):
                raise CVTestStepFailure(f"The toggle {label} wasn't disabled")

            self.wizard.enable_toggle(label)

    @test_step
    def validate_radio_button(self):
        """Test step to validate if radio button can be clicked"""
        self.wizard.select_radio_button(label="Number of snap recovery points")

        self.wizard.select_radio_button(id="RETENTION_PERIOD")

    @test_step
    def validate_fill_input_by_id(self):
        """Validate if we can fill input using ID"""
        value = f"TestPlan{self.time_string}"
        id = "planName"
        self.wizard.fill_text_in_field(id=id, text=value)

        if self.wizard.get_input_data(id=id) != value:
            raise CVTestStepFailure("The input filled and actual value doesn't match!")

    @test_step
    def validate_cancel_button(self):
        """Validate clicking cancel button"""
        self.wizard.click_cancel()
        self.dialog.click_submit()

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_plan()
            self.rtable.access_menu_from_dropdown("Server backup", "Create plan")

            self.validate_radio_card()

            self.validate_fill_input()

            self.validate_fill_input_by_id()

            self.validate_next()

            self.validate_click_button()

            self.validate_toggle()

            self.validate_next()

            self.validate_click_icon_button()

            self.validate_cancel_button()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.browser.close()
