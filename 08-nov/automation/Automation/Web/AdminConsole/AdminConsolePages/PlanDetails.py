# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
plan detail page on the AdminConsole

Class:

    PlanDetails()

Functions:

plan_info()                             --  Displays all the information of the plan in the form of a dictionary
copy_info()                             --  Retrieves all information from Copy details page in the form of a dictionary
edit_plan_storage_pool()                --  Edits the storage pool associated with the plan
edit_plan_alerts()                      --  Edits the alerts associated with the plan
edit_plan_network_resources()           --  Edits the network resources associated with the plan
edit_plan_rpo()                         --  Edits the backup SLA associated with the plan
edit_plan_options()                     --  Edits the options associated with the plan
edit_plan_backup_content()              --  Edits the backup content associated with the plan
edit_plan_associated_users_and_groups() --  Edits the users and user groups
                                            associated with the plan
remove_associated_users_and_groups      --  Method to remove associated users or user groups
                                            from a plan
edit_plan_retention()                   --  Method to edit plan retention properties
edit_plan_override_restrictions()       --  Method to edit plan override settings
data_classication_plan_entities()       --  Returns list of entities selected for DC plan
edit_server_plan_storage_pool           --  Method to edit storage pool associated with the plan
access_snap_copy_type_dialog()          --  Method to access copy type edit dialog
delete_server_plan_storage_copy()       --  Method to delete storage copy in a server plan
edit_plan_rpo_start_time()              --  Method to edit RPO start time associated to the plan
edit_plan_full_backup_rpo()             --  Method to edit Full backup RPO settings
redirect_to_plans()                     --  Method to redirect to the plan listing page
convert_elastic_plan()                  --  Method to Convert plan into elastic plan by configuring region based storage
add_security_associations()             --  Method to add security associations
delete_security_associations()          --  Method to delete security associations
is_tile_editable()                      --  Method to check if tile is editable
is_plan_derivable()                     --  Method to check if tile is derivable
is_plan_deletable()                     --  Method to check if tile is deletable
plan_tile()                             --  Method to return available plan tile names
edit_copy_retention_rules               --  Method to edit copy retention
edit_copy_extended_retention_rules      --  Method to edit extended retention rules of a copy
delete_multiple_snaps_plan_level()      --  Delete multiple snaps which has common snap job id
run_auxiliary_job()                     --  Method to run auxiliary copy job
get_backup_destination_regions()        --  get Backup destination regions associated to a plan
"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.Components.panel import PanelInfo, ModalPanel, DropDown, RPanelInfo, RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RSecurity, RModalDialog, RTags, SLA
from Web.AdminConsole.Components.core import BlackoutWindow
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.content import RBackupContent
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.AdminConsolePages.CopyDetails import Configuration, Jobs
from Web.AdminConsole.Components.alert import Alert


