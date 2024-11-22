from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for,
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be used in metallic Archiving pages.

ContentGroup:

    add_new_content_group()    :     click add content group option and launch to add new content group page

    access_content_group()     :     click content group and launch to content group details page

    is_content_group_exists()  :     return true if provided content group exists

    run_archive()              :     click archive action for provided content group and trigger archiving job

    action_restore()           :     click restore action for provided content group

    delete_content_group()     :     click delete action for provided content group and delete it

    get_visible_column_names() :     Get visible Column names

    action_manage_tags()       :     Click manage tags action for provided content group

    get_tag_name_value_dict()  :     Get tag name and names dictionary for provided content group

    get_tag_name_or_value_list():    Get list of tag names or tag values for provided content group

    add_tag()                  :     Add tags to content group

    get_tags_column_value()    :     Get Tags column value

    view_tags()                :     Click content group tags column and view the tag names and values

    filter_with_tagname()      :     Search content groups with provided tag name

    remove_tags()              :     Remove provided tag name or remove all tag names for provided content group

ContentGroupDetails:

    select_deploy_option()     :     on add content group page, select archive or run analysis option

    select_access_node()       :     select the access node

    add_new_access_node()      :     add new access node

    install_fs()               :     install downloaded cv package on new machine

    configure_content_group()  :     configure content group name and content path when adding new content group

    view_summary()             :     view summary information when adding content group

    access_insights_tab()      :     access the Insights tab under content group details

    access_overview_tab()      :     access overview tab

    set_archive_plan()         :     select provided plan, if plan not exist, create new plan and select the
                                     plan then save the changes

    set_archiving_rule_and_create_plan  :    select provided plan, if plan not exist, set archiving rules on
                                             content group details then create new plan. once done, select
                                             the new plan and save the changes

    run_archive()              :     click archive option on content group details and click Yes on popup
                                     window to trigger archive job

    click_restore()            :     click restore option on content group details

ArchivingNasServer:

    access_nas_server()        :     click nas server from archiving -> nas servers and launch to nas server
                                     details page

    is_nas_server_exists()     :     check if nas client exists on metallic archiving -> nas server page

    retire_nas_server()        :     retire the provided nas server

    delete_nas_server()        :     delete the provided nas server

ArchivingPlans:

    set_archiving_rule()       :     set archiving rules

    create_plan_from_metallic_archiving()    :     create archiving plan from content group details page

    is_plan_exists()           :     check if plan exists under metallic archiving -> plans

    delete_plan()              :     delete the provided plan

