
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Applications Section on the Restore Wizard of Kubernetes

"""
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable


class Applications:
    """
    class for handling Applications section on restore wizard
    """
    def __init__(self, wizard, inplace, admin_console, application_list, app_info):
        self.wizard = wizard
        self.inplace = inplace
        self.__admin_console = admin_console
        self.application_list = application_list
        self.log = admin_console.log
        self.app_info = app_info
        self.app_table = Rtable(admin_console=self.__admin_console, id='FullVMRestoreVirtualMachine')
        self.config()

    def config(self):

        if not self.inplace:
            for app in self.application_list:
                self.app_table.search_for(app)
                self.app_table.select_rows(names=[app])
                # Change Namespace and storage class if needed
                self.configure_namespace_and_storage_class(
                    app_name=app,
                    namespace=self.app_info[app]['new_namespace'],
                    storage_class=self.app_info[app]['new_sc']
                )

                self.app_table.clear_search()
        self.wizard.click_next()

    def configure_namespace_and_storage_class(self, app_name='', namespace='Original', storage_class='Original'):

        self.app_table.access_toolbar_menu('Configure restore options')
        modal_title = 'Configure restore options for ' + app_name
        restore_options_dialog = RModalDialog(admin_console=self.__admin_console, title=modal_title)
        if self.app_info[app_name]['new_name']:
            restore_options_dialog.fill_text_in_field(
                element_id="vmDisplayNameField",
                text=self.app_info[app_name]['new_name']
            )
        restore_options_dialog.select_dropdown_values(drop_down_id='namespace', values=[namespace])
        restore_options_dialog.select_dropdown_values(drop_down_id='storageClass', values=[storage_class])
        restore_options_dialog.click_submit()

    def edit_display_name(self, name):
        """
        edit the display name for the application on the wizard
        Args:
            name    str     New name

        """
        self.wizard.click_icon_button_by_title(title='Edit Display Name')
        display_name = name
        self.wizard.fill_text_in_field(id='vmDisplayNameField', text=display_name)
        self.wizard.click_icon_button_by_title(title='Save Display Name')

