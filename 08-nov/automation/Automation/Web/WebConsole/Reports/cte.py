from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
File for all CTE operations like export, schedule, alert and Security operations
any common functionality across Reports APP can be added here.

Security:

    _access_security_frame  --  Access security frame.

    _get_associated_users   --  Get associate users.

    _search_user            --  Enters the username in the security-search-user field.

    _move_to_selected_list  --   Move to selected list.

    _move_to_available_list --   Move to available list.

    _click_available_user   --  Clicks the user from the list of available users.

    _click_selected_user    --  Clicks the user from the list of selected users.

    _click_ok               --  Clicks Ok button to save changes.

    _switch_back_frame      --  Switch back to default frame.

    associate_user          --  associate user

    deassociate_user        --  de-associate user

    get_associated_users    --  Gets the list of user/user groups already associated.

    _is_user_associated     --  Verify if the user is associated.

    add_user                --  Add the user to the selected list.

    remove_user             --  Removes the user from the selected list

    close()                 --  Closes the security panel

"""
from enum import Enum
from time import sleep, time

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from AutomationUtils import logger, config

from Web.WebConsole.webconsole import WebConsole
from Web.Common.exceptions import CVTimeOutException, CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)

_CONFIG = config.get_config()


class ExportHandler:
    """
    ExportHandler has the interfaces to do export operations on Reports and operate on
    export panels

    export_as_built_guide() -- export the as built guide report

    do_export (file_format) -- export report with file format given in input

    get_available_export_types() -- gives all export types available
    """
    class ExportConstants:
        """
        Export constants
        """
        AS_BUILT_GUIDE_DATSOURCE_DATABASE = 'dataBase'
        AS_BUILT_GUIDE_DATSOURCE_XML = 'xml'

    def __init__(self, webconsole: WebConsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction()
    def _click_file_menu(self):
        """
        click on file menu
        """
        self._driver.find_element(By.XPATH, ".//*[@id='reportButton']").click()

    @WebAction()
    def _mouse_hover(self, element):
        """
            Performs an action where the mouse hovers over the specified web element.
           Arg1:
            web element that you would like to hover over.
        """
        hover = ActionChains(self._driver).move_to_element(element)
        hover.perform()

    @WebAction()
    def _mouse_hover_save_as(self):
        """
        Mouse hover on save as
        """
        save_as = self._driver.find_element(By.ID, "exportRightArrow")
        hover = ActionChains(self._driver).move_to_element(save_as)
        hover.perform()

    @WebAction()
    def _click_pdf(self):
        """
        click pdf
        """
        self._driver.find_element(By.ID, 'exportpdf').click()

    @WebAction()
    def _click_csv(self):
        """
        Click csv
        """
        self._driver.find_element(By.ID, 'exportCsv').click()

    @WebAction()
    def _click_html(self):
        """
        click html
        :return:
        """
        self._driver.find_element(By.ID, 'exporthtml').click()

    @WebAction()
    def _click_apac_qbr_ppt(self):
        """
        click ppt
        """
        self._driver.find_element(By.ID, 'export-APAC-QBR').click()

    @WebAction()
    def _click_esp_monthly(self):
        """
        click QBR monthly
        """
        self._driver.find_element(By.ID, 'monthly').click()

    @WebAction()
    def _click_rms_ppt(self):
        """
        click ppt
        """
        self._driver.find_element(By.ID, 'export-RMS-PPT').click()

    @WebAction()
    def _click_emea_qbr_doc(self):
        """
        click on export of qbr doc
        """
        self._driver.find_element(By.ID, 'export-EMEA-QBR').click()

    @WebAction()
    def _click_word(self):
        """
        click word
        """
        self._driver.find_element(By.ID, 'exportWord').click()

    @WebAction()
    def _click_executive_summary(self):
        """
        Click executive summary export
        """
        self._driver.find_element(By.ID, 'exportExecutiveSummary').click()

    @WebAction()
    def _mouse_hover_ppt(self):
        """
        Mouse hover ppt
        """
        ppt_object = self._driver.find_element(By.ID, 'exportPpt')
        self._mouse_hover(ppt_object)

    @WebAction()
    def _click_value_assesmt_ppt(self):
        """
        Click on value assessment ppt
        """
        self._driver.find_element(By.ID, 'exportValAssessPpt').click()

    @WebAction()
    def _click_osos_ppt(self):
        """
        Click on osos ppt
        """
        self._driver.find_element(By.ID, 'export-OSOS-PPT').click()

    @WebAction()
    def _click_health_ppt(self):
        """
        Click on health ppt
        """
        self._driver.find_element(By.ID, 'exportHealthPpt').click()

    @WebAction()
    def _set_customer_name(self, customer_name):
        """
        Set customer name
        :param customer_name:Specify the customer name
        """
        self._driver.find_element(By.ID, 'name').send_keys(customer_name)

    @WebAction()
    def _set_dc_location(self, data_center_location):
        """
        Set data centre location
        :param data_center_location:specify the data centre location
        """
        self._driver.find_element(By.ID, 'location').send_keys(data_center_location)

    @WebAction()
    def _click_proceed(self):
        """
        Click on proceed
        """
        self._driver.find_element(By.XPATH, "//button[text()='Proceed']").click()

    @WebAction()
    def _click_submit(self):
        """
        Click on submit
        """
        self._driver.find_element(By.ID, 'proceedButton').click()

    @PageService()
    def _submit_health(self, customer_name, data_center_location):
        """
        Submit health report word export
        Args:
            customer_name:customer name
            data_center_location: data center location
        """
        self._set_customer_name(customer_name)
        self._set_dc_location(data_center_location)
        self._click_proceed()

    @WebAction()
    def _switch_to_executive_frame(self):
        """
        Switch to executive summary frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _set_designation(self, designation):
        """
        Set destination
        """
        self._driver.find_element(By.ID, 'designation').send_keys(designation)

    @PageService()
    def _submit_exec_summary(self, customer_name, designation):
        """
        Submit executive summary report
        :param customer_name: Specify the customer name
        :param designation: Set the description
        """
        self._switch_to_executive_frame()
        self._set_customer_name(customer_name)
        self._set_designation(designation)
        self._click_submit()
        self._driver.switch_to.window(self._driver.current_window_handle)

    @WebAction()
    def _get_export_objs(self):
        """
        Get all export objects
        """
        return self._driver.find_elements(By.XPATH, "//ul[@id = 'exportMenu']//span[2]")

    @PageService()
    def _get_available_export_types(self):
        """
        Function to get the available export options for a report
        :returns list of export types available as strings
        """
        export_types = [str(export_type.text) for export_type in self._get_export_objs()
                        if export_type.text != ""]
        self._click_file_menu()  # to close the file menu
        return export_types

    @WebAction()
    def _click_on_as_built_guide(self):
        """
        Click on as built guide
        """
        self._driver.find_element(By.ID, "exportASBuild").click()

    @WebAction()
    def _click_on_net_backup_ppt(self):
        """
        Click on net backup ppt
        """
        self._driver.find_element(By.ID, "exportNetBackupPPT").click()

    @PageService()
    def _access_export(self):
        """
        Access export
        """
        self._click_file_menu()
        self._mouse_hover_save_as()

    @WebAction()
    def _access_built_guide_frame(self):
        """
        Switch to as built guide frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _select_datasource(self, database_source):
        """
        Select data source in as built guide export
        :param database_source: Specify the datasource name
        """
        self._driver.find_element(By.ID, database_source).click()

    @WebAction()
    def _access_help_menu(self):
        """
        Access help menu
        """
        self._driver.find_element(By.ID, 'helpText').click()

    @PageService()
    def _submit_as_built_guide_export(self, customer, data_source_type):
        """
        Submit as built guide export
        :param data_source_type: Database/xml select from Constants class
        """
        try:
            self._access_built_guide_frame()
            self._set_customer_name(customer)
            self._select_datasource(data_source_type)
            self._click_submit()
        finally:
            self._driver.switch_to.default_content()

    @PageService()
    def export_as_built_guide(self, customer='Automation',
                              data_source_type=ExportConstants.AS_BUILT_GUIDE_DATSOURCE_DATABASE):
        """
        Exports As built guide report available in worldwide report,
        page should be in ww report page before accessing this.
        :param customer: customer name to add in built guide report
        :param data_source_type: Database or XML select from Constants class
        """
        if data_source_type not in (
                ExportHandler.ExportConstants.AS_BUILT_GUIDE_DATSOURCE_DATABASE,
                ExportHandler.ExportConstants.AS_BUILT_GUIDE_DATSOURCE_XML
        ):
            raise ValueError(
                "Invalid data source supplied (%s') expected is either [%s] or [%s]",
                data_source_type, ExportHandler.ExportConstants.AS_BUILT_GUIDE_DATSOURCE_DATABASE,
                ExportHandler.ExportConstants.AS_BUILT_GUIDE_DATSOURCE_XML
            )
        self._access_help_menu()
        sleep(2)
        self._click_on_as_built_guide()
        sleep(2)
        self._submit_as_built_guide_export(customer, data_source_type)
        self._webconsole.wait_till_load_complete(timeout=120)

    @PageService()
    def export_as_net_backup_ppt(self):
        """
        From worldwide report export as net backup ppt
        """
        self._access_help_menu()
        sleep(2)
        self._click_on_net_backup_ppt()
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _set_support_account_manager(self, name):
        """
        Set support account manager name
        :param name: Specify support account manager name
        """
        self._driver.find_element(By.ID, 'support-account-manager').send_keys(name)


    @WebAction()
    def _set_technical_account_manager(self, name):
        """
        Set technical account manager name
        :param name: specify the name
        """
        self._driver.find_element(By.ID, 'technical-account-manager').send_keys(name)

    @WebAction(delay=5)
    def _switch_qbr_frame(self):
        """
        switch to QBR frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _click_submit_qbr(self):
        """
        Click submit button
        """
        self._driver.find_element(By.ID, 'qbrSubmitButton').click()

    def _submit_qbr_ppt(self, support_account_manager, technical_account_manager):
        """
        Submit QBR ppt
        Args:
            support_account_manager: specify the support account manager name
            technical_account_manager: specify the technical account manager name
        """
        self._switch_qbr_frame()
        self._set_support_account_manager(support_account_manager)
        self._set_technical_account_manager(technical_account_manager)
        self._click_submit_qbr()
        self._driver.switch_to.window(self._driver.current_window_handle)

    def _submit_qbr_monthly_ppt(self, support_account_manager):
        """
        Submit QBR monthly ppt
        Args:
            support_account_manager: specify the support account manager name
        """
        self._switch_qbr_frame()
        self._click_esp_monthly()
        self._set_support_account_manager(support_account_manager)
        self._click_submit_qbr()
        self._driver.switch_to.window(self._driver.current_window_handle)

    @PageService()
    def to_pdf(self):
        """
        Perform pdf export operation
        """
        self._webconsole.wait_till_load_complete()
        self._access_export()
        self._click_pdf()
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _wait_for_progressbar_to_complete(self):
        """Wait till progressbar disappears"""
        xpath = "//div[@id='exportStatusBox' and @style='display: block;']"
        try:
            # wait for progressbar to appear
            WebDriverWait(self._driver, 15).until(EC.presence_of_element_located((By.XPATH,
                                                                                 xpath)))
            # wait for progressbar to disapprear
            WebDriverWait(self._driver, 300).until(EC.invisibility_of_element_located((By.XPATH,
                                                                                       xpath)))
        except TimeoutException:
            # In case there is no progressbar, there should not be any exception
            pass

    @PageService()
    def to_csv(self):
        """
        Perform csv export operation
        """
        self._webconsole.wait_till_load_complete()
        self._access_export()
        self._click_csv()
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_html(self):
        """
        Perform html export operation
        """
        self._webconsole.wait_till_load_complete()
        self._access_export()
        self._click_html()
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_qbr_ppt(self, support_account_manager="support manager",
                   technical_account_manager="technical manager"):
        """
        Perform QBR ppt export operation
        """
        self._access_export()
        self._click_apac_qbr_ppt()
        self._submit_qbr_ppt(support_account_manager, technical_account_manager)
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_qbr_monthly_ppt(self, support_account_manager="support manager"):
        """
        Perform QBR ppt export operation
        """
        self._access_export()
        self._click_apac_qbr_ppt()
        self._submit_qbr_monthly_ppt(support_account_manager)
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_emea_qbr_doc(self,
                        support_account_manager="support manager",
                        technical_account_manager="technical manager"
                        ):
        """
        Perform EMEA qbr doc export
        Args:
            support_account_manager             (String)   --   Support manager name
            technical_account_manager           (String)   --   Technical manager
        """
        self._access_export()
        self._click_emea_qbr_doc()
        self._submit_qbr_ppt(support_account_manager, technical_account_manager)
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_rms_ppt(self):
        """
        Perform RMS ppt export operation
        """
        self._access_export()
        self._click_rms_ppt()
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_value_assesment_ppt(self):
        """
        Perform value assessment report ppt export operation
        """
        self._access_export()
        self._mouse_hover_ppt()
        self._click_value_assesmt_ppt()
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_health_word(self, customer_name='Auto_Customer',
                       data_center_location='Auto_data_center'):
        """
        Perform health word export operation
        :param customer_name: customer name to fill in file
        :param data_center_location: DC location to fill in file
        """
        self._access_export()
        self._click_word()
        sleep(5)
        self._submit_health(customer_name, data_center_location)
        sleep(2)
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_health_ppt(self, customer_name='Auto_Customer',
                      data_center_location='Auto_data_center'):
        """
        Perform health ppt export operation
        :param customer_name: customer name to fill in file
        :param data_center_location: DC location to fill in file
        """
        self._access_export()
        self._mouse_hover_ppt()
        self._click_health_ppt()
        self._submit_health(customer_name, data_center_location)
        sleep(5)
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_executive_summary(self, customer_name='Auto_Customer',
                             data_center_location='Auto_data_center'):
        """
        Perform executive summary export operation
        :param customer_name: customer name to fill in file
        :param data_center_location: DC location to fill in file
        """
        self._access_export()
        self._click_executive_summary()
        sleep(10)
        self._submit_exec_summary(customer_name, data_center_location)
        sleep(2)
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def to_osos_ppt(self):
        """
        Perform osos ppt export operation
        """
        self._access_export()
        self._click_osos_ppt()
        self._wait_for_progressbar_to_complete()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_available_export_types(self):
        """
        gives all export types available for report.
        :return: list of export options
        """
        self._access_export()
        return self._get_available_export_types()


