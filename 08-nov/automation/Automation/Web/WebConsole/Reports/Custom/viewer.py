from selenium.webdriver.common.by import By
"""
All the APIs necessary to use the Custom Report Viewer
"""

from Web.Common.page_object import (
    WebAction,
    PageService
)

from Web.WebConsole.Reports.Custom.builder import BaseReportPage
from Web.WebConsole.Reports.Custom.inputs import HTMLController
from Web.WebConsole.Reports.cte import CustomSecurity
from Web.WebConsole.Reports.report import FileMenu
from Web.WebConsole.Reports.report import Report
from selenium.webdriver.common.action_chains import ActionChains

from ._components import base
from ._components.table import (
    DataTableViewer,
    ColumnInViewer,
    ButtonInViewer,
    TableViewer
)
from ._components.form import (
    DateRangeViewer,
    SearchBarViewer
)
from ._components.chart import (
    HorizontalBarViewer,
    LineChartViewer,
    TimelineChartViewer,
    RectangularChartViewer,
    CircularChartViewer
)
from ._components.other import (
    HtmlComponentViewer,
    RComponentViewer,
    HitsViewer,
    FacetViewer
)


class CustomReportViewer(BaseReportPage, Report):

    """All the custom report viewer specific actions go here"""

    @property
    def report_type(self):
        return "CustomReport"

    @WebAction()
    def __read_report_name(self):
        """Read report name"""
        report_title = self._driver.find_element(By.XPATH, 
            "//*[@model='customReport.report.customReportName']"
        )
        return report_title.text

    @WebAction()
    def __click_edit(self):
        """Click edit on file menu"""
        edit_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='editLink']"
        )
        edit_btn.click()

    @WebAction()
    def __read_report_description(self):
        """ Read report description. """
        report_description = self._driver.find_element(By.XPATH, "//div[@id='crdescription']")
        return report_description.text.strip()

    @WebAction()
    def __click_delete(self):
        """Click delete on file menu"""
        delete_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='deleteButton']"
        )
        delete_btn.click()

    @WebAction()
    def __fetch_all_page_title_names(self):
        """Returns all page titles"""
        list_ = self._driver.find_elements(By.XPATH, "//li[not(contains(@class,'ng-hide'))]/div[@class = 'ng-binding']")
        return [title.get_attribute("title") for title in list_]

    @WebAction()
    def __fetch_all_report_table_names(self):
        """Returns all table names in that page"""
        list_ = self._driver.find_elements(By.XPATH, "//li[@data-component-type='TABLE']//span[contains(@class,'tileHelpLabels')]")
        return [title.text for title in list_]

    @WebAction()
    def __fetch_all_required_input_names(self):
        """Returns all required input names in that page"""
        list_ = self._driver.find_elements(By.XPATH, 
            "//*[contains(@class,'required-input')]")
        return [title.text for title in list_]

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
        if not isinstance(component, base.CRComponentViewer):
            raise ValueError("invalid component type")
        component.configure_viewer_component(self._webconsole, page, comp_id)

    @PageService()
    def associate_input(self, input_):
        """Associate input to viewer"""
        if not isinstance(input_, HTMLController):
            raise ValueError("Invalid input component")
        input_.configure(self._webconsole, _builder=False)

    @PageService()
    def edit_report(self):
        """Edit custom report"""
        file = FileMenu(self._webconsole)
        file.click_file_menu()
        self.__click_edit()

    @PageService()
    def delete_report(self):
        """Delete custom report"""
        file = FileMenu(self._webconsole)
        file.click_file_menu()
        self.__click_delete()
        self._click_yes_on_confirmation_popup()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_all_page_title_names(self):
        """Returns all page titles."""
        return self.__fetch_all_page_title_names()

    @PageService()
    def get_all_report_table_names(self):
        """Returns all page titles."""
        return self.__fetch_all_report_table_names()

    @PageService()
    def get_all_required_input_names(self):
        """Returns all required inputs in page"""
        return self.__fetch_all_required_input_names()

    @PageService()
    def open_security(self):
        """
        Opens Security panel

        Returns:
             security panel object
        """
        file = FileMenu(self._webconsole)
        file.click_file_menu()
        file.click_security()
        self._webconsole.wait_till_load_complete()
        return CustomSecurity(self._webconsole)


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


class PivotTable(TableViewer):
    """
    Dummy class to expose all the private Pivot Table APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """
    @property
    def type(self):
        """Returns:Category type as 'Table'"""
        return "PIVOT_TABLE"


class DateRange(DateRangeViewer):
    """
    Dummy class to expose all the private DateRange Viewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class SearchBar(SearchBarViewer):
    """
    Dummy class to expose all the private Search Viewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class VerticalBar(RectangularChartViewer):
    """
    Dummy class to expose all the private VerticalBar APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class HorizontalBar(HorizontalBarViewer):

    """
    Dummy class to expose all the private HorizontalBar APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """
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
        tooltip = self._driver.find_element(By.XPATH, "//div[contains(@class,'highcharts-tooltip')]")
        return tooltip.text

    @PageService()
    def get_tooltip_text(self):
        """gets tooltip text"""
        self._hover_over_bars()
        text = self._read_tooltip_text()
        return text


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


class HitsComponent(HitsViewer):
    """
    Dummy class to expose all the private HIT APIs as public

    For the builder and properties panel specific actions, refer builder.py file
    """


class FacetFilters(FacetViewer):
    """
    Dummy class to expose all the private HTML component APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class HtmlComponent(HtmlComponentViewer):
    """
    Dummy class to expose all the private HTML component APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class RComponent(RComponentViewer):
    """
    Dummy class to expose all the private R component APIs as public

    For the builder and properties panel specific actions, refer builder.py file
    """
