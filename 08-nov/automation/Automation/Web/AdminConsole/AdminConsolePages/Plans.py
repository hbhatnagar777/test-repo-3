# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
plans page on the AdminConsole

Class:

    Plans()

Functions:

    _add_replication_details()                      --  add replication details
    _select_entities()                              --  Selects Entities Needed For a
                                                        Data Classification Plan
    _deselect_entities()                            --  Deselects Entities For a given
                                                        Data Classification Plan
    _click_create_index_server()                    --  Clicks the create index server button
    __set_dynamics365_retention_period              --  Assign retention time in units to a Dynamics 365 Plan
    __define_exclusions                             --  To Enable/Disable Exclusion filters in O365 plan
    create_replication_plan()                       --  creates backup and replication plan
    create_data_classification_plan()               --  Creates a Data Classification plan
    edit_data_classification_plan()                 --  Edit a given data classification
                                                         plan and add/remove the given entities
    deselect_entities_in_data_classification_plan() --  Deselects all entities
                                                         in a given data classification plan
    action_delete_plan()                            --  deletes the plan with the given name
    list_plans()                                    --  lists all the plans
    select_plan()                                   --  selects the plan
    create_server_plan()                            --  create server plan by entering necessary data
    create_ibmi_vtl_plan()                          --  create IBMi VTL plan by entering necessary data
    create_laptop_plan()                            --  create laptop plan by entering necessary data
    delete_plan                                     --  deletes the plans given in the dictionary
    create_laptop_derived_plan()                    --  create laptop derived plan by entering necessary data
    create_archive_plan()                           --  Method to create Archival plan
    create_dynamics365_plan()                       --  Method to create a Dynamics 365 Plan
    getting_started_create_sdg_plan                 --  Creates a SDG Plan from getting started page
    available_plan_types()                          --  Method to return available plan types
    edit_plan_name()                                --  Method to edit plan name
    search_for()                                    --  search a string in the search bar and return all the plans listed
    create_simplified_ra_plan()                     --  Creates RA plan with minimal inputs from project page
"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RDropDown, RPanelInfo, RModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog, Form, SLA, RTags
from Web.AdminConsole.Components.content import RBackupContent
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.core import Toggle, Checkbox, BlackoutWindow, CalendarView
from datetime import datetime
from Web.AdminConsole.Components.alert import Alert


