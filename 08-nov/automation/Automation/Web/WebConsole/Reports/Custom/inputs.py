from selenium.webdriver.common.by import By
"""
All the options accessed from Input tab go to this module

Only classes present inside the __all__ variable should be
imported by TestCases and Utils, rest of the classes are for
internal use
"""

from abc import ABC
from abc import abstractmethod
from collections import deque

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from Web.Common.page_object import (
    WebAction,
    PageService
)


class DataType(ABC):
    """
    This class deals with the following responsibilities of an input

        * Configure the datatype
        * Provide builder specific options
    """

    def __init__(self, name):
        """
        Driver and webconsole objects will be initialised when
        input is added to builder using the Builder.add_input

        Args:
            name (str): Variable name to be used by the input
        """
        self.__webconsole = None
        self.__browser = None
        self.__driver = None
        self._html_controller = None
        self.name = name
        self.is_multi_enabled = False

    @property
    def _webconsole(self):
        if self.__webconsole is None:
            raise ValueError(
                "Input variable not initialized, "
                "was Builder.add_input called ?")
        return self.__webconsole

    @property
    def _browser(self):
        if self.__browser is None:
            raise ValueError(
                "Input variable not initialized, "
                "was Builder.add_input called ?")
        return self.__browser

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError(
                "Input variable not initialized, "
                "was Builder.add_input called ?")
        return self.__driver

    @WebAction()
    def __click_done(self):
        """Click Done"""
        button = self._driver.find_element(By.XPATH, 
            "//*[@id='addDataSetModal']//*[.='Done']")
        button.click()

    @WebAction()
    def __set_input_variable_textbox(self, name):
        """Type into input variable TextField"""
        text_field = self._driver.find_element(By.XPATH, 
            "//*[label[.='Input Variable']]//input"
        )
        text_field.send_keys(name)

    @WebAction()
    def __set_default_value_textbox(self, value):
        """Set the default value textfield"""
        textfield = self._driver.find_element(By.XPATH, 
            "//*[label[.='Default Value']]//input"
        )
        textfield.send_keys(value)

    @WebAction(delay=2)
    def __set_input_variable_type(self):
        """Set input variable type"""
        select_webobject = self._driver.find_element(By.XPATH, 
            "//*[label[.='Input Variable Type']]//select"
        )
        select = Select(select_webobject)
        select.select_by_visible_text(self.type)

    @WebAction()
    def __select_control_type_dropdown(self, type_):
        """Select control type from dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[label[.='Input Control Type']]//select"
        )
        Select(dropdown).select_by_visible_text(type_)

    @WebAction()
    def __enable_required(self):
        """Enable required option field"""
        option = self._driver.find_element(By.XPATH, 
            "//input[@data-ng-model='currentInput.required' and @value='true']"
        )
        option.click()

    @WebAction()
    def __enable_optional(self):
        """Enable optional option field"""
        option = self._driver.find_element(By.XPATH, 
            "//*[label[.='Required']]//input[@value='true']"
        )
        option.click()

    @WebAction()
    def __enable_hide_input(self):
        """Enable hide input checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            "//*[label[.='Hide Input']]//input"
        )
        checkbox.click()

    def __str__(self):
        s = f"<{self.__class__.__name__} "
        s += f"Name=[{self.name}] "
        return s + f"ID=[{id(self)}]>"

    @property
    @abstractmethod
    def type(self):
        """Override this method as a variable and assign the dropdown
        value seen on the variable type list"""
        raise NotImplementedError

    @PageService()
    def add_html_controller(self, input_):
        """Add HTML controller to Input"""
        if not isinstance(input_, HTMLController):
            raise ValueError("Argument input_ is not an HTML Element")
        self.__select_control_type_dropdown(input_.control_type)
        input_.configure(self._webconsole, _builder=True)
        self._html_controller = input_

    @PageService()
    def configure(self, webconsole):
        """Set the input variable type dropdown

        This function need not be called, it will be automatically
        called by `add_input()` in Builder class
        """
        self.__webconsole = webconsole
        self.__browser = webconsole.browser
        self.__driver = webconsole.browser.driver

        self.__set_input_variable_type()
        self.__set_input_variable_textbox(self.name)

    @PageService()
    def hide_input(self):
        """Hide input"""
        self.__enable_hide_input()

    @PageService()
    def set_default_value(self, value):
        """Set default value"""
        self.__set_default_value_textbox(value)

    @PageService()
    def set_optional(self):
        """Set optional"""
        self.__enable_optional()

    @PageService()
    def set_required(self):
        """Set required"""
        self.__enable_required()

    @PageService()
    def save(self):
        """Save the input changes"""
        self.__click_done()

    @PageService()
    def set_display_name(self, disp_name):
        """Set display name of the daterange Input"""
        text_field = self._driver.find_element(By.XPATH, 
            "//*[label[.='DisplayName']]//input"
        )
        text_field.send_keys(disp_name)


