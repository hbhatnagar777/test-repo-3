from selenium.webdriver.common.by import By
"""
All the options accessed from Dataset tab go to this module

Only classes present inside the __all__ variable should be
imported by TestCases and Utils, rest of the classes are for
internal use
"""

from abc import (
    ABC,
    abstractmethod
)
from time import sleep

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import Select

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.Reports.Custom.inputs import DataType
from ._components.table import PreviewTable


class Dataset(ABC):
    """Base dataset class for all the dataset tabs"""

    _DATASET_DROPDOWN = "//*[@id='dropdownMenu1']"

    def __init__(self):
        self.__webconsole = None
        self.__browser = None
        self.__driver = None
        self._dataset_name = None

    @property
    def dataset_name(self):
        if self._dataset_name is None:
            raise ValueError("Dataset name not available")
        return self._dataset_name

    @dataset_name.setter
    def dataset_name(self, value):
        self._dataset_name = value

    @property
    def _webconsole(self):
        if self.__webconsole is None:
            raise ValueError(
                "Dataset not initialized, was Builder.add_dataset called ?"
            )
        return self.__webconsole

    @property
    def _browser(self):
        if self.__browser is None:
            raise ValueError(
                "Dataset not initialized, was Builder.add_dataset called ?"
            )
        return self.__browser

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError(
                "Dataset not initialized, was Builder.add_dataset called ?"
            )
        return self.__driver

    @WebAction()
    def __click_preview_button(self):
        """Click preview button on Dataset"""
        button = self._driver.find_element(By.XPATH, 
            "//*[@class='previewButtonPanel']/*[.='Preview']")
        button.click()

    @WebAction()
    def __click_done(self):
        """Click Done button"""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetModal']//*[@data-ng-click='addDataSet()']"
        )
        button.click()

    @WebAction()
    def __click_save_deploy(self):
        """Click Done button"""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetModal']//*[@data-ng-click='saveAndDeploy()']"
        )
        button.click()

    @WebAction()
    def __click_dataset_type_on_dropdown(self):
        """Click Dataset type on the dropdown"""
        buttons = self._driver.find_element(By.XPATH, 
            "%s/..//*[text()='%s']" % (
                Dataset._DATASET_DROPDOWN, self._dataset_type))
        buttons.click()

    @WebAction()
    def __click_dataset_dropdown(self):
        """Click Dataset type dropdown button"""
        dropdown = self._driver.find_element(By.XPATH, 
            Dataset._DATASET_DROPDOWN)
        dropdown.click()

    @property
    @abstractmethod
    def _dataset_type(self):
        """Override this method and implement it as a variable whose
        value is set to the exact string on the Dataset type dropdown"""
        raise NotImplementedError

    @PageService()
    def configure_dataset(self, webconsole):
        """Configure dataset

        DO NOT CALL THIS METHOD, this method is for internal use, to
        add dataset, call add_dataset method on builder
        """
        self.__webconsole = webconsole
        self.__browser = webconsole.browser
        self.__driver = webconsole.browser.driver
        self.__click_dataset_dropdown()
        self.__click_dataset_type_on_dropdown()

    @PageService()
    def get_preview_data(self):
        """Get the previewed data"""
        self.__click_preview_button()
        table = PreviewTable()
        table.configure_viewer_component(self._webconsole)
        self._webconsole.wait_till_load_complete(comp_load=False)
        return table.get_table_data()

    @PageService()
    def save(self):
        """Save the dataset"""
        self.__click_done()
        self._webconsole.wait_till_load_complete(unfade=True)

    @PageService()
    def save_and_deploy(self):
        """Save and deploy the dataset"""
        self.__click_save_deploy()
        self._webconsole.wait_till_load_complete(unfade=True)

    def __str__(self):
        return f"""<Dataset type=[{self._dataset_type}] id=[{id(self)}]>"""


