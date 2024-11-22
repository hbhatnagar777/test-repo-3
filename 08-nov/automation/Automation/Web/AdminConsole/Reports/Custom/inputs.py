from abc import ABC
from abc import abstractmethod
from collections import deque
from datetime import datetime
from typing import final

from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown
from Web.Common.page_object import (
    WebAction,
    PageService
)


class HTMLController(ABC):
    """All the HTML Input controllers inherit this class"""

    def __init__(self, display_name, base_xp=None, base_menu_xp=None):
        """
        All driver and webconsole objects will be initialised when
        HTMLElement is added to the input using add_html_controller
        method defined inside Input

        base_xp: xpath to the input controller
        base_menu_xp: xpath to the input menu/dialog

        """

        self.__adminconsole = None
        self.__browser = None
        self.__driver = None
        self.display_name = display_name

        self.__inp_xp = "//*[contains(@class, 'inputsRow')]"

        self.__base_xp = base_xp
        self.__base_menu_xp = base_menu_xp

    @property
    def _default_base_xp(self):
        """
        default base xpath
        """
        return (f"{self._inp_xp}//label[text()='{self.display_name}']"
                f"/ancestor::*[contains(@class, 'MuiFormControl-root')]")

    @property
    def _default_base_menu_xp(self):
        """
        default base menu xpath
        """
        return f"{self._base_xp}//*[@id='menu-']"

    @property
    def _inp_xp(self):
        """xpath to inputs row"""
        return self.__inp_xp

    @final
    @property
    def _base_xp(self):
        """
        xpath to input controller
        override _default_base_menu_xp if subclass has different xpath
        """
        if self.__base_xp:
            return self.__base_xp
        else:
            return self._default_base_xp

    @final
    @property
    def _base_menu_xp(self):
        """
        xpath to input dropdown menu
        override _default_base_xp if subclass has different xpath
        """
        if self.__base_menu_xp:
            return self.__base_menu_xp
        else:
            return self._default_base_menu_xp

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError(
                "driver not initialized, is Controller added "
                "to any component using add_html_controller method ?")
        return self.__driver

    @property
    def _adminconsole(self):
        if self.__adminconsole is None:
            raise ValueError(
                "webconsole not initialized, is Controller added "
                "to any component using add_html_controller method ?")
        return self.__adminconsole

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
        more_icon = self._driver.find_elements(
            By.XPATH,
            f"{self._inp_xp}//*[contains(@class, 'more-less-btn-icon')]"
        )

        if len(more_icon) > 0:
            more_icon[0].click()

    @WebAction()
    def __is_apply_exist(self):
        """Click Apply button"""
        button = self._driver.find_elements(By.XPATH,
                                            f"{self._inp_xp}//button[@aria-label='Apply']"
                                            )
        if button:
            return True
        return False

    @WebAction()
    def __click_apply(self):
        """Click Apply button"""
        button = self._driver.find_element(By.XPATH,
                                           f"{self._inp_xp}//button[@aria-label='Apply']"
                                           )
        button.click()

    def __str__(self):
        s = f"<{self.__class__.__name__} "
        s += f"DisplayName=[{self.display_name}] "
        return s + f"ID=[{id(self)}]>"

    @WebAction()
    def _click_controller(self):
        """Click input controller"""
        controller = self._driver.find_element(By.XPATH,
                                               f"{self._base_xp}//*[contains(@class, 'MuiInput-input')]"
                                               )
        controller.click()

    @WebAction()
    def _unclick_controller(self):
        """unclick input controller"""
        backdrop = self._driver.find_element(By.XPATH, f"{self._base_menu_xp}//*[contains(@class, 'MuiBackdrop-root')]")
        self._driver.execute_script('arguments[0].click()', backdrop)  # element.click() sometimes gets intercepted

    @PageService()
    def expand_input_controller(self):
        """Expands the input so that more controllers are visible"""
        self.__expand_input()

    @PageService()
    def apply(self):
        """Submit input, and wait till loading is complete"""
        if self.__is_apply_exist():
            self.__click_apply()
            self._adminconsole.wait_for_completion()

    @property
    @abstractmethod
    def control_type(self):
        """Implement as variable and assign the Control type
        as value"""
        raise NotImplementedError

    @PageService()
    def configure(self, adminconsole, _builder=False):
        """Configure HTML input controller

        DO NOT CALL THIS METHOD, this method is reserved
        for internal use by builder and viewer when add_*
        is called on them
        """
        self.__adminconsole = adminconsole
        self.__browser = adminconsole.browser
        self.__driver = adminconsole.browser.driver
        # if _builder:
        #     self.__set_display_name_textbox(self.display_name)


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
        textbox = self._driver.find_element(By.XPATH, f"{self._base_xp}//input")
        textbox.send_keys(Keys.CONTROL + 'a' + Keys.DELETE)
        textbox.send_keys(text)

    @PageService()
    def set_textbox_controller(self, text):
        """Set text on textbox"""
        self._click_controller()
        self.__set_text_box(text)
        self._adminconsole.wait_for_completion()


