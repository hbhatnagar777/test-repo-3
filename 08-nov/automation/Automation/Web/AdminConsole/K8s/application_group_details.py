# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for all the actions that can be done of the application group
details page.


Classes:

   AppGroupDetails  --  This class contains all the methods for action in a particular application
   group details page

Functions:

    select_application_from_browse_tree()   --      select application from the browse tree

    select_namespace_from_browse_tree()     --      select namespace from browse tree

    backup()                                --      run backup job

    job()                                   --      open the job page with all the running
                                                    jobs for the application group

    restore()                               --      select restore button from app group details

    manage_content()                        --      select Manage hyperlink from Content tile

    enable_stateless_toggle()               --      enable toggle for stateless filter

    change_no_of_readers()                  --      Changes Number of Readers for a Application Group

    change_worker_pod_resource_settings()   --      Change Worker Pod Resource Settings for a Application Group

    enable_live_volume_fallback()           --      Enables Live Volume Fallback for a application group


"""

from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.dialog import RBackup, ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import DropDown, RPanelInfo, RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.K8s.content import KubernetesContent
import time


class AppGroupDetails:
    """
    This class contains all the methods for action in Application Group Details page
    """

    def __init__(self, admin_console):
        """ """
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__dropdown = DropDown(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__browse = RContentBrowse(admin_console)
        self.__panel_info = RPanelInfo(admin_console)
        self.__content = KubernetesContent(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__backup = RBackup(self._admin_console)
        self.__panel = RModalPanel(self._admin_console)

    @PageService()
    def select_overview(self):
        """
        Switch to Overview Tab in Application Details Page
        """
        self.__page_container.select_tab("Overview")

    @PageService()
    def select_configuration(self):
        """
        Switch to Configuration Tab in Application Details Page
        """
        self.__page_container.select_tab("Configuration")

    @PageService()
    def select_content(self):
        """
        Switch to Content Tab in Application Details Page
        """
        self.__page_container.select_tab("Content")

    @PageService()
    def backup(self, bkp_type):
        """
        run backup job
        """
        self.__page_container.access_page_action(self._admin_console.props['K8sClusters']['action.commonAction.backup'])
        return self.__backup.submit_backup(bkp_type)

    @PageService()
    def jobs(self):
        """
        Opens the jobs page with all the running jobs for the server

        Raises:
            Exception:
                if the jobs page could not be opened

        """
        self.__page_container.access_page_action(self._admin_console.props['label.globalActions.viewJobs'])

    @PageService()
    def restore(self):
        """Select restore button from app group details
        """
        self.select_overview()
        self.__panel_info = RPanelInfo(self._admin_console, title="Recovery points")
        self._admin_console.scroll_into_view(
            element_name="//button[contains(@class, 'MuiButton-root') and @id='submit-btn']"
        )
        self.__panel_info.click_button("Restore")

    @PageService()
    def change_access_node(self, access_node):
        """Select change access node button from app group details

            access_node    (str)      --  Access node to change to this

        """
        self.select_configuration()
        self.__panel_info = RPanelInfo(self._admin_console, title="Access nodes")
        self._admin_console.browser.scroll_down()
        self.__panel_info.click_action_item(
            action_name='Edit',
            aria_label='Actions'
        )
        self.__browse.select_content([access_node])
        self.__dialog.click_submit()
        tile_row_details = self.__panel_info.get_details()
        self._admin_console.log.info(tile_row_details)
        if access_node in tile_row_details.keys():
            self._admin_console.log.info(f"Access node changed to {access_node}")
        else:
            raise CVWebAutomationException("Access node not changed. Failing the Testcase")

    @PageService()
    def change_plan(self, plan_name):
        """Select change plan button from app group details

            plan_name    (str)      --  Plan to change to this

        """
        self.select_overview()
        self.__panel_info = RPanelInfo(self._admin_console, title="Summary")

        self._admin_console.browser.scroll_down()
        self.__panel_info.edit_tile()
        dropdown = RDropDown(self._admin_console)
        dropdown.select_drop_down_values(values=[plan_name], drop_down_id='plan')
        self.__panel_info.click_button('Submit')
        panel_details = self.__panel_info.get_details()
        if panel_details['Plan'] != plan_name:
            raise Exception("Failed to change plan to {0}".format(plan_name))
        else:
            self._admin_console.log.info(f"Plan changed to {plan_name}")

    @PageService()
    def manage_content(self):
        """Select 'Manage' hyperlink from Content tile
        """
        self.select_content()
        self.__panel_info = RPanelInfo(self._admin_console, title="Content")
        self.__panel_info.edit_tile()

    @PageService()
    def validate_preview_content(self, validate_matrix):
        """Select 'Manage' hyperlink from Content tile
        """
        self.manage_content()
        self.__content.validate_preview(validate_matrix=validate_matrix)


    @PageService()
    def skip_stateless_apps(self):
        """Enable toggle for stateless filter
        """
        self.manage_content()
        self.__content.enable_stateless_toggle()

    @PageService()
    def delete_from_manage_content(self, row_idx):
        """Select 'Manage' hyperlink from Content tile"""
        self.manage_content()
        self.__content.delete_content(
            table_header="Content",
            row_idx=row_idx
        )

    @PageService()
    def modify_app_group_contents(self, content, validate_matrix):
        """Select 'Manage' hyperlink from Content tile"""
        self.manage_content()
        self.__content.add_content(
            table_header="Content",
            content=content,
            onboarding=False,
            validate_preview=True,
            validate_matrix=validate_matrix
        )

    @PageService()
    def configure_backup_filters(self, backup_filters, remove_existing_filters, exclude_dependencies=True):
        """
        Select manage content and configure backup filters
        """
        self.manage_content()
        self.__content.configure_backup_filters(
            table_header=self._admin_console.props['heading.filters'],
            content=backup_filters,
            remove_existing_filters=remove_existing_filters,
            exclude_dependencies=exclude_dependencies,
            onboarding=False
        )

    def change_no_of_readers_(self, no_of_readers):
        """Change Number of Readers for a Application Group

                    Args:

                        no_of_readers       (str)       --  Number of readers

        """
        self.select_configuration()
        self.__panel_info = RPanelInfo(self._admin_console, title='Options')
        self.__panel_info.edit_tile()
        self.__panel = RModalPanel(self._admin_console)
        self.__panel.fill_input(id='noOfReaders', text=no_of_readers)
        self.__panel.save()

        self._admin_console.wait_for_completion()

    def change_worker_pod_resource_settings_(self, cpu_request, cpu_limit, memory_request, memory_limit):
        """Change Worker Pod Resource Settings for a Application Group

                            Args:

                                cpu_request         (str)        --  CPU Request

                                cpu_limit           (str)        --  CPU Limit

                                memory_request      (str)        --  Memory Request

                                memory_limit        (str)        --  Memory Limit

        """
        self.select_configuration()
        self.__panel_info = RPanelInfo(self._admin_console, title='Options')
        self.__panel_info.edit_tile_entity(entity_name='Worker pod resource settings')
        self.__panel = RModalPanel(self._admin_console)
        self.__panel.fill_input(id='CPURequestField', text=cpu_request)
        self.__panel.fill_input(id='CPULimitField', text=cpu_limit)
        self.__panel.fill_input(id='memoryRequestField', text=memory_request)
        self.__panel.fill_input(id='memoryLimitField', text=memory_limit)
        self.__panel.save()
        self._admin_console.wait_for_completion()

    def enable_live_volume_fallback_(self):
        """Enables Live Volume Fallback for a application group"""
        self.select_configuration()
        self.__panel_info = RPanelInfo(self._admin_console, title='Options')
        self.__panel_info.enable_toggle(label="Enable fallback to live volume backup")
        self._admin_console.wait_for_completion()
