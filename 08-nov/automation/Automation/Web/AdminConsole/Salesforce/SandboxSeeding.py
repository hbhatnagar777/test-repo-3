# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on a Salesforce sandbox seeding page

SalesforceSandboxSeed:

    create_new_template()                --  Creates new seeding template
    __add_seed_objects()             --  Adds objects to the template under creation
    __select_parent_and_child_level  --  Selects parent and child seeding levels for the objects
    __select_records_type            --  Selects record seed type for the objects
    seed_sandbox                     --  Runs seeding job for a template

"""
from dataclasses import dataclass

from Web.AdminConsole.Salesforce.constants import ParentLevel, DependentLevel, SeedRecordType
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable


@dataclass(frozen=True)
class TemplateConfig:
    """Read only class to hold configuration definitions for seeding template"""
    sobject: str
    record_type: SeedRecordType
    parent_level: ParentLevel = ParentLevel.NONE
    dependent_level: DependentLevel = DependentLevel.NONE
    param: 'typing.Any' = None


class SalesforceSandboxSeed:
    """Class for Salesforce Sandbox Seeding page"""

    def __init__(self, admin_console):
        """
        Init method for this class

        Args:
            admin_console (Web.AdminConsole.Helper.AdminConsoleBase.AdminConsoleBase): Object of AdminConsoleBase class

        Returns:
            None:
        """
        self.__admin_console = admin_console
        self.__page_container = PageContainer(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__rrestore = RSalesforceRestore(self.__admin_console)

    @PageService()
    def create_new_template(self, temp_name, configs, masking=None):
        """
               Creates new sandbox seeding template

               Args:
                   temp_name: name of the seeding template
                   configs: list of TemplateConfig objects
                   masking: name of data masking policy to use
               Returns:
                   temp_name: created template name
               """
        self.__admin_console.click_button(value="Create new")
        self.__admin_console.fill_form_by_name("name", temp_name)
        if masking:
            self.__rdropdown.select_drop_down_values(values=[masking],
                                                     drop_down_id="maskingPolicy")
        for config in configs:
            self.__add_config(config)
        self.__rpanel.click_button(self.__admin_console.props["action.save"])
        return temp_name

    @PageService()
    def __add_config(self, config: TemplateConfig):
        """
               Add objects to a seeding template

               Args:
                    config: object of TemplateConfig class

               Returns:
                   None:
               """

        self.__admin_console.click_button(value=self.__admin_console.props["label.add"])
        self.__rdropdown.select_drop_down_values(values=[config.sobject], drop_down_id="objectNames")
        self.__select_records_type(config.record_type, config.param)
        self.__select_parent_and_child_level(config.parent_level, config.dependent_level)
        self.__rdialog.click_submit()

    @PageService()
    def __select_parent_and_child_level(self, parent_level=ParentLevel.NONE, dependent_level=DependentLevel.NONE):
        """
              select parent and child levels

              Args:
                   parent_level: Enum of type ParentLevel
                   dependent_level: Enum of type DependentLevel
              Returns:
                  None:

                  """
        self.__admin_console.scroll_into_view("restoreParentType")
        self.__rdropdown.select_drop_down_values(
            values=[parent_level.value],
            drop_down_id="restoreParentType")
        if parent_level is ParentLevel.NONE:
            self.__rdialog.click_button_on_dialog(id="Cancel")
        self.__rdropdown.select_drop_down_values(
            values=[dependent_level.value],
            drop_down_id="dependentRestoreLevel")

    @PageService()
    def __select_records_type(self, record_type: SeedRecordType, param):
        """
              select record type and corresponding number

              Args:
                   record_type: object of class SeedRecordType
              Returns:
                  None:

          """
        self.__rdropdown.select_drop_down_values(
            values=[record_type.value],
            drop_down_id="typex")

        if record_type == SeedRecordType.SQL:
            self.__rrestore.apply_simplified_filter(param)
            return

        child_id = {
            SeedRecordType.ALL_RECORDS: None,
            SeedRecordType.RECENT_RECORDS:  "nRows",
            SeedRecordType.UPDATED_DAYS:  "nDays"
        }
        child_id = child_id[record_type]

        if child_id:
            self.__admin_console.fill_form_by_name(name=child_id, value=param)

    @PageService()
    def seed_sandbox(self, temp_name, dest_org, options=None):
        """
               Fill seeding options and run the seed job
               Args:
                   temp_name: name of the seeding template
                   dest_org: destination org to which seeding should be done
                   options: {
                     disable_triggers (bool): (default is True),
                     insert_null (bool): (default is False),
                     associate_ownership: (default is True),
                     masking_policies (list[str]): List of data masking policies to select
                 }
               Returns:
                   Job id
               """

        self.__rtable.access_action_item(entity_name=temp_name,
                                         action_item=self.__admin_console.props["action.seedSandbox"])
        return self.__rrestore.seed_sandbox(dest_org, options or {})

    @PageService()
    def access_overview_tab(self):
        """
        Clicks on overview tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.tab.overview'])
