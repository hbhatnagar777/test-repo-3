from selenium.webdriver.common.by import By
"""
Common classes and functions used in contract management page
"""
from selenium.webdriver.support.ui import Select
from Web.Common.exceptions import CVWebAutomationException
from Web.WebConsole.webconsole import WebConsole
from Web.Common.page_object import (
    WebAction, PageService
)
from AutomationUtils import logger, config

_CONFIG = config.get_config()


class BillingConstants:
    """
    Constants used fin Billing classes
    """
    BILLING_CYCLE_MONTHLY = "Monthly"
    BILLING_CYCLE_QUARTERLY = "Quarterly"
    USE_AS_PURCHASE_ORDER_YES = "Yes"
    USE_AS_PURCHASE_ORDER_NO = "No"


class BillingGroupOptions:
    """
    Common functions used for contract management feature.
    """

    def __init__(self, webconsole: WebConsole):
        """
        Args:
            webconsole(webconsole): Webconsole object
        """
        self._webconsole = webconsole
        self._browser = self._webconsole.browser
        self._driver = self._webconsole.browser.driver
        self._royalty_report = RoyaltyReport(self._webconsole)
        self._log = logger.get_log()

    @WebAction()
    def _click_associate(self):
        """
        Click on associate
        """
        self._driver.find_element(By.XPATH, "//*[contains(@id, 'associate')]").click()

    @WebAction()
    def _click_edit(self, name):
        """
        Click on edit
        """
        self._driver.find_element(By.XPATH, "//*[@title = 'Edit " + name + "']").click()

    @WebAction()
    def _click_delete(self, name):
        """
        Click on delete
        """
        self._driver.find_element(By.XPATH, "//*[@title = 'Delete " + name + "']").click()

    @WebAction()
    def _click_button_dialogue_yes(self):
        """
        Click on popup dialogue yes
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Yes']").click()

    @WebAction()
    def _click_button_save(self):
        """
        Click on button save
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Save']").click()

    @WebAction()
    def _click_generate_royalty_report(self, name):
        """
        Click on button generate royalty report
        """
        self._driver.find_element(By.XPATH, "//*[@title='Generate Royalty Report for " + name +
                                           "']").click()

    @WebAction()
    def _click_partner_royalty_reports(self):
        """
        click on partner royalty reports
        """
        self._driver.find_element(By.ID, "partnerRedirectButton").click()

    @WebAction()
    def _click_service_provider_royalty_reports(self):
        """
        click on service provider royalty report
        """
        self._driver.find_element(By.ID, "aggregatorRedirectButton").click()

    @WebAction()
    def _click_manage_billing_groups(self):
        """
        click on manage billing group
        """
        self._driver.find_element(By.ID, "manageContractButton").click()

    @WebAction()
    def _click_manage_billing_group_association(self):
        """
        click on manage billing association
        """
        self._driver.find_element(By.XPATH, "//*[text()='Manage Billing Group "
                                           "Associations']").click()

    @WebAction()
    def _get_element_with_text(self, text):
        """
        find element with specified text
        """
        element = self._driver.find_elements(By.XPATH, "//table//*[text()='" + text + "']/../td[1]")
        return element

    @WebAction()
    def _click_manage_service_providers(self):
        """
        Click on manage service provider
        """
        self._driver.find_element(By.ID, "manageAggregatorButton").click()

    @WebAction()
    def _click_manage_partner(self):
        """
        Click on manage partner
        """
        self._driver.find_element(By.ID, "managePartnerButton").click()

    @WebAction()
    def is_dialog_form_visible(self):
        """
        check if dialogue panel is visible
        """
        ele = self._driver.find_elements(By.XPATH, "//*[contains(@aria-labelledby,'dialog-form')]")
        if ele:
            return True
        return False

    @WebAction()
    def _click_manage_skus(self):
        """
        Click manage sku
        """
        self._driver.find_element(By.XPATH, "//*[text()='Manage SKUs']").click()

    @PageService()
    def generate_royalty_report(self, name, download_type=None, month=None, year=None,
                                include_peak_usage=None):
        """
        Generates royalty report.
        Args:
            name(string): Name of the entity to generate royalty report
            download_type(string): pdf/html can be from constant RoyaltyReport:
            PDF/RoyaltyReport:HTML
            month(string): Provide month from RoyaltyReport: class constants
            year(string): Provide year from RoyaltyReport: class constants
            include_peak_usage: True/False to include peak usage
        """
        self._click_generate_royalty_report(name)
        self._royalty_report.generate_royalty_report(download_type, month, year,
                                                     include_peak_usage)

    @PageService()
    def access_manage_billing_assoc(self):
        """
        Clicks on manage billing group
        """
        self._click_manage_billing_group_association()

    @PageService()
    def access_manage_service_providers(self):
        """
        Clicks on manage manage service providers
        """
        self._click_manage_service_providers()

    @PageService()
    def access_manage_partner(self):
        """
        Clicks on manage partner
        """
        self._click_manage_partner()

    @PageService()
    def access_manage_billing_groups(self):
        """
        Clicks on manage billing groups
        """
        self._click_manage_billing_groups()

    @PageService()
    def access_service_provider_royalty_report(self):
        """
        Accesses service provider report link
        """
        self._click_service_provider_royalty_reports()

    @PageService()
    def access_partner_royalty_reports(self):
        """
        Clicks on partner royalty report
        """
        self._click_partner_royalty_reports()

    @PageService()
    def access_manage_skus(self):
        """
        Clicks on manage skus
        """
        self._click_manage_skus()