class MultiValueDataType(DataType):
    """
    Classes which have the 'Allow MultiSelection' option would inherit
    this class, this class is not mapped to any class on the UI
    """

    @WebAction()
    def __enable_multi_selection(self):
        """Enable multi selection checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            "//*[label[.='Allow MultiSelection']]//input"
        )
        checkbox.click()

    @PageService()
    def enable_multi_selection(self):
        """Enable multi selection on input"""
        self.is_multi_enabled = True
        self.__enable_multi_selection()


class Date(DataType):
    """
    This class contains all the methods to deal with Date input variable
    """

    @property
    def type(self):
        return "Date"

    @WebAction()
    def __set_input_control(self, control_type):
        """Set input control dropdown"""
        select_webobject = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Input Control Type']"
            "/following-sibling::*/select")
        select = Select(select_webobject)
        select.select_by_visible_text(control_type.value)

    @PageService()
    def set_control_type(self, control_type):
        """Set Input Control type"""
        self.__set_input_control(control_type)


class DateRange(DataType):
    """
    This class contains all the methods to deal with
    DateRange variable
    """

    _DATE_RANGE_OPTIONS = "//label[contains(.,'%s')]/input"

    @property
    def type(self):
        return "DateRange"

    @WebAction()
    def __enable_last_n(self):
        """Click Last N checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Last N")
        checkbox.click()

    @WebAction()
    def __enable_next_n(self):
        """Click Next N checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Next N")
        checkbox.click()

    @WebAction()
    def __enable_custom_range(self):
        """Click Custom Range checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Custom Range")
        checkbox.click()

    @WebAction()
    def __enable_time_selection(self):
        """Click Include Time Selection checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Include Time Selection")
        checkbox.click()

    @WebAction()
    def __enable_minutes(self):
        """Click Minutes checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Minutes")
        checkbox.click()

    @WebAction()
    def __enable_hours(self):
        """Click hours checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Hours")
        checkbox.click()

    @WebAction()
    def __enable_days(self):
        """Click Days checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Days")
        checkbox.click()

    @WebAction()
    def __enable_weeks(self):
        """Click Weeks checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Weeks")
        checkbox.click()

    @WebAction()
    def __enable_months(self):
        """Click Months checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Months")
        checkbox.click()

    @WebAction()
    def __enable_years(self):
        """Click Years checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            DateRange._DATE_RANGE_OPTIONS % "Years")
        checkbox.click()

    @PageService()
    def enable_options(
            self, last_n=False, next_n=False, custom_range=False, time=False,
            minutes=False, hours=False, days=False, weeks=False,
            months=False, years=False):
        """Configure the DateRange input options

        Args are the same as shown in the UI
        """
        if last_n:
            self.__enable_last_n()
        if next_n:
            self.__enable_next_n()
        if custom_range:
            self.__enable_custom_range()
        if time:
            self.__enable_time_selection()
        if minutes:
            self.__enable_minutes()
        if hours:
            self.__enable_hours()
        if days:
            self.__enable_days()
        if weeks:
            self.__enable_weeks()
        if months:
            self.__enable_months()
        if years:
            self.__enable_years()


class Decimal(MultiValueDataType):
    """
    This class contains all the methods to deal with
    Decimal variable
    """

    @property
    def type(self):
        return "Decimal"


class Integer(MultiValueDataType):
    """
    This class contains all the methods to deal with
    Integer variable
    """

    @property
    def type(self):
        return "Integer"


class String(MultiValueDataType):
    """
    This class contains all the methods to deal with
    String variable
    """

    @property
    def type(self):
        return "String"


class Time(DataType):
    """
    This class contains all the methods to deal with
    Time variable
    """

    @property
    def type(self):
        return "Time"


class Commcell(MultiValueDataType):
    """
    This class contains all the methods to deal with
    Commcell variable
    """

    @property
    def type(self):
        return "Commcell"


class HTMLController(ABC):
    """All the HTML Input controllers inherit this class"""

    def __init__(self, display_name):
        """All driver and webconsole objects will be initialised when
        HTMLElement is added to the input using add_html_controller
        method defined inside Input"""
        self.__webconsole = None
        self.__browser = None
        self.__driver = None
        self.display_name = display_name

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError(
                "driver not initialized, is Controller added "
                "to any component using add_html_controller method ?")
        return self.__driver

    @property
    def _webconsole(self):
        if self.__webconsole is None:
            raise ValueError(
                "webconsole not initialized, is Controller added "
                "to any component using add_html_controller method ?")
        return self.__webconsole

    @property
    def _browser(self):
        if self.__browser is None:
            raise ValueError(
                "browser not initialized, is Controller added "
                "to any component using add_html_controller method ?")
        return self.__browser

    @WebAction()
    def __expand_input(self):
        """Clicks the expand button near the input controllers"""
        button = self._driver.find_element(By.XPATH, "//*[@title='Show more']")
        button.click()

    @WebAction(delay=1)
    def __is_apply_exist(self):
        """Click Apply button"""
        button = self._driver.find_elements(By.XPATH, 
            "//button[.='Apply' and @type='submit']"
        )
        if button:
            return True
        return False

    @WebAction()
    def __click_apply(self):
        """Click Apply button"""
        button = self._driver.find_element(By.XPATH, 
            "//button[.='Apply' and @type='submit']"
        )
        button.click()

    @WebAction()
    def __set_control_type(self):
        """Set the input control type"""
        select = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.="
            "'Input Control Type']/following-sibling::*/select")
        Select(select).select_by_visible_text(self.control_type)

    @WebAction()
    def __set_display_name_textbox(self, name):
        """Type into display name textbox"""
        text_field = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='DisplayName']"
            "/following-sibling::*/input")
        text_field.send_keys(name)

    def __str__(self):
        s = f"<{self.__class__.__name__} "
        s += f"DisplayName=[{self.display_name}] "
        return s + f"ID=[{id(self)}]>"

    @WebAction()
    def _click_controller(self):
        """Click input controller"""
        controller = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
        )
        controller.click()

    @WebAction()
    def _click_ok(self):
        """Click Ok on TextBox"""
        button = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            "/following-sibling::*//button[text()='Ok']"
        )
        button.click()

    @PageService()
    def expand_input_controller(self):
        """Expands the input so that more controllers are visible"""
        self.__expand_input()

    @PageService()
    def apply(self):
        """Submit input, and wait till loading is complete"""
        if self.__is_apply_exist():
            self.__click_apply()
            self._webconsole.wait_till_load_complete()

    @property
    @abstractmethod
    def control_type(self):
        """Implement as variable and assign the Control type
        as value"""
        raise NotImplementedError

    @PageService()
    def configure(self, webconsole, _builder=False):
        """Configure HTML input controller

        DO NOT CALL THIS METHOD, this method is reserved
        for internal use by builder and viewer when add_*
        is called on them
        """
        self.__webconsole = webconsole
        self.__browser = webconsole.browser
        self.__driver = webconsole.browser.driver
        if _builder:
            self.__set_display_name_textbox(self.display_name)


class BaseDropdownController(HTMLController):
    """
    There is no input by name _Dropdown, this class is for all the
    common operations between ListBox and Dropdown.
    """

    @WebAction()
    def __get_all_available_options(self):
        """Get the list of all the available options"""
        options = self._driver.find_elements(By.XPATH, 
            f"""//*[@data-input-displayname='{self.display_name}']/
            following-sibling::*//*[@data-ng-repeat="option in options"]"""
        )
        return [
            option.get_attribute("innerText").strip()
            for option in options
        ]

    @PageService()
    def get_available_options(self):
        """Get all the available options"""
        return self.__get_all_available_options()


