from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Entity Manager page.


Classes:

    EntityManager() ---> GovernanceApps() ---> object()

    ClassifierManager() ---> GovernanceApps() ---> object()


EntityManager  --  This class contains all the methods for action in Entity
    Manager page and is inherited by other classes to perform GDPR related actions

    Functions:

    _select_entity()                --  Selects the given entity
    _select_sensitivity             -- Selects the given sensitivity type
    _select_parent_entity           -- Selects the given parent entity
    _add_regex                      --    Adds the given Regex
    _clear_regex                    --     Clears all the existing Regex
    _add_keywords                   --     Keywords to be added
    _clear_keywords                 --     Clears all the existing Keywords
    select_entity                   --    Selects a given entity and raises exception if not found
    check_if_activate_entity_exists -- Checks if entity exists
    check_if_entity_is_enabled()    -- Returns True if enabled. False if Disabled
    entity_action()                 -- Enable/Disable/Delete the selected entity
    add_custom_entity()             -- Adds a regex or derived or Keywords based custom entity
    edit_entity()                   -- Edit a given entity and replace existing parameters with new parameters
    delete_entity()                 -- Deletes a given entity by name

ClassifierManager -- This class contains all the methods for classifier related operations

    Functions:

    create_classifier()         --      Creates classifier on the commcell

    delete_classifier()         --      deletes classifier from the commcell

    edit_classifier()           --      edits classifier on the commcell

    get_training_details()      --      returns training details for the given classifier

    get_training_status()       --      returns training status for the classifier from details page

    get_training_accuracy()     --      returns training accuracy for the classifier from details page

    get_info()                  --      returns general details related to classifier

    open_classifier_details()   --      Opens classifier details page for the given input

    start_training()            --      Starts training for the classifier

    cancel_training()           --      Cancels training for classifier in details page

    open_classifier_mgr_via_bread_crumb()   --  Opens classifier manager by clicking on breadcrumb
