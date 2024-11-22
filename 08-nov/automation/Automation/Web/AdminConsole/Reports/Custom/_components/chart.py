import re
from abc import abstractmethod

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from Reports.Custom.sql_utils import SQLQueries
from Web.Common.page_object import (
    WebAction,
    PageService
)
from .base import CRComponentViewer


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
        title = self._driver.find_element(
            By.XPATH,
            f"{self._x}//*[name()='g' and contains(@class,'highcharts-axis highcharts-xaxis')]"
        )
        return title.text

    @WebAction()
    def _get_y_axis_title(self):
        """Fetches y axis title"""
        title = self._driver.find_element(
            By.XPATH,
            f"{self._x}//*[name()='g' and contains(@class,'highcharts-axis highcharts-yaxis')]"
        )
        return title.text

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(By.XPATH, self._x + "//*[name()='rect' and @aria-label]")
        return [re.search(r".*,\s(\S+)\.\s", bar.get_attribute('aria-label')).group(1) for bar in bars]

    @WebAction()
    def _get_x_axis_labels(self):
        """Fetches the x-axis labels"""
        labels = self._driver.find_elements(
            By.XPATH,
            f"{self._x}//*[contains(@class,'highcharts-xaxis-labels')]/*[name()='text']"
        )
        return [label.text for label in labels]

    @WebAction()
    def _get_y_axis_labels(self):
        """Fetches the y-axis labels"""
        labels = self._driver.find_elements(
            By.XPATH,
            f"{self._x}//*[contains(@class,'highcharts-yaxis-labels')]/*[name()='text']"
        )
        return [label.text for label in labels]

    @WebAction()
    def _hover_over_bars(self):
        """Hovers over the chart bars and returns tooltip"""
        bar = self._driver.find_element(By.XPATH, "//*[name()='rect' and contains(@class, 'highcharts-point')]")
        action_chain = ActionChains(self._driver)
        hover = action_chain.move_to_element(bar)
        hover.perform()

    @WebAction()
    def _read_tooltip_text(self):
        """Returns tooltip text"""
        tooltip = self._driver.find_element(By.XPATH, "//*[contains(@class,'highcharts-tooltip')]")
        return tooltip.text

    @PageService()
    def get_chart_details(self):
        """Fetches chart details"""
        heights = self._fetch_object_values()
        return {
            "x-axis_title": self._get_x_axis_title(),
            "y-axis_title": self._get_y_axis_title(),
            "count": len(heights),
            "height": heights,
            "x-axis_labels": self._get_x_axis_labels(),
            "y-axis_labels": self._get_y_axis_labels()
        }

    @PageService()
    def get_tooltip_text(self):
        """gets tooltip text"""
        self._hover_over_bars()
        text = self._read_tooltip_text()
        return text


class LineChartViewer(RectangularChartViewer):
    """This class contains all the viewer actions specific to Line Chart"""

    @WebAction()
    def _get_count(self):
        """Fetch slice count"""
        points = self._driver.find_elements(By.XPATH, f"{self._x}//*[name()='path' and @aria-label]")
        return len(points)

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(By.XPATH, f"{self._x}//*[name()='path' and @aria-label]")
        return [re.search(r".*,\s(\S+)\.\s", bar.get_attribute('aria-label')).group(1) for bar in bars]


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
        return [re.search(r".*,\s(\S+)\.\s", bar.get_attribute('aria-label')).group(1) for bar in bars]


class CircularChartViewer(ChartViewer):
    """This class contains the methods for one dimensional charts"""

    @WebAction()
    def _get_legend(self):
        """Get legend information"""
        legends = self._driver.find_elements(
            By.XPATH,
            f"{self._x}//*[contains(@class, 'highcharts-legend-item')]"
        )
        return [legend.text for legend in legends if legend.text]

    @WebAction()
    def _fetch_object_values(self):
        """Fetches the height of the bars"""
        bars = self._driver.find_elements(
            By.XPATH,
            f"{self._x}//*[name()='g' and contains(concat(' ', @class, ' '), ' highcharts-series ')]"
            f"//*[name()='path' and @aria-label]"
        )
        return [re.search(r".*,\s(\S+)\.\s", bar.get_attribute('aria-label')).group(1) for bar in bars]

    @WebAction()
    def __click_slice(self, slice_name):
        """Clicks the given slice"""
        slice_ = self._driver.find_element(
            By.XPATH,
            f"{self._x}//*[name()='path' and contains(@aria-label,'{slice_name}')]"
        )
        slice_.click()

    @PageService()
    def get_chart_legend(self):
        """Fetches chart legend values and Legend Text"""
        legends_text = self._get_legend()
        legend_values = []
        for legend in legends_text:
            legend_value = re.search(r".*:\s(\S+)\s.*", legend)
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
        self._adminconsole.wait_for_completion()


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
