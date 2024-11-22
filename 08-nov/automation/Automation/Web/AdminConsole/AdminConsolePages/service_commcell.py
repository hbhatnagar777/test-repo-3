# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Service CommCell page on the AdminConsole

Class:

    ServiceCommcell()

Functions:

    _init_()                            :   initialize the class object

    __select_service_commcell_tile()    :   selects the service commcell tile on the systems page

    register_commcell()                 :   registers a new service commcell

    delete_registered_commcell()        :   unregisters a service commcell

    refresh_registered_commcell()       :   synchronize a service commcell

    select_service_commcell()           :   Selects the given commcell
    
    _click_edit_associations()          :   Clicks on Edit associations hyperlink
    
    _confirm_associations()             :   Clicks on Save to confirm the associations
    
    associate_entities()                :   Associates given list of Company or User Group or User
                                            to the service commcell
    
    dissociate_entities()               :   Dissociates given list of Company or User Group
                                            or User to the service commcell
    
    add_entity_association()            :   Associates the entity to given commcells

    delete_entity_association()         :   Deletes all associations for given entity

    get_user_suggestions()              :   Gets the list of suggestions for given entity

    get_service_commcell_associations() :   Gets associations listed for given entity/all entities

    get_service_commcells_listed()      :   Gets the commcells names available for association

