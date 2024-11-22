# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Cases for validating [Laptop] [AdminConsole][AdminMode]: Validation of the of laptop users from Security-->
    users

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Laptop.laptophelper import LaptopHelper
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Components.table import Rtable, Rfilter
from selenium.webdriver.common.by import By

class TestCase(CVTestCase):
    """Test Case for validating [Laptop] [AdminConsole][AdminMode]: User Details Page Validation for owned laptops"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.driver = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "[Laptop] [AdminConsole][AdminMode]: Views validation from laptop listing page"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = True
        self.rtable = None

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']
                                 ["commcellPassword"])
        self.navigator = self.admin_console.navigator
        self.driver = self.browser.driver
        self.rtable = Rtable(self.admin_console)

    def run(self):
        view_new_name = None
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            laptop_helper = LaptopHelper(self)
            view_name = "Automation_View_63565"

            # -------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            From laptop listing page in top right corner we can see gear button to create the views
                            Verify below working as expected
                                1. Able to create view and that view should be visible from laptop listing page as tab
                                2. Edit the view 
                                3 . Reorder the view
                                4. Set the view as default
                                5. Delete the view
                        """, 200)

            # -------------------------------------------------------------------------------------
            self.log.info("Navigating to Protect > Laptops page")
            self.navigator.navigate_to_devices()
            self.admin_console.access_tab("Laptops")

            self.log.info("Attempting to create view and validating view visibility")
            self.rtable.create_view(view_name, rules={"Configured": "No"})
            self.log.info(f"View {view_name} created successfully")

            # test for view check: View has NO configured, so we shouldn't see any configured ones when we filter for it
            # so if laptop count in this view isn't 0, that is a failure
            self.log.info("Checking if view created is visible")
            self.rtable.select_view(view_name)
            self.rtable.apply_filter_over_column(column_name="Configured", filter_term="Yes", criteria=Rfilter.equals)
            configured_in_negative_case = self.rtable.get_total_rows_count()
            if configured_in_negative_case != 0:
                exp = "View is not working properly"
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("Created view is functioning properly")
            self.rtable.clear_column_filter(column_name="Configured", filter_term="Yes")

            self.log.info("Attempting to edit view")
            view_new_name = view_name + '_Edited'
            self.rtable.select_view(view_name)
            self.rtable.edit_view(view_new_name=view_new_name, new_rules={"Configured": "Yes"})
            self.log.info(f"View {view_name} edited successfully to {view_new_name}")

            # test for check: View has YES configured, so we shouldn't see any deconfigured ones when we filter for it
            # so if laptop count in this view isn't 0, that is a failure
            self.log.info("Checking if view edited is visible")
            self.rtable.select_view(view_new_name)
            self.rtable.apply_filter_over_column(column_name="Configured", filter_term="No", criteria=Rfilter.equals)
            configured_in_negative_case = self.rtable.get_total_rows_count()
            if configured_in_negative_case != 0:
                exp = "View is not working properly"
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("Edited view is functioning properly")
            self.rtable.clear_column_filter(column_name="Configured", filter_term="No")

            self.log.info("Setting the view as default")
            self.rtable.select_view(view_new_name)
            self.rtable.edit_view(set_default=True)
            self.rtable.select_view('All')
            self.log.info("Checking default view")

            # test here is to jump onto other tab and come back to this tab, if we see the new view as the current view
            # test result is favourable, otherwise not
            self.admin_console.access_tab("Users")
            self.admin_console.access_tab("Laptops")
            default_view_element_text = self.admin_console.driver.find_element(By.XPATH,
                                    "//button[contains(@class,'MuiTab-root') and @aria-selected='true']").text
            if default_view_element_text != view_new_name:
                exp = "Default view is not working properly"
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("Default view is functioning properly")

            self.log.info("Attempting to reorder the views, viewing the current ordering of views")
            current_views = self.rtable.get_all_tabs()
            self.log.info(f"Current ordering of views: {current_views}")
            self.rtable.reorder_view(view_new_name, 'All')
            check_current_views = self.rtable.get_all_tabs()
            check_current_views.reverse()

            # test: view == rev(rev(view))
            if check_current_views != current_views:
                exp = "Reordering views is not working properly"
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("Reordering views is functioning properly")

            self.log.info("Attempting to delete the view")
            self.rtable.delete_view(view_new_name)
            self.log.info("Checking if view has been deleted")
            current_views = self.rtable.get_all_tabs()
            if view_new_name in current_views:
                exp = "Deleting view is not working properly"
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("Deleting view is functioning properly")

        except Exception as excp:
            self.admin_console.refresh_page()
            self.rtable.delete_view(view_new_name)
            laptop_helper.tc.fail(excp)
            handle_testcase_exception(self, excp)

    def tear_down(self):
        """ Tear down function of this test case """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