"""
import time
from selenium.webdriver.common.keys import Keys
from Install.install_custom_package import InstallCustomPackage
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog, RTags
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.wizard import Wizard


class ContentGroups:
    """class for metallic Protect -> Archiving -> Content groups """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._admin_console.load_properties(self)
        self.__table = Rtable(self._admin_console)
        self.__dropdown = RDropDown(self._admin_console)
        self.__rmodaldialog = RModalDialog(self._admin_console)
        self._rtags = RTags(self._admin_console)

    def __get_tags_from_popup(self):
        """
        click tags column and get stored tags from popup
        """
        self._admin_console.driver.find_element(By.XPATH, 
            "//span[starts-with(@id, 'popper-callout')]").click()
        text_elements = self._admin_console.driver.find_elements(By.XPATH, 
            "//div[@id='tagsCalloutTable']//tr/td/span")
        texts = [element.text.strip() for element in text_elements]

        return {texts[i]: texts[i + 1] for i in range(0, len(texts), 2)}

    @PageService()
    def add_new_content_group(self):
        """
            Create new content Group
        """
        self.__table.access_toolbar_menu('Add content group')
        return ContentGroupDetails(self._admin_console)

    @PageService()
    def access_content_group(self, content_group_namp):
        """
        Access content group
        Args:
            contentgroup        (String)       --    content group name
        """
        self.__table.access_link(content_group_namp)

    @PageService()
    def is_content_group_exists(self, content_group_name):
        """
        Check if group exists
        Args:
            contentgroup        (String)       --    content group name
        """
        return self.__table.is_entity_present_in_column(
            'Name', content_group_name)

    @PageService()
    def run_archive(self, content_group_name):
        """
        run archive for content group
        """
        self.__table.access_action_item(content_group_name, "Archive")
        self._admin_console.click_button("Yes")

    @PageService()
    def action_restore(self, content_group_name):
        """
        click restore action for content group
        """
        self.__table.access_action_item(content_group_name, "Restore")

    @PageService()
    def delete_content_group(self, content_group_name):
        """
        delete content group
        """
        self.__table.access_action_item(content_group_name, "Delete")
        self.__rmodaldialog.type_text_and_delete(
            text_val="PRUNING WILL BE BASED ON RETENTION DURATION",
            button_name="Delete")

    @PageService()
    def action_manage_tags(self, content_group_name):
        """
        click manage tags action for content group
        Args:
            content_group_name    (str)    :    content group name
        """
        self.__table.access_action_item(content_group_name, "Manage tags")

    @PageService()
    def get_tag_name_value_dict(self, content_group_name):
        """
        get dictionary of tag name and value pairs for content group
        Args:
            content_group_name    (str)    :    content group name
        """
        self.action_manage_tags(content_group_name)
        tags = self._rtags.get_tags()
        self._admin_console.click_button(value="Cancel")
        return tags

    @PageService()
    def add_tag(self, content_group_name, tag_name_dict):
        """
        add tags to content group
        Args:
            content_group_name    (str)    :    content group name
            tag_name_dict         (dict)    :   dictionary which contains tag name/values pairs
        """
        self.action_manage_tags(content_group_name)
        for tagname in [*tag_name_dict]:
            self._rtags.add_tag(tagname, tag_name_dict[tagname].strip())
        self._admin_console.click_button(value="Save")
        self._admin_console.check_error_message()

    @PageService()
    def get_tags_column_value(self, content_group_name=None, tag_name=None):
        """
        get the Tags column value for provided content group or tag name
        """
        if content_group_name is not None:
            self.__table.search_for(content_group_name)
        if tag_name is not None:
            self.__table.search_for(tag_name)
        tags = self.__table.get_column_data("Tags")
        self.__table.clear_search()
        return tags

    @PageService()
    def view_tags(self, content_group_name):
        """
        click content group tag value and view the tag names values
        """
        tags = {}
        tagstring = self.get_tags_column_value(content_group_name)
        if "+" in tagstring[0]:
            self.__table.search_for(content_group_name)
            tags = self.__get_tags_from_popup()
            self._table.clear_search()
        elif ":" in tagstring[0]:
            taglist = tagstring[0].split(":")
            tags[taglist[0].strip()] = taglist[1].strip()
        else:
            tags[tagstring[0].strip()] = ""
        return tags

    @PageService()
    def filter_with_tagname(self, tag_name):
        """
        search content groups with tag name and return content group list
        Args:
            tag_name              (str)    :    tag name
        """
        self.__table.search_for(tag_name)
        groupnames = self.__table.get_column_data("Name")
        self.__table.clear_search()
        return groupnames

    @PageService()
    def remove_tags(self, content_group_name, tag_name=None):
        """
        delete provided tag names for provide content group
        Args:
            content_group_name    (str)    :    content group name
            tag_name              (str)    :    tag name
        """
        self.action_manage_tags(content_group_name)
        taglist = self._rtags.get_tags()
        if tag_name is not None:
            self._rtags.delete_tags(tag_name, taglist[tag_name])
        else:
            for tagname in [*taglist]:
                self._rtags.delete_tag(tagname, taglist[tagname])
        self._admin_console.click_button(value="Save")
        self._admin_console.check_error_message()


class ContentGroupDetails:
    """class for content group details under metallic -> archiving"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.__table = Rtable(self._admin_console)
        self.__dropdown = RDropDown(self._admin_console)
        self.__rmodaldialog = RModalDialog(self._admin_console)
        self.__wizard = Wizard(admin_console)

    @WebAction()
    def __click_add_option(self, formid, index=0):
        """click '+' button"""
        xpath = "//*[@id='" + formid + "']//button"
        elems = self._driver.find_elements(By.XPATH, xpath)
        elems[index].click()

    @WebAction()
    def __save_plan(self):
        """save plan change"""
        self._admin_console.click_button("Apply")
        time.sleep(120)
        self._admin_console.click_button("Yes")
        time.sleep(120)

    @PageService()
    def select_deploy_option(self, analyze=True):
        """
        select archive or run analysis option
        """
        if analyze:
            self._admin_console.select_radio(id="analyzeConf")
        else:
            self._admin_console.select_radio(id="archiveConf")

        self._admin_console.click_button("Next")

    @PageService()
    def select_access_node(self, accessnode):
        """
        select access node and click next button
        Args:
            accessnode (str)    :    access node client name
        """
        accessnodes = [accessnode]
        self.__dropdown.select_drop_down_values(
            values=accessnodes, drop_down_id='accessNodeDropdown')
        self._admin_console.click_button("OK")
        self._admin_console.click_button('Next')

    @PageService()
    def add_new_access_node(self, installinputs):
        """
        add new access node when creating new content group
        Args:
            installinputs (dict)    :    Inputs for Installation
        """
        self.__click_add_option('accessNodesSelectionForm')
        if installinputs.get('os_type') == "windows":
            self._admin_console.click_button_using_text("Windows")
        else:
            self._admin_console.click_button_using_text("Linux")
        time.sleep(300)
        self.install_fs(installinputs)
        self._admin_console.click_button("Done")
        # refresh access node drop down
        self.__click_add_option('accessNodesSelectionForm')
        self._admin_console.wait_for_completion()

    def install_fs(self, installinputs):
        """
        interactive install cv packages on new machine
        Args:
            installinputs (dict)    :    Inputs for Installation
        """
        install_helper = InstallCustomPackage(installinputs.get('commcell'),
                                              installinputs,
                                              installinputs.get('os_type'))
        install_helper.install_custom_package(
            full_package_path=installinputs.get('full_package_path'),
            username=installinputs.get('registering_user'),
            password=installinputs.get('registering_user_password')
        )

    @PageService()
    def configure_source(
            self,
            fileservername,
            sharetype,
            region,
            shareuser=None,
            sharepwd=None):
        """
        define source information when creating new content group
        Args:
            fileservername (str)    :    source file server name
            sharetype (str)    :    share type,  CIFS or NFS
            accessnode  (str)  :    access node
            shareuser  (str)   :    SMB share user name
            sharepwd  (str)    :    SMB share user password
        """
        # self.sharetype = sharetype
        regions = [region]
        fileservernames = [fileservername]
        existingservers = self.__dropdown.get_values_of_drop_down(
            'archiveServer')
        if fileservername not in existingservers:
            self.__click_add_option('addArchivingSource')
            self._admin_console.fill_form_by_id(
                'existingServer', fileservername)
            self._driver.find_element(By.ID, 
                'existingServer').send_keys(Keys.RETURN)
            self._admin_console.fill_form_by_id('hostName', fileservername)
            self._admin_console.click_button("Create")
        self.__dropdown.select_drop_down_values(
            values=fileservernames, drop_down_id='archiveServer')

        self.__dropdown.select_drop_down_values(values=regions,
                                                drop_down_id='archiveRegion')
        if sharetype == "CIFS":
            self._admin_console.fill_form_by_id('userName', shareuser)
            self._admin_console.fill_form_by_id('password', sharepwd)

        self._admin_console.click_button("Next")

    @PageService()
    def configure_plan(self, planname, storage):
        """
        select a plan when creating new content group
        Args:
            planname (str)    :    plan name
            storage (str)     :    storage name

        """
        archivingplan = ArchivingPlans(self._admin_console)
        self.__wizard.fill_text_in_field(id="searchPlanName", text=planname)
        xpath = f"//span[text()='{planname}']"
        if not self._admin_console.check_if_entity_exists("xpath", xpath):
            self.__wizard.click_add_icon()
            storages = {'pri_storage': None,
                        'pri_ret_period': '30',
                        'sec_storage': None,
                        'sec_ret_period': '45',
                        'ret_unit': 'day(s)'}
            storages["pri_storage"] = storage
            archiving_rules = {"last_accessed_unit": None,
                               "last_accessed": None,
                               "last_modified_unit": "days",
                               "last_modified": 0,
                               "file_size": 1,
                               "file_size_unit": "MB"}

            archivingplan.add_new_plan(
                planname, storages, archiving_rules, rpo=None)
            time.sleep(120)

        else:
            self.__wizard.select_plan(planname)
        self.__wizard.click_next()

    @PageService()
    def configure_content_group(
            self,
            contentgroupname,
            srcpath,
            sharetype,
            servername):
        """
        configure content group name and content path
        Args:
            contentgroupname    (str)    :    content group name
            srcpath    (str)             :    source path
            sharetype    (str)           :    share type, either 'NFS' or 'CIFS'
            servername    (str)          :    file server name
        """
        self._admin_console.fill_form_by_id(
            'contentGroupName', contentgroupname)
        self._admin_console.click_button("Add")
        self._admin_console.click_button("Custom path")
        if sharetype == 'CIFS':
            self._admin_console.fill_form_by_id('custom-path', srcpath)
        else:
            path = servername + ":" + srcpath
            self._admin_console.fill_form_by_id('custom-path', path)
        self._driver.find_element(By.ID, 'custom-path').send_keys(Keys.RETURN)
        self._admin_console.click_button("Next")

    @PageService()
    def view_summary(self):
        """view summary and click submit to create content group"""
        self._admin_console.click_button("Submit")

    @PageService()
    def access_insights_tab(self):
        """
        access Insights tab
        """
        self._admin_console.click_button("Insights")

    @PageService()
    def access_overview_tab(self):
        """
        access Overview tab
        """
        self._admin_console.click_button("Overview")

    def set_archive_plan(self, planname, storage):
        """
        select provided plan, if plan not exist, then create and select new plan then save
        Args:
            planname    (str)    :    plan name
            storage    (str)     :    storage name
        """
        archivingplan = ArchivingPlans(self._admin_console)
        existingplans = self.__dropdown.get_values_of_drop_down(
            'contentGroupPlanListDropdown')
        if planname not in existingplans:
            storages = {'pri_storage': None,
                        'pri_ret_period': '30',
                        'sec_storage': None,
                        'sec_ret_period': '45',
                        'ret_unit': 'day(s)'}
            storages["pri_storage"] = storage

            archiving_rules = {"last_accessed_unit": None,
                               "last_accessed": None,
                               "last_modified_unit": "days",
                               "last_modified": 0,
                               "file_size": 1,
                               "file_size_unit": "MB"}

            archivingplan.create_plan_from_metallic_archiving(
                planname, storages, archiving_rules, rpo=None)
        plans = [planname]
        self.__dropdown.select_drop_down_values(
            values=plans, drop_down_id='contentGroupPlanListDropdown')
        self.__save_plan()

    def set_archiving_rule_and_create_plan(self, planname, storage):
        """
        select provided plan, if not exist, set archiving rules and create new plan,
        then select and save
        Args:
            planname    (str)    :    plan name
            storage    (str)     :    storage name
        """
        archivingplan = ArchivingPlans(self._admin_console)
        existingplans = self.__dropdown.get_values_of_drop_down(
            drop_down_id='contentGroupPlanListDropdown')

        if planname not in existingplans:
            storages = {'pri_storage': None,
                        'pri_ret_period': '30',
                        'sec_storage': None,
                        'sec_ret_period': '45',
                        'ret_unit': 'day(s)'}
            storages["pri_storage"] = storage
            archiving_rules = {"last_accessed_unit": None,
                               "last_accessed": None,
                               "last_modified_unit": "days",
                               "last_modified": 0,
                               "file_size": 1,
                               "file_size_unit": "MB"}

            archivingplan.set_archiving_rule(archiving_rules)
            archivingplan.create_plan_from_metallic_archiving(
                planname, storages, archiving_rules=None, rpo=None)
        else:
            plans = [planname]
            self.__dropdown.select_drop_down_values(
                values=plans, drop_down_id='contentGroupPlanListDropdown')
            self.__save_plan()

    @PageService()
    def run_archive(self):
        """
        click archive option and click yes button to trigger archiving job
        """
        self._admin_console.click_button("Archive")
        self._admin_console.click_button("Yes")

    @PageService()
    def click_restore(self):
        """
        click restore option
        """
        self._admin_console.click_button("Restore")

    @PageService()
    def delete_content_group(self):
        """
        delete content group
        """
        self._admin_console.click_button("Delete")
        self.__rmodaldialog.type_text_and_delete(
            text_val="PRUNING WILL BE BASED ON RETENTION DURATION",
            button_name="Delete")

    @PageService()
    def get_number_of_files_to_be_archived(self):
        """
        get number of files to be archived
        """
        self.access_insights_tab()
        self._admin_console.click_button("To be archived")
        return self.__table.get_total_rows_count()

    @PageService()
    def get_number_of_files_remain_on_disk(self):
        """
        get number of files remain on disk
        """
        self.access_insights_tab()
        self._admin_console.click_button("Remain on disk")
        return self.__table.get_total_rows_count()


