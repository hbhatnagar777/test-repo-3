# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
CompanyDetails Page on the AdminConsole

Class:

    CompanyDetails()

Functions:

edit_general_settings()               -- Edits general settings tile of the company

edit_contact()                        -- Edits the contact information of the company

edit_domains()                        -- Edits the domain information of the company

edit_sender_email()                   -- Edits the email information of the company

edit_company_plan()                   -- Edits the plans associated with the company

edit_laptop_ownership()               -- Edits the laptop ownership option for the company

deactivate_company()                  -- Deactivates the company

activate_company()                    -- Activate Company from company details page

deactivated_activities()              -- returns deactivated activities shown on company page

deactivate_and_delete_company_from_details() --Deactivates and deletes the company

company_info()                        -- Extracts and returns all information about the company

extract_company_info()                -- Extracts and returns contained information from the company

de_associate_plans_from_company()     -- Method to de-associate all plans associated to the company

edit_company_file_exceptions()        -- Edits file exceptions tile of the company

edit_company_operators()              -- Method to edit Operators for the company

edit_company_security_associations()  -- Edits Security Associations for a company

edit_external_authentication()        -- Method to create domain association for company

check_data_encryption_tile()          -- Returns true if there is data encryption tile in computers page in my data

select_user_groups_tfa()              -- Select user group while enabling TFA

get_security_associations()           -- Get security associations for company

enabled_activities()                  -- Returns the enabled activities

access_tags()                         -- Returns the tags shown

delete_tags()                         -- Deletes the given tags

add_tags()                            -- Adds the given tags

access_operators()                    -- Returns the user and usergroup operator associations

add_operators()                       -- Adds operator associations

delete_operators()                    -- Deletes operator associations

get_associated_commcells()            -- Gets the associated commcells tile data

access_associated_commcell()          -- Clicks the link for given service commcell

access_entity_link()                  -- Clicks the entity page link for given entity

get_entity_counts()                   -- Gets the entity names and counts

