# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
IdentityServerDetails Page on the AdminConsole

Class:

    IdentityServerDetails() -> _Navigator() -> login_page()
    login_page()-> AdminConsoleBase() -> object()

Functions:

get_app_name()                  --Gets the SAML app name
is_app_enabled()                --Returns True/False if app is enabled /disabled
get_auto_create_user_flag()     --Returns flag set for auto create user
get_default_user_group          --Returns the default user group set
get_company_name()              --Returns the company for which app is created
edit_idp_details()              --Selects the IDP edit option from app details page
edit_sp_entity_id()             --Edits SP Entity Id of SAML App
add_sp_alias()                 --Adds SP Alias to SAML App
download_sp_metadata()          --Downloads the SP metadata file from SAML app details page
modify_enable_app()             --changes the enable option in app
modify_auto_create_user()       -- Edits the auto user create option
modify_user_group()             -- Edits the user group option
sp_metadata_attributes()        -- Returns SP Entity Id, SSO Url, SLO Url of an app
fetch_associations()            --fetches the associations of SAML app
delete_saml_app()               --deletes SAML app
add_attribute_mappings()        --adds attribute mappings to the SAML app
edit_attribute_mapping()        --edits attribute mappings on the SAML app
delete_attribute_mapping()      --deletes attribute mappings on the SAML app
fetch_attribute_mappings()      -- fetches attribute mappings on the SAML app
"""

import time
import os
from selenium.webdriver.common.by import By
from Web.AdminConsole.AdminConsolePages.identity_servers import IdentityServers
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import DropDown, PanelInfo, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException


class IdentityServerDetails:
    """
    Class for the Identity server Details page
    """

    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.

        Args:
            admin_console  (Object) : Admin console class object
        """
        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.log = self.__admin_console.log
        self.__admin_console.load_properties(self)
        self.identity_servers_obj = IdentityServers(self.__admin_console)
        self.__table = Table(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)

        self.rpanel_info = RPanelInfo(self.__admin_console, 'Service provider metadata')
        self.dialog = None
        self.page_container = PageContainer(self.__admin_console)

    @WebAction()
    def get_app_name(self):
        """
        Gets the SAML app name
        Args:    None
        Returns    (str):    app name
        """
        app_name = self.__driver.find_element(By.XPATH, "//h1[@class='page-title']").text
        return app_name

    @WebAction()
    def is_app_enabled(self):
        """
        Returns True/False if app is enabled/disabled
        Args:    None
        Returns (bool):    True/False
        """
        toggle_class = self.__driver.find_element(By.XPATH,
                                                  "//toggle-control[@class='tc.activityInfo.isEnabled \
                                                          ng-isolate-scope']/div").get_attribute('class')
        if toggle_class == "cv-material-toggle cv-toggle enabled":
            return True
        if toggle_class == "cv-material-toggle cv-toggle":
            return False
        raise CVWebAutomationException("SAML app in unknown state")

    @WebAction()
    def get_auto_create_user_flag(self):
        """
        Returns flag set for auto create user
        Args:    None
        Returns    (bool):    True/False
        """
        toggle_class = self.__driver.find_element(By.XPATH,
                                                  "//toggle-control[@class=\
                                                  'tc.activityInfo.createUserAutomatically ng-isolate-scope']\
                                                  /div").get_attribute('class')
        if toggle_class == "cv-material-toggle cv-toggle enabled":
            return True
        if toggle_class == "cv-material-toggle cv-toggle":
            return False
        raise CVWebAutomationException("SAML app in unknown state")

    @WebAction()
    def get_default_user_group(self):
        """
        Gets the default user group set in app
        Args:    None
        Returns    (str):    user group name
        """
        user_group_elem = self.__driver.find_element(By.XPATH, "//span\
                        [@class='pageDetailColumn' and \
                        contains(text(),'" + self.__admin_console.props['label.userGroup'] + "')]")
        default_user_group = user_group_elem.find_element(By.XPATH,
                                                          ".//../../span[2]").text
        default_user_group = default_user_group.split('\n')[0]
        return default_user_group

    @WebAction()
    def get_company_name(self):
        """
        Returns the company name for which the app is created
        Args:    None
        Returns    (str):    company name
        """
        company_name = None
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//span[contains(text(),\
                        '" + self.__admin_console.props['label.createdForCompany'] + "')]"):
            company_elem = self.__driver.find_element(By.XPATH,
                                                      "//span[contains(text(),'" + self.__admin_console.props[
                                                          'label.createdForCompany'] + "')]")
            company_name = company_elem.find_element(By.XPATH,
                                                     ".//ancestor::li/span[2]").get_attribute('title')
        return company_name

    @PageService()
    def download_sp_metadata(self, app_name, download_dir):
        """
        Downloads the SP metadata and returns the location
        Args:
        app_name    (str): SAML app name for which
                            metadata has to be downloaded
        download_dir    (str):location where the file has to be downloaded
        Returns    (str):    SP metadata file downloaded location
        """
        filename = "SPMetadata_" + app_name + ".xml"
        downloaded_file_path = download_dir + "\\" + filename
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
        self.__driver.find_element(By.XPATH, "//div[contains(text(),\
                                    '" + self.__admin_console.props['action.downloadSpMetadata'] + "')]").click()
        self.log.info("SP metadata location: %s", downloaded_file_path)
        return downloaded_file_path

    @WebAction()
    def edit_saml_app_details(self):
        """
            Clicks Edit option in SAML app details page
        """
        self.__driver.find_element(By.XPATH,
                                   "//a[@data-ng-click=\
                                       'tc.showAddThirdPartyAppDialog(tc.thirdPartyApp)']").click()

    @WebAction()
    def __expand_keystore_section(self):
        """ Method to expand keystore section in SAML App panel """
        self.__driver.find_element(By.XPATH,
                                   "//legend[@class='cursor-pointer']").click()

    @PageService()
    def edit_idp_details(self, idp_metadata_path=None, web_console_url=None,
                         jks_file_path=None, key_password=None, keystore_password=None,
                         alias_name=None):
        """
        Edits the SAML app IDP details and keystore configurations

        Args:
        idp_metadata_path    (str)    :IDP metadata file path
        webconsole_url        (str)   :webconsole url to edit
        jks_file_path        (str)    :keystore file path
        key_password        (str)     :key password for the
                                         .jks file
        keystore_password    (str)    :keystore password for
                                        the .jks file
        alias_name            (str)    :alias name for
                                        the .jks file
        Returns:     None
        Raises:
            Exception:
                -- if editing app details failed
        """
        self.__admin_console.click_button(self.__admin_console.props['wizardStep.IDPMetadata'])

        if idp_metadata_path:
            self.rpanel_info = RPanelInfo(self.__admin_console, 'Identity provider metadata')
            self.rpanel_info.edit_tile()
            self.identity_servers_obj.upload_idp_metadata(idp_metadata_path)
            self.__admin_console.click_button('Save')
            time.sleep(3)
        if web_console_url:
            self.identity_servers_obj.set_service_provider_endpoint(web_console_url)

        if any([jks_file_path, alias_name, key_password, keystore_password]):
            if all([jks_file_path, alias_name, key_password, keystore_password]):
                self.page_container.access_page_action(self.__admin_console.props['label.uploadNewKeystoreFile'])
                self.identity_servers_obj.upload_jks_file(jks_file_path)
                self.identity_servers_obj.set_alias_name(alias_name)
                self.identity_servers_obj.set_key_password(key_password)
                self.identity_servers_obj.set_keystore_password(keystore_password)
                self.__admin_console.click_button('Save')
            else:
                raise CVWebAutomationException("invalid inputs for jks file")

        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    def edit_sp_entity_id(self, sp_entity_id=None):
        """Edits sp entity id of saml app
            Args:
                sp_entity_id        (str)       new value of sp entity id
        """
        self.__admin_console.click_button(self.__admin_console.props['wizardStep.SPMetadata'])
        self.rpanel_info.edit_tile_entity(self.__admin_console.props['label.spEntityId'])

        self.dialog = RModalDialog(self.__admin_console, title=self.__admin_console.props['modalHeader.editSPEntityId'])
        self.dialog.fill_text_in_field(element_id='serviceProviderEndpoint', text=sp_entity_id)
        self.dialog.click_submit()
        self.__admin_console.check_error_message()

    def add_sp_alias(self, sp_alias=None):
        """Add a new sp alias to saml app
        Args:
            sp_alias        (str)   ap_alias to be added to saml app
        """
        self.__admin_console.click_button(self.__admin_console.props['wizardStep.SPMetadata'])
        self.rpanel_info.add_tile_entity(self.__admin_console.props['label.spEntityId'])
        time.sleep(3)
        self.dialog = RModalDialog(self.__admin_console, 'Service provider alias')
        self.dialog.fill_text_in_field('spAlias1', sp_alias)
        self.dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def modify_enable_app(self, enable_app=True):
        """
        Changes the enable option in app
        Args
        enable_app    (bool):True/False
        Returns    None
        """
        if enable_app:
            self.__admin_console.enable_toggle(0)
        else:
            self.__admin_console.disable_toggle(0)

    @PageService()
    def modify_auto_create_user(self, enable_auto_create_user=True):
        """
        Edits the auto user create option
        Args
        enable_auto_create_user    (bool):True/False
        Returns    None
        """
        if enable_auto_create_user:
            self.__admin_console.enable_toggle(1)
        else:
            self.__admin_console.disable_toggle(1)
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_default_usergroup(self, user_group_name):
        """
        Add's the default user group
        Args:
            user_group_name    (str):user group name
        Returns:
            None
        """
        PanelInfo(self.__admin_console, 'General').add_tile_entity(self.__admin_console.props['label.userGroup'])
        self.__admin_console.wait_for_completion()
        self._select_usergroup_from_dropdown(user_group_name)
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @WebAction()
    def _select_usergroup_from_dropdown(self, user_group):
        """
        selects the user group from drop down list

        user_group (str)    :   user group name to select
        """
        self.__driver.find_element(By.XPATH, '//*[@id="defaultUserGroup"]/span/button').click()
        self.__driver.find_element(By.XPATH, '//*[@id="defaultUserGroup"]'
                                             '/span/div/div[1]/div/div[1]/input').send_keys(user_group)
        time.sleep(2)
        self.__driver.find_element(By.XPATH, '//*[@id="defaultUserGroup"]/span/div/div[2]').click()

    @PageService()
    def modify_user_group(self, user_group_name):
        """
        Edits the default user group
        Args:
            user_group_name    (str):new user group name
        Returns:
            None
        """
        PanelInfo(self.__admin_console, 'General').edit_tile_entity(self.__admin_console.props['label.userGroup'])
        self.__admin_console.wait_for_completion()
        self._select_usergroup_from_dropdown(user_group_name)
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @WebAction()
    def sp_metadata_attributes(self):
        """
        Returns the sp entity id
        Args   : None
        Returns    (str):SP entity id of the SAML app
        """
        self.__driver.find_element(By.XPATH, "//span[contains(text(),\
                                            '" + self.__admin_console.props['wizardStep.SPMetadata'] + "')]").click()
        sp_entity_id = self.__driver.find_element(By.ID, 'popper-spEntityId').text
        sso_url = self.__driver.find_element(By.ID, 'popper-singleSignOnUrl').text
        slo_url = self.__driver.find_element(By.ID, 'popper-singleLogoutUrl').text

        return sp_entity_id, sso_url, slo_url

    @WebAction()
    def fetch_associations(self):
        """
        Returns the list of associations on SAML app
        Args   : None
        Returns    (dict):values as list of associations
                    {Associations:list of associated entities}
        """
        associated_entity = []
        ul_elements = self.__driver.find_elements(By.XPATH, "//ul[@class='list-style__\
                                            row group associated-users ng-scope']")
        for ul_elem in ul_elements:
            associated_entity.append(ul_elem.find_element(By.XPATH, ".//li/span").text)
        return associated_entity

    @PageService()
    def delete_saml_app(self):
        """
            Deletes the SAML app

        """
        self.__driver.find_element(By.XPATH, "//*[@class='popup']").click()
        self.__driver.find_element(By.XPATH, "//div[contains(text(),\
                            '" + self.__admin_console.props['action.delete'] + "')]").click()
        self.__driver.find_element(By.XPATH, "//div[contains(text(),\
                            '" + self.__admin_console.props['label.yes'] + "')]").click()

    @WebAction()
    def __enter_attribute_value(self, value):
        """
        Method to enter attribute value for attribute mapping.

        Args:
            value (str)      -- the value to be filled in the element
        """
        element = self.__driver.find_element(By.NAME, "saml-attribute-input")
        element.clear()
        element.send_keys(value)

    @WebAction()
    def add_attribute_mappings(self, mapping_dict, from_edit=False):
        """
        Adds the given set of values in attribute mapping
        Args
        mapping_dict    (dict): attribute mappings to add.
                                {"saml_attr1":"user_attr1",
                                 "saml_attr2":"user_attr2"}
        from_edit    (bool):True when called from edit attribute
                            mappings
        Returns    :None
        """
        if mapping_dict:
            if not from_edit:
                try:
                    attribute_elem = self.__driver.find_element(By.XPATH,
                                                                "//a[@data-ng-click='tc.editAttributeMappings()']")
                    attribute_elem.click()
                    time.sleep(8)
                except BaseException:
                    raise CVWebAutomationException("There is no option to add attribute mapping")
            for user_attr, saml_attr in mapping_dict.items():
                self.__admin_console.select_hyperlink(self.__admin_console.props['label.addMappings'])
                self.__enter_attribute_value(saml_attr)
                self.__admin_console.wait_for_completion()

                self.__driver.find_element(By.XPATH, '//button[@id="gitAppTypeKey"]').click()

                drop_down_elems = self.__driver.find_elements(By.XPATH, '//*[@class="checkBoxContainer"]//label')
                found = False
                for drop_down_elem in drop_down_elems:
                    if drop_down_elem.text == user_attr:
                        drop_down_elem.click()
                        found = True
                        break
                if not found:
                    raise CVWebAutomationException("Custom attribute you were trying to add is not found")
                self.__driver.find_element(By.XPATH,
                                           "//i[@class='glyphicon glyphicon-ok']").click()
            if not from_edit:
                self.__admin_console.submit_form()
                self.__admin_console.check_error_message()
        else:
            raise CVWebAutomationException("Empty values in add attribute mapping dictionary")

    @WebAction()
    def edit_attribute_mappings(self, mapping_dict):
        """
        Edits the given set of values in attribute mapping
        Args
        mapping_dict    (dict): attribute mappings to edit.
                                {"saml_attr1":"user_attr1",
                                 "saml_attr2":"user_attr2"}
        Returns    :None
        """
        displayed_attributes = self.fetch_attribute_mappings()
        if displayed_attributes == mapping_dict:
            self.log.info("No need to edit the mappings")
        else:
            attribute_elem = self.__driver.find_element(By.XPATH,
                                                        "//a[@data-ng-click='tc.editAttributeMappings()']")
            attribute_elem.click()
            self.__admin_console.wait_for_completion()
            matching_dict1, to_be_del_mappings = self.__comparedicts(
                displayed_attributes, mapping_dict)
            to_be_edited_mappings, to_be_added_mappings = self.__comparedicts(
                mapping_dict, displayed_attributes)
            if to_be_del_mappings.items():
                self.delete_attribute_mapping(to_be_del_mappings, from_edit=True)
            if to_be_added_mappings.items():
                self.add_attribute_mappings(to_be_added_mappings, from_edit=True)
            if to_be_edited_mappings.items():
                for user_attr, saml_attr in to_be_edited_mappings.items():
                    div_elements = self.__driver.find_elements(By.XPATH,
                                                               "//div[@class='ui-grid-row ng-scope']")
                    for div_elem in div_elements:
                        custom_text = div_elem.find_element(By.XPATH,
                                                            "./div/div[1]/span/label").text
                        if custom_text == user_attr:
                            div_elem.find_element(By.XPATH, ".//div[3]/span[1]/\
                                i[@class='glyphicon glyphicon-pencil']").click()
                            match_found = True
                            self.__admin_console.fill_form_by_name('saml-attribute-input', saml_attr)
                            self.__driver.find_element(By.XPATH,
                                                       "//button[@id='gitAppTypeKey']").click()
                            drop_down_elements = self.__driver.find_elements(By.XPATH,
                                                                             '//*[@class="checkBoxContainer"]//label')
                            found = False
                            for drop_down_elem in drop_down_elements:
                                if drop_down_elem.text == user_attr:
                                    drop_down_elem.click()
                                    found = True
                                    break
                            if not found:
                                raise CVWebAutomationException("Custom attribute you were trying to edit is not found")
                            self.__driver.find_element(By.XPATH,
                                                       "//i[@class='glyphicon glyphicon-ok']").click()
                            if match_found:
                                break
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @WebAction()
    def delete_attribute_mapping(self, mapping_dict, from_edit=False):
        """
        Deletes the given set of values in attribute mapping
        Args
        mapping_dict    (dict): attribute mappings to delete.
                                {"saml_attr1":"user_attr1",
                                 "saml_attr2":"user_attr2"}
        from_edit    (bool):True when called from edit attribute
                            mappings
        Returns    :None
        """
        if not from_edit:
            try:
                attribute_elem = self.__driver.find_element(By.XPATH,
                                                            "//a[@data-ng-click='tc.editAttributeMappings()']")
                attribute_elem.click()
                self.__admin_console.wait_for_completion()

            except BaseException:
                raise CVWebAutomationException("There is no option to delete attribute mapping")

        for user_attr, saml_attr in mapping_dict.items():
            div_elements = self.__driver.find_elements(By.XPATH,
                                                       "//div[@class='ui-grid-row ng-scope']")
            match_found = False
            for div_elem in div_elements:
                if ((div_elem.find_element(By.XPATH, "./div/div[1]/span/label").text
                     == user_attr)
                        and
                        (div_elem.find_element(By.XPATH, "./div/div[2]/span/label").text
                         == saml_attr)):
                    match_found = True
                    div_elem.find_element(By.XPATH, "./div/div[3]/\
                        span[2]/i[@class='glyphicon glyphicon-trash']").click()
                    time.sleep(2)
                    break
            if not match_found:
                raise CVWebAutomationException("Attributes given do not match with any")
        if not from_edit:
            self.__admin_console.submit_form()
            self.__admin_console.check_error_message()

    @WebAction()
    def fetch_attribute_mappings(self):
        """
        Fetches the set of values in attribute mapping
        Args   :None
        Returns    (dict):dict of attribute mappings set on SAML app
        """
        attribute_mappings = {}
        li_elements = self.__driver.find_elements(By.XPATH, '//*[@id="attributeMappingTable"]//tbody/tr')
        for li_elem in li_elements:
            saml_attr = li_elem.find_element(By.XPATH, "./td[2]/div").text
            user_attr = li_elem.find_element(By.XPATH, "./td[1]/div").text
            attribute_mappings[user_attr] = saml_attr

        return attribute_mappings

    @PageService()
    def saml_app_info(self):
        """
        Displays all the information about the SAML app
        returns
        SAML_info    (dict)  -- all info about the SAML app
        """
        saml_app_name = self.get_app_name()
        auto_user_create_flag = self.get_auto_create_user_flag()
        default_user_group = self.get_default_user_group()
        company_name = self.get_company_name()
        sp_entity_id, sso_url, slo_url = self.sp_metadata_attributes()
        associations = self.fetch_associations()
        attribute_mappings = self.fetch_attribute_mappings()
        saml_app_info = {"AppName": saml_app_name,
                         "Auto user create flag": auto_user_create_flag,
                         "Default user group": default_user_group,
                         "Company name": company_name,
                         "SP entity ID": sp_entity_id,
                         "SSO URL": sso_url,
                         "Associations": associations,
                         "Attribute mapping": attribute_mappings}
        return saml_app_info

    def __comparedicts(self, dict1, dict2):
        """
        Compares the 2 given dicts and returns common and uniques keys
        :param dict1:
        :param dict2:
        returns: matching_dictionary    (dict)
                unique_dictionary        (dict)
        """
        matching_dict = {}
        unique_dict = {}
        for key, value in dict1.items():
            if key in dict2:
                matching_dict.update({key: value})
            else:
                unique_dict.update({key: value})
        return matching_dict, unique_dict