class ArchivingNasServer:
    """class for NAS servers under metallic -> archiving"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(self._admin_console)
        self.__rmodaldialog = RModalDialog(self._admin_console)

    @PageService()
    def access_nas_server(self, nas_server_host_name):
        """
        Access nas server client
        Args:
            nas_server_host_name       (String)       --    nas server host name
        """
        self.__table.access_link(nas_server_host_name)

    @PageService()
    def is_nas_server_exists(self, nas_server_host_name):
        """
        Check if nas server exists
        Args:
            nas_server_host_name        (String)       --    nas server host name
        """
        return self.__table.is_entity_present_in_column(
            'Name', nas_server_host_name)

    @PageService()
    def retire_nas_server(self, nas_server_host_name):
        """
        retire nas server
        Args:
            nas_server_host_name        (String)       --    nas server host name
        """
        self.__table.access_action_item(nas_server_host_name, "Retire")
        self.__rmodaldialog.type_text_and_delete(text_val="RETIRE",
                                                 button_name="Retire")

    @PageService()
    def delete_nas_server(self, nas_server_host_name):
        """
        delete nas server
        Args:
            nas_server_host_name        (String)       --    nas server host name
        """
        self.__table.access_action_item(nas_server_host_name, "Delete")
        self.__rmodaldialog.type_text_and_delete(text_val="DELETE",
                                                 button_name="Delete")


class ArchivingPlans(Plans):
    """class for Plans under metallic -> archiving"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.__table = Rtable(self._admin_console)
        self.__dropdown = RDropDown(self._admin_console)

    @WebAction()
    def __open_edit_archive_frequence_dialog(self):
        """ Method to open edit archive frequence dialog """
        edit_backup_window_link = self._driver.find_element(By.XPATH, 
            "//*[contains(@class, 'backup-freq-wrapper')]//button")
        edit_backup_window_link.click()

    @WebAction()
    def __open_edit_archive_window_dialog(self):
        """ Method to open edit archive window dialog """
        edit_backup_window_link = self._driver.find_element(By.XPATH, 
            "//*[contains(@class, 'backup-window')]//button")
        edit_backup_window_link.click()

    @PageService()
    def set_archiving_rule(self, archiving_rules):
        """
        set archiving rules
        archiving_rules (dictionary):   dictionary containing values of archiving rules
            Eg. -   archiving_rules = {
            "last_modified_unit": None,
            "last_modified": None,
            "last_modified_unit": "hours",
            "last_modified": 0,
            "file_size": 1,
            "file_size_unit": "MB"
            }
        """
        if archiving_rules['last_accessed'] is not None:
            self.__dropdown.select_drop_down_values(
                values=["Last accessed"],
                drop_down_id='timestampAccessRuleSelection')
            self._admin_console.fill_form_by_id(
                "accessedAgo", archiving_rules['last_accessed'])

        if archiving_rules['last_accessed_unit']:
            units = [archiving_rules['last_accessed_unit']]
            self.__dropdown.select_drop_down_values(
                values=units, drop_down_id='timestampRuleSelection')

        if archiving_rules['last_modified'] is not None:

            self.__dropdown.select_drop_down_values(
                values=["Last modified"],
                drop_down_id='timestampAccessRuleSelection')
            self._admin_console.fill_form_by_id(
                "accessedAgo", archiving_rules['last_modified'])

        if archiving_rules['last_modified_unit']:
            units = [archiving_rules['last_modified_unit']]
            self.__dropdown.select_drop_down_values(
                values=units, drop_down_id='timestampRuleSelection')

        if archiving_rules['file_size'] is not None:
            self._admin_console.fill_form_by_id(
                "size", archiving_rules['file_size'])

        if archiving_rules['file_size_unit']:
            units = [archiving_rules['file_size_unit']]
            self.__dropdown.select_drop_down_values(
                values=units, drop_down_id='fileSizeRuleSelection')

    @PageService()
    def add_new_plan(
            self,
            plan_name,
            storage,
            archiving_rules,
            archive_day=None,
            archive_duration=None,
            rpo=None,):
        """
        Method to add a new plan in step "select a plan" when creating new content group
        Args:
            plan_name (string): Name of the plan to be created

            storage (dict) : Dict containing storage attributes for admin console
                Eg. - self._storage = {'pri_storage': None,
                         'pri_ret_period':'30',
                         'sec_storage': None,
                         'sec_ret_period':'45',
                         'ret_unit':'day(s)'}


            rpo (dictionary): dictionary containing RPO values
                Eg. -   rpo = {
                "archive_frequency": 2
                "archive_frequency_unit": Hours
                }

            archiving_rules (dictionary):   dictionary containing values of archiving rules
                Eg. -   archiving_rules = {
                "last_modified_unit": "hours",
                "last_modified": 0,
                "file_size": 1,
                "file_size_unit": "KB"
                }

        """
        self._admin_console.fill_form_by_name("planName", plan_name)

        if rpo:
            if rpo['archive_frequency']:
                self.__open_edit_archive_frequence_dialog()
                self._admin_console.wait_for_completion()
                self.__admin_console.fill_form_by_id(
                    "incremantalBackup", rpo['archive_frequency'])
            if rpo['archive_frequency_unit']:
                units = [rpo['archive_frequency_unit']]
                self.__dropdown.select_drop_down_values(
                    values=units, drop_down_id='incremantalBackupDropdown')

        self.__dropdown.select_drop_down_values(
            values=[storage['pri_storage']], drop_down_id='storageDropdown')
        if archive_day and archive_duration:
            self.__dropdown.select_drop_down_values(
                values=[archive_duration], drop_down_id='retentionPeriodDaysUnit')
            self._admin_console.fill_form_by_id(
                "retentionPeriodDays", archive_day)

        if archiving_rules:
            self.set_archiving_rule(archiving_rules)

        self._admin_console.click_button(value="Create")

    @PageService()
    def create_plan_from_metallic_archiving(
            self,
            plan_name,
            storage,
            archiving_rules,
            archive_day=None,
            archive_duration=None,
            rpo=None,):
        """
        Method to create Archival plan from metallic -> archiving -> plan

        Args:
            plan_name (string): Name of the plan to be created

            storage (dict) : Dict containing storage attributes for admin console
                Eg. - self._storage = {'pri_storage': None,
                         'pri_ret_period':'30',
                         'sec_storage': None,
                         'sec_ret_period':'45',
                         'ret_unit':'day(s)'}


            rpo (dictionary): dictionary containing RPO values
                Eg. -   rpo = {
                "archive_frequency": 2
                "archive_frequency_unit": Hours
                }

            archiving_rules (dictionary):   dictionary containing values of archiving rules
                Eg. -   archiving_rules = {
                "last_modified_unit": "hours",
                "last_modified": 0,
                "file_size": 1,
                "file_size_unit": "KB"
                }

        """
        self._admin_console.click_button("Create new Plan"))
        self._admin_console.fill_form_by_name("planName", plan_name)

        if rpo:
            if rpo['archive_frequency']:
                self.__open_edit_archive_frequence_dialog()
                self._admin_console.wait_for_completion()
                self.__admin_console.fill_form_by_id(
                    "incremantalBackup", rpo['archive_frequency'])
            if rpo['archive_frequency_unit']:
                units = [rpo['archive_frequency_unit']]
                self.__dropdown.select_drop_down_values(
                    values=units, drop_down_id='incremantalBackupDropdown')

        if archive_day and archive_duration:
            self.__dropdown.select_drop_down_values(
                values=[archive_duration], drop_down_id='retentionPeriodDaysUnit')
            self._admin_console.fill_form_by_id(
                "retentionPeriodDays", archive_day)

        if archiving_rules:
            self.set_archiving_rule(archiving_rules)

        self._admin_console.click_button("Next")
        self.__dropdown.select_drop_down_values(
            values=[storage['pri_storage']], drop_down_id='storageDropdown')
        self._admin_console.click_button("Next")
        self._admin_console.click_button("Submit")

    @PageService()
    def is_plan_exists(self, archivingplanname):
        """
        check whether plan existing under metallic -> archiving -> plans
        Args:
            archivingplanname (string): archiving plan name
        """
        return self.__table.is_entity_present_in_column(
            'Plan name', archivingplanname)

    @PageService()
    def delete_plan(self, archivingplanname):
        """
        check whether plan existing under metallic -> archiving -> plans
        Args:
            archivingplanname (string): archiving plan name
        """
        self.__table.access_action_item(archivingplanname, "Delete")
        self._admin_console.click_button("Yes")