class PlanDetails:
    """ Class for the Plans page """

    def __init__(self, admin_console):
        """
        Method to initiate PlanDetails class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.__admin_console = admin_console
        self.__props = self.__admin_console.props
        self.__driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__plans = Plans(self.__admin_console)
        self.__panel_dropdown_obj = DropDown(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__rsecurity = RSecurity(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__rbackup_content = RBackupContent(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rtags = RTags(self.__admin_console)
        self.__toggle = Toggle(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rpanel_info = RPanelInfo(self.__admin_console)
        self.__rpo = RPO(self.__admin_console)
        self.__backup_window = BlackoutWindow(self.__admin_console)
        self.__sla = SLA(self.__admin_console)
        self.__extended_rule_id_list = ["firstExtendedRetentionRule",
                                        "secondExtendedRetentionRule",
                                        "thirdExtendedRetentionRule"]
        self.navigator = self.__admin_console.navigator
        self.copydetails = Configuration(self.__admin_console)
        self.copydetails_jobs = Jobs(self.__admin_console)

    @WebAction()
    def __check_if_copy_present(self, copy_name):
        """
                Method to check if a storage policy copy exists

                Args:
                    copy_name: Name of copy to be checked

                Returns:
                    boolean: True/False based on copy presence
                """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        copy_exists = False
        copy_list = table.get_column_data('Name')
        for item in copy_list:
            if copy_name in item:
                copy_exists = True
                break
        return copy_exists

    @WebAction()
    def __extract_plan_info(self, plan_type):
        """
        Method to extract plan information and return a dictionary

        Args:
            plan_type : Type of plan to be fetched details of (Laptop/Server)

        Returns:
            details dict() : dictionary containing plan information displayed in UI
        """
        self.log.info("Getting all plan information")
        if self.is_advance_view_toggle_visible():
            self.enable_advanced_view()
        details = {}
        title = PageContainer(self.__admin_console).fetch_title()
        details.update({"PlanName": title})
        elems = RPanelInfo(self.__admin_console).available_panels()
        for key in elems:
            if key != '':
                if key == "Security":
                    security_table = Rtable(self.__admin_console, id='securityAssociationsTable')
                    column_names = security_table.get_visible_column_names()
                    if not column_names:
                        details.update({key: {}})
                        continue
                    key_rows = security_table.get_column_data(column_names[0])
                    value_rows = security_table.get_column_data(column_names[1])
                    temp_dict = {}
                    for i in range(len(key_rows)):
                        value_list = []
                        if "[Custom] - " in value_rows[i]:
                            value_rows[i] = value_rows[i][11:]
                            value_list = value_rows[i].split(" , ")
                        else:
                            value_list.append(value_rows[i])
                        if key_rows[i] in temp_dict:
                            temp_dict[key_rows[i]].append(value_list)
                        else:
                            temp_dict[key_rows[i]] = [value_list]
                    details.update({key: temp_dict})
                elif key == "Backup content":
                    temp_dict1 = self.get_backup_content()
                    temp_dict = {'Windows': temp_dict1['Windows']['BACKUP_CONTENT'],
                                 'Unix': temp_dict1['Unix']['BACKUP_CONTENT']}
                    if plan_type == 'laptop_plan':
                        temp_dict['Mac'] = temp_dict1['Mac']['BACKUP_CONTENT']
                    details.update({key: temp_dict})
                else:
                    values = RPanelInfo(self.__admin_console, key).get_details()
                    details.update({key: values})

        if plan_type != "Dynamics365":
            PageContainer(self.__admin_console).select_tab(self.__props['label.nav.storagePolicy'])
            details.update({'Backup destinations': [Rtable(self.__admin_console, id='planBackupDestinationTable')
                           .get_column_data('Storage')[0].split('\n')[0]]})
        self.log.info(details)
        return details

    @WebAction()
    def __dissociate_all_users_user_groups(self):
        """ Method to dissociate all users and user groups"""
        user_list = self.__driver.find_elements(By.XPATH,
                                                "//div[@class='users-list']/ul/li")
        for user in user_list:
            user.find_element(By.XPATH, ".//span[@class='delete-row']").click()

    @WebAction()
    def __dissociate_all_users(self):
        """ Method to dissociate all users """
        users = self.__driver.find_elements(By.XPATH,
                                            "//div[@class='invited-user']")
        for user in users:
            user.find_element(By.XPATH, ".//button[@title='Delete']").click()

    @WebAction()
    def __dissociate_all_user_groups(self):
        """ Method to dissociate all user groups """
        users = self.__driver.find_elements(By.XPATH,
                                            "//div[@class='users-list']//span[@class='group-type']")
        for user in users:
            user.find_element(By.XPATH, ".//span[@class='delete-row']").click()

    @WebAction()
    def __dissociate_specific_users_user_groups(self, user_and_group_list):
        """ Method to dissociate specific users or user groups """
        user_list = self.__driver.find_elements(By.XPATH,
                                                "//div[@class='users-list']/ul/li")
        for user in user_list:
            for value in user_and_group_list['Delete_Specific_user_or_group']:
                if user.find_element(By.XPATH, ".//span[@class='ng-binding']").text == value:
                    user.find_element(By.XPATH,
                                      ".//span[@class='delete-row']").click()

    @WebAction()
    def __access_rpo_edit_dialog(self):
        """ Method to access RPO edit dialog """
        self.__driver.find_element(By.XPATH,
                                   "//a[@data-ng-click='enableEditModeForIncrementalRPO()']").click()

    @WebAction()
    def __access_snap_points_edit_dialog(self):
        """ Method to access snap recovery points edit dialog """
        if not self.__driver.find_element(By.ID, "retention-"
                                                 "jobs-mode-for-plan").is_selected():
            self.__driver.find_element(By.ID, "retention-jobs-"
                                              "mode-for-plan").click()
            self.__admin_console.click_button("Yes")
        self.__driver.find_element(By.XPATH,
                                   "//*[@class='group retention-period-options']//..//a[@data-ng-click='ctrl.toggleEdit()']").click()

    @WebAction()
    def __access_snap_copy_type_dialog(self, type="vault"):
        """ Method to access copy type edit dialog """
        if type == "vault":
            self.__driver.find_element(By.ID, "VAULT").click()
        else:
            self.__driver.find_element(By.ID, "MIRROR").click()

    @WebAction()
    def __click_add_svm_mappings(self):
        """Method to click on adding svm mappings during secondary snap copy creation"""
        self.__driver.find_element(By.XPATH,
                                   "//*[contains(@class,'MuiButton-containedSizeMedium')]//*[text()='Add']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __access_retention_period_edit_dialog(self):
        """Method to access retention period edit dialog"""
        if not self.__driver.find_element(By.ID, "retention-non-"
                                                 "jobs-mode-for-plan").is_selected():
            self.__driver.find_element(By.ID, "retention-non-"
                                              "jobs-mode-for-plan").click()
            self.__admin_console.click_button("Yes")
        self.__driver.find_element(By.XPATH, "//*[@id='tileContent_Retention']//.."
                                             "//li[@class='group retention-period-options']//../"
                                             "a[@data-ng-click='ctrl.toggleEdit()']").click()

    @WebAction()
    def __access_snap_rpo_edit_dialog(self):
        """ Method to access snap recovery points edit dialog """
        self.__driver.find_element(By.XPATH, "//*[@id='tileContent_Snapshot options']//.."
                                             "//span[contains(text(),'Backup copy frequency (in HH:MM)')]"
                                             "//..//a[@data-ng-click='ctrl.toggleEdit()']").click()

    @WebAction()
    def __access_log_rpo_edit_dialog(self):
        """ Method to access database log rpo edit dialog """
        xpath = "//span[contains(text(),'Log backup RPO')]/ancestor::li//a[@data-ng-click='ctrl.toggleEdit()']"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __fill_snap_retention_period(self, retention_period):
        """Method to set the snap retention period"""
        retentionval = self.__driver.find_element(By.XPATH,
                                                  "//*[@class='group retention-period-options']//../input[@data-ng-model='uiModel.retentionInfo.value']")
        retentionval.click()
        retentionval.clear()
        retentionval.send_keys(retention_period['retention_value'])
        self.__admin_console.select_value_from_dropdown(
            "retentionPeriodOptionsAsRadioBtn", retention_period['period'])

    @WebAction()
    def __fill_rpo(self, backup_rpo, flag_snapshot=True, flag_db_log=False):
        """ Method to fill database log rpo edit dialog """
        if flag_snapshot:
            backup_copy_label = self.__admin_console.props['label.backupCopyRPOinHHMM']
            hour_xpath = f"//span[contains(text(),'{backup_copy_label}')]//..//input[@placeholder='HH']"
            minute_xpath = f"//span[contains(text(),'{backup_copy_label}')]//..//input[@placeholder='MM']"
            save_xpath = f"//span[contains(text(),'{backup_copy_label}')]//..//" \
                         "a[@data-ng-click='ctrl.saveEdit()']"

        elif flag_db_log:
            log_backup_label = self.__admin_console.props['label.logBackupRPO']
            hour_xpath = f"//span[contains(text(),'{log_backup_label}')]/ancestor::li//input[@placeholder='HH']"
            minute_xpath = f"//span[contains(text(),'{log_backup_label}')]/ancestor::li//input[@placeholder='MM']"
            save_xpath = f"//span[contains(text(),'{log_backup_label}')]/ancestor::li//a[@data-ng-click='ctrl.saveEdit()']"

        self.__driver.find_element(By.XPATH, hour_xpath).click()
        self.__driver.find_element(By.XPATH, hour_xpath).clear()
        self.__driver.find_element(By.XPATH,
                                   hour_xpath).send_keys(str(backup_rpo['hours']))
        self.__driver.find_element(By.XPATH, minute_xpath).click()
        self.__driver.find_element(By.XPATH, minute_xpath).clear()
        self.__driver.find_element(By.XPATH,
                                   minute_xpath).send_keys(str(backup_rpo['minutes']))
        self.__driver.find_element(By.XPATH, save_xpath).click()

    @WebAction()
    def __search_user(self, user_or_group):
        """
        Method to search for user or group in associate users dialog

        Args:
            user_or_group (str) : user or group name to be associated
        """
        self.__rdialog.fill_text_in_field('searchUsers', user_or_group)

    @WebAction()
    def __select_user(self, user_or_group):
        """
        Method to associate users and user groups

        Args:
            user_or_group (str) : user or group name to be associated
        """
        self.__driver.find_element(By.XPATH,
                                   f"//ul[@class='select2-results']//span[contains(text(),'{user_or_group}')]").click()
        time.sleep(2)

    @WebAction()
    def __access_allowed_feature_settings(self, data_ng_click):
        """
        Method to click on settings hyperlink for Edge drive

        Args:
            data_ng_click (str) : data-ng-click attribute of the element
        """
        settings_link = self.__driver.find_element(By.XPATH,
                                                   f"//a[@data-ng-click='{data_ng_click}']")
        settings_link.click()

    @WebAction()
    def __click_add_storage_copy(self, region=None, snap=False):
        """ Method to click on Add 'Copy' or 'Snap Copy' to add additional storage """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        if region:
            self.__table.expand_row(region)

        self.__driver.find_element(By.XPATH,
                                   "//*[contains(@class,'MuiButton-sizeMedium')]//*[text()='Add']").click()
        self.__admin_console.wait_for_completion()
        if snap:
            self.__driver.find_element(By.XPATH,
                                       "//li[contains(text(),'Snap copy')]").click()
        else:
            self.__driver.find_element(By.XPATH,
                                       "//*[text()='Copy']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __enable_netapp_snapmirror_cloud_target(self):
        """ Method to enable NetApp SnapMirror Cloud Target Toggle"""

        self.__rmodal_dialog.enable_toggle(toggle_element_id="netAppCloudTarget")
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_edit_storage_action_item(self, storage_name, region=None):
        """
        Method to click on edit storage action item for existing storage

        Args:
            storage_name (str)  : name of storage to be edited
        """
        if region:
            self.__driver.find_element(By.XPATH,
                                       f"//label[text()='{region}']/ancestor::div[@class='panel-group']"
                                       f"//div[contains(@class,'plan-storage-grid')]//td[@role='gridcell']/a[text()='{storage_name}']") \
                .click()
        else:
            self.__driver.find_element(By.XPATH,
                                       f"//div[contains(@class,'plan-storage-grid')]//td[@role='gridcell']/a[text()='{storage_name}']") \
                .click()

    @WebAction()
    def __edge_drive_settings(self, quota):
        """
        Method to set edge drive settings

        Args:
            quota (str) : quota to be set for edge drive
        """

        self.__admin_console.checkbox_select("isEdgeDriveQuotaEnabled")
        self.__admin_console.fill_form_by_id("edgeDriveQuota", quota)
        self.__modal_panel.submit()

    def __edit_plan_storage_ret_period(self, ret_value):
        """ """
        elem = self.__driver.find_element(By.XPATH,
                                          "//input[contains(@class,'policy-retention')]")
        elem.clear()
        elem.send_keys(ret_value)

    @WebAction()
    def __edit_snap_recovery_point(self, snap_recovery_points):
        """Edits number snap recovery points"""
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//*[@id='cv-k-grid-td-StoragePolicyCopy.copyName']/a[contains(text(),'snap copy')]"):
            self.__driver.find_element(By.XPATH,
                                       "//*[@id='cv-k-grid-td-StoragePolicyCopy.copyName']/a[contains(text(),'snap copy')]").click()
            self.__admin_console.wait_for_completion()
            self.__driver.find_element(By.ID, "retention-jobs-mode").click()
            self.__admin_console.fill_form_by_id(
                "snapRecoveryPoints", snap_recovery_points)
            self.__admin_console.submit_form()
        else:
            self.__driver.find_element(By.XPATH,
                                       "//div[@value='snapshotOptions.snapRecoveryPoints']//a[@data-ng-click='ctrl.toggleEdit()']").click()
            self.__driver.find_element(By.ID, 'retention-jobs-mode').click()
            self.__admin_console.fill_form_by_id(
                "snapRecoveryPoints", snap_recovery_points)
            self.__driver.find_element(By.XPATH,
                                       "//div[contains(@value,'snapRecovery')]//a[@data-ng-click='ctrl.saveEdit()']").click()

    @WebAction()
    def redirect_to_plans(self):
        """
            Method to redirect back to the plans page from the bread crumb
             of the plan details page
        """
        self.__driver.find_element(By.LINK_TEXT,
                                   self.__admin_console.props['label.nav.profile']).click()

    @PageService()
    def plan_info(self, plan_type):
        """
        Retrieves all plan information displayed from Plan Details Section

        Args:
            plan_type : Type of plan to be fetched details of (Laptop/Server)

        Returns:
            plan_details dict() : dictionary containing plan information displayed in UI
        """
        plan_details = self.__extract_plan_info(plan_type)
        return plan_details

    @PageService()
    def copy_info(self, copy_name, region=None):
        """Retrieves all information from Copy details page in the form of a dictionary

            Args:
                copy_name   (str)   - Name of copy
                region      (str)   - Region name if it is a multi-region plan

            Returns:
                dict                - All the information displayed on copy page
        """
        # Navigate to copy page
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id='planBackupDestinationTable')
        if region:
            self.__table.expand_row(region)
        table.access_link(copy_name)

        self.log.info('Getting all copy information')
        details = {}
        title = PageContainer(self.__admin_console).fetch_title()
        details.update({"CopyName": title})
        panels = RPanelInfo(self.__admin_console).available_panels()
        for panel in panels:
            if panel != '':
                self.log.info('Getting information for %s panel' % panel)
                values = RPanelInfo(self.__admin_console, panel).get_details()
                details.update({panel: values})
        return details

    @PageService()
    def is_copy_present(self, copy):
        """
        Checks if provided copy is present inside plan

        Args:
            copy :(str) Name of copy

        Returns:
            boolean: True/False based on if copy is present
        """
        return self.__check_if_copy_present(copy)

    @PageService()
    def edit_plan_storage_pool(self, additional_storage, edit_storage, region=None):
        """
        Method to edit storage pool associated with the plan

        Args:
            additional_storage (dictionary): Dictionary containing values for an additional
                storage, if it is to be added and the values of it
                Eg. - additional_storage = {'Add':False, 'storage_name':'Store',
                                                    'storage_pool':'Secondary',
                                                    'ret_period':'10'}
            edit_storage (dictionary): Dictionary containing values to edit existing storage
                Eg. - edit_plan_storage = {'Edit': True,
                                          'old_storage_name': 'Primary',
                                          'new_storage_name':'New Primary',
                                          'new_ret_period':'20'}
            region (string): region name
        """
        xpath_region = "//a[contains(text(),'Configure region based storage')]"
        xpath_add = "//span[contains(text(),'Backup destinations')]/ancestor::div//a[contains(text(),'Add')]"
        if region and self.__admin_console.check_if_entity_exists("xpath", xpath_region):
            self.__driver.find_element(By.XPATH, xpath_region).click()
            if additional_storage:
                self.__additional_storage(additional_storage)
            if edit_storage:
                self.__edit_storage(edit_storage)
            self.__panel_dropdown_obj.select_drop_down_values(
                values=[region], index=0)
            self.__admin_console.submit_form()
        elif region and region == self.__driver.find_element(By.XPATH, "//uib-accordion//label").text:
            if additional_storage:
                self.__additional_storage(additional_storage, region)
            if edit_storage:
                self.__edit_storage(edit_storage, region)
        elif self.__admin_console.check_if_entity_exists("xpath", xpath_add):
            if additional_storage:
                self.__additional_storage(additional_storage)
            if edit_storage:
                self.__edit_storage(edit_storage)

    @PageService()
    def __additional_storage(self, additional_storage, region=None):
        """Add additional storage"""
        self.__click_add_storage_copy(region)
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_id(
            "storageName", additional_storage['storage_name'])
        self.__panel_dropdown_obj.select_drop_down_values(values=[additional_storage['storage_pool']],
                                                          drop_down_id="storage")
        self.__admin_console.submit_form()

    @PageService()
    def __edit_storage(self, edit_storage, region=None):
        """Edit name of storage"""
        self.__click_edit_storage_action_item(
            edit_storage['old_storage_name'], region)
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_id(
            "storageName", edit_storage['new_storage_name'])
        self.__admin_console.submit_form()

    @PageService()
    def edit_server_plan_storage_pool(self, additional_storage, edit_storage, snap=False):
        """
        Method to edit storage pool associated with the plan or Add additional Storage

        Args:
            additional_storage (dictionary): Dictionary containing values for an additional
                storage, if it is to be added and the values of it
                Eg. - additional_storage = {'Add':False, 'storage_name':'Store',
                                                    'storage_pool':'Secondary',
                                                    'ret_period':'10'}
            edit_storage (dictionary): Dictionary containing values to edit existing storage
                Eg. - edit_plan_storage = {'Edit': True,
                                          'old_storage_name': 'Primary',
                                          'new_storage_name':'New Primary',
                                          'new_ret_period':'20'}
        """
        if additional_storage and snap:
            self.__click_add_storage_copy(snap=snap)
            self.__admin_console.fill_form_by_id(
                "backupDestinationName", additional_storage['storage_name'])
            if additional_storage['cloud_copy']:
                self.__enable_netapp_snapmirror_cloud_target()
            else:
                self.__access_snap_copy_type_dialog(additional_storage['copy_type'])
            self.__rdropdown.select_drop_down_values(
                values=[additional_storage['storage_pool']],
                drop_down_id='storageDropdown'
            )
            self.__rdropdown.select_drop_down_values(
                drop_down_id='sourceCopy',
                values=[additional_storage['source_copy']]
            )
            if additional_storage['snap_engine'] in ["NetApp", "Amazon Web Services", "Pure Storage FlashArray Snap", "Microsoft Azure"]:
                self.__driver.find_element(By.XPATH, 
                    "//*[contains(@class,'MuiButton-sizeSmall')]//*[text()='Add']").click()
                self.__admin_console.wait_for_completion()
                if additional_storage['snap_engine'] in ["Pure Storage FlashArray Snap"]:
                    additional_storage['snap_engine'] = "Pure Storage FlashArray"
                if additional_storage['cloud_copy']:
                    self.__rdropdown.select_drop_down_values(drop_down_id = "snapVendorDropdown", 
                                                             values = [additional_storage['cloud_snap_engine']])
                else:
                    self.__rdropdown.select_drop_down_values(drop_down_id = "snapVendorDropdown", 
                                                             values = [additional_storage['snap_engine']])

                self.__rdropdown.select_drop_down_values(
                    values=[additional_storage['mappings']['src_svm']], drop_down_id='sourceSVMDropdown')
                self.__rdropdown.select_drop_down_values(
                    values=[additional_storage['mappings']['dest_svm']], drop_down_id='targetSVMDropdown')
                self.__click_add_svm_mappings()
                if additional_storage['cloud_copy']:
                    mappings_dialog = RModalDialog(self.__admin_console, title="Add SVM to SnapMirror Cloud Target mappings")
                elif additional_storage['snap_engine'] == "Pure Storage FlashArray":
                    if additional_storage['default_replica']:
                        mappings_dialog = RModalDialog(self.__admin_console, title="Add Mappings")
                    else:
                        mappings_dialog = RModalDialog(self.__admin_console, title="Add Configured Target Array")
                else:
                    if additional_storage['default_replica']:
                        mappings_dialog = RModalDialog(self.__admin_console, title="Add Mappings")
                    else:
                        mappings_dialog = RModalDialog(self.__admin_console, title="Add SVM Mappings")
                mappings_dialog.click_button_on_dialog('Save')

            self.__rmodal_dialog.click_button_on_dialog('Save')
            if additional_storage['snap_engine'] == "Pure Storage FlashArray":
                self.__rmodal_dialog.click_yes_button()

        if additional_storage and not snap:
            self.__click_add_storage_copy()
            self.__admin_console.wait_for_completion()
            self.__admin_console.fill_form_by_id(
                "backupDestinationName", additional_storage['storage_name'])
            self.__rdropdown.select_drop_down_values(
                drop_down_id='storageDropdown',
                values=[additional_storage['storage_pool']]
            )
            self.__admin_console.submit_form()

        if edit_storage:
            self.__admin_console.select_hyperlink(
                edit_storage['old_storage_name'])
            self.__admin_console.wait_for_completion()

            if edit_storage['new_storage_name']:
                self.__admin_console.fill_form_by_id(
                    "storageName", edit_storage['new_storage_name'])

            if edit_storage['new_ret_period']:
                self.__edit_plan_storage_ret_period(
                    edit_storage['new_ret_period'])
            self.__admin_console.submit_form()

    @PageService()
    def edit_plan_alerts(self, update_alerts):
        """
        Method to edit alerts associated with the plan

        Args:
            update_alerts (dict): dictionary containing alert details,
                    which alerts to enable/disable.
                Eg. - update_alerts = {"Backup" :None,
                                       "Jobfail": "Restore Job failed",
                                       "edge_drive_quota":None}
        """

        RPanelInfo(self.__admin_console, 'Alerts').edit_tile()
        self.__plans.set_alerts(update_alerts, edit_alert=True)
        self.__modal_panel.submit()

    @PageService()
    def edit_plan_network_resources(self, throttle_send, throttle_receive):
        """
        Method to edit  network resources associated with the plan

        Args:
            throttle_send (str or int): Network resource value
            throttle_receive (str or int): Network resource value
        """
        RPanelInfo(self.__admin_console, 'Network resources').edit_tile()
        self.__plans.set_network_resources(throttle_send, throttle_receive)
        self.__modal_panel.submit()

    @WebAction()
    def edit_plan_rpo_hours(self, rpo_hours):
        """
        Method to edit the RPO (Backup SLA) associated with the plan

        Args:
            rpo_hours (string): Value of RPO hours for the plan
        """
        self.__access_rpo_edit_dialog()
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_id("rpo", rpo_hours)
        self.__driver.find_element(By.XPATH,
                                   "//*[@id='tileContent_RPO']//a[contains(@class,'save-frequency')]").click()

    @WebAction()
    def edit_plan_rpo_start_time(self, start_time):
        """
        Method to edit the RPO start time associated with the plan

        Args:
             start_time (str):  Start time of the plan in format: (%I:%M %p) eg. "07:00 AM"
        """
        self.__access_rpo_edit_dialog()
        self.__admin_console.wait_for_completion()
        hours_minutes, session = start_time.split(" ")
        self.__admin_console.date_picker(time_value={'date': "",
                                                     'hours': hours_minutes.split(":")[0],
                                                     'mins': hours_minutes.split(":")[1],
                                                     'session': session}, pick_time_only=True)
        self.__driver.find_element(By.XPATH,
                                   "//*[@id='tileContent_RPO']//a[contains(@class,'save-frequency')]").click()

    @WebAction()
    def edit_plan_full_backup_rpo(self, start_time=None, start_days=None, enable=True):
        """Method to edit Full backup RPO settings
            Args:
                start_days  (list): Day(s) on which full backup is to be done weekly
                start_time  (str):  start time of schedule
                enable      (bool): True if full backup schedule is to be enabled
        """
        if not enable:
            self.__admin_console.disable_toggle(index=0)
        else:
            self.__admin_console.disable_toggle(index=0)
            self.__admin_console.enable_toggle(index=0)
            self.__admin_console.wait_for_completion()
            if start_days:
                self.__panel_dropdown_obj.select_drop_down_values(drop_down_id="isteven-multi-select2",
                                                                  values=start_days)
            hours_minutes, session = start_time.split(" ")
            self.__admin_console.date_picker(time_value={'date': "",
                                                         'hours': hours_minutes.split(":")[0],
                                                         'mins': hours_minutes.split(":")[1],
                                                         'session': session}, pick_time_only=True)
            self.__driver.find_element(By.XPATH,
                                       "//*[@id='tileContent_RPO']//a[contains(@class,'save-frequency')]").click()

    @WebAction()
    def edit_plan_options(self, file_system_quota):
        """
        Method to edit options (file system quota) associated with the plan

        Args:
            file_system_quota (string): value of upper limit of File system quota for plan

        Returns:
            None

        Raises:
            Exception:
                None
        """

        RPanelInfo(self.__admin_console, 'Options').edit_tile()

        if file_system_quota:
            self.__admin_console.checkbox_select('isQuotaEnabled')
            self.__admin_console.fill_form_by_id("quota", file_system_quota)
        else:
            self.__admin_console.checkbox_deselect('isQuotaEnabled')

        self.__modal_panel.submit()

    @PageService()
    def enable_backup_content(self):
        """Method to enable backup content for a server plan"""
        RPanelInfo(self.__admin_console, 'Backup content').edit_tile()

        if self.__rdialog.toggle.is_exists(id='isIncludedContentDefined'):
            self.__rdialog.toggle.enable(id='isIncludedContentDefined')

        self.__rdialog.click_submit()

    @WebAction()
    def edit_plan_backup_content(self,
                                 file_system: str,
                                 content_folders=[],
                                 custom_content=[],
                                 exclude_folders=[],
                                 exclude_custom_content=[],
                                 exception_folders=[],
                                 exception_custom_content=[]):
        """
        Method to edit backup content associated with the plan

        Args:
            file_system                 (str) : Type of operating system (Windows/Unix/Mac)
            content_folders             (list): List of folders to be selected for content backup
            custom_content              (list): List of Custom Paths
            exclude_folders             (list): List of folders to be selected for exclude content
            exclude_custom_content      (list): List of Custom Paths for exclude content
            exception_folders           (list): List of folders to be selected for exception content
            exception_custom_content    (list): List of Custom Paths for exception content
        """
        backup_content_panel = RPanelInfo(
            self.__admin_console, 'Backup content')

        if backup_content_panel.toggle.is_exists('Define backup content'):
            backup_content_panel.toggle.enable('Define backup content')
        else:
            backup_content_panel.edit_tile()

        self.__rbackup_content.select_file_system(os_name=file_system)
        self.__plans.backup_content_selection(content_folders, custom_content)
        self.__plans.exclusion_content_selection(
            exclude_folders, exclude_custom_content)
        self.__plans.exception_content_selection(
            exception_folders, exception_custom_content)

        self.__rdialog.click_submit()

    @PageService()
    def edit_plan_associate_users_and_groups(self, user_or_group):
        """
        Method to edit users/user groups associated with the plan

        Args:
            user_or_group (list): List of Users or user groups to be associated to the plan

                    Eg.- user_or_group = ["Media",
                                          "Tester1",
                                          "TestNew2",
                                          "View All"]
        """

        RPanelInfo(self.__admin_console,
                   'Associated users and user groups').edit_tile()
        for value in user_or_group:
            self.__search_user(value)
            self.__admin_console.wait_for_completion()
            RSecurity(self.__admin_console).laptop_plan_select_user(value)

        self.__admin_console.click_button('Preview')
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//button[@class='btn btn-primary cvBusyOnAjax']"):
            self.__modal_panel.submit()

        elif self.__admin_console.check_if_entity_exists(
                "xpath", "//h4[contains(text(),'Affected client list')]"):
            RModalDialog(self.__admin_console,
                         'Affected client list').click_submit()

    @PageService()
    def edit_plan_features(self, allowed_features, archiving_rules, quota=None, media_agent=None):
        """
        Method to edit plan features associated with the plan

        Args:
            allowed_features (dict)   :     dictionary containing features to be enabled for the
                             plan

                Eg. - allowed_features = {"Laptop": "ON", "Edge Drive": "ON", "DLP": "ON",
                                         "Archiving": "ON"}
            archiving_rules (dict)    :     dictionary containing values for Archive Feature rules

                Eg. - archiving_rules = {"do_edit": True, "start_clean": "40", "stop_clean": "90",
                                        "file_access_time": "85", "file_modify_time": None,
                                        "file_create_time": "2", "archive_file_size": None,
                                        "max_file_size": None, "archive_read_only": True,
                                        "replace_file": None, "delete_file": None}

            quota (str)             :       variable containing value for Edge Drive quota

            media_agent ()          :       media agent to be used for edge drive
        """

        if allowed_features["Edge Drive"] == "ON":
            if not self.__admin_console.check_if_entity_exists("xpath", "//a[@data-ng-click='editEdgeDrive()']"):
                PanelInfo(self.__admin_console,
                          'Allowed features').enable_toggle('Edge Drive')
                self.__admin_console.select_value_from_dropdown(media_agent)
                if quota:
                    self.__edge_drive_settings(quota)
            else:
                if quota:
                    self.__access_allowed_feature_settings("editEdgeDrive()")
                    self.__admin_console.wait_for_completion()
                    self.__edge_drive_settings(quota)

        if allowed_features["DLP"] == "ON":
            RPanelInfo(self.__admin_console,
                       'Allowed features').enable_toggle('DLP')
        else:
            RPanelInfo(self.__admin_console,
                       'Allowed features').disable_toggle('DLP')

        if allowed_features["Archiving"] == "ON":
            if not self.__admin_console.check_if_entity_exists("xpath", "//a[@data-ng-click='editArchiving()']"):
                RPanelInfo(self.__admin_console,
                           'Allowed features').enable_toggle('Archiving')
                if archiving_rules:
                    self.__plans.set_archiving_rules(archiving_rules)
                    self.__modal_panel.submit()
                else:
                    self.__modal_panel.submit()
            else:
                if archiving_rules:
                    self.__access_allowed_feature_settings("editArchiving()")
                    self.__plans.set_archiving_rules(archiving_rules)
                    self.__modal_panel.submit()
        else:
            RPanelInfo(self.__admin_console,
                       'Allowed features').disable_toggle('Archiving')
            self.__admin_console.checkbox_select("disable-archiving-input")
            self.__admin_console.click_button('Save')

    @PageService()
    def remove_associated_users_and_groups(self, user_user_group_de_association):
        """
        Method to remove users/user groups associated to a plan

        Args:
            user_user_group_de_association (dictionary) : Dictionary containing users or users groups to be
                                        de-associated from a plan (if All or just Users or just user groups)

                Eg. - "user_user_group_de_association" : {"DeleteAll": true,
                                                          "DeleteAllUsers": false,
                                                          "DeleteAllUserGroups": false,
                                                          "Delete_Specific_user_or_group": false}
        """
        RPanelInfo(self.__admin_console,
                   'Associated users and user groups').edit_tile()
        if user_user_group_de_association['DeleteAll']:
            self.__dissociate_all_users()
        else:
            if user_user_group_de_association['DeleteAllUsers']:
                self.__dissociate_all_users()

            if user_user_group_de_association['DeleteAllUserGroups']:
                self.__dissociate_all_user_groups()

            if user_user_group_de_association['Delete_Specific_user_user_or_group']:
                self.__dissociate_specific_users_user_groups(
                    user_user_group_de_association['Delete_Specific_user_user_or_group'])

        self.__admin_console.click_button('Preview')

        if self.__admin_console.check_if_entity_exists(
                "xpath", "//h4[contains(text(),'Affected client list')]"):
            RModalDialog(self.__admin_console,
                         'Affected client list').click_submit()

        elif self.__admin_console.check_if_entity_exists(
                "xpath", "//button[@class='btn btn-primary cvBusyOnAjax']"):
            self.__modal_panel.submit()

    @PageService()
    def edit_plan_retention(self, retention):
        """
        Method to edit retention properties for a plan

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
        RPanelInfo(self.__admin_console, 'Retention').edit_tile()
        self.__plans.set_retention(retention)
        self.__modal_panel.submit()

    @PageService()
    def edit_copy_retention_rules(self,
                                  copy_name,
                                  ret_period,
                                  ret_unit,
                                  jobs,
                                  snap_copy=False,
                                  region=None, waitForCompletion=False):
        """
        Method to modify retention period of a copy

        Args:
            copy_name (str)  :  Name of copy
            ret_period (int) : Value of retention period
            ret_unit (str) : Value of retention unit
            jobs (bool) : True if retention period is for jobs else
            snap_copy (bool) : True if retention period is changed from Jobs to days on snap copy
            region (str)    : Region name if it is a multi-region plan
            waitForCompletion (bool): Want to wait for completion or not, after click on Yes
        """
        # Select Backup Destinations Tab
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        # Click edit copy
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        if region:
            self.__table.expand_row(region)
        table.access_link(copy_name)
        RPanelInfo(self.__admin_console, 'Retention rules').edit_tile()
        if not jobs:
            if snap_copy:
                self.__rmodal_dialog.select_radio_by_id(radio_id= "RETENTION_PERIOD")
            self.__rmodal_dialog.fill_text_in_field('retentionPeriodDays', ret_period)
            # Edit retention unit
            self.__rdropdown.select_drop_down_values(drop_down_id='retentionPeriodDaysUnit', values=[ret_unit])
        else:
            self.__rmodal_dialog.select_radio_by_id(radio_id="SNAP_RECOVERY_POINTS")
            self.__rmodal_dialog.fill_text_in_field('numOfSnapRecoveryPoints', ret_period)

        self.__rmodal_dialog.click_button_on_dialog('Save')
        self.__admin_console.click_button('Yes', wait_for_completion=waitForCompletion)
        notification_text = self.__admin_console.get_notification(wait_time=5)
        return notification_text

    @PageService()
    def edit_copy_extended_retention_rules(self,
                                           num_rules,
                                           copy_name,
                                           ret_period,
                                           ret_unit,
                                           ret_freq_type,
                                           region=None):
        """
        Method to modify extended retention of a copy

        Args:
            num_rules (int)  : Number of extended rules to apply
            copy_name (str)  : The name of the copy to modify
            ret_period (list of int) : Values of retention periods
            ret_unit (list of str) : Values of retention units
            ret_freq_type (list of str) : Type of retention, eg: weekly, monthly,..
            region (str)    : Region name if it is a multi-region plan
        """
        # Select Backup Destinations Tab
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        if region:
            self.__table.expand_row(region)
        table.access_link(copy_name)
        RPanelInfo(self.__admin_console, 'Retention rules').edit_tile()

        # Enable extended retention if not enabled
        extended_retention_toggle = self.__driver.find_element(By.XPATH, "//input[@name='useExtendedRetentionRules']")
        is_toggle_enabled = extended_retention_toggle.get_attribute('checked')
        if not is_toggle_enabled:
            self.__admin_console.click_by_xpath("//input[@name='useExtendedRetentionRules']")

        cur_rule = 0
        while cur_rule < num_rules:
            # Edit retention frequency
            self.__rdropdown.select_drop_down_values(drop_down_id=self.__extended_rule_id_list[cur_rule],
                                                     values=[ret_freq_type[cur_rule]])

            # Edit retention unit
            self.__rdropdown.select_drop_down_values(
                drop_down_id=(self.__extended_rule_id_list[cur_rule] + '-textUnit'),
                values=[ret_unit[cur_rule]])

            # Edit retention period
            self.__rmodal_dialog.fill_text_in_field(self.__extended_rule_id_list[cur_rule] + '-text',
                                                    ret_period[cur_rule])

            cur_rule += 1
            if cur_rule < num_rules:
                self.__admin_console.click_button('Add')

        self.__rmodal_dialog.click_button_on_dialog('Save')
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button('Yes')

    @PageService()
    def edit_plan_override_restrictions(self, allow_override, override_laptop_plan=False):
        """
        Method to edit override restrictions

        Args:
            allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override optional",
                                        "Folders_to_backup": "Override not allowed"}
            override_laptop_plan (boolean) = To check if it is laptop plan type
        """
        override_restrictions_panel = RPanelInfo(self.__admin_console, 'Override restrictions')
        override_dialog = RModalDialog(self.__admin_console)
        if not override_restrictions_panel.toggle.is_enabled(id='allowPlanOverride-toggle-btn'):
            override_restrictions_panel.toggle.enable(id='allowPlanOverride-toggle-btn')
        else:
            override_restrictions_panel.edit_tile()
        self.__plans.set_override_options(allow_override, edit_override_laptop=override_laptop_plan)
        override_dialog.click_submit()

    @WebAction()
    def data_classication_plan_entities(self):
        """
        Returns a list of all the entities selected for a data classification plan
        """
        self.log.info("Clicking on the entities to view all")
        self.__driver.find_element(By.XPATH,
                                   '//*[@id="entities"]/span/button').click()
        entities = self.__driver.find_elements(By.XPATH,
                                               '//div[@class="checkBoxContainer"]/div/div[@class="acol"]\
                                               //input/../span')
        entities_list = []
        for entity_id in range(1, len(entities) + 1):
            xpath_value = '//div[@class="checkBoxContainer"]/div[%d]\
            /div[@class="acol"]//input[@checked="checked"]/../span' % entity_id
            if self.__admin_console.check_if_entity_exists('xpath', xpath_value):
                entities_list.append(str(self.__driver.find_element(By.XPATH,
                                                                    xpath_value).text).strip())

        self.log.info("Entities found are: %s" % entities_list)
        return entities_list

    @WebAction()
    def configure_region_based_storage(self, regions, secondary_storage):
        """
        Method to select regions to make storage rules in Backup Destinations Tile

          Args:
              regions (list): list containing the regions that are to be added as the storage rules
        """
        region_panel = RPanelInfo(
            self.__admin_console, title='Backup destinations')
        region_dropdown = RDropDown(self.__admin_console)
        region_dialog = RModalDialog(self.__admin_console)
        xpath_region = '//*[@id="multiRegion"]'
        for i in range(len(regions)):
            self.log.info(f"Adding Storage Rule for {regions[i]}")
            if i == 0:
                self.__admin_console.driver.find_element(By.XPATH,
                                                         xpath_region).click()
                region_dropdown.select_drop_down_values(
                    values=[regions[i]], index=0, partial_selection=True)
            else:
                region_panel.click_button(
                    'Add destinations for another region')
                region_dialog.click_button_on_dialog('Add copy')
                region_dropdown.select_drop_down_values(
                    values=[secondary_storage], index=1)
                region_dialog.fill_text_in_field(
                    element_id='backupDestinationName', text='Primary')
                self.__admin_console.driver.find_elements(By.XPATH,
                                                          "*//button[contains(.,'Save')]")[1].click()
                region_dropdown.select_drop_down_values(
                    values=[regions[i]], index=1, partial_selection=True)
                region_dialog.click_submit()
            self.log.info(f"Added Storage Rule for {regions[i]}")

    @PageService()
    def edit_snapshot_options(self, enable_backup_copy=True, backup_rpo={}):
        """ Method to edit snapshot options

        Args:
            enable_backup_copy (bool)   :   Whether to enable or disable backup copy
            backup_rpo         (dict)   :   Dictionary containing backup rpo value
            example - backup_rpo = {"hours": 10, "minutes": 20}
        """
        snap_shot_panel = RPanelInfo(self.__admin_console, 'Snapshot options')
        rpo_hours = backup_rpo.get('hours')
        rpo_mins = backup_rpo.get('minutes')

        if enable_backup_copy:
            if not snap_shot_panel.toggle.is_enabled('Enable backup copy'):
                snap_shot_panel.toggle.enable('Enable backup copy')
                self.__rmodal_dialog.click_submit()

            self.__admin_console.wait_for_completion()

            if rpo_hours or rpo_mins:
                snap_shot_panel.edit_tile_entity('Backup copy RPO')

                if rpo_hours:
                    snap_shot_panel.fill_value_with_label(
                        'Hour(s)', str(rpo_hours))

                if rpo_mins:
                    snap_shot_panel.fill_value_with_label(
                        'Minute(s)', str(rpo_mins))

                snap_shot_panel.click_button("Submit")
                self.__admin_console.wait_for_completion()
        else:
            snap_shot_panel.toggle.disable('Enable backup copy')

        self.__admin_console.wait_for_completion()

    @PageService()
    def edit_database_options(self, full_backup_schedule=False, backup_rpo=None, use_disk_cache=False, commit_every=8):
        """ Method to edit database options for server plan details

         Args:
            full_backup_schedule (bool)   :   Flag to determine if the full backup schedule is to be edited
                Example: True or False  - Set this as False when modifying log backup rpo
            backup_rpo   (dict)         :   Dictionary containing backup rpo value
                Example: {
                'Frequency'  : '1',
                'FrequencyUnit' : 'Day(s)'  Accepted Values: ['Day(s)', 'Week(s)', 'Month(s)']
                'StartTime'  : '10:30 pm' (optional)
            }
            use_disk_cache    (bool)   :   Whether to use disk cache or not
            commit_every      (int)    :   Commit hours for disk caching
                default: 8
        """
        if not backup_rpo:
            backup_rpo = {}
        if full_backup_schedule:
            label = 'Run full for databases'
        else:
            label = 'Run transaction log for databases'
            backup_rpo['DiskCache'] = use_disk_cache
            if use_disk_cache:
                backup_rpo['CommitEvery'] = commit_every
        self.__rpo.edit_schedule(new_values=backup_rpo, label=label)

    @PageService()
    def delete_server_plan_storage_copy(self, copy_name):
        """
        Method to delete storage copy in a server plan

        Args:
            copy_name (string): name of the copy
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_action_item(copy_name, self.__admin_console.props['label.globalActions.delete'])
        self.__rmodal_dialog.type_text_and_delete(text_val="Delete", checkbox_id="onReviewConfirmCheck", wait=False)
        notification_text = self.__admin_console.get_notification(wait_time=5)
        return notification_text

    @PageService()
    def convert_elastic_plan(self, plan_obj, secondary_storage=None):
        """
        Converts a plan into elastic plan by configuring region based storage and adding regions

        Args:
            plan_obj (dict): Dictionary containing name of the plan and regions to be configured
            {
            "Name": "NAME OF THE PLAN",
            "Region": ["REGION 1", "REGION 2"]
            }
        """
        regions = plan_obj.get("Region")
        self.configure_region_based_storage(regions, secondary_storage)

    @PageService()
    def add_security_associations(self, associations: dict = dict()):
        """ Method to add security associations

        Args:
            associations (dict) : User and Roles

            eg:
            associations = {
                    'user1' : ['View', 'Alert owner'],
                    'user2' : ['Master', 'Plan Subscription Role', 'Tenant Admin']
                }

        """
        RPanelInfo(self.__admin_console, 'Security').edit_tile()
        self.__rsecurity.edit_security_association(associations)

    @PageService()
    def delete_security_associations(self, associations: dict = dict()):
        """Method to delete security associations"""
        RPanelInfo(self.__admin_console, 'Security').edit_tile()
        self.__rsecurity.edit_security_association(associations, False)

    @PageService()
    def is_tile_editable(self, tile_name):
        """Method to check if tile is editable or not"""
        rpanel = RPanelInfo(self.__admin_console, tile_name)
        return rpanel.is_edit_visible()

    @PageService()
    def is_plan_derivable(self):
        """Method to check if plan can be derived"""
        toggle_status = self.get_override_restrictions().get('Allow plan to be overridden')
        derive_button_exists = self.__page_container.check_if_page_action_item_exists(
            'Derive and create new')

        return True if toggle_status and derive_button_exists else False

    @PageService()
    def is_plan_deletable(self):
        """Method to check if plan can be deleted"""
        return self.__page_container.check_if_page_action_item_exists('Delete')

    @PageService()
    def plan_tiles(self):
        """Method to get all the panel names"""
        return RPanelInfo(self.__admin_console).available_panels()

    @PageService()
    def edit_backup_system_state(self, backup_system_state: bool, use_vss=True, only_with_full_backup=False):
        """Method to edit the backup system state"""
        RPanelInfo(self.__admin_console, 'Backup content').edit_tile()

        if self.__rdialog.toggle.is_exists(id='isIncludedContentDefined'):
            self.__rdialog.toggle.enable(id='isIncludedContentDefined')

        self.__rbackup_content.select_file_system('Windows')
        if backup_system_state:
            self.__rbackup_content.enable_backup_system_state(
                use_vss, only_with_full_backup)
        else:
            self.__rbackup_content.disable_backup_system_state()

        self.__rdialog.click_submit()

    @WebAction()
    def get_backup_system_state_details(self):
        """Method to get the backup system state details"""
        return self.get_backup_content(file_system='Windows', backup_system_state=True).get('BACKUP_SYSTEM_STATE', {})

    @WebAction()
    def get_backup_content(self, file_system='', backup_system_state=False):
        """Method to get backup content"""
        backup_content_panel = RPanelInfo(self.__admin_console, 'Backup content')
        if backup_content_panel.is_edit_visible():
            backup_content_panel.edit_tile()
        else:
            backup_content_panel.view_tile()
        result = self.__rbackup_content.get_content_details(
            file_system, backup_system_state)
        self.__rdialog.click_cancel()
        return result

    @WebAction()
    def get_override_restrictions(self):
        """Method to get details on override restrictions"""
        if 'Override restrictions' in self.plan_tiles():
            return RPanelInfo(self.__admin_console, 'Override restrictions').get_details()
        else:
            return {}

    @WebAction()
    def get_snapshot_options(self):
        """Method to get details on snapshot options"""
        return RPanelInfo(self.__admin_console, 'Snapshot options').get_details()

    @WebAction()
    def get_database_options(self):
        """Method to get details on database options"""
        return RPanelInfo(self.__admin_console, 'Database options').get_details()

    @PageService()
    def get_file_search_settings(self):
        """Method to get file search settings"""
        return RPanelInfo(self.__admin_console, 'Settings').get_details()

    @PageService()
    def get_applicable_solns(self):
        """Method to get applicable solns configured on plan"""
        solutions = RPanelInfo(
            self.__admin_console, 'Applicable solutions').get_details().get('Solutions')
        return solutions.split('\n') if solutions else []

    @PageService()
    def edit_applicable_solns(self, solutions: list) -> None:
        """Method to set applicable solns

        Args:
            solutions (list) : List of solutions, Pass Empty list to disable restriction
        """
        RPanelInfo(self.__admin_console, 'Applicable solutions').edit_tile()

        if solutions:
            self.__rdialog.toggle.enable(id='isRestricted')
            deselect_solutions = list(
                set(self.__rdropdown.get_values_of_drop_down('solutions')) - set(solutions))
            self.__rdropdown.select_drop_down_values(
                drop_down_id='solutions', values=solutions)
            self.__rdropdown.deselect_drop_down_values(
                deselect_solutions, 'solutions')
        else:
            self.__rdialog.toggle.disable(id='isRestricted')

        self.__rdialog.click_submit()

    @PageService()
    def edit_tags(self, values: dict, operation_type='ADD'):
        """Method to add new tags"""
        RPanelInfo(self.__admin_console, 'Tags').edit_tile()
        for tag_name, tag_value in values.items():
            if operation_type == 'ADD':
                self.__rtags.add_tag(tag_name, tag_value)
            elif operation_type == 'DELETE':
                self.__rtags.delete_tag(tag_name, tag_value)
            else:
                raise CVWebAutomationException(
                    'Invalid operation type passed as a parameter')

        self.__rdialog.click_submit()

    @PageService()
    def modify_tag(self, old_tag: tuple, new_tag: tuple):
        """Method to modify the Tag"""
        RPanelInfo(self.__admin_console, 'Tags').edit_tile()
        self.__rtags.modify_tag(old_tag, new_tag)
        self.__rdialog.click_submit()

    @WebAction()
    def get_associated_tags(self):
        """Method to get details on associated tags"""
        tags = RPanelInfo(self.__admin_console, 'Tags').get_details()
        if 'Tag name' in tags:
            tags.pop('Tag name')
        return tags

    @PageService()
    def is_advance_view_toggle_visible(self):
        """Method to check if advanced view toggle exists"""
        toggle_1 = self.__toggle.is_exists(id='metallicViewToggle')
        toggle_2 = self.__toggle.is_exists(id='serverPlanViewToggle')
        toggle_3 = self.__toggle.is_exists(id='laptopPlanViewToggle')
        return toggle_1 or toggle_2 or toggle_3

    @PageService()
    def is_plan_in_advanced_view(self):
        """Method to check if plan is in advanced or simplified view"""
        return True if len(self.plan_tiles()) > 3 else False

    @PageService()
    def enable_advanced_view(self):
        """Method to enable advanced view"""
        if self.__toggle.is_exists(id='metallicViewToggle'):
            self.__toggle.enable(id='metallicViewToggle')
        if self.__toggle.is_exists(id='laptopPlanViewToggle'):
            self.__toggle.enable(id='laptopPlanViewToggle')

    @PageService()
    def disable_advanced_view(self):
        """Method to disable advanced view"""
        if self.__toggle.is_exists(id='serverPlanViewToggle'):
            self.__toggle.disable(id='serverPlanViewToggle')
        if self.__toggle.is_exists(id='laptopPlanViewToggle'):
            self.__toggle.disable(id='laptopPlanViewToggle')

    @PageService()
    def edit_backup_window(self, backup_window: dict = None, full_backup_window: dict = None) -> None:
        """
            Method to edit the backup and full backup window

            backup_window   (dict)       :   key value pair of day and its blackout timings

            full_backup_window   (dict)  :   key value pair of day and its blackout timings

            Example:
                input = {
                    'Monday and Thursday' : ['All day'],
                    'Tuesday' : ['2am-6am', '1pm-6pm'],
                    'Tuesday through Thursday' : ['9pm-12am'],
                    'Wednesday' : ['5am-2pm'],
                    'Friday' : ['1am-3am', '5am-1pm'],
                    'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am'],
                    'Sunday' : ['1am-5am', '7am-1pm', '7pm-11pm']
                }
        """
        if backup_window:
            self.__rpo.click_on_edit_backup_window()
            self.__backup_window.edit_blackout_window(backup_window)
            self.__rdialog.click_submit()

        if full_backup_window:
            self.__rpo.click_on_edit_full_backup_window()
            self.__backup_window.edit_blackout_window(full_backup_window)
            self.__rdialog.click_submit()

    @PageService()
    def get_backup_window_labels(self) -> dict:
        """
            Method to get backup window labels

            Return example:
                label = {
                    'Backup window' : 'Run interval',
                    'Full backup window' : 'Do not run interval'
                }
        """
        self.__rpo.click_on_edit_backup_window()  # backup window labels
        backup_window = self.__backup_window.get_labels()
        self.__rdialog.click_cancel()

        self.__rpo.click_on_edit_full_backup_window()  # full backup window labels
        full_backup_window = self.__backup_window.get_labels()
        self.__rdialog.click_cancel()

        return {
            'Backup window': backup_window,
            'Full backup window': full_backup_window
        }

    @PageService()
    def get_configured_sla(self) -> str:
        """
            Method to get SLA string

            Example: "SLA period is 5 days"
        """
        return self.__rpo.get_sla()

    @PageService()
    def get_sla_exclude_reason(self) -> str:
        """Method to get SLA exclude reason"""
        self.__rpo.click_on_edit_sla()
        exclude_messsage = self.__sla.get_exclude_reason()
        self.__rdialog.click_cancel()
        return exclude_messsage

    @PageService()
    def use_system_default_sla(self) -> None:
        """Method to select system default SLA"""
        self.__rpo.click_on_edit_sla()
        self.__sla.use_system_default_sla()
        self.__rdialog.click_submit()

    @PageService()
    def set_sla_period(self, period: str = None, custom_days: int = None) -> None:
        """
            Method to select SLA period

            Args:
                period (str)        -   SLA period (e.g: 1 day / week / month)

                custom_days (int)   -   custom value for SLA in days
        """
        self.__rpo.click_on_edit_sla()
        self.__sla.select_sla_period(period, custom_days)
        self.__rdialog.click_submit()

    @PageService()
    def exclude_from_sla(self, reason: str = None) -> None:
        """
            Method to exclude SLA

            Args:
                reason (str)    -   Reason for exclusion
        """
        self.__rpo.click_on_edit_sla()
        self.__sla.exclude_sla(reason)
        self.__rdialog.click_submit()

    @PageService()
    def action_list_snaps(self, copy_name: str) -> None:

        """
        Lists the snaps on plan level with the given name

        Args :
            copy_name   (str)   --  the name of the copy whose snaps are to listed
        """
        ltable = Rtable(self.__admin_console, id="planBackupDestinationTable")
        ltable.access_action_item(copy_name, self.__admin_console.props['action.listSnaps'])

    @PageService()
    def delete_multiple_snaps_plan_level(self, job_id: str, copy_name: str) -> str:
        """
            Args:
                job_id(str) : job id
            Returns:
                  delete_job_id: job id of multiple delete snaps

            Note:Deleting multiple snaps at plan level with same jobid (if subclient has subclientcontent from Different volumes)
        """
        self.action_list_snaps(copy_name)
        self.__table.search_for(job_id)
        self.__table.apply_filter_over_column(column_name="Job ID", filter_term=job_id)
        self.__table.select_all_rows()
        self.__table.access_toolbar_menu("Delete")
        self.__rmodal_dialog.click_submit(wait=False)
        self.__admin_console.click_button_using_text('Yes')
        delete_job_id = self.__admin_console.get_jobid_from_popup()
        return delete_job_id

    @PageService()
    def run_offline_backup_copy(
            self,
            copy_name: str = "Primary snap",
    ):
        """
        Function to run a offline backupcopy job for a plan
           Args:
               copy_name (str): Name of the copy to backup
           Raises:
               Exception :
                -- if fails to run the offline backupcopy
        """
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_action_item(copy_name, self.__admin_console.props['action.backupCopy'])
        self.__admin_console.click_button_using_text("Yes")

    @PageService()
    def run_auxiliary_copy(self, copy_name=None) -> str:
        """
            Method to run auxiliary copy job
               Args:
                  copy_name (str): Name of the copy to run auxiliary copy job
               Raises:
                   Exception :
                    -- if fails to run auxiliary copy
               Returns:
                  jobid (str) : Job id for the auxiliary copy job
        """
        atable = Rtable(self.__admin_console, id="planBackupDestinationTable")
        atable.access_toolbar_menu("Run auxiliary copy")
        if copy_name is not None:
            self.__rdialog.select_radio_by_id(radio_id="runOnSelectedCopy")
            self.__rdialog.select_dropdown_values(drop_down_id="copyList", values=[copy_name])
        self.__admin_console.click_button_using_text("Submit")
    
    @PageService()
    def disassociate_plan(self, client_name: str, backupset_name: str = 'defaultBackupSet') -> None:
        """
        Method to disassociate plan from a client

        Args:
            client_name (str): Name of the client
            backupset_name (str): Name of the backupset
        """
        self.__page_container.select_tab('Associated entities')
        self.__table.access_action_item(entity_name=client_name, action_item='Edit association',
                                        second_entity=backupset_name)
        self.__admin_console.wait_for_completion()
        self.__rdialog.dropdown.select_drop_down_values(values=['None'], drop_down_id='plansDropdownplans')
        self.__rdialog.click_submit()

    @PageService()
    def edit_content_indexing_maxsize(self, size):
        """
            Edits content indexing maxsize setting
        """
        RPanelInfo(self.__admin_console, title='Search').edit_tile()
        self.__admin_console.fill_form_by_id("maxDocSize", size)
        self.__modal_panel.submit()

    @PageService()
    def change_source_for_backupcopy(self, copy_name):
        """
                Method to change source for backupcopy to a particular copy name under a plan
                Args:
                    copy_name (str): Name of the copy
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        otable = Rtable(self.__admin_console, id="planBackupDestinationTable")
        otable.access_link(copy_name)
        self.copydetails.change_source_for_backupcopy()

    @PageService()
    def enable_compliance_lock(self, copy) -> None:
        """
        Enable Compliance Lock for the Copy
        Args:
            copy (str) : Copy Name
    
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_link(copy)
        self.copydetails.enable_compliance_lock()

    @PageService() 
    def disable_compliance_lock(self, copy) -> None:
        """
        Disable Compliance Lock for the Copy
        Args:
            copy (str) : Copy Name
    
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_link(copy)
        self.copydetails.disable_compliance_lock()

    @PageService()    
    def delete_job_on_locked_copy(self, copy, jobid) -> None:
        """
        Method to verify delete job on the Compliance/Immutable locked Copy
        Args:
            copy (str) : Copy Name
            jobid (str) : Job ID
    
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_action_item(copy, self.__admin_console.props['label.globalActions.viewJobs'])
        notification_text = self.copydetails_jobs.delete_job_on_locked_copy(jobid)
        return notification_text
    
    @PageService()
    def enable_immutable_snap(self, copy) -> None:
        """
        Enable Immutable snap for the Copy
        Args:
            copy (str) : Copy Name
    
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_link(copy)
        self.copydetails.enable_immutable_snap()

    @PageService() 
    def disable_immutable_snap(self, copy) -> None:
        """
        Disable immutable snap for the Copy
        Args:
            copy (str) : Copy Name
    
        """
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id="planBackupDestinationTable")
        table.access_link(copy)
        self.copydetails.disable_immutable_snap()

    @PageService()
    def get_backup_destination_regions(self) -> list:
        """
        Method to get Backup destination regions associated to a plan

        returns:
            regions - list of region associated with the plan
        """
        self.__page_container.select_tab(self.__props['label.nav.storagePolicy'])
        data = Rtable(self.__admin_console, title="Regions").get_column_data('Region name')
        regions = [data[i] for i in range(len(data) - 1) if "Backup destinations" in data[i + 1]]
        return regions