class _FieldsTab(Dataset):
    """ All operations in fields tab common to all datasets go here"""

    _FIELD_NAMES_XPATH = "//input[@*='field.name' and (not(contains(@class,'field')))]"

    @WebAction()
    def _click_fields_tab(self):
        """Clicks on fields tab."""
        tab = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetLeftPane']//*[contains(text(),'Fields')]"
        )
        tab.click()

    @WebAction()
    def __click_add_fields_button(self):
        """Clicks on 'Add' button."""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='fieldButtonWrapper']/*[contains(., 'Add')]"
        )
        button.click()

    @WebAction()
    def __click_delete_fields_button(self):
        """Clicks on 'Delete' button."""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='fieldButtonWrapper']/*[contains(., 'Delete')]"
        )
        button.click()

    @WebAction()
    def __click_fields_down_button(self):
        """Clicks on down arrow button."""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='fieldButtonWrapper']/*[@title='Move field down']"
        )
        button.click()

    @WebAction()
    def __click_fields_up_button(self):
        """Clicks on up arrow button."""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='fieldButtonWrapper']/*[@title='Move field up']"
        )
        button.click()

    @WebAction()
    def __click_field(self, field_name):
        """Click field"""
        columns = self._driver.find_elements(By.XPATH, 
            _FieldsTab._FIELD_NAMES_XPATH
        )
        clicked_columns = [
            column.click()
            for column in columns
            if column.get_attribute("value") == field_name
        ]
        if len(clicked_columns) != 1:
            raise WebDriverException(
                msg=f"Unable to click on textbox with value [{field_name}]"
            )

    @WebAction()
    def __set_selected_field_name(self, field_name):
        """Rename field"""
        text_box = self._driver.find_element(By.XPATH, 
            "//*[contains(@class, 'current')]" + _FieldsTab._FIELD_NAMES_XPATH
        )
        text_box.clear()
        text_box.send_keys(field_name)

    @WebAction()
    def __get_field_names(self):
        """Fetches all field names"""
        columns = self._driver.find_elements(By.XPATH, 
            _FieldsTab._FIELD_NAMES_XPATH
        )
        return [column.get_attribute("value") for column in columns]

    @WebAction()
    def __click_all_fields(self):
        """Clicks on 'All Fields' radio button."""
        radio = self._driver.find_element(By.XPATH, 
            "//label[contains(., 'All Fields')]"
        )
        radio.click()

    @WebAction()
    def __click_show_specific_fields(self):
        """Clicks on 'Show Specific Fields' radio button."""
        radio = self._driver.find_element(By.XPATH, 
            "//label[contains(., 'Show Specific Fields')]"
        )
        radio.click()

    @WebAction()
    def __click_last_field_name(self):
        """Click last field"""
        field_objects = self._driver.find_elements(By.XPATH, 
            _FieldsTab._FIELD_NAMES_XPATH
        )
        if field_objects:
            field_objects[-1].click()
        else:
            raise WebDriverException("Not fields found to click")

    @PageService()
    def enable_all_fields(self):
        """Switch to 'All Fields'."""
        self._click_fields_tab()
        self.__click_all_fields()

    @PageService()
    def enable_show_specific_fields(self):
        """Switch to 'Show Specific Fields'"""
        self._click_fields_tab()
        self.__click_show_specific_fields()

    @PageService()
    def add_field(self, field_name):
        """Adds a new row"""
        self._click_fields_tab()
        self.__click_add_fields_button()
        self.__click_last_field_name()
        self.__set_selected_field_name(field_name)

    @PageService()
    def delete_field(self, field_name):
        """Delete a specific row"""
        self._click_fields_tab()
        self.__click_field(field_name)
        self.__click_delete_fields_button()

    @PageService()
    def move_field_up(self, field_name):
        """Moves up a specific row"""
        self._click_fields_tab()
        self.__click_field(field_name)
        self.__click_fields_up_button()

    @PageService()
    def move_field_down(self, field_name):
        """Moves down a specific row"""
        self._click_fields_tab()
        self.__click_field(field_name)
        self.__click_fields_down_button()

    @PageService()
    def rename_field(self, field_source, field_name):
        """Rename field"""
        self._click_fields_tab()
        self.__click_field(field_source)
        self.__set_selected_field_name(field_name)

    @PageService()
    def get_fields_names(self):
        """Get field names"""
        self._click_fields_tab()
        return self.__get_field_names()


class _DatasetQueryTab(Dataset):
    """Class to hold the common functions for all datasets"""

    @WebAction()
    def _click_dataset_query_tab(self):
        """Click on Query tab"""
        tab = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetLeftPane']//li[contains(., 'Query')]")
        tab.click()

    @WebAction()
    def __set_dataset_name_textbox(self, name):
        """Type Dataset name on textbox"""
        txt_box = self._driver.find_element(By.XPATH, 
            "//label[.='Data Set Name']/following-sibling::*/input")
        txt_box.clear()
        txt_box.send_keys(name)

    @WebAction()
    def _set_query(self, sql):
        """Type the SQL Query in TextArea"""
        textarea = self._driver.find_element(By.XPATH, 
            "//label[.='Query']/../following-sibling::*/textarea")
        textarea.clear()
        textarea.send_keys(sql)

    @PageService()
    def set_dataset_name(self, name):
        """Set the name of Dataset"""
        self._dataset_name = name
        self._click_dataset_query_tab()
        self.__set_dataset_name_textbox(self.dataset_name)


class _SQLQueryDataset(_DatasetQueryTab):
    """Common class to hold the Query operations for
    Database, Script and Dataset datasets"""

    @PageService(hide_args=True)
    def set_sql_query(self, sql):
        """Set the SQL Query"""
        self._click_dataset_query_tab()
        self._set_query(sql)


class _DatabaseDatasetQueryTab(_SQLQueryDataset):
    """Database Dataset type used for mixin"""


class _HTTPDatasetQueryTab(_DatasetQueryTab):
    """
    HTTP Dataset type containing HTTP Dataset specific functionalities
    used for mixin
    """

    _ROW_EXPRESSION = "//label[.='Row Expression']/following-sibling::*/input"

    @WebAction()
    def __set_rest_textfield(self, rest):
        """Enter REST API TextField"""
        textboxes = self._driver.find_elements(By.XPATH, 
            "//label[contains(text(),'REST')]/following-sibling::*/input")
        for textbox in textboxes:
            if textbox.is_displayed():
                textbox.clear()
                textbox.send_keys(rest)
                break
        else:
            raise CVWebAutomationException("Element Not Visible")

    @WebAction()
    def __set_http_content_textarea(self, http_content):
        """Enter HTTP Content TextField"""
        textbox = self._driver.find_element(By.XPATH, 
            "//label[.='HTTP Content']/../following-sibling::*/textarea")
        textbox.clear()
        textbox.send_keys(http_content)

    @WebAction()
    def __set_row_expression(self, expression):
        """Enter row expression in TextBox"""
        textbox = self._driver.find_element(By.XPATH, 
            _HTTPDatasetQueryTab._ROW_EXPRESSION)
        textbox.clear()
        textbox.send_keys(expression)

    @WebAction()
    def __click_json_content_type(self):
        """Click JSON Content Type Button"""
        json_btn = self._driver.find_element(By.XPATH, 
            "//label[.='Content Type']/following-sibling::*/*/*[.='JSON']")
        json_btn.click()

    @WebAction()
    def __click_xml_content_type(self):
        """Click XML Content Type Button"""
        xml_btn = self._driver.find_element(By.XPATH, 
            "//label[.='Content Type']/following-sibling::*/*/*[.='XML']")
        xml_btn.click()

    @WebAction()
    def __click_use_https_checkbox(self):
        """Click enable HTTPS checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            "//label[.=' Use HTTPS']/input")
        checkbox.click()

    @WebAction()
    def __click_post_button(self):
        """Click the POST button"""
        button = self._driver.find_element(By.XPATH, 
            "//label[.='HTTP Method']/following-sibling::*/*/*[.='POST']")
        button.click()

    @WebAction()
    def __click_get_button(self):
        """Click the GET button"""
        button = self._driver.find_element(By.XPATH, 
            "//label[.='HTTP Method']/following-sibling::*/*/*[.='GET']")
        button.click()

    @WebAction()
    def __click_xml_accept_type(self):
        """Set XML Accept type"""
        xml_btn = self._driver.find_element(By.XPATH, 
            "//label[.='Accept Type']/following-sibling::*/*/*[.='XML']")
        xml_btn.click()

    @WebAction()
    def __click_json_accept_type(self):
        """Set JSON Accept type"""
        json_btn = self._driver.find_element(By.XPATH, 
            "//label[.='Accept Type']/following-sibling::*/*/*[.='JSON']")
        json_btn.click()

    @WebAction()
    def __get_row_expression(self):
        """Read row expression textbox"""
        textfield = self._driver.find_element(By.XPATH, _HTTPDatasetQueryTab._ROW_EXPRESSION)
        return textfield.get_attribute("value")

    @PageService()
    def set_post(self, api, http_content="", json_content_type=True, json_accept_type=True):
        """Set POST API info

        Args:
            api (str): API URL to use

            http_content (str): Data that has to be posted

            json_accept_type (bool): True for Json, False for XML

            json_content_type (bool): True for Json, False for XML

        """

        self._click_dataset_query_tab()
        self.__click_post_button()
        self.__set_rest_textfield(api)
        self.__set_http_content_textarea(http_content)
        if json_content_type:
            self.__click_json_content_type()
        else:
            self.__click_xml_accept_type()
        if json_accept_type:
            self.__click_json_accept_type()
        else:
            self.__click_xml_accept_type()

    @PageService()
    def set_get(self, api, json_accept_type=True):
        """Set GET as the REST API method

        Args:
            api (str): API URL to use
            json_accept_type (bool): True for Json, False for XML
        """
        self._click_dataset_query_tab()
        self.__click_get_button()
        self.__set_rest_textfield(api)
        if json_accept_type:
            self.__click_json_accept_type()
        else:
            self.__click_xml_accept_type()

    @PageService()
    def set_row_expression(self, expression):
        """Add row expression

        Args:
            expression (str): Expression string
        """
        self.__set_row_expression(expression)

    @PageService()
    def get_row_expression(self):
        """Get row expression

        Returns:
            str: Currently set row expression
        """
        return self.__get_row_expression()

    @PageService()
    def enable_https(self):
        """Enable HTTPs Checkbox"""
        self.__click_use_https_checkbox()


class _ParametersTab(Dataset):
    """Methods to work with parameters tab"""

    @WebAction()
    def __click_parameter_tab(self):
        """Click the Parameter tab"""
        parameter_tab = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetLeftPane']//li[contains(., 'Parameter')]")
        parameter_tab.click()

    @WebAction()
    def __click_add_parameter(self):
        """Click Add parameter button"""
        add_button = self._driver.find_element(By.XPATH, 
            "//*[@data-ng-click='addParameter()']")
        add_button.click()

    @WebAction()
    def __click_on_ui_input_component(self, input_value):
        """Click to select the Input in 'Input Variables' window"""
        input_button = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetModal']//button/"
            "following-sibling::*/*[.='%s']" % input_value)
        input_button.click()

    @WebAction()
    def __click_insert_on_parameter_window(self):
        """Click Insert on parameters tab"""
        insert_buttons = self._driver.find_elements(By.XPATH, 
            "//*[@id='parametersView']//button[.='Insert']")
        if insert_buttons:
            insert_buttons[-1].click()
        else:
            raise CVWebAutomationException(
                "Unable to find the Insert button on Parameter tab")

    @WebAction()
    def __click_insert_in_input_variable_window(self):
        """Click Insert button on 'Input Variables' window"""
        insert = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetModal']//*[@class='modal-footer']/*[.='Insert']")
        insert.click()

    @WebAction()
    def __enable_multi(self):
        """Enable Multi checkbox"""
        checkboxes = self._driver.find_elements(By.XPATH, 
            "//input[@*='parameter.isList']")
        if checkboxes:
            checkboxes[-1].click()
        else:
            raise CVWebAutomationException(
                "Could not enable 'Multi' type checkbox")

    @WebAction()
    def __enable_required(self):
        """Enable Required checkbox"""
        checkboxes = self._driver.find_elements(By.XPATH, 
            "//input[@*='parameter.required']")
        if checkboxes:
            checkboxes[-1].click()
        else:
            raise CVWebAutomationException(
                "Could not enable 'Required' checkbox")

    @WebAction()
    def __set_last_parameter(self, parameter):
        """Set the SQL variable name"""
        input_fields = self._driver.find_elements(By.XPATH, 
            "//*[contains(@class, 'current')]//input[@data-ng-model='parameter.name']")
        if input_fields:
            input_fields[-1].clear()
            input_fields[-1].send_keys(parameter)
        else:
            raise CVWebAutomationException(
                "Unable to find any input parameter to add")

    @WebAction()
    def __set_parameter_type(self, type_):
        """Set the parameter type"""
        dropdown = Select(self._driver.find_element(By.XPATH, 
            "//*[@id='parametersView']//*[contains(@class, 'current')]//select"))
        if type_ in [option.text for option in dropdown.options]:
            dropdown.select_by_visible_text(type_)

    @WebAction()
    def __set_value_textbox(self, val_string):
        """Type into Parameter Value TextBox"""
        values = self._driver.find_elements(By.XPATH, 
            "//input[@*='parameter.values']")
        if values:
            values[-1].send_keys(val_string)
        else:
            raise CVWebAutomationException(
                "No Value field found")

    @PageService()
    def add_parameter(self, param_name, input_variable, required=False, map_input_with_ui=True):
        # TODO: Add Change to support expression
        """Add parameter to the Dataset

        Args:
            param_name (str): SQL Variable name to use

            input_variable (DataType): Any instance of input variable

            required (bool): Required checkbox, enabled if True

            map_input_with_ui (bool): IF this is false, input_name will be typed
                as string into the Value field, else Insert button will be clicked
                and the input will be mapped using the UI
        """
        if not isinstance(input_variable, DataType):
            raise ValueError("Input is not instance of DataType class")
        self.__click_parameter_tab()
        self.__click_add_parameter()
        self.__set_last_parameter(param_name)
        self.__set_parameter_type(input_variable.type)
        if input_variable.is_multi_enabled:
            self.__enable_multi()
        if required:
            self.__enable_required()
        if map_input_with_ui is False:
            self.__set_value_textbox(input_variable.name)
        else:
            sleep(1)
            self.__click_insert_on_parameter_window()
            sleep(1)
            self.__click_on_ui_input_component(input_variable.name)
            sleep(1)
            self.__click_insert_in_input_variable_window()
            sleep(1)


class _AdvancedTab(Dataset):
    """All operations in advanced tab common to all datasets go here"""

    @WebAction()
    def __set_post_query_filter(self, sql):
        """Set PostQuery textarea"""
        textarea = self._driver.find_element(By.XPATH, 
            "//*[@id='advancedView']//textarea"
        )
        textarea.send_keys(sql)

    @WebAction()
    def __offline_enable_checkbox(self):
        """Enable offline collection checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            "//input[@data-ng-model='queryPlan.offline']"
        )
        checkbox.click()

    @WebAction()
    def __click_advanced_tab(self):
        """Click Advanced Tab"""
        tab = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetLeftPane']//li[contains(., 'Advanced')]"
        )
        tab.click()

    @WebAction()
    def __click_collection_frequency_checkbox(self):
        """Enable collection frequency checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            "//*[./label[.='Collection Frequency:']]/input"
        )
        checkbox.click()

    @WebAction()
    def __click_multicommcell_query(self):
        """Click Multi Commcell query0"""
        button = self._driver.find_element(By.XPATH, 
            "//*[text()='Multi CommCell query']"
        )
        button.click()

    @WebAction()
    def __set_multicommcell_query(self, sql):
        """set multicommcell query text area"""
        textarea = self._driver.find_element(By.XPATH, 
            "//*[@id='advancedView']//*[contains(@placeholder,'CommCell')]"
        )
        textarea.send_keys(sql)

    @PageService()
    def enable_offline_collection(self):
        """Enable offline collection"""
        self.__click_advanced_tab()
        self.__offline_enable_checkbox()

    @PageService()
    def set_collection_frequency(self, frequency):
        """Set collection frequency"""
        self.__click_advanced_tab()
        self.__click_collection_frequency_checkbox()

    def disable_frequency_collection(self):
        """Disable frequency collection"""
        self.__click_advanced_tab()
        self.__click_collection_frequency_checkbox()

    @PageService(hide_args=True)
    def set_post_query_filter(self, sql):
        """Set post query filter"""
        self.__click_advanced_tab()
        self.__set_post_query_filter(sql)

    @PageService()
    def set_multicommcell_query(self,sql):
        """Set Multicommcell query"""
        self.__click_advanced_tab()
        self.__click_multicommcell_query()
        self.__set_multicommcell_query(sql)



class _DataSource(Dataset):
    """All the datasource selection methods for Dataset"""

    _DATASOURCES_TXT_FIELD = "//label[.='Data Sources']"

    @WebAction()
    def __click_datasource_dropdown(self):
        """Open the datasource dropdown menu"""
        dropdowns = self._driver.find_elements(By.XPATH, 
            _DataSource._DATASOURCES_TXT_FIELD +
            "/..//*[@class='arrow-down']")
        for dropdown in dropdowns:  # For HTTP & Database
            if dropdown.is_displayed():
                dropdown.click()

    @WebAction()
    def __expand_datasource_category(self, ds_type):
        """Expand DataSource category"""
        drop_buttons = self._driver.find_elements(By.XPATH, 
            "//*[text()='%s']//..//*[@ng-if='showExpando(item)']" % ds_type)
        drop_button = [
            drop_button
            for drop_button in drop_buttons
            if drop_button.is_displayed()
        ]
        if drop_button:
            drop_button[0].click()
        else:
            raise ValueError(
                f"Unable to find datasource category [{ds_type}]"
            )

    @WebAction()
    def __enable_datasource_checkbox(self, datasource_name):
        """Expand commcell datasource type"""
        checkboxes = self._driver.find_elements(By.XPATH, 
            _DataSource._DATASOURCES_TXT_FIELD + "/..//input/../../*"
        )
        checkbox = [
            checkbox for checkbox in checkboxes
            if datasource_name in checkbox.text
        ]
        if checkbox:
            checkbox[0].click()
        else:
            raise CVWebAutomationException(
                f"Unable to find datasource [{datasource_name}]"
            )

    def _enable_datasource(
            self, datasources_sub_str, remove_existing, expand_datasources=None):
        """Interim FH for enabling datasource"""
        if not isinstance(datasources_sub_str, list):
            raise ValueError("Argument datasources_sub_str has to be a iterable")
        if remove_existing:
            self.__remove_all_datasources()
        self.__click_datasource_dropdown()
        if expand_datasources is None:
            expand_datasources = []
        elif not isinstance(expand_datasources, list):
            raise ValueError("Argument datasources_sub_str has to be a iterable")

        list(map(self.__expand_datasource_category, expand_datasources))
        list(map(self.__enable_datasource_checkbox, datasources_sub_str))
        self.__click_datasource_dropdown()

    @WebAction()
    def __remove_all_datasources(self):
        """Remove all enabled datasources"""
        datasources = self._driver.find_elements(By.XPATH, 
            _DataSource._DATASOURCES_TXT_FIELD +
            "/..//*[@class='selected-item-close']")
        for datasource in datasources:
            if datasource.is_displayed():
                datasource.click()

    @PageService()
    def set_all_commcell_datasource(self, remove_existing=True):
        """Set all commcell datasource

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["CommCells"], remove_existing)


