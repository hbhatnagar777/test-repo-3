# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Companies page on the AdminConsole

Class:

    Companies()

Functions:

_init_()                        :     initialize the class object

__set_company_name()            :     fill the company name field with the specified
                                      company name

__set_email()                   :     fill the email field with the specified email

__set_contact_name()            :     fill the contact name field with the specified
                                      contact name

__set_plans()                   :     fill the plans field with the specified plans

__set_company_alias()           :     fill the company alias field with the specified
                                      company alias

__set_smtp()                    :     fill the smtp field with the specified smtp alias

__enable_custom_domain()        :     Check/Uncheck the *Enable custom domain* checkbox

__set_primary_domain()          :     fill the primary domain field with the specified
                                      primary domain

__click_add_company()           :     clicks the link add company

__submit_company()              :     clicks the save button in company

add_company()                   :     adds the new company clicking save

------------------------------ COMPANIES ACTIONS ----------------------------------

deactivate_and_delete_company() :     deletes the selected company

deactivate_company()            :     deactivates a company

delete_company()                :     deletes a company

activate_company()              :     Method to activate a company from companies page

access_tags()                   :     Method to access the tags of company

delete_tags()                   :     Method to delete tags of company

add_tags()                      :     Method to add tags to company

access_operators()              :     Method to access the operators of company

delete_operators()              :     Method to delete operators of company

add_operators()                 :     Method to add operators to company

access_configure()              :     Method to access the configure option from company actions

unlink_company()                :     method to unlink a company

------------------------------ COMPANIES LINKS ----------------------------------

access_company()                :     Method to open company details from companies page

access_self_company()           :     Method for tenant admins who are reseller to access their own company

access_entities_summary()       :     Method to access the entities summary of company

access_entities_link()          :     Method to access the entity link from entity summary of company

access_edit()                   :     Method to access the edit company next to company name

access_dashboard()              :     Method to access the dashboard icon next to company name

------------------------------ COMPANIES VIEWS ----------------------------------

company_exists()                :     Method to check if a company is present on the companies page

set_scope_local()               :     Method to set the scope view to local or global

get_active_companies()          :     Method to get active companies

get_all_companies()             :     Method to get all companies

unlink_company()                :     method to unlink a company

companies_exist()               :     method to check if list of companies are present in the company listing page

get_deactivated_companies()     :     Method to get deactivated companies

get_deleted_companies()         :     Method to get deleted companies

------------------------------ MISC ----------------------------------

edit_company_name()             :     method to edit company's name

