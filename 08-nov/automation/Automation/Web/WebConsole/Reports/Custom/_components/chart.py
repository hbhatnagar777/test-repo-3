from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
All the operations common to chart component go to
this file
"""

import re
from abc import abstractmethod

from selenium.webdriver.support.select import Select

from Reports.Custom.sql_utils import SQLQueries
from Web.Common.page_object import (
    WebAction,
    PageService
)
from .base import (
    CRComponentBuilder,
    CRComponentProperties,
    CRComponentViewer
)


class ChartBuilder(CRComponentBuilder):
    """ Actions common to Chart Builder goes here """


class RectangularChartBuilder(ChartBuilder):
    """Common builder for  Rectangular Charts"""
    @WebAction()
    def __set_aggregation_drop_down(self, value):
        """Selects specific aggregation from drop down"""
        drop_down = self._driver.find_element(By.XPATH, self._x + "//fieldset[@data-droptype='yAxis']//select")
        option = Select(drop_down)
        option.select_by_value(value)

    @WebAction()
    def __drag_column_to_x_axis(self, column):
        """Drags column to X axis"""
        self._drag_column_from_dataset(column, self._x + "//fieldset[@data-droptype='xAxis']")

    @WebAction()
    def __drag_column_to_y_axis(self, column):
        """Drags column to Y axis"""
        self._drag_column_from_dataset(column, self._x + "//fieldset[@data-droptype='yAxis']")

    @PageService()
    def set_x_axis(self, column):
        """Adds column to X-axis

        Args:
            column  (str): name of the column

        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_x_axis(column)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_y_axis(self, column):
        """Adds column to Y-axis

        Args:
            column  (str): name of the column

        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_y_axis(column)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_aggregation(self, value):
        """Sets aggregation drop down

        Args:
            value   (str):  Type of the aggregation which you want to group

        """
        self.__set_aggregation_drop_down(value)
        self._webconsole.wait_till_load_complete()


class CircularChartBuilder(ChartBuilder):
    """Common Builder for Circular Charts"""

    @WebAction()
    def __drag_column_to_dimension(self, column):
        """Drags column to Dimension"""
        self._drag_column_from_dataset(column, self._x + "//fieldset[@data-droptype='xAxis']")

    @WebAction()
    def __drag_column_to_measure(self, column):
        """Drags column to Measure"""
        self._drag_column_from_dataset(column, self._x + "//fieldset[@data-droptype='yAxis']")

    @WebAction()
    def __set_aggregation_drop_down(self, value):
        """Selects specific aggregation from drop down"""
        drop_down = self._driver.find_element(By.XPATH, self._x + "//fieldset[@data-droptype='yAxis']//select")
        option = Select(drop_down)
        option.select_by_value(value)

    @PageService()
    def add_column_to_dimension(self, column):
        """Adds column to Dimension

        Args:
            column  (str): name of the column

        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_dimension(column)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def add_column_to_measure(self, column):
        """Adds column to Measure

        Args:
            column  (str): name of the column

        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_measure(column)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_aggregation(self, value):
        """Sets aggregation drop down

        Args:
            value   (str):  Type of the aggregation which you want to group

        """
        self.__set_aggregation_drop_down(value)
        self._webconsole.wait_till_load_complete()


class TimelineChartBuilder(RectangularChartBuilder):
    """This class contains all the builder actions specific to Timeline Chart"""

    @property
    def category(self):
        return "Chart"

    @property
    def name(self):
        return "Timeline Chart"

    @WebAction()
    def __set_time_grouping_drop_down(self, value):
        """Selects specific time from drop down"""
        drop_down = self._driver.find_element(By.XPATH, self._x + "//fieldset[@data-droptype='xAxis']//select")
        option = Select(drop_down)
        option.select_by_value(value)

    @PageService()
    def set_time_grouping(self, value):
        """Sets time grouping drop down

        Args:
            value   (str):  Type of time grouping which you want to group

        """
        self.__set_time_grouping_drop_down(value)
        self._webconsole.wait_till_load_complete()


class ChartViewer(CRComponentViewer):
    """Actions common to Chart Viewer goes here"""

    @property
    def type(self):
        return "CHART"

    @abstractmethod
    def get_chart_details(self):
        raise NotImplementedError

    @abstractmethod
    def _fetch_object_values(self):
        raise NotImplementedError


class RectangularChartViewer(ChartViewer):
    """This class contains the methods for two dimensional charts"""

    @WebAction()
    def _get_x_axis_title(self):
        """Fetches x axis title"""
        title = self._driver.find_element(By.XPATH, 
            self._x + "//*[name()='g' and contains(@class,'highcharts-axis highcharts-xaxis')]")
        return title.text

    @WebAction()
    def _get_y_axis_title(self):
        """Fetches y axis title"""
        title = self._driver.find_element(By.XPATH, 
            self._x + "//*[name()='g' and contains(@class,'highcharts-axis highcharts-yaxis')]")
        return title.text

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(By.XPATH, self._x + "//*[name()='rect' and @aria-label]")
        return [re.search("(.*,\s)(.*).", bar.get_attribute('aria-label')).group(2) for bar in bars]

    @WebAction()
    def _get_x_axis_labels(self):
        """Fetches the x-axis labels"""
        labels = self._driver.find_elements(By.XPATH, 
            self._x + "//*[contains(@class,'highcharts-xaxis-labels')]/span")
        labels.sort(key=lambda e: float(re.search(".*left:\s([0-9]*[.]*[0-9]*)px.*",
                                                  e.get_attribute("style")).group(1)))
        return [label.text for label in labels]

    @WebAction()
    def _get_y_axis_labels(self):
        """Fetches the y-axis labels"""
        labels = self._driver.find_elements(By.XPATH, 
            self._x + "//*[contains(@class,'highcharts-yaxis-labels')]/span")
        labels.sort(key=lambda e: float(re.search(".*top:\s([0-9]*[.]*[0-9]*)px.*",
                                                  e.get_attribute("style")).group(1)), reverse=True)
        return [label.text for label in labels]

    @PageService()
    def get_chart_details(self):
        """Fetches chart details"""
        obj = self._fetch_object_values()
        return {
            "x-axis_title": self._get_x_axis_title(),
            "y-axis_title": self._get_y_axis_title(),
            "count": len(obj),
            "height": obj,
            "x-axis_labels": self._get_x_axis_labels(),
            "y-axis_labels": self._get_y_axis_labels()
        }


class CircularChartViewer(ChartViewer):
    """This class contains the methods for one dimensional charts"""

    @WebAction()
    def _get_legend(self):
        """Get legend information"""
        legends = self._driver.find_elements(By.XPATH, self._x + "//*[name()='text']")
        return [legend.text for legend in legends if legend.text]

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(By.XPATH, self._x + "//*[name()='path' and @aria-label]")
        return [re.search("(.*,\s)(.*).", bar.get_attribute('aria-label')).group(2) for bar in bars]

    @WebAction()
    def __click_slice(self, slice_name):
        """Clicks the given slice"""
        slice_ = self._driver.find_element(By.XPATH, 
            self._x + f"//*[name()='path' and contains(@aria-label,'{slice_name}')]")
        slice_.click()

    @PageService()
    def get_chart_legend(self):

        """Fetches chart legend values and Legend Text"""
        legends_text = self._get_legend()
        legend_values = []
        for legend in legends_text:
            legend_value = re.search(".*:\s(.*)\s.*", legend)
            if legend_value:
                legend_values.append(legend_value.group(1))
        return legend_values, legends_text

    @PageService()
    def get_chart_details(self):
        """Fetches chart details"""
        legends, _ = self.get_chart_legend()
        values = self._fetch_object_values()
        SQLQueries.validate_list_equality(legends, values)

        return {
            "slice_count": len(values),
            "slice_values": values
        }

    @PageService()
    def click_slice(self, slice_name):
        """Clicks a slice"""
        self.__click_slice(slice_name)
        self._webconsole.wait_till_load_complete()


class HorizontalBarViewer(RectangularChartViewer):
    """This class contains all the viewer actions specific to Horizontal Bar"""

    @WebAction()
    def _get_x_axis_labels(self):
        """Fetches the x-axis labels"""
        labels = self._driver.find_elements(By.XPATH, 
            self._x + "//*[contains(@class,'highcharts-xaxis-labels')]/span")
        labels.sort(key=lambda e: float(re.search(".*top:\s([0-9]*[.]*[0-9]*)px.*",
                                                  e.get_attribute("style")).group(1)), reverse=True)
        return [label.text for label in labels]

    @WebAction()
    def _get_y_axis_labels(self):
        """Fetches the y-axis labels"""
        labels = self._driver.find_elements(By.XPATH, 
            self._x + "//*[contains(@class,'highcharts-yaxis-labels')]/span")
        labels.sort(key=lambda e: float(re.search(".*left:\s([0-9]*[.]*[0-9]*)px.*",
                                                  e.get_attribute("style")).group(1)))
        return [label.text for label in labels]


class LineChartViewer(RectangularChartViewer):
    """This class contains all the viewer actions specific to Line Chart"""

    @WebAction()
    def _get_count(self):
        """Fetch slice count"""
        points = self._driver.find_elements(By.XPATH, self._x + "//*[name()='path' and @aria-label]")
        return len(points)

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(By.XPATH, self._x + "//*[name()='path' and @aria-label]")
        return [re.search("(.*,\s)(.*).", bar.get_attribute('aria-label')).group(2) for bar in bars]


class TimelineChartViewer(RectangularChartViewer):
    """This class contains all the viewer actions specific to Timeline Chart"""

    @WebAction()
    def _get_count(self):
        """Fetch slice count"""
        points = self._driver.find_elements(By.XPATH, self._x + "//*[name()='path' and @aria-label]")
        return len(points)

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(By.XPATH, self._x + "//*[name()='path' and @aria-label]")
        return [re.search("(.*,\s)(.*).", bar.get_attribute('aria-label')).group(2) for bar in bars]


class ChartProperties(CRComponentProperties):
    """Actions common to Chart Properties goes here"""


class _CommonChartProperties(ChartProperties):

    @WebAction()
    def __expand_custom_group(self):
        """Expands custom group."""
        expand_tab = self._driver.find_element(By.XPATH, "//span[contains(.,'Custom Groups')]")
        expand_tab.click()

    @WebAction()
    def __toggle_custom_group_for_field(self, field):
        """Toggle on custom group."""
        toggle = self._driver.find_element(By.XPATH, f"//label[@title='{field}']/..//*[@for]")
        toggle.click()

    @WebAction()
    def __click_edit_custom_group(self, field):
        """Clicks edit."""
        edit = self._driver.find_element(By.XPATH, 
            f"//label[@title='{field}']/..//*[contains(@class,'ico ico-pencil')]")
        edit.click()

    @WebAction()
    def __click_add_group_button(self):
        """Clicks 'Add' button under custom group."""
        button = self._driver.find_element(By.XPATH, "//button[contains(.,'Add Group')]")
        button.click()

    @WebAction()
    def __set_group_name(self, group_name):
        """Sets the custom group name."""
        groups = self._driver.find_elements(By.XPATH, "//input[@data-ng-model='group.groupName']")
        group = groups[len(groups) - 1]
        group.click()
        group.send_keys(group_name)

    @WebAction()
    def __set_group_values(self, group_values):
        """Sets the custom group values."""
        groups = self._driver.find_elements(By.XPATH, "//input[@data-ng-model='group.groupValues']")
        group = groups[len(groups) - 1]
        group.click()
        group.send_keys(group_values)

    @WebAction()
    def __click_apply(self):
        """Clicks apply."""
        button = self._driver.find_element(By.XPATH, 
            "//*[@data-ng-show='propData.additionalProperties']//button[contains(.,'Apply')]")
        button.click()

    @WebAction()
    def __toogle_show_top_right_tooltip(self):
        """toogle on show top right tooltip property"""
        tooltip = self._driver.find_element(By.XPATH, 
            "//label[text()='Show top right tooltip']/..//div[@class='on-off-switch']")
        tooltip.click()

    @PageService()
    def add_custom_group(self, field, groups):
        """Creates a new custom group.

        Args:
            field   (str):     Field on which the cudtom group is applied

            groups  (list):     Name of the group.

        """
        if not isinstance(groups, list):
            raise TypeError("Expected list")
        self._select_current_component()
        self._click_fields_tab()
        self.__expand_custom_group()
        self.__toggle_custom_group_for_field(field)
        self.__click_edit_custom_group(field)
        for group in groups:
            self.__click_add_group_button()
            self.__set_group_name(group[0])
            self.__set_group_values(group[1])
        self.__click_apply()
        self._webconsole.wait_till_load_complete()
        self.__expand_custom_group()

    @PageService()
    def enable_show_top_right_tooltip(self):
        """Enables show top right tooltip property"""
        self._select_current_component()
        self.__toogle_show_top_right_tooltip()


class HorizontalBarProperties(_CommonChartProperties):
    """This class contains all the Properties panel actions specific to Horizontal Bar"""


class VerticalBarProperties(_CommonChartProperties):
    """This class contains all the Properties panel actions specific to Vertical Bar"""


class PieChartProperties(_CommonChartProperties):
    """This class contains all the Properties panel actions specific to Pie Chart"""


class DonutChartProperties(_CommonChartProperties):
    """This class contains all the Properties panel actions specific to Donut Chart"""


class LineChartProperties(_CommonChartProperties):
    """This class contains all the Properties panel actions specific to Line Chart"""


class TimelineChartProperties(_CommonChartProperties):
    """This class contains all the Properties panel actions specific to Timeline Chart"""


class MailChart:
    """This class contains actions specific to chart present in mail body"""
    def __init__(self, driver, chart_id):
        """To initialize MailChart class

        Args:
            driver      (obj)   -- browser driver object

            chart_id    (str)   -- chart_id of the chart

        """
        self.driver = driver
        self.id = chart_id.replace("component_", "")
        self._x = "//*[@comp='%s']" % self.id

    @WebAction()
    def __get_chart_title(self):
        """
        Returns the chart title

        Args:
             None

        Returns:
            str  -- chart_title
        """
        chart_title = self.driver.find_element(By.XPATH, f"{self._x}/span").text
        return chart_title

    @PageService()
    def get_chart_title(self):
        """
        Gets the chart title of the given chart
        """
        return self.__get_chart_title()