"""

import time
import re
from selenium.webdriver.common.keys import Keys

from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVWebAutomationException


class EntityManager(GovernanceApps):
    """
     This class contains all the methods for action in Entity Manager page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__dropdown = RDropDown(self.__admin_console)
        self.__panelinfo = RPanelInfo(self.__admin_console)

    @WebAction()
    def _select_entity(self, entity_name):
        """
        If entity exists, selects the entity and raises exception if entity doesn't exist

            :param entity_name    (str)   --  Name of the Entity
        """
        self.driver.find_element(
            By.XPATH, '//div/span[contains(@class,"MuiListItemText-primary") and text()="%s"]' % entity_name).click()

    @WebAction()
    def _select_sensitivity(self, sensitivity_type, edit=False):
        """
        Selects the given sensitivity type

            :param sensitivity_type    (str)   --  Type of the sensitivity
            Values:
                "Critical",
                "High",
                "Moderate"
        """
        sensitivity_type_dict = {
            'Critical':self.__admin_console.props['label.taskDetail.critical'],
            'High':self.__admin_console.props['label.taskDetail.high'],
            'Moderate':self.__admin_console.props['label.taskDetail.moderate']
            }
        self.__dropdown.select_drop_down_values(int(edit), [sensitivity_type_dict[sensitivity_type]])

    @WebAction()
    def _select_parent_entity(self, parent_entity):
        """
        Selects the given parent entity

            :param parent_entity    (str)   --  Parent entity name
        """
        self.__dropdown.select_drop_down_values(0, [parent_entity])

    @WebAction()
    def _add_entity(self, entity_name, add_type='Create'):
        """
        Selects the given sensitivity type

            :param sensitivity_type    (str)   --  Type of the sensitivity
            Values:
                "Create",
                "Import"
        Raises:
            Exception:
                -- if unknown add type is passed
        """
        if re.search(add_type, 'Create', re.IGNORECASE):
            add_type = 'Create entity'
        elif re.search(add_type, 'Import', re.IGNORECASE):
            add_type = 'Import entity'
        else:
            raise CVWebAutomationException('Unexpected type: %s' % add_type)
        self.__admin_console.click_button_using_text("Add entity")
        self.__admin_console.click_button_using_text(add_type)
        self.log.info("Entering Entity name")
        self.__admin_console.fill_form_by_name("entityName", entity_name)

    @WebAction()
    def _add_regex(self, python_regex, sleep_time=10):
        """
        Adds the given regex

            :param python_regex    (str)   --  Regex to be added
            :param sleep_time    (int)   --  Time in seconds to sleep after regex addition
        """
        self.driver.find_element(By.XPATH, '//textarea').clear()
        self.driver.find_element(By.XPATH, '//textarea').send_keys(python_regex)
        self.__admin_console.wait_for_completion()
        time.sleep(sleep_time)

    @WebAction()
    def _clear_regex(self, sleep_time=10):
        """
        Clears all the existing regex

            :param sleep_time    (int)   --  Time in seconds to sleep after regex addition
        """
        self.driver.find_element(By.XPATH, '//textarea').clear()
        self.__admin_console.wait_for_completion()
        time.sleep(sleep_time)

    @WebAction()
    def _add_keywords(self, keywords, edit=False):
        """
        Adds the given keywords

            :param keywords    (str)   --  Keywords to be added
        """
        self.log.info("Entering Keywords")
        key_id = 'customKeywords'
        if edit:
            key_id = 'entityKeywords'
        self.driver.find_element(By.ID, key_id).clear()
        for keyword in keywords:
            self.driver.find_element(By.ID, key_id).send_keys(keyword)
            self.__admin_console.wait_for_completion()
            self.driver.find_element(By.ID, key_id).send_keys(Keys.ENTER)
            self.__admin_console.wait_for_completion()

    @WebAction()
    def _clear_keywords(self, edit=False):
        """
        Clears all of the existing keywords
        """
        key_id = 'customKeywords'
        if edit:
            key_id = 'entityKeywords'
        existing_keywords = self.driver.find_elements(By.XPATH,
                                                      f'//*[@id={key_id}]/span')
        self.log.info(
            "Number of existing keywords: {}".format(
                len(existing_keywords)))
        self.log.info("Clearing existing keywords")
        for count in range(len(existing_keywords)):
            self.driver.find_element(By.ID, key_id).send_keys(Keys.BACKSPACE)
            self.__admin_console.wait_for_completion()

    @PageService()
    def select_entity(self, entity_name):
        """
        If entity exists, selects the entity and raises exception if entity doesn't exist

            :param entity_name    (str)   --  Name of the Entity
        """
        self.driver.find_element(By.ID, "entityListSearchInput").send_keys(u'\ue009' + 'a' + u'\ue003')
        self.driver.find_element(By.ID, "entityListSearchInput").send_keys(entity_name)
        if self.__admin_console.check_if_entity_exists(
                "xpath", '//div/span[contains(@class,"MuiListItemText-primary") and text()="%s"]' % entity_name):
            self._select_entity(entity_name)
            self.__admin_console.wait_for_completion()
        else:
            raise CVWebAutomationException("Entity {0} is not present".format(entity_name))

    @PageService()
    def check_if_activate_entity_exists(self, entity_name):
        """
        Returns True if exists, False if not.

            :param entity_name    (str)   --  Name of the Entity
        """
        if self.__admin_console.check_if_entity_exists(
                "xpath", '//div/span[contains(@class,"MuiListItemText-primary") and text()="%s"]' % entity_name):
            return True
        return False

    @PageService()
    def check_if_entity_is_enabled(self, entity_name):
        """
        Returns True if enabled. False if Disabled

            :param entity_name    (str)   --  Name of the Entity
        """
        self.select_entity(entity_name)
        state = self.__dropdown.get_selected_values(drop_down_id="filterDropdown_state", expand=False)
        return "Enabled" in state

    @PageService()
    def entity_action(self, entity_name, action="Enable"):
        """
        Enable/Disable/Delete/Edit the selected entity

            :param entity_name    (str)   --  Name of the Entity
            :param action    (str)   --  Action to be performed on the Entity
                Valid values are:
                    Enable
                    Disable
                    Delete
                    Edit
            Raise:
                Exception if Entity not found
        """
        if action == 'Enable' and self.check_if_entity_is_enabled(entity_name):
            self.log.info("Entity '{0}' already enabled".format(entity_name))
        elif action == 'Disable' and not self.check_if_entity_is_enabled(entity_name):
            self.log.info("Entity '{0}' already disabled".format(entity_name))
        else:
            self.select_entity(entity_name)
            self.__admin_console.click_button_using_text("Actions")
            self.__admin_console.click_button(action)
            if action != 'Edit':
                self.__admin_console.wait_for_completion()
                self.__panelinfo.click_button("Yes")

    @PageService()
    def add_custom_entity(
            self,
            entity_name,
            sensitivity,
            python_regex=None,
            parent_entity=None,
            keywords=None):
        """
        Adds a regex or derived or Keywords based custom entity

            :param entity_name    (str)   --  Entity name to be added
            :param sensitivity    (str)  -- sensitivity to be selected
            :param python_regex    (str)  -- Python regular expression to be added
            :param parent_entity    (str)  -- Parent entity to be selected from the dropdown
            :param keywords    (list)  -- list of keywords to be added

            Raise:
                Exception if entity addition failed
        """
        self._add_entity(entity_name)
        if python_regex is not None:
            self._add_regex(python_regex)
        elif parent_entity is not None:
            self._select_parent_entity(parent_entity)
        if keywords:
            self._add_keywords(keywords)
        self._select_sensitivity(sensitivity)
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_entity(
            self,
            entity_name,
            old_entity_type,
            sensitivity=None,
            python_regex=None,
            parent_entity=None,
            keywords=None,
            clear_existing_keywords=True):
        """
        Edit a given entity and replace existing parameters with new parameters

            :param entity_name    (str)   --  Entity name of the old_entity that will be edited
            :param old_entity_type     (str)    -- Takes input 'derived' or 'regex_based'
                                                    or 'system' to define type of old_entity
                                                    that will be edited
            :param old_entity_keyword_count    (int) -- number of keywords in the old_entity
                                                    that will be edited.
            :param python_regex    (str)  -- Python regular expression of new_entity to be
                                                used to edit
            :param parent_entity    (str)  -- Parent entity of new_entity to be used to edit
            :param sensitivity    (str)  -- sensitivity of new_entity to edit
            :param keywords    (list)  -- list of keywords of new_entity to edit
            clear_existing_keywords    (bool)    -- Clears the existing keywords if True

            Raise:
                Exception if entity addition failed
        """
        self.log.info("Select Entity and click Edit")
        self.entity_action(entity_name, action="Edit")
        self.__admin_console.wait_for_completion()
        self.log.info(
            "Make changes in entity. Old_entity type is: %s" %
            old_entity_type)
        if python_regex is not None:
            if old_entity_type == 'derived':
                self.log.info(
                    "Old_entity is a derived entity but new_entity is regex based.\
                    So clearing parent_entity from dropdown")
                self._select_parent_entity("Select entity")
            self._add_regex(python_regex)
        if parent_entity is not None:
            self._select_parent_entity(parent_entity)
        if python_regex is None and parent_entity is None:
            if old_entity_type == 'derived':
                self.log.info(
                    "Old_entity is a derived entity but new_entity is keyword based.\
                    So clearing parent_entity from dropdown")
                self._select_parent_entity("Select entity")
            elif old_entity_type == 'regex_based':
                self.log.info(
                    "Old_entity is a regex entity but new_entity is keyword based.\
                    So clearing regex")
                self._clear_regex()
        if clear_existing_keywords:
            self._clear_keywords(edit=True)
        if keywords:
            self._add_keywords(keywords, edit=True)
        if sensitivity is not None:
            self._select_sensitivity(sensitivity, edit=old_entity_type=='derived')
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_entity(self, entity_name):
        """
        Deletes a given entity by name

            :param entity_name    (str)   --  Name of the Entity
            Raise:
                Exception if Entity not found
                Exception if Entity deletion fails
        """
        if not self.check_if_activate_entity_exists(entity_name):
            raise Exception("Entity doesn't exist for the current logged in user")
        self.entity_action(entity_name, action="Delete")
        self.__admin_console.check_error_message()


