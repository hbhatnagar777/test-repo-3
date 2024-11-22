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
from Web.AdminConsole.Reports.Custom import viewer


class Sla:
    """Class to interact with WEB SLA page"""


    class Exclude_sla_categories(Enum):
        """ Available SLA exclusion categories"""

        PERMANENT = "Exclude From SLA Property"
        INVESTIGATION_INFRASTRUCTURE = "Service provider action pending"
        INVESTIGATION_APPLICATION = "Customer action pending"
        RECENTLY_INSTALLED = "Recently Installed with No Finished Job"
        BACKUP_ACTIVITY_DISABLED = "Backup Activity Disabled"
        EXCLUDED_SERVER_TYPE = "Excluded Server Type"

    def __init__(self, admin_console):
        """
        Args:
           admin_console (Adminconsole): The webconsole object to use
        """
        self.SLA_exclusion_panel = _SLA_exclusion_panel(admin_console)
        self._admin_console = admin_console
        self._driver = admin_console.browser.driver
        self.viewer = viewer.CustomReportViewer(self._admin_console)
        self._main_chart = None
        self._missed_chart = None

    @property
    def main_chart(self):
        if self._main_chart is None:
            self._main_chart = viewer.CircularChartViewer("")
            self.viewer.associate_component(self._main_chart, comp_id='highcharts-s77trn2-10')
        return self._main_chart

    @property
    def missed_chart(self):
        if self._missed_chart is None:
            self._missed_chart = viewer.CircularChartViewer("")
            self.viewer.associate_component(self._main_chart, comp_id='highcharts-25seh1e-13')
        return self._missed_chart

    @PageService()
    def access_missed_sla(self):
        """
        Drill down on missed sla in Chart
        """
        self.main_chart.click_slice('Missed SLA')

    @PageService()
    def access_met_sla(self):
        """
        Drill down on sla in Chart
        """
        self.main_chart.click_slice('Met SLA')

    @PageService()
    def access_failed_clients(self):
        """
        Drill down on sla in Chart
        """
        self.missed_chart.click_slice('Failed')

    @PageService()
    def access_no_schedule_clients(self):
        """
        Drill down on sla in Chart
        """
        self.missed_chart.click_slice('No Schedule')

    @PageService()
    def access_no_job_clients(self):
        """
        Drill down on sla in Chart
        """
        self.missed_chart.click_slice('No Finished Job within SLA Period')

    @PageService()
    def access_snap_with_nobackupcopy_clients(self):
        """
        Drill down on sla in Chart
        """
        self.missed_chart.click_slice('Snap Job with ')

    @PageService()
    def access_excluded_sla(self):
        """
        Drill down on sla in Chart
        """
        excluded_comp = viewer.HitsComponent("")
        self.viewer.associate_component(excluded_comp, comp_id='component_Hits1538575288482')
        excluded_comp.click_by_content('entities are excluded from SLA')

    @PageService()
    def access_all_missed_sla(self):
        """
        Drill down on sla in Chart
        """
        missed_comp = viewer.HitsComponent("")
        self.viewer.associate_component(missed_comp, comp_id='component_Hits1649448423044')
        missed_comp.click_by_content('All subclients and VMs that missed SLA')

    @WebAction()
    def _get_sla_percentage_txt(self):
        """Read the text for SLA percent"""
        html_comp = viewer.HtmlComponent("")
        self.viewer.associate_component(html_comp, comp_id='component_CustomHtml1538721582492')
        return html_comp.get_html_component_contents()

    @PageService()
    def get_sla_percentage(self):
        """Get SLA percentage value"""
        sla_text = self._get_sla_percentage_txt()
        return sla_text.split("Current SLA is ")[1].split("%")[0]

    def _get_action_pending_content(self):
        """"
        get the action pending count from SLA report
        """
        html_comp = viewer.HtmlComponent("")
        self.viewer.associate_component(html_comp, comp_id='component_CustomHtml1538721582492')
        return html_comp.get_html_component_contents()

    @PageService()
    def get_custom_action_pending(self):
        """
        get the count of customer action pending
        Returns:
            count (INT) : count of customer action pending
        """
        txt = self._get_action_pending_content()
        return int(txt.split("Customer action pending")[1].split("Service provider action pending")[0])

    @PageService()
    def get_msp_action_pending(self):
        """
        get the count of MSP action pending
        Returns:
            count (INT) : count of MSP action pending
        """
        txt = self._get_action_pending_content()
        return int(txt.split("Service provider action pending")[1])

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
        table = viewer.DataTable("Unprotected servers")
        self.viewer.associate_component(table)
        table.set_number_of_rows(number_of_results=100)
        table.access_action_item(entity_name.upper(), 'Exclude From SLA')
        self.SLA_exclusion_panel.exclude_entity_from_sla(exclude_category, reason)


class _SLA_exclusion_panel:
    """ SLA exclusion panel"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.browser.driver

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