class SliderController(HTMLController):
    """Slider control type for Integer and Decimal DataTypes"""

    @property
    def control_type(self):
        return "Slider"

    @property
    def _default_base_xp(self):
        """
        default base xpath
        """
        return (f"{self._inp_xp}//label[text()='{self.display_name}']"
                f"/following-sibling::*[contains(@class, 'MuiSlider-root')]")

    @WebAction()
    def _drag_to_value(self, val):
        """clicks slider at val"""
        slider = self._driver.find_element(
            By.XPATH,
            f"{self._base_xp}//*[contains(@class, 'MuiSlider-thumb')]"
        )

        target = self._driver.find_element(By.XPATH, f"{self._base_xp}//*[@data-index='{val}']")

        ActionChains(self._driver).drag_and_drop(slider, target).perform()

    @PageService()
    def select_value(self, val):
        """selects val in slider"""
        self._drag_to_value(val)


class BaseDropdownController(HTMLController, ABC):
    """
    There is no input by name _Dropdown, this class is for all the
    common operations between ListBox and Dropdown.
    """

    @WebAction()
    def __get_all_available_options(self):
        """Get the list of all the available options"""
        options = self._driver.find_elements(By.XPATH, f"{self._base_menu_xp}//li[@role='menuitem']"
                                             )
        return [
            option.text.strip()
            for option in options
        ]

    @PageService()
    def get_available_options(self):
        """Get all the available options"""
        self._click_controller()
        opts = self.__get_all_available_options()
        self._unclick_controller()
        return opts


class DropDownController(BaseDropdownController):
    """DropDown control type for supported DataTypes"""

    @property
    def control_type(self):
        return "DropDown"

    @WebAction()
    def __click_option_in_dropdown(self, value):
        """Select option from dropdown"""
        option = self._driver.find_element(
            By.XPATH,
            f"{self._base_menu_xp}//li[@role='menuitem']//*[@title='{value}']"
        )
        option.click()

    @PageService()
    def select_value(self, value):
        """Select value from dropdown"""
        self._click_controller()
        self.__click_option_in_dropdown(value)


