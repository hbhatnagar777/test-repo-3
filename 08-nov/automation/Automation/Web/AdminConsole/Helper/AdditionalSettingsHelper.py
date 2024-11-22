# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to add, edit
additional settings

Class:

    AdditionalSettingsHelper()

Functions:

    add_predefined_commcell_key()   :   Method to add and verify predefined commcell setting

    add_custom_commcell_key()       :   Method to add and verify custom commcell setting

    edit_predefined_commcell_key()  :   Method to edit and verify predefined commcell setting

    edit_custom_commcell_key()      :   Method to edit and verify custom commcell setting

"""

from AutomationUtils import logger
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.AdminConsolePages.AdditionalSettings import AdditionalSettings


class AdditionalSettingsHelper:
    """
        Helper for Additional Settings page
    """

    def __init__(self, admin_console):
        """
            Initializes the Additional Settings helper module

            Args:
                admin_console  (object)   --  AdminConsole class object

        """

        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__rtable = Rtable(self.__admin_console)
        self.__additional_settings = AdditionalSettings(self.__admin_console)

        self.log = logger.get_log()

    def add_predefined_commcell_key(self,
                                        column=None,
                                        key_name=None,
                                        key_value=None,
                                        key_comment=None,
                                        key_isBooleanKey=False):
        """ Method to add and verify predefined commcell setting

            Args:
                column              --  Name of column to use to check whether the key is already present
                key_name            --  Name of the key to add
                key_value           --  Value of the key to add
                key_comment         --  Key's comment
                key_isBooleanKey    --  Whether the key is boolean type (True/False)

            Raises:
                Exception:
                    -- if fails to add commcell setting

        """

        if self.__additional_settings.is_key_exist(column, key_name):
            raise Exception('Pre-defined Commcell key is already present')

        self.__additional_settings.add_commcell_setting(setting_name=key_name,
                                                        value=key_value,
                                                        comment=key_comment,
                                                        isBooleanKey=key_isBooleanKey)
                                                        
        data = self.__additional_settings.get_key_values(key_name)

        if not (data['Name'][0] == key_name
                and data['Value'][0] == key_value
                and data['Comment'][0] == key_comment):
            raise Exception('Pre-defined Commcell key values dont match')

    def add_custom_commcell_key(self,
                                column=None,
                                key_name=None,
                                key_value=None,
                                key_comment=None,
                                key_valueType=None,
                                key_category=None):
        """ Method to add and verify custom commcell setting

            Args:
                column              --  Name of column to use to check whether the key is already present
                key_name            --  Name of the key to add
                key_value           --  Value of the key to add
                key_comment         --  Key's comment
                key_valueType       --  Value type of the key to be added. String, Integer, Boolean
                key_category        --  Category under which the key has to be added

            Raises:
                Exception:
                    -- if fails to add commcell setting

        """

        if self.__additional_settings.is_key_exist(column, key_name):
            raise Exception('Custom Commcell key is already present')

        self.__additional_settings.add_commcell_custom_setting(setting_name=key_name,
                                                               value=key_value,
                                                               comment=key_comment,
                                                               valueType=key_valueType,
                                                               category=key_category)
                                                               
        data = self.__additional_settings.get_key_values(key_name)

        if not (data['Name'][0] == key_name
                and data['Value'][0] == key_value
                and data['Comment'][0] == key_comment
                and data['Type'][0] == key_valueType
                and data['Category'][0] == key_category):
            raise Exception('Custom Commcell key values dont match')

    def edit_predefined_commcell_key(self,
                                     column=None,
                                     key_name=None,
                                     key_value=None,
                                     key_comment=None,
                                     key_isBooleanKey=None):
        """ Method to edit and verify predefined commcell setting

            Args:
                    column              --  Name of column to use to check whether the key is already present
                    key_name            --  Name of the key to edit
                    key_value           --  Value of the key to edit
                    key_comment         --  Key's comment
                    key_isBooleanKey    --  Whether the key is boolean type (True/False)

            Raises:
                Exception:
                    -- if fails to edit commcell setting
        """

        if not self.__additional_settings.is_key_exist(column, key_name):
            raise Exception('Pre-defined Commcell key is NOT present. Please create it first before editing')

        self.__additional_settings.edit_commcell_setting(setting_name=key_name,
                                                         value=key_value,
                                                         comment=key_comment,
                                                         isBooleanKey=key_isBooleanKey)

        data = self.__additional_settings.get_key_values(key_name)

        if not (data['Name'][0] == key_name
                and data['Value'][0] == key_value
                and data['Comment'][0] == key_comment):
            raise Exception('Pre-defined Commcell key values dont match')

    def edit_custom_commcell_key(self,
                                 column=None,
                                 key_name=None,
                                 key_value=None,
                                 key_comment=None,
                                 key_valueType=None,
                                 key_category=None):
        """ Method to edit and verify custom commcell setting

            Args:
                column              --  Name of column to use to check whether the key is already present
                key_name            --  Name of the key to edit
                key_value           --  Value of the key to edit
                key_comment         --  Key's comment to be edited 
                key_valueType       --  Value type of the key to be edited. String, Integer, Boolean
                key_category        --  Category under which the key has to be edited

            Raises:
                Exception:
                    -- if fails to edit commcell setting

        """

        if not self.__additional_settings.is_key_exist(column, key_name):
            raise Exception('Custom Commcell key is NOT present. Please create it first before editing')

        self.__additional_settings.edit_commcell_custom_setting(setting_name=key_name,
                                                                value=key_value,
                                                                comment=key_comment,
                                                                valueType=key_valueType,
                                                                category=key_category)

        data = self.__additional_settings.get_key_values(key_name)

        if not (data['Name'][0] == key_name
                and data['Value'][0] == key_value
                and data['Comment'][0] == key_comment
                and data['Type'][0] == key_valueType
                and data['Category'][0] == key_category):
            raise Exception('Custom Commcell key values dont match')