"""
import time

from selenium.webdriver.common.by import By
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.panel import RModalPanel
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.dialog import ServiceCommcellAssociationsDialog, RModalDialog, Form


class ServiceCommcell:
    """ Class for Service Commcell page in Admin Console """

    def __init__(self, admin_console: AdminConsole):
        """
        Method to initiate ServiceComcell class

        Args:
            admin_console   (Object) :   Admin Console Class object
        """
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__log = admin_console.log
        self.__driver = admin_console.driver
        self.__admin_console.load_properties(self)
        self.__panel = RPanelInfo(self.__admin_console)
        self.__toggle = Toggle(self.__admin_console)
        self.__associations_dialog = ServiceCommcellAssociationsDialog(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__form = Form(self.__admin_console)

    @PageService()
    def register_commcell(self, hostname, username, password, configure_as_IdP):
        """
        Function to add a new service commcell

        Args    :

        hostname (string)   :   hostname of the commcell to be registered

        username (string)   :   username of the commcell to be registered

        password (string)   :   password of the commcell to be registered

        configure_as_IdP(bool): True - Register service commcell for Jupiter

                                False - Register service commcell for Router
        """
        self.__table.access_toolbar_menu('Add')
        self.__form.select_radio_by_value(radio_value=["WEBSERVICEOPTION", "GLOBALCC"][int(configure_as_IdP)])
        self.__form.click_submit() # Clicking on Next button

        self.__form.fill_text_in_field('hostName', hostname)
        self.__form.fill_text_in_field('userName', username)
        self.__form.fill_text_in_field('password', password)

        self.__form.click_add()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_registered_commcell(self, hostname, force=False):
        """
        Function to delete a registered commcell

        Args    :

            hostname (string)   :   hostname of the commcell to be un-registered
            force   (bool)      :
        """
        self.__table.access_action_item(hostname, 'Delete')

        if force:
            self.__rdialog.toggle.enable(label="Force unregister")
        else:
            self.__rdialog.toggle.disable(label="Force unregister")
        
        self.__rdialog.click_yes_button()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def refresh_registered_commcell(self, hostname):
        """
        Function to delete a registered commcell

        Args    :

        hostname (string)   :   hostname of the commcell to be synchronized
        """
        self.__table.access_action_item(hostname, 'Refresh')
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def is_service_commcell_exists(self, commcell_name: str) -> bool:
        """
        Checks if the given service commcell exists in the table

        Args:
            commcell_name (str) : name of the service commcell

        Returns:
            bool    :   True if exists, False otherwise
        """
        return self.__table.is_entity_present_in_column('Name', commcell_name)

    @PageService()
    def select_service_commcell(self, commcell_name):
        """Selects the given commcell"""
        self.__table.access_link(commcell_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_service_commcells(self) -> list:
        """Gets the service commcells table data"""
        return self.__table.get_column_data('Name', fetch_all=True)

    @PageService()
    def get_service_commcell_details(self, commcell_name: str):
        """Gets the service commcell details"""
        return self.__table.get_rows_data(search=commcell_name, id_column='Name')

    @PageService()
    def get_service_commcell_sync_status(self, commcell_name: str):
        """Gets the service commcell sync status"""
        return self.get_service_commcell_details(commcell_name)[1][commcell_name]['Sync status']

    @WebAction()
    def _click_edit_associations(self):
        """Clicks on Edit associations hyperlink"""
        self.__panel.open_hyperlink_on_tile(
            self.__admin_console.props['label.globalActions.editClientGroupAssociations'])

    @WebAction()
    def _confirm_associations(self):
        """Clicks on Save to confirm the associations"""
        save_text = self.__admin_console.props['action.save']
        self.__admin_console.click_by_xpath(
            f"//*[@class='button-container']/div[contains(text(),'{save_text}')]")

    @PageService()
    def associate_entities(self, entities):
        """
        Associates given list of Company or User Group or User to the service commcell
        Args:
            entities (list)   :   List of entities Company/User Group/User
        """
        self._click_edit_associations()
        for entity in entities:
            self.__admin_console.fill_form_by_name('searchComponent', entity)
            time.sleep(10)
            self.__admin_console.click_by_xpath(
                f"//*[@class='result-item']//*[contains(text(),'{entity}')]")
            self.__modal_panel.submit()
        self._confirm_associations()

    @PageService()
    def dissociate_entities(self, entities):
        """
        Dissociates given list of Company or User Group or User to the service commcell
        Args:
            entities (list)   :   List of entities Company/User Group/User
        """
        self._click_edit_associations()
        orig_xp = self.__table._xp
        # Changing the view of the table as dissociation has same table with different id
        self.__table._xp = (orig_xp[:-1] + " and @id='multiCommcellAssociationList'" + orig_xp[-1])
        for entity in entities:
            self.__table.access_context_action_item(
                entity, self.__admin_console.props['label.globalActions.delete'])
        self._confirm_associations()
        self.__table._xp = orig_xp  # Changing it back to original

    @WebAction()
    def _open_associations(self):
        """Clicks on Associations hyperlink"""
        if not self.__associations_dialog.is_dialog_present():
            self.__table.access_toolbar_menu('Associations')
            self.__admin_console.wait_for_completion()

    @PageService()
    def add_entity_association(self, entity, commcells):
        """
        Associates the entity to given commcells
        
        Args:
            entity  (str)   -   name of entity
            commcells   (list)  -   list of commcells to associate to
        """
        self._open_associations()
        self.__associations_dialog.add_association(entity, commcells)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_entity_association(self, entity):
        """
        Deletes the entity association to all commcells
        
        Args:
            entity  (str)   -   name of entity
        """
        self._open_associations()
        self.__associations_dialog.delete_association(entity)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def get_user_suggestions(self, entity, pages=1):
        """
        Gets the entity suggestions in associations dialog after searching term
        
        Args:
            entity  (str)   -   name of entity
            pages   (int)   -   number of pages of suggestions to read

        Returns:
            list[str]   -   list of suggestions
        """
        self._open_associations()
        return self.__associations_dialog.get_user_suggestions(entity, pages=pages)

    @PageService()
    def get_service_commcell_associations(self, entity=None, all_pages=False):
        """
        Gets the associations listed
        
        Args:
            entity  (str)   -   name of entity
            all_pages   (bool)  -   will read all pages if True
        
        Returns:
            dict    -   dictionary with associations table column data
        """
        self._open_associations()
        return self.__associations_dialog.get_associations(entity, all_pages)

    @PageService()
    def get_service_commcells_listed(self):
        """
        Gets the service commcells available for associations
        
        Returns:
            list[str]   -   list of commcell names
        """
        self._open_associations()
        return self.__associations_dialog.available_commcells()