class DatePickerController(HTMLController):
    """DatePicker control type for Date DataType"""

    @property
    def control_type(self):
        return "DatePicker"

    @WebAction()
    def __set_date_field(self, day, month, year):
        """Type date field"""
        textfield = self._driver.find_element(By.XPATH, 
            "//*[.='%s']/../following-sibling::*/input" % self.display_name
        )
        textfield.send_keys("%s/%s/%s" % (month, day, year))

    @PageService()
    def set_date_controller(self, day, month, year):
        """Set Date on DatePicker"""
        self.__set_date_field(day, month, year)


class DateRangeController(HTMLController):
    """DateRange control type for DateRange DataType"""

    @property
    def control_type(self):
        return "DateRange"

    @WebAction()
    def __set_field(self, field, value):
        """Sets the value for the field passed."""
        date = self._driver.find_element(By.XPATH, "//input[@name='%s']" % field)
        date.send_keys(value)

    @WebAction()
    def __click_option_in_dropdown(self, value):
        """Select option from dropdown"""
        option = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            f"/following-sibling::*//*[text()='{value}']"
        )
        option.click()

    @WebAction()
    def __get_all_available_options(self):
        """Get the list of all the available options"""
        options = self._driver.find_elements(By.XPATH, 
            f"""//*[@data-input-displayname='{self.display_name}']//following-sibling::div//button"""
        )
        return [
            option.get_attribute("innerText").strip()
            for option in options
        ]

    @PageService()
    def get_available_options(self):
        """Get all the available options"""
        return self.__get_all_available_options()

    @PageService()
    def set_starting_date(self, day, month, year):
        """Sets the date range."""
        self.__set_field("startDate", ("%s/%s/%s" % (month, day, year)))

    @PageService()
    def set_ending_date(self, day, month, year):
        """Sets the date range."""
        self.__set_field("endDate", ("%s/%s/%s" % (month, day, year)))

    @PageService()
    def set_starting_time(self, hour, minute, am=True):
        """Sets the time range."""
        am_ = "AM" if am else "PM"
        self.__set_field("startTime", "%s:%s %s" % (hour, minute, am_))

    @PageService()
    def set_ending_time(self, hour, minute, am=True):
        """Sets the time range."""
        am_ = "AM" if am else "PM"
        self.__set_field("endTime", "%s:%s %s" % (hour, minute, am_))

    @PageService()
    def set_relative_daterange(self, relative_daterange):
        """select relative daterange options from the input controller

        Args:
            relative_daterange (str) : option in the daterange dropdown
                                       Ex - "Last 6 months", "Last 1 year" etc.
        """
        self._click_controller()
        self.__click_option_in_dropdown(relative_daterange)
        self.apply()