class MultiSelectHTMLController(HTMLController, ABC):
    """Input controls which support multiple value selection inherit
    this class, no such component exists on the UI"""

    @WebAction()
    def __click_input_value(self, value):
        """Select input value on Input dropdown"""
        value_button = self._driver.find_element(By.XPATH,
                                                 f"{self._base_menu_xp}//li[@role='menuitem']//*[@title='{value}']"
                                                 )
        value_button.click()

    @WebAction()
    def __click_all(self):
        """clicks all option from dropdown"""
        xp = f"{self._base_menu_xp}//button[@aria-label='Select all']"

        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __click_reset(self):
        """clicks reset option from dropdown"""
        xp = f"{self._base_menu_xp}//button[@aria-label='Reset']"

        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __click_ok(self):
        """clicks ok in dropdown"""
        xp = f"{self._base_menu_xp}//button[@aria-label='OK']"

        self._driver.find_element(By.XPATH, xp).click()

    @PageService()
    def select_value(self, value, ok=False):
        """Select single value on Input dropdown
            Args:
                value (string): the input value
                ok ( Boolean): set to True if Ok box is present during input selection
        """
        self._click_controller()
        self.__click_input_value(value)
        if ok:
            self.__click_ok()
        self._adminconsole.wait_for_completion()

    @PageService()
    def select_values(self, values: list):
        """Select multiple values on Input dropdown"""
        self._click_controller()
        deque(map(self.__click_input_value, values))
        self.__click_ok()

    @PageService()
    def select_all(self):
        """Enables All option on Input dropdown"""
        self._click_controller()
        self.__click_all()
        self.__click_ok()
        self._adminconsole.wait_for_completion()

    @PageService()
    def unselect_all(self):
        """Enables All option on Input dropdown"""
        self._click_controller()
        self.__click_reset()
        self.__click_ok()
        self._adminconsole.wait_for_completion()


class CheckBoxController(MultiSelectHTMLController, BaseDropdownController):
    """Checkbox control type for supported DataTypes"""

    @property
    def control_type(self):
        return "CheckBox"


class ListBoxController(MultiSelectHTMLController, BaseDropdownController):
    """ListBox control type for supported DataTypes"""

    @property
    def control_type(self):
        return "ListBox"


class TimePickerController(HTMLController):
    """TimePicker control type for Date DataType"""

    @property
    def _default_base_menu_xp(self):
        label_id = self._driver.find_element(By.XPATH, f"{self._base_xp}//label").get_attribute('id')
        return f"//div[@aria-labelledby='{label_id}']"

    @property
    def control_type(self):
        return "TimePicker"

    @WebAction()
    def _click_controller(self):
        """clicks controller"""
        elem = self._driver.find_element(By.XPATH, f"{self._base_xp}//*[@data-testid='ClockIcon']")
        elem.click()

    @WebAction()
    def __set_hour(self, hour):
        """Set hour"""
        xpath = (f"{self._base_menu_xp}//ul[@aria-label='Select hours']//li[text()='{str(hour).zfill(2)}'] | "
                 f"{self._base_menu_xp}//*[contains(@class, 'k-time-list-wrapper')]/*[text()='hour']/..//ul//*[text()='{hour}']")

        elem = self._driver.find_element(
            By.XPATH,
            xpath
        )
        self._driver.execute_script("arguments[0].click();", elem)  # since elem might not be visible

    @WebAction()
    def __set_minute(self, minute):
        """Set minute"""
        xpath = (f"{self._base_menu_xp}//ul[@aria-label='Select minutes']//li[text()='{str(minute).zfill(2)}'] | "
                 f"{self._base_menu_xp}//*[contains(@class, 'k-time-list-wrapper')]/*[text()='minute']/..//ul//*[text()='{str(minute).zfill(2)}']")

        elem = self._driver.find_element(
            By.XPATH,
            xpath
        )
        self._driver.execute_script("arguments[0].click();", elem)  # since elem might not be visible

    @WebAction()
    def __set_meridiem(self, am):
        """
        Set AM / PM
        dialog closes when clicked
        """

        xpath = (f"{self._base_menu_xp}//ul[@aria-label='Select meridiem']//li[text()='{'AM' if am else 'PM'}'] | "
                 f"{self._base_menu_xp}//*[contains(@class, 'k-time-list-wrapper')]/*[text()='AM/PM']/..//ul//*[text()='{'AM' if am else 'PM'}']")

        elem = self._driver.find_element(
            By.XPATH,
            xpath
        )
        self._driver.execute_script("arguments[0].click();", elem)  # since elem might not be visible

    @WebAction()
    def _set_time_input(self, text):
        """enters text into input"""
        inp = self._driver.find_element(By.XPATH, f"{self._base_xp}//input")
        inp.send_keys(Keys.CONTROL + 'a' + Keys.DELETE)
        for ch in text:  # since send_keys(text) doesn't work
            inp.send_keys(ch)

    @PageService()
    def _set_time_controller(self, hour, minute, am=True):
        """Set time input"""
        self.__set_hour(int(hour))
        self.__set_minute(int(minute))
        self.__set_meridiem(am)

    @PageService()
    def set_time_controller(self, hour, minute, am=True):
        """Set time on Time input controller"""
        self._click_controller()
        self._set_time_controller(hour, minute, am)

    @PageService()
    def set_time_input(self, hour, minute, am=True):
        """types time in input element"""
        self._set_time_input(f"{hour} {minute} {'AM' if am else 'PM'}")