class Plans:
    """ Class for the Plans page """

    def __init__(self, admin_console: AdminConsole):
        """
        Method to initiate Plans class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__rmodal_panel = RModalPanel(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__governance_apps = GovernanceApps(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__navigator = self.__admin_console.navigator
        self.__rbackup_content = RBackupContent(self.__admin_console)
        self.__checkbox = Checkbox(self.__admin_console)
        self.__toggle = Toggle(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__rwizard = Wizard(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__rpo = RPO(self.__admin_console)
        self.__calendar = CalendarView(self.__admin_console)
        self.__backup_window = BlackoutWindow(self.__admin_console)
        self.__rtags = RTags(self.__admin_console)
        self.__alerts = Alert(self.__admin_console)

    @WebAction()
    def _check_if_entity_selected(self, entity):
        """
        Checks if the entity is already selected

            Args:
                entity (str)   :   String of entities
                    Example Values:
                        "Credit card number",
                        "Social Security number",
                        "Email"
            Returns:
                True if entity already selected
                False if entity not selected
        """
        return self.__admin_console.check_if_entity_exists(
            By.XPATH, "//span[text()='%s']/../../div[1]//span[contains(@class, 'MuiCheckBox')]" % entity)

    @WebAction()
    def __enable_entity_detection(self):
        """
        Enable Entity selection checkbox while DC plan creation
        """
        self.__driver.find_element(By.XPATH,
            "//label[text()='Entity detection']").click()

    @WebAction()
    def _expand_classification(self):
        """Expands the classification accordion"""
        self.__driver.find_element(
            By.XPATH,
            f"//div[contains(@class,'accordion-header')]/h3[contains(text(),"
            f"'{self.__admin_console.props['label.classification']}')]").click()

    @WebAction()
    def _select_entities(self, entities_list):
        """
        Selects Entities Needed For a Data Classification Plan

            Args:
                entities_list (list)   :   List of entities
                    Example Values:
                        "Credit card number",
                        "Social Security number",
                        "Email"
        """
        # select all option is not supported. so adding logic to click on group fully to select all items
        if "Select all" in entities_list and len(entities_list) == 1:
            entities_list = ["Financial", "Global", "Healthcare", "Personal"]
        for entity in entities_list:
            if not self._check_if_entity_selected(entity):
                self.__driver.find_element(
                    By.XPATH, "//span[text()='%s']/../../div" % entity).click()
                self.__admin_console.wait_for_completion()
            else:
                self.log.info("Entity: %s already selected" % entity)

    @WebAction()
    def _deselect_entities(self, entities_list):
        """
         Entities For a Given Data Classification Plan

            Args:
                entities_list (list)   :   List of entities
                    Example Values:
                        "Credit card number",
                        "Social Security number",
                        "Email"
        """
        for entity in entities_list:
            if self._check_if_entity_selected(entity):
                self.__driver.find_element(By.XPATH,
                                           "//span[text()='%s']/../../div" % entity).click()
                self.__admin_console.wait_for_completion()
            else:
                self.log.info("Entity: %s already deselected" % entity)

    @WebAction()
    def __click_create_plan_button(self):
        """
        Click on the create plan button
        """
        self.__driver.find_element(By.XPATH,
            "//button[@id='action-grid' and text()='Create plan']").click()

    @WebAction()
    def __click_server_plan_next_button(self):
        """
        Click on the next button while creating Server Plan
        """
        self.__rwizard.click_next()

    @WebAction()
    def __click_server_plan_save_button(self):
        """
        Click on the next button while creating Server Plan
        """
        self.__driver.find_element(By.XPATH, 
            "//button[contains(@class, 'MuiButton-textPrimary')]//div[text()='Save']"
        ).click()

    @WebAction()
    def __open_rpo_modal(self):
        """
        Clicks on the link to open the modal to set RPO
        """
        self.__driver.find_element(By.XPATH, 
            "//div[@class='schedule-wrapper']//button[@title='Edit']"
        ).click()

    @WebAction()
    def backup_window_selection(self, not_run_interval):
        """
        Edits the backup window time slot based on the input given

        Args:
            not_run_interval    (dict)   --  the time slots when the backup should not be run
        """
        self.__driver.find_element(By.LINK_TEXT, "Clear").click()
        self.__admin_console.wait_for_completion()
        keys = not_run_interval.keys()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            self.__driver.find_element(By.XPATH, "//a[text()='" + day + "']").click()
            self.__admin_console.wait_for_completion()
            if day in keys:
                slot_values = self.__driver.find_elements(By.XPATH, f"//a[text()='{day}']/../../td")
                for slot in slot_values:
                    class_name = slot.get_attribute('class')
                    if class_name != 'label-day':
                        if int(slot.get_attribute('date-time-id')) in not_run_interval[day]:
                            if 'selected' in class_name:
                                slot.click()

    @WebAction()
    def _click_create_index_server(self):
        """Clicks the create index server button"""
        self.log.info("Clicking create index server button")
        self.__driver.find_element(By.CLASS_NAME, "k-i-plus-outline").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _select_dc_plan_solution(self, solution):
        """Selects the DC plan solution for which plan has to be created"""
        plan_types_dict = {
            "casemanager": self.__admin_console.props['label.casemanager'],
            "fso": self.__admin_console.props['label.analytics'],
            "gdpr": self.__admin_console.props['label.gdpr'],
            "ci": self.__admin_console.props['label.contentIndexing']
        }
        self.__driver.find_element(By.XPATH, "//span[text()='%s']" % plan_types_dict[solution]).click()

    @PageService()
    def create_data_classification_plan(
            self, plan, index_server, content_analyzer=None, entities_list=None,
            select_all=False, content_search=True, metadata_only=False,
            content_analysis=True, enable_ocr=False, target_app='gdpr',
            create_index_server=False, node_name=None, index_directory=None, classifier_list=None, guided_setup=False,
            storage_pool=False):
        """
        Creates a Data Classification plan

            Args:
                plan (str)           :   Name of the plan to be created
                index_server (str)        :   Index Server name
                content_analyzer (str/list)   :   Content Analyzer name or list of content analyzer name
                entities_list (list)   :   List of entities
                    Values:
                        "Credit card number",
                        "Social Security number",
                        "Email"
                select_all (bool)   :   True/False to select all entities
                content_search (bool)    : True/False to enable content search
                metadata_only (bool)    : True to select Metadata.
                                          False to select both Metadata and content
                content_analysis (bool)    : True/False to enable content analysis for Case Manager
                enable_ocr (bool)    : True/False to enable
                                            content extraction from scanned docs for SDG
                target_app (str)     :    The target app for the plan to be created for.
                                        Default is gdpr
                    Values:
                        "gdpr"(default),
                        "casemanager",
                        "fso"
                create_index_server (bool)  :   True if new index server has to be created
                                                False if existing index server to use
                node_name   (str)           :   Index server node name for new index server
                index_directory (str)       :   Index directory for the new index server
                classifier_list (list)      :   list of classifier to be selected
                guided_setup  (bool)              :   create plan from guided setup or not
                storage_pool (str)          :   The storage pool to be selected

            """
        if isinstance(content_analyzer, str):
            content_analyzer = [content_analyzer]
        self.log.info("Creating data classification plan with name: %s", plan)
        if not guided_setup:
            self.__table.access_toolbar_menu(self.__admin_console.props['label.createProfile'])
            self.__table.access_menu_from_dropdown(self.__admin_console.props['label.dataClassification'])
            self.__admin_console.wait_for_completion()
            self._select_dc_plan_solution(target_app)
            self.__admin_console.button_next()
        self.log.info("Entering plan name")
        self.__admin_console.fill_form_by_id("planName", plan)
        if create_index_server:
            self.log.info("Creating Index Server with node: %s" % node_name)
            self.__rwizard.click_icon_button_by_title(self.__admin_console.props['title.add.indexServer'])
            self.log.info("Filling in Index server name")
            self.__admin_console.fill_form_by_id("newIndexServerName", index_server)
            self.log.info("Selecting index server node name")
            self.__rdropdown.select_drop_down_values(drop_down_id="indexServerNodes", values=[node_name])
            self.log.info("Filling in Index directory")
            self.__admin_console.fill_form_by_id(node_name, index_directory)
            self.__rmodal_panel.save()
            self.__admin_console.wait_for_completion()
        self.log.info("Selecting Index Server")
        self.__rdropdown.select_drop_down_values(drop_down_id="IndexServersDropdown", values=[index_server])
        if target_app != 'fso':
            if target_app == 'casemanager':
                self.__admin_console.button_next()
                if content_analysis:
                    self.log.info("Clicking on Enabling Entity detection")
                    self.__rwizard.enable_toggle(self.__admin_console.props['label.entityDetection'])
                    self.__admin_console.wait_for_completion()
            if content_analysis:
                self.log.info("Deselecting existing CA")
                self.__driver.find_element(By.XPATH, "//*[@data-testid='CancelIcon']").click()
                self.log.info("Selecting content analyzer")
                self.__rdropdown.select_drop_down_values(drop_down_id="ContentAnalyzersDropdown",
                                                         values=content_analyzer)
                if select_all:
                    self._select_entities(['Select all'])
                else:
                    self._select_entities(entities_list)
                if classifier_list:
                    self._expand_classification()
                    time.sleep(2)
                    self.__rdropdown.select_drop_down_values(drop_down_id="classifiersDropdown", values=classifier_list)
            if target_app == 'gdpr':
                self.__admin_console.button_next()
                if storage_pool:
                    self.__rdropdown.select_drop_down_values(values=[storage_pool], drop_down_id="storagePool")
            if enable_ocr:
                self.__rwizard.enable_toggle('Extract text from image')
        else:
            self.__admin_console.button_next()
        self.__admin_console.click_submit()

    @PageService()
    def edit_data_classification_plan(self, plan, entities_list):
        """
        Edit a given data classification plan and add/remove the given entities
        :param plan    (str)   --  Plan name to be edited
        :param entities_list    (list)    -- Entities list to be added or removed in the plan
        Raise:
                Exception if modification of Data Classification plan fails
        """
        self.log.info("Click Edit in plan '%s'", plan)
        self.__driver.find_element(By.XPATH, "//span[contains(@title,'Entity detection')]/../..//button[contains(@title,'Edit')]").click()
        self.__admin_console.wait_for_completion()
        self._select_entities(entities_list)
        self.log.info("Clicking on Save after the selection of the entities")
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def deselect_entities_in_data_classification_plan(self, plan, entities_list=None):
        """
        Deselects all entities in a given data classification plan
        :param plan    (str)   --  Plan name from which entities will be deselected
        :param entities_list    (list)  --  Entity names list to be deselected
        """
        # Select all feature deprecated, method will return an error if entities list not set
        self.log.info("Click Edit in plan '%s'", plan)
        self.__driver.find_element(By.XPATH, "//span[contains(@title,'Entity detection')]/../..//button[contains(@title,'Edit')]").click()
        self.__admin_console.wait_for_completion()
        self._deselect_entities(entities_list)
        self.__modal_panel.submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def action_delete_plan(self, plan):
        """Deletes the plan with the given name
            plan    :   a string, the name of the plan to be deleted
        """
        delete_label = self.__admin_console.props['label.globalActions.delete']
        delete_label = delete_label.upper()
        self.__table.access_action_item(plan, "Delete")
        self.__admin_console.fill_form_by_id('confirmText', delete_label)
        self.__admin_console.click_button(id="Submit")
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def available_plan_types(self):
        """Returns the list of available plan types"""
        return self.__table.get_all_tabs()[1:]

    @PageService()
    def reset_filters(self):
        """Method to reset the filters applied on the page"""
        self.__table.reset_filters()

    @PageService()
    def list_plans(self, plan_type: str = str(), company_name: str = str()):
        """
            Lists all the plans

            Arguments:
                plan_type       (str):      To filter/ fetch plans of a particular type
                company_name    (str):      To filter/ fetch plans of a particular company
        """
        if plan_type:
            self.__table.view_by_title(plan_type)
        if company_name:
            self.__table.select_company(company_name)
        return self.__table.get_column_data(column_name= 'Plan name', fetch_all= True)

    @PageService()
    def select_plan(self, plan):
        """
        Selects the given plan
        """
        self.__navigator.navigate_to_plan()
        self.__table.access_link(plan)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_plan_name(self, new_name):
        """Method to edit plan name"""
        self.__page_container.edit_title(new_name)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def create_simplified_ra_plan(self, plan, entities_list=None, select_all=False):
        """
        Creates Risk Analysis plan with minimal inputs from project page

            Args:
                plan (str)           :   Name of the plan to be created
                entities_list (list)   :   List of entities
                    Values:
                        "Credit card number",
                        "Social Security number",
                        "Email"
                select_all (bool)   :   True/False to select all entities
            """
        self.log.info("Creating data classification plan with name: %s", plan)
        self.log.info("Entering plan name")
        self.__admin_console.fill_form_by_id("planName", plan)
        self.log.info("Selecting Entities")
        if select_all:
            self._select_entities(['Select all'])
        else:
            self._select_entities(entities_list)
        self.__admin_console.click_button(
            self.__admin_console.props['button.label.create']
        )

    @WebAction()
    def __set_plan_name(self, plan_name):
        """
        Method to set plan name
        Args:
            plan_name (str) : name of the plan
        """
        self.__admin_console.fill_form_by_name("planName", plan_name)

    @WebAction()
    def __open_edit_backup_window_dialog(self):
        """ Method to open edit backup window dialog """
        edit_backup_window_link = self.__driver.find_element(By.XPATH,
            "//cv-backup-window-list[@data-cv-model='globalTemplate.backupWindow']")
        edit_backup_window_link.click()

    @WebAction()
    def __open_edit_full_backup_window_dialog(self):
        """ Method to open edit backup window dialog """
        edit_full_backup_window_link = self.__driver.find_element(By.XPATH,
            "//cv-backup-window-list[@data-cv-model='globalTemplate.fullBackupWindow']")
        edit_full_backup_window_link.click()

    @WebAction()
    def __set_backup_window(self, backup_day, backup_time):
        """
        Method to set back up window
        Args:
            backup_day (dict): dictionary containing values of backup days for backup window
                Eg.- dict.fromkeys(['1', '2', '3'], 1)
                        backup days for schedule
                            1 : Monday
                            2: Tuesday and so on
            backup_time (dict): dictionary containing values of backup time for backup window
                Eg.- dict.fromkeys(['2', '3', '4', '5'], 1)
                    backup time for schedule
                        2 : 12:00am to 1:00 am
                        3 : 1:00am to 2:00 am
                        and so on..
        """

        self.__admin_console.select_hyperlink(self.__admin_console.props['action.clear'])
        for key_day, val_day in backup_day.items():
            if val_day == 1:
                for key_time, val_time in backup_time.items():
                    if val_time == 1:
                        self.__driver.find_element(By.XPATH,
                            f"//table[@class='time-obj']/tbody/tr[{key_day}]/td[{key_time}]").click()
        self.__driver.find_element(By.XPATH, "//*[@id='editPlanOperationWindowModal_button_#4242']").click()
        self.__admin_console.check_error_message()

    @WebAction()
    def __open_edit_storage_dialog(self):
        """ Method to set primary storage of a plan """
        self.__driver.find_element(By.XPATH,
            "//cv-grid//a[contains(@class,'uib-dropdown-toggle')]").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH,
            f"//a[contains(text(),'{self.__admin_console.props['action.edit']}')]").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __set_retention_period(self, ret_period):
        """
        Method to set retention period

        Args:
            ret_period (str) : Value of retention period
        """
        textbox = self.__driver.find_element(By.XPATH,
            "//input[@id='retentionPeriodDays']")
        textbox.send_keys(u'\ue009' + 'a' + u'\ue003') # CTRL + A + Backspace
        textbox.send_keys(ret_period)

    @WebAction()
    def __set_retention_unit(self, ret_unit):
        """
        Method to set retention unit

        Args:
            ret_unit (str) : retention unit to be set
        """
        self.__rdropdown.select_drop_down_values(values=[ret_unit], drop_down_id='retentionPeriodDaysUnit')

    @WebAction()
    def __modify_server_plan_copy_retention(self, copy_name, ret_period, ret_unit):
        """
        Method to edit retention of a copy created while creating a server backup plan
        in the add copy step; prior to submitting the configs for plan creation

        Args:
            copy_name (str) : Name of copy
            ret_period (str) : Value of retention period
            ret_unit (str) : retention unit to be set
        """
        self.__table.access_action_item(copy_name, 'Edit')
        self.__set_retention_period(ret_period)
        self.__set_retention_unit(ret_unit)
        self.__dialog.click_submit()

    @WebAction()
    def __specify_date_backups_on_or_after(self, copy_name, date):
        """
        Method to specify date from when to backup copies for a copy during plan creation

        Args:
            copy_name (str) : Name of copy
            date (dict) : :   Date value as dictionary
                                                Eg,
                                                {
                                                    'year': 1999,
                                                    'month': "March",
                                                    'day': 21,
                                                }
        """
        self.__table.access_action_item(copy_name, 'Edit')
        self.__admin_console.select_radio(id='specificBackup')
        self.__admin_console.click_by_xpath("//button[@title='Open calendar']")
        self.__calendar.select_date(date, click_today=False)    # selecting TODAY closes calendar, avoid it
        self.__admin_console.click_button(value="Save")

    @WebAction()
    def __set_rpo_start_time(self, rpo_time):
        """
        Method to set Backup Start Time for RPO

        Args:
            rpo_time (str):    Value of time to be set

        """
        textbox = self.__driver.find_element(By.XPATH,
            "//div[@id='fullBackupFrequency_startTime']//input")
        textbox.send_keys(Keys.CONTROL + "a")
        textbox.send_keys(Keys.DELETE)
        textbox.send_keys(rpo_time)

    @WebAction()
    def __click_plan_type(self, plan_type_id):
        """
        Method to select type of plan to be created from create plan option menu

        Args:
            plan_type_id (str) : id of the plan type to be selected

        """
        self.__driver.find_element(By.LINK_TEXT, plan_type_id).click()

    @WebAction()
    def __expand_sub_panel(self, sub_panel_text):
        """ Method to expand sub panel """
        panel_xpath = self.__driver.find_element(By.XPATH,
            f"//div[@class='cv-accordion-header']//span[contains(text(),'{sub_panel_text}')]")
        panel_xpath.click()

    @WebAction()
    def __select_file_system_tab(self, file_system):
        """ Method to select file system """
        self.__driver.find_element(By.XPATH,
            "//ul[@class='nav nav-tabs nav-justified']//a[contains(text(),\
            '" + file_system + "')]").click()

    @WebAction()
    def __set_sla_hours(self, sla_hours):
        """ Method to set sla hours """
        elems = self.__driver.find_elements(By.ID, "backupCopyRPO_hours")
        for elem in elems:
            if elem.is_displayed():
                elem.clear()
                elem.send_keys(Keys.CONTROL, 'a')
                elem.send_keys(Keys.BACKSPACE)
                elem.send_keys(sla_hours)

    @WebAction()
    def __set_sla_minutes(self, sla_minutes):
        """ Method to set sla minutes """
        elems = self.__driver.find_elements(By.ID, "backupCopyRPO_minutes")
        for elem in elems:
            if elem.is_displayed():
                elem.clear()
                elem.send_keys(Keys.CONTROL, 'a')
                elem.send_keys(Keys.BACKSPACE)
                elem.send_keys(sla_minutes)

    @WebAction()
    def __enable_allow_override(self):
        """ Method to set allow over ride check box state """
        if not self.__driver.find_element(By.XPATH,
                "//label[contains(@for,'derivation-enabled')]/preceding-sibling::input") \
                .get_attribute('checked') == 'checked':
            self.__driver.find_element(By.XPATH,
                "//label[contains(@for,'derivation-enabled')]").click()

    @WebAction()
    def __select_override_backup_content(self):
        """ Method to select the override backup content"""
        if self.__rwizard.toggle.is_editable(
                id='override-setting-toggle-backupContent'):
            self.__rwizard.toggle.disable(
                id='override-setting-toggle-backupContent')
        else:
            raise CVWebAutomationException(
                'Toggle is not editable as was expected')

    @WebAction()
    def __select_override_retention(self):
        """ Method to select the override retention"""
        if self.__rwizard.toggle.is_editable(
                id='override-setting-toggle-retention'):
            self.__rwizard.toggle.disable(
                id='override-setting-toggle-retention')
        else:
            raise CVWebAutomationException(
                'Toggle is not editable as was expected')

    @WebAction()
    def __select_override_storage(self):
        """ Method to select the override storage"""
        if self.__rwizard.toggle.is_editable(
                id='override-setting-toggle-storage'):
            self.__rwizard.toggle.disable(
                id='override-setting-toggle-storage')
        else:
            raise CVWebAutomationException(
                'Toggle is not editable as was expected')

    @WebAction()
    def __select_override_rpo(self):
        """ Method to select the override rpo"""
        if self.__rwizard.toggle.is_editable(
                id='override-setting-toggle-rpo'):
            self.__rwizard.toggle.disable(
                id='override-setting-toggle-rpo')
        else:
            raise CVWebAutomationException(
                'Toggle is not editable as was expected')

    @WebAction()
    def __set_override_option(self, override_drop_down_id, override_value):
        """ Method to set override option """
        self.__rdropdown.select_drop_down_values(
            drop_down_id=override_drop_down_id, values=[override_value])

    @WebAction()
    def __click_browse_button(self):
        """ Method to click on browse button """
        self.__driver.find_element(By.ID, "generalSetup_button_#6532").click()

    @WebAction()
    def __select_browse_root(self):
        """ Method to select Browse root  """
        self.__driver.find_element(By.XPATH,
            "//span[@class='path-title ng-binding']").click()

    @WebAction()
    def __click_new_folder_button(self):
        """ Method to click on New folder button """
        self.__driver.find_element(By.XPATH,
            "//*[@id='machineBrowse_button_#5674']").click()

    @PageService()
    def __create_index_server(self):
        """ Method to create index server """
        self.__click_browse_button()
        self.__admin_console.wait_for_completion()
        self.__select_browse_root()
        self.__click_new_folder_button()
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_id('folder-name', "IndexServer")
        self.__modal_panel.submit()
        self.__admin_console.click_button(self.__admin_console.props['label.save'])

    @WebAction()
    def __enable_secondary_storage(self):
        """ Method to enable secondary storage for laptop plan """
        if not self.__driver.find_element(By.XPATH,
                "//input[@id='enableSecondaryStorage']").is_selected():
            self.__driver.find_element(By.XPATH,
                "//label[@for='enableSecondaryStorage']").click()

    @WebAction()
    def __select_radio_by_id(self, radio_button_id):
        """ Method to select radio button based on id """
        if not self.__driver.find_element(By.ID, radio_button_id).is_selected():
            self.__driver.find_element(By.ID, radio_button_id).click()

    @WebAction()
    def __select_checkbox_by_label(self, label):
        """ Method to select checkbox by label """
        if not self.__driver.find_element(By.XPATH,
                f"//label[text()='{label}']/preceding-sibling::input").is_selected():
            self.__driver.find_element(By.XPATH, f"//label[text()='{label}']").click()

    @WebAction()
    def __click_next_button(self):
        """ Method to click next button on Laptop plan creation page """
        next_buttons = self.__driver.find_elements(By.XPATH,
            "//div[contains(@class,'button-container')]/button[contains(text(),'Next')]")
        for next_button in next_buttons:
            if next_button.is_displayed():
                next_button.click()
                break

    @WebAction()
    def __setup_edge_drive_features(self,
                                    allowed_features,
                                    media_agent):
        """
        Method to setup edge drive features

        Args:
            allowed_features (dictionary): dictionary containing features to be enabled for the
                             plan and corresponding attributes
                Eg. - allowed_features = {'Edge Drive': 'ON',
                                          'audit_drive_operations': True,
                                          'notification_for_shares': True,
                                          'edge_drive_quota':'200',
                                          'DLP': 'ON',
                                          'Archiving': 'ON'}

            media_agent (string)    :   media agent to be used to configure edge drive for plan
        """
        if self.__admin_console.check_if_entity_exists("id", "client"):
            self.__admin_console.select_value_from_dropdown('client', media_agent)
        else:
            self.__admin_console.select_value_from_dropdown('mediaAgent', media_agent)

        if self.__admin_console.check_if_entity_exists("id", "mountPath"):
            self.__create_index_server()

        if allowed_features['audit_drive_operations']:
            self.__admin_console.checkbox_select('auditDriveActivities')
        else:
            self.__admin_console.checkbox_deselect('auditDriveActivities')

        if allowed_features['notification_for_shares']:
            self.__admin_console.checkbox_select('enableNotificationsForShares')
        else:
            self.__admin_console.checkbox_deselect('enableNotificationsForShares')

        if allowed_features['edge_drive_quota']:
            self.__admin_console.checkbox_select('isEdgeDriveQuotaEnabled')
            self.__admin_console.fill_form_by_id("edgeDriveQuota", allowed_features['edge_drive_quota'])
        else:
            self.__admin_console.checkbox_deselect('isEdgeDriveQuotaEnabled')

    @WebAction()
    def __click_remove_content(self, tab_id):
        """
        Method to click on remove all content button

        Args:
            tab_id (str) : id of backup/exclusion content tab
        """
        remove_button = f"//div[@class='tab-pane ng-scope active']//div[@id='{tab_id}']" \
                        "//a[contains(@data-ng-click,'deleteAll')]"
        if self.__admin_console.check_if_entity_exists("xpath", remove_button):
            if self.__driver.find_element(By.XPATH, remove_button).is_displayed():
                self.__driver.find_element(By.XPATH, remove_button).click()
                self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_add_content(self, tab_id):
        """
        Method to click on add content button

        Args:
            tab_id (str) : id of backup/exclusion content tab
        """
        add_button = f"//div[@class='tab-pane ng-scope active']//div[@id='{tab_id}']" \
                     "//a[contains(text(),'Add')]"
        self.__driver.find_element(By.XPATH, add_button).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_content(self,
                         content,
                         content_library):
        """
        Method to select backup/exclusion content

        Args:
            content (list) : List with folder names to be selected
                            for content backup
                Eg. - content_backup:["Content Library", "Documents", "Desktop",
                                        "Office", "Music", "Pictures", "Videos"]
            content_library (list): List with content library values to be
                            selected for backup
                Eg. - content_library = ['Content Library', 'GoogleDrive', 'Image',
                                         'Office', 'OneDrive', 'System',
                                        'Temporary Files', 'Text',
                                        'Thumbnail Supported', 'Video',
                                        'iCloudDrive']
        """
        for value in content:
            if not value == 'Content Library':
                if not self.__driver.find_element(By.XPATH,
                        "//label[@for='" + value + "']/../..//input").is_selected():
                    self.__driver.find_element(By.XPATH,
                        "//label[@for='" + value + "']/../..//input").click()
                    if value == 'Library':
                        break
            else:
                if self.__admin_console.check_if_entity_exists(
                        "xpath", "//li[@class='ivh-treeview-node ng-scope ng-isolate-scope "
                                 "ivh-treeview-node-collapsed']"):
                    self.__driver.find_element(By.XPATH,
                        "//li[@class='ivh-treeview-node ng-scope ng-isolate-scope ivh-treeview"
                        "-node-collapsed']//span[@class='glyphicon glyphicon-chevron-right']"
                    ).click()
                    for value_lib in content_library:
                        if not self.__driver.find_element(By.XPATH,
                                "//label[@for='" + value + "']/../..//input").is_selected():
                            self.__driver.find_element(By.XPATH,
                                "//label[@for='" + value_lib + "']/../..//input").click()

    @WebAction()
    def __click_add_custom_content(self):
        """ Method to click on add custom content link """
        self.__driver.find_element(By.XPATH,
            "//a[contains(text(),'" + self.__admin_console.props['label.customContent'] + "')]").click()

    @WebAction()
    def __click_create_derived_plan_button(self):
        """ Method to click on derive plan"""
        self.__page_container.access_page_action('Derive and create new')

    @WebAction()
    def __select_file_size_unit(self, file_size_unit):
        """ Method to select File Size Unit """
        self.__driver.find_element(By.XPATH,
            "//select[@ng-model='fileSizeConfig.rule']/option[text()='{}']".format(
                file_size_unit)).click()

    @WebAction()
    def __select_last_modified_unit(self, last_modified_unit):
        """ Method to select Last Modified Unit """
        self.__driver.find_element(By.XPATH,
            "//select[@ng-model='fileTimestampConfig.timestampRule']/option[text()='{}']".format(
                last_modified_unit)).click()

    @WebAction()
    def __select_last_accessed_unit(self, last_accessed_unit):
        """ Method to select Last Modified Unit """
        self.__driver.find_element(By.XPATH,
            "//select[@ng-model='fileTimestampConfig.timestampRule']/option[text()='{}']".format(
                last_accessed_unit)).click()

    @WebAction()
    def __select_access_time_rule(self):
        """ Method to select access time rule. """
        self.__driver.find_element(By.XPATH,
            "//select[@ng-model='fileTimestampConfig.accessRule']/option[text()='Last accessed']").click()

    @WebAction()
    def __select_modify_time_rule(self):
        """ Method to select modify time rule. """
        self.__driver.find_element(By.XPATH,
            "//select[@ng-model='fileTimestampConfig.accessRule']/option[text()='Last modified']").click()

    @WebAction()
    def __select_archive_frequency_unit(self, archive_frequency_unit):
        """ Method to set Archive frequency unit. """
        self.__driver.find_element(By.XPATH,
            "//select[@ng-model='incrementalBackupFreq.type']/option[text()='{}']".format(
                archive_frequency_unit)).click()

    @WebAction()
    def __set_office365_retention_period(self, period):
        """
        Method to set the Office 365 Plan Retention

        Args:
            period (int):   No. of days/months/years data should be retained

        """
        self.__driver.find_element(By.XPATH,
            "//input[@picker-id='deletedRetentionDays']").click()
        input_element = self.__driver.find_element(By.XPATH,
            "//input[@data-ng-model='ctrl.pickerNum']")
        input_element.clear()
        input_element.send_keys(str(period))

    @WebAction()
    def __click_edit_onedrive_filters(self):
        """Clicks on Edit option for OneDrive Filters for Office 365 Plan"""
        self.__driver.find_element(By.XPATH, 
            "//span[contains(text(),'OneDrive')]/parent::div/following-sibling::div"
        ).click()

    @WebAction()
    def __click_file_filters_tab(self):
        """Clicks on File Filters Tab for Office 365 Plan"""
        self.__driver.find_element(By.XPATH, 
            "//span[text()='File filters']").click()

    @WebAction()
    def __define_exclusions(self, enable=True):
        """
            Enables/Disables exclusion filters Office 365 plan
            Args:
            enable (bool):   True/False to enable/disable exclusion filter
        """

        if self.__admin_console.check_if_entity_exists('xpath', "//input[contains(@id, 'excludeFolders')]"):
            if enable == False:
                self.__driver.find_element(By.XPATH,
                                           "//input[@id='isEXCLUDE_ContentDefined']"
                                           ).click()
        else:
            if enable == True:
                self.__driver.find_element(By.XPATH,
                                           "//input[@id='isEXCLUDE_ContentDefined']"
                                           ).click()

    @WebAction()
    def __define_exclusions(self, enable=True):
        """
            Enables/Disables exclusion filters Office 365 plan
            Args:
            enable (bool):   True/False to enable/disable exclusion filter
        """

        if self.__admin_console.check_if_entity_exists('xpath', "//input[contains(@id, 'excludeFolders')]"):
            if enable == False:
                self.__driver.find_element(By.XPATH,
                                           "//input[@id='isEXCLUDE_ContentDefined']"
                                           ).click()
        else:
            if enable == True:
                self.__driver.find_element(By.XPATH,
                                           "//input[@id='isEXCLUDE_ContentDefined']"
                                           ).click()

    @WebAction()
    def __add_include_folder_filter(self, include_filter):
        """
        Adds the include folder filter

        Args:
            include_filter (str):   Filter to be added

        """
        input_element = self.__driver.find_element(By.ID, 'includeFolders')
        input_element.clear()
        input_element.send_keys(include_filter)
        self.__driver.find_element(By.XPATH,
            "//input[@id='includeFolders']/following-sibling::button"
        ).click()

    @WebAction()
    def __add_exclude_folder_filter(self, exclude_filter):
        """
        Adds the exclude folder filter

        Args:
            exclude_filter (str):   Filter to be added

        """
        input_element = self.__driver.find_element(By.ID, 'excludeFolders')
        input_element.clear()
        input_element.send_keys(exclude_filter)
        self.__driver.find_element(By.XPATH,
            "//input[@id='excludeFolders']/following-sibling::button"
        ).click()

    @WebAction()
    def __add_include_file_filter(self, include_filter):
        """
        Adds the include file filter

        Args:
            include_filter (str):   Filter to be added

        """
        input_element = self.__driver.find_element(By.ID, 'includeFileFilter')
        input_element.clear()
        input_element.send_keys(include_filter)
        self.__driver.find_element(By.XPATH,
             "//input[@id='includeFileFilter']/following-sibling::button"
        ).click()

    @WebAction()
    def __add_exclude_file_filter(self, exclude_filter):
        """
        Adds the exclude file filter

        Args:
            exclude_filter (str):   Filter to be added

        """
        input_element = self.__driver.find_element(By.ID, 'excludeFileFilter')
        input_element.clear()
        input_element.send_keys(exclude_filter)
        self.__driver.find_element(By.XPATH,
            "//input[@id='excludeFileFilter']/following-sibling::button"
        ).click()

    @WebAction()
    def __set_dynamics365_retention_period(self, time_period):
        """
            Method to set the Retention for a Dynamics 365 PLan

        Args:
            time_period (int):   No. of days/months/years data should be retained

        """
        self.__rdropdown.select_drop_down_values(values=["Day(s)"], drop_down_id='deletionRetentionPeriodTimePeriodUnit')
        self.__admin_console.fill_form_by_id('deletionRetentionPeriodTimePeriod', time_period)

    @PageService()
    def click_create_derived_plan_button(self):
        """
        click on derive plan button

        """
        self.__click_create_derived_plan_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def backup_content_selection(self, content= [], custom_path= []):
        """Method to select backup content for a plan

        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths

        Example:
            content = ['Desktop', 'Music', 'Google Drive']
        """
        self.__rbackup_content.add_backup_content(content, custom_path)

    @PageService()
    def exclusion_content_selection(self, content= [], custom_path= []):
        """Method to select exclude content for a plan

        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths

        Example:
            content = ['Desktop', 'Music', 'Google Drive']
        """
        self.__rbackup_content.add_exclude_content(content, custom_path)

    @PageService()
    def exception_content_selection(self, content= [], custom_path= []):
        """Method to select exclude content for a plan

        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths

        Example:
            content = ['Desktop', 'Music', 'Google Drive']
        """
        self.__rbackup_content.add_exception_content(content, custom_path)

    @PageService()
    def set_network_resources(self,
                              throttle_send,
                              throttle_receive):
        """
        Method to set network resources

        Args:
            throttle_send (string ot integer): Network Resource send parameter value

            throttle_receive (string or integer): Network Resource receive parameter value
        """
        if throttle_send is not None:
            if throttle_send == "No limit":
                self.__checkbox.check(id='throttleSendInfinite')
            else:
                self.__checkbox.uncheck(id='throttleSendInfinite')
                self.__wizard.fill_text_in_field(
                    id='throttleSend', text=throttle_send)
        if throttle_receive is not None:
            if throttle_receive == "No limit":
                self.__checkbox.check(id='throttleReceiveInfinite')
            else:
                self.__checkbox.uncheck(id='throttleReceiveInfinite')
                self.__wizard.fill_text_in_field(
                    id='throttleReceive', text=throttle_receive)

    @WebAction()
    def __alert_checkbox(self, alert):
        """ Method to get alert checkbox element """
        xp = f"//*[@class='panel-content ']//*[text()='{alert}']"
        return self.__driver.find_element(By.XPATH, xp)

    @WebAction()
    def __edit_alert_checkbox(self, alert):
        """ Method to edit alert checkbox element """
        xp = f"//form[@name='editAlertsForm']//*[text()='{alert}']"
        return self.__driver.find_element(By.XPATH, xp)

    @PageService()
    def set_alerts(self, alerts, edit_alert=False):
        """
        Method to set alerts

        Args:
            alerts (dictionary): Dictionary with values for determining whether alerts should
                be Enabled/Disabled
                Eg. - alerts = {"Backup" : "No backup for last 4 days",
                                "Jobfail": "Restore Job failed",
                                "edge_drive_quota":"Edge drive quota alert",
                                "edge_drive_operations":"Edge drive/share operations alert"}
            edit_alert (boolean) = Whether to edit alerts or not
        """
        if alerts.get("Backup", None):
            if not edit_alert:
                elem = self.__alert_checkbox('No backup for last 4 days')
            else:
                elem = self.__edit_alert_checkbox('No backup for last 4 days')
            if alerts["Backup"] == "No backup for last 4 days":
                self.__checkbox.check("No backup for last 4 days")
            else:
                self.__checkbox.uncheck("No backup for last 4 days")
        if alerts.get("Jobfail", None):
            if not edit_alert:
                elem = self.__alert_checkbox('Restore Job failed')
            else:
                elem = self.__edit_alert_checkbox('Restore Job failed')
            if alerts["Jobfail"] == "Restore Job failed":
                self.__checkbox.check("Restore Job failed")
            else:
                self.__checkbox.uncheck("Restore Job failed")
        if alerts.get("edge_drive_quota", None):
            if not edit_alert:
                elem = self.__alert_checkbox('Edge drive quota alert')
            else:
                elem = self.__edit_alert_checkbox('Edge drive quota alert')
            if alerts["edge_drive_quota"] == "Edge drive quota alert":
                self.__checkbox.check("Edge drive quota alert")
            else:
                self.__checkbox.uncheck("Edge drive quota alert")
        if alerts.get("file_system_quota", None):
            if not edit_alert:
                elem = self.__alert_checkbox('File system quota alert')
            else:
                elem = self.__edit_alert_checkbox('File system quota alert')
            if alerts["file_system_quota"] == "File system quota alert":
                self.__checkbox.check("File system quota alert")
            else:
                self.__checkbox.uncheck("File system quota alert")

    @PageService()
    def set_override_options(self, allow_override, edit_override_laptop=False):
        """
        Method to set override options

        Args:
            allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage pool": "Override required",
                                        "RPO": "Override optional",
                                        "Backup content": "Override not allowed",
                                        "Retention": "Override not allowed"}

            edit_override_laptop (boolean) = Whether to edit override or not
        """
        if allow_override.get('Backup content'):
            self.__set_override_option('backupContent', allow_override['Backup content'])

        if allow_override.get('Storage pool'):
            self.__set_override_option('storagePool', allow_override['Storage pool'])

        if allow_override.get('RPO'):
            self.__set_override_option('RPO', allow_override['RPO'])

        if allow_override.get('Retention'):
            self.__set_override_option('retention', allow_override['Retention'])

    @PageService()
    def set_retention(self, retention):
        """
        Method to set retention values

        Args:
             retention (dict) : dictionary containing retention attributes for laptop plan
                Eg. - retention = {'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                                   'file_version_retention': {'duration': {'value': '4',
                                                                          'unit': 'day(s)'},
                                                              'versions': '5',
                                                              'rules': {'days': '4',
                                                                        'weeks': '5',
                                                                        'months': '6'}}}
                    OR
                        retention = {'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                                       'file_version_retention': {'duration': None,
                                                                  'versions': None,
                                                                  'rules': {'days': '4',
                                                                            'weeks': '5',
                                                                            'months': '6'}}}
        """
        if retention.get('deleted_item_retention', None):

            if retention['deleted_item_retention']['value'] == "Indefinitely":
                self.__wizard.select_radio_button(id="indefinitely")
            else:
                self.__wizard.select_radio_button(id="forNDays")
                self.__wizard.fill_text_in_field(id="deletedItemKeepForTimePeriod",
                                                 text=retention['deleted_item_retention']['value'])
                self.__wizard.select_drop_down_values(id="deletedItemKeepForTimePeriodDropdown",
                                                      values=retention['deleted_item_retention']['unit'])
        if retention.get('file_version_retention', None):

            if retention['file_version_retention']['duration']:
                self.__wizard.select_radio_button(id="retainObjectFor")
                self.__wizard.fill_text_in_field(id="keepOlderVersionsForNDays",
                                                 text=retention['file_version_retention']['duration']['value'])
                self.__wizard.select_drop_down_values(id="filesVersionKeepForTimePeriodDropdown",
                                                      values=retention['file_version_retention']['duration']['unit'])
            elif retention['file_version_retention']['versions']:
                self.__wizard.select_radio_button(id="retain")
                self.__wizard.fill_text_in_field(id="versions",
                                                 text=retention['file_version_retention']['versions'])
            elif retention['file_version_retention']['rules']:
                self.__wizard.select_radio_button(id="sparseRetention")
                self.__wizard.fill_text_in_field(id="dailyVersions",
                                                 text=retention['file_version_retention']['rules']['days'])
                self.__wizard.fill_text_in_field(id="weeklyVersions",
                                                 text=retention['file_version_retention']['rules']['weeks'])
                self.__wizard.fill_text_in_field(id="monthlyVersions",
                                                 text=retention['file_version_retention']['rules']['months'])

    @PageService()
    def set_archiving_rules(self, archiving_rules):
        """
        Method to set archiving rules

        Args:
             archiving_rules (dictionary): dictionary containing values for Archive Feature rules
                Eg. - archiving_rules = {"do_edit": True, "start_clean": "40", "stop_clean": "90",
                                        "file_access_time": "85", "file_modify_time": None,
                                        "file_create_time": "2", "archive_file_size": None,
                                        "max_file_size": None, "archive_read_only": True,
                                        "replace_file": None, "delete_file": None}
        """
        if archiving_rules.get("start_clean", None):
            self.__admin_console.fill_form_by_id("startCleanDisk", archiving_rules["start_clean"])
        if archiving_rules.get("stop_clean", None):
            self.__admin_console.fill_form_by_id("stopCleanDisk", archiving_rules["stop_clean"])
        if archiving_rules.get("file_access_time", None):
            self.__admin_console.fill_form_by_id("fileAccessTime", archiving_rules["file_access_time"])
        if archiving_rules.get("file_modify_time", None):
            self.__admin_console.fill_form_by_id("fileModifiedTime", archiving_rules["file_modify_time"])
        if archiving_rules.get("file_create_time", None):
            self.__admin_console.fill_form_by_id("fileCreatedTime", archiving_rules["file_create_time"])
        if archiving_rules.get("archive_file_size", None):
            self.__admin_console.fill_form_by_id("archiveFileSize", archiving_rules["archive_file_size"])
        if archiving_rules.get("max_file_size", None):
            self.__admin_console.fill_form_by_id("maxFileSize", archiving_rules["max_file_size"])

        if archiving_rules.get("archive_read_only", None):
            self.__admin_console.checkbox_select('archiveReadOnlyFile')
        else:
            self.__admin_console.checkbox_deselect('archiveReadOnlyFile')

        if archiving_rules.get("replace_file", None):
            self.__admin_console.select_radio('replaceFile')
        else:
            self.__admin_console.select_radio('deleteFile')
        self.__modal_panel.submit()

    @PageService()
    def create_server_plan(
            self,
            plan_name,
            storage,
            rpo=None,
            allow_override=None,
            backup_window=None,
            full_backup_window=None,
            backup_data=None,
            snapshot_options=None,
            database_options=None,
            system_state=True,
            full_backup=False,
            vss=True,
            sec_copy_name=None,
            **kwargs):
        """
        Method to create Server plan

        Args:
            plan_name (string): Name of the plan to be created

            storage (dict) : Dict containing storage attributes for admin console
                Eg. - self._storage = {'pri_storage': None,
                         'pri_ret_period':'30',
                         'snap_pri_storage': None,
                         'sec_storage': None,
                         'sec_ret_period':'45',
                         'ret_unit':'Day(s)',
                         'pri_storage_type': 'Archive/Cool/Disk'}

            rpo (list): List of schedule properties
                Eg. - rpo_dict = [{
                            'BackupType' : 'Full',
                            'Agents'     : 'Databases',
                            'Frequency'  : '1',
                            'FrequencyUnit' : 'Day(s)',
                            'StartTime'  : '10:30 pm'
                        }, {
                            'BackupType' : 'Incremental',
                            'Agents'     : 'All agents',
                            'Frequency'  : '10',
                            'FrequencyUnit' : 'Month(s)',
                            'StartTime'  : '05:30 pm'
                        }]

            allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override optional"}

            backup_window (dict)    :   key value pair of day and its backup window timings

                Example:
                    backup_window = {
                        'Monday and Thursday' : ['All day'],
                        'Tuesday' : ['2am-6am', '1pm-6pm'],
                        'Tuesday through Thursday' : ['9pm-12am'],
                        'Wednesday' : ['5am-2pm'],
                        'Friday' : ['1am-3am', '5am-1pm'],
                        'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am'],
                        'Sunday' : ['1am-5am', '7am-1pm', '7pm-11pm']
                    }

            full_backup_window (dict)   :   key value pair of day and its full backup window timings

            backup_data (Dictionary): Dictionary with data to be selected
                for backup or excluded from backup
                Eg. - backup_data = {'file_system':["Mac", "Unix", "Windows"],
                                    'content_backup':["Content Library"],
                                    'content_library':['Content Library', 'GoogleDrive'],
                                    'custom_content':None,
                                    'exclude_folder':['Content Library', 'Documents'],
                                    'exclude_folder_library':['DropBox', 'EdgeDrive', 'Executable']
                                    'exclude_folder_custom_content':None}

            system_state (boolean): value, if "Backup system state" should be checked or not

            full_backup (boolean): value, if "Only with full backup" should be checked or not

            vss (boolean): value, if "Use VSS for system state" should be checked or not

            snapshot_options (dictionary) : dictionary containing values for snapshot parameters
                Eg. - snapshot_options = {'snap_recovery_points':'5',
                                          'Enable_backup_copy':True,
                                          'sla_hours':'5',
                                          'sla_minutes':'20'}

            database_options (dictionary) : dictionary containing values for databse parameters
                Eg. - database_options = {'sla_hours':'5',
                                          'sla_minutes':'20'}

            sec_copy_name (string): Name of the secondary copy

            kwargs**
                guided (bool) : set to true if creating plan from guided setup
                selective (string) : selective copy type for secondary copy
                regions (string) : regions for mult-region enabled copy
                specify_date (bool) : When set to 'True' it sets todays date in jobs on or after
                service_commcells (list) : list of service commcells, To select all => ["All"]


        Returns:
            None

        Raises:
            Exception:
                -- if fails to create the plan
        """

        if not kwargs.get("guided"):
            # self.__click_create_plan_button()
            self.__table.access_toolbar_menu(self.__admin_console.props['label.createProfile'])
            self.__table.access_menu_from_dropdown(self.__admin_console.props['label.backup'])
            self.__admin_console.wait_for_completion()

        self.__set_plan_name(plan_name)
        self.__admin_console.click_button(value="Next")
        # self.__click_server_plan_next_button()

        self.__admin_console.click_button("Add copy")

        if kwargs.get("service_commcells"): # Creating global plan
            for tag_name, tag_value in storage.items():
                self.__rtags.add_tag(tag_name, tag_value)
        else:
            self.__rdropdown.select_drop_down_values(values=[storage['pri_storage']], drop_down_id='storageDropdown')

        if storage.get('pri_ret_period'):
            if storage['pri_ret_period'] == 'Infinite':
                self.__set_retention_unit(storage['ret_unit'])
            else:
                self.__set_retention_period(storage['pri_ret_period'])
                if storage.get('ret_unit', None):
                    self.__set_retention_unit(storage['ret_unit'])
        # self.__click_server_plan_save_button()
        self.__admin_console.click_button(value="Save")

        if storage.get('pri_storage_type') and storage['pri_storage_type'] == 'Archive':
            self.__admin_console.click_button(value="Yes")

        if storage.get('sec_storage', None):
            self.__admin_console.click_button('Add copy')
            self.__admin_console.fill_form_by_id("backupDestinationName", sec_copy_name)
            self.__rdropdown.select_drop_down_values(
                values=[storage['sec_storage']], drop_down_id='storageDropdown')

            if storage['sec_ret_period']:
                if storage['sec_ret_period'] == 'Infinite':
                    self.__set_retention_unit(storage['ret_unit'])
                else:
                    self.__set_retention_period(storage['sec_ret_period'])
                    if storage.get('ret_unit', None):
                        self.__set_retention_unit(storage['ret_unit'])
            # For selective copy type selection
            if kwargs.get("selective"):
                self.__rdropdown.select_drop_down_values(
                    values=[kwargs['selective']], drop_down_id='backupsToCopy')

            # self.__click_server_plan_save_button()
            self.__admin_console.click_button(value="Save")

        if storage.get('snap_pri_storage', None):
            self.__admin_console.click_button('Add Snap copy')
            self.__rdropdown.select_drop_down_values(
                values=[storage['snap_pri_storage']], drop_down_id='storageDropdown')

            if snapshot_options:
                # self.__expand_sub_panel('Snapshot options')
                # self.__admin_console.wait_for_completion()
                if snapshot_options.get('snap_recovery_points', None):
                    self.__admin_console.select_radio(id="SNAP_RECOVERY_POINTS")
                    if self.__admin_console.check_if_entity_exists("id", "numOfSnapRecoveryPoints"):
                        self.__admin_console.fill_form_by_id("numOfSnapRecoveryPoints",
                                                             snapshot_options['snap_recovery_points'])

            self.__admin_console.click_button(value="Save")

        # To enable multi-region and select region
        if kwargs.get("regions"):
            self.__admin_console.click_by_id('multiRegion')
            self.__rdropdown.select_drop_down_values(
                values=[kwargs['regions'][0]], drop_down_id='regionDropdown_0')

            if kwargs.get("modify_ret"):
                self.__modify_server_plan_copy_retention(sec_copy_name,
                                                         storage['ter_ret_period'],
                                                         storage['ret_unit'])

            if kwargs.get("specify_date"):
                current_time = datetime.now()
                date = {'year': current_time.year,
                        'month': str(current_time.strftime("%B")),
                        'day': current_time.day}
                self.__specify_date_backups_on_or_after(sec_copy_name, date)

            # For second region in multi-region
            if kwargs['regions'][1]:
                self.__rwizard.click_button(
                    'Add destinations for another region')
                self.__rdropdown.select_drop_down_values(
                    values=[kwargs['regions'][1]], drop_down_id='regionDropdown_1')
                self.__admin_console.click_by_xpath(
                    "(//button[contains(@class, 'MuiButton-root')]//div[text()='Add copy'])[2]")
                self.__rdropdown.select_drop_down_values(
                    values=[storage['ter_storage']], drop_down_id='storageDropdown')
                self.__rpanel.click_button("Save") #rwizard click button method does not work here

        self.__rwizard.click_next()

        if isinstance(rpo, list):
            while self.__rpo.get_schedules(get_synth_full=False):
                self.__rpo.delete_schedule(1) # remove existing schedules except synthetic full

            for schedule_prop in rpo:
                self.__rpo.create_schedule(schedule_prop) # Add new schedules

        if backup_window:
            self.log.info("Setting up back up window...")
            self.__rpo.click_on_edit_backup_window()
            self.__backup_window.edit_blackout_window(backup_window)
            self.__dialog.click_submit()

        if full_backup_window:
            self.log.info("Setting up full back up window...")
            self.__rpo.click_on_edit_full_backup_window()
            self.__backup_window.edit_blackout_window(full_backup_window)
            self.__dialog.click_submit()

        # self.__click_server_plan_next_button()
        self.__admin_console.click_button(value="Next")

        if backup_data:
            self.__expand_sub_panel('Folders to backup')
            self.__admin_console.wait_for_completion()

            for value in backup_data['file_system']:
                self.__select_file_system_tab(value)
                self.__admin_console.wait_for_completion()
                time.sleep(2)

                self.backup_content_selection(
                    backup_data.get('content_backup', None),
                    backup_data.get('content_library', None),
                    backup_data.get('custom_content', None))

                if backup_data['exclude_folder'] or backup_data['exclude_folder_library'] or backup_data[
                    'exclude_folder_custom_content']:
                    self.exclusion_content_selection(
                        backup_data.get('exclude_folder', None),
                        backup_data.get('exclude_folder_library', None),
                        backup_data.get('exclude_folder_custom_content', None))

                if value == "Windows":
                    if system_state:
                        self.__admin_console.checkbox_select('backupSystemState')

                        if full_backup:
                            self.__admin_console.checkbox_select('backupSystemStateforFullBkpOnly')
                        else:
                            self.__admin_console.checkbox_deselect('backupSystemStateforFullBkpOnly')

                        if vss:
                            self.__admin_console.checkbox_select('useVSSForSystemState')
                        else:
                            self.__admin_console.checkbox_deselect('useVSSForSystemState')
                    else:
                        self.__admin_console.checkbox_deselect('backupSystemState')

        # self.__click_server_plan_next_button()
        # self.__admin_console.click_button(value="Next") # currently, backup content is removed from UI

        if snapshot_options:
            # self.__expand_sub_panel('Snapshot options')
            # self.__admin_console.wait_for_completion()

            if snapshot_options.get('Enable_backup_copy', None):
                if snapshot_options['Enable_backup_copy'] == 'OFF':
                    self.__admin_console.click_by_id('toggleBackupCopy')

            if snapshot_options.get('sla_hours', None):
                self.__set_sla_hours(snapshot_options['sla_hours'])

            if snapshot_options.get('sla_minutes', None):
                self.__set_sla_minutes(snapshot_options['sla_minutes'])

        if storage.get('snap_pri_storage'):
            self.__wizard.select_radio_button('Backup copy snap jobs based on retention set on snap copy')

        if database_options:
            self.__expand_sub_panel('Database options')
            self.__admin_console.wait_for_completion()

            if database_options.get('sla_hours', None):
                self.__set_sla_hours(database_options['sla_hours'])

            if database_options.get('sla_minutes', None):
                self.__set_sla_minutes(database_options['sla_minutes'])

        if allow_override:
            self.__expand_sub_panel(self.__admin_console.props['label.overrideRestrictions'])
            self.__admin_console.wait_for_completion()
            self.__enable_allow_override()
            self.__admin_console.wait_for_completion()
            self.set_override_options(allow_override)

        if service_commcells := kwargs.get("service_commcells"):
            if self.__wizard.get_active_step() != 'Service CommCells':
                self.__wizard.click_next()
            self.__admin_console.wait_for_completion()
            self.__wizard.drop_down.select_drop_down_values(values=service_commcells, drop_down_id="GlobConfigInfoCommCellId")

        # self.__click_server_plan_next_button()
        self.__admin_console.click_button(value="Submit")
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def create_ibmi_vtl_plan(self,
                             plan_name: str,
                             vtl_library: str,
                             retention: dict = None,
                             rpo_details=None
                             ):
        """create IBMi VTL plan by entering necessary data
        Args:

            plan_name (string)      : Name of the plan to be created

            vtl_library (string)    : Name of the Tape library

            rpo_details (dict)      : rpo details
                example:-
                rpo_details = {
                                'inc_frequency' : {'Frequency': '1', 'FrequencyUnit': 'Day(s)','StartTime': '10:30 pm'},
                                'full_frequency' : {
                                    'FullFrequency': 'Daily' / 'Weekly' / 'Monthly' / "Yearly",
                                    'FullStartTime': '11:30 pm',
                                    'FullStartEvery': 'Monday' / 'Tuesday'/ 'Wednesday'/ 'Thursday'/ 'Friday'/
                                                        'Saturday'/ 'Sunday',
                                    'FullStartWeek' : 'First' / 'Second' / 'Third' / 'Fourth' / 'Last',
                                    'FullStartMonth':  'January' / <Any one month of the year>},
                                'inc_window' :{'Monday and Thursday' : ['All day'],
                                    'Tuesday' : ['2am-6am', '1pm-6pm'],
                                    'Tuesday through Thursday' : ['9pm-12am'],
                                    'Wednesday' : ['5am-2pm'],
                                    'Friday' : ['1am-3am', '5am-1pm'],
                                    'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am'],
                                    'Sunday' : ['1am-5am', '7am-1pm', '7pm-11pm']},
                                'full_window' :{'Monday and Thursday' : ['All day'],
                                    'Tuesday' : ['2am-6am', '1pm-6pm'],
                                    'Tuesday through Thursday' : ['9pm-12am'],
                                    'Wednesday' : ['5am-2pm'],
                                    'Friday' : ['1am-3am', '5am-1pm'],
                                    'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am'],
                                    'Sunday' : ['1am-5am', '7am-1pm', '7pm-11pm']}
                                }

            retention(dict)         : retention details
                example:-
                retention = {'value': '5',
                            'unit': 'Day(s)'}

        """
        self.__table.access_toolbar_menu(self.__admin_console.props['label.createProfile'])
        self.__table.access_menu_from_dropdown('IBM i VTL')
        self.__rwizard.fill_text_in_field(label='Plan name', text=plan_name)
        self.__rwizard.click_next()
        self.__rwizard.click_button(name=self.__admin_console.props['action.add'])
        self.__rdropdown.select_drop_down_values(values=[vtl_library], drop_down_id='storageDropdown')

        if retention:
            if retention['unit'] == 'Infinite':
                self.__set_retention_unit(retention['unit'])
            else:
                self.__set_retention_period(retention['value'])
                if retention.get('unit', None):
                    self.__set_retention_unit(retention['unit'])

        self.__dialog.click_submit()
        self.__rwizard.click_next()

        if rpo_details:
            if 'inc_frequency' in rpo_details.keys():
                self.__rpo.click_on_edit_ibmi_inc_backup_frequency()
                self.__rpo.fill_ibmi_backup_frequency(rpo_details['inc_frequency'])

            if 'full_frequency' in rpo_details.keys():
                self.__rpo.click_on_edit_ibmi_full_backup_frequency()
                # self.__admin_console.wait_for_completion()
                self.__rpo.fill_ibmi_backup_frequency(rpo_details['full_frequency'])

            if rpo_details['inc_window']:
                self.__rpo.click_on_edit_ibmi_backup_window()
                self.__backup_window.edit_blackout_window(rpo_details['inc_window'])
                self.__dialog.click_submit()

            if rpo_details['full_window']:
                self.__rpo.click_on_edit_ibmi_full_backup_window()
                self.__backup_window.edit_blackout_window(rpo_details['full_window'])
                self.__dialog.click_submit()

        self.__rwizard.click_submit()

    @PageService()
    def create_laptop_plan(
            self,
            plan_name,
            allowed_features=None,
            media_agent=None,
            archiving_rules=None,
            backup_data=None,
            file_system_quota=None,
            storage=None,
            rpo_hours=None,
            retention=None,
            throttle_send=None,
            throttle_receive=None,
            alerts=None,
            allow_override=None,
            from_plans_page=True):
        """
        Method to create Laptop plan

        Args:

            plan_name (string): Name of the plan to be created

            rpo_hours (string): RPO Hours value

            allowed_features (dictionary): dictionary containing features to be enabled for the
                             plan and corresponding attributes
                Eg. - allowed_features = {'Edge Drive': 'ON',
                                          'audit_drive_operations': True,
                                          'notification_for_shares': True,
                                          'edge_drive_quota':'200',
                                          'DLP': 'ON',
                                          'Archiving': 'ON'}

            media_agent (string)    :   media agent to be used to configure edge drive for plan

            archiving_rules (dictionary): dictionary containing values for Archive Feature rules
                Eg. - archiving_rules = {"do_edit": True, "start_clean": "40", "stop_clean": "90",
                                        "file_access_time": "85", "file_modify_time": None,
                                        "file_create_time": "2", "archive_file_size": None,
                                        "max_file_size": None, "archive_read_only": True,
                                        "replace_file": None, "delete_file": None}

            backup_data (dictionary) : Dictionary containing multiple lists with values for back
                up content to be selected and excluded while creating the plan
                Eg. - backup_data = {'file_system':["Mac", "Unix", "Windows"],
                                    'content_backup':["Content Library"],
                                    'content_library':['Content Library', 'GoogleDrive'],
                                    'custom_content':None,
                                    'exclude_folder':['Content Library', 'Documents'],
                                    'exclude_folder_library':['DropBox', 'EdgeDrive', 'Executable']
                                    'exclude_folder_custom_content':None
                                   }

            file_system_quota (string): Variable containing value for File system quota

            storage (dict) : Dict containing storage attributes for admin console
                Eg. - self._storage = {'pri_storage': None,
                         'pri_ret_period':'30',
                         'sec_storage': None,
                         'sec_ret_period':'45',
                         'ret_unit':'day(s)'}

            throttle_send (string ot integer): Network Resource send parameter value

            throttle_receive (string or integer): Network Resource receive parameter value

            alerts (dictionary): Dictionary with values for determining whether alerts should
                be Enabled/Disabled
                Eg. - alerts = {"Backup" : "No backup for last 4 days",
                                "Jobfail": "Restore Job failed",
                                "edge_drive_quota":"Edge drive quota alert",
                                "edge_drive_operations":"Edge drive/share operations alert"}

            allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override optional",
                                        "Folders_to_backup": "Override not allowed"}

            retention (dict) : dictionary containing retention attributes for laptop plan
                Eg. - retention = {'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                                   'file_version_retention': {'duration': {'value': '4',
                                                                          'unit': 'day(s)'},
                                                              'versions': '5',
                                                              'rules': {'days': '4',
                                                                        'weeks': '5',
                                                                        'months': '6'}}}
                    OR
                        retention = {'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                                       'file_version_retention': {'duration': None,
                                                                  'versions': None,
                                                                  'rules': {'days': '4',
                                                                            'weeks': '5',
                                                                            'months': '6'}}}

            from_plans_page (bool) : To check if currently in Manage > Plans page (default: True)

        Returns:
            None

        Raises:
            Exception:
                -- if fails to create the plan
        """

        self.__table.access_toolbar_menu(self.__admin_console.props
                                         ['label.createProfile'])
        if from_plans_page:
            self.__table.access_menu_from_dropdown('Laptop')
        self.__admin_console.wait_for_completion()
        self.__rwizard.fill_text_in_field(label='Plan name', text=plan_name)
        self.__rwizard.click_next()

        if allowed_features:
            # Edge Drive and Archiving features have been removed now
            if allowed_features.get("DLP", None):
                if allowed_features["DLP"] == "ON":
                    self.log.info("Enabling DLP for the plan")
                    self.__checkbox.check(id='dlp')
                else:
                    self.__checkbox.uncheck(id='dlp')
        self.__rwizard.click_next()

        if backup_data:
            for value in backup_data['file_system']:
                self.__rbackup_content.select_file_system(value)
                self.backup_content_selection(
                    backup_data.get('content_backup', None),
                    backup_data.get('custom_content', None))

                self.exclusion_content_selection(
                    backup_data.get('exclude_folder', None),
                    backup_data.get('exclude_folder_custom_content', None))

        if file_system_quota:
            self.__checkbox.check('Enable file system quota')
            self.__wizard.fill_text_in_field(
                id="fileSystemQuota", text=file_system_quota)

        self.__rwizard.click_next()

        if storage.get('pri_storage', None):
            self.__rdropdown.select_drop_down_values(
                values=[storage['pri_storage']], drop_down_id='primarystorage')
        if storage.get('sec_storage', None):
            self.__enable_secondary_storage()
            self.__admin_console.wait_for_completion()
            self.__rdropdown.select_drop_down_values(
                values=[storage['sec_storage']], drop_down_id=
                'secondarystorage')
        if rpo_hours:
            self.__wizard.fill_text_in_field(
                id="backupFrequency", text=rpo_hours)

        self.__rwizard.click_next()

        self.set_retention(retention)
        self.__rwizard.click_next()
        self.set_network_resources(throttle_send, throttle_receive)
        self.set_alerts(alerts)
        self.__rwizard.click_next()
        self.__rwizard.click_button(name='Submit')
        self.__admin_console.check_error_message()

    @PageService()
    def is_plan_exists(self, plan_name):
        """ check plan entry existence from Plans page
        Args:
                plan_name     (str) -- Plan Name

        returns: boolean
            True: if plan exists
            false: if plan does not exist
        """
        self.__navigator.navigate_to_plan()
        status = self.__table.is_entity_present_in_column(column_name='Plan name',
                                                          entity_name=plan_name)
        self.__table.clear_search()
        return status

    @PageService(react_frame=True)
    def delete_plan(self, plan_name: str, company: str = None, wait: bool = True, raise_error: bool = True):
        """
        Method to delete an existing plan

        Args:
            plan_name (str): Name of the plan to be deleted
            company (str)   : name of the company plan belongs to

        Raises:
            Exception:
                -- if fails to delete plan
        """
        self.__navigator.navigate_to_plan()
        if company:
            self.__navigator.switch_company_as_operator(company)
        self.__table.access_action_item(plan_name, "Delete")
        self.__dialog.type_text_and_delete("DELETE", wait=wait)
        notification_text = self.__admin_console.get_notification(wait_time=5)
        self.__admin_console.check_error_message(raise_error=raise_error)
        self.__alerts.close_popup()
        self.__table.clear_search()
        if company:
            self.__navigator.switch_company_as_operator("Reset")
        return notification_text

    @PageService()
    def create_derived_server_plan(self, base_plan: str, derived_plan_name: str, storage=None, rpo_hours=None):
        """Method to derive a server plan

        Args:
            base_plan           (str)   :   Base Plan Name
            derived_plan_name   (str)   :   Derived Plan Name
            storage             (dict)  :   if storage values are passed, storage would be overriden
            rpo_hours           (dict)  :   if rpo values are passed, rpo would be overriden
        """
        self.__navigator.navigate_to_plan()
        self.select_plan(base_plan)
        self.__admin_console.wait_for_completion()
        self.__click_create_derived_plan_button()
        self.__admin_console.wait_for_completion()
        self.__set_plan_name(derived_plan_name)
        self.__click_server_plan_next_button()

        if storage:
            self.__rwizard.toggle.disable(id= 'override-setting-toggle-storage')
            # TODO: IMPLEMENT OVERRIDE CONDITIONS
        self.__click_server_plan_next_button()

        if rpo_hours:
            self.__rwizard.toggle.disable(id= 'override-setting-toggle-rpo')
            # TODO: IMPLEMENT OVERRIDE CONDITIONS
        self.__click_server_plan_next_button()

        # TODO: HANDLE SNAPSHOT / DATABASE OPTIONS
        self.__admin_console.click_button(value="Submit")
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def create_laptop_derived_plan(self,
                                   derived_plan,
                                   allow_override=None,
                                   backup_data=None,
                                   storage=None,
                                   rpo_hours=None,
                                   retention=None):
        """
        Method to create Laptop derived plan

        Args:

            derived_plan (string): Name of the derived plan to be created

           allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override optional"}

            backup_data (dictionary) : Dictionary containing multiple lists with values for back
                up content to be selected and excluded while creating the plan
                Eg. - backup_data = {'file_system':["Mac", "Unix", "Windows"],
                                    'content_backup':["Content Library"],
                                    'content_library':['Content Library', 'GoogleDrive'],
                                    'custom_content':None,
                                    'exclude_folder':['Content Library', 'Documents'],
                                    'exclude_folder_library':['DropBox', 'EdgeDrive', 'Executable']
                                    'exclude_folder_custom_content':None
                                   }

            storage (dict) : Dict containing storage attributes for admin console
                Eg. - self._storage = {'pri_storage': None,
                         'pri_ret_period':'30',
                         'sec_storage': None,
                         'sec_ret_period':'45',
                         'ret_unit':'day(s)'}

            rpo_hours (string): RPO Hours value

            retention (dict) : dictionary containing retention attributes for laptop plan
                Eg. - retention = {'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                                   'file_version_retention': {'duration': {'value': '4',
                                                                          'unit': 'day(s)'},
                                                              'versions': '5',
                                                              'rules': {'days': '4',
                                                                        'weeks': '5',
                                                                        'months': '6'}}}
                    OR
                        retention = {'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                                       'file_version_retention': {'duration': None,
                                                                  'versions': None,
                                                                  'rules': {'days': '4',
                                                                            'weeks': '5',
                                                                            'months': '6'}}}

        Returns:
            None

        Raises:
            Exception:
                -- if fails to create the plan

        """

        self.__rwizard.fill_text_in_field(label='Plan name', text=derived_plan)
        self.__rwizard.click_next()
        self.__rwizard.click_next()
        if backup_data:
            if allow_override['Folders_to_backup'] == "Override optional":
                self.__select_override_backup_content()
            for value in backup_data['file_system']:
                self.__rbackup_content.select_file_system(value)
                self.backup_content_selection(
                    backup_data.get('content_backup', None),
                    backup_data.get('custom_content', None))

                self.exclusion_content_selection(
                    backup_data.get('exclude_folder', None),
                    backup_data.get('exclude_folder_custom_content', None))
        self.__rwizard.click_next()
        if storage:
            if allow_override['Storage_pool'] == "Override optional":
                self.__select_override_storage()
            self.__rdropdown.select_drop_down_values(values=[storage['pri_storage']], drop_down_id='primarystorage')
        if rpo_hours:
            if allow_override['RPO'] == "Override optional":
                self.__select_override_rpo()
            self.__admin_console.fill_form_by_id("backupFrequency", rpo_hours)
        self.__rwizard.click_next()
        if retention:
            if allow_override['Retention'] == "Override optional":
                self.__select_override_retention()
            self.set_retention(retention)
        self.__rwizard.click_next()
        self.__rwizard.click_next()
        self.__rwizard.click_button(name='Submit')
        self.__admin_console.check_error_message()
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_archive_plan(
            self,
            plan_name,
            storage,
            rpo=None,
            archive_day=None,
            archive_duration=None,
            archiving_rules=None,
            allow_override=None,
            delete_files=False):
        """
        Method to create Archival plan

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

            archive_day (dictionary): dictionary containing values of backup days for backup
                window
                Eg. - archive_day = dict.fromkeys(['1', '2', '3'], 1)

            archive_duration (dictionary): dictionary containing values of excluded backup
                time for backup window
                Eg. - archive_duration = dict.fromkeys(['2', '3', '4', '5'], 1)

            archiving_rules (dictionary):   dictionary containing values of diskcleanup/archiving rules
                Eg. -   archiving_rules = {
                "last_accessed_unit":   "days",
                "last_accessed": 2,
                "last_modified_unit": "hours",
                "last_modified": 3,
                "file_size": 20,
                "file_size_unit": "KB"
                }

            allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override optional"}

        """
        self.__admin_console.click_button("Create plan")

        self.__click_plan_type("Archive")
        self.__admin_console.wait_for_completion()
        self.__admin_console.unswitch_to_react_frame()

        self.__admin_console.select_hyperlink("Add")

        self.__drop_down.select_drop_down_values(0, [storage['pri_storage']])

        if storage['pri_ret_period']:
            if storage['pri_ret_period'] != 'Infinite':
                self.__set_retention_unit(storage['ret_unit'])
                self.__set_retention_period(storage['pri_ret_period'])
        self.__admin_console.submit_form()

        self.__set_plan_name(plan_name)

        if rpo:
            if rpo['archive_frequency']:
                self.__admin_console.fill_form_by_id("rpo", rpo['archive_frequency'])
            if rpo['archive_frequency_unit']:
                self.__select_archive_frequency_unit(rpo['archive_frequency_unit'])

        if archive_day and archive_duration:
            self.__open_edit_backup_window_dialog()
            self.__admin_console.wait_for_completion()
            self.__set_backup_window(archive_day, archive_duration)

        if archiving_rules:

            if archiving_rules['last_accessed'] is not None:
                self.__select_access_time_rule()
                self.__admin_console.fill_form_by_id("accessedAgo", archiving_rules['last_accessed'])

            if archiving_rules['last_accessed_unit']:
                self.__select_last_accessed_unit(archiving_rules['last_accessed_unit'])

            if archiving_rules['last_modified'] is not None:
                self.__select_modify_time_rule()
                self.__admin_console.fill_form_by_id("accessedAgo", archiving_rules['last_modified'])

            if archiving_rules['last_modified_unit']:
                self.__select_last_modified_unit(archiving_rules['last_modified_unit'])

            if archiving_rules['file_size'] is not None:
                self.__admin_console.fill_form_by_id("size", archiving_rules['file_size'])

            if archiving_rules['file_size_unit']:
                self.__select_file_size_unit(archiving_rules['file_size_unit'])

        if delete_files:
            self.__admin_console.select_radio(id="deleteTheFile")
            self.__admin_console.wait_for_completion()

        if allow_override:
            self.__expand_sub_panel(self.__admin_console.props['label.overrideRestrictions'])
            self.__admin_console.wait_for_completion()
            self.__enable_allow_override()
            self.__admin_console.wait_for_completion()
            self.set_override_options(allow_override)

        self.__driver.find_element(By.XPATH, "//*[@id='archivalPlanTemplate_button_#4019']").click()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService(react_frame=True)
    def create_office365_plan(
            self,
            plan_name,
            retention=None,
            backup_archive_mailbox=False,
            set_content_search=False,
            generate_previews=False,
            set_entity_search=False,
            backup_all_versions=True,
            onedrive_filters=None):
        """
        Method to create Office365 Plan

        Args:
            plan_name (str):                Name of the plan

            retention (dict):               How long the backed up data should be retained
                                            Eg: retention = {'ret_period': '365',
                                                             'ret_unit': 'day(s)'}

            backup_archive_mailbox (bool):  Whether or not archive mailbox has to be backed up

            set_content_search (bool):      Whether or not Content Search has to be enabled

            generate_previews (bool):       Whether or not Pre-generate previews has to be enabled

            set_entity_search (bool):       Whether or not Entity Search has to be enabled

            backup_all_versions (bool):     Whether or not all versions have to be backed up

            onedrive_filters (dict):        Filters that have to be applied
                                            Eg: filters = {'include_folders': ['test_folder'],
                                                           'include_files': ['*.log', 'test_file.txt']}
                                            Eg: filters = {'exclude_folders': ['test_folder'],
                                                           'exclude_files': ['*.log', 'test_file.txt']}

        """
        self.__table.access_toolbar_menu(self.__admin_console.props['label.createProfile'])
        self.__table.access_menu_from_dropdown('Office 365')
        self.__admin_console.unswitch_to_react_frame()
        self.__admin_console.wait_for_completion()
        self.__set_plan_name(plan_name)
        self.__wizard.click_next()

        if backup_archive_mailbox:
            self.__admin_console.enable_toggle(index=1, cv_toggle=True)
        self.__wizard.click_next()
        if retention:
            if retention['ret_period'] != 'Infinite':
                self.__select_radio_by_id('retainBasedOnDeletionTime')
                self.__set_office365_retention_period(retention['ret_period'])
                if retention.get('ret_unit', None):
                    self.__admin_console.select_value_from_dropdown(
                        select_id='cvTimeRelativePicker_isteven-multi-select_#6209',
                        value=retention['ret_unit'])

        if set_content_search:
            self.__admin_console.enable_toggle(index=2, cv_toggle=True)
            if generate_previews:
                self.__admin_console.enable_toggle(index=3, cv_toggle=True)
            if set_entity_search:
                self.__admin_console.enable_toggle(index=4, cv_toggle=True)
        elif set_entity_search:
            self.__admin_console.enable_toggle(index=3, cv_toggle=True)
        self.__wizard.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

        if not backup_all_versions:
            self.__admin_console.disable_toggle(index=5, cv_toggle=True)
            self.__admin_console.disable_toggle(index=6, cv_toggle=True)

        if onedrive_filters:
            self.__click_edit_onedrive_filters()
            self.__admin_console.wait_for_completion()

            if onedrive_filters.get('include_folders', None):
                for item in onedrive_filters['include_folders']:
                    self.__add_include_folder_filter(item)

            if onedrive_filters.get('exclude_folders', None):
                self.__define_exclusions()
                for item in onedrive_filters['exclude_folders']:
                    self.__add_exclude_folder_filter(item)

            if onedrive_filters.get('include_files', None):
                self.__click_file_filters_tab()
                for item in onedrive_filters['include_files']:
                    self.__add_include_file_filter(item)

            if onedrive_filters.get('exclude_files', None):
                self.__click_file_filters_tab()
                self.__define_exclusions()
                for item in onedrive_filters['exclude_files']:
                    self.__add_exclude_file_filter(item)

            self.__admin_console.click_button(self.__admin_console.props['label.submit'])
            if self.__admin_console.check_if_entity_exists("xpath", "//h4[contains(text(),'filters')]"):
                self.__driver.find_element(By.XPATH, "//div[contains(text(),'Yes')]").click()
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()

    @PageService()
    def create_dynamics365_plan(self, plan_name, retention=None):
        """
            Method to create a Dynamics 365 Plan

            Arguments:
                plan_name           (str):      Name of the Dynamics 365 plan
                retention           (dict):     How long the retention for the plan is to be set
                    Default:
                        infinite
                    Format:
                                {'ret_period': '365',
                                'ret_unit': 'day(s)'}
                        'ret_unit'
                            Allowed values:
                                'day(s)' , 'month(s), year(s)
                    'ret_period':   (int):      Retain for that many number of unit time period

        """
        self.__table.access_toolbar_menu(self.__admin_console.props['label.createProfile'])
        self.__table.access_menu_from_dropdown(self.__admin_console.props['label.dynamics365'])
        self.__admin_console.wait_for_completion()
        self.__set_plan_name(plan_name)
        self.__wizard.click_next()
        if retention:
            if retention['ret_period'] != 'Infinite':
                self.__select_radio_by_id('deletionBasedRetention')
                self.__set_dynamics365_retention_period(retention['ret_period'])
        self.__wizard.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def getting_started_create_sdg_plan(self, plan, index_server,
                                        content_analyzer, entities_list):
        """
                Method to create sensitive data governance plan from getting started page
                Args:
                    plan (str):                Name of the plan

                    index_server (str):        Name of the index server to be used

                    content_analyzer(str):     Name of the content analyzer to be used

                    entities_list(list):       List of entities to be analyzed
        """
        self.log.info("Creating sensitive data governance plan. Filling plan name")
        self.__admin_console.fill_form_by_id("planName", plan)
        self.log.info("Selecting Index Server")
        self.__drop_down.select_drop_down_values(0, [index_server])
        self.log.info("Selecting content analyzer")
        self.__drop_down.select_drop_down_values(1, [content_analyzer])
        self._select_entities(entities_list)
        self.log.info("Moving to next section")
        self.__admin_console.button_next()
        self.log.info("Submitted the form for creating SDG plan")
        self.__admin_console.submit_form()

    @PageService()
    def associate_to_company(self, plan, company):
        """
        method to associate plan to a company
        Args:
            plan(str) : Name of the plan

            company(list) : Name of the company to be assoicated
        """
        self.__table.access_action_item(plan, "Associate to company")
        self.__table.access_toolbar_menu('Add company')

        self.__temp_table = Rtable(self.__admin_console, id="associateCompaniesToPlan")

        self.__temp_table.search_for(company)
        self.__temp_table.select_rows(names=company, partial_selection=False)
        self.__dialog.click_submit()

    @PageService()
    def disassociate_from_company(self, plan: str, company: str) -> None:
        """
            Method to disassociate plan from a company

            Args:
                plan (str)      :   Plan name
                company (str)   :   Company name
        """
        self.__table.access_action_item(plan, "Associate to company")
        self.__admin_console.wait_for_completion()
        self.__table.access_action_item(company, "Remove association")
        self.__dialog.click_submit()

    @PageService()
    def get_plans_with_tag(self, tag_marker: str) -> list:
        """
            Method to get list of plan names that matches specified tag marker

            Args:
                tag_marker (str)    :   Tag string
        """
        self.__table.apply_filter_over_column('Tags', tag_marker)
        return self.__table.get_column_data('Plan name')

    @PageService()
    def search_for(self, search_string: str) -> list:
        """
        Method to search a string in the search bar and return all the plans listed
        Args:
            search_string(str): string to search for

        returns:
            list : list of plans matching the string
        """
        self.__table.search_for(search_string)
        res = self.__table.get_column_data(column_name='Plan name')
        return res


class RPO:
    """ Class for the RPO Management """

    def __init__(self, admin_console: AdminConsole):
        """
        Method to initiate RPO class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.__dialog = RModalDialog(self.__admin_console)
        self.__drop_down = RDropDown(self.__admin_console)

        # panel or wizard
        self.__base_xpath = "(//*[contains(@class, 'rpo-tile')]/ancestor::div[contains(@class, 'MuiCardContent')] | //*[@id='rpoForm'])"
        self.__base_ibmi_xpath = "//*[contains(@class, 'form-content')]"
        self.__backup_schedules_xpath = "//*[contains(@class, 'backup-freq')]//div[contains(@class, 'schedule')]"

        # supported values from command center
        self.__frequency_units = ['Minute(s)', 'Hour(s)', 'Day(s)', 'Week(s)', 'Month(s)', 'Year']
        self.__backup_types = ['Differential', 'Full', 'Incremental']
        self.__agents = ['All agents', 'Databases']

        self.__toggle = Toggle(self.__admin_console)
        self.__checkbox = Checkbox(self.__admin_console)
        self.__dropdown = self.__dialog._dropdown
        self.__rpanel_info = RPanelInfo(self.__admin_console, 'RPO')

    @property
    def frequency_units(self):
        """Returns supported frequency types"""
        return self.__frequency_units

    @property
    def backup_types(self):
        """Returns supported backup types"""
        return self.__backup_types

    @property
    def agents(self):
        """Returns supported agents"""
        return self.__agents

    @WebAction()
    def __click_on_add(self):
        """Method to click on ADD schedule button"""
        self.__driver.find_element(By.XPATH,
            f"{self.__base_xpath}//button[contains(.,'Add')]"
        ).click()

    @WebAction()
    def __click_on_edit(self, index: int = None, label: str = None):
        """Method to click on EDIT schedule button

        Args:
            index (int) : Index of schedule to be edited (Starting from 1)

            label (str): label for schedule to edit (partial string is also supported)
        """
        edit_xpath = f"({self.__backup_schedules_xpath})[{index}]//button[@title='Edit']"
        if label:
            edit_xpath = f"{self.__backup_schedules_xpath}//*[contains(text(), '{label}')]/ancestor"\
                    f"::div[contains(@class, 'schedule')]//button[@title='Edit']"
        self.__driver.find_element(By.XPATH, edit_xpath).click()

    @WebAction()
    def __click_on_delete(self, index):
        """Method to click on delete buttonschedule

        Args:
            index (int) : Index of schedule to be deleted (Starting from 1)
        """
        delete_btn_xpath = f"({self.__backup_schedules_xpath}//button[@title='Delete'])[{index}]"
        self.__driver.find_element(By.XPATH, delete_btn_xpath).click()

    @WebAction()
    def __select_backup_type(self, backup_type):
        """Method to select backup type

        Args:
            backup_type (str)   :   Backup type for the schedule
        """
        self.__dialog.select_dropdown_values(drop_down_id= 'backupLevelDropdown', values= [backup_type])

    @WebAction()
    def __select_agent(self, agent_name):
        """Method to select agent type

        Args:
            agent_name (str)   :   Agent name for the schedule
        """
        self.__dialog.select_dropdown_values(drop_down_id= 'forDatabasesOnly', values= [agent_name])

    @WebAction()
    def __fill_rpo_frequency(self, value):
        """Method to fill RPO

        Args:
            value (int)   :   RPO value for the schedule
        """
        rpo_input = self.__driver.find_element(By.ID, 'incremantalBackup')
        rpo_input.send_keys(u'\ue009' + 'a' + u'\ue003') # CTRL + A + Backspace
        rpo_input.send_keys(value)

    @WebAction()
    def __select_rpo_frequency_unit(self, freq_unit):
        """Method to select RPO unit

        Args:
            freq_unit (str)   :   Frequency type of the schedule (minutes / hours / days)
        """
        self.__dialog.select_dropdown_values(drop_down_id= 'incremantalBackupDropdown', values= [freq_unit])

    @WebAction()
    def __select_schedule_mode(self, mode: str) -> None:
        """Method to select schedule mode

        Args:
            mode (str)   :   Continuous or Automatic
        """
        auto_disk_rules = 'enableAutoDiskRules'
        if 'automatic' in mode.lower() and not self.__toggle.is_enabled(id=auto_disk_rules):
            self.__toggle.enable(id=auto_disk_rules)
        if 'continuous' in mode.lower() and self.__toggle.is_enabled(id=auto_disk_rules):
            self.__toggle.disable(id=auto_disk_rules)

    @WebAction()
    def __fill_start_time(self, value):
        """Method to fill RPO start time

        Args:
            value (int)   :   Start time of the schedule
        """
        self.__dialog.fill_input_by_xpath(text=value, element_xpath=".//input[contains(@class, 'inputAdornedEnd')]")

    @WebAction()
    def __enable_advanced_options(self, enable: bool = True) -> None:
        """Method to enable advanced toggle"""
        self.__toggle.enable('Advanced') if enable else self.__toggle.disable('Advanced')

    @WebAction()
    def __select_time_zone(self, time_zone):
        """Method to select time_zone

        Args:
            time_zone (str)   :   Time zone
        """
        self.__dialog.select_dropdown_values(drop_down_id= 'timezoneId', values= [time_zone])

    @WebAction()
    def __enable_disk_cache(self, enable: bool = True) -> None:
        """Method to enable disk cache"""
        self.__toggle.enable(id='useDiskCacheForLogBackups') if enable else self.__toggle.disable(
            id='useDiskCacheForLogBackups')

    @WebAction()
    def __fill_commit_every_hours(self, hours: str) -> None:
        """Method to fill commit every hours"""
        self.__enable_disk_cache()
        self.__dialog.fill_text_in_field('commitHours', hours)

    @WebAction()
    def __set_force_full_backup(self, frequency: int, freq_unit: str) -> None:
        """Method to set force full backup frequency"""
        self.__enable_advanced_options()
        self.__dialog.fill_text_in_field('runFullBackupEvery', str(frequency))
        self.__dropdown.select_drop_down_values(drop_down_id='runFullBackupDropdown', values=[freq_unit])

    @WebAction()
    def __fill_data(self, values):
        """Method to fill RPO values

        Args:
            values (dict) : Schedule properties that needs to be filled

            Example: {
                'BackupType' : 'Full',
                'Agents'     : 'Databases',
                'Frequency'  : '1',
                'FrequencyUnit' : 'Day(s)',
                'StartTime'  : '10:30 pm',
                'ScheduleMode'  : 'Continuous',
                'AdvanceOptions': True,
                'ForceFullBackup' : (1, 'Week(s)'),
                'TimeZone': 'CommServe TimeZone',
                'DiskCache' :   True,
                'CommitEvery' : 24
            }
        """
        for key, value in values.items():
            if key == 'BackupType':
                self.__select_backup_type(value)
            elif key == 'Agents':
                self.__select_agent(value)
            elif key == 'Frequency':
                self.__fill_rpo_frequency(str(value))
            elif key == 'FrequencyUnit':
                self.__select_rpo_frequency_unit(value)
            elif key == 'StartTime':
                self.__fill_start_time(value)
            elif key == 'ScheduleMode':
                self.__select_schedule_mode(value)
            elif key == 'AdvanceOptions':
                self.__enable_advanced_options(value)
            elif key == 'ForceFullBackup':
                self.__set_force_full_backup(*value)
            elif key == 'TimeZone':
                self.__select_time_zone(value)
            elif key == 'DiskCache':
                self.__enable_disk_cache(value)
            elif key == 'CommitEvery':
                self.__fill_commit_every_hours(str(value))
            else:
                raise CVWebAutomationException(f"Invalid Key Passed in Input : [{key}]")

    @WebAction()
    def __read_schedules(self):
        """Method to read schedules from UI"""
        return self.__driver.find_elements(By.XPATH, self.__backup_schedules_xpath)

    @PageService()
    def create_schedule(self, values):
        """Method to create new schedule

        Args:
            values (dict) : new schedule properties
        """
        self.log.info(f'Creating schedule : {values}')
        self.__click_on_add()
        self.__fill_data(values)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_schedule(self, index: int = None, new_values: dict = {}, label: str = None):
        """Method to update existing schedule

        Args:
            index      (int)  : Index of schedule to be edited (Starting from 1)
            new_values (dict) : schedule properties that needs to be updated
                Example: {
                'BackupType' : 'Full',
                'Agents'     : 'Databases',
                'Frequency'  : '1',
                'FrequencyUnit' : 'Day(s)',
                'StartTime'  : '10:30 pm',
                'ScheduleMode'  : 'Continuous',
                'AdvanceOptions': True,
                'ForceFullBackup' : (1, 'Week(s)'),
                'TimeZone': 'CommServe TimeZone',
                'DiskCache' :   True,
                'CommitEvery' : 24
            }
            label      (str)  : label for schedule to edit (partial string is also supported)
        """
        self.log.info(f'Editing schedule at Index : [{index}] with new values => {new_values}')
        self.__click_on_edit(index, label)
        self.__fill_data(new_values)
        self.__dialog.click_button_on_dialog('Save')
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_schedule(self, index):
        """Method to delete existing schedule

        Args:
            index (int) : Index of schedule to be deleted (Starting from 1)
        """
        self.log.info(f'Deleting schedule at Index : [{index}]')
        delete_btn_xpath = f"{self.__backup_schedules_xpath}//button[@title='Delete']"

        if self.__driver.find_elements(By.XPATH, delete_btn_xpath):
            self.__click_on_delete(index)
        else:
            self.__click_on_edit(index)
            self.__dialog.click_button_on_dialog('Delete')
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def get_schedules(self, get_synth_full: bool = True) -> list:
        """Method to get list of available schedules"""
        self.log.info('Reading available schedules...')
        return [schedule.text.replace('\n', ' ') for schedule in self.__read_schedules() if 'synthetic full' not in schedule.text or get_synth_full]

    @PageService()
    def get_schedule_index(self, backup_type: str) -> list:
        """Method to get schedule index of the specified backup type"""
        schedules = self.get_schedules()
        return [i+1 for i in range(len(schedules)) if backup_type.lower() in schedules[i].lower()]

    @WebAction()
    def __populate_props(self, index: int) -> dict:
        """Method to populate schedule properties"""
        self.__click_on_edit(index)
        backup_type = self.__dropdown.get_selected_values('backupLevelDropdown', False)[0]
        agents = self.__dropdown.get_selected_values('forDatabasesOnly', False)[0]
        frequency = int(self.__driver.find_element(By.ID, 'incremantalBackup').get_attribute('value'))
        freq_unit = self.__dropdown.get_selected_values('incremantalBackupDropdown', False)[0]

        props = {
            'BackupType': backup_type,
            'Agents': agents,
            'Frequency': frequency,
            'FrequencyUnit': freq_unit,
        }

        if self.__toggle.is_exists('Advanced'):
            props['AdvanceOptions'] = self.__toggle.is_enabled('Advanced')

        start_time_xpath = "//*[contains(@id, 'startTime')]//input"
        if self.__admin_console.check_if_entity_exists('xpath', start_time_xpath):
            props['StartTime'] = self.__driver.find_element(By.XPATH, start_time_xpath).get_attribute('value')

        if self.__driver.find_elements(By.ID, 'enableAutoDiskRules'):
            is_automatic = self.__toggle.is_enabled(id='enableAutoDiskRules')
            props['ScheduleMode'] = 'Based on automatic schedule settings' if is_automatic else 'Continuous'

        if self.__toggle.is_exists(id='useDiskCacheForLogBackups'):
            props['DiskCache'] = self.__toggle.is_enabled(id='useDiskCacheForLogBackups')
        if props.get('DiskCache'):
            props['CommitEvery'] = int(self.__driver.find_element(By.ID, 'commitHours').get_attribute('value'))

        if not props.get('AdvanceOptions'):
            self.__dialog.click_cancel()
            return props

        ### ADVANCED OPTIONS ###
        if self.__admin_console.check_if_entity_exists('id', 'timezoneId'):
            props['TimeZone'] = self.__dropdown.get_selected_values('timezoneId', False)[0]

        if self.__admin_console.check_if_entity_exists('id', 'runFullBackupEvery'):
            freq = int(self.__driver.find_element(By.ID, 'runFullBackupEvery').get_attribute('value'))
            unit = self.__dropdown.get_selected_values('runFullBackupDropdown', False)[0]
            props['ForceFullBackup'] = (freq, unit)

        self.__dialog.click_cancel()
        return props

    @PageService()
    def get_schedule_prop(self, index: int) -> dict:
        """Method to schedule properties"""
        return self.__populate_props(index)

    @WebAction()
    def __click_on_edit_window(self, window_name: str) -> None:
        """Method to click on edit backup window"""
        edit_button = f"{self.__base_xpath}//*[text()='{window_name}']//ancestor::*[contains(@class,'tile-row') or contains(@class,'field-wrapper')]//button"
        self.__driver.find_element(By.XPATH, edit_button).click()

    @PageService()
    def click_on_edit_backup_window(self) -> None:
        """Method to click on backup window"""
        self.__click_on_edit_window('Backup window')

    @PageService()
    def click_on_edit_full_backup_window(self) -> None:
        """Method to click on full backup window"""
        self.__click_on_edit_window('Full backup window')

    @PageService()
    def click_on_edit_ibmi_backup_window(self) -> None:
        """Method to click on backup window"""
        self.__click_on_edit_window_ibmi('Backup window')

    @PageService()
    def click_on_edit_ibmi_full_backup_window(self) -> None:
        """Method to click on full backup window"""
        self.__click_on_edit_window_ibmi('Full backup window')

    @PageService()
    def click_on_edit_ibmi_inc_backup_frequency(self) -> None:
        """Method to click on full backup window"""
        self.__click_on_edit_window_ibmi('Backup frequency')
        # self.__admin_console.wait_for_completion()

    @PageService()
    def click_on_edit_ibmi_full_backup_frequency(self) -> None:
        """Method to click on full backup window"""
        if not self.__toggle.is_enabled(label="Add full backup"):
            self.__toggle.enable(label="Add full backup")
        self.__click_on_edit_window_ibmi('Full backup frequency')
        # self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_on_edit_window_ibmi(self, window_name: str) -> None:
        """Method to click on edit backup window"""
        edit_button = f"{self.__base_ibmi_xpath}//*[text()='{window_name}']//ancestor::*[contains(@class,'tile-row') or contains(@class,'field-wrapper')]//button"
        self.__driver.find_element(By.XPATH, edit_button).click()

    @WebAction()
    def fill_ibmi_backup_frequency(self, values):
        """Method to fill IBMi schedule
        Args:
        values(dict): frequency properties that needs to be filled
        Example: {'Frequency': '1',
                  'FrequencyUnit': 'Day(s)',
                  'StartTime': '10:30 pm',
                  'FullFrequency': 'Daily' / 'Weekly' / 'Monthly' / "Yearly",
                  'FullStartTime': '11:30 pm',
                  'FullStartEvery': 'Monday' / 'Tuesday'/ 'Wednesday'/ 'Thursday'/ 'Friday'/ 'Saturday'/ 'Sunday',
                  'FullStartWeek' : 'First' / 'Second' / 'Third' / 'Fourth' / 'Last',
                  'FullStartMonth':  'January' / <Any one month of the year>
                  }
        """

        if 'Frequency' in values.keys():
            self.__fill_rpo_frequency(values['Frequency'])
        if 'FrequencyUnit' in values.keys():
            self.__select_rpo_frequency_unit(values['FrequencyUnit'])
        if 'StartTime' in values.keys():
            self.__fill_start_time(values['StartTime'])
        if 'FullFrequency' in values.keys():
            self.__dialog.select_dropdown_values(drop_down_id='fullBackupFreqDropdown',
                                                 values=[values['FullFrequency']])
            self.__fill_start_time(values['FullStartTime'])
            if values['FullFrequency'] == "Yearly" or values['FullFrequency'] == "Monthly":
                # select the
                self.__dialog.select_dropdown_values(drop_down_id='fullBackupFreqMonthlyFreqDropdown',
                                                     values=[values['FullStartWeek']])
                self.__dialog.select_dropdown_values(drop_down_id='fullBackupFreqMonthlyDaysDropdown',
                                                     values=[values['FullStartEvery']])
                if values['FullFrequency'] == "Yearly":
                    self.__dialog.select_dropdown_values(drop_down_id='incrementalBackupFreqYearlyMonthOfYear',
                                                         values=[values['FullStartMonth']])
            elif values['FullFrequency'] == "Weekly":
                self.__dialog.select_dropdown_values(drop_down_id='weeklyOptions', values=[values['FullStartEvery']])
            if values['FullFrequency'] not in ["Weekly", "Yearly", "Monthly", "Daily"]:
                raise CVWebAutomationException(f"Invalid Key Passed in Input : [{values['FullFrequency']}]")
        self.__dialog.click_submit()

    @PageService()
    def click_on_edit_sla(self) -> None:
        """Method to click on edit SLA"""
        self.__click_on_edit_window('SLA')

    @PageService()
    def __read_backup_window_list(self, backup_window: str) -> dict:
        """Method to read configured backup window list"""
        backup_list_xpath = f"{self.__base_xpath}//*[text()='{backup_window}']//ancestor::*[@class='field-wrapper']//*[contains(@class,'list')]//li"
        backup_list = self.__driver.find_elements(By.XPATH, backup_list_xpath)
        return {day.strip(): time.strip().split(', ') for backup in backup_list for day, time in [backup.text.split(':', 1)]}

    @PageService()
    def get_backup_window_config(self) -> dict:
        """Method to get backup window details"""
        return {
            'Backup window' : self.__read_backup_window_list('Backup window'),
            'Full backup window' : self.__read_backup_window_list('Full backup window')
        }

    @PageService()
    def get_sla(self) -> str:
        """Method to get SLA string"""
        return self.__rpanel_info.get_details()['SLA']

    @PageService()
    def click_on_edit_inc_backup_frequency(self) -> None:
        """Method to click on full backup window"""
        self.__click_on_edit_window('Backup frequency')

    @PageService()
    def click_on_edit_full_backup_frequency(self) -> None:
        """Method to click on full backup window"""
        if not self.__toggle.is_enabled(label="Add full backup"):
            self.__toggle.enable(label="Add full backup")
        self.__click_on_edit_window('Full backup frequency')


