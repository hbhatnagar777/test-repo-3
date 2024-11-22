# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Tags page on the AdminConsole

Class:

    Tags() -> _Navigator() -> AdminConsoleBase() -> object

Tags:

    create_tagset()                      --  Create a tagset and tagset description in Tags
    action_delete_tagset()               --  Deletes the tagset with the given name
    action_add_tag()                     --  Adds tag to a tagset with the given tag name
    _get_tagsets                         --  Gets a list all the tag sets
    _select_tagset                       --  Selects the given tagset
    _select_tagset_action                --  Selects the action on the given Tag set
    _check_if_tagset_exists              --  Searches for given Tag set

EntityTags:

    is_tag_name_exists()                 --  Check if given tag name exist
    action_delete_entity_tag             --  Deletes the tag with the given name
    add                                  --  Creates an entity tag from Entity Tags page under Manage
"""
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog


class Tags:
    """ Class for the Tags page """

    def __init__(self, admin_console):
        """
        Method to initiate Tags class

        Args:
            admin_console (Object) :   admin console object
        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__tagset_Grid_Id = "tagsetTable"
        self.__rtable = Rtable(self.__admin_console, id=self.__tagset_Grid_Id)
        self.__rmodal = RModalDialog(self.__admin_console)

    @PageService()
    def create_tagset(self, tagset, desc=None):
        """ Creates a Tag Set

            Args:
                tagset (str) :   Name of the tagset to be created
                desc(str)    :   Description of the tagset

            """
            
        self.__rtable.access_toolbar_menu(self.__admin_console.props['label.tagset.add'])
        self.__admin_console.fill_form_by_name("tagsetName", tagset)
        self.__admin_console.fill_form_by_name("tagsetDescription", desc)
        self.__rmodal.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
    
    @PageService()
    def action_delete_tagset(self, tagset):
        """ Deletes the tagset with the given name
        
        Args:
            tagset (str)   :   the name of the tagset to be deleted
        """
        self.log.info("Searching for the tagset with name: %s", tagset)
        self.__rtable.access_action_item(tagset, self.__admin_console.props['label.action.delete'])
        self.__rmodal.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
    
    @PageService()
    def action_add_tag(self, tagset, tag):
        """ Adds tag to a tagset with the given tag name
        
        Args:
            tagset (str)    :   the name of the tagset
            tag (str)       :   the name of the tag to be added
        """
        self.__rtable.access_action_item(tagset, self.__admin_console.props['label.addTag'])
        self.__admin_console.fill_form_by_name("tagname", tag)
        self.__rmodal.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()   

    @PageService()
    def _get_tagsets(self):
        """ Gets a list all the tag sets
        
        Returns:
            (list)      :    a list of the tag sets
        """
        tagsets_dict = self.__rtable.get_table_data()
        self.log.info("The list of all tag sets is %s", str(tagsets_dict))
        return tagsets_dict

    @PageService()
    def _select_tagset(self, tagset):
        """ Selects the given Tag set
        
        Args:
            tagset (str)   :   the name of the tagset
        """
        self.__rtable.access_link(tagset)
    
    @PageService()
    def _select_tagset_action(self, tagset, action):
        """ Selects the action on the given Tag set
        
        Args:
            tagset (str)   :   the name of the tagset
            action (str)   :   the name of the action
        """
        self.__rtable.access_context_action_item(tagset, action)   
        
    @WebAction()
    def _check_if_tagset_exists(self, tagset):
        """ Searches for given Tag set
        
        Args:    
            tagset (str)   :   the name of the tagset
        Returns:
            (bool)        :    True/False based on presence of tagset
        """
        return self.__rtable.is_entity_present_in_column("Tagset", tagset)

class EntityTags:
    """ Class for the Entity tags page """

    def __init__(self, admin_console):
        """
        Method to initiate EntityTags class

        Args:
            admin_console (Object) :   admin console object
        """
        self._admin_console = admin_console
        self.__rtable = Rtable(self._admin_console)
        self.__modal_dialog = RModalDialog(self._admin_console)
        self.__page_container = PageContainer(self._admin_console)
        self._admin_console.load_properties(self)

    @PageService()
    def is_tag_name_exists(self, tagname):
        """
        Check if entity tag name exist

        Args:
            tagname (str)   :   the name of the tags to be deleted
        """
        return self.__rtable.is_entity_present_in_column('Tag name', tagname)

    @PageService()
    def action_delete_entity_tag(self, tagname):
        """ Deletes the entity tag with the given name

        Args:
            tagname (str)   :   tag name to be deleted
        """
        self.__rtable.access_action_item(
            tagname, self._admin_console.props['action.delete'])
        self._admin_console.check_error_message()

    @PageService()
    def add(self, name: str) -> None:
        """Creates an Entity Tag

        Args:
            name (str): tag name to create
        """
        self.__page_container.click_on_button_by_text(self._admin_console.props['label.tag.add'])
        self.__modal_dialog.fill_text_in_field(element_id='tagname', text=name)
        self.__modal_dialog.click_submit()
        self._admin_console.wait_for_completion()