class DatePickerController(HTMLController):
    """DatePicker control type for Date DataType"""

    @property
    def _default_base_xp(self):
        """default xp to select first datetimepicker available"""
        return f"{self._inp_xp}//*[contains(@class, 'cv-date-time-picker-container')]"

    @property
    def _default_base_menu_xp(self):
        """default xpath to datetime popup"""
        return f"//*[contains(@class, 'cv-date-time-picker-popup')]"

    @property
    def control_type(self):
        return "DatePicker"

    @WebAction()
    def _click_controller(self):
        """clicks controller"""
        self._driver.find_element(By.XPATH, f"{self._base_xp}//*[@aria-label='Open calendar']").click()

    @WebAction()
    def __set_date_field(self, day, month_str, full_month_str, year):
        """Set date field"""
        title = self._driver.find_element(By.XPATH, f"{self._base_menu_xp}//*[contains(@class, 'k-calendar-title')]")

        title.click()
        title.click()

        decade = self._driver.find_element(
            By.XPATH,
            f"{self._base_menu_xp}"
            f"//*[contains(@class, 'k-calendar-navigation')]"
            f"//*[text()='{10 * (year // 10)}']"
        )
        self._driver.execute_script("arguments[0].scrollIntoView();", decade)
        WebDriverWait(self._driver, 10).until(EC.element_to_be_clickable(decade))
        decade.click()

        self._driver.find_element(
            By.XPATH,
            f"{self._base_menu_xp}"
            f"//*[contains(@class, 'k-calendar-table')]"
            f"//*[text()='{year}']"
        ).click()

        self._driver.find_element(
            By.XPATH,
            f"{self._base_menu_xp}"
            f"//*[contains(@class, 'k-calendar-table')]"
            f"//*[contains(@class, 'k-calendar-caption') and text()='{year}']/ancestor::tbody"
            f"//*[text()='{month_str}']"
        ).click()

        self._driver.find_element(
            By.XPATH,
            f"{self._base_menu_xp}"
            f"//*[contains(@class, 'k-calendar-table')]"
            f"//*[contains(@class, 'k-calendar-caption') and text()='{full_month_str} {year}']/ancestor::tbody"
            f"//*[text()='{day}']"
        ).click()

    @WebAction()
    def _set_date_input(self, text):
        """enters text into input"""
        inp = self._driver.find_element(By.XPATH, f"{self._base_xp}//input")
        inp.send_keys(Keys.CONTROL + 'a' + Keys.DELETE)
        for ch in text:  # since send_keys(text) doesn't work
            inp.send_keys(ch)

    @PageService()
    def _set_date_controller(self, day, month, year):
        """set date"""
        day = int(day)
        year = int(year)

        # convert month to str
        month = int(month)
        month, full_month = datetime(year=year, month=month, day=day).strftime("%b %B").split()

        self.__set_date_field(day, month, full_month, year)

    @PageService()
    def set_date_controller(self, day, month, year):
        """Set Date on DatePicker"""

        self._click_controller()
        self._set_date_controller(day, month, year)

    @PageService()
    def set_date_input(self, day, month, year):
        """types time in input element"""
        self._set_date_input(datetime(year=year, month=month, day=day).strftime("%b %d %Y"))


