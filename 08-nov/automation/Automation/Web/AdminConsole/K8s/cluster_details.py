# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
details file has the functions to operate on cluster overview and configuration page where
we can view application group, run backup, view jobs, run restore job ....

Overview:

    view_appgrp_jobs                   --      view application group jobs

    backup                             --      Initiates backup job for the selected application

    access_restore                     --      initiate restore job for the selected application
                                               group

    access_configuration               --      access configuration tab

    change_sa_and_sa_token()           --       Change ServiceAccount and ServiceAccountToken


Configuration:

      access_overview()                  --     access overview tab

     change_image_url_and_image_secret() --     Change Image URL and Image Pull Secret for a cluster

     change_config_namespace()           --     Change Configuration Namespace for a cluster

     change_wait_timeout()               --      Change Wait Timeout settings for a cluster


"""
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.dialog import RBackup, RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import Backup, RModalPanel, RPanelInfo
from Web.AdminConsole.K8s.application_group_details import AppGroupDetails

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
import time


class Overview:
    """
    Functions to operate on cluster overview page
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__panel = RModalPanel(admin_console)
        self.__panel_info = RPanelInfo(admin_console)
        self.__page_container = PageContainer(admin_console)

    @PageService()
    def access_configuration(self):
        """Access configuration page"""
        self.__page_container.select_tab(self._admin_console.props['label.nav.configuration'])
        return Configuration(self._admin_console)

    @PageService()
    def access_application_groups(self):
        """Access application groups page"""
        self.__page_container.select_tab(self._admin_console.props['label.applicationGroup'])
        return ApplicationGroups(self._admin_console)

    @PageService()
    def add_application_group(self):
        """Open add application group wizard"""
        self.__page_container.access_page_action(self._admin_console.props['K8sClusters']['action.addVMGroup'])

    @PageService()
    def change_sa_and_sa_token_(self, sa, token):
        """Change ServiceAccount and ServiceAccountToken for a cluster"""

        self.__panel_info = RPanelInfo(self._admin_console, title='General')
        self.__panel_info.edit_tile()
        self.__panel = RModalPanel(self._admin_console)
        self.__panel.fill_input(id='authKey', text=sa)
        self.__panel.fill_input(id='authValue', text=token)
        self.__panel.save()
        self._admin_console.wait_for_completion()