class DateTimePickerController(HTMLController):
    """DateTimePicker control type for Date DataType"""

    @property
    def control_type(self):
        return "DateTimePicker"

    @WebAction()
    def __set_time_field(self, hour, minute, am):
        """Set Time TextField"""
        time_field = self._driver.find_element(By.XPATH, 
            "//*[.='%s']/../following-sibling::*/input[@placeholder='Time']" % self.display_name)
        time_field.send_keys("%s:%s %s" % (hour, minute, am))

    @WebAction()
    def __set_date_field(self, day, month, year):
        """Set Date TextField"""
        date_field = self._driver.find_element(By.XPATH, 
            "//*[.='%s']/../following-sibling::*/input[@placeholder='Date']" % self.display_name
        )
        date_field.send_keys("%s/%s/%s" % (month, day, year))

    @PageService()
    def set_date_time_controller(self, day, month, year, hour, minute, am=True):
        """Set DateTime on the DateTime input controller"""
        am_ = "AM" if am else "PM"
        self.__set_date_field(day, month, year)
        self.__set_time_field(hour, minute, am_)


class TimePickerController(HTMLController):
    """TimePicker control type for Date DataType"""

    @property
    def control_type(self):
        return "TimePicker"

    @WebAction()
    def __click_apply(self):
        """Click Apply time"""
        button = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            "/following-sibling::*//button[.='Apply']"
        )
        button.click()

    @WebAction()
    def __set_hour(self, hour):
        """Set hour"""
        field = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            "/following-sibling::*//input[@placeholder='HH']"
        )
        field.send_keys(hour)

    @WebAction()
    def __set_minute(self, minute):
        """Set minute"""
        field = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            "/following-sibling::*//input[@placeholder='MM']"
        )
        field.clear()
        field.send_keys(minute)

    @WebAction()
    def __is_am(self):
        """Is time in AM ?"""
        am_pm_field = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']/"
            "following-sibling::*//*[@class='uib-time am-pm']/button"
        )
        return "am" in am_pm_field.text.lower()

    @WebAction()
    def __toggle_am_pm(self):
        """Toggle AM PM"""
        am_pm_field = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']/"
            "following-sibling::*//*[@class='uib-time am-pm']/button"
        )
        am_pm_field.click()

    @PageService()
    def set_time_controller(self, hour, minute, am=True):
        """Set time on Time input controller"""
        self._click_controller()
        self.__set_hour(hour)
        self.__set_minute(minute)
        is_am_selected = self.__is_am()
        if am and not is_am_selected:
            self.__toggle_am_pm()
        elif not am and is_am_selected:
            self.__toggle_am_pm()
        self.__click_apply()  # Applies only time input