class _DatabaseDataSource(_DataSource):
    """Contains the Datasource methods specific to Database dataset"""

    @WebAction()
    def __click_database_dropdown(self):
        """Click Database dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//label[.='Databases']/following-sibling::*//button"
        )
        dropdown.click()

    @WebAction(delay=2)
    def __select_first_database(self):
        """Select first database"""
        dbs = self._driver.find_elements(By.XPATH, 
            "//label[.='Databases']/following-sibling::"
            "*//*[@*='db in databases']"
        )
        if dbs:
            dbs[0].click()
        else:
            raise CVWebAutomationException(
                "No DataBase found to select"
            )

    @WebAction()
    def __select_database(self, name):
        """Selects the given database from the drop down"""
        database = self._driver.find_element(By.XPATH, f"//a[contains(text(),'{name}')]")
        database.click()

    @PageService()
    def set_local_commcell_datasource(self, remove_existing=True):
        """Remove existing datasource and add local commcell

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["Local ("], remove_existing, ["CommCells"])

    @PageService()
    def set_all_metrics_datasource(self, remove_existing=True):
        """Set all metrics datasource

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["Metrics"], remove_existing)

    @PageService()
    def set_all_mysql_datasource(self, remove_existing=True):
        """Set all mysql datasource

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["MySQL"], remove_existing)

    @PageService()
    def set_all_sql_server_datasource(self, remove_existing=True):
        """Set all mysql datasource

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["SQL Server"], remove_existing)

    @PageService()
    def set_all_oracle_datasource(self, remove_existing=True):
        """Set all mysql datasource

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["Oracle"], remove_existing)

    @PageService()
    def set_database(self, name=""):
        """Select DB

        Args:
            name(str): Name of the DataBase, implement when need be, currently
                we select the first DB available
        """
        self.__click_database_dropdown()
        sleep(1)
        self._webconsole.wait_till_load_complete(
            overlay_check=False, line_check=False, comp_load=False
        )
        sleep(1)

        if name:
            self.__select_database(name)
        else:
            self.__select_first_database()

    @PageService()
    def set_oracle_datasources(self, data_sources, remove_existing=True):
        """
        Args:
            data_sources    (list): list of oracle data sources to be selected

            remove_existing (bool): Remove all the datasource selected

        Returns:

        """
        self._enable_datasource(data_sources, remove_existing, ["Oracle"])

    @PageService()
    def set_sql_server_datasources(self, data_sources, remove_existing=True):
        """
        Args:
            data_sources    (list): list of oracle data sources to be selected

            remove_existing (bool): Remove all the datasource selected

        Returns:

        """
        self._enable_datasource(data_sources, remove_existing, ["SQL Server"])

    @PageService()
    def set_mysql_datasources(self, data_sources, remove_existing=True):
        """
        Args:
            data_sources    (list): list of oracle data sources to be selected

            remove_existing (bool): Remove all the datasource selected

        Returns:

        """
        self._enable_datasource(data_sources, remove_existing, ["MySQL"])


class _SharedDataSet(_DatasetQueryTab):
    """Contains the Datasets methods specific to Shared dataset"""

    @WebAction()
    def __select_dataset_dropdown(self, name):
        """ Selects the dataset name """
        dropdown = self._driver.find_element(By.XPATH, 
            "//label[contains(text(),'Data Sets')]//following-sibling::div/select")
        Select(dropdown).select_by_visible_text(name)

    @PageService()
    def select_dataset(self, name):
        """ Selects the given dataset from the drop down

        Args:
            name(str) : Name of the dataset to be selected

        """
        self.__select_dataset_dropdown(name)


class _HTTPDataSource(_DataSource):
    """Contains the Datasource methods specific to HTTP dataset"""

    def enable_other_http(self, remove_existing):
        """Enable Other HTTP checkbox

        Args:
            remove_existing (bool): Remove all the datasource selected
        """
        self._enable_datasource(["Other HTTP"], remove_existing)


class DatabaseDataset(
        _DatabaseDatasetQueryTab,
        _DatabaseDataSource,
        _ParametersTab,
        _AdvancedTab,
        _FieldsTab):
    """
    Mixin class used for database type Dataset, all operations
    on the database type class has to be done using this class

    Examples::

        db_dataset = DatabaseDataset()

        builder_object.add(db_dataset)
        # above line takes care of opening and closing the Dataset.
        # Dataset object is not usable without adding it to the
        # Builder object, and the methods will work only when the
        # Dataset modal is opened

        # Below method will be provided by _DatabaseDataSet implementation
        db_dataset.set_dataset_name("HardRock Testing")

        # Below method will be provided by _dataset.DataSource implementation
        db_dataset.set_all_commcell_datasource()
    """

    @property
    def _dataset_type(self):
        return "Database"


class JoinDataset(
        _SQLQueryDataset,
        _ParametersTab,
        _AdvancedTab):
    """
    Public API class used for Dataset type datasets

    Example usage is similar to DatabaseDataset class
    """

    @property
    def _dataset_type(self):
        return "Join Dataset"


class SharedDataset(
        _SharedDataSet,
        _FieldsTab,
        _ParametersTab,
        _AdvancedTab):
    """
    Public API class used for Shared type dataset
    """

    @property
    def _dataset_type(self):
        return "Shared"


class HTTPDataset(
        _HTTPDatasetQueryTab,
        _HTTPDataSource,
        _ParametersTab,
        _AdvancedTab):
    """
    Public API class used for HTTP type datasets

    Example usage is similar to DatabaseDataset class
    """

    @property
    def _dataset_type(self):
        return "HTTP"


class ScriptDataset(
        _SQLQueryDataset,
        _ParametersTab):
    """
    Public API class used for Script type datasets

    Example usage is similar to DatabaseDataset class
    """

    @property
    def _dataset_type(self):
        return "Script"


class RDataset(_DatasetQueryTab, _ParametersTab):
    """
    Public API class used for Script type datasets

    Example usage is similar to DatabaseDataset class
    """

    @property
    def _dataset_type(self):
        return "R Script"

    @WebAction()
    def __set_plot_query(self, query):
        """set plot query"""
        textbox = self._driver.find_element(By.XPATH, 
            "//textarea[@data-ng-model='dataSet.GetOperation.rPlotQuery']"
        )
        textbox.clear()
        textbox.send_keys(query)

    @WebAction()
    def __click_dataset_dropdown(self):
        """click dataset dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            """//div[@data-ng-show="dataSet.endpoint === 'R'"]//textarea[@ng-model="rDataSets"]
            """
        )
        dropdown.click()

    @WebAction()
    def __set_query(self, query):
        """set dataset query"""
        textbox = self._driver.find_element(By.XPATH, 
            """//div[@data-ng-show="dataSet.endpoint === 'R'"]
            //textarea[@data-ng-model='dataSet.GetOperation.rDataSetQuery']"""
        )
        textbox.clear()
        textbox.send_keys(query)

    @WebAction(delay=3)
    def __select_dataset(self, dataset_name):
        """select data set for R dataset"""
        datasets = self._driver.find_elements(By.XPATH, 
            "//li[@data-ng-repeat='rDataSet in rDataSetList']"
        )
        for dataset in datasets:
            if dataset_name == dataset.text:
                dataset.find_element(By.XPATH, "//input").click()
                return
        raise WebDriverException(f"Dataset [{dataset_name}] not found in R dataset panel")

    @WebAction()
    def __click_done(self):
        """Click Done button"""
        button = self._driver.find_element(By.XPATH, 
            "//div[@class='modal-footer ng-scope']//*[@data-ng-click='addDataSetList()']"
        )
        button.click()

    @WebAction()
    def __select_column(self, column_name):
        """select particular column"""
        columns = self._driver.find_elements(By.XPATH, 
            "//li[@data-ng-repeat='rDataSet in rDataSetList']"
        )
        for column in columns:
            if column_name == column.text:
                column.find_element(By.XPATH, "//input").click()
                return
        raise WebDriverException(f"column [{column_name}] not found in R dataset panel")

    @WebAction()
    def __select_all_fields(self):
        """select all fields from dataset"""
        self._driver.find_elements(By.XPATH, 
            "//input[@data-ng-model='curRdataSet.includeAllColumns']"
        ).click()

    @PageService()
    def select_dataset(self, dataset_name, column_name=None):
        """select dataset for R"""
        self.__click_dataset_dropdown()
        self.__select_dataset(dataset_name)
        if column_name:
            self.__select_all_fields()
            self.__select_column(column_name)
        self.__click_done()

    @PageService(hide_args=True)
    def set_dataset_query(self, sql):
        """Set the SQL Query"""
        self._click_dataset_query_tab()
        self.__set_query(sql)

    @PageService(hide_args=True)
    def set_plot_query(self, sql):
        """Set the SQL Query"""
        self._click_dataset_query_tab()
        self.__set_plot_query(sql)
