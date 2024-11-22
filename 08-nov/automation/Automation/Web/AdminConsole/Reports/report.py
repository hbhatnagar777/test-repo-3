from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.page_container import PageContainer

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
individual report page of the AdminConsole
"""
from time import sleep
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException
)
from selenium.webdriver import ActionChains

from Web.AdminConsole.Reports.cte import (
    Email,
    RConfigureSchedules
)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import (
    WebAction,
    PageService
)


class Report:
    """Class for Report Page"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self.page_container = PageContainer(admin_console)
        self._admin_console = admin_console
        self.driver = admin_console.driver
        self._admin_console.load_properties(self)
        self.__modal_dialog_obj = RModalDialog(self._admin_console)

    @WebAction()
    def __click_save_as_view(self):
        """clicks "Save as view"""
        save_as_view = self.driver.find_element(By.XPATH,
                                                "//div[contains(@class,'page-action-list')]//button[@aria-label='Save as view']")
        save_as_view.click()

    @WebAction()
    def __click_refresh(self):
        """Clicks refresh"""
        refresh = self.driver.find_element(By.XPATH, "//div[contains(@class,'page-action-list')]//button[contains(., "
                                                     "'Refresh')]")
        refresh.click()

    @WebAction()
    def __set_view_name(self, name):
        """Sets the given view name"""
        view = self.driver.find_element(By.XPATH, "//input[@id='viewName']")
        view.clear()
        view.send_keys(name)

    @WebAction()
    def __set_url(self, url):
        """Sets the given URL"""
        view = self.driver.find_element(By.XPATH, "//input[@id='urlName']")
        view.clear()
        view.send_keys(url)

    @WebAction()
    def __set_as_default(self):
        """Selects the 'Set as Default' Checkbox"""
        view = self.driver.find_element(By.XPATH, "//*[@for='chkSetAsDefault']")
        view.click()

    @WebAction()
    def __click_save(self):
        """Clicks Save button"""
        button = self.driver.find_element(By.XPATH, "//button[contains(.,'Save')]")
        button.click()

    @WebAction()
    def __fetch_current_view(self):
        """Fetches current view"""
        view = self.driver.find_element(By.XPATH, "//a[@id='views-dropdown']")
        return view.text

    @WebAction()
    def __fetch_all_views(self):
        """Fetches all views"""
        objects = self.driver.find_elements(By.XPATH, "//*[@id='1']//ul[@role='menu']/li")
        if len(objects) == 0:
            return []
        return [each.text.strip() for each in objects]

    @WebAction()
    def __click_view_drop_down(self):
        """Clicks the view dropdown"""
        view = self.driver.find_elements(By.XPATH, "//div[contains(@class,'page-action-list')]//button")
        view[0].click()

    @WebAction()
    def __select_view(self, view_name):
        """Selects the view from the dropdown"""
        view = self.driver.find_element(By.XPATH, f"//ul[@role='menu']//li[contains(.,'{view_name}')]")
        view.click()

    @WebAction()
    def __hover_over_the_view(self, view_name):
        """Hovers over the given view"""
        view = self.driver.find_element(By.XPATH, f"//ul[@role='menu']//li[contains(.,'{view_name}')]")
        action_chain = ActionChains(self.driver)
        action = action_chain.move_to_element(view)
        action.perform()

    @WebAction()
    def __click_delete_icon(self):
        """Click delete icon on the given view name"""
        button = self.driver.find_element(By.XPATH, "//div[contains(@class,'page-action-list')]//button["
                                                    "@aria-label='Delete view']")
        button.click()

    @WebAction()
    def __click_delete(self):
        """clicks delete button"""
        self.__click_delete_icon()
        delete_button = self.driver.find_element(By.XPATH, "//*[@id='createViewForm']//button[@aria-label='Delete']")
        delete_button.click()

    @WebAction()
    def __check_for_permission(self):
        """Checks for permission errors"""
        notification = self.driver.find_elements(By.XPATH, "//*[@id='notificationContainer']//p")
        if notification:
            raise CVWebAutomationException(f"{notification[0].text}")

    @WebAction()
    def __click_yes_on_delete_confirmation(self):
        """Click yes on delete confirmation"""
        button = self.driver.find_element(By.XPATH,
                                          "//button[.='Yes' and @data-ng-disabled='!confirmBox']")
        button.click()

    @PageService()
    def save_as_pdf(self):
        """Save as PDF"""
        self.page_container.hover_over_save_as(self._admin_console.props['CustomReport.SaveAs'])
        self.page_container.access_page_action("PDF")

    @PageService()
    def save_as_html(self):
        """Save as HTML"""
        self.page_container.hover_over_save_as(self._admin_console.props['CustomReport.SaveAs'])
        self.page_container.access_page_action("HTML")

    @PageService()
    def save_as_csv(self):
        """Save as CSV"""
        self.page_container.hover_over_save_as(self._admin_console.props['CustomReport.SaveAs'])
        self.page_container.access_page_action("CSV")

    @PageService()
    def to_executive_summary(self, customer_name='Auto_Customer',
                             designation='Auto_Designation', values=None):
        """
        Perform executive summary export operation
        :param customer_name: customer name to fill in file
        :param designation: designation to fill in file
        :param values: list of commcell groups to be selected in the dropdown
        """
        self.page_container.hover_over_save_as(self._admin_console.props['CustomReport.SaveAs'])
        self.page_container.access_page_action("Executive summary")
        rmodal = RModalDialog(self._admin_console)
        rmodal.fill_text_in_field('headName', customer_name)
        rmodal.fill_text_in_field('designation', designation)
        rmodal.select_dropdown_values('clientGroupList', values, case_insensitive=True)
        rmodal.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def access_security(self):
        """Access security of the report"""
        self.page_container.access_page_action_from_dropdown("Security")

    @PageService()
    def edit_report(self):
        """Edit Report"""
        try:
            self.page_container.access_page_action_from_dropdown("Edit")
        except WebDriverException:
            raise CVWebAutomationException("User has no privileges")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.__check_for_permission()

    @PageService()
    def delete_report(self):
        """Delete Report"""
        try:
            self.page_container.access_page_action_from_dropdown("Delete")
        except WebDriverException:
            raise CVWebAutomationException("User has no privileges")
        self.__click_yes_on_delete_confirmation()
        notification = self._admin_console.get_notification()
        if "successfully" not in notification:
            self._admin_console.wait_for_completion()
            raise CVWebAutomationException(notification)
        self._admin_console.wait_for_completion()

    @PageService()
    def save_as_view(self, name, url=None, set_as_default=True):
        """Saves as view

        Args:
            name (str): Name of the view

            url (str):  URL string

                defaults: None.(keeps the url at the time of on clicking 'save as view' intact)

            set_as_default (bool):  Sets as default

                defaults: True

        """
        self.__click_save_as_view()
        self._admin_console.wait_for_completion()
        self.__set_view_name(name)
        if url:
            self.__set_url(url)
        if set_as_default:
            self.__set_as_default()
        self.__click_save()
        self._admin_console.wait_for_completion()

    @PageService()
    def schedule(self):
        """Schedules the report"""
        self.page_container.access_page_action_from_dropdown("Schedule")
        return RConfigureSchedules(self._admin_console)

    @PageService()
    def email(self):
        """Emails the report"""
        self.page_container.access_page_action_from_dropdown("Email")
        return Email(self._admin_console)

    @PageService()
    def refresh(self):
        """Refreshes the report"""
        self.__click_refresh()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_current_view(self):
        """Gets the name of the view which is set as default"""
        return self.__fetch_current_view()

    @PageService()
    def get_all_views(self):
        """Returns a list of views available for the report"""
        try:
            self.__click_view_drop_down()
            views = self.__fetch_all_views()
            self._admin_console.click_on_base_body()
        except NoSuchElementException:
            return []
        return views

    @PageService()
    def delete_view(self, name):
        """Deletes the given view

        Args:
            name (str): Name of the view to be deleted

        """
        self.__click_view_drop_down()
        self.__select_view(name)
        self._admin_console.wait_for_completion()
        self.__click_delete()

    @WebAction()
    def _get_all_reports_objects(self):
        """Get all the reports objects """
        return self.driver.find_elements(By.XPATH, "//a[contains (@class,'report-name-link')]")

    @PageService()
    def get_all_reports(self):
        """
        Get all the reports with its URLs.
        Returns:
            list: dictionary of report details with name and href
        """
        _report_names = []
        reports = []
        for each_report_obj in self._get_all_reports_objects():
            if str(each_report_obj.text) not in _report_names and each_report_obj.text != '':
                reports.append(
                    {
                        'name': str(each_report_obj.text),
                        'href': each_report_obj.get_attribute('href')
                    }
                )
                _report_names.append(each_report_obj.text)
        return reports

    @WebAction()
    def _get_no_data_error(self):
        """ Get chart error if exists"""
        chart_error_classes = ['chart-no-data', 'chartErrorMessage', 'noDataErrorMsg',
                               'ngLabel', 'noChartDiv', 'k-grid-norecords']
        for each_class in chart_error_classes:
            chart_error_message = self.driver.find_elements(By.CLASS_NAME, each_class)
            if chart_error_message:
                for each_obj in chart_error_message:
                    if each_obj.text:
                        return each_obj.text

    @WebAction()
    def _get_report_title(self):
        """ Check if report page title exist"""
        xpath = "//div[@class='rep-title-div']"
        page_title = self.driver.find_elements(By.XPATH, xpath)
        if page_title and page_title[0].text:
            return page_title[0].text
        return ''

    @PageService()
    def is_page_blank(self):
        """Check if Metrics report page is blank"""
        if not self._get_report_title():
            return True
        return False

    @PageService()
    def is_no_data_error_exists(self):
        """ Check if any chart error exists """
        if self._get_no_data_error() is not None:
            return True
        return False

    @PageService()
    def verify_page_load(self, can_be_empty=False):
        """Verify page is loading without any errors"""

        self._admin_console.check_error_message(raise_error=True)

        if self.is_no_data_error_exists() and not can_be_empty:
            raise CVWebAutomationException("Page is not having data in link %s" %
                                           self.driver.current_url)
        if self.is_page_blank():
            raise CVWebAutomationException("Page is blank in link %s" %
                                           self.driver.current_url)

    @WebAction()
    def _get_export_objs(self):
        """
        Get all export objects
        """
        return self.driver.find_elements(By.XPATH, "//ul[contains(@class,'MuiMenu-list') and @tabindex=-1]//li")

    @PageService()
    def _get_available_export_types(self):
        """
        Function to get the available export options for a report
        :returns list of export types available as strings
        """
        export_types = [str(export_type.text) for export_type in self._get_export_objs()
                        if export_type.text != ""]
        self._admin_console.click_on_base_body()  # to close action menu
        return export_types

    @PageService()
    def get_available_export_types(self):
        """
        gives all export types available for report.
        :return: list of export options
        """
        self.page_container.hover_over_save_as(self._admin_console.props['CustomReport.SaveAs'])
        return self._get_available_export_types()

    @PageService()
    def update_report_settings(self):
        """
        Updates the report's settings
        """
        self.page_container.access_page_action('Update report settings')
        sleep(3)

    @PageService()
    def cancel_report_update(self):
        """
        Cancels the report update
        """
        self.page_container.access_page_action('Go back')
        sleep(3)