class HiddenController(HTMLController):
    """Hidden control type for supported DataTypes"""

    @property
    def control_type(self):
        return "Hidden"


class TextBoxController(HTMLController):
    """TextBox control type for supported DataTypes"""

    @property
    def control_type(self):
        return "TextBox"

    @WebAction()
    def __set_text_box(self, text):
        """Type text into TextField"""
        textbox = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']//input"
        )
        textbox.clear()
        textbox.send_keys(text + "\n")

    @PageService()
    def set_textbox_controller(self, text):
        """Set text on textbox"""
        self._click_controller()
        self.__set_text_box(text)
        self._webconsole.wait_till_load_complete()


class TextAreaController(HTMLController):
    """TextArea control type for supported DataTypes"""

    @property
    def control_type(self):
        return "TextArea"

    @WebAction()
    def __set_textarea_field(self, text):
        """Type text into textarea"""
        textarea = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            f"/following-sibling::*//textarea"
        )
        textarea.send_keys(text)

    @PageService()
    def set_textarea_controller(self, text):
        """Set text on TextArea"""
        self._click_controller()
        self.__set_textarea_field(text)
        self._click_ok()


class SliderController(HTMLController):
    """Slider control type for Integer and Decimal DataTypes"""

    @property
    def control_type(self):
        return "Slider"

    @WebAction()
    def __set_minimum_value_textbox(self, value):
        """Set Minimum value textbox"""
        textbox = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Minimum Value']"
            "/following-sibling::*/input")
        textbox.send_keys(value)

    @WebAction()
    def __set_max_value_textbox(self, value):
        """Set Max value textbox"""
        textbox = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Max Value']"
            "/following-sibling::*/input")
        textbox.send_keys(value)

    @WebAction()
    def __set_step_value_textbox(self, value):
        """Set Step value textbox"""
        textbox = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Step']"
            "/following-sibling::*/input")
        textbox.send_keys(value)

    @PageService()
    def set_min_max_and_step_fields(self, min_value="", max_value="", step=""):
        """Configure Slider input type"""
        self._click_controller()
        self.__set_minimum_value_textbox(min_value)
        self.__set_max_value_textbox(max_value)
        self.__set_step_value_textbox(step)


class DropDownController(BaseDropdownController):
    """DropDown control type for supported DataTypes"""

    @property
    def control_type(self):
        return "DropDown"

    @WebAction()
    def __click_option_in_dropdown(self, value):
        """Select option from dropdown"""
        option = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            f"/following-sibling::*//*[@title='{value}']"
        )
        option.click()

    @PageService()
    def select_value(self, value):
        """Select value from dropdown"""
        self._click_controller()
        self.__click_option_in_dropdown(value)


class RadioButtonController(HTMLController):
    """RadioButton control type for supported DataTypes"""

    @property
    def control_type(self):
        return "RadioButton"

    @WebAction()
    def __click_option(self, value):
        """Click option"""
        option = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            f"/following-sibling::*//*[@title='{value}']"
        )
        option.click()

    @PageService()
    def select_option(self, value):
        """Select option"""
        self._click_controller()
        self.__click_option(value)


