from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage License Summary activity report.

LicenseSummary:

    __init__()                             --  initialize instance of the LisenceSummary class

    _get_table_data()                      --  returns table data

    get_alltables_data                     -- returns all table data present on Worldwide Current Capacity Usage Report

    get_table_data()                       --  returns table data for a specified table

    _click_moreinfo()                       -- selects More Info hyperlink

    access_moreinfo()                      -- perform more info action on license summary

    _click_usage_by_agents_and_licenses()   -- selects Usage by Agents and Licenses hyperlink

    access_usage_by_agents()                 -- perform more info action on license summary

    get_page_chart_data()                  -- returns chart data for all charts on the current page

    access_subclientpeak()                 -- perform subclient peak action on license summary

    _select_subclient_license()             -- selects subclient license hyperlink with given license name

    get_allchart_data()                   -- returns all chart data for the page

    _get_license_chart_data()              -- returns chart data of specific frame

    _get_usagecollection_value()           -- get the usage collection time on Licenses summary
    
    click_workloadusage()                  -- selects the Current workload usage hyperlink
    
    click_workloadsummary()               --  selects the Workload summary hyperlink

"""

from datetime import datetime
from Web.Common.exceptions import CVTimeOutException, CVWebAutomationException
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom._components.chart import RectangularChartViewer


class LicenseSummary:
    """
    Activity report operation on metrics
    """

    def __init__(self, webconsole):
        """
                Args:
                     webconsole: WebConsole object
                """
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self.mail_table = None
        self.group = False
        self.chart = None
        self.license_types = {
            "Capacity Licenses": {
                'Commvault Backup and Recovery - peak usage per month': [],
                'Commvault Backup and Recovery for Unstructured Data - peak usage per month': [],
                'Snapshot - peak usage per month': [],
                'Replication - peak usage per month': []},
            "Commvault Complete OI Licenses": {
                'Operating Instances - peak usage per month': [],
                'Virtual Operating Instances - peak usage per month': []},
            "Virtualization Licenses": {
                'VM Sockets - peak usage per month': [],
                'DR VM - peak usage per month': []},
            "User Licenses": {
                'Endpoint Users - peak usage per month': [],
                'Application Users - peak usage per month': []},
            "Activate Licenses": {
                'File Storage Optimization - peak usage per month': [],
                'Activate E-Discovery For Files - peak usage per month': []},
            "Metallic Licenses": {'Metallic Storage Service - peak usage per month': []},
            "Other Licenses": {'HyperScale Storage - peak usage per month': []},
            "Current usage by Agents": {},
            "Current usage by Licenses": {},
            "CommCells": {},
            "Other Licenses - current usage details": {},
            "Workload usage by capacity": {},
            "Workload usage by users": {}}
        self.column_values = ('Available Total', 'Available Total (TB)', 'Available Total (instances)',
                              'Available Total (users)', 'Total Sold (instances)', 'Total Sold',
                              'Total Sold (users)', 'Total Sold (TB)')
        self.row_values = ('Used (TB)', 'Used', 'Used (users)', 'Used (instances)')
        self.additional_columns = ['Commvault Backup and Recovery for Unstructured Data Sold (TB)',
                                   'Commvault Backup and Recovery for Unstructured Data Used (TB)',
                                   'Commvault Backup and Recovery Sold (TB)',
                                   'Commvault Backup and Recovery Used (TB)',
                                   'Operating Instances Sold',
                                   'Operating Instances Used',
                                   'Replication Sold (TB)',
                                   'Replication Used (TB)']
        self.workload_columns=["Replication Used",
                                "Complete (Backup + Archive) Used","Number of Replication Clients",
                                "Number of Snapshot Clients","Snapshot Used", "Workload ID"]

    @PageService()
    def __get_table_data(self, title, additional_col=False):
        """
        returns a dict of the data in a given table
            Args:
                title    (str)    -- table name
            Returns:
                tabledata (dict)  -- returns table data
                additional_col (bool) -- select additional columns on table

        """
        report_viewer = viewer.CustomReportViewer(self._webconsole)
        self.table = viewer.DataTable(title)
        report_viewer.associate_component(self.table)
        self.table.expand_table()
        self._webconsole.wait_till_load_complete()
        if additional_col:
            visible_columns = self.table.get_table_columns()
            if self.additional_columns != visible_columns:
                hide_columns = list(set(self.additional_columns) - set(visible_columns))
                for col in hide_columns:
                    self.table.toggle_column_visibility(col)
                    self._webconsole.wait_till_load_complete()
        return self.table.get_table_data()

    @PageService()
    def get_alltables_data(self):
        """
        returns a dict the data of all license tables present
        on worldwide or commcell current capacity usage page)

            Args:
               none

            Returns:
                table_data (dict) -- Returns table data

        """
        table_data = {}
        table_keys = list(self.license_types.keys())
        table_data['capacity'] = self.__get_table_data(table_keys[0])
        table_data['oi'] = self.__get_table_data(table_keys[1])
        self._driver.refresh()
        self._webconsole.wait_till_load_complete()
        table_data['virtualization'] = self.__get_table_data(table_keys[2])
        table_data['users'] = self.__get_table_data(table_keys[3])
        self._driver.refresh()
        self._webconsole.wait_till_load_complete()
        table_data['active'] = self.__get_table_data(table_keys[4])
        table_data['metallic'] = self.__get_table_data(table_keys[5])
        table_data['other'] = self.__get_table_data(table_keys[6])
        if self.group:
            table_data['commcells'] = self.__get_table_data(table_keys[9])
        return table_data

    @PageService()
    def get_table_data(self, ttype='capacity'):
        """
        returns a dict of the data for a given license table
            Args:
               ttype    (str)    -- License summary table name

            Returns:
                table_data (dict) -- returns table data in the form of dictionary

        """
        table_data = {}
        table_keys = list(self.license_types.keys())
        if ttype == 'capacity':
            table_data = self.__get_table_data(table_keys[0])
        elif ttype == 'oi':
            table_data = self.__get_table_data(table_keys[1])
        elif ttype == 'virtualization':
            table_data = self.__get_table_data(table_keys[2])
        elif ttype == 'users':
            table_data = self.__get_table_data(table_keys[3])
        elif ttype == 'active':
            table_data = self.__get_table_data(table_keys[4])
        elif ttype == 'metallic':
            table_data = self.__get_table_data(table_keys[5])
        elif ttype == 'other':
            if self.group:
                table_data['other'] = self.__get_table_data(table_keys[6])
            else:
                table_data['other'] = self.__get_table_data(table_keys[10])
        elif ttype == 'moreinfo':
            if self.group:
                table_data['moreinfo'] = self.__get_table_data(table_keys[6])
            else:
                table_data['moreinfo'] = self.__get_table_data(table_keys[10])
        elif ttype == 'commcells':
            table_data = self.__get_table_data(table_keys[9])
        elif ttype == 'ual':
            table_data['cagents'] = self.__get_table_data(table_keys[7])
            table_data['ulicenses'] = self.__get_table_data(table_keys[8])
        elif ttype == 'spu':
            table_data = self.get_allchart_data()
        elif ttype == "workload":
            self.additional_columns = self.workload_columns
            table_data['cworkload'] = self.__get_table_data(table_keys[11],True)
            self.additional_columns = [self.workload_columns[-1]]
            table_data['uworkload'] = self.__get_table_data(table_keys[12],True)
        return table_data

    @PageService()
    def access_moreinfo(self):
        """
        perform more info action on license summary
        """
        self._click_moreinfo()
        self._webconsole.wait_till_load_complete()
        log_windows = self._driver.window_handles
        self._driver.switch_to.window(log_windows[1])
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _click_moreinfo(self):
        """
        selects the More Info hyperlink
            Args:
                None

            Returns:
                None

        """
        self._driver.find_element(By.XPATH,"//a[text()='More Info']").click()
    
    @WebAction()
    def click_workloadusage(self):
        """
        selects the Current workload usage hyperlink
            Args:
                None

            Returns:
                None

        """
        self._driver.find_element(By.XPATH,"//a[text()='Current workload usage']").click()

    @WebAction()
    def click_recalculate(self):
        """
        selects the More Info hyperlink
            Args:
                None

            Returns:
                None

        """
        self._driver.find_element(By.XPATH,"//a[text()='Recalculate']").click()
    
    
    @WebAction()
    def click_workloadsummary(self):
        """
        selects the Workload summary hyperlink
            Args:
                None

            Returns:
                None

        """
        self._driver.find_element(By.XPATH,"//a[text()='Workload summary']").click()

    @WebAction()
    def _get_usagecollection_value(self):
        """
        get the usage collection time on Licenses summary
            Args:
                None

            Returns:
                None

        """
        return self._driver.find_element(By.XPATH, 
            "//*[@id='CustomHtml1528754534654']//*[@class='spanHdrUrl']").get_attribute('innerHTML')

    @PageService()
    def access_recalculate(self):
        """
        perform recalculate operation on license summary page
        Rasies:
        Exception if the values are not matched after recalculate
        """
        begin_time = datetime.now()  # measure the begin time
        self.click_recalculate()
        self._webconsole.wait_till_load_complete()
        end_time = datetime.now()
        time_elapsed = (end_time - begin_time)
        time_elapsed_minutes = time_elapsed.total_seconds() / 60
        if time_elapsed_minutes > 2:
            raise CVTimeOutException(time_elapsed_minutes, 'recalculation')
        dt_string = end_time.strftime("%b %d,%Y, %I:%M:%S %p")
        ucstr = f"Usage collection time: {dt_string}"
        usagevalue = self._get_usagecollection_value()
        self._webconsole.wait_till_load_complete()
        if usagevalue[:-10].replace(" ", "") == ucstr[:-9].replace(" ",
                                                                   "") and usagevalue[-3:].strip() == ucstr[-2:].strip():
            pass
        else:
            raise CVWebAutomationException(f"values are not matching after recalculate {usagevalue} ,{ucstr}")

    @PageService()
    def access_usage_by_agents(self):
        """
        perform more info action on license summary
        """
        self._click_usage_by_agents_and_licenses()
        self._webconsole.wait_till_load_complete()
        log_windows = self._driver.window_handles
        if len(log_windows) >= 2:
            self._driver.switch_to.window(log_windows[2])
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _click_usage_by_agents_and_licenses(self):
        """
        selects the Usage by Agents and Licenses hyperlink
            Args:
                None

            Returns:
                None

        """
        self._driver.find_element(By.XPATH, "//a[text()='Usage by Agents and Licenses']").click()

    @PageService()
    def access_subclientpeak(self):
        """
        perform subclient peak action on license summary
        """
        self._click_subclient_peak_usage()
        self._webconsole.wait_till_load_complete()
        log_windows = self._driver.window_handles
        self._driver.switch_to.window(log_windows[1])
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _click_subclient_peak_usage(self):
        """
        selects the Subclient Peak Usage hyperlink
            Args:
                None

            Returns:
                None

        """
        self._driver.find_element(By.XPATH, "//a[text()='Subclient peak usage']").click()

    @WebAction()
    def _get_license_chart_data(self):
        """
        returns chart data of specific frame
            Args:
                None

            Returns:
                chartdata (dict) : Returns chart data in the form of dictionary.

        """
        chartdata = self.chart.get_chart_details()
        return chartdata

    @PageService()
    def get_allchart_data(self):
        """
        returns all chart data for the page
        """
        keys = list(self.license_types.keys())[0:7]
        for key in keys:
            if key != keys[0]:
                self._select_subclient_license(key)
                self._webconsole.wait_till_load_complete()
            for nkey in self.license_types[key].keys():
                self.chart = RectangularChartViewer(nkey)
                self.chart._driver = self._driver
                webcomp = self.chart._get_id_from_component_title(nkey)
                self.chart._set_x(webcomp)
                data = self._get_license_chart_data()
                self.license_types[key][nkey].append(data)
        return self.license_types

    @WebAction()
    def _select_subclient_license(self, lic_name):
        """
        selects a given license hyperlink on the subclient peak usage page
            Args:
                lic_name    (str)    --name of license

            Returns:
                None

        """
        self._driver.find_element(By.XPATH, "//a[text()='%s']" % lic_name).click()