class DateTimePickerController(DatePickerController, TimePickerController):
    """DateTimePicker control type for Date DataType"""

    @property
    def control_type(self):
        return "DateTimePicker"

    @WebAction()
    def _click_set(self):
        """clicks set"""
        self._driver.find_element(By.XPATH, "//button[@title='Set']").click()

    @PageService()
    def set_date_time_controller(self, day, month, year, hour, minute, am=True):
        """Set DateTime on the DateTime input controller"""
        self._click_controller()
        self._set_date_controller(day, month, year)
        self._set_time_controller(hour, minute, am)
        self._click_set()

    @WebAction()
    def _set_date_time_input(self, text):
        """enters text into input"""
        inp = self._driver.find_element(By.XPATH, f"{self._base_xp}//input")
        inp.send_keys(Keys.CONTROL + 'a' + Keys.DELETE)
        for ch in text:  # since send_keys(text) doesn't work
            inp.send_keys(ch)

    @PageService()
    def set_date_time_input(self, day, month, year, hour, minute, am=True):
        """types time in input element"""
        self._set_date_time_input(datetime(year=year, month=month, day=day, hour=hour, minute=minute).strftime("%b %d %Y %I %M %p"))


class DateRangeController(DropDownController):
    """DateRange control type for DateRange DataType"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._dialog = None
        self._from_date = None
        self._to_date = None

    @PageService()
    def configure(self, *args, **kwargs):
        """configures self and datetime controllers"""
        super().configure(*args, **kwargs)

        self._dialog = RModalDialog(self._adminconsole)

        base_xp_templ = (f"{self._dialog.base_xpath}//label[text()='%s']"
                         f"/following-sibling::*[contains(@class, 'cv-date-time-picker-container')]")

        self._from_date = DateTimePickerController('', base_xp=base_xp_templ % 'From date')
        self._to_date = DateTimePickerController('', base_xp=base_xp_templ % 'To date')

        self._from_date.configure(*args, **kwargs)
        self._to_date.configure(*args, **kwargs)

    @property
    def control_type(self):
        return "DateRange"

    @PageService()
    def set_relative_daterange(self, relative_daterange):
        """select relative daterange options from the input controller

        Args:
            relative_daterange (str) : option in the daterange dropdown
                                       Ex - "Last 6 months", "Last 1 year" etc.
        """
        self.select_value(relative_daterange)
        self.apply()

    @PageService()
    def set_custom_relative_daterange(self, val, unit):
        """sets custom relative daterange"""
        self.select_value('Custom')
        self._dialog.select_radio_by_id('Relative')
        self._dialog.fill_text_in_field('number', val)
        RDropDown(
            self._adminconsole,
            base_element=self._driver.find_element(By.XPATH, self._dialog.base_xpath)
        ).select_drop_down_values(index=1, values=[unit])
        self._dialog.click_button_on_dialog(id='Save')

    @PageService()
    def set_custom_daterange(self, from_datetime: datetime, to_datetime: datetime):
        """sets custom daterange"""

        from_year, from_month, from_day, from_hr, from_min, from_am = from_datetime.strftime("%Y %m %d %I %M %p").split()
        to_year, to_month, to_day, to_hr, to_min, to_am = to_datetime.strftime("%Y %m %d %I %M %p").split()

        self.select_value('Custom')
        self._dialog.select_radio_by_id('Between')
        self._from_date.set_date_time_controller(from_day, from_month, from_year, from_hr, from_min, from_am == 'AM')
        self._to_date.set_date_time_controller(to_day, to_month, to_year, to_hr, to_min, to_am == 'AM')

        self._dialog.click_button_on_dialog(id='Save')
