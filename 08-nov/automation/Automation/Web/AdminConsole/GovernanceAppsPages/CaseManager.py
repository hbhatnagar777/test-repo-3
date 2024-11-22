from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done on Case Manager page.

Case Manager  --  This class contains all the methods for action in Case Manager page

    Functions:

    select_dropdown_input()     -- Selects the dropdown input value of the element given the id
    get_index_copy_job_id()     --  Gets the Job Id from the popup
    submit_collection_job()     --  Submits collection job
    enter_case_details()        --  Enters the details to add a case
    create_definition()	        --  Adds a new definition to a case
    get_keyword_email_count()   --  Gets the number of emails containing that word
    select_add_case()           --  Clicks on the 'Add case' link
    select_case()               --  Opens the case page of the case with given name
    open_search_tab()           --  Opens the search tab of a case
    open_job_history()          --  Opens job history of that particular case
    select_add_definition()     --  Clicks on 'Add definition'
    click_search_button()       --  Clicks on search in Case Manager UI
    open_admin_jobs             --  Opens the Admin Jobs tab
    run_collection_job          --  Runs the case manager index copy job and verifies job completes successfully
    verify_collection_job       --  Checks whether there is an already running case manager index copy Job

"""

import re
from Web.AdminConsole.Components.panel import RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Rtable, CVTable
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.Common.exceptions import CVWebAutomationException
from selenium.common.exceptions import NoSuchElementException


class CaseManager:
    """
    This class contains all the methods for action in Case Manager page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object

        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.view_jobs_label = self.__admin_console.props['label.viewJobs']
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rpanel = RModalPanel(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__cvtable = CVTable(self.__admin_console)
        self.__compl_search = ComplianceSearch(self.__admin_console)
        self.__jobs= Jobs(self.__admin_console)
        self.__filter_count = 0
        self.__wizard=Wizard(self.__admin_console)
        self.__alert = Alert(self.__admin_console)
        self.__navigator= self.__admin_console.navigator
        self.__activate = GovernanceApps(self.__admin_console)
        self.reference_copy_job_id = None

    @WebAction()
    def __enter_custodian_value(self, value):
        """
        Enters the custodian value
        Args:
            value (str): Email id of custodian

        """
        self.__driver.find_element(By.XPATH, 
            '//input[@ng-model="model.selectedCustodian"]'
        ).send_keys(value)

    @WebAction()
    def __add_custodian(self):
        """
        Clicks on the Add button to add the custodian
        """
        self.__driver.find_element(By.XPATH, "//li[contains(text(),'Add custodians')]").click()

    @WebAction()
    def __select_filter_menu_list(self, value):
        """
        Selects the required value from the filter menu list
        Args:
            value (str): Value to be selected

        """
        values = self.__driver.find_elements(By.XPATH, 
            '//ul[@class="dropdown-menu case-filter-menu"]/li'
        )
        for option in values:
            if option.text == value:
                option.click()
                break

    @WebAction()
    def __enter_filter_text_input(self, value):
        """
        Enters the value in the field Attachment name
        Args:
            value (str): Value to be entered

        """
        self.__driver.find_elements(By.XPATH, 
            '//*[@data-ng-if="addedFilter.type === \'text\'"]'
        )[-1].find_element(By.XPATH, './/input').send_keys(value)

    @WebAction()
    def __enter_filter_folder(self, value):
        """
        Enters and selects the values in the field 'Folder'
        Args:
            value (list): List of values to be selected and entered

        """
        self.__driver.find_elements(By.XPATH, 
            '//*[@data-ng-if="addedFilter.type === \'match\'"]/div/input'
        )[-1].send_keys(value[0])
        self.__driver.find_element(By.XPATH, 
            '//*[@data-ng-if="addedFilter.type === \'match\'"]/div/select'
        ).click()
        values = self.__driver.find_elements(By.XPATH, 
            '//*[@data-ng-if="addedFilter.type === \'match\'"]/div/select/option'
        )
        for option in values:
            if value[1] == option.text:
                option.click()
                break

    @WebAction()
    def __enter_filter_received_time(self, value):
        """
        Enters the values in the field 'Received Time'
        Args:
            value (List): Time to be entered

        """
        datepickers = self.__driver.find_elements(By.XPATH, 
            '//*[@data-role="datetimepicker"]'
        )
        for i in range(2):
            r_time = (
                value[i]['Month'] +
                '/' +
                value[i]['Day'] +
                '/' +
                value[i]['Year'] +
                ' ' +
                value[i]['Hours'] +
                ':' +
                value[i]['Minutes'] +
                ' ' +
                value[i]['Time'])
            datepickers[i].clear()
            datepickers[i].send_keys(r_time)

    @WebAction()
    def __add_filter(self, additional_filter, value):
        """
        Adds a filter to the case / definition
        Args:
            additional_filter (str):Field Name
            value (list/str):       Value to be entered / selected

        """
        self.__dropdown.select_drop_down_values(
            drop_down_id='queryFilter',
            values=[additional_filter]
        )
        if additional_filter in ['Email address', 'From', 'To', 'CC', 'BCC']:
            self.__admin_console.fill_form_by_id('suggestionInput', value)
        elif additional_filter in ['Attachment name', 'Subject']:
            self.__enter_filter_text_input(value)
        elif additional_filter == 'Has attachment':
            self.__dropdown.select_drop_down_values(
                values=[value],
                drop_down_id=('selection-' + str(self.__filter_count))
            )
        elif additional_filter == 'Folder':
            self.__enter_filter_folder(value)
        elif additional_filter == 'Received time':
            self.__enter_filter_received_time(value)

    @WebAction()
    def get_index_copy_job_id(self):
        """
        Gets the Index Copy Job Id
        Returns:
            int: Job Id
        """
        return self.__alert.get_jobid_from_popup()

    @WebAction()
    def __access_links(self, text):
        """
        Access links
        """
        self.__driver.\
            find_element(By.XPATH, "//div[contains(text(),'" + text + "')]")\
            .click()

    @WebAction()
    def delete_case_confirmation(self):
        """
        To provide confirmation for delete case
        """
        self.__driver.find_element(By.XPATH, 
            '//*[@id="confirmText"]'
        ).send_keys("DELETE")
        self.__rpanel.submit()

    @WebAction()
    def get_custodian_count(self, case_name):
        """
        Get the count of custodians
        Returns:
            int : the cont of custodians
        """
        custodian_list = str(self.__rtable.get_column_data("Custodians"))
        return (len(custodian_list.split(",")))

    @WebAction()
    def __click_legal_hold(self):
        """
        Clicks on legal hold option in select case
        """
        elem = self.__driver.find_element(By.XPATH, "//li[contains(text(),'Legal hold')]")
        elem.click()

    @WebAction()
    def click_search_button(self):
        """
        Clicks on search button in casemanager search view
        """
        elem = self.__driver.find_element(By.XPATH, "//button[contains(@title,'Search')]")
        elem.click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_custodian_to_definition(self, definition, custodians):
        """
        Adds additional custodian
        Args:
            definition (str):  Definition to which custodian should be added
            custodians (list): Email id of custodians

        """
        self.__rtable.access_action_item(definition, 'Edit definition')
        self.__admin_console.wait_for_completion()
        while not self.__wizard.get_active_step()=="Data Source":
            self.__wizard.click_next()

        for custodian in custodians:
            self.__admin_console.click_button("Add")
            self.__add_custodian()
            self.__admin_console.wait_for_completion()
            self.__wizard.select_drop_down_values(id="eDiscoveryCustodiansDropdown", values=[custodian])
            self.__admin_console.click_button(id="Save")
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_button(id="Submit")
        self.__admin_console.wait_for_completion()

    @PageService()
    def submit_collection_job(self):
        """
        Submits a collection job
        """
        self.__access_links('Submit collection job')
        self.__access_links('Yes')
        return self.get_index_copy_job_id()

    @PageService()
    def verify_collection_job(self,case_name):
        """
        Checks whether there is an already running case manager index copy Job
            case_name:- name of the case manager client
        """
        job_id = None
        self.__navigator.navigate_to_jobs()
        self.__admin_console.wait_for_completion()
        try:
            job_id = self.__jobs.get_job_id_by_operation("Case Manager Index Copy", case_name)
            if not job_id:
                raise ValueError("Job Id is None")
        except (ValueError, NoSuchElementException):
            self.__admin_console.refresh_page()
            self.__navigator.navigate_to_governance_apps()
            self.__activate.select_case_manager()
            if self.__rtable.is_entity_present_in_column('Name', case_name):
                self.select_case(case_name)
            self.open_job_history()
            self.open_admin_jobs()
            try:
                job_id = self.__jobs.get_job_id_by_operation("Case Manager Index Copy", case_name)
            except (ValueError, NoSuchElementException):
                self.__admin_console.refresh_page()
        return job_id

    @PageService()
    def run_collection_job(self,case_name):
        """
        Runs the case manager index copy job and verifies job completes successfully
            case_name:- name of the case manager client
        """
        job_id = self.verify_collection_job(case_name=case_name)
        if not job_id:
            self.__navigator.navigate_to_governance_apps()
            self.__activate.select_case_manager()
            if self.__rtable.is_entity_present_in_column('Name', case_name):
                self.select_case(case_name)
            job_id=self.submit_collection_job()
        return str(job_id)

    @PageService()
    def index_copy_job(self,case_name):
        """Verifying index copy job
            case_name:- name of the case manager client
        """
        try:
            job_id=self.run_collection_job(case_name=case_name)
            index_copy_details = self.__jobs.job_completion(job_id)
            if 'Completed' == index_copy_details['Status']:
                return index_copy_details
            if not 'Completed' == index_copy_details['Status']:
                raise CVWebAutomationException("Indexcopy job  not completed successfully")
        except Exception:
            raise CVWebAutomationException(
                "Error Verifying whether collection job has been submitted")

    @PageService()
    def reference_copy_job(self,case_name):
        """Verifying Reference Copy inline
            case_name:- name of the case manager client
        """
        try:
            self.__navigator.navigate_to_governance_apps()
            self.__activate.select_case_manager()
            if self.__rtable.is_entity_present_in_column('Name', case_name):
                self.select_case(case_name)
            self.open_job_history()

            self.reference_copy_job_id = int(self.__jobs.get_job_id_by_operation(operation='Case Manager Reference Copy',server=case_name))
            self.__jobs.access_job_by_id(self.reference_copy_job_id)
            reference_copy_details = self.__jobs.job_details()
            if self.reference_copy_job_id:
                return reference_copy_details
        except Exception:
            raise CVWebAutomationException(
                'Error verifying whether all jobs get triggered inline')

    @PageService()
    def content_index_job(self,case_name):
        """Verifying CI jobs inline
            case_name:- name of the case manager client
        """
        try:
            self.__navigator.navigate_to_governance_apps()
            self.__activate.select_case_manager()
            if self.__rtable.is_entity_present_in_column('Name', case_name):
                self.select_case(case_name)
            self.open_job_history()
            self.open_admin_jobs()

            content_indexing_job_id = int(self.__jobs.get_job_id_by_operation(operation='Content Indexing',server=case_name))
            self.__jobs.access_job_by_id(content_indexing_job_id)
            content_indexing_details = self.__jobs.job_details()
            if content_indexing_job_id:
                return content_indexing_details
        except Exception:
            raise CVWebAutomationException(
                'Error verifying whether all jobs get triggered inline')

    @PageService()
    def enter_case_details(self, name, datatype, data_collection,
                           custodians, dcplan, server_plan, keyword):
        """
        Enters the basic details required to create the case
        Args:
            name (str):             Name of the Case
            datatype (str):         Type of data
            data_collection (str):  One time only, Continuous or Do not collect
            custodians (List):      Email id of custodian
            dcplan (str):           Data Classification Plan
            server_plan (str):      Server Plan
            keyword (str):          Keyword based upon which case is to be created

        """
        self.__admin_console.fill_form_by_id('appNameField', name)
        self.__wizard.select_drop_down_values(id='plan', values=[dcplan])
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.select_plan(server_plan)
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.select_drop_down_values(id="sourceDataType",values=[datatype])
        self.__wizard.select_drop_down_values(id="sourceDataIngestionType",values=[data_collection])
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        for custodian in custodians:
            self.__admin_console.click_button("Add")
            self.__add_custodian()
            self.__admin_console.wait_for_completion()
            self.__wizard.select_drop_down_values(id="eDiscoveryCustodiansDropdown", values=[custodian])
            self.__admin_console.click_button(id="Save")

        self.__admin_console.wait_for_completion()
        self.__wizard.expand_accordion('Additional criteria')
        self.__admin_console.click_button("Add criteria")
        self.__admin_console.fill_form_by_id('keywordField', keyword)

        self.__rpanel.submit()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_button(id="Submit")
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_definition(self, name, datatype, data_collection,
                          custodians, keyword, filters=None):
        """
        Enters the details required to create a definition
        Args:
            name (str):             Name of the Definition
            datatype (str):         Type of data
            data_collection (str):  One time only, Continuous or Do not collect
            custodians (list):      Email id of custodian
            keyword (str):          Keyword based upon which definition is to be created
            filters (dictionary):   List of Additional filter criteria

        """
        self.__admin_console.fill_form_by_id('caseDefinitionNameField', name)
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.select_drop_down_values(id="sourceDataType",values=[datatype])
        self.__wizard.select_drop_down_values(id="sourceDataIngestionType",values=[data_collection])
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        for custodian in custodians:
            self.__admin_console.click_button("Add")
            self.__add_custodian()
            self.__admin_console.wait_for_completion()
            self.__wizard.select_drop_down_values(id="eDiscoveryCustodiansDropdown", values=[custodian])
            self.__admin_console.click_button(id="Save")

        self.__admin_console.wait_for_completion()
        self.__wizard.expand_accordion('Additional criteria')
        self.__admin_console.click_button("Add criteria")
        self.__admin_console.fill_form_by_id('keywordField', keyword)
        if filters:  # In case filters is None
            self.__add_filter(additional_filter=filters)
            self.__filter_count += 1

        self.__rpanel.submit()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_button(id="Submit")
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_keyword_email_count(self, value):
        """
        Gets the count of emails which matches the keyword
        Args:
            value (str): Keyword to be searched for

        Returns:
            int: No of emails
        """
        self.__admin_console.fill_form_by_id('search-bar', value)
        self.click_search_button()
        email_num = int(self.__rtable.get_total_rows_count())
        return email_num

    def select_add_case(self):
        """
        Clicks on Add Case link
        """
        self.__admin_console.click_button("Add case")
        self.__click_legal_hold()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_case(self, name):
        """
        Clicks on the case with given name
        Args:
            name (str): Name of the case

        """
        self.__admin_console.select_hyperlink(name)

    @PageService()
    def open_search_tab(self):
        """
        Opens the search tab in the Case Details Page
        """
        self.__admin_console.access_tab('Search')

    @PageService()
    def open_overview_tab(self):
        """
        Opens the overview tab in the Case details Page
        """
        self.__admin_console.access_tab('Overview')

    @PageService()
    def open_admin_jobs(self):
        """
        Opens the Admin Jobs tab of case manager
        """
        self.__admin_console.access_tab('Admin jobs')
        self.__admin_console.wait_for_completion()

    @PageService()
    def open_job_history(self):
        """
        Opens the Job History of that particular case
        """
        self.__access_links("View jobs")
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_add_definition(self):
        """
        Clicks on Add definition link
        """
        self.__access_links('Add definition')

    @PageService()
    def delete_case(self, case_name):
        """
        Delete case with given name
        Args:
            case_name: Case to be deleted
        """
        self.__rtable.access_action_item(case_name, 'Close case')
        self.__admin_console.click_button("Yes")
        self.__admin_console.wait_for_completion()
        self.__rtable.access_action_item(case_name, 'Delete')
        self.__admin_console.wait_for_completion()
        self.delete_case_confirmation()
        self.__admin_console.wait_for_completion()
