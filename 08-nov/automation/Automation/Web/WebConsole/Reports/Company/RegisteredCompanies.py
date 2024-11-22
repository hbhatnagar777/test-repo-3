from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Operations related to companies page.


Companies:

    __init__()                          --  initialize instance of the Companies class,
                                             and the class attributes.

    filter_by_company_name()           --  filter monitoring page by company name.


"""
from time import sleep
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import viewer
from Web.Common.page_object import WebAction, PageService


class RegisteredCompanies:
    """Operations on companies page"""

    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._webconsole = web_console
        self.viewer = viewer.CustomReportViewer(self._webconsole)
        self.__companies_table = None

    @property
    def _companies_table(self):
        if self.__companies_table is None:
            self.__companies_table = viewer.DataTable("")
            self.viewer.associate_component(self.__companies_table)
        return self.__companies_table

    @WebAction()
    def _is_company_name_filtered(self, company_name):
        """
        Verify company page is already filtered by company name using url
        Args:
            company_name        (String)     --         name of the company

        Returns(Boolean) : True if page is filtered with company name else return false
        """
        _str = "filter.Name=%s" % company_name
        return _str in self._driver.current_url

    @WebAction()
    def _click_company_name(self, company_name):
        """
        Click on specified company name
        Args:
            company_name        (String)     --         name of the company
        """
        xpath = "//a[@title='%s']" % company_name
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _click_delete(self):
        """Click on specified company name"""
        self._driver.find_element(By.XPATH, "//button[text()='Delete']").click()

    @WebAction()
    def _client_new_commcellGroup(self):
        """
        click new commcell group button from the page
        """
        self._driver.find_element(By.ID, "newCommCellGroup").click()

    @PageService()
    def filter_by_company_name(self, company_name):
        """
        Filter by specified company name on column 'Company Name'
        Args:
            company_name        (String)     --         name of the company
        """
        if not self._is_company_name_filtered(company_name):
            self._companies_table.set_filter('Name', company_name)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_company(self, company_name):
        """Access specified company"""
        self.filter_by_company_name(company_name)
        self._click_company_name(company_name)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_companies_list(self):
        """Get companies list"""
        return self._companies_table.get_table_data()['Name']

    @PageService()
    def get_commcell_count(self):
        """Get commcell count"""
        return self._companies_table.get_table_data()['Number Of CommCells']

    @PageService()
    def edit_company(self, company_name):
        """Edit the subcompany
        Returns:
            object of Subcompany class
        """
        self._companies_table.access_action_item(company_name, 'Edit')
        sleep(5)
        return SubCompany(self._webconsole)

    @PageService()
    def delete_company(self, company_name):
        """Deletes the subcompany
        Returns:
            object of Subcompany class
        """
        self._companies_table.access_action_item(company_name, 'Delete')
        sleep(3)
        self._click_delete()
        sleep(5)

    @PageService()
    def create_company(self):
        """
        Open create subcompany menu
        Returns:
            object of Subcompany class
        """
        self._client_new_commcellGroup()
        self._webconsole.wait_till_load_complete()
        return SubCompany(self._webconsole)


class SubCompany:
    """Sub Company menu"""
    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._webconsole = web_console

    @WebAction()
    def _enter_company_name(self, name):
        """enters company name"""
        self._driver.find_element(By.XPATH, "//input[@id='companyName']").send_keys(name)
        sleep(3)

    @WebAction()
    def _click_prefix(self):
        """click prefix"""
        self._driver.find_element(By.XPATH, "//div[@id='prefixWrapper']").click()

    @WebAction()
    def _select_prefix(self, prefix):
        """enters company name"""
        cc_name = self._driver.find_element(By.XPATH, 
            f"//li[@class='prefix-item' and text()='{prefix}']"
        )
        cc_name.click()

    @WebAction()
    def _click_commcells(self):
        """click Commcell dropdown"""
        self._driver.find_element(By.XPATH, "//input[@id='commCellGroup_filterText-2']").click()

    @WebAction()
    def _select_commcells(self, commcells):
        """
        select commcells
        Args:
            commcells (list): list of commcell name
       """
        for cc in commcells:
            sleep(3)
            self._driver.find_element(By.XPATH, "//input[@id='commCellGroup_filterText-2']").send_keys(cc, Keys.ENTER)
            try:
                xp_select_checkbox = f"//td[contains(text(), '{cc}')]/..//input[@type='checkbox']"
                self._driver.find_element(By.XPATH, xp_select_checkbox).click()
            except NoSuchElementException as expt:
                raise NoSuchElementException(f"CommCell {cc} not found in the list") from expt

    @WebAction()
    def _remove_commcells(self, commcells):
        """
        Removes commcells
        Args:
            commcells (list): list of commcell name
      """
        self._select_commcells(self, commcells)

    @WebAction()
    def _switch_users_tab(self):
        """ click users"""
        self._driver.find_element(By.ID, 'usersTab').click()

    @WebAction()
    def _click_add_user(self):
        """clicks add user"""
        self._driver.find_element(By.ID, 'addCompanyUser').click()

    @WebAction()
    def _enter_user_name(self, username):
        """enters user name"""
        xp1 = "//div[@id='addUserDialogWrapper']/..//input[@id='userName']"
        new_user = self._driver.find_element(By.XPATH, xp1)
        new_user.clear()
        new_user.send_keys(username)

    @WebAction()
    def _enter_email(self, email_id):
        """Fill the email field"""
        xp = "//div[@id='addUserDialogWrapper']/..//input[@id='email']"
        email = self._driver.find_element(By.XPATH, xp)
        email.clear()
        email.send_keys(email_id)

    @WebAction()
    def _click_add(self):
        """click add button"""
        xp = "//button[@type='button']/..//span[text()='Add']"
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def _click_save(self):
        """clicks save button"""
        self._driver.find_element(By.XPATH, "//a[@class='okSaveButton']").click()

    @WebAction()
    def _click_update(self):
        """clicks update button"""
        self._driver.find_element(By.XPATH, "//button[text()='Update']").click()

    @WebAction()
    def _click_cancel(self):
        """clicks cancel button"""
        self._driver.find_element(By.XPATH, "//a[@id='cancelButton']").click()

    @WebAction()
    def _click_delete_user(self, email_id):
        """Click on delete icon for users"""
        self._driver.find_element(By.XPATH, 
            f"//td[@title='{email_id}']/..//span[@title='Remove User']"
        ).click()

    @WebAction()
    def _read_saved_commcells(self):
        """read saved commcells"""
        xp = "//input[@checked]/ancestor::td//following-sibling::td[@data-label='CommCell Name']"
        commcells = self._driver.find_elements(By.XPATH, xp)
        return [each_cc.text.split(' - ')[1] for each_cc in commcells if each_cc.text]

    @WebAction()
    def _read_emails(self):
        """gets the assoicated users email id"""
        emails = []
        xp = "//td[@data-label='User Email']"
        email_obj = self._driver.find_elements(By.XPATH, xp)
        for email in email_obj:
            emails.append(email.text)
        return emails

    @PageService()
    def get_commcells(self):
        """Gets commcells present in subcompany
        Returns: Commcell names list in the format displayed in webpage"""
        return self._read_saved_commcells()

    @PageService()
    def add_commcells(self, commcell_name):
        """Adds more comcells in subcompany"""
        self._click_commcells()
        self._select_commcells(commcell_name)

    @PageService()
    def delete_commcells(self, commcell_name):
        """deselect the comcells from subcompany"""
        self._select_commcells(commcell_name)

    @PageService()
    def delete_user(self, user_emailid):
        """Deletes the user"""
        self._switch_users_tab()
        self._click_delete_user(user_emailid)

    @PageService()
    def add_user(self, user_name, user_email_id):
        """Adds the user"""
        self._switch_users_tab()
        self._click_add_user()
        self._enter_user_name(user_name)
        self._enter_email(user_email_id)

    @PageService()
    def save_user(self):
        """click on save user"""
        self._click_save()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def update(self):
        """Clicks on Update Button"""
        self._click_add()
        self._click_save()
        self._webconsole.wait_till_load_complete()
        sleep(5)  # wait for process to be submitted and to receive notification

    @PageService()
    def cancel(self):
        """Clicks on Cancel Button"""
        self._click_cancel()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def create(self, prefix, name, commcells, users):
        """
        creates new subcompany
        Args:
            prefix      (str): prefix for subcompany
            name        (str): name of subcompany
            commcells  (list): list of commcell names
            users      (list): list of dictionary containing username and email

            ex.: [{
            'user_name': 'user1',
            'email': 'email@email.com'
            }
            ]
        """
        self._click_prefix()
        self._select_prefix(prefix)
        self._enter_company_name(name)
        self._click_commcells()
        self._select_commcells(commcells)
        for each_user in users:
            self._switch_users_tab()
            self._click_add_user()
            self._enter_user_name(each_user['user_name'])
            self._enter_email(each_user['email'])
            self._click_add()
        self._click_save()
        self._webconsole.wait_till_load_complete()
        sleep(5)   # wait for process to be submitted and to receive notification

    @PageService()
    def get_associated_users(self):
        """returns associated users email id"""
        self._switch_users_tab()
        return self._read_emails()
