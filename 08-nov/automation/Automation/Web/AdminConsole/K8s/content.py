# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This file has classes and functions to interact with Kubernetes restore pages

KubernetesContent:

    select_app()                --  Select application from tree

    select_namespace()          --  Select namespace from tree

    enable_exclusion()          --  Enable toggle for exclusions

    add_label_selector()        --  Add label selector from dialog box

"""
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import PageService


class KubernetesContent:
    """
    Content component for Kubernetes Application Group
    """

    def __init__(self, admin_console):
        """Initialize class variables
            Args:

                admin_console       (obj)           --  Admin console object
        """
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__browse = RContentBrowse(admin_console)
        self.__dialog = RModalDialog(admin_console)

    def __set_table_object(self, title):
        """Set the table object based on title"""
        self.__table = Rtable(admin_console=self._admin_console, title=title)

    def select_namespace(self, namespace):
        """Select a namespace checkbox
            Args:
                namespace       (str)       --  Namespace to select
        """
        self.__browse.select_path(path=namespace, wait_for_spinner=300)

    def select_app(self, namespace, app_name):
        """Select application from namespace drill down
            Args:
                namespace       (str)       --      Namespace that contains the application
                app_name        (str)       --      Application to select under namespace
        """

        self.__browse.select_path(path="/".join([namespace, app_name]), wait_for_spinner=300)

    @PageService()
    def add_label_selector(self, browse_type, selector):
        """Add label selector content
            Args:
                browse_type        (str)       --  Type of the label selector
                selector    (str)       --  Label selector value
        """

        self.__dialog.select_dropdown_values(drop_down_id="labelType", values=[browse_type])
        self.__dialog.fill_text_in_field(element_id="selector_value", text=selector)

    @PageService()
    def enable_exclusion(self):
        """Enable exclusion toggle
        """
        self.__dialog.enable_toggle(label=self._admin_console.props['label.excludeItems'])

    @PageService()
    def configure_backup_filters(
            self, table_header, content, onboarding=True, remove_existing_filters=0, exclude_dependencies=True
    ):
        """
        Configure backup filters for the content
        Args:

            table_header      (str)         --  Header of the table to select content in

            content      (list)             -- Set backup content with this format -
                                                'FilterType:FilterCondition:FilterValue'
                                                Should be a list of strings with above format.
            onboarding  (bool)              -- True if we want to add backup filters in onboarding wizard

            remove_existing_filters (int)  -- Number of filters we want to remove

            exclude_dependencies (bool)    -- Set to true if we want to exclude dependencies

        """

        self.__set_table_object(title=table_header)
        __add_k8s_backup_filters = RModalDialog(self._admin_console, title="Add rule")
        for i in range(0, remove_existing_filters):
            self.delete_content(table_header=table_header, row_idx=1,save=False)
            self.enable_exclusion()

        self.__table.access_menu_from_dropdown(menu_id=self._admin_console.props['heading.labelExcludeByRule'])

        for item_index in range(0, len(content)):
            content_item = content[item_index]
            rule_array = content_item.split(':')
            filter_type = rule_array[0]
            filter_condition = rule_array[1]
            filter_value = rule_array[2]
            __add_k8s_backup_filters.select_dropdown_values(
                drop_down_id=f"filterType_{item_index}",
                values=[filter_type]
            )
            __add_k8s_backup_filters.select_dropdown_values(
                drop_down_id=f"filterCondition_{item_index}",
                values=[filter_condition]
            )
            __add_k8s_backup_filters.fill_text_in_field(
                element_id=f"filterValue_{item_index}",
                text=filter_value
            )
            # __add_k8s_backup_filters.click_button_on_dialog(text='Add', button_index=1)

        if not exclude_dependencies:
            __add_k8s_backup_filters.disable_toggle(label=self._admin_console.props['label.excludeDependencies'])

        __add_k8s_backup_filters.click_button_on_dialog(id='Save')

        if not onboarding:
            self.save()
            self._admin_console.wait_for_completion()

    @PageService()
    def add_content(self, table_header, content, validate_matrix=None, onboarding=True, validate_preview=False):
        """Add content in either content or filter table
        Args:
            table_header      (str)         --  Header of the table to select content in

            onboarding          (bool)      --  Set to true if this function is being called to onboard cluster.
                                                False if we are using to manage content

            content      (list)             -- Set backup content with this format -
                                                'ContentType:BrowseType:namespace/app'
                                                Should be a list of strings with above format.

                                                        Valid ContentType -
                                                            Applications, Selector.
                                                            If not specified, default is 'Application'
                                                        Valid BrowseType for Application ContentType -
                                                            Applications, Volumes, Labels
                                                            If not specified, default is 'Applications'
                                                        Valid BrowseType for Selector ContentType -
                                                            Application, Volumes, Namespaces
                                                            If not specified, default is 'Namespaces'

                                                        Examples -
                                                            1. ns001 -- Format : namespace
                                                            2. ns001/app001 -- Format : namespace/app
                                                            3. Volumes:ns001/pvc001 -- Format : BrowseType:namespace/app
                                                            4. Selector:Namespaces:app=demo -n ns004
                                                                    -- Format : ContentType:BrowseType:namespace
                                                            5. ['Application:Volumes:nsvol/vol001', 'nsvol02/app1']

            onboarding      (bool)              Set to true if the function is being called from cluster onboarding

            validate_preview    (bool)          Set to true if the function is required to validate preview

            validate_matrix     (dict)          Matrix to validate preview content


        """

        self.__set_table_object(title=table_header)
        __add_k8s_apps_dialog = RModalDialog(self._admin_console, title="Add Kubernetes applications")
        __add_k8s_apps_selector = RModalDialog(self._admin_console, title="Add label selector")
        for item in content:
            # Split first `:` to get content type (Application or Selector).
            if item.find(':') < 0:
                item = f'Applications:{item}'
            content_type, content_item = item.split(':', 1)

            # Split second `:` to get Browse type and app value
            if content_item.find(':') < 0:
                content_item = f'Applications:{content_item}'
            browse_type, app = content_item.split(':')

            if content_type == 'Applications':
                self.__table.access_menu_from_dropdown(menu_id=self._admin_console.props['label.virtualMachines'])
                self._admin_console.wait_for_completion()
                __add_k8s_apps_dialog.select_dropdown_values(drop_down_id="value", values=[browse_type])
                self._admin_console.wait_for_completion()

                # Currently a workaround to expand the cluster tree item
                if browse_type != 'Labels':
                    # Expanding root tree item for cluster
                    self.__browse.expand_folder_path(wait_for_spinner=300)
                # END

                self.__browse.select_path(path=app, wait_for_spinner=300)
                __add_k8s_apps_dialog.click_button_on_dialog(id='Save')

            elif content_type == 'Selector':
                self.__table.access_menu_from_dropdown(menu_id=self._admin_console.props['heading.labelSelector'])
                self._admin_console.wait_for_completion()
                if onboarding:
                    self.add_label_selector(browse_type, app)
                else:
                    __add_k8s_apps_selector.select_dropdown_values(drop_down_id="labelType", values=[browse_type])
                    __add_k8s_apps_selector.fill_text_in_field(element_id="selector_value", text=app)
                    __add_k8s_apps_selector.click_button_on_dialog(id='Save')

            self._admin_console.wait_for_completion()

        if validate_preview:
            self.validate_preview(validate_matrix=validate_matrix)

        if not onboarding:
            self.save()

    @PageService()
    def validate_preview(self, validate_matrix, close_manage_content=False):
        """
        Validate the preview content
        """
        self.__dialog.click_preview_button()
        self._admin_console.wait_for_completion()
        __preview_dialog = RModalDialog(admin_console=self._admin_console, title='Preview')
        __preview_table = Rtable(
            admin_console=self._admin_console,
            xpath="//div[contains(@class, 'MuiDialog-paper')]//h2[text()='Preview']/ancestor::div[contains(@class, "
                  "'MuiDialog-paper')]//div[@class='grid-body']")
        table_data = __preview_table.get_table_data()
        if table_data != validate_matrix:
            raise Exception(f"Preview table data did not match. Expected - {validate_matrix}, Actual - {table_data}")
        self._admin_console.log.info(f"Preview table data matched. Expected - {validate_matrix}")
        __preview_dialog.click_close()
        self._admin_console.wait_for_completion()

    @PageService()
    def enable_stateless_toggle(self):
        """Enable toggle for stateless filter
        """
        self.__dialog.enable_toggle(label=self._admin_console.props['label.skipStatelessApplications'])

    @PageService()
    def save(self):
        """Select the Save button
        """
        self.__dialog.click_submit()

    def delete_content(self, table_header, row_idx, save=True):
        """Deletes content in manage content"""

        content_table = Rtable(admin_console=self._admin_console, title=table_header)
        content_table.delete_row(row_idx)
        if not save:
            return
        self.save()