class RoyaltyReport:
    """
    Class can be used to communicate with royalty report options.
    """
    JANUARY = "January"
    FEBRUARY = "February"
    MARCH = "March"
    APRIL = "April"
    MAY = "May"
    JUNE = "June"
    JULY = "July"
    AUGUST = "August"
    SEPTEMBER = "September"
    OCTOBER = "October"
    NOVEMBER = "November"
    DECEMBER = "December"
    PDF = "pdf"
    html = "html"

    def __init__(self, webconsole: WebConsole):
        """
        Args:
            webconsole(WebConsole): Webconsole object
        """
        self._webconsole = webconsole
        self._browser = self._webconsole.browser
        self._driver = self._webconsole.browser.driver
        self.log = logger.get_log()

    @WebAction()
    def _click_button_ok(self):
        """
        click on button ok
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Ok']").click()

    @WebAction()
    def _click_button_cancel(self):
        """
        Click on button cancel
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Cancel']").click()

    @WebAction()
    def _select_download_as_pdf(self):
        """
        select download as pdf
        """
        self.log.info("Selecting download as pdf")
        self._driver.find_element(By.XPATH, "//input[@value='pdf']").click()

    @WebAction()
    def _select_view_as_html(self):
        """
        select view as html
        """
        self.log.info("Selecting view as html")
        self._driver.find_element(By.XPATH, "//input[@value='html']").click()

    @WebAction()
    def _select_month(self, month):
        """
        select month
        """
        self.log.info("Selecting month %s", month)
        month_select = Select(self._driver.find_element(By.ID, "monthSelect"))
        month_select.select_by_visible_text(str(month))

    @WebAction()
    def _select_year(self, year):
        """
        Select year
        """
        self.log.info("Selecting year %s", year)
        year_select = Select(self._driver.find_element(By.ID, "monthSelect"))
        years_list = [years.text for years in year_select.options]
        if year not in years_list:
            raise CVWebAutomationException("Specified year couldn't be found:%s" % year)
        year_select.select_by_visible_text(str(year))

    @WebAction()
    def _click_include_peak_usage(self):
        """
        click include peak usage
        """
        self._driver.find_element(By.ID, "includeDetails").click()

    @WebAction()
    def _click_generate_royalty_report(self, name):
        """
        click on generate royalty report
        """
        self._driver.find_element(By.XPATH, "//span[@title = 'Generate Royalty "
                                           "Report for " + name + "']").click()

    @PageService()
    def generate_royalty_report(self, name, download_type, month=None, year=None,
                                include_peak_usage=False):
        """
        Generates royalty report
        Args:
            name(string): Specify the entity name for which royalty report to be generated
            download_type(String): PDF/HTML
            month(String): Specify the month
            year(string): Specify the year
            include_peak_usage: True/False
        """
        self._click_generate_royalty_report(name)
        self._webconsole.wait_till_loadmask_spin_load()
        if download_type is None:
            pass
        elif download_type == RoyaltyReport.PDF:
            self._select_download_as_pdf()
        else:
            self._select_view_as_html()
        if month is not None:
            self._select_month(month)
        if year is not None:
            self._select_year(year)
        if include_peak_usage is True:
            self._click_include_peak_usage()
        self._click_button_ok()
