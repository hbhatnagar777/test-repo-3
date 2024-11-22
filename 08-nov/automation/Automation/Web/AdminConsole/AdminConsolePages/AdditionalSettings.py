# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Additional Settings page on the AdminConsole

Class:

    AdditionalSettings()

Functions:

_init_()                                :     initialize the class object
add_commcell_setting()                  :     Method to add a predefined commcell setting
add_commcell_custom_setting()           :     Method to add a custom commcell setting
delete_commcell_additional_setting()    :     Method to delete a commcell setting
edit_commcell_setting()                 :     Method to edit a predefined commcell setting
edit_commcell_custom_setting()          :     Method to edit a custom commcell setting
is_key_exist()                          :     Method to find whether a commcell key exists
get_key_values                          :     Method to find the values of an added key

"""

from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.panel import RModalPanel, RDropDown


class AdditionalSettings:
    """ Class for Additional Settings page in Admin Console """

    def __init__(self, admin_console):
        """
        Method to initiate AdditionalSettings class

        Args:
            admin_console   (Object) :   AdminConsole Class object
        """
        self.__admin_console = admin_console
        self.__rtable = Rtable(self.__admin_console)
        self.__driver = admin_console.driver
        self.__drop_down = DropDown(self.__admin_console)
        self.__rdrop_down = RDropDown(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)

    @PageService()
    def add_commcell_setting(self,
                             setting_name,
                             value,
                             comment,
                             isBooleanKey=False):
        """ Method to add a predefined commcell setting

            Args:
                setting_name:   name of the commcell additional setting to be added
                value:          value of the commcell additional setting to be added
                comment:        comment for the commcell additional setting to be added
                isBooleanKey:   whether the commcell addtional setting to be added is a boolean key

            Raises:
                Exception:
                    -- if fails to add commcell setting
        """

        xpath = "//form[contains(@class, 'form-wrapper')]"
        self.__rdialog = RModalDialog(self.__admin_console, xpath=xpath)

        self.__rtable.access_toolbar_menu(self.__admin_console.props['label.add'])
        self.__rtable.access_menu_from_dropdown('CommCell settings')

        self.__rdrop_down.search_and_select(select_value=setting_name, id='additionalSettingName')

        if isBooleanKey:
            self.__rdialog.select_dropdown_values(drop_down_id='settingValue', values=[value])
        else:
            self.__rdialog.fill_text_in_field('settingValue', value)

        self.__rdialog.fill_text_in_field('settingValueComment', comment)

        self.__modal_panel.submit()
        self.__rdialog = RModalDialog(self.__admin_console, xpath=" ")
        self.__rdialog.click_submit()

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def add_commcell_custom_setting(self,
                                    setting_name,
                                    value,
                                    comment,
                                    valueType,
                                    category):
        """ Method to add new commcell custom setting

            Args:
                setting_name:   name of the commcell custom additional setting to be added
                value:          value of the commcell custom additional setting to be added
                comment:        comment for the commcell custom additional setting to be added
                valueType:      value type of the commcell custom key. Integer, String or Boolean
                Category:       category under which the commcell custom key has to be added

            Raises:
                Exception:
                    -- if fails to add commcell setting
        """

        xpath = "//form[contains(@class, 'form-wrapper')]"
        self.__rdialog = RModalDialog(self.__admin_console, xpath=xpath)

        self.__rtable.access_toolbar_menu(self.__admin_console.props['label.add'])
        self.__rtable.access_menu_from_dropdown('CommCell settings')

        self.__rdrop_down.search_and_select(select_value=setting_name, id='additionalSettingName')

        self.__rdrop_down.search_and_select(category, 'Category')

        if valueType == "Boolean":
            self.__rdialog.select_dropdown_values(drop_down_id='customTypeName', values=['Boolean'])
            self.__rdialog.select_dropdown_values(drop_down_id='settingValue', values=[value])
        else:
            self.__rdialog.select_dropdown_values(drop_down_id='customTypeName', values=[valueType])
            self.__rdialog.fill_text_in_field('settingValue', value)

        self.__rdialog.fill_text_in_field('settingValueComment', comment)

        self.__modal_panel.submit()
        self.__rdialog = RModalDialog(self.__admin_console, xpath=" ")
        self.__rdialog.click_submit()

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_commcell_additional_setting(self,
                                           setting_name):
        """ Method to delete a commcell setting

            Args:
                setting_name:   name of the commcell additional setting to be deleted

            Raises:
                Exception:
                    -- if fails to delete commcell setting
        """
        if not self.__rtable.is_entity_present_in_column('Name', setting_name):
            raise Exception('Commcell key not present. Add the key first before trying deletion')

        self.__rtable.access_action_item(setting_name, 'Delete')

        self.__rdialog = RModalDialog(self.__admin_console, xpath=" ")
        self.__rdialog.click_submit()

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        self.__admin_console.refresh_page()

    @PageService()
    def edit_commcell_setting(self,
                              setting_name,
                              value,
                              comment,
                              isBooleanKey=False):
        """ Method to edit a predefined commcell setting

            Args:
                setting_name:   name of the commcell additional setting to be edited
                value:          value of the commcell additional setting to be added
                comment:        comment for the commcell additional setting to be added
                isBooleanKey:   whether the commcell addtional setting to be edited is a boolean key

            Raises:
                Exception:
                    -- if fails to edit commcell setting
        """

        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rtable.access_action_item(setting_name, 'Edit')
        if isBooleanKey:
            self.__rdialog.select_dropdown_values(drop_down_id='settingValue', values=[value])
        else:
            self.__rdialog.fill_text_in_field('settingValue', value)

        self.__rdialog.fill_text_in_field('settingValueComment', comment)

        self.__rdialog = RModalDialog(self.__admin_console,xpath=" ")
        self.__rdialog.click_submit()
        self.__rdialog.click_submit()

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_commcell_custom_setting(self,
                                     setting_name,
                                     value,
                                     comment,
                                     valueType,
                                     category):
        """ Method to edit a custom commcell setting

            Args:
                setting_name:   name of the commcell custom additional setting to be edited
                value:          value of the commcell custom additional setting to be edited
                comment:        comment for the commcell custom additional setting to be edited
                valueType:      value type of the commcell custom key. Integer, String or Boolean
                Category:       category under which the commcell custom key has to be edited

            Returns:
                The added key's values

            Raises:
                Exception:
                    -- if fails to edit commcell setting
        """

        xpath = "//form[contains(@id, 'editSettingForm')]"
        self.__rdialog = RModalDialog(self.__admin_console)

        self.__rtable.access_link(setting_name)

        if valueType == "Boolean":
            self.__rdialog.select_dropdown_values(drop_down_id='settingValue', values=[value])
        else:
            self.__rdialog.fill_text_in_field('settingValue', value)

        self.__rdialog.fill_text_in_field('settingValueComment', comment)
        self.__rdialog = RModalDialog(self.__admin_console, xpath=" ")
        self.__rdialog.click_submit()
        self.__rdialog.click_submit()

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def is_key_exist(self,
                     column_name,
                     setting_name):
        """ Method to find whether a commcell key exists

            Args:
                column_name         --  Name of column to use to check whether the key is already present
                setting_name        --  Name of the commcell custom additional setting to be edited

            Returns:
                True if the key exists. False if the key doesn't

            Raises:
                Exception:
                    -- if fails to search for the key
        """

        return self.__rtable.is_entity_present_in_column(column_name, setting_name)

    @PageService()
    def get_key_values(self,
                       setting_name):
        """ Method to find the values of an added key 

            Args:
                setting_name        --  Name of the commcell key to be searched and find it's values

            Returns:
                values of the searched keys

            Raises:
                Exception:
                    -- if fails to search or get the values for the key
        """
        self.__admin_console.refresh_page()
        self.__rtable.search_for(setting_name)
        return self.__rtable.get_table_data()