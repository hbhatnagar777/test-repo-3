from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
All classes operations related to report builder which are not part
of reports, dataset or inputs tab reside in this module

Only classes present inside the __all__ variable should be
imported by TestCases and Utils, rest of the classes are for
internal use
"""

from abc import ABC
from time import sleep

from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

from Web.WebConsole.Reports.Custom.inputs import DataType
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    PageService,
    WebAction
)

from ._components.form import (
    DateRangeViewer,
    DateRangeBuilder,
    DateRangeProperties,
    SearchBarBuilder,
    SearchBarProperties,
    SearchBarViewer,
)
from ._components.base import (
    CRComponentBuilder,
    CRComponentProperties
)
from ._components.page import (
    PageViewer,
    PageProperties,
    PageBuilder
)
from ._components.table import (
    DataTableBuilder,
    DataTableViewer,
    DataTableProperties,
    Column,
    Button,
    PivotTableBuilder,
    TableViewer,
    TableProperties
)
from ._datasets import (
    Dataset,
    DatabaseDataset,
    HTTPDataset,
    ScriptDataset,
    JoinDataset,
    SharedDataset,
    RDataset
)
from ._components.chart import (
    VerticalBarProperties,
    HorizontalBarViewer,
    HorizontalBarProperties,
    DonutChartProperties,
    PieChartProperties,
    LineChartViewer,
    LineChartProperties,
    TimelineChartBuilder,
    TimelineChartViewer,
    TimelineChartProperties,
    RectangularChartBuilder,
    CircularChartBuilder,
    RectangularChartViewer,
    CircularChartViewer
)
from ._components.other import (
    HtmlComponentBuilder,
    HtmlComponentViewer,
    HtmlComponentProperties,
    RPlotBuilder,
    RComponentViewer,
    RComponentProperties
)
from ._localization import Localization


class BaseReportPage(ABC):
    """
    Common operations for CustomReport Viewer and Builder
    """

    def __init__(self, webconsole):
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def __get_all_component_titles(self):
        """Get all component titles"""
        titles = self._driver.find_elements(By.XPATH, 
            """//li[@comp]//div[contains(@id,'component-title')]/span"""
        )
        return [title.text for title in titles]

    @WebAction()
    def __click_page(self, page_name):
        """Clicks the given page in the report builder.

        Args:
            page_name    --  Name of the page.

        """
        page = self._driver.find_element(By.XPATH, "//div[@title = '%s']" % page_name)
        page.click()

    @WebAction(delay=3)
    def _click_yes_on_confirmation_popup(self):
        """Click Yes on confirmation popup"""
        yes_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='confirmModal']//*[.='Yes']")
        yes_btn.click()

    @WebAction()
    def __click_no_on_confirmation_popup(self):
        """Click No on deploy popup"""
        no_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='confirmModal']//*[.='No']")
        no_btn.click()

    @WebAction()
    def __get_all_input_names(self):
        """Get the name of all the inputs"""
        return [
            ip.get_attribute("data-input-displayname") for ip in
            self._driver.find_elements(By.XPATH, "//*[@data-input-displayname]")
            if ip.is_displayed()
        ]

    @PageService()
    def switch_page(self, page):
        """Switches to the desired page in the report builder.

        Args:
            page   --  Page Object

        """
        self.__click_page(page.page_name)

    def get_all_component_titles(self, page=None):
        """Returns the title of all custom report components

        Return:
            (list): Text containing all component names
        """
        if page:
            self.switch_page(page)
        return self.__get_all_component_titles()

    @PageService()
    def get_all_input_names(self):
        """Get all the available input names"""
        return self.__get_all_input_names()


class ReportBuilder(BaseReportPage):
    """
    This class holds the APIs necessary to work with the Custom Report Builder
    """

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): WebConsole instance
        """
        super().__init__(webconsole)
        self._inputs = []
        self._dataset = []
        self._titles = []

    @WebAction()
    def __click_dataset_tab(self):
        """Click the Dataset tab"""
        tab = self._driver.find_element(By.XPATH, 
            "//*[@id='leftCol']//*[.='Dataset']")
        self._browser.click_web_element(tab)

    @WebAction()
    def __click_report_tab(self):
        """Click the Report tab"""
        tab = self._driver.find_element(By.XPATH, 
            "//*[@id='leftCol']//*[.='Report']")
        self._browser.click_web_element(tab)

    @WebAction(delay=3)
    def __click_add_ui_tags(self):
        """Click UI Tags"""
        button = self._driver.find_element(By.XPATH, 
            "//*[text()='UI Tags']/following-sibling::*[1]"
        )
        button.click()

    @WebAction()
    def __click_tags_dropdown(self):
        """Click UI Tags type dropdown button"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[text()='UI Tags']/../../following-sibling::*[contains(@data-ng-repeat,'uiTag')][last()]"
        )
        dropdown.click()

    @WebAction(delay=3)
    def __click_tags_type_on_dropdown(self, tag_type):
        """Click Dataset type on the dropdown"""
        try:
            buttons = self._driver.find_element(By.XPATH, 
            "//*[text()='UI Tags']/../../following-sibling::*[contains(@data-ng-repeat,'uiTag')][last()]"
            "/descendant::option[text()='%s']" % tag_type)
            buttons.click()
        except NoSuchElementException as exp:
            # Tag doesnt exist enter manually
            xp = "//*[text()='UI Tags']/../../following-sibling::*[contains(@data-ng-repeat,'uiTag')][last()]//input"
            tag_input = self._driver.find_element(By.XPATH, xp)
            tag_input.send_keys(tag_type)

    @WebAction()
    def __click_add_dataset(self):
        """Click Add Dataset"""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='leftCol']//*[.='Data Sets']"
            "/following-sibling::*[.='Add']")
        button.click()

    @WebAction()
    def __click_input_tab(self):
        """Click the input tab"""
        tab = self._driver.find_element(By.XPATH, 
            "//*[@id='leftCol']//*[.='Inputs']")
        self._browser.click_web_element(tab)

    @WebAction(delay=2)
    def __click_add_input(self):
        """Click Add Input"""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='leftCol']//*[contains(.,'Inputs')]"
            "/following-sibling::*/*[.='Add']")
        button.click()

    @WebAction()
    def __click_add_new_page(self):
        """Click 'Add New Page' button"""
        button = self._driver.find_element(By.XPATH, "//li[@title = 'Add New Page']")
        button.click()

    @WebAction()
    def __click_page_title(self, page):
        """Click Page title text"""
        title = self._driver.find_element(By.XPATH, 
            "//*[@id='centerCol']//*[@title='%s']" % page)
        title.click()

    @WebAction()
    def __click_refresh(self):
        """Click refresh button"""
        refresh_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='refreshButton']"
        )
        refresh_btn.click()

    @WebAction()
    def __click_save(self):
        """Click Save option on builder"""
        save_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='saveButton']")
        save_btn.click()

    @WebAction()
    def __click_deploy(self):
        """Click deploy on builder"""
        deploy_button = self._driver.find_element(By.XPATH, 
            "//*[@id='deployButton']"
        )
        deploy_button.click()

    @WebAction()
    def __click_no_on_confirmation_popup(self):
        """Click No on deploy popup"""
        no_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='confirmModal']//*[.='No']")
        no_btn.click()

    @WebAction()
    def __click_under_action(self, button):
        """Clicks the given button under the actions drop down"""
        btn = self._driver.find_element(By.XPATH, f"//*[text()='{button}']")
        btn.click()

    @WebAction()
    def __click_actions(self):
        """Click Actions button"""
        actions_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='actionsButton']")
        actions_btn.click()

    @WebAction()
    def __click_delete_dataset(self, name):
        """Click delete dataset"""
        delete_arrow = self._driver.find_element(By.XPATH, 
            f"//li[@data-datasetname='{name}']//*[@title='Delete']"
        )
        delete_arrow.click()

    @WebAction()
    def __click_open_report(self):
        """Click open report"""
        open_btn = self._driver.find_element(By.XPATH, 
            "//*[@id='openReportButtonLabel']"
        )
        open_btn.click()

    @WebAction(delay=5)
    def __drag_component(self, category, name):
        """Drag component to builder workspace"""
        self._browser.drag_and_drop_by_xpath(
            "//*[@id='rightCol']//*[@title='%s']//*[.='%s']" % (
                category, name),
            "//*[@id='lowerPaddingDiv']")

    @WebAction()
    def __edit_dataset(self, name):
        """Edit dataset"""
        edit_arrow = self._driver.find_element(By.XPATH, 
            f"//li[@data-datasetname='{name}']//*[@title='Edit']"
        )
        edit_arrow.click()

    @WebAction()
    def __set_report_name(self, name):
        """Type name into Report Name TextBox"""
        textbox = self._driver.find_element(By.XPATH, 
            "//*[@id='sectionTitle']/input")
        textbox.clear()
        textbox.send_keys(name)

    @WebAction()
    def __set_report_description(self, description):
        """Set Report Description"""
        text_area = self._driver.find_element(By.XPATH, "//textarea[@title='Description']")
        text_area.clear()
        text_area.send_keys(description)

    @WebAction(log=False, delay=4)
    def __is_builder_faded(self):
        """Check if builder is faded because of any popup"""
        overlay = self._driver.find_elements(By.XPATH, 
            "//*[@class='modal-backdrop fade ng-scope in']")
        return len(overlay) > 0

    @WebAction(log=False, delay=2)
    def __read_active_component_id(self):
        """Retrieve component ID"""
        id_field = self._driver.find_element(By.XPATH, 
            "//*[@id='propertiesArea']//*[.='ID']/following-sibling::*/input")
        return id_field.get_attribute("value")

    @WebAction()
    def __get_report_version(self):
        """ Get report version."""
        report_version = self._driver.find_element(By.XPATH, 
            "//span[@data-ng-bind ='customReport.reportVersion']")
        return report_version.text

    @WebAction()
    def __get_deployed_version(self):
        """Get deployed version. """
        deployed_version = self._driver.find_element(By.XPATH, 
            "//span[@data-ng-bind ='customReport.deployedVersion']")
        return deployed_version.text

    @WebAction()
    def __click_open_report(self):
        """Clicks open report button"""
        report = self._driver.find_element(By.XPATH, "//div[@id='openReportButton']")
        return report.click()

    @WebAction()
    def __click_visualization(self):
        """Clicks visualization tab. """
        visualization = self._driver.find_element(By.XPATH, "//span[@title='Visualization']")
        visualization.click()

    @WebAction()
    def __click_properties(self):
        """Clicks properties tab. """
        properties = self._driver.find_element(By.XPATH, "//div[@title='Properties']")
        properties.click()

    @WebAction()
    def __toggle_show_pages_as_tabs(self):
        """Toggles 'Show pages as Tabs'."""
        toggle = self._driver.find_element(By.XPATH, "//label[@for='pagesAsTabs']")
        toggle.click()

    @WebAction()
    def __click_localization(self):
        """Clicks localization"""
        localization = self._driver.find_element(By.XPATH, "//span[contains(text(),'Localization')]")
        localization.click()

    @WebAction()
    def __click_view_or_edit_localizable_string(self):
        """Clicks 'view or edit localizable string'"""
        link = self._driver.find_element(By.XPATH, "//*[contains(text(),'View or Edit Localizable String')]")
        link.click()

    @WebAction()
    def __click_software_store_settings(self):
        """Clicks Software store settings"""
        store_settings = self._driver.find_element(By.XPATH, "//span[contains(text(),'Software Store Settings')]")
        store_settings.click()

    @WebAction(delay=1)
    def _set_feature_release(self, feature_release):
        """Click feature release in the dropdown"""
        fr = self._driver.find_element(By.XPATH, 
            "//label[text()='Feature Release']/..//*[contains(@data-ng-model,'minCommCellVersion.servicePack')]")
        fr.send_keys(feature_release)

    @PageService()
    def add_component(self, component, dataset, page="Page0"):
        """Add report component to builder"""
        if not isinstance(component, (CRComponentBuilder, CRComponentProperties)):
            raise TypeError("Invalid component type")
        if page != "Page0":
            self.__click_page_title(page)
        self.__click_visualization()
        self.__drag_component(component.category, component.name)
        id_ = self.__read_active_component_id()
        component.configure_builder_component(self._webconsole, dataset.dataset_name, page, id_)
        component.set_component_title(component.title)

    @PageService()
    def associate_page(self, page):
        """Associates the given page"""
        page.configure_builder_component(
            self._webconsole, None, page.title, None)

    @PageService()
    def enable_show_pages_as_tabs(self):
        """Shows multiple pages in the report as separate tabs."""
        self.__click_report_tab()
        self.__toggle_show_pages_as_tabs()

    @PageService()
    def add_dataset(self, dataset):
        """Adds Dataset to the Builder

        Args:
            dataset (Dataset): Any valid dataSet instance
        """
        if not isinstance(dataset, Dataset):
            raise TypeError("Invalid dataset argument")

        self.__click_dataset_tab()
        sleep(3)
        self.__click_add_dataset()
        sleep(4)
        dataset.configure_dataset(self._webconsole)
        self._dataset.append(dataset)

    @PageService()
    def add_tags(self, tags):
        """Add UI Tags to report"""
        self.__click_report_tab()
        sleep(4)
        for tag_type in tags:
            self.__click_add_ui_tags()
            self.__click_tags_type_on_dropdown(tag_type)

    @PageService()
    def export_report_template(self):
        """Export Report Template in XML"""
        self.__click_actions()
        self.__click_under_action("Export Template")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def add_input(self, input_, page="Page0"):
        """Add input using report builder

        Please be careful to add input datatype and not HTML Controller
        """
        if not isinstance(input_, DataType):
            raise TypeError("Invalid input argument")

        if page != "Page0":
            self.__click_page_title(page)
        self.__click_input_tab()
        self.__click_add_input()
        self._webconsole.wait_till_load_complete()
        sleep(2)
        input_.configure(self._webconsole)
        self._inputs.append(input_)

    @PageService()
    def add_new_page(self, page):
        """Adds new page"""
        if not isinstance(page, CRComponentBuilder):
            raise TypeError("Invalid component type")
        self.__click_add_new_page()
        page.configure_builder_component(
            self._webconsole, None, page.title, None)

    @PageService()
    def delete_dataset(self, name):
        """Delete dataset"""
        self.__click_dataset_tab()
        self.__click_delete_dataset(name)
        sleep(2)
        self._click_yes_on_confirmation_popup()
        sleep(2)

    @PageService()
    def edit_dataset(self, dataset):
        """Edit dataset"""
        if not isinstance(dataset, Dataset):
            raise TypeError("Expecting dataset object, invalid object type received.")
        self.__click_dataset_tab()
        self.__edit_dataset(dataset.dataset_name)
        dataset.configure_dataset(self._webconsole)
        sleep(2)

    @PageService()
    def open_report(self):
        """Open report"""
        self.__click_open_report()
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_report_name(self, name):
        """Set Report Name"""
        self.__click_report_tab()
        self.__set_report_name(name)

    @PageService()
    def set_report_description(self, description):
        """Set Report Description"""
        self.__click_report_tab()
        self.__set_report_description(description)

    @PageService()
    def refresh(self):
        """Refresh builder components"""
        self.__click_refresh()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def save(self, deploy=False):
        """Save the report"""
        self._webconsole.clear_all_notifications()
        self.__click_save()
        sleep(5)
        if self.__is_builder_faded():
            if deploy:
                sleep(2)
                self._click_yes_on_confirmation_popup()
                deploy = False
            else:
                self.__click_no_on_confirmation_popup()
        notifications = self._webconsole.get_all_error_notifications()
        if notifications:
            raise CVWebAutomationException(
                f"Save report failed with [{notifications}]"
            )
        if deploy:
            self.deploy()
        sleep(1)

    @PageService()
    def deploy(self):
        """Deploys the report."""
        self._webconsole.clear_all_notifications()
        self.__click_deploy()
        self._webconsole.wait_till_load_complete(unfade=True)
        notifications = self._webconsole.get_all_error_notifications()
        if notifications:
            raise CVWebAutomationException(
                f"Deploy report failed with [{notifications}]"
            )
        sleep(1)

    def save_and_deploy(self):
        """* DEPRECATED FUNCTION *

        DO NOT USE THIS, USE `self.save(deploy=True)` INSTEAD
        """
        self.save(deploy=True)

    @PageService()
    def get_report_version(self):
        """Fetches the Report Version. """
        return self.__get_report_version()

    @PageService()
    def get_deployed_version(self):
        """Fetches the Deployed Version. """
        return self.__get_deployed_version()

    @PageService()
    def goto_report_manager(self):
        """Open report manager from builder"""
        self.__click_actions()
        self.__click_under_action("Report Manager")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def export_preview(self):
        """Open report manager from builder"""
        self.__click_actions()
        self.__click_under_action("Export Preview")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def add_localization(self, localization):
        """Adds Localization to the report"""
        if not isinstance(localization, Locale):
            raise TypeError("Expecting Locale object, invalid object type received.")
        self.__click_report_tab()
        self.__click_localization()
        self.__click_view_or_edit_localizable_string()
        localization.configure_localization(self._webconsole)

    @PageService()
    def add_feature_release(self, feature_release):
        """Adds Localization to the report"""
        self.__click_report_tab()
        sleep(4)
        self.__click_software_store_settings()
        self._set_feature_release(feature_release)