class MultiSelectHTMLController(HTMLController):
    """Input controls which support multiple value selection inherit
    this class, no such component exists on the UI"""

    @WebAction()
    def __click_input_value(self, value):
        """Select input value on Input dropdown"""
        value_button = self._driver.find_element(By.XPATH, 
            f"//*[@data-input-displayname='{self.display_name}']"
            f"/following-sibling::*//*[@title='{value}']/label"
        )
        value_button.click()

    @WebAction()
    def __enable_manual(self):
        """Select manual option button"""
        option = self._driver.find_element(By.XPATH, 
            "(//*[@id='addNewInputForm']//*[.='Values']"
            "/following-sibling::*/input)[1]")
        option.click()

    @WebAction()
    def __enable_dataset(self):
        """Select dataset option button"""
        option = self._driver.find_element(By.XPATH, 
            "(//*[@id='addNewInputForm']//*[.='Values']"
            "/following-sibling::*/input)[2]")
        option.click()

    @WebAction()
    def __set_labels(self, labels):
        """Set the label field"""
        textarea = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*"
            "[.='Possible Labels']/following-sibling::*/textarea")
        for label in labels:
            textarea.send_keys(label)
            textarea.send_keys(Keys.ENTER)

    @WebAction()
    def __set_values(self, values):
        """Set value field"""
        textarea = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*"
            "[.='Possible Values']/following-sibling::*/textarea")
        for value in values:
            textarea.send_keys(value)
            textarea.send_keys(Keys.ENTER)

    @WebAction()
    def __set_input_dataset_name(self, dataset_name):
        """Select input dataset from dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='DataSet']"
            "/following-sibling::*/select")
        Select(dropdown).select_by_visible_text(dataset_name)

    @WebAction(delay=1)
    def __select_value_dropdown(self, value_field):
        """Select value field from dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Value Field']"
            "/following-sibling::*/select")
        Select(dropdown).select_by_visible_text(value_field)

    @WebAction()
    def __select_label_dropdown(self, label_field):
        """Select label field from dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Label Field']"
            "/following-sibling::*/select")
        Select(dropdown).select_by_visible_text(label_field)

    @WebAction()
    def __select_depends_on_dropdown(self, depends_on):
        """Select depends on field from dropdown"""
        xp = "//div[@selected-model='currentInput.dependendent']/div"
        self._driver.find_element(By.XPATH, xp).click()
        self._driver.find_element(By.XPATH, f"//li//span[text()='{depends_on}']").click()
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __select_sort_by_dropdown(self, sort_by):
        """Select sort by field from dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Sort by']"
            "/following-sibling::*/select")
        Select(dropdown).select_by_visible_text(sort_by)

    @WebAction()
    def __select_sort_direction_dropdown(self, sort_direction):
        """Select Sort Direction field from dropdown"""
        dropdown = self._driver.find_element(By.XPATH, 
            "//*[@id='addNewInputForm']//*[.='Sort Direction']"
            "/following-sibling::*/select")
        Select(dropdown).select_by_visible_text(sort_direction)

    @WebAction()
    def __click_all(self):
        """clicks all option from dropdown"""
        xp = (
            f"//*[@data-input-displayname='{self.display_name}']"
            f"//..//div[@title='Select/clear all']"
        )
        self._driver.find_element(By.XPATH, xp).click()

    @PageService()
    def set_labels_and_values(self, labels, values):
        """Add user defined labels and values

        Args:
            labels (list): List of labels
            values (list): List of values
        """
        if (not isinstance(labels, list)) and (not isinstance(values, list)):
            raise ValueError("Invalid argument type")
        else:
            self.__enable_manual()
            self.__set_labels(labels)
            self.__set_values(values)

    @PageService()
    def set_dataset_options(
            self, dataset_name, value_field, label_field,
            depends_on=None, sort_by=None, sort_direction=None):
        """Add dataset defined labels and values

        Arguments are mapped to the fields on the UI
        """
        self.__enable_dataset()
        self.__set_input_dataset_name(dataset_name)
        self._webconsole.wait_till_load_complete()
        self.__select_value_dropdown(value_field)
        self.__select_label_dropdown(label_field)
        if depends_on:
            self.__select_depends_on_dropdown(depends_on)
        if sort_by:
            self.__select_sort_by_dropdown(sort_by)
        if sort_direction:
            self.__select_sort_direction_dropdown(sort_direction)

    @PageService()
    def select_value(self, value):
        """Select single value on Input dropdown"""
        self._click_controller()
        self.__click_input_value(value)
        self._click_controller()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def select_values(self, values: list):
        """Select multiple values on Input dropdown"""
        self._click_controller()
        deque(map(self.__click_input_value, values))
        self._click_controller()

    @PageService()
    def select_all(self):
        """Enables All option on Input dropdown"""
        self._click_controller()
        self.__click_all()
        self._click_controller()
        self._webconsole.wait_till_load_complete()


class CheckBoxController(MultiSelectHTMLController):
    """Checkbox control type for supported DataTypes"""

    @property
    def control_type(self):
        return "CheckBox"

    @WebAction(log=False)
    def _click_down_arrow(self):
        """No need to expand dropdown for CheckBox, this overrides
        the base class method to do nothing"""
        pass


class ListBoxController(MultiSelectHTMLController, BaseDropdownController):
    """ListBox control type for supported DataTypes"""

    @property
    def control_type(self):
        return "ListBox"