"""

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.callout import CompanyEntitiesCallout
from Web.AdminConsole.Components.dialog import ServiceCommcellSelectionDialog, TagsDialog, SecurityDialog
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import  Rtable
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import RModalDialog, RTags
from Web.AdminConsole.Components.core import Checkbox

class Companies:
    """ Class for Companies page in Admin Console """

    def __init__(self, adminconsole):
        """
        Method to initiate Companies class

        Args:
            adminconsole   (Object) :   Adminconsole Class object
        """
        self.__admin_console = adminconsole
        self.__table = Rtable(self.__admin_console)
        self.__driver = adminconsole.driver
        self.__drop_down = RDropDown(self.__admin_console)
        self.__navigator = self.__admin_console.navigator
        self.__page_container = PageContainer(self.__admin_console)
        self.__workload_selection = ServiceCommcellSelectionDialog(self.__admin_console)
        self.__tags_dialog = RTags(self.__admin_console)
        self.__operators_dialog = SecurityDialog(self.__admin_console, 'Edit operators', True)
        self.__callout = CompanyEntitiesCallout(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__admin_console.load_properties(self, unique=True)
        self.__admin_console.load_properties(self)

    # # # COMPANY TABLE ACTIONS # # #

    @PageService()
    def add_company(self,
                    company_name,
                    email=None,
                    contact_name=None,
                    plans=None,
                    company_alias=None,
                    smtp_alias=None,
                    mail_template=None,
                    primary_domain=None,
                    service_commcell=None):
        """ Method to add new company as per inputs provided as arguments

            Args:
                company_name (string) : Name of the company to be created

                company_alias (string): company alias for the company

                smtp_alias (string)   : smtp alias for the company

                primary_domain (string): primary_domain to be set for the company to be
                                        created

                email (string)        : email of Tenant admin for the company to be
                                        created

                contact_name (string) : Contact name for the company

                mail_template (str)   : mail template to be used to send intimation after
                                        company creation

                plans (list)          : plans to be associated to the company

                service_commcell  (str): Target commcell where to add company

            Returns:
                None

            Raises:
                Exception:
                    -- if fails to set primary_domain for the company
        """
        self.__table.access_toolbar_menu(self.__admin_console.props['Companies']['label.addSubscription'])
        if service_commcell:
            self.__workload_selection.select_commcell(service_commcell) #TODO: convert this to react as well

        self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']['label.companyName'], text=company_name)
        if not company_alias:
            raise Exception("Company alias required")

        self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']['label.companyAlias'], text=company_alias)
        if smtp_alias:
            # self.__wizard.fill_text_in_field(label=self.__admin_console.props['label.associatedSMTP'], text=smtp_alias)
            self.__wizard.fill_text_in_field(label="Associated SMTP", text=smtp_alias)

        if primary_domain:
            self.__wizard.enable_toggle(self.__admin_console.props['Companies']['label.enableCustomDomain'])
            self.__admin_console.wait_for_completion()
            self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']["label.primaryDomainName"], text=primary_domain)
        else:
            self.__wizard.disable_toggle(self.__admin_console.props['Companies']['label.enableCustomDomain'])
            self.__admin_console.wait_for_completion()

        self.__wizard.click_next()
        self.__admin_console.check_for_react_errors()

        if not contact_name and not email:
            self.__wizard.click_button(self.__admin_console.props['Skip'])
            self.__admin_console.check_for_react_errors()
        else:
            self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']['label.email'], text=email)
            self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']['label.fullName'], text=contact_name)

            if mail_template:
                mail_template = [mail_template]
                self.__wizard.enable_toggle(self.__admin_console.props['Companies']['label.sendOnboardingEmail'])
                self.__admin_console.wait_for_completion()
                self.__drop_down.select_drop_down_values(drop_down_id='templateList', values=mail_template)
            else:
                self.__wizard.disable_toggle(self.__admin_console.props['Companies']['label.sendOnboardingEmail'])
                self.__admin_console.wait_for_completion()

            self.__wizard.click_next()
            self.__admin_console.check_for_react_errors()

        if plans:
            self.__wizard.enable_toggle('Configure plan')
            for plan in plans:
                self.__wizard.select_plan(plan)
    
        else:
            self.__wizard.disable_toggle('Configure plan')

        self.__wizard.click_button("Submit")
        self.__admin_console.check_error_message()

    @PageService()
    def deactivate_and_delete_company(self,
                                      company_name,
                                      company_disable_login=None,
                                      company_disable_backup=None,
                                      company_disable_restore=None):
        """
        Method to deactivate and delete a company

        Args:
            company_name (str) : Name of the company to be deleted

            company_disable_login (bool) : if login to be disabled while de-activating
                                           the company

            company_disable_backup (bool) : if backup to be disabled while de-activating
                                            the company

            company_disable_restore (bool) : if restore to be disabled while de-activating
                                             the company

        Returns:
            None

        Raises:
            Exception:
                -- if fails delete company with given name
        """
        self.deactivate_company(company_name, company_disable_login, company_disable_backup, company_disable_restore)
        self.delete_company(company_name)

    def companies_exist(self, company_list: list) -> bool:
        """Method to check if list of companies are present in the company listing page

        Args:
            company_list (list): List of companies to check if present on company listing page

        Returns:
            Bool: If all companies are present or not, if even one is not present returns False, else True
        """
        all_companies = self.get_all_companies()
        for company in company_list:
            if company not in all_companies:
                raise CVWebAutomationException(f"{company} not present in the Company listing page")

        return True

    @PageService()
    def deactivate_company(self,
                           company_name,
                           company_disable_login=None,
                           company_disable_backup=None,
                           company_disable_restore=None):
        """
        Method to deactivate a company

        Args:
            company_name (str) : Name of the company to be deactivated

            company_disable_login (bool) : if login to be disabled while de-activating
                                           the company

            company_disable_backup (bool) : if backup to be disabled while de-activating
                                            the company

            company_disable_restore (bool) : if restore to be disabled while de-activating
                                             the company

        Returns:
            None

        Raises:
            Exception:
                -- if fails deactivate company with given name
        """
        self.__table.set_default_filter("Status", "All")
        self.__table.access_action_item(company_name, 'Deactivate')
        check_box = Checkbox(self.__admin_console, "//div[contains(@class, 'mui-modal-dialog mui-modal-centered')]")
        if company_disable_login:
            check_box.uncheck(self.__admin_console.props['Companies']['label.disableLogin'])
        elif company_disable_backup:
            check_box.uncheck(self.__admin_console.props['Companies']['label.disableBackup'])
        elif company_disable_restore:
            check_box.uncheck(self.__admin_console.props['Companies']['label.disableRestore'])
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_company(self, company_name):
        """
        Method to delete a company

        Args:
            company_name (str) : Name of the company to be deleted

        Raises:
            Exception:
                -- if fails delete company with given name
        """
        self.__table.set_default_filter("Status", "All")
        self.__table.access_action_item(company_name, 'Delete')
        self.__dialog.type_text_and_delete("Permanently delete company with data loss")
        self.__admin_console.check_error_message()

    @PageService()
    def activate_company(self, company_name):
        """Method to activate a company from companies page

        Args:
            company_name (str): company name to activate
        """
        self.__table.set_default_filter("Status", "All")
        self.__table.access_action_item(company_name, 'Activate')
        self.__admin_console.check_error_message()

    @PageService()
    def access_tags(self, company_name, close=True):
        """Method to access the tags dialog of company and get the tags visible

        Args:
            company_name    (str)   -   name of company to access tags of
            close   (bool)          -   will close the dialog after reading if True

        Returns:
            tags    (list)  -   list of dicts containing the tags
            example:
                [
                    {
                    "name": "key1",
                    "value": "value1"
                    },
                    {
                    "name": "key2",
                    "value": "value2"
                    }
                ]
        """
        if not self.__tags_dialog.is_dialog_present():
            self.__table.set_default_filter("Status","All")
            self.__table.access_action_item(company_name, 'Manage tags')
        tags_visible = self.__tags_dialog.get_tags()
        if close:
            self.__tags_dialog.click_cancel()
        return tags_visible

    @PageService()
    def delete_tags(self, company_name, tags):
        """Deletes the given tags from company

        Args:
            company_name    (str)   -   name of company whose tags to delete
            tags    (list)  -   list of dicts with tag details
                    example - [
                                    {
                                    "name": "key1",
                                    "value": "value1"
                                    },
                                    {
                                    "name": "key2",
                                    "value": "value2"
                                    }
                                ]
        """
        self.__table.set_default_filter("Status","All")
        self.__table.access_action_item(company_name, 'Manage tags')
        for tag in tags:
            self.__tags_dialog.delete_tag(tag["name"], tag.get("value", ""))
        self.__tags_dialog.click_submit()

    @PageService()
    def add_tags(self, company_name, tags):
        """Adds the given tags to company

        Args:
            company_name    (str)   -   name of company where to add tags
            tags    (list)  -   list of dicts with tag details
                    example - [
                                    {
                                    "name": "key1",
                                    "value": "value1"
                                    },
                                    {
                                    "name": "key2",
                                    "value": "value2"
                                    }
                                ]
        """
        self.__table.set_default_filter("Status","All")
        self.__table.access_action_item(company_name, 'Manage tags')
        for tag in tags:
            self.__tags_dialog.add_tag(tag["name"], tag.get("value", ""))
        self.__tags_dialog.click_submit()

    @PageService()
    def access_operators(self, company_name, close=True):
        """Method to access the operators dialog of company and get the associations

        Args:
            company_name    (str)   -   name of company to access tags of
            close   (bool)          -   will close the dialog after reading if True

        Returns:
            operators    (list)  -   list of dicts containing the associations
            example:
                [
                    {'role':'<name of role>','userGroup':'<usergroupname>'},
                    {'role':'<name of role>','user':'<username>'}
                ]
        """
        if not self.__operators_dialog.is_dialog_present():
            self.__table.set_default_filter("Status","All")
            self.__table.access_action_item(company_name, 'Manage operators')
        operators = self.__operators_dialog.get_user_role_associations()
        operators+= self.__operators_dialog.get_usergroup_role_associations()
        if close:
            self.__operators_dialog.click_cancel()
        return operators

    @PageService()
    def delete_operators(self, company_name, operators):
        """Deletes the given operators from company

        Args:
            company_name    (str)   -   name of company whose tags to delete
            operators    (list)  -   list of dicts with operator association details
                    example -  [
                    {'role':'<name of role>','userGroup':'<usergroupname>'},
                    {'role':'<name of role>','user':'<username>'}
                ]
        """
        if not self.__operators_dialog.is_dialog_present():
            self.__table.set_default_filter("Status","All")
            self.__table.access_action_item(company_name, 'Manage operators')
        for operator in operators:
            self.__operators_dialog.remove_association(
                operator.get("user") or operator.get("userGroup"),
                operator["role"]
            )
        self.__operators_dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def add_operators(self, company_name, operators):
        """Adds the given tags to company

        Args:
            company_name    (str)   -   name of company where to add operators
            operators    (list)  -   list of dicts with association details
                    example - [
                    {'role':'<name of role>','userGroup':'<usergroupname>'},
                    {'role':'<name of role>','user':'<username>'}
                ]
        """
        if not self.__operators_dialog.is_dialog_present():
            self.__table.set_default_filter("Status","All")
            self.__table.access_action_item(company_name, 'Manage operators')
        for operator in operators:
            self.__operators_dialog.add_association(
                operator.get("user") or operator.get("userGroup"),
                operator["role"]
            )
        self.__operators_dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def access_configure(self, company_name):
        """
        Access the configure link from company actions

        Args:
            company_name    (str)   -   name of company
        """
        self.__table.access_action_item(company_name, 'Configure')
        self.__admin_console.wait_for_completion()

    @PageService()
    def unlink_company(self, company_name):
        """
        Method to unlink a company

        Args:
            company_name (string): Name of workload company to unlink
        Raises:
            Exception:
            -- if company unlinking fails
        """
        self.__table.access_action_item(company_name, 'Unlink Metallic')
        self.__admin_console.click_button("Yes")
        self.__admin_console.click_button("Yes")
        self.__admin_console.check_error_message()

    # # # COMPANY TABLE LINKS # # #

    @PageService()
    def access_company(self, company_name, status="All", deactivated=False):
        """ Method to open company details from companies page 
        
        Args:
            company_name (str): company name to open
            status (str): default filter (status) value
        """
        self.__table.set_default_filter("Status",status)
        self.__table.access_link(company_name)
        if not deactivated:
            self.__admin_console.select_overview_tab()

    @PageService()
    def access_self_company(self, company_name, multicommcell=False):
        """ Method for tenant admins who are reseller to access their own company 
        
        Args:
            company_name (str):     company name to open
            multicommcell (bool):   if company is multicommcell company
        """
        self.__table.set_default_filter("Status","All")
        self.__table.access_link(company_name)

        if multicommcell:
            self.__navigator.navigate_to_company()

    @PageService()
    def access_entities_summary(self, company_name, close=True):
        """
        Accesses the entity summary callout for the company and returns Entity counts

        Args:
            company_name    (str)    -   name of the company
            close   (bool)           -   will close the callout after reading if True

        Returns:
            dict    -   dict with entity name as key and count as value
                        example:    {
                            'Alerts definitions': '1',
                            'Server group': '2',
                            'User group': '3',
                            'total': '6'
                        }
        """
        self.__table.set_default_filter("Status","All")
        self.__table.clear_search()
        self.__table.search_for(company_name)
        total = self.__table.get_column_data('Entities')[0]
        self.__table.click_cell_text(company_name, 'Entities', span_class='associated-entities')
        self.__admin_console.wait_for_completion()
        if not self.__callout.is_callout_open():
            raise CVWebAutomationException("Entities Callout failed to Open")
        data = self.__callout.get_entities_data()
        data['total'] = total
        if close:
            self.__table.click_title()
            self.__admin_console.wait_for_completion()
        return data

    @PageService()
    def access_entities_link(self, company_name, entity_name):
        """
        Accesses the entity count redirection link

        Args:
            company_name    (str)   -   name of company
            entity_name     (str)   -   name of entity (User/User group/File servers....)
        """
        if not self.__callout.is_callout_open():
            self.__table.set_default_filter("Status","All")
            self.__table.clear_search()
            self.__table.search_for(company_name)
            self.__table.click_cell_text(company_name, 'Entities', span_class='associated-entities')
            self.__admin_console.wait_for_completion()
        self.__callout.access_entity_link(entity_name)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __hover_row_click(self, company_name, title):
        """
        Hovers over company's row and clicks on svg link with given title

        Args:
            company_name    (str)   -   name of company
            title   (str)           -   title of svg icon
        """
        hover_span = self.__driver.find_element(By.XPATH, 
            f"//*[text()='{company_name}']/ancestor::tr//div[@class='company-actions-column-wrapper']"
        )
        svg_button = hover_span.find_element(By.XPATH, f".//*[@title='{title}']")
        ActionChains(self.__driver).move_to_element(hover_span).click(svg_button).perform()

    @PageService()
    def access_edit(self, company_name):
        """Access company pencil edit icon

        Args:
            company_name    (str)   -   name of company
        """
        self.__hover_row_click(company_name, 'Edit')
        self.__admin_console.wait_for_completion()

    @PageService()
    def access_dashboard(self, company_name):
        """Access company dashboard icon

        Args:
            company_name    (str)   -   name of company
        """
        self.__hover_row_click(company_name, 'Dashboard')
        self.__admin_console.wait_for_completion()

    # # # COMPANY TABLE VIEWS # # #

    @PageService()
    def company_exists(self, company_name: str, raise_error: bool=True, status: str = None) -> bool:
        """Method to check if company exists 
        
        Args:
            company_name (str): company name to check if it exisits
            raise_error (bool): True for raising exception
            status (str): To apply status filter before checking
        """
        if status:
            self.__table.set_default_filter("Status", status)

        if status == "Deactivated":
            self.__table.search_for(company_name)
            return f'{company_name}\nDeactivated' in self.__table.get_column_data('Name', fetch_all=True)

        comp_created_successfully = self.__table.is_entity_present_in_column('Name', company_name)
        if not comp_created_successfully:
            if raise_error:
                raise Exception('Company Does not exist')

        return comp_created_successfully

    @PageService()
    def set_scope_local(self, local=True):
        """
        Method to set the company listing scope to local or global

        Args:
            local   (bool)  -   will set local if True and global if False
        """
        self.__table.view_by_title(["Global", "Local"][local], "Scope")

    @PageService()
    def get_all_companies(self):
        """Method to get all companies

        Returns:
            List: List of all the companies
        """
        self.__table.set_default_filter("Status","All")
        self.__table.clear_search()
        companies_list = self.__table.get_column_data('Name', fetch_all=True)
        return companies_list

    @PageService()
    def get_active_companies(self):
        """Method to get active companies

        Returns:
            List: List of all the active companies
        """
        self.__table.set_default_filter("Status","Active")
        companies_list = self.__table.get_column_data('Name', fetch_all=True)
        return companies_list

    @PageService()
    def get_deactivated_companies(self):
        """Method to get deactivated companies

        Returns:
            List: List of all the deactivated companies
        """
        self.__table.set_default_filter("Status","Deactivated")
        self.__table.clear_search()
        companies_list = self.__table.get_column_data('Name', fetch_all=True)
        listc = [item.split("\nDeactivated")[0] for item in companies_list]
        return listc

    @PageService()
    def get_deleted_companies(self):
        """Method to get deleted companies

        Returns:
            List: List of all the deleted companies
        """
        self.__table.set_default_filter("Status", "Deleted")
        self.__table.clear_search()
        companies_list = self.__table.get_column_data('Name', fetch_all=True)
        return companies_list

    @PageService()
    def get_company_data(self, company):
        """
        Method to get all columns data for given company

        Args:
            company (str)   -   name of company

        Returns:
            company_data    (dict)  -   dict with each column as key and rows as value
        """
        self.__table.set_default_filter("Status","All")
        self.__table.clear_search()
        self.__table.search_for(company)
        return self.__table.get_table_data()

    @PageService()
    def get_total_companies_count(self, company=None):
        """
        Method to get the total number of companies listed

        Args:
            company  (str)  -   company name to apply search first if required

        Returns:
            count   (int)   -   number of companies listed in table
        """
        self.__table.set_default_filter("Status","All")
        return self.__table.get_total_rows_count(search_keyword=company)

    # # # MISC # # #

    @PageService()
    def edit_company_name(self, name, new_name):
        """
        method to edit company name
        Args:
            name: name of the company to be edited
            new_name: new name of the company
        """
        self.access_company(name)
        self.__admin_console.wait_for_completion()
        self.__page_container.edit_title(new_name)
        self.__admin_console.wait_for_completion()
        
