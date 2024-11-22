# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on Data Masking Policies Page

MaskType: Enum for Masking Policy Type

Configuration: Read only class to hold configuration definitions inside masking policies

DataMasking: Class for Data Masking Policies Page

    add()       --  Add a new data masking policy
"""
from dataclasses import dataclass
from enum import Enum

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.panel import RDropDown


class MaskType(Enum):
    """Enum for Masking Policy Type"""
    shuffling = 'Shuffling'
    format_preserving = 'Format-preserving encryption alphanumeric'
    numeric_range = 'Numeric range'
    numeric_variance = 'Numeric variance'
    fixed_string = 'Fixed string'
    dictionary = 'Dictionary'


@dataclass(frozen=True)
class Configuration:
    """Read only class to hold configuration definitions inside masking policies"""
    sobject: str
    fields: list[dict]
    type: MaskType
    attributes: list = None


class DataMasking:
    """Class for Data Masking Policies Page"""

    def __init__(self, admin_console):
        """Init method for the class"""
        self.__admin_console = admin_console
        self.__drop_down = RDropDown(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__config_dialog = RModalDialog(self.__admin_console, title='New config')

    @PageService()
    def add(self, name, *configurations):
        """
        Add a new data masking policy

        Args:
            name (str): Name of data masking policy
            configurations (Configuration): Configurations to create in the policy

        Returns:
            None:
        """
        self.__admin_console.click_button(self.__admin_console.props['salesforce.label.addPolicy'])
        self.__dialog.fill_text_in_field('name', name)

        for configuration in configurations:
            self.__dialog.click_button_on_dialog(text=self.__admin_console.props['label.add'])
            self.__admin_console.wait_for_completion()
            self.__drop_down.select_drop_down_values(drop_down_id='objectNames', values=[configuration.sobject])
            self.__drop_down.select_drop_down_values(
                drop_down_id='fields',
                values=[f"{field['name']} ({field['type']})" for field in configuration.fields]
            )
            self.__drop_down.select_drop_down_values(drop_down_id='maskingType', values=[configuration.type.value])
            if configuration.type == MaskType.numeric_range or configuration.type == MaskType.numeric_variance:
                raise NotImplementedError()
            elif configuration.type == MaskType.fixed_string:
                self.__config_dialog.fill_text_in_field("param[0]", configuration.attributes[0])
            self.__config_dialog.click_submit()
        self.__dialog.click_submit()

    @PageService()
    def delete(self, name):
        """
        Deletes an existing data masking policy

        Args:
            name (str): Name of data masking policy

        Returns:
            None:

        Raises:
            Exception: if data masking policy does not exist
        """
        raise NotImplementedError()
