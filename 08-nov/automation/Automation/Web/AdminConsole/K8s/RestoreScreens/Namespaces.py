
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Namespaces Section on the Restore Wizard of Kubernetes

"""
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable


class Namespaces:
    """
    class for handling Namespaces section on restore wizard
    """
    def __init__(self, wizard, inplace, admin_console, namespace_list, namespace_info):
        self.wizard = wizard
        self.inplace = inplace
        self.__admin_console = admin_console
        self.namespace_list = namespace_list
        self.log = admin_console.log
        self.namespace_info = namespace_info
        self.namespace_table = Rtable(admin_console=self.__admin_console, id='FullVMRestoreVirtualMachine')
        self.config()

    def config(self):
        if not self.inplace:
            for namespace in self.namespace_list:
                self.namespace_table.search_for(namespace)
                # Add storage class mapping if needed
                self.configure_storage_class_mapping(
                    namespace=namespace,
                    storage_class_mapping=self.namespace_info[namespace]['sc_mapping']
                )

                self.namespace_table.clear_search()
        self.wizard.click_next()

    def configure_storage_class_mapping(self, namespace, storage_class_mapping):

        self.namespace_table.select_rows(names=[namespace])
        self.namespace_table.access_toolbar_menu('Configure restore options')
        modal_title = 'Configure restore options for ' + namespace
        restore_options_dialog = RModalDialog(admin_console=self.__admin_console, title=modal_title)
        restore_options_dialog.fill_text_in_field(
            element_id='vmDisplayNameField',
            text=self.namespace_info[namespace]['new_name']
        )
        if storage_class_mapping:
            restore_options_dialog.click_button_on_dialog(text='Add')
            storage_class_dialog = RModalDialog(admin_console=self.__admin_console, title='Storage class')
            storage_class_dialog.select_dropdown_values(
                drop_down_id='source',
                values=list(storage_class_mapping.keys())
            )
            storage_class_dialog.select_dropdown_values(
                drop_down_id='destination',
                values=list(storage_class_mapping.values())
            )
            storage_class_dialog.click_button_on_dialog(text='Save')

        restore_options_dialog.click_button_on_dialog(text='Save')