class Datasets:
    """Public reference to all the datasets available in the DataSet dialogue"""

    DatabaseDataset = DatabaseDataset
    HTTPDataset = HTTPDataset
    ScriptDataset = ScriptDataset
    JoinDataset = JoinDataset
    SharedDataset = SharedDataset
    RDataset = RDataset


class DataTable(DataTableViewer, DataTableBuilder, DataTableProperties):
    """
    Dummy class to reference all the Data Table operations
    available on the report Builder
    """
    Column = Column
    Button = Button


class PivotTable(PivotTableBuilder, TableViewer, TableProperties):
    """
    Dummy class to reference all the Pivot Table operations
    available on the report Builder
    """
    @property
    def type(self):
        """Returns:Category type as 'Table'"""
        return "PIVOT_TABLE"


class Page(PageBuilder, PageViewer, PageProperties):
    """
    Dummy class to reference all the Page Operations
    available on the report Builder
    """


class Locale(Localization):
    """public Reference to Localization"""


class DateRange(DateRangeProperties, DateRangeBuilder, DateRangeViewer):
    """
    Dummy class to reference all the Daterange Operations inside a DateRange
    available on the report Builder
    """


class SearchBar(SearchBarBuilder, SearchBarViewer, SearchBarProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Search Bar
    available on the report Builder
    """


class VerticalBar(RectangularChartBuilder, RectangularChartViewer, VerticalBarProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Vertical Bar
    available on the report Builder
    """
    @property
    def category(self):
        """
        Returns:Category type as 'Chart'
        """
        return "Chart"

    @property
    def name(self):
        """
        Returns:Name as 'Vertical Bar'
        """
        return "Vertical Bar"


class HorizontalBar(RectangularChartBuilder, HorizontalBarViewer, HorizontalBarProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Horizontal Bar
    available on the report Builder
    """
    @property
    def category(self):
        """
        Returns:Category type as 'Chart'
        """
        return "Chart"

    @property
    def name(self):
        """
        Returns:Name as 'Horizontal Bar'
        """
        return "Horizontal Bar"


class PieChart(CircularChartBuilder, CircularChartViewer, PieChartProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Pie Chart
    available on the report Builder
    """
    @property
    def category(self):
        """
        Returns:Category type as 'Chart'
        """
        return "Chart"

    @property
    def name(self):
        """
        Returns:Name as 'Pie Chart'
        """
        return "Pie Chart"


class DonutChart(CircularChartBuilder, CircularChartViewer, DonutChartProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Pie Chart
    available on the report Builder
    """
    @property
    def category(self):
        """
        Returns:Category type as 'Chart'
        """
        return "Chart"

    @property
    def name(self):
        """
        Returns:Name as 'Donut'
        """
        return "Donut"


class LineChart(RectangularChartBuilder, LineChartViewer, LineChartProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Line Chart
    available on the report Builder
    """
    @property
    def category(self):
        """
        Returns:Category type as 'Chart'
        """
        return "Chart"

    @property
    def name(self):
        """
        Returns:Name as 'Line Chart'
        """
        return "Line Chart"


class TimelineChart(TimelineChartBuilder, TimelineChartViewer, TimelineChartProperties):
    """
    Dummy class to reference all the SearchBar Operations inside a Timeline Chart
    available on the report Builder
    """


class HtmlComponent(HtmlComponentBuilder, HtmlComponentViewer, HtmlComponentProperties):
    """
    Dummy class Html component available in builder
    """


class RComponent(RPlotBuilder, RComponentViewer, RComponentProperties):
    """
    Dummy class RPlot component available in builder
    """
