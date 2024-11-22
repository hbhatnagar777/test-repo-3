from selenium.webdriver.common.by import By
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import WebDriverException
from AutomationUtils.logger import get_log

from Web.Common.page_object import (
    WebAction, PageService
)


class Dashboard:

    def __init__(self, webconsole, name):
        self.__webconsole = webconsole
        self.__driver = webconsole.browser.driver
        self.name = name

    def __str__(self):
        return f"<Dashboard name=[{self.name}] id=[{id(self)}]>"

    @WebAction()
    def __set_component_name(self, name):
        """Set the name of the component"""
        textfield = self.__driver.find_element(By.XPATH, 
            "//*[@data-ng-model='titleText']"
        )
        textfield.send_keys(name)

    @WebAction()
    def __select_report(self, report_name):
        """Select report"""
        select = Select(self.__driver.find_element(By.XPATH, 
            "//select[@data-ng-model='reportId']"
        ))
        select.select_by_visible_text(report_name)

    @WebAction()
    def __select_component(self, comp_name):
        """Select component"""
        select = Select(self.__driver.find_element(By.XPATH, 
            "//select[@data-ng-model='componentId']"
        ))
        select.select_by_visible_text(comp_name)

    @WebAction()
    def __click_refresh(self):
        """Refresh the dashboard"""
        refresh_btn = self.__driver.find_element(By.XPATH, 
            "//*[@id='refreshButton']"
        )
        refresh_btn.click()

    @WebAction()
    def __click_add_report(self):
        """Click add new report"""
        add_report = self.__driver.find_element(By.XPATH, 
            "//*[@id='addNewReport']"
        )
        add_report.click()

    @WebAction()
    def __click_ok(self):
        """Click OK"""
        ok_button = self.__driver.find_element(By.XPATH, 
            "//button[@ng-click='updateUrlAndClose()']"
        )
        ok_button.click()

    @WebAction()
    def __switch_to_component(self, title):
        """Get frame ID from component Title and switch to it"""
        li_obj = self.__driver.find_element(By.XPATH, 
            f"//li[.//span[text()='{title}']]"
        )
        frame_id = li_obj.get_attribute("comp")
        self.__driver.switch_to.frame(f"frame-{frame_id}")

    @WebAction()
    def __set_url(self, url):
        """Set URL"""
        field = self.__driver.find_element(By.XPATH, 
            "//input[@data-ng-model='url']"
        )
        field.send_keys(url)

    @WebAction()
    def __select_component_type(self, type_):
        """Set component type"""
        dropdown = Select(self.__driver.find_element(By.XPATH, 
            "//select[@data-ng-model='frameType']"
        ))
        dropdown.select_by_visible_text(type_)

    @PageService()
    def refresh(self):
        """Refresh dashboard"""
        self.__click_refresh()
        self.__webconsole.wait_till_load_complete()

    @PageService()
    def add_report(self, report_name, comp_id):
        """Add report"""
        self.__click_add_report()
        self.__set_component_name(comp_id)
        self.__select_component_type("Report")
        self.__select_report(report_name)
        self.__select_component(comp_id)
        self.__click_ok()
        self.__webconsole.wait_till_load_complete()
        self.__webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=[
                f"Dashboard {self.name} updated successfully."
            ]
        )

    @PageService()
    def add_url(self, name, url):
        """Add URL to the dashboard"""
        self.__click_add_report()
        self.__set_component_name(name)
        self.__select_component_type("Custom")
        self.__set_url(url)
        self.__click_ok()
        self.__webconsole.wait_till_load_complete()

    @PageService()
    def focus_component(self, component):
        """Associate component to Dashboard"""
        self.__switch_to_component(component.title)
        component.configure_viewer_component(
            self.__webconsole, "Page0"
        )

    @PageService()
    def un_focus_all_components(self):
        """Associate component to Dashboard"""
        self.__driver.switch_to.default_content()


class DashboardManager:

    def __init__(self, webconsole):
        self.__webconsole = webconsole
        self.__driver = webconsole.browser.driver

    @WebAction()
    def __click_new_dashboard(self):
        """Click new dashboard"""
        button = self.__driver.find_element(By.XPATH, 
            "//button/*[.='New Dashboard']"
        )
        button.click()

    @WebAction()
    def __set_name(self, name):
        """Set dashboard name"""
        WebDriverWait(self.__driver, 60).until(ec.visibility_of_element_located(
            (By.ID, "dashboard-name")))
        name_field = self.__driver.find_element(By.XPATH, 
            "//*[@id='dashboard-name']"
        )
        name_field.send_keys(name)

    @WebAction()
    def __set_description(self, desc):
        """Set dashboard description"""
        desc_field = self.__driver.find_element(By.XPATH, 
            "//*[@id='dashboard-description']"
        )
        desc_field.send_keys(desc)

    @WebAction()
    def __click_add(self):
        """Click add button"""
        add_button = self.__driver.find_element(By.XPATH, 
            "//*[@id='addDashboardButton']"
        )
        add_button.click()

    @WebAction()
    def __click_delete(self, dashboard_name):
        """Click delete"""
        del_href = self.__driver.find_element(By.XPATH, 
            f"//tr[.//a[.='{dashboard_name}']]//a[@title='Delete']"
        )
        del_href.click()

    @WebAction()
    def __confirm_delete(self):
        """Click OK on confirmation popup"""
        alert = self.__driver.switch_to.alert
        alert.accept()

    @WebAction()
    def __click_dash_hyperlink(self, dashboard_name):
        """Click Dashboard hyperlink"""
        dash = self.__driver.find_element(By.XPATH, 
            f"//a[.='{dashboard_name}' and @href]"
        )
        dash.click()

    @PageService()
    def add_dashboard(self, name, description=None):
        """Add dashboard"""
        self.__click_new_dashboard()
        self.__set_name(name)
        if description:
            self.__set_description(description)
        self.__click_add()
        sleep(2)
        self.__webconsole.wait_till_load_complete()
        self.__webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=[
                f"Dashboard {name} created successfully."
            ]
        )
        return Dashboard(self.__webconsole, name)

    @PageService()
    def delete(self, name):
        """Delete dashboard"""
        self.__click_delete(name)
        self.__confirm_delete()
        self.__webconsole.wait_till_load_complete()
        self.__webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=[
                f"Report {name} deleted successfully."
            ]
        )

    def delete_silently(self, dashboard_name):
        try:
            self.delete(dashboard_name)
        except WebDriverException as err:
            get_log().info(
                f"[{dashboard_name}] not found to delete "
                f"[{' '.join(str(err).splitlines())}]"
            )

    @PageService()
    def open(self, dashboard_name):
        """Open dashboard"""
        self.__click_dash_hyperlink(dashboard_name)
        self.__webconsole.wait_till_load_complete()


class URLAdaptor:

    def __init__(self, title, custom_report_viewer):
        self.__report_viewer = custom_report_viewer
        self.title = title

    def configure_viewer_component(self, webconsole, page):
        pass

    def get_all_component_titles(self):
        return self.__report_viewer.get_all_component_titles()