"""
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from Web.AdminConsole.AdminConsolePages.identity_servers import Domains
from Web.AdminConsole.Components.core import CalendarView
from Web.AdminConsole.Components.dialog import TagsDialog, SecurityDialog
from Web.AdminConsole.Components.panel import Security, RSecurityPanel

from Web.Common.page_object import (WebAction, PageService)

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import PanelInfo, ModalPanel, RPanelInfo
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog, RSecurity
from Web.AdminConsole.Components.page_container import PageContainer


class CompanyDetails:
    """
    This class provides the operations that can be performed on CompanyDetails Page of
    admin console
    """
    def __init__(self, admin_console):
        """
        Method to initiate Companies class

        Args:
            admin_console   (Object) :   AdminConsole Class object
        """
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__driver = admin_console.driver
        self.__drop_down = RDropDown(self.__admin_console)
        self.__panel_info = RPanelInfo(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.security_component = RSecurity(self.__admin_console)
        self.__tags_dialog = TagsDialog(self.__admin_console)
        self.__operators_dialog = SecurityDialog(self.__admin_console, 'Edit operators', True)
        self.__admin_console.load_properties(self)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)

    @WebAction()
    def __click_remove_link(self):
        """ MEthod to click on remove link on edit sites dialog """
        self.__driver.find_element(By.XPATH,
            "//a[@data-ng-click='removeDomain(domain)']").click()

    @WebAction()
    def __remove_secondary_sites(self):
        """ Method to remove secondary sites from a company """
        old_secondary_site_entries = self.__admin_console.driver.find_elements(By.XPATH,
            "//input[@data-ng-model='domain.value']")
        for old in old_secondary_site_entries:
            old.clear()
            self.__click_remove_link()

    @WebAction()
    def __add_secondary_sites(self, secondary_sites):
        """ Method to add secondary sites to a company"""

        for site in secondary_sites:
            self.__admin_console.select_hyperlink('Add an additional site')
        index = len(secondary_sites)

        for elem in range(1, index + 1):
            self.__admin_console.driver.find_element(By.XPATH,
                "//ul[" + str(elem) + "]//input"
            ).send_keys(secondary_sites[elem - 1])

    @WebAction()
    def __select_default_plan(self, laptop_default_plan):
        """ Method to select default plan from edit plan panel """
        self.__drop_down.select_drop_down_values(values=[laptop_default_plan],
                                                 drop_down_id='LaptopDefault')

    @WebAction()
    def __extract_company_info(self, tile_name):
        """
        Extracts all the information about the company

        Args:
        tile_name (list): tile names to fetch info

        Returns:
            company_info (dict) : info about all the companies

        Raises:
            Exception:
                -- if fails to return company info
        """
        if tile_name:
            return RPanelInfo(self.__admin_console, tile_name).get_details()

        tiles = RPanelInfo(self.__admin_console).available_panels()
        tiles_info = {}
        for tile in tiles:
            tile_info = RPanelInfo(self.__admin_console, tile).get_details()
            tiles_info[tile] = tile_info

        return tiles_info

    @WebAction()
    def __select_ad_panel(self):
        """ Method to select AD section in 'Add domain' panel """
        self.__admin_console.driver.find_element(By.XPATH, 
            "//div[@ng-click='authenticationChoice=1']").click()

    @WebAction()
    def __access_ad_details(self):
        """ Method to click on AD name and open AD details page """
        self.__admin_console.driver.find_element(By.XPATH, 
            "//a[@data-ng-click='authenticationAction(externalAuthentication)").click()

    @WebAction()
    def __edit_panel_field(self, label, value):
        """Method to click edit, fill text and click submit"""
        self.__panel_info.edit_tile_entity(label)
        self.__panel_info.fill_input(label, value)
        self.__panel_info.click_button("Submit")
        self.__admin_console.wait_for_completion()

    @PageService()
    def edit_general_settings(self, general_settings):
        """
        Method to edit general setting associated o a company

        Args:
            general_settings (dict): dictionary containing values for general settings
                Eg. - general_settings = {'smtp':'comm.com', 'authcode': 'ON',
                                          'shared_laptop_usage': 'ON', 'UPN': 'ON',
                                          '2-factor': 'ON', 'data_encryption': ON,
                                          'infra_type': 'Rented'}

        Returns:
            None

        Raises:
            Exception:
                if fails to edit general settings
        """
        self.__admin_console.log.info("Editing general settings for the company")
        self.__panel_info = RPanelInfo(self.__admin_console, 'General')

        if general_settings.get('company_alias', None):
            self.__edit_panel_field(self.__admin_console.props['label.companyAlias'], general_settings["company_alias"])
            self.__admin_console.click_button('Yes')
            self.__admin_console.check_error_message()
            self.__admin_console.wait_for_completion()

        if general_settings.get('smtp', None):
            # self.__panel_info.edit_tile_entity(self.__admin_console.props['label.associatedSMTP'])
            self.__panel_info.edit_tile_entity("Associated email suffixes")
            self.__dialog.fill_text_in_field("smtp-addr", general_settings['smtp'])
            self.__dialog.click_submit()
            self.__admin_console.check_error_message()

        if general_settings.get('authcode', None):
            if general_settings['authcode'] == "ON":
                self.__panel_info.enable_toggle(self.__admin_console.props['label.enableAuthCode'])
            else:
                self.__panel_info.disable_toggle(self.__admin_console.props['label.enableAuthCode'])
                self.__dialog.click_submit()

            self.__admin_console.check_error_message()

        if general_settings.get('2-factor', None):
            if general_settings['2-factor']['default'] == "ON":
                self.__panel_info.enable_toggle(self.__admin_console.props['label.twoFactorAuthentication'])
                self.__admin_console.wait_for_completion()
                self.__dialog.click_submit()
            elif general_settings['2-factor']['default'] == "OFF":
                self.__panel_info.disable_toggle(self.__admin_console.props['label.twoFactorAuthentication'])
            else:
                self.__edit_user_group(general_settings['2-factor'])

            self.__admin_console.check_error_message()

        if general_settings.get('reseller_mode', None):
            if general_settings['reseller_mode']:
                self.__panel_info.enable_toggle(self.__admin_console.props['label.enableReseller'])
                self.__dialog.click_submit()

            self.__admin_console.check_error_message()

        if general_settings.get('data_encryption', None):
            if general_settings['data_encryption']:
                self.__panel_info.enable_toggle(self.__admin_console.props['label.showDLP'])
            else:
                self.__panel_info.disable_toggle(self.__admin_console.props['label.showDLP'])

            self.__admin_console.check_error_message()

        if general_settings.get('auto_discover_applications', None):
            if general_settings['auto_discover_applications']:
                self.__panel_info.enable_toggle(self.__admin_console.props['label.enableAutoDiscover'])
            else:
                self.__panel_info.disable_toggle(self.__admin_console.props['label.enableAutoDiscover'])

            self.__admin_console.check_error_message()

        if general_settings.get('infra_type', None):
            if general_settings['infra_type']:
                self.__panel_info.edit_tile_entity(self.__admin_console.props['label.infrastructureType'])

                self.__drop_down.select_drop_down_values(drop_down_id="infrastructureType",
                                                         values=[general_settings['infra_type']])
                self.__panel_info.click_button("Submit")

            self.__admin_console.check_error_message()

        if general_settings.get('supported_solutions', None):  # This is still in react so this won't be ported
            if general_settings['supported_solutions']:
                self.__panel_info.edit_tile_entity(self.__admin_console.props['label.supportedSolutions'])
                self.__drop_down.select_drop_down_values(0, general_settings['supported_solutions'])

            self.__admin_console.check_error_message()

        if general_settings.get('job_start_time', None):
            self.__panel_info.edit_tile_entity(self.__admin_console.props['label.jobStartTime'])
            hours_minutes, session = general_settings['job_start_time'].split(" ")
            self.__set_job_start_time(
                {
                    'hour': hours_minutes.split(":")[0],
                    'minute': hours_minutes.split(":")[1],
                    'session': session
                })

            self.__panel_info.click_button("Submit")

            self.__admin_console.check_error_message()

        if general_settings.get('Workload region', None):
            self.__panel_info.edit_tile_entity('Workload region')
            RDropDown(self.__admin_console).select_drop_down_values(drop_down_id="regionDropdown_",
                                                                    values=general_settings['Workload region'])
            self.__panel_info.click_button(self.__admin_console.props["label.save"])
            self.__admin_console.check_error_message()

    @PageService()
    def edit_contacts(self, contact_names):
        """
        Edits the contact information of the company

        Args:
            contact_names (list): String containing users to be associated/de-associated
                                  to the company
                        Eg.- contact_names = 'User1,User2,User3'

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit contact for the company
        """

        RPanelInfo(self.__admin_console, 'Contacts').edit_tile()
        self.__admin_console.wait_for_completion()
        self.__table.unselect_all_rows()
        self.__table.select_rows(contact_names)
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_sites(self,
                   primary_site,
                   secondary_sites=None):
        """
        Edits the domain information of the company

        Args:
            primary_site(str) -- the name of the primary site to be added
            secondary_sites (list) -- list of all secondary sites to be added

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit sites for the company
        """

        RPanelInfo(self.__admin_console, 'Sites').edit_tile()
        self.__admin_console.wait_for_completion()

        if primary_site:
            self.__admin_console.fill_form_by_id("primaryDomainName", primary_site)

        if secondary_sites:
            self.__remove_secondary_sites()
            self.__add_secondary_sites(secondary_sites)

        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_sender_email(self,
                          sender_name,
                          sender_email):
        """
        Edits the email information of the company

        Args:
            sender_name      (str)   --  the name of the sender of the email
            sender_email     (str)   --  the email of the sender

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit domains for the company
        """
        RPanelInfo(self.__admin_console, 'Email settings').edit_tile()
        self.__admin_console.wait_for_completion()

        self.__dialog.fill_text_in_field("senderName", sender_name)
        self.__dialog.fill_text_in_field("senderEmail", sender_email)

        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_company_plans(self,
                           plans,
                           laptop_default_plan=None):
        """
        Edits the plans associated with the company

        Args:
            plans (list)                    -- list of plans to be associated to the company

            laptop_default_plan (str)       --  name of the default laptop plan to be set

       Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit domains for the company
        """
        self.__admin_console.access_tab("Overview")
        RPanelInfo(self.__admin_console, 'Plans').edit_tile()
        self.__admin_console.wait_for_completion()

        self.__table.unselect_all_rows()
        self.__table.select_rows(plans)
        if laptop_default_plan:
            self.__select_default_plan(laptop_default_plan)

        RModalDialog(self.__admin_console, xpath=' ').click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_laptop_ownership(self, option, user_groups=[]):
        """
        Edits the laptop ownership option for the company
        Args:
            user_groups (list)              -- list containing the names of user groups for choosing option three

            option (str)                    -- text corresponding to the option to be chosen for the company

       Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit the ownership options for the company
        """
        self.__admin_console.access_tab("Overview")
        ownership_panel = RPanelInfo(self.__admin_console, 'Automatic laptop ownership assignment')
        ownership_panel.edit_tile_entity(self.__admin_console.props['label.laptopOwnerOptions'])
        if option == self.__admin_console.props['label.allUserGroups']:
            text = ",".join(user_groups)
            ownership_panel.select_radio_button_and_type(option=option, type_text=True, text=text)
        else:
            ownership_panel.select_radio_button_and_type(option=option, type_text=False, text='')
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def company_info(self, tile_name=None):
        """
        collates and returns all the information about the company

        Args:
            tile_name (list): list of tile to fetch info

        Returns:
            displayed_val(dict) : displayed values of the company in question

        Raises:
            Exception:
                -- if fails to return displayed_val
        """
        displayed_val = self.__extract_company_info(tile_name)
        self.__admin_console.log.info(displayed_val)
        return displayed_val

    @PageService()
    def de_associate_plans_from_company(self):
        """de-associates plans associated to the company

        Args:
            None

        Returns:
            None

        Raises:
            Exception:
                -- if fails to de-associate plans associated to the company
        """

        RPanelInfo(self.__admin_console, 'Plans').edit_tile()
        self.__admin_console.wait_for_completion()
        self.__table.unselect_all_rows()
        self.__admin_console.submit_form()
        self.__admin_console.click_button('Yes')
        self.__admin_console.check_error_message()

    @PageService()
    def deactivate_company(self,
                           company_disable_login=None,
                           company_disable_backup=None,
                           company_disable_restore=None):
        """
        Deactivates the company

        Args:
            company_disable_login (bool) : if login to be disabled while
                                           de-activating the company

            company_disable_backup (bool) : if backup to be disabled while
                                            de-activating the company

            company_disable_restore (bool) : if restore to be disabled while
                                             de-activating the company

        Returns:
            None
        """
        self.__page_container.access_page_action('Deactivate')
        if company_disable_login:
            self.__dialog.checkbox.uncheck('Disable login')
        elif company_disable_backup:
            self.__dialog.checkbox.uncheck('Disable backup')
        elif company_disable_restore:
            self.__dialog.checkbox.uncheck('Disable restore')
        self.__dialog.click_submit()
        self.__admin_console.close_popup()

    @PageService()
    def activate_company(self):
        """Activate Company from company details page"""
        self.__page_container.access_page_action('Activate')

    @PageService()
    def deactivated_activities(self):
        """Returns deactivated activities at company level"""
        banner = self.__driver.find_element(By.XPATH, "//div[contains(@class, 'MuiAlert-message')]//b")
        deactivated_activities = None
        if banner:
            deactivated_activities = banner.text

        return deactivated_activities

    @PageService()
    def deactivate_and_delete_company_from_details(self,
                                                   company_disable_login=None,
                                                   company_disable_backup=None,
                                                   company_disable_restore=None):
        """
        Deletes the company

        Args:
            company_disable_login (bool) : if login to be disabled while
                                           de-activating the company

            company_disable_backup (bool) : if backup to be disabled while
                                            de-activating the company

            company_disable_restore (bool) : if restore to be disabled while
                                             de-activating the company

        Returns:
            None

        Raises:
            Exception:
                -- if fails to delete the company
        """
        self.deactivate_company(company_disable_login,
                                company_disable_backup,
                                company_disable_restore)
        self.__page_container.access_page_action('Delete')
        self.__dialog.type_text_and_delete("Permanently delete company with data loss")

    @PageService()
    def edit_company_file_exceptions(self,
                                     file_exceptions):
        """
        Edits file exceptions for a company

        Args:
            file_exceptions (dict of lists) : List of paths to be excluded for the company
               Eg. -  file_exceptions = {"windows_path":["C:\\Test"],
                                         "unix_path": ["/root/file1"]}

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit file exceptions for the company
        """

        RPanelInfo(self.__admin_console, 'File exclusions').edit_tile()
        self.__admin_console.wait_for_completion()

        exception_dialog = RModalDialog(self.__admin_console, xpath="//div[contains(@class, 'mui-modal-dialog')]")

        if file_exceptions.get('windows_path', None):
            formatted_exclusion = ''
            for win_path in file_exceptions['windows_path']:
                formatted_exclusion = formatted_exclusion + win_path + '\n'

            exception_dialog.fill_text_in_field('windows', formatted_exclusion[:-1])

        if file_exceptions.get('unix_path', None):
            formatted_exclusion = ''
            for unix_path in file_exceptions['unix_path']:
                formatted_exclusion = formatted_exclusion + unix_path + '\n'

            exception_dialog.fill_text_in_field('unix', formatted_exclusion[:-1])

        exception_dialog.click_submit()
        self.__admin_console.check_error_message()
        self.__admin_console.wait_for_completion()

    @PageService()
    def edit_company_operators(self, operators):
        """
        Edits operators for a company

        Args:
            operators (dict) : dictionary containing operators to be assigned to the company
               Eg. -  operators = {'TestUser': ['Tenant Operator']}

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit operators for the company
        """
        sec_panel = RSecurityPanel(self.__admin_console, "Operators")
        sec_panel.edit_tile()
        self.security_component.edit_security_association(operators)

    @PageService()
    def edit_company_security_associations(self, associations_dict):
        """
        Edits Security Associations for a company

        Args:
            associations_dict (dict) : dictionary containing operators to be assigned to the company
               Eg. -  associations_dict = {'TestUser': ['Tenant Operator']}

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit operators for the company
        """
        sec_panel = RSecurityPanel(self.__admin_console, "Security")
        sec_panel.edit_tile()
        self.security_component.edit_security_association(associations_dict)

    @PageService()
    def edit_external_authentication(self,
                                     netbios_name=None,
                                     username=None,
                                     password=None,
                                     domain_name=None,
                                     usergroup=None,
                                     local_group=None,
                                     proxy_client=None):
        """
        NOTE : This funtion is used to add AD, use edit_external_auth_SAML for adding SAML app
        Edits external authentication for the company

        Args:
            netbios_name (str) : 'Netbios name/OSX server name/Host' value
                                 based on dir_type

            username     (str) : Username for AD registration

            password     (str) : Password for AD registration

            domain_name  (str) : domain name for AD to be created

            proxy_client (str) : Name of the client serving as proxy between
                                 Host machine and AD

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit external authentication for the company
        """
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//a[@data-ng-click='authenticationAction(externalAuthentication)' and text()='Edit']"):
            RPanelInfo(self.__admin_console, 'External authentication').edit_tile()
            self.__admin_console.select_hyperlink("AD/LDAP")
            self.__admin_console.wait_for_completion()

            if proxy_client:
                has_proxy_client = True
                proxy_client_value = proxy_client

            self.domain_obj = Domains(admin_console=self.admin_console)
            self.domain_obj.add_domain(domain_name=domain_name,
                                       netbios_name=netbios_name,
                                       username=username,
                                       password=password,
                                       user_group=usergroup,
                                       local_group=[local_group],
                                       proxy_client=has_proxy_client,
                                       proxy_client_value=proxy_client_value)

    @PageService()
    def check_data_encryption_tile(self, client_name):
        """
        Returns true if there is data encryption tile in computers page in my data
        """
        windows = self.__admin_console.driver.window_handles
        self.__admin_console.driver.switch_to.window(windows[-1])
        self.__admin_console.click_by_xpath("//span[text()='Computers']")
        self.__panel_info.click_button("Settings")
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_configuration_tab()
        all_panels = self.__panel_info.available_panels()
        tile_present = "Data encryption" in all_panels
        self.__admin_console.driver.switch_to.window(windows[0])
        return tile_present

    @PageService()
    def get_security_associations(self, hidden=False):
        """Get security associations for company

            Args:
                hidden (bool): get hidden inherited associations
        """
        sec_panel = RSecurityPanel(self.__admin_console)

        return sec_panel.get_details(show_hidden=hidden)

    @WebAction()
    def __select_user_groups(self, groups):
        """To add user groups in TFA tile

        Args:
            groups (list): list of groups to be added.
        """
        for group in groups:
            self.__admin_console.driver.find_element(By.XPATH, 
                "//div[contains(@class,'search-input-container')]/input").send_keys("{0}".format(group))
            time.sleep(5)
            self.__admin_console.driver.find_element(By.XPATH, 
                f"//div[@class='result-item']/h5[contains(text(),'{group}')]").click()
        self.__admin_console.submit_form()

    @WebAction()
    def __remove_user_groups(self, groups):
        """To remove user groups from TFA tile

        Args:
            groups (list): list of groups to be removed.
        """
        for group in groups:
            self.__admin_console.driver.find_element(By.XPATH, 
                f"//span[@class='group-type']/span[@title='Remove {group}']").click()
        self.__admin_console.submit_form()

    def __edit_user_group(self, two_factor_groups):
        """to edit user groups option in two factor authentication of company

        Args:
            two_factor_groups (dict): list of user groups to be added or removed with option
        """
        element = self.__panel_info.get_toggle_element(self.__admin_console.props["label.twoFactorAuthentication"])
        if not self.__panel_info.is_toggle_enabled(element):
            self.__panel_info.enable_toggle(self.__admin_console.props["label.twoFactorAuthentication"])
            self.__admin_console.wait_for_completion()
            self.__admin_console.click_button('Save')

        self.__panel_info.edit_tile_entity(entity_name=self.__admin_console.props["label.twoFactorAuthentication"])
        self.__dialog.select_radio_by_id("userGroups")
        if "add" in two_factor_groups['default']:
            for user_group in two_factor_groups['user_groups']:
                self.__drop_down.search_and_select(id="userGroups", select_value=user_group)
        elif "Remove" in two_factor_groups['default']:
            for user_group in two_factor_groups['user_groups']:
                self.__drop_down.deselect_auto_dropdown_values(value=user_group, id="userGroups")

        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_save(self):
        """Clicks on the save icon for job start time"""
        self.__driver.find_element(By.XPATH, 
            "//span[@data-uib-tooltip='Save']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __get_panel_information(self, label_class: str, title: str = None):
        """Get infromation from panel based on label class name

        Args:
            label_class (str)   : Label class used to identify label
            title (str)         : Title of the tile

        Returns:
            Dict: key value pair infromation on tile
        """
        base_element = self.__driver

        if label_class:
            base_element = self.__driver.find_element(
                By.XPATH, f"//span[contains(@class, 'MuiCardHeader-title')"
                          f" and text()='{title}']/ancestor::div[contains(@class, 'MuiCard-root')]")

        rows = base_element.find_elements(By.XPATH, f".//*[contains(@class, '{label_class}')]")

        panel_info = {}

        for row in rows:
            toggle = row.find_element(By.XPATH, f"..//span[contains(@class, 'MuiSwitch-switchBase')]")
            value = 'Mui-checked' in toggle.get_attribute("class")
            panel_info[row.text] = value

        return panel_info


    @PageService()
    def enabled_activities(self):
        """Returns the enabled activities at server group level"""

        activities = self.__get_panel_information('activity-label', 'Activity control')
        enabled_activities = []
        for i in activities:
            if activities[i]:
                enabled_activities.append(i)
        return enabled_activities

    @PageService()
    def enable_passkey_for_restores(self, passkey):
        """Enables passkey for restores"""
        passkey_panel = RPanelInfo(self.__admin_console, 'Passkey')
        modal_dialog = RModalDialog(self.__admin_console)
        enable_passkey_label = 'Require passkey for restores'
        if not passkey_panel.is_toggle_enabled(label=enable_passkey_label):
            passkey_panel.enable_toggle(enable_passkey_label)
            self.__admin_console.fill_form_by_id("passkey", passkey)
            self.__admin_console.fill_form_by_id("passkey-confirm", passkey)
            modal_dialog.click_submit()
            self.__admin_console.click_button('Yes')
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()

    @PageService()
    def disable_passkey_for_restores(self, passkey):
        """Disables passkey for restores"""
        passkey_panel = RPanelInfo(self.__admin_console, 'Passkey')
        modal_dialog = RModalDialog(self.__admin_console)
        passkey_label = 'Require passkey for restores'
        if passkey_panel.is_toggle_enabled(label=passkey_label):
            passkey_panel.disable_toggle(passkey_label)
            self.__admin_console.fill_form_by_id("passkey", passkey)
            modal_dialog.click_submit()
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()

    @PageService()
    def access_tags(self, close=True):
        """Method to access the tags dialog of company and get the tags visible

        Args:
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
            RPanelInfo(self.__admin_console, 'Tags').edit_tile()
            self.__admin_console.wait_for_completion()
        tags_visible = self.__tags_dialog.get_tags()
        if close:
            self.__tags_dialog.click_cancel()
        return tags_visible

    @PageService()
    def delete_tags(self, tags):
        """Deletes the given tags from company

        Args:
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
        if not self.__tags_dialog.is_dialog_present():
            RPanelInfo(self.__admin_console, 'Tags').edit_tile()
            self.__admin_console.wait_for_completion()
        for tag in tags:
            self.__tags_dialog.delete_tag(tag["name"])
        self.__tags_dialog.click_submit()

    @PageService()
    def add_tags(self, tags):
        """Adds the given tags to company

        Args:
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
        if not self.__tags_dialog.is_dialog_present():
            RPanelInfo(self.__admin_console, 'Tags').edit_tile()
            self.__admin_console.wait_for_completion()
        for tag in tags:
            self.__tags_dialog.add_tag(tag["name"], tag.get("value", ""))
        self.__tags_dialog.click_submit()

    @PageService()
    def access_operators(self, close=True):
        """Method to access the operators dialog of company and get the associations

        Args:
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
            RPanelInfo(self.__admin_console, 'Operators').edit_tile()
            self.__admin_console.wait_for_completion()
        operators = self.__operators_dialog.get_user_role_associations()
        operators += self.__operators_dialog.get_usergroup_role_associations()
        if close:
            self.__operators_dialog.click_cancel()
        return operators

    @PageService()
    def delete_operators(self, operators):
        """Deletes the given operators from company

        Args:
            operators    (list)  -   list of dicts with operator association details
                    example -  [
                    {'role':'<name of role>','userGroup':'<usergroupname>'},
                    {'role':'<name of role>','user':'<username>'}
                ]
        """
        if not self.__operators_dialog.is_dialog_present():
            RPanelInfo(self.__admin_console, 'Operators').edit_tile()
            self.__admin_console.wait_for_completion()
        for operator in operators:
            self.__operators_dialog.remove_association(
                operator.get("user") or operator.get("userGroup"),
                operator["role"]
            )
        self.__operators_dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def add_operators(self, operators):
        """Adds the given associations to company operators

        Args:
            operators    (list)  -   list of dicts with association details
                    example - [
                    {'role':'<name of role>','userGroup':'<usergroupname>'},
                    {'role':'<name of role>','user':'<username>'}
                ]
        """
        if not self.__operators_dialog.is_dialog_present():
            RPanelInfo(self.__admin_console, 'Operators').edit_tile()
            self.__admin_console.wait_for_completion()
        for operator in operators:
            self.__operators_dialog.add_association(
                operator.get("user") or operator.get("userGroup"),
                operator["role"]
            )
        self.__operators_dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def get_associated_commcells(self):
        """Gets list of commcells associated as shown in panel

        Returns:
            list    -   ['cs1','cs2',...]
        """
        return PanelInfo(self.__admin_console, 'CommCells associated').get_all_hyperlinks()

    @PageService()
    def access_associated_commcell(self, service_commcell):
        """Accesses the associated commcell link for given commcells

        Args:
            service_commcell    (str)   -   display name of service commcell
        """
        RPanelInfo(self.__admin_console, 'CommCells associated').open_hyperlink_on_tile(service_commcell)

    @WebAction()
    def __access_entity_link(self, label):
        """Clicks on the entity links on top of company details page"""
        self.__driver.find_element(By.XPATH, f"//span[contains(text(),'{label}')]/ancestor::a[1]").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __read_entities_header(self):
        """Gets the entity counts and label from company details page header"""
        entities_count = {}
        for entity_div in self.__driver.find_elements(By.XPATH, "//div[contains(@class,'kpi-entity')]"):
            entity_name = entity_div.find_element(By.XPATH, ".//span[@ng-bind='entity.title']").text.strip()
            entity_count = entity_div.find_element(By.XPATH, ".//span[@ng-bind='entity.value']").text.strip()
            entities_count[entity_name] = int(entity_count)
        return entities_count

    @PageService()
    def access_entity_link(self, entity_label):
        """
        Accesses the entity's link on top of company details page

        Args:
            entity_label    (str)   -   the entity name as labelled on the page
        """
        self.__access_entity_link(entity_label)

    @PageService()
    def get_entity_counts(self):
        """Gets the entity label and counts displayed on top of company details page

        Returns:

            dict    -   dict with entity name as key and count as value
        """
        return self.__read_entities_header()

    @PageService()
    def get_general_settings(self):
        """returns all the data from General settings tab"""
        _panel_info = RPanelInfo(self.__admin_console,title="General").get_details()
        return _panel_info

    @WebAction()
    def __set_job_start_time(self, time_dict: dict):
        """Sets job start time on company details page"""
        xpath = "//*[contains(@class, 'MuiInputBase-root')]//input"
        element = self.__driver.find_element(By.XPATH, xpath)
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        element.send_keys(time_dict['hour'] + ":" + time_dict["minute"] + " " + time_dict["session"].lower())