class Configuration:
    """Operations on cluster configuration page"""

    def __init__(self, admin_console):
        self.__browse = RContentBrowse(admin_console)
        self._admin_console = admin_console
        self.__panel_info = RPanelInfo(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__panel = RModalPanel(admin_console)

    @WebAction()
    def __check_etcd_status(self):
        """Check if etcd is enabled"""
        return self.__panel_info.is_toggle_enabled(label=self._admin_console.props['label.etcd.protection'])

    @PageService()
    def access_overview(self):
        """Access overview page"""
        self.__page_container.select_tab(self._admin_console.props['label.tab.overview'])
        return Overview(self._admin_console)

    def change_access_node(self, access_node, old_access_node):
        """Change access node

        Args:
            access_node         (str)       --  New access node to be selected
            old_access_node     (str)       --  Old access node to be unselected

        """
        self.__panel_info = RPanelInfo(self._admin_console, title=self._admin_console.props['label.accessNodes'])
        self.__panel_info.click_action_item(
            action_name='Edit',
            aria_label='Actions'
        )
        self.__browse.unselect_content([old_access_node])
        self.__browse.select_content([access_node])
        self.__dialog.click_submit()
        tile_row_details = self.__panel_info.get_details()
        self._admin_console.log.info(tile_row_details)
        if access_node in tile_row_details.keys():
            self._admin_console.log.info(f"Access node changed to {access_node}")
        else:
            raise CVWebAutomationException("Access node not changed. Failing the Testcase")

    @PageService()
    def enable_etcd_protection(self, plan_name):
        """Enable toggle for etcd protection
            Args:
                plan_name       (str)   --  Name of the plan to select for etcd protection
        """
        self.__panel_info = RPanelInfo(self._admin_console, title=self._admin_console.props['label.etcd.protection'])
        if not self.__check_etcd_status():
            self._admin_console.log.info("Enabling etcd-protection toggle")
            self.__panel_info.enable_toggle(label=self._admin_console.props['label.etcd.protection'])
            self._admin_console.log.info(f"Selecting Plan [{plan_name}] from Plan dropdown")
            self.__dialog.select_dropdown_values(drop_down_id="plan", values=[plan_name])
            self.__dialog.click_submit()
        else:
            raise CVWebAutomationException(
                "etcd protection is already enabled for this cluster"
            )

    @PageService()
    def navigate_to_etcd(self):
        """Navigate to etcd app group if etcd protection is enabled"""
        self.__panel_info = RPanelInfo(self._admin_console, title=self._admin_console.props['label.etcd.protection'])
        if self.__check_etcd_status():
            self.__panel_info.open_hyperlink_on_tile(hyperlink="etcd (system generated)")
        else:
            raise CVWebAutomationException(
                "etcd protection has not been enabled for this cluster"
            )

    @PageService()
    def navigate_to_modifiers(self):
        """Navigate to Restore Modifiers wizard from Configuration page
        """
        self.__panel_info = RPanelInfo(self._admin_console, title='Advanced options')
        self.__panel_info.open_hyperlink_on_tile(hyperlink="Configure")

    @PageService()
    def change_image_url_and_image_secret_(self, image_url, image_secret):
        """Change Image URL and Image Pull Secret for a cluster

                    Args:

                        image_url           (str)       --   URL for Worker Pod image

                        image_secret        (str)       --  Image Pull Secret for the worker pod image

        """
        self.__panel_info = RPanelInfo(self._admin_console, title='Advanced options')
        self._admin_console.browser.scroll_down()

        self.__panel_info.edit_tile_entity(entity_name='Image registry settings')
        self.__panel = RModalPanel(self._admin_console)
        self.__panel.fill_input(id='imageRegistryURLField', text=image_url)
        self.__panel.fill_input(id='authenticationSecretName', text=image_secret)
        self.__panel.save()
        self._admin_console.wait_for_completion()

    @PageService()
    def change_config_namespace_(self, config_ns):
        """Change Configuration Namespace for a cluster

                Args:

                    config_ns           (str)       --  Configuration Namespace

        """
        self.__panel_info = RPanelInfo(self._admin_console, title='Advanced options')
        self._admin_console.browser.scroll_down()
        self.__panel_info.edit_tile_entity(entity_name='Configuration namespace')
        self.__panel = RModalPanel(self._admin_console)
        self.__panel.fill_input(id='tile-row-field', text=config_ns)
        self.__panel_info = RPanelInfo(self._admin_console, title='Advanced options')
        self.__panel_info.click_button('Submit')
        self._admin_console.wait_for_completion()

    @PageService()
    def change_wait_timeout_(self, worker_startup, resource_cleanup, snapshot_ready, snapshot_cleanup):
        """Change Wait Timeout settings for a cluster

                    Args:

                        worker_startup      (str)       --  Timeout for Worker Pod startup

                        resource_cleanup    (str)       --  Timeout for Cluster Resource Cleanup

                        snapshot_ready      (str)       --  Timeout for Snapshot Ready

                        snapshot_cleanup    (str)       --  Timeout for Snapshot Cleanup
        """
        self.__panel_info = RPanelInfo(self._admin_console, title='Advanced options')
        self._admin_console.browser.scroll_down()
        self.__panel_info.edit_tile_entity(entity_name='Wait timeout for job steps')
        self.__panel = RModalPanel(self._admin_console)
        self.__panel.fill_input(id='workerPodStartup', text=worker_startup)
        self.__panel.fill_input(id='resourceCleanup', text=resource_cleanup)
        self.__panel.fill_input(id='snapshotReady', text=snapshot_ready)
        self.__panel.fill_input(id='snapshotCleanup', text=snapshot_cleanup)
        self.__panel.save()
        self._admin_console.wait_for_completion()


class ApplicationGroups:
    """
    Functions to operate on cluster application groups page
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__panel_info = RPanelInfo(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__table = Rtable(admin_console)
        self.__backup = RBackup(admin_console)
        self.__browse = RContentBrowse(admin_console)

    @PageService()
    def access_application_groups_tab(self):
        """Access the application groups tab"""
        self.__page_container.select_tab('Application groups')

    @PageService()
    def view_appgrp_jobs(self, app_grp_name):
        """
        view job history for the provided application group
        Args:
            app_grp_name                       (String)       --     application group name
        """
        self.__table.access_action_item(app_grp_name, self._admin_console.props['label.globalActions.viewJobs'])

    @PageService()
    def backup(self, app_grp_name, backup_level=Backup.BackupType.FULL):
        """
        Initiate backup
        Args:
            app_grp_name                 (String)       --    Instance name
            backup_level                 (String)       --    Specify backup level from constant
                                                              present in ApplicationGroups class
        """
        self.__table.access_action_item(app_grp_name, self._admin_console.props['label.globalActions.backup'])
        return self.__backup.submit_backup(backup_level)

    @PageService()
    def access_restore(self, app_grp_name):
        """
        click application group restore action
        Args:
            app_grp_name                  (String)     --  application group name
        """
        self.__table.access_action_item(app_grp_name, self._admin_console.props['label.restore'])

    @PageService()
    def access_configuration(self):
        """Access configuration page"""
        self.__page_container.select_tab(self._admin_console.props['label.nav.configuration'])
        return Configuration(self._admin_console)

    @PageService()
    def open_application_group(self, app_group_name):
        """Select an application group from the table"""
        self.__table.access_link(app_group_name)
        return AppGroupDetails(self._admin_console)

    @PageService()
    def delete_application_group(self, app_group_name):
        """Delete an application group"""
        self.__table.access_action_item(app_group_name, self._admin_console.props['action.delete'])
        self._admin_console.click_button(self._admin_console.props['label.yes'])
