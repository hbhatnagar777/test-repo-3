# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on a Salesforce Organization details page

SalesforceApp:

    _fill_content_checkboxes()  --  Select/Deselects checkboxes in manage content panel out of 'All files',
                                    'All metadata' and 'Archived and deleted records'

    delete()                    --  Deletes Salesforce org

    access_configuration_tab()  --  Clicks on Configuration tab

    _click_on_backup()          --  Method to click on backup

    backup()                    --  Runs backup

    select_time_for_restore()   --  Selects PIT and clicks on restore

    restore()                   --  Clicks on run restore and opens Select Restore Type page

    data_masking()              --  Clicks on data masking and opens data masking policies page

    access_monitoring_tab()       --  Clicks on Monitoring tab

SalesforceApp instance Attributes:
    **org_name**            --  Gets Organization name from page title

    **details**             --  Gets general org details

    **content**             --  Gets/Sets org content
"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.panel import RPanelInfo, RModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.page_container import PageContainer
from .base import SalesforceBase
from selenium.common.exceptions import NoSuchElementException
from Web.AdminConsole.Salesforce.constants import MONTH_SHORT_NAMES


class SalesforceOverview(SalesforceBase):
    """Class for Salesforce app details page"""

    def __init__(self, admin_console, commcell):
        """Init method for the class"""
        super().__init__(admin_console, commcell)
        self.__admin_console = admin_console
        self.__commcell = commcell
        self.__checkbox = Checkbox(self.__admin_console)
        self.__general_panel = RPanelInfo(
            self.__admin_console,
            title=self.__admin_console.props['label.cAppClientAccountDet']
        )
        self.__content_panel = RPanelInfo(
            self.__admin_console,
            title=self.__admin_console.props['label.content']
        )
        self.__recovery_panel = RPanelInfo(
            self.__admin_console,
            title=self.__admin_console.props['header.recoveryPoints']
        )
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__org_name = None

    @property
    def org_name(self):
        """
        Gets org name from page title

        Returns:
            org_name (str)
        """
        if not self.__org_name:
            self.__org_name = self.__page_container.fetch_title()
        return self.__org_name

    @property
    def details(self):
        """
        Get general org details

        Returns:
            details (dict)  --  dictionary containing org details like
                                {'Organization name': ,
                                 'Environment': 'Production' or 'Sandbox',
                                 'Plan': ,
                                 'Last backup time': ,
                                 'Last backup size': }
        """
        return self.__general_panel.get_details()

    @property
    def content(self):
        """
        Get org content

        Returns:
            (list)          --  list containing content like
                                ['All objects', 'All files', 'All metadata', 'Archived and deleted records']
        """
        return self.__content_panel.get_details()

    @content.setter
    def content(self, content):
        """
        Set content

        Args:
            content (list)  --  list of content containing one or more from
                                ['All files', 'All metadata', 'Archived and deleted records']
                                content items present in list will be selected, and items not in list will be unselected
                                'All Objects' item will always be selected

        Example:
            if content = ['All files'] then 'All files' will be selected, and 'All metadata' and 'Archived and deleted
            records' will be deselected
        """
        self.__content_panel.edit_tile()
        self._fill_content_checkboxes(content)
        self.__dialog.click_submit()

    @PageService()
    def access_sandbox_seed_tab(self):
        """
        Clicks on sandbox seed tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.sf.tabs.sandboxSeeding'])

    @PageService()
    def access_monitoring_tab(self):
        """
        Clicks on Monitoring tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.sf.tabs.anomalyAlerts'])

    @PageService()
    def access_compare_tab(self):
        """
        Clicks on Compare tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.sf.tabs.compare'])

    @PageService()
    def access_compliance_manager(self):
        """
        Clicks on Compliance Manager tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['header.gdpr.complianceManager'])


    @PageService()
    def _fill_content_checkboxes(self, content):
        """
        Select/Deselects checkboxes in manage content panel

        Args:
            content (list)  --  list of content containing one or more from
                                ['All files', 'All metadata', 'Archived and deleted records']
                                content items present in list will be selected, and items not in list will be unselected
                                'All Objects' item will always be selected
        """
        for content_item, checkbox_id in [(self.__admin_console.props['label.allSfFiles'], 'backupFileObjects'),
                                          (self.__admin_console.props['label.allSfMetadata'], 'backupSFMetadata'),
                                          (self.__admin_console.props['label.archDelRecs'],
                                           'backupArchivedandDeletedRecs')]:
            if content_item in content:
                self.__checkbox.check(id=checkbox_id)
            else:
                self.__checkbox.uncheck(id=checkbox_id)

    @PageService()
    def delete(self):
        """
        Deletes Salesforce Organization

        """
        org_name = self.org_name
        self.__page_container.access_page_action(self.__admin_console.props['action.delete'])
        self.__dialog.type_text_and_delete(text_val=org_name.upper(),
                                           button_name=self.__admin_console.props['action.delete'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def access_configuration_tab(self):
        """
        Clicks on Configuration tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['salesforce.label.configuration'])

    @PageService()
    def _click_on_backup(self, org_name):
        """
        Method to click on backup

        Args:
            org_name (str)  --  Name of org to click on backup for
        """
        self.__page_container.access_page_action(self.__admin_console.props['label.globalActions.backup'])

    @PageService()
    def _click_on_dropdown_element(self, option):
        """
        Method to select an option from Overview dropdown

        Args:
            option (str) -- Name of the option to select from dropdown
        """
        self.__admin_console.access_menu_from_dropdown(option)

    @PageService()
    def backup(self, backup_type="Incremental", wait_for_job_completion=True):
        """
        Runs backup

        Args:
            backup_type (str)           --  "Full" or "Incremental", case insensitive
            wait_for_job_completion (bool) --  if True, waits for current job and any automatic job that launches
                                            if False, just returns job id of full/incremental job run

        Returns:
            (tuple)                     --  (job_id, ) or (full_job_id, incremental_job_id)

        Raises:
            Exception                   --  if wait_for_job_completion is True and waiting for full/automatic
                                            incremental job encounters an error
        """
        return super().backup(self.org_name, backup_type, wait_for_job_completion)

    @PageService()
    def select_time_for_restore(self, timestamp):
        """
        Selects time for restore in date picker.

        Args:
            timestamp (datetime.datetime): timestamp of backup job

        Returns:
            None:

        Raises:
            Exception: if no backup job exists for given timestamp
        """
        self.__recovery_panel.date_picker(
            {
                'year': str(timestamp.year),
                'month': timestamp.strftime("%B"),
                'date': str(timestamp.day),
                'hours': timestamp.hour,
                'minutes': timestamp.minute
            }
        )
        self.click_on_restore()

    @PageService()
    def click_on_restore(self):
        """Clicks on run restore and opens Select Restore Type page"""
        self.__recovery_panel.click_button(self.__admin_console.props['label.globalActions.restore'])

    @PageService()
    def click_on_data_masking(self):
        """Clicks on data masking and opens data masking policies page"""
        self.__page_container.access_page_action(self.__admin_console.props['label.dataMasking'])