class PlanRules:
    """ Class for the Plan Rule page """

    def __init__(self, admin_console: AdminConsole):
        """
        Method to initiate PlanRules class

        Args:
            admin_console   (Object) :   AdminConsole Class object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__rtable = Rtable(self.__admin_console)
        self.__drop_down = RDropDown(self.__admin_console)
        self.__form = Form(admin_console)
        self.__rdialog = RModalDialog(admin_console)
        self.__rmodal_panel = RModalPanel(admin_console)
        self.__page_container = PageContainer(admin_console, 'rules')

    @WebAction()
    def __select_servergroup(self, server_groups: list) -> None:
        """Method to select server groups"""
        self.__drop_down.select_drop_down_values(
            values=server_groups, drop_down_id='serverGroups')

    @WebAction()
    def __select_region(self, regions: list) -> None:
        """Method to select regions"""
        self.__drop_down.select_drop_down_values(
            values=regions, drop_down_id='region')

    @WebAction()
    def __select_solutions(self, solutions: list) -> None:
        """Method to select solutions"""
        self.__drop_down.select_drop_down_values(
            values=solutions, drop_down_id='solutions')

    @WebAction()
    def __fill_tags(self, tags: dict) -> None:
        """Method to fill tag names and tag values"""
        for tag_name, tag_value in tags.items():
            self.__drop_down.search_and_select(select_value=tag_name, id='tagname')
            self.__form.fill_text_in_field(
                element_id='tagValue', text=tag_value)
            self.__form.click_icon('Add tag')

    @WebAction()
    def __get_tags(self) -> dict:
        """Method to get tag names and tag values"""
        text_elements = self.__driver.find_elements(By.XPATH,
            "//*[contains(@class, 'tagsList')]//input")[2:]
        texts = [element.get_attribute('value') for element in text_elements]

        return {texts[i]: texts[i + 1] for i in range(0, len(texts), 2)}

    @WebAction()
    def __select_plan(self, plan_name: str) -> None:
        """Method to select server plan"""
        self.__drop_down.select_drop_down_values(
            values=[plan_name], drop_down_id='serverPlan')

    @WebAction()
    def __go_to_rules_tab(self) -> None:
        """Method to select rule tab"""
        self.__page_container.select_tab('Rules')

    @WebAction()
    def __go_to_waiting_room(self) -> None:
        """Method to select waiting room tab"""
        self.__page_container.select_tab('Waiting room')

    @WebAction()
    def __go_to_excluded_entities(self) -> None:
        """Method to select excluded entities tab"""
        self.__page_container.select_tab('Excluded entities')

    @WebAction()
    def __process_rule_props(self, rule_props: dict) -> None:
        """Method to process rule props"""
        if 'serverGroups' in rule_props:
            self.__select_servergroup(rule_props['serverGroups'])
        if 'region' in rule_props:
            self.__select_region(rule_props['region'])
        if 'solutions' in rule_props:
            self.__select_solutions(rule_props['solutions'])
        if 'tags' in rule_props:
            self.__fill_tags(rule_props['tags'])
        if 'serverPlan' in rule_props:
            self.__select_plan(rule_props['serverPlan'])

    @WebAction()
    def __perform_action(self, rank: str, action: str) -> None:
        """Method to perform action on specified rank of plan rule"""
        self.__rtable.display_hidden_column(column_name='Priority number')
        self.__rtable.access_action_item(entity_name=rank, action_item=action)

    @PageService()
    def go_to_plan_rules_page(self) -> None:
        """Method to navigate to plan rules pages"""
        self.__admin_console.navigator.navigate_to_plan()
        self.__rtable.access_toolbar_menu('Plan rules')

    @PageService()
    def add(self, rule_props: dict) -> None:
        """
        Method to add plan rule

        Args:
            rule_props (dict)   :   Plan Rule properties

            Example:
                rule_props = {
                    'serverGroups'  :   [],
                    'region'        :   [],
                    'solutions'     :   [],
                    'tags'          :   {'tag_1' : 'value_1', 'tag_2' : ''},
                    'serverPlan'    :   'Server Plan'
                }
        """
        self.__go_to_rules_tab()
        self.__rtable.access_toolbar_menu('Add')
        self.__process_rule_props(rule_props)
        self.__form.click_button_on_dialog('Add')
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def edit(self, priority_num: int, rule_props: dict) -> None:
        """
        Method to add plan rule

        Args:
            priority_num (int)    :   Index of the plan rule
            rule_props (dict)   :   Plan Rule properties

            Example:
                rule_props = {
                    'serverGroups'  :   [],
                    'region'        :   [],
                    'solutions'     :   [],
                    'tags'          :   {'tag_1' : 'value_1', 'tag_2' : ''},
                    'serverPlan'    :   'Server Plan'
                }
        """
        self.__go_to_rules_tab()
        self.__perform_action(priority_num, 'Edit')
        self.__process_rule_props(rule_props)
        self.__form.click_button_on_dialog('Add')

    @PageService()
    def delete(self, priority_num: int) -> None:
        """
        Method to delete plan rule

        Args:
            priority_num      (int)    :   Index of the plan rule
        """
        self.__go_to_rules_tab()
        self.__perform_action(priority_num, 'Delete')
        self.__rdialog.click_submit()

    @PageService()
    def get(self, priority_num: int) -> dict:
        """
        Method to get plan rule details

        Args:
            priority_num (int)    :   Index of the plan rule

            Returns:
                rule_props = {
                    'serverGroups'  :   [],
                    'region'        :   [],
                    'solutions'     :   [],
                    'tags'          :   {'tag_1' : 'value_1', 'tag_2' : ''},
                    'serverPlan'    :   'Server Plan'
                }
        """
        self.__go_to_rules_tab()
        self.__perform_action(priority_num, 'Edit')
        server_groups = self.__drop_down.get_selected_values('serverGroups', False)
        regions = self.__drop_down.get_selected_values('region', False)
        solutions = self.__drop_down.get_selected_values('solutions', False)
        tags = self.__get_tags()
        server_plan = self.__drop_down.get_selected_values('serverPlan', False)

        rule_props = {
            'serverGroups': server_groups,
            'region': regions,
            'solutions': solutions,
            'tags': tags,
            'serverPlan': server_plan
        }
        self.__form.click_button_on_dialog('Cancel')
        self.__admin_console.wait_for_completion()
        return rule_props

    @PageService()
    def is_exec_mode_automatic(self) -> bool:
        """Method to check if Execution Mode is Automatic"""
        self.__go_to_waiting_room()
        self.__rtable.access_toolbar_menu('Settings')
        automatic_mode_status = self.__rdialog.checkbox.is_checked(
            id='automatic')
        self.__rdialog.click_cancel()
        return automatic_mode_status

    @PageService()
    def set_execution_mode(self, mode: str) -> None:
        """
        Method to set Execution Mode

        Args:
            mode    (str)   :   "manual" or "automatic"

        """
        self.__go_to_waiting_room()
        self.__rtable.access_toolbar_menu('Settings')
        self.__rdialog.checkbox.check(id=mode)
        self.__rdialog.click_submit()

    @PageService()
    def get_execution_mode(self) -> str:
        """Method to check the execution mode"""
        return 'automatic' if self.is_exec_mode_automatic() else 'manual'

    @WebAction()
    def __get_subclients_list(self) -> list:
        """Method to get list of subclients shown on listing page"""
        return [(parts[1].split()[0], parts[0]) for parts in
                (i.split('\n') for i in self.__rtable.get_column_data('Subclient'))]

    @PageService()
    def available_plan_rules(self) -> list:
        """Method to get list of available plan rule ranks"""
        self.__go_to_rules_tab()
        self.__rtable.display_hidden_column(column_name='Priority number')
        return self.__rtable.get_column_data('Priority number')

    @PageService()
    def waiting_subclients(self) -> list:
        """Method to get subclients in waiting room"""
        self.__go_to_waiting_room()
        return self.__get_subclients_list()
    
    @PageService()
    def get_plan_to_be_assigned(self, server_name: str, subclient_name: str='default') -> str:
        """
            Method to get the plan to be assigned to the subclient as per waiting room
            
            Args:
                server_name     (str)   :   Server name
                subclient_name  (str)   :   Subclient name
        """
        self.__go_to_waiting_room()
        self.__rtable.search_for(server_name)
        self.__rtable.apply_filter_over_column(column_name=self.__admin_console.props['label.subclient'], filter_term=subclient_name)
        plan_name = self.__rtable.get_column_data(self.__admin_console.props['label.planToBeAssigned'])
        self.__rtable.clear_column_filter(column_name=self.__admin_console.props['label.subclient'], filter_term=subclient_name)
        return plan_name[0] if plan_name else 'No Plan to be assigned'

    @PageService()
    def excluded_subclients(self) -> list:
        """Method to get excluded subclients"""
        self.__go_to_excluded_entities()
        return self.__get_subclients_list()

    @PageService()
    def is_subclient_present_in_waiting_room(self, server_name: str, subclient_name: str) -> bool:
        """Method to check if subclient is present in waiting room"""
        return (server_name, subclient_name) in self.waiting_subclients()

    @PageService()
    def is_subclient_excluded(self, server_name: str, subclient_name: str) -> bool:
        """Method to check if subclient is present in excluded list"""
        return (server_name, subclient_name) in self.excluded_subclients()

    @WebAction()
    def __select_subclient_row(self, server_name: str, subclient_name: str) -> None:
        """Method to apply filter for specified server and subclient name"""
        self.__rtable.apply_filter_over_column(
            column_name='Server', filter_term=server_name)
        self.__rtable.apply_filter_over_column(
            column_name='Subclient', filter_term=subclient_name)
        self.__rtable.select_rows(names=[subclient_name])
        self.__rtable.clear_column_filter(
            column_name='Server', filter_term=server_name)
        self.__rtable.clear_column_filter(
            column_name='Subclient', filter_term=subclient_name)

    @PageService()
    def manually_assign_plan(self, server_name: str, subclient_name: str) -> None:
        """
        Method to manually assign plan

        Args:
            server_name    (str)   :   Server name
            subclient_name (str)   :   Subclient name

        """
        self.__go_to_waiting_room()
        self.__select_subclient_row(server_name, subclient_name)
        self.__rtable.access_toolbar_menu('Assign')
        self.__rdialog.click_submit()

    @PageService()
    def exclude_subclient(self, server_name: str, subclient_name: str) -> None:
        """
        Method to exclude subclient from plan rules

        Args:
            server_name    (str)   :   Server name
            subclient_name (str)   :   Subclient name

        """
        self.__go_to_waiting_room()
        self.__select_subclient_row(server_name, subclient_name)
        self.__rtable.access_toolbar_menu('Skip assignment')

    @PageService()
    def include_subclient(self, server_name: str, subclient_name: str) -> None:
        """
        Method to include subclient for plan rules

        Args:
            server_name    (str)   :   Server name
            subclient_name (str)   :   Subclient name

        """
        self.__go_to_excluded_entities()
        self.__select_subclient_row(server_name, subclient_name)
        self.__rtable.access_toolbar_menu('Include')
