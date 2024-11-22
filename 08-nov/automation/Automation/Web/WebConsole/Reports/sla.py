from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" All the Web SLA Reports page. """
from enum import Enum
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.Reports.Custom import viewer


class WebSla:
    """Class to interact with WEB SLA page"""

    class Exclude_sla_categories(Enum):
        """ Available SLA exclusion categories"""

        PERMANENT = "Exclude From SLA Property"
        INVESTIGATION_INFRASTRUCTURE = "Service provider action pending"
        INVESTIGATION_APPLICATION = "Customer action pending"
        RECENTLY_INSTALLED = "Recently Installed with No Finished Job"
        BACKUP_ACTIVITY_DISABLED = "Backup Activity Disabled"
        EXCLUDED_SERVER_TYPE = "Excluded Server Type"

    def __init__(self, webconsole):
        """
        Args:
           webconsole (WebConsole): The webconsole object to use
        """
        self.SLA_exclusion_panel = _SLA_exclusion_panel(webconsole)
        self.table = None
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self.viewer = viewer.CustomReportViewer(self._webconsole)

    @WebAction()
    def _click_text(self, text):
        """
        Clicks on chart category
        Args:
            text: Chart category text
        """
        chart_category = (
            f"//*[name()='tspan' and contains(text(), '{text}')] "
            f"| //*[name()='text' and contains(text(), '{text}')] "
            f"| //a[contains(text(),'{text}')]"
        )
        # first xpath is for WebConsole SLA Report with SP<25
        # second xpath is for WebConsole SLA Report with SP>25
        # third xpath is for SLA Custom Report.

        self._driver.find_element(By.XPATH, chart_category).click()

    @PageService()
    def access_missed_sla(self):
        """
        Drill down on missed sla in Chart
        """
        self._click_text('Missed SLA')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_excluded_from_sla(self):
        """
        drill down on excluded from SLA link from SLA report
        """
        self._click_text('excluded from SLA')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_met_sla(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('Met SLA')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_failed_clients(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('Failed')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_no_schedule_clients(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('No Schedule')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_no_job_clients(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('No Finished Job within SLA Period')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_filtered_vms(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('Filtered VM')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_snap_with_nobackupcopy_clients(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('Snap Job with ')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_excluded_sla(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('entities are excluded from SLA')
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_all_missed_sla(self):
        """
        Drill down on sla in Chart
        """
        self._click_text('All subclients and VMs that missed SLA')
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _get_sla_txt(self):
        """Read the text for SLA Panel"""
        return self._driver.find_element(By.ID, 'slaPercent').text

    @PageService()
    def get_sla(self):
        """
        Clicks on chart category
        Args:
            text: Chart category text
        """
        sla_text = self._get_sla_txt()
        return sla_text.split("SLA is ")[1]

    @WebAction()
    def _get_sla_percentage_txt(self):
        """Read the text for SLA percent"""
        chart_label = "//div[@class='sla-text-align-center sla-width-full sla-large-font']/span"
        return self._driver.find_element(By.XPATH, chart_label).text

    @PageService()
    def get_sla_percentage(self):
        """
        Get SLA percentage value
        Args:
            text: Chart category text
        """
        sla_text = self._get_sla_percentage_txt()
        return sla_text[:-1]

    @WebAction()
    def _get_pending_action_count(self):
        """
        get the pending action count form sla report
        Returns:
            count (INT) : pending action count from sla
        """
        xpath = "//*[@class='exclusion-count-container']/..//span[contains(@class, 'exclusion-count-bg ')]"
        pending_category = self._driver.find_elements(By.XPATH, xpath)
        return {'Customer_action': pending_category[0].text, 'MSP_action': pending_category[1].text}

    @WebAction()
    def _get_customer_pending_action(self):
        """
        get the customer action pending count from SLA report
        Returns:
            count (INT) : count in int
        """
        xpath = "//span[@class='exclusion-count-bg exclusion-count-yellow right-margin'] "
        customer_pending = self._driver.find_element(By.XPATH, xpath)
        if customer_pending:
            return int(customer_pending.text)
        return 0

    @WebAction()
    def _get_msp_action_pending(self):
        """
        get MSP action pending from SLA report
        Returns:
            count (INT) : count in int
        """
        xpath = "//span[@class='exclusion-count-bg exclusion-count-orange']"
        msp_count = self._driver.find_element(By.XPATH, xpath)
        if msp_count:
            return int(msp_count.text)
        return 0

    @PageService()
    def get_custom_action_pending(self):
        """
        get the count of customer action pending
        Returns:
            count (INT) : count of customer action pending
        """
        return self._get_customer_pending_action()

    @PageService()
    def get_msp_action_pending(self):
        """
        get the count of MSP action pending
        Returns:
            count (INT) : count of MSP action pending
        """
        return self._get_msp_action_pending()

    @PageService()
    def exclude_sla(self, entity_name, exclude_category, reason):
        """
        exclude entity from SLA report
        Args:
            entity_name: server/subclient name
            exclude_category: Exclude SLA
            reason: reason for exclusion
        """
        self.access_missed_sla()
        self.table = viewer.DataTable("Unprotected servers")
        self.viewer.associate_component(self.table)
        self.table.set_number_of_rows(number_of_results=100)
        self.table.access_action_item(entity_name.upper(), 'Exclude From SLA')
        self.SLA_exclusion_panel.exclude_entity_from_sla(exclude_category, reason)


class _SLA_exclusion_panel:
    """ SLA exclusion panel"""

    def __init__(self, webconsole):
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def _choose_exclude_category(self, exclude_category):
        """ choose a exclude category"""
        xpath = f"//input[@type='radio']/..//label[text()='{exclude_category}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _choose_sla_description(self, reason=None):
        """fill the description in the SLA exclude field"""

        fill_description = self._driver.find_element(By.ID, "sla-description")
        fill_description.send_keys(reason)

    @WebAction()
    def _choose_include_sla_delay(self):
        """select the SLA delay for inclusion"""

        self._driver.find_element(By.ID, "excludeDays").click()
        self._driver.find_element(By.XPATH, "//*[@id='excludeDays']/option[2]").click()  # select 15 days

    @WebAction()
    def _submit_sla_exclusion(self):
        """ submit the sla exclusion panel"""
        self._driver.find_element(By.ID, "excludeSLABtn").click()

    @PageService()
    def exclude_entity_from_sla(self, exclude_category, reason=None):
        """ exclude a server/subclient from sla report"""

        self._choose_exclude_category(exclude_category)
        self._choose_sla_description(reason)
        self._choose_include_sla_delay()
        self._submit_sla_exclusion()
