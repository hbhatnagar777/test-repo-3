from selenium.webdriver.common.by import By

from Web.AdminConsole.Reports.Custom.base_report import BaseReportPage
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.Custom.inputs import HTMLController
from Web.Common.page_object import WebAction, PageService

from ._components.chart import CircularChartViewer, RectangularChartViewer, LineChartViewer, TimelineChartViewer
from ._components.table import DataTableViewer, ColumnInViewer,ButtonInViewer
from ._components.base import CRComponentViewer

from ._components.other import (
    HtmlComponentViewer,
    HitsViewer,
    RComponentViewer,
)
from ._components.form import (
    DateRangeViewer,
    SearchBarViewer
)



class CustomReportViewer(BaseReportPage, Report):
    """All the custom report viewer specific actions go here"""

    @property
    def report_type(self):
        return "CustomReport"

    @WebAction()
    def __read_report_name(self):
        """Read report name"""
        report_title = self._driver.find_element(By.XPATH, "//*[contains(@class, 'rep-title-div')]")
        return report_title.text.strip()

    @WebAction()
    def __read_report_description(self):
        """ Read report description. """
        report_description = self._driver.find_element(By.XPATH, "//*[contains(@class, 'rep-desc')]")
        return report_description.text.strip()

    @WebAction()
    def __fetch_all_page_title_names(self):
        """Returns all page titles"""
        list_ = self._driver.find_elements(By.XPATH, "//button[contains(@class,' MuiTab-root')]")
        return [title.get_attribute("id") for title in list_]

    @WebAction()
    def __fetch_all_tabs(self):
        """
            get all the tabs from the report

            Returns: tab names (list)
        """
        if self.__is_tab():
            list_ = self._driver.find_elements(By.XPATH,
                                                   "//div[@data-component-type='TABS']//button[contains(@class,"
                                                   "' MuiTab-root')]")
            return [title.text.strip() for title in list_]

    @WebAction()
    def __is_tab(self):
        """Return true of tab else false """
        xpath = "//div[@data-component-type='TABS']//button[contains(@class,' MuiTab-root')]"
        result = self._driver.find_elements(By.XPATH, xpath)
        if result:
            return True
        return False

    @PageService()
    def is_tab(self):
        """find tab or page"""
        if self.__is_tab():
            return True
        return False

    @WebAction()
    def __fetch_all_report_table_names(self):
        """Returns all table names in that page"""
        list_ = self._driver.find_elements(By.XPATH, "//h2[@class='grid-title']//span")
        return [title.text for title in list_]

    @WebAction()
    def __fetch_all_required_input_names(self):
        """Returns all required input names in that page"""
        list_ = self._driver.find_elements(By.XPATH,
                                           "//*[contains(@class,'required-input')]")
        return [title.text for title in list_]

    @PageService()
    def get_all_required_input_names(self):
        """Returns all required inputs in page"""
        return self.__fetch_all_required_input_names()

    @PageService()
    def get_all_report_table_names(self):
        """Returns all page titles."""
        return self.__fetch_all_report_table_names()

    @PageService()
    def get_report_name(self):
        """Get report name"""
        return self.__read_report_name()

    @PageService()
    def get_report_description(self):
        """Get report description. """
        return self.__read_report_description()

    @PageService()
    def associate_component(self, component, page="Page0", comp_id=None):
        """Associate component to Viewer

        Args:
            component (CRComponentViewer): Any component which
                has a viewer implementation

            page (str): Page in which component is residing
            comp_id (str): component id from li tag comp attribute use this when no title exist but id is known

        """
        if not isinstance(component, CRComponentViewer):
            raise ValueError("invalid component type")
        component.configure_viewer_component(self._adminconsole, page, comp_id)

    @PageService()
    def associate_input(self, input_):
        """Associate input to viewer"""
        if not isinstance(input_, HTMLController):
            raise ValueError("Invalid input component")
        input_.configure(self._adminconsole, _builder=False)

    @PageService()
    def get_all_page_title_names(self):
        """Returns all page titles."""
        return self.__fetch_all_page_title_names()


class DataTable(DataTableViewer):

    """
    Dummy class to expose all the private DataTableViewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    Example::

        table = DataTable("tableName")
        rpt_viewer.associate_component(table)
        print(table.get_table_data())  # gets all the table data as JSON

    """
    Button = ButtonInViewer
    Column = ColumnInViewer


class VerticalBar(RectangularChartViewer):
    """
    Dummy class to expose all the private VerticalBar APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class HorizontalBar(RectangularChartViewer):

    """
    Dummy class to expose all the private HorizontalBar APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class PieChart(CircularChartViewer):
    """
    Dummy class to expose all the private PieChart APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class DonutChart(CircularChartViewer):
    """
    Dummy class to expose all the private DonutChart APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class LineChart(LineChartViewer):
    """
    Dummy class to expose all the private LineChart APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class TimelineChart(TimelineChartViewer):
    """
    Dummy class to expose all the private TimelineChart APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class HtmlComponent(HtmlComponentViewer):
    """
    Dummy class to expose all the private HTML component APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class HitsComponent(HitsViewer):
    """
    Dummy class to expose all the private HIT APIs as public

    For the builder and properties panel specific actions, refer builder.py file
    """


class RComponent(RComponentViewer):
    """
    Dummy class to expose all the private R component APIs as public

    For the builder and properties panel specific actions, refer builder.py file
    """


class SearchBar(SearchBarViewer):
    """
    Dummy class to expose all the private Search Viewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class DateRange(DateRangeViewer):
    """
    Dummy class to expose all the private DateRange Viewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """

