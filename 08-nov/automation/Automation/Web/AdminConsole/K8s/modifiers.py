# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This file has classes and functions to interact with Kubernetes restore pages

ConfigureModifiers:


    add_action()                --  Add an action for the modifier

    add_selector()              --  Add a selector for the modifier

    delete_modifier()           --  Delete a modifier from the list

    save()                      --  Save a modifier

    select_modifier()           --  Select a modifier from the list

    select_test()               --  Select on TEST on configure modifier page

"""

from Kubernetes.RestoreModifierHelper import SelectorCriteria, ModifierAction
from Kubernetes.constants import RestoreModifierConstants
from Web.AdminConsole.Components.dialog import Form, RModalDialog
from Web.Common.page_object import PageService, WebAction


class ConfigureModifiers:
    """Configure Modifiers page
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__form = Form(admin_console)
        self.__dialog = RModalDialog(admin_console)

    @WebAction()
    def __enter_modifier_name(self, name):
        """Enter the name of a new modifier in the dropdown
            Args:
                name    (str)   :   Modifier name to select
        """
        self.__form.click_button_on_dialog(aria_label="Add modifier")
        self.__admin_console.wait_for_completion()
        self.__dialog.fill_text_in_field(element_id="newModifierName", text=name)
        self.__dialog.click_submit()

    @WebAction()
    def __choose_selector_type(self, selector):
        """Choose the selector type from dropdown
            Args:
                selector    (str)   :   Selector value to select
        """
        self.__form.select_dropdown_values(drop_down_id="selectorDropdown", values=[selector.title()])

    @WebAction()
    def __choose_action_type(self, action):
        """Choose the action type from dropdown
            Args:
                action    (str)   :   Selector value to select
        """
        self.__form.select_dropdown_values(drop_down_id="actionDropdown", values=[action.title()])

    @PageService()
    def _input_kind_selector_values(self, value):
        """Input values for 'Kind' selector
            Args:
                value  (str)  :   Value for kind
        """
        self.__choose_selector_type(RestoreModifierConstants.SELECTOR_KIND.value)
        self.__form.fill_text_in_field(element_id="selectorValue", text=value)
        self.__form.click_button_on_dialog(text="Add", button_index=0)

    @PageService()
    def _input_name_selector_values(self, value):
        """Input values for 'Name' selector
            Args:
                value  (str)  :   Value for name
        """
        self.__choose_selector_type(RestoreModifierConstants.SELECTOR_NAME.value)
        self.__form.fill_text_in_field(element_id="selectorValue", text=value)
        self.__form.click_button_on_dialog(text="Add", button_index=0)

    @PageService()
    def _input_namespace_selector_values(self, value):
        """Input values for 'Namespace' selector
            Args:
                value  (str)  :   Value for namespace
        """
        self.__choose_selector_type(RestoreModifierConstants.SELECTOR_NAMESPACE.value)
        self.__form.fill_text_in_field(element_id="selectorValue", text=value)
        self.__form.click_button_on_dialog(text="Add", button_index=0)

    @PageService()
    def _input_labels_selector_values(self, values):
        """Input values for 'Labels' selector
            Args:
                values  (dict)  :   Dictionary containing labels
        """
        labels = ','.join(
            [f"{key}:{value}" for key, value in values.items()]
        )

        self.__choose_selector_type(RestoreModifierConstants.SELECTOR_LABELS.value)
        self.__form.fill_text_in_field(element_id="selectorValue", text=labels)
        self.__form.click_button_on_dialog(text="Add", button_index=0)

    @PageService()
    def _input_field_selector_values(self, values):
        """Input values for 'Field' selector
            Args:
                values  (dict)  :   Dictionary containing values
        """

        self.__choose_selector_type(RestoreModifierConstants.SELECTOR_FIELD.value)
        self.__form.fill_text_in_field(
            element_id="pathField", text=values[RestoreModifierConstants.SELECTOR_FIELD_PATH.value]
        )

        if values[RestoreModifierConstants.SELECTOR_FIELD_EXACT.value]:
            self.__form.select_dropdown_values(drop_down_id="exactDropdown", values=["True"])
        else:
            self.__form.select_dropdown_values(drop_down_id="exactDropdown", values=["False"])

        if values[RestoreModifierConstants.SELECTOR_FIELD_CRITERIA.value] == SelectorCriteria.CONTAINS.value:
            self.__form.select_dropdown_values(drop_down_id="criteriaDropdown", values=["Contains"])
        else:
            self.__form.select_dropdown_values(drop_down_id="criteriaDropdown", values=["Does not contain"])

        self.__form.fill_text_in_field(
            element_id="selectorValue", text=values[RestoreModifierConstants.SELECTOR_FIELD_VALUE.value]
        )
        self.__form.click_button_on_dialog(text="Add", button_index=0)

    @PageService()
    def _input_add_action_values(self, values):
        """Input values for 'Add' action
            Args:
                values  (dict)  :   Dictionary containing values
        """
        self.__choose_action_type(ModifierAction.ADD.value)
        self.__form.fill_text_in_field(
            element_id="pathField", text=values[RestoreModifierConstants.MODIFIER_PATH.value]
        )
        self.__form.fill_text_in_field(
            element_id="actionValueField", text=values[RestoreModifierConstants.MODIFIER_VALUE.value]
        )
        self.__form.click_button_on_dialog(text="Add", button_index=1)

    @PageService()
    def _input_delete_action_values(self, values):
        """Input values for 'Delete' action
            Args:
                values  (dict)  :   Dictionary containing values
        """
        self.__choose_action_type(ModifierAction.DELETE.value)
        self.__form.fill_text_in_field(
            element_id="pathField", text=values[RestoreModifierConstants.MODIFIER_PATH.value]
        )
        self.__form.click_button_on_dialog(text="Add", button_index=1)

    @PageService()
    def _input_modify_action_values(self, values):
        """Input values for 'Modify' action
            Args:
                values  (dict)  :   Dictionary containing values
        """
        self.__choose_action_type(ModifierAction.MODIFY.value)
        self.__form.fill_text_in_field(
            element_id="pathField", text=values[RestoreModifierConstants.MODIFIER_PATH.value]
        )
        self.__form.select_dropdown_values(
            drop_down_id="parametersDropdown", values=[values[RestoreModifierConstants.MODIFIER_PARAMETERS.value]]
        )
        self.__form.fill_text_in_field(
            element_id="actionValueField", text=values[RestoreModifierConstants.MODIFIER_VALUE.value]
        )
        self.__form.fill_text_in_field(
            element_id="newValueField", text=values[RestoreModifierConstants.MODIFIER_NEW_VALUE.value]
        )
        self.__form.click_button_on_dialog(text="Add", button_index=1)

    @PageService()
    def select_modifier(self, name):
        """Select modifier from dropdown
            Args:
                name    (str)   :   Modifier name to select
        """
        self.__form.select_dropdown_values(drop_down_id="modifiersDropdown", values=[name])

    @PageService()
    def delete_modifier(self, name):
        """Delete modifier from dropdown
            Args:
                name    (str)   :   Modifier name to delete
        """
        self.__form.select_dropdown_value_action(drop_down_id="modifiersDropdown", value=name, action="Delete")
        self.__dialog.click_submit()

    @PageService()
    def add_name(self, name):
        """Enter the name of a new modifier in the dropdown
            Args:
                name    (str)   :   Modifier name to select
        """

        self.__enter_modifier_name(name=name)

    @PageService()
    def add_selector(self, selector_json):
        """Add a selector
            Args:
                selector_json   (dict)  :   List of dictionary containing selector values
        """

        for key, value in selector_json.items():
            getattr(self, f"_input_{key}_selector_values")(value)
            self.__admin_console.wait_for_completion()

    @PageService()
    def add_action(self, action_list):
        """Add actions
            Args:
                action_list   (list[dict])  :   List of dictionary containing action values
        """
        for actions in action_list:
            getattr(self, f"_input_{actions[RestoreModifierConstants.MODIFIER_ACTION.value]}_action_values")(actions)
            self.__admin_console.wait_for_completion()

    @PageService()
    def select_test(self):
        """Select the TEST button
        """
        self.__form.click_button_on_dialog(preceding_label="Test")
        self.__admin_console.wait_for_completion()

    @PageService()
    def save(self):
        """Save modifier
        """
        self.__form.click_button_on_dialog(text="Save")
        self.__admin_console.wait_for_completion()