class EmailNow:
    """
    EmailNow has the interfaces to work on Email now panel and do email operations on Reports

    email_now(file_format, recipient_mail_id) -- emails the report with given format
                                                 to recipient mail given in input
    """
    class Format:
        """
        Format is a constant on different type of file formats in Email now panel on reports
        """
        PDF = "PDF"
        HTML = "HTML"
        CSV = "CSV"
        INLINE = "INLINE"

    def __init__(self, webconsole: WebConsole):
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self.format = EmailNow.Format

    @WebAction()
    def _switch_frame(self):
        """
        Switch to email frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def __select_format(self, format_text):
        """
        selects format
        Args:
            format_text: format text to select
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text(format_text)

    @WebAction()
    def _set_recipient(self, recipient_mail_id):
        """
        recipient_name is a comma seperated value for multiple recipients
        """
        self._driver.find_element(By.ID, "emails").clear()
        self._driver.find_element(By.ID, "emails").send_keys(recipient_mail_id)

    @WebAction()
    def _access_email_now_frame(self):
        """
        Switch email frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _click_ok(self):
        """
        Click ok
        """
        self._driver.find_element(By.ID, "okButton").click()

    @PageService()
    def _choose_format(self, file_format):
        """
        Choose file format
        """
        if file_format == self.format.PDF:
            self.__select_format("PDF")
        elif file_format == self.Format.HTML:
            self.__select_format("HTML")
        elif file_format == self.format.CSV:
            self.__select_format("CSV")
        elif file_format == self.format.INLINE:
            self.__select_format("Email body")

    @PageService()
    def email_now(self, file_format, recipient_mail_id):
        """
        emails the report
        :param file_format: fomat of report to be emailed
                            use self.format to know the available formats supported
        :param recipient_mail_id: recipient mail id
        """
        self._switch_frame()
        self._set_recipient(recipient_mail_id)
        sleep(2)
        self._choose_format(file_format)
        sleep(3)
        self._click_ok()
        sleep(2)
        self._driver.switch_to.window(self._driver.current_window_handle)

    def get_job_id(self, time_out=150):
        """
        Get job id of email job from notification
        Returns:(string) job id
        """
        end_time = time() + time_out
        while time() < end_time:
            notifications = self._webconsole.get_all_unread_notifications()
            if not notifications:
                continue
            if "Job Id" not in notifications[0]:
                raise CVWebAutomationException("Job ID is not found in email notification, "
                                               "Notification:[%s]", notifications[0])
            job_id = (notifications[0].split('Job Id ')[1]).split(')')[0]
            return job_id
        raise CVTimeOutException(time_out, "failure to get job id from email notification")


class ConfigureSchedules:
    """
    ConfigureSchedules has the interfaces to schedule reports and
    to operate on Reports schedule panels

    create_schedule(schedule_name, email_recipient, file_format, frequency) -- creates a schedule
                    with email notification with given frequency type of default time.
    set_network_path(network_path, user_name, password) -- sets the n/w output path
    set_time(hour, minute, ampm='AM') -- sets time for schedule
    select_format(file_type) -- selects format of file for schedule
    set_recipient(recipient) -- sets recipient mail id
    close() -- closes schedule panel
    save() -- saves schedule
    """
    class Frequency:
        """
        Frequency is a constant on different frequency types available on Reports schedule panel
        """
        DAILY = 'Daily'
        WEEKLY = "Weekly"
        Monthly = "Monthly"

    class Format:
        """
        Format is a constant on different type of format available on schedule panel of reports
        """
        PDF = "PDF"
        HTML = "HTML"
        CSV = "CSV"
        EXECUTIVE_SUMMARY = "Executive Summary"  # executive summary for WW activity report.
        INLINE = "INLINE"
        QBR_QUARTERLY = "ESP Quarterly PPT"
        QBR_MONTHLY = "ESP Monthly PPT"

    def __init__(self, webconsole):
        self._webconsole = webconsole
        self._driver = self._webconsole.browser.driver
        self.format = ConfigureSchedules.Format
        self.frequency = ConfigureSchedules.Frequency
        self._access_schedule_frame()
        self._log = logger.get_log()

    @WebAction()
    def _access_schedule_frame(self):
        """
        Switch to schedule frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _click_pdf(self):
        """
        Click on pdf
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("PDF")

    @WebAction()
    def _click_html(self):
        """
        Click on html
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("HTML")

    @WebAction()
    def _click_csv(self):
        """
        Click on csv
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("CSV")

    @WebAction()
    def _click_pptx(self):
        """
        Select Executive Summary
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("Executive Summary")

    @WebAction()
    def _click_QBR_QUARTERLY(self):
        """
        Select QBR QUARTERLY
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("ESP Quarterly PPT")

    @WebAction()
    def _click_QBR_MONTHLY(self):
        """
        Select QBR Monthly
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("ESP Monthly PPT")

    @WebAction()
    def _select_inline(self):
        """
        Select Inline as email body
        """
        export_type = self._driver.find_element(By.CLASS_NAME, "exportType")
        Select(export_type).select_by_visible_text("Email body")

    @WebAction()
    def _select_daily(self):
        """
        Select daily schedule
        """
        self._driver.find_element(By.ID, "freqDaily").click()

    @WebAction()
    def _select_weekly(self):
        """
        Select weekly
        """
        self._driver.find_element(By.ID, "freqWeekly").click()

    def _select_monthly(self):
        """
        Select monthly
        """
        self._driver.find_element(By.ID, "freqMonthly").click()

    @WebAction()
    def _click_on_save(self):
        """
        Click on save button
        """
        self._driver.find_element(By.XPATH, "//a[@id='okButton']").click()

    @WebAction()
    def _click_close(self):
        """
        Click on close button
        """
        self._driver.find_element(By.ID, 'closeButton').click()

    @WebAction()
    def _select_hour(self, hour):
        """
        Select hour
        """
        hour_elem = self._driver.find_element(By.XPATH, "//*[contains(@class,'hourDD')]")
        Select(hour_elem).select_by_visible_text(hour)

    @WebAction()
    def _select_minute(self, minute):
        """
        Select minute
        """
        minute_elem = self._driver.find_element(By.XPATH, "//*[contains(@class,'minuteDD')]")
        minute_elem.clear()
        minute_elem.send_keys(minute)

    @WebAction()
    def _select_ampm(self, ampm):
        """
        Select am/pm
        """
        ampm_elem = self._driver.find_element(By.XPATH, "//*[contains(@class,'AMDD')]")
        Select(ampm_elem).select_by_visible_text(ampm)

    @staticmethod
    def _isvalid_time(hour, minute, ampm):
        if int(hour) < 1 or int(hour) > 12:
            raise Exception('invalid Hour input')
        if int(minute) < 0 or int(minute) > 60:
            raise Exception('invalid Minute input')
        if ampm.lower() in ('am', 'pm'):
            raise Exception('invalid time period input')

    @WebAction(delay=5)
    def set_schedule_name(self, schedule_name):
        """
        sets name for the schedule
        :param schedule_name: name for schedule
        """
        WebDriverWait(self._driver, 15).until(EC.presence_of_element_located((By.ID,
                                                                              'description')))
        self._driver.find_element(By.ID, "description").clear()
        self._driver.find_element(By.ID, "description").send_keys(schedule_name)

    @WebAction()
    def _edit_report_settings(self):
        """
        Edit Report Settings in edit schedule pop-up
        """
        self._driver.find_element(By.XPATH, "//*[@id='updateScheduleParameters']").click()

    @PageService()
    def edit_report_settings(self):
        """
        Click edit report settings button
        """
        self._edit_report_settings()
        sleep(3)

    @PageService()
    def select_frequency(self, frequency):
        """
        selects the frequency pattern for schedules
        :param frequency: frequency to select, use self.frequency for available types
        """
        if frequency == self.frequency.DAILY:
            self._select_daily()
        elif frequency == self.frequency.WEEKLY:
            self._select_weekly()
        elif frequency == self.frequency.Monthly:
            self._select_monthly()
        else:
            raise Exception("Undefined Frequency type [%s] " % frequency)

    @PageService()
    def set_time(self, hour, minute, ampm='AM'):
        """
        sets the time for schedule
        :param hour:  hour input 1-12
        :param minute: minute input 1-60
        :param ampm: period input 'AM' or 'PM'
        """
        self._isvalid_time(hour, minute, ampm)
        self._log.info("Setting alert time:" + str(hour) + ":" + str(minute) + ":" + str(ampm))
        self._select_hour(hour)
        self._select_minute(minute)
        self._select_ampm(ampm)

    @PageService()
    def save(self):
        """
        saves the schedule
        """
        self._click_on_save()
        self._driver.switch_to.window(self._driver.current_window_handle)

    @PageService()
    def close(self):
        """
        closes the schedule panel
        """
        self._click_close()
        self._driver.switch_to.window(self._driver.current_window_handle)

    @WebAction()
    def set_recipient(self, recipient):
        """
        sets recipient mail id in schedule
        :param recipient: mail id of recipient, use comma seperation for multiple id
        """
        self._driver.find_element(By.ID, "emails").clear()
        self._driver.find_element(By.ID, "emails").send_keys(recipient)

    @WebAction()
    def set_users_to_notify(self, username):
        """
        sets users to Notify username in schedule
        :param username: user name of recipient
        """
        self._driver.find_element(By.ID, "users-to-notify-input-field-container").click()
        sleep(5)
        user_list = self._driver.find_element(By.XPATH, "//div[@id='available-users-section']/input[@type ='text']")
        if not user_list.is_displayed():
            sleep(4)
        user_list.clear()
        user_list.send_keys(username)
        sleep(4)
        self._driver.find_element(By.XPATH, f"//span[@title='{username}']/preceding::input[@title = 'Add']").click()

    @WebAction()
    def clear_recipient(self):
        """
        Clears recipient name in schedule
        """
        self._driver.find_element(By.ID, "emails").clear()

    @PageService()
    def select_format(self, file_type='PDF'):
        """
        selects the format given in input
        :param file_type: file format to select in schedule
        """
        if file_type == self.format.PDF:
            self._click_pdf()
        elif file_type == self.format.HTML:
            self._click_html()
        elif file_type == self.format.CSV:
            self._click_csv()
        elif file_type == self.format.EXECUTIVE_SUMMARY:  # present in WW activity report.
            self._click_pptx()
        elif file_type == self.format.QBR_QUARTERLY:  # present in CommCell, CommCell group dashboard.
            self._click_QBR_QUARTERLY()
        elif file_type == self.format.QBR_MONTHLY:  # present in CommCell, CommCell group dashboard.
            self._click_QBR_MONTHLY()
        elif file_type == self.format.INLINE:
            self._select_inline()
        else:
            raise Exception('Given format %s not available in schedule panel' % file_type)

    @WebAction()
    def _enable_nw_output(self):
        """
        Enable network output
        """
        self._driver.find_element(By.XPATH, "//div[@name = 'networkShare']").click()

    @WebAction()
    def _set_nw_user(self, user_name):
        """
        Set network user
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'networkUser']").send_keys(user_name)

    @WebAction()
    def _set_nw_pwd(self, password):
        """
        Set network password
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'networkPassword']").send_keys(password)

    @WebAction()
    def _set_nw_path(self, network_path):
        """
        Set network path
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'networkPath']").send_keys(network_path)

    @PageService()
    def set_network_path(self, network_path, user_name, password):
        """
        sets network path in schedule panel
        :param network_path: path to save file ex: \\machine\folder1
        :param user_name: user to access network path with write permission
        :param password: password for the user given
        """
        self._enable_nw_output()
        self._set_nw_path(network_path)
        self._set_nw_user(user_name)
        self._set_nw_pwd(password)

    @PageService()
    def enable_end_user_security(self):
        """ select the end user security"""
        self._enable_end_user_security()

    @WebAction()
    def _enable_end_user_security(self):
        """ select the end user security"""
        xpath = '//*[@name="endUserSecurity"]/..//*[@class="cv-material-toggle cv-toggle"]'
        self._driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def set_support_manager_schedule(self, name):
        """
        Set support account manager name
        :param name: Specify support account manager name
        """
        self._set_support_account_manager_schedule(name)

    @PageService()
    def set_technical_manager_schedule(self, name):
        """
        Set technical account manager name
        :param name: specify the technical account manager name
        """
        self._set_technical_account_manager_schedule(name)

    @WebAction()
    def _set_support_account_manager_schedule(self, name):
        """
        Set support account manager name
        :param name: Specify support account manager name
        """
        self._driver.find_element(By.ID, 'sam').send_keys(name)

    @WebAction()
    def _set_technical_account_manager_schedule(self, name):
        """
        Set technical account manager name
        :param name: specify the technical account manager name
        """

        self._driver.find_element(By.ID, 'tam').send_keys(name)

    @PageService()
    def create_schedule(self, schedule_name, email_recipient, file_format=Format.PDF,
                        frequency=Frequency.DAILY):
        """
        Method to create schedule with basic options with email notification and with
        given format and frequency
        :param schedule_name: name of schedule to be created
        :param email_recipient: email id for notfication, comma seperated to multiple id
        :param file_format: format of file type, use self.format for available formats
        :param frequency: frequency pattten for schedule
        """
        self._log.info("Creating schedule:%s ; email recipient:%s; format:%s; frequency:%s;",
                       schedule_name, email_recipient, file_format, frequency)
        sleep(4)
        self.set_schedule_name(schedule_name)
        self.set_recipient(email_recipient)
        self.select_format(file_format)

        self.select_frequency(frequency)
        self.save()
        sleep(4)


class ConfigureAlert:
    """
    ConfigureAlert has interfaces to setup alert on reports, for basic alert use create_alert,
    to create alert with for non default options create your own customized method

    create_alert(alert_name=None, column_name=None, column_value=None,
                     recipient_mail='reportautomation@commvault.com')
                -- creates a alert with email notification and with default time.

    set_name(name): -- sets name for the alert

    select_notifications_type(notification_option)
                -- selects notification type, use self.notifications_type for available formats

    set_recipient(recipient) -- sets recipient mail id

    set_time(hour, minute, ampm='AM')  -- sets time for Alert

    select_frequency(self, interval): selects frequency of alert

    add_condition() -- clicks on add alert condition

    check_test_criteria() -- clicks test criteria in alert panel

    select_alert_severity(notification_with) -- select severity in alert notification

    select_alert_condition(condition='all') --selection condition for alerts (all or any)

    select_column(name) -- selects the column for alert

    set_value(value) -- sets the value for column selected

    select_operator(operator) -- selects the operator for column to be checked

    save() -- saves Alert

    cancel() -- closes Alert panel

    get_column_names() - gets the columns name available in drop down

    get_available_conditions() - gets available conditions for a column.

    select_health_param(status) -- select health param status in alert(good/warning/critical)
    """

    class Operator:
        """
        Operator is constant on different types of operators supported in alerts
        """
        EQUAL_TO = "Equal To"
        NOT_EQUAL_TO = "Not Equal To"
        CONTAINS = "Contains"
        NOT_CONTAINS = "Not Contains"
        IS_EMPTY = "Is Empty"
        NOT_EMPTY = "Not Empty"
        LESS_THAN = "Less Than"
        MORE_THAN = "More Than"

    class Notification:
        """
        Notification is a constant on different notification types
        available on Reports Alerts panel
        """
        EMAIL = "Email"
        CONSOLE_ALERTS = "Console Alerts"
        EVENT_VIEWER = "Windows Event Viewer"
        SNMP_Traps = "SNMP Traps"

    class Frequency:
        """
        Frequency is a constant on different frequency types available on Reports Alerts panel
        """
        DAILY = 'Day'
        WEEKLY = "Week"
        Monthly = "Month"

    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self.operator = ConfigureAlert.Operator
        self.notifications_type = ConfigureAlert.Notification
        self.frequency = ConfigureAlert.Frequency
        self._log = logger.get_log()

    @staticmethod
    def _isvalid_time(hour, minute, ampm):
        if int(hour) < 1 or int(hour) > 12:
            raise Exception('invalid Hour input')
        if int(minute) < 0 or int(minute) > 60:
            raise Exception('invalid Minute input')
        if ampm not in ('AM', 'PM'):
            raise Exception('invalid time period input')

    @WebAction()
    def _set_alert_name(self, name):
        """
        Set alert name
        """
        name_field = self._driver.find_element(By.XPATH, ".//*[@id='alarmName']")
        name_field.clear()
        name_field.send_keys(name)

    @WebAction()
    def _select_severity(self, notification_with):
        """
        Select severity
        """
        severity = self._driver.find_element(By.XPATH, "//select[@id='alertSeveritySelect']")
        Select(severity).select_by_visible_text(notification_with)

    @WebAction()
    def _select_notfication_condition(self, value):
        """
        Select notification condition
        """
        conditn = self._driver.find_element(By.XPATH, "//*[@id='allOrAnyDiv']/select")
        Select(conditn).select_by_visible_text(value)

    @WebAction()
    def _select_health_status(self, status):
        """
        Select health status
        """
        status_list = self._driver.find_element(By.XPATH, "//select[@id = 'statusSelect']")
        Select(status_list).select_by_visible_text(status)

    @WebAction()
    def _select_column_name(self, name, condition_number=1):
        """
        Select column name
        Args:
            name                          (String)    --     column name
            condition_number              (Numeric)   --     On which condition column should be selected
        """
        condition_number = condition_number - 1
        column_dropdown = self._driver.find_elements(By.XPATH, "//*[contains(@id,'alarms-columns-dropdown')] | "
                                                              "//*[contains(@class,'gen-columnSelect')] ")
        column_dropdown[condition_number].click()
        self._driver.find_elements(By.XPATH, "//li[contains(@class,'table-column-selector') and text()='"+name+"'] | "
                                            "//*[contains(@class,'gen-columnSelect')]/option[text()='"+name+"']"
                                            )[condition_number].click()
        sleep(1)

    @WebAction()
    def _select_operator(self, operator):
        """
        Select operator
        """
        Select(self._driver.find_element(By.ID, "gen-opSelect")).select_by_visible_text(operator)
        sleep(1)

    @WebAction()
    def _set_value(self, value, condition_number):
        """
        Set value
        Args:
            value                      (String)       --    set value
            condition_number           (Numeric)      --    On which condition column should be
                                                            selected
        """
        condition_number = condition_number - 1
        value_field = self._driver.find_elements(By.XPATH, "//div[@id='paramsDiv']//input")
        value_field = value_field[condition_number]
        value_field.clear()
        value_field.send_keys(value)

    @WebAction()
    def _select_email(self):
        """
        Select email
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'emailAlertCB']").click()

    @WebAction()
    def _select_console_alert(self):
        """
        Select console alert
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'consoleAlertCB']").click()

    @WebAction()
    def _select_event_viewer(self):
        """
        Select event viewer
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'eventViewerCB']").click()

    @WebAction()
    def _select_snmp(self):
        """
        Select snmp
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'snmpCB']").click()

    @WebAction()
    def _set_emailid(self, recipient):
        """
        Select email id
        """
        emailto = self._driver.find_element(By.ID, "emailTo")
        emailto.clear()
        emailto.send_keys(recipient)

    @WebAction()
    def _select_hour(self, hour):
        """
        Select hour
        """
        hour_elem = self._driver.find_element(By.XPATH, "//*[contains(@class,'hourDD')]")
        Select(hour_elem).select_by_visible_text(hour)

    @WebAction()
    def _select_minute(self, minute):
        """
        Select minute
        """
        minute_elem = self._driver.find_element(By.XPATH, "//*[contains(@class,'minuteDD')]")
        minute_elem.clear()
        minute_elem.send_keys(Keys.BACK_SPACE + Keys.BACK_SPACE + minute)

    @WebAction()
    def _select_ampm(self, ampm):
        """
        Select am/pm
        """
        ampm_elem = self._driver.find_element(By.XPATH, "//*[contains(@class,'AMDD')]")
        Select(ampm_elem).select_by_visible_text(ampm)

    @WebAction()
    def _select_frequency(self, interval):
        """
        Select frequency
        """
        freq_option = self._driver.find_element(By.ID, "alarmFreqOptionSelect")
        Select(freq_option).select_by_visible_text(interval)

    @WebAction()
    def _click_on_add_condition(self):
        """
        clicks on add condition.
        """
        self._driver.find_element(By.XPATH, "//button[contains(@class,'addNewCondition')]").click()

    @WebAction()
    def _click_on_test_criteria(self):
        """
        clicks on test criteria condition.
        """
        self._driver.find_element(By.XPATH, "//button[@class = 'testCriteria']").click()

    @WebAction()
    def _click_on_save(self):
        """
        clicks on save button.
        """
        self._driver.find_element(By.ID, "dialogbutton-save").click()

    @WebAction()
    def _click_on_cancel(self):
        """
        clicks on save button.
        """
        self._driver.find_element(By.ID, "dialogbutton-cancel").click()

    @WebAction()
    def _get_column_names(self):
        """
        Get column names
        """
        col_list = self._driver.find_element(By.XPATH, "//*[contains(@class, 'gen-columnSelect')]")
        return [column.text for column in col_list.find_elements(By.TAG_NAME, "option")]

    @WebAction()
    def _get_available_conditions(self):
        """
        Get available conditions
        """
        condtn_list = self._driver.find_element(By.XPATH, "//*[contains(@class, 'gen-opSelect')]")
        return [condtn.text for condtn in condtn_list.find_elements(By.TAG_NAME, "option")]

    @WebAction()
    def _select_column_condition(self, condition, condition_number=1):
        """
        Select column condition
        Args:
            condition                (String)       --     select condition using class
                                                           ColumnCondition
        condition_number             (Numeric)   --       On which column condition should be
                                                           selected
        """
        condition_number = condition_number - 1
        select_element = self._driver.find_elements(By.XPATH, "//select[@id='gen-opSelect']")[
            condition_number]
        try:
            Select(select_element).select_by_visible_text(condition)
        except:
            Select(select_element).select_by_visible_text(condition.lower())

    @WebAction()
    def __expand_tab(self, tab_name):
        """Expands the given tab"""
        tab = self._driver.find_element(By.XPATH, f"//*[@role='dialog']//span[contains(text(),'{tab_name}') "
                                                 f"and contains(@class,'title-val')]")
        tab.click()

    @WebAction()
    def _click_edit_criteria(self):
        """Click on edit criteria"""
        self._driver.find_element(By.ID, "editCriteria").click()

    @PageService()
    def access_edit_criteria(self):
        """access edit criteria"""
        self._click_edit_criteria()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_name(self, name):
        """
        sets alert name
        :param name: name for the alert
        """
        self._set_alert_name(name)

    @PageService()
    def select_notifications_type(self, notification_option):
        """
        select notification types for alert
        :param notification_option: use self.notifications_type for available notification types
        """
        if notification_option == self.notifications_type.EMAIL:
            self._select_email()
        elif notification_option == self.notifications_type.CONSOLE_ALERTS:
            self._select_console_alert()
        elif notification_option == self.notifications_type.EVENT_VIEWER:
            self._select_event_viewer()
        elif notification_option == self.notifications_type.SNMP_Traps:
            self._select_snmp()

    @PageService()
    def set_recipient(self, recipient):
        """
        sets recipient mail id in schedule
        :param recipient: mail id of recipient, use comma seperation for multiple id
        """
        self._set_emailid(recipient)

    @PageService()
    def set_time(self, hour, minute, ampm='AM'):
        """
        sets the time for schedule
        :param hour:  hour input 1-12
        :param minute: minute input 1-60
        :param ampm: period input 'AM' or 'PM'
        """
        self._isvalid_time(hour, minute, ampm)
        self._log.info("Setting alert time:" + str(hour) + ":" + str(minute) + ":" + str(ampm))
        self.__expand_tab("Schedule")
        self._select_hour(hour)
        self._select_minute(minute)
        self._select_ampm(ampm)

    @PageService()
    def select_frequency(self, frequency='Day'):
        """
        selects the frequency pattern for schedules
        :param frequency:  frequency to select, use self.frequency for available types
        """
        self._log.info("Setting interval:" + str(frequency))
        self._select_frequency(frequency)

    @PageService()
    def add_condition(self, column_name, condition_string,
                      column_condition=Operator.EQUAL_TO, condition_number=1):
        """
        add alert condition
        Args:
            column_name                      (String)    --     name of the column
            condition_string                 (String)    --     conditon to be set for column
            column_condition                 (String)    --     Operator to be selected
            condition_number                 (Numeric)   --     On which condition to set
        """
        self._click_on_add_condition()
        self.select_column(column_name, condition_number)
        self._select_column_condition(column_condition, condition_number)
        self.set_value(condition_string, condition_number)

    @PageService()
    def check_test_criteria(self):
        """
        clicks test criteria in alert panel
        """
        self._click_on_test_criteria()
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._webconsole.wait_till_load_complete(timeout=300)

    @PageService()
    def select_alert_severity(self, notification_with):
        """
        send notification with option can be changed as: Info/Warning/Critical
        """
        self._select_severity(notification_with)

    @PageService()
    def select_alert_condition(self, condition='all'):
        """
        select condition: all or any
        """
        self._select_notfication_condition(condition)

    @PageService()
    def select_column(self, name, condition_number=1):
        """
        selects specified column name
        """
        self._select_column_name(name, condition_number)

    @PageService()
    def set_value(self, value, condition_number=1):
        """
        set the value for columns selected
        """
        self._set_value(value, condition_number)

    @PageService()
    def select_operator(self, operator):
        """
        select the operator to be applied to column,
        :param operator: use self.operator to find the available types
        """
        self._select_operator(operator)

    @PageService()
    def save(self):
        """
        saves the Alert
        """
        self._click_on_save()
        sleep(2)

    @PageService()
    def cancel(self):
        """
        closes the schedule panel by cancelling the panel
        """
        self._click_on_cancel()
        sleep(2)

    @PageService()
    def expand_tab(self, tab_name):
        """
        expands the input tab
        """
        self.__expand_tab(tab_name)

    @PageService()
    def create_alert(self, alert_name=None, column_name=None, column_value=None,
                     recipient_mail=_CONFIG.email.email_id):
        """
        :param alert_name: Specify the alert name
        :param column_name: specify the column neame to select
        :param column_value: Specify the column value to be selected.
        :param recipient_mail: Specify the email recipient name
        """
        self._log.info("Creating alert:%s", alert_name)
        sleep(1)
        if alert_name is not None:
            self.set_name(alert_name)
        if column_name is not None:
            self.select_column(column_name)
            sleep(2)
        if column_value is not None:
            self.set_value(column_value)
        self.__expand_tab("Notification")
        self.set_recipient(recipient_mail)
        self.save()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def is_alert_created(self, time_out=30):
        """
        Verify alert is created through notification
        Returns:True/False
        """
        end_time = time() + time_out
        while time() < end_time:
            notifications = self._webconsole.get_all_unread_notifications()
            if not notifications:
                continue
            if notifications[0] == "Alert created successfully":
                return True
            self._log.info("Notification:[%s]", notifications[0])
            return False
        raise CVTimeOutException(time_out, "Alert notification is not recieved within time "
                                           "period")

    @PageService()
    def get_column_names(self):
        """
        :return: columns list available for alert
        """
        self._get_column_names()

    @PageService()
    def get_available_conditions(self):
        """
        :return: list of available conditions for column
        """
        self._get_available_conditions()

    @PageService()
    def select_health_param(self, status):
        """
        selects the status of parameter to be set.
        :param status: Warning/Critical/Good
        """
        self._select_health_status(status)


class Security:
    """Security has interfaces to do security changes on reports and in metrics report pages."""

    def __init__(self, webconsole: WebConsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction(delay=2)
    def _access_security_frame(self):
        """Access security frame"""
        frame = self._driver.find_elements(By.CLASS_NAME, "modal-iframe")
        if frame:  # in custom reports frame doesnt exist
            self._driver.switch_to.frame(frame[0])

    @WebAction()
    def _get_associated_users(self):
        """Gets the list of associated users
        Returns(list): List of user names
        """
        return [user.text for user in self._driver.find_elements(By.XPATH, 
            "//ul[@id='selectedUserList']/li")]

    @WebAction()
    def _search_user(self, username):
        """Enters the username in the security-search-user field
        Args:
            username: Name of the user to be entered
        """
        search_field = self._driver.find_element(By.ID, "cr-security-search-user")
        search_field.send_keys(username)
        search_field.send_keys(Keys.RETURN)
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _move_to_selected_list(self):
        """Move to selected list """
        self._driver.find_element(By.ID, "moveRight").click()
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _move_to_available_list(self):
        """Move to available list """
        self._driver.find_element(By.ID, "moveLeft").click()
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _click_available_user(self, username):
        """Clicks the user from the list of available users
        Args:
            username: Name of the user
        """
        user_path = "//ul[@id='availableUserList']/li[@data-user='" + username + "']"
        self._driver.find_element(By.XPATH, user_path).click()

    @WebAction()
    def _click_selected_user(self, username):
        """Clicks the user from the list of selected users
        Args:
            username: Name of the user
        """
        user_path = "//ul[@id='selectedUserList']/li[@data-user='" + username + "']"
        self._driver.find_element(By.XPATH, user_path).click()

    @WebAction()
    def _click_ok(self):
        """Clicks Ok button to save changes"""
        self._driver.find_element(By.CLASS_NAME, "okSaveButton").click()

    @WebAction()
    def _switch_back_frame(self):
        """Switch back to default frame """
        self._driver.switch_to.window(self._driver.window_handles[-1])

    @PageService()
    def is_user_associated(self, username):
        """Verify if the user is associated
        Args:
            username:  Name of the user
        """
        if username in self._get_associated_users():
            return True
        return False

    @PageService()
    def associate_user(self, username):
        """ Adds the user to the selected list
        Args:
            username: user name to associate
        """
        self._access_security_frame()
        if self.is_user_associated(username) is False:
            self._search_user(username)
            self._click_available_user(username)
            self._move_to_selected_list()

    @PageService()
    def deassociate_user(self, username):
        """ Removes the user from the selected list
        Args:
            username: user name to de-associate
        """
        self._access_security_frame()
        if self.is_user_associated(username) is True:
            self._click_selected_user(username)
            self._move_to_available_list()

    @PageService()
    def get_associated_users(self):
        """ Gets the list of user/user groups already associated
        Returns:
            list: List of users/user groups
        """
        self._webconsole.wait_till_load_complete()
        return self._get_associated_users()

    @PageService()
    def close(self):
        """ Closes the security panel"""
        self._click_ok()
        self._switch_back_frame()
        self._webconsole.wait_till_load_complete()


class CustomSecurity:
    """Security has interfaces to do security changes on reports and in metrics report pages."""

    class Permissions(Enum):
        """List of permissions which are present in Permissions drop down"""
        CHANGE_SECURITY_SETTINGS = "Change Security Settings"
        EDIT_REPORT = "Edit Report"
        DELETE_REPORT = "Delete Report"
        EXECUTE_REPORT = "Execute Report"

    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction()
    def __set_user_search_text(self, text):
        """Set user search text"""
        search = self._driver.find_element(By.XPATH, "//input[@id='field']")
        search.send_keys(text)

    @WebAction(delay=2)
    def __click_permissions(self):
        """Click permissions"""
        permissions = self._driver.find_element(By.XPATH, 
            "//*[@id='searchContainer']//*[contains(text(),'Permissions')]")
        permissions.click()

    @WebAction()
    def __select_permission(self, permission):
        """Click change security settings permission"""
        popup_checkboxes = self._driver.find_elements(By.XPATH, f"//span[contains(text(),'{permission.value}')]")
        for single_pop in popup_checkboxes:
            if single_pop.is_displayed():
                single_pop.click()
                return

    @WebAction()
    def __click_add_user(self):
        """Click add user"""
        button = self._driver.find_element(By.XPATH, "//div[@id='addUserButton']")
        button.click()

    @WebAction()
    def __click_update(self):
        """Click update"""
        update = self._driver.find_element(By.XPATH, "//*[@id='entity-security-modal']//*[contains(text(),'Update')]")
        update.click()

    @WebAction()
    def __click_cancel(self):
        """Click cancel"""
        cancel = self._driver.find_element(By.XPATH, "//*[@id='entity-security-modal']//*[contains(text(),'Cancel')]")
        cancel.click()

    @WebAction(delay=5)
    def __wait_for_user_list_to_load(self, time_out=60):
        """Wait till users list getting loaded"""
        sleep(2)
        end_time = time() + time_out
        while time() < end_time:
            if self._driver.find_elements(By.XPATH, "//*[contains(@class,'ng-valid-parse loading')]"):
                sleep(2)
            else:
                sleep(2)
                return
        raise CVTimeOutException(
            time_out,
            "users list is loading for long time in security pane",
            self._driver.current_url
        )

    @WebAction(delay=5)
    def __select_suggested_user(self, user_name):
        """Select suggested user"""
        users = self._driver.find_elements(By.XPATH, "//li[@class='search-result ng-scope']")
        for each_user in users:
            if user_name in each_user.text:
                each_user.click()
                return
        raise NoSuchElementException(f"{user_name}User or user group not found in security panel")

    @WebAction()
    def _get_associated_users(self):
        """Gets the list of associated users
        Returns(list) : List of user names
        """
        return [user.text for user in self._driver.find_elements(By.XPATH, 
            "//*[@class='user-info ng-scope']//li[@class='ng-binding']")]

    @WebAction()
    def __deassociate_user(self, user):
        """
        Deassociate specified user
        Args:
            user                         (String)    --    user/user group name
        """
        try:
            xpath = f"//*[contains(text(), '{user}')]/ancestor::div[@class='user-row']//*[contains(@class,'xButton')]"
            self._driver.find_element(By.XPATH, xpath).click()
        except NoSuchElementException:
            raise NoSuchElementException("Cannot deassociate [%s] user" % user)

    @WebAction()
    def __click_user_specific_permission(self, user):
        """Clicks the specific permission button of the user"""
        permission = self._driver.find_element(By.XPATH, 
            f"//*[@class='user-info ng-scope']//*[contains(text(),'{user}')]"
            f"/ancestor::div[@class='user-row']//*[@class='permissions-label']")
        permission.click()

    @PageService()
    def __select_users(self, user_names):
        """
        select user/user group in security panel
        Args:
            user_names                  (List)    --   user or user group name
        """
        for each_user in user_names:
            self.__set_user_search_text(each_user)
            self.__wait_for_user_list_to_load()
            self.__select_suggested_user(each_user)

    @PageService()
    def update(self):
        """Click update security panel"""
        self.__click_update()
        sleep(4)

    @PageService()
    def associate_security_permission(self, users, permissions=None):
        """
        Associate permission to user
        Args:
            users                          (List)    --     users or user group names

            permissions                   (List)    --     Permission to be selected from
                                                           Permissions class

            Defaults to [CustomSecurity.Permissions.EXECUTE_REPORT]
        """

        if not isinstance(users, list):
            raise TypeError("'Users' parameter value should be a list for associating security permissions")

        permissions = permissions if permissions else [CustomSecurity.Permissions.EXECUTE_REPORT]
        if not isinstance(permissions, list):
            raise TypeError("Permission Parameter must be a list of Permissions Enum")
        for permission in permissions:
            if permission not in CustomSecurity.Permissions:
                raise TypeError("Permission Parameter must be a list of Permissions Enum")

        self.__select_users(users)
        self.__click_permissions()
        sleep(2)
        list(map(self.__select_permission, permissions))
        self.__click_permissions()
        self.__click_add_user()

    @PageService()
    def is_user_associated(self, username):
        """Verify if the user is associated
        Args:
            username:  Name of the user
        """
        users = self._get_associated_users()
        for each_user in users:
            if username in each_user:
                return True
        return False

    @PageService()
    def deassociate_user(self, username):
        """ Removes the user from the selected list
        Args:
            username: user name to de-associate
        """
        self.__deassociate_user(username)

    @PageService()
    def get_associated_users(self):
        """ Gets the list of user/user groups already associated
        Returns:
            list: List of users/user groups
        """
        return self._get_associated_users()

    @PageService()
    def cancel(self):
        """Click cancel"""
        self.__click_cancel()

    @PageService()
    def modify_permissions(self, user, permissions=None):
        """
        Associate permission to user
        Args:
            user                          (str)    --     users or user group names

            permissions                   (List)    --     Permission to be selected from
                                                             Permissions class

                Defaults to [CustomSecurity.Permissions.EXECUTE_REPORT]
        """

        permissions = permissions if permissions else [CustomSecurity.Permissions.EXECUTE_REPORT]
        for permission in permissions:
            if permission not in CustomSecurity.Permissions:
                raise TypeError("Permission Parameter must be a list of Permissions Enum")

        self.__click_user_specific_permission(user)
        list(map(self.__select_permission, permissions))
        self.__click_user_specific_permission(user)