class ClassifierManager(GovernanceApps):
    """
     This class contains all the methods for action in classifier manager page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(admin_console)
        self.__dropdown = RDropDown(admin_console)
        self.__training_panel = RPanelInfo(admin_console, self.__admin_console.props['label.training'])
        self.__general_panel = RPanelInfo(admin_console, self.__admin_console.props['header.general'])

    @WebAction()
    def __click_add_classifier(self):
        """clicks on add classifier on table"""
        self.__table.access_toolbar_menu(self.__admin_console.props['label.classifiermanager.add'])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __set_description(self, desc):
        """Sets description for the classifier
            Args:
                desc        (str)       --  Description for this entity
        """
        text_area_element = self.driver.find_element(By.XPATH, '//textarea')
        text_area_element.clear()
        text_area_element.send_keys(desc)

    @WebAction()
    def __upload_file(self, file_path):
        """Uploads modal data zip file to classifier
            Args:
                file_path       (str)   :   Zip file path
        """
        upload = self.driver.find_element(By.XPATH, "//input[contains(@id,'sampleDocs')]")
        upload.send_keys(file_path)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __get_training_details(self):
        """Returns the training details for this classifier"""
        self.log.info("Going to fetch training details")
        retry = 20
        details = None
        while retry > 0:
            try:
                details = self.__training_panel.get_details()
                break
            except Exception:
                time.sleep(30)
                retry = retry - 1
        if not details:
            raise CVWebAutomationException("Fetching Classifier training details failed")
        return details

    @WebAction()
    def __get_classifier_info(self):
        """Returns the training details for this classifier"""
        return self.__general_panel.get_details()

    @WebAction()
    def __open_classifier_details(self, name):
        """opens the details pahge of the given classifier"""
        self.__table.access_action_item(name, action_item=self.__admin_console.props['label.details'])

    @WebAction()
    def get_training_status(self):
        """returns the training status"""
        return self.__get_training_details()[self.__admin_console.props['label.status']]

    @WebAction()
    def get_training_accuracy(self):
        """returns the training accuracy"""
        return self.__get_training_details()[self.__admin_console.props['label.classifier.accuracy']]

    @WebAction()
    def __set_classifier_name(self, name):
        """Sets classifier name on the form"""
        self.__admin_console.fill_form_by_name('entityName', name)

    @WebAction()
    def __unset_table_search_word(self):
        """Removes the keyword set on table search bar"""
        # remove the search filter
        self.__table.search_for(" ")
        self.__admin_console.wait_for_completion()

    @WebAction()
    def cancel_training(self):
        """cancels the training on the classifier details page"""
        self.__training_panel.open_hyperlink_on_tile(
            self.__admin_console.props['label.classifier.cancelTraining'])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def open_classifier_mgr_via_bread_crumb(self):
        """Opens classifier manager home page by clicking on bread crum at top"""
        self.__admin_console.select_breadcrumb_link_using_text(self.__admin_console.props['label.classifiermanager'])

    @PageService()
    def create_classifier(self, name, content_analyzer, model_zip_file_path, desc=None):
        """ Create classifier with given name and model data file

            Args:

                name                (str)       --  Name of the classifier

                desc                (str)       --  Description for this entity (if any)

                content_analyzer    (str)       --  Name of the content analyzer cloud

                model_zip_file_path (str)       --  Zip file path which needs to be trained

            Raises:

                    Exception:

                        if failed to create classifier

        """
        self.log.info("Going to create classifier with name : %s", name)
        self.__click_add_classifier()
        self.__set_classifier_name(name)
        self.log.info("Selecting Content Analyzer : %s", content_analyzer)
        self.__dropdown.select_drop_down_values(0, [content_analyzer])
        if desc:
            self.log.info("Setting description for clasifier")
            self.__set_description(desc)
        self.log.info("Click next on form")
        self.__admin_console.button_next()
        self.__admin_console.wait_for_completion()
        self.log.info("Uploading file : %s", model_zip_file_path)
        self.__upload_file(model_zip_file_path)
        self.log.info("Click next on form")
        self.__admin_console.submit_form()
        self.log.info("Click Finish on form")
        self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_training_details(self, classifier_name):
        """returns the training details for the given classifier
            Args:
                classifier_name     (str)       --  Name of the classifier

            Returns:
                dict        --  containing all training details of the classifier

        """
        self.log.info("Opening details page for classifier : %s", classifier_name)
        self.__open_classifier_details(classifier_name)
        self.log.info("Going to fetch training details")
        details = self.__get_training_details()
        # go back to classifier manager home page
        self.open_classifier_mgr_via_bread_crumb()
        return details

    @PageService()
    def open_classifier_details(self, classifier_name):
        """opens the details pahge of the given classifier
            Args:
                classifier_name     (str)   --  Name of the classifier
        """
        self.__open_classifier_details(classifier_name)

    @PageService()
    def get_info(self, classifier_name):
        """returns the general details for the given classifier
            Args:
                classifier_name     (str)       --  Name of the classifier

            Returns:
                dict        --  containing all training details of the classifier

        """
        self.log.info("Opening details page for classifier : %s", classifier_name)
        self.__open_classifier_details(classifier_name)
        self.log.info("Going to fetch training details")
        details = self.__get_classifier_info()
        # go back to classifier manager home page
        self.open_classifier_mgr_via_bread_crumb()
        return details

    @PageService()
    def delete_classifier(self, name):
        """Deletes the given classifier
            Args:
                name        (str)       :   Name of the classifier

            Returns:
                Exception:
                    if failed to delete the classifier
        """
        self.log.info("Deleting the classifier : %s", name)
        self.__table.access_action_item(name, action_item=self.__admin_console.props['action.delete'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button_using_text('Yes')
        self.__admin_console.wait_for_completion()
        time.sleep(5)
        self.log.info("Recheck whether entry exists in table")
        if self.__table.is_entity_present_in_column(self.__admin_console.props['label.name'], name):
            raise Exception("Classifier exists even after deletion")
        self.log.info("Classifier got deleted!!!")
        self.__unset_table_search_word()

    @PageService()
    def edit_classifier(self, name, new_name=None, desc=None):
        """ Edits classifier with given name and description

                   Args:

                       name                (str)       --  Name of the classifier

                       new_name            (str)       --   New name for the classifier

                       desc                (str)       --  Description for this entity (if any)


                   Raises:

                           Exception:

                               if failed to edit classifier

        """
        self.log.info("Going to open classifier details : %s", name)
        self.__open_classifier_details(name)
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button_using_id("tile-action-btn")
        self.__admin_console.wait_for_completion()
        if desc:
            self.__set_description(desc)
        self.__admin_console.click_button_using_text('Save')
        self.__admin_console.wait_for_completion()
        self.log.info("Editing classifier completed")

    @PageService()
    def enable_or_disable_classifier(self, name, enable=True):
        """Enables or disables the classifier on the commcell
            Args:

                name            (str)       --      Name of the classifier

                enable          (bool)      --      Bool to specify whether to enable ot disable classifier

            Raises:

                           Exception:

                               if failed to enable/disable classifier

        """
        self.log.info("Going to enable/disable classifier details : %s", name)
        self.__open_classifier_details(name)
        self.__admin_console.wait_for_completion()
        if enable:
            self.log.info("Enabling classifier")
            self.__general_panel.open_hyperlink_on_tile(self.__admin_console.props['label.enable'])
        else:
            self.log.info("Disabling classifier")
            self.__general_panel.open_hyperlink_on_tile(self.__admin_console.props['label.disable'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button_using_text('Yes')
        self.__admin_console.wait_for_completion()
        # go back to classifier manager home page
        self.open_classifier_mgr_via_bread_crumb()

    @PageService()
    def start_training(self, name, file_path):
        """Starts training for the classifier after uploading new model data

            Args:

                file_path           (str)       --  Zip path containing training documents

                name                (str)       --  Classifier name
        """
        self.log.info("Going to Upload new documents for training in classifier details for : %s", name)
        self.__open_classifier_details(name)
        self.__admin_console.wait_for_completion()
        self.__upload_file(file_path=file_path)
        self.__admin_console.click_button_using_text('No')
        self.__admin_console.wait_for_completion()
        self.__training_panel.open_hyperlink_on_tile(
            self.__admin_console.props['header.classifiermanager.startTraining'])
        self.__admin_console.wait_for_completion()
