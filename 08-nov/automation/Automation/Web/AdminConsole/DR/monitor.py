# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on replication monitor page

"""
from selenium.webdriver.common.by import By
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.table import Rtable, CVTable
from Web.AdminConsole.Components.panel import RModalPanel, ModalPanel, DropDown
from Web.AdminConsole.Components.dialog import RModalDialog, ModalDialog
from Web.AdminConsole.DR.test_failover_vms import TestFailoverVMs
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
from Web.AdminConsole.DR.pair_details import PairDetailsOperations
from Web.AdminConsole.DR.fs_replication import ConfigureBLR, ReplicaCopy
from Web.Common.exceptions import CVWebAutomationException


class EditSchedule:
    """Modal to edit a schedule for reverse replication"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__drop_down = DropDown(self.__admin_console)

    @WebAction()
    def get_schedule_name(self) -> str:
        """
        Gets the schedule name from the schedule field in the modal
        Returns: The schedule name
        """
        input_element_xpath = f"//input[@id='name']"
        return (self.__admin_console.driver.find_element(By.XPATH, input_element_xpath)
                .get_property('value'))

    @PageService()
    def set_schedule_name(self, schedule_name: str):
        """
        Sets the schedule name
        Args:
            schedule_name (str): The name of the schedule
        """
        self.__admin_console.fill_form_by_id('name', schedule_name)

    @WebAction()
    def get_repeat_frequency(self) -> str:
        """
        Gets the repeat frequency of the schedule
        Returns: String of frequency value in form <# hours> hours,<# minutes> minutes
        """
        input_element_xpath = ["//input[@id='repeat.hrs']", "//input[@id='repeat.mins']"]
        return (self.__admin_console.driver.find_element(By.XPATH, "//input[@id='repeat.hrs']")
                .get_property('value') + ' hours,' +
                self.__admin_console.driver.find_element(By.XPATH, "//input[@id='repeat.mins']")
                .get_property('value') + ' minutes')

    @PageService()
    def delete(self):
        """Clicks the delete button which deletes the schedule"""
        self.__admin_console.click_button(id="Delete")

    @PageService()
    def cancel(self):
        """Closes the modal"""
        self.__admin_console.click_button(id="Cancel")

    @PageService()
    def save(self):
        """Saves the modal"""
        self.__admin_console.click_button(id="addScheduleModal_button_#6833")


class ReplicationMonitor:
    """All operation specific to Replication monitors goes here"""

    def __init__(self, admin_console):
        self.__admin_console : AdminConsole = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__alert = Alert(self.__admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @PageService()
    def __filter_row_select(self, source, replication_group=None, select=True):
        """ Selects the row after applying the filters for source and replication group
        Args:
            source(str/list): Source vm name/list
            replication_group(str or None): replication group name
            select(bool): whether to select the row
        """
        if replication_group:
            self.__table.apply_filter_over_column(self.__label['label.replicationGroup'], replication_group)
        if isinstance(source, str):
            self.__table.apply_filter_over_column(self.__label['label.replicationSource'], source)
            source = [source]
        if select:
            self.__table.select_rows(source)

    @PageService()
    def has_replication_group(self, group_name):
        """
        Check if specified replication group exists
        Args:
            group_name           (str):      Replication group name
        Returns                  (bool):     True if replication group exists or False otherwise
        """
        return self.__table.is_entity_present_in_column(self.__label['label.replicationGroup'], group_name)

    @PageService()
    def get_replication_group_details(self, source, replication_group=None):
        """
        Read replication monitor page content for specific group name
        Args:
            replication_group   (str or None): Specify replication group name
        Returns                 (dict): table content
        """
        self.__filter_row_select(source, replication_group, select=False)
        data = self.__table.get_table_data()
        if data.get(self.__label['label.replicationSource']):
            return data
        if replication_group:
            raise CVWebAutomationException("Replication group [%s] not in replication monitor page"
                                           % replication_group)
        return

    @PageService()
    def access_source(self, source, replication_group):
        """
        Opens the vm with the given name
        Args:
            source              (str):  name of vm
            replication_group    (str or None): replication group name
        Raises:
            Exception:
                If there is no vm with given name
        """
        self.__filter_row_select(source, replication_group, select=False)
        self.__table.access_link(source)

    @PageService()
    def _perform_pair_level_dr_operation(self, source, replication_group, operation_label, checkbox_id=None, select=False):
        """
        Perform DR operation.

        Args:
            source (str): The source of the DR operation.
            replication_group (str): The replication group for the DR operation.
            operation_label (str): The label of the operation to be performed.
            checkbox_id (str, optional): The ID of the checkbox to be selected/deselected. Defaults to None.
            select (bool, optional): Select or deselect the checkbox. Defaults to False.

        Returns:
            str: The job ID obtained from the popup alert.
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_menu_from_dropdown(menu_id=operation_label,
                                               label=self.__label['label.failover'])
        self.__dialog.select_deselect_checkbox(
            checkbox_id=checkbox_id, select=select) if checkbox_id else None
        self.__dialog.click_submit(wait=False)
        return self.__alert.get_jobid_from_popup()

    @PageService()
    def unplanned_failover(self, source, replication_group=None, retain_disk_snapshots=True):
        """Performs unplanned failover (group level)"""
        job_id = (self._perform_pair_level_dr_operation(source=source,
                                                        replication_group=replication_group,
                                                        operation_label=self.__label['label.unplannedFailover'])
                  if retain_disk_snapshots
                  else self._perform_pair_level_dr_operation(source=source,
                                                             replication_group=replication_group,
                                                             operation_label=self.__label['label.unplannedFailover'],
                                                             checkbox_id='retainDiskSnapShot',
                                                             select=retain_disk_snapshots))
        return job_id

    @PageService()
    def planned_failover(self, source, replication_group=None, retain_disk_snapshots=True):
        """Performs planned failover (group level)"""
        job_id = (self._perform_pair_level_dr_operation(source=source,
                                                        replication_group=replication_group,
                                                        operation_label=self.__label['label.plannedFailover'])
                  if retain_disk_snapshots
                  else self._perform_pair_level_dr_operation(source=source,
                                                             replication_group=replication_group,
                                                             operation_label=self.__label['label.plannedFailover'],
                                                             checkbox_id='retainDiskSnapShot',
                                                             select=retain_disk_snapshots))
        return job_id

    @PageService()
    def undo_failover(self, source, replication_group=None):
        """Performs undo failover (group level)"""
        job_id = self._perform_pair_level_dr_operation(source=source,
                                                       replication_group=replication_group,
                                                       operation_label=self.__label['label.failback'],
                                                       checkbox_id='discardChanges',
                                                       select=True)
        return job_id

    @PageService()
    def failback(self, source, replication_group=None):
        """Performs failback (group level)"""
        job_id = self._perform_pair_level_dr_operation(source=source,
                                                       replication_group=replication_group,
                                                       operation_label=self.__label['label.failback'])
        return job_id

    @PageService()
    def mark_for_full_replication(self, source, replication_group):
        """
         This method marks the VM for full replication

        Args:
            source            (string)    : vm whose replication is to be started immediately
            replication_group (string)    : replication group name
        Raises:
            Exception:
                Replication action item is not present

                Wrong job text is displayed
        """
        sync_status = self.sync_status(source, replication_group)
        expected_sync_status = [self.__label['failoverSynsStatus.VSAREP_COMPLETE'],
                                self.__label['failoverSynsStatus.VSAREP_ENABLED'],
                                self.__label['failoverSynsStatus.VSAREP_PENDING']]

        if sync_status in expected_sync_status:
            self.__filter_row_select(source, replication_group)
            self.__table.access_menu_from_dropdown(menu_id=self.__label['action.replication.markForSync'],
                                                   label=self.__label['label.replication'])
            self.__dialog.click_submit(wait=False)
            status = self.__alert.get_content()
        else:
            raise CVWebAutomationException("status [%s] of source is not in expected state[%s]"
                                           % (sync_status, str(expected_sync_status)))
        return status

    @PageService()
    def test_boot_vm(self, source, replication_group):
        """
        This method test the boot for VM
        Args:
            source            (str/list)    : specify the source name list
            replication_group (string)    : replication group name
        Raises:
            Exception:
                Test boot VM action item is not present
                Wrong job text is displayed
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu('Test boot VM')
        self.__dialog.click_yes_button()
        job_id = self.__admin_console.get_jobid_from_popup()
        return job_id

    @PageService()
    def sync_status(self, source, replication_group):
        """
        Returns the sync status of vm
        Args:
            source              (String) : source name whose sync status has to be checked
            replication_group   (string) : replication group name
        Returns:
            Sync Status of the VM
        Raises:
            Exception:
                Not able to find the staus for VM
        """
        self.__filter_row_select(source, replication_group, select=False)
        sync_status = self.__table.get_column_data(self.__label['label.column.status'])
        if not sync_status:
            raise CVWebAutomationException("Source[%s] and replication_group[%s] row is not "
                                           "found in monitor page" % (source, replication_group))
        return sync_status[0]

    def replicate_now(self, source, replication_group):
        """
        Triggers replicate now by filtering source and replication group name in monitor page
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_menu_from_dropdown(menu_id=self.__label['action.runReplication'],
                                               label=self.__label['label.replication'])
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def view_details(self, source, replication_group):
        """
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu("Details")

    @PageService()
    def delete(self, source: str | list, replication_group: str = None, delete_destination=False):
        """
        Deletes the specified source from the replication group.

        Args:
            source
                (list): List of source VMs to be deleted.
                (str): Source VM to be deleted.
            replication_group (str, optional): Replication group to which the sources belong. Defaults to None.
            delete_destination (bool, optional): Flag indicating whether to delete the destination as well. Defaults to False.

        Returns:
            str: Job ID of the deletion operation.
        """
        self.__filter_row_select(source, replication_group)
        # Label - To be updated once a unique label is available
        self.__table.access_toolbar_menu(menu_id='Delete')
        self.__dialog.select_deselect_checkbox(checkbox_id="deleteVMFromHypervisor",
                                               select=delete_destination)
        self.__dialog.click_submit(wait=False)
        return self.__alert.get_jobid_from_popup(hyperlink=True)

    @PageService()
    def enable_validation(self, source, replication_group):
        """
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu("EnabledValidation")

    @PageService()
    def disable_validation(self, source, replication_group):
        """
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu("DisabledValidation")

    @PageService()
    def disable_replication(self, source, replication_group):
        """
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu("VSAREP_DISABLED")

    @PageService()
    def enable_replication(self, source, replication_group):
        """
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu('VSAREP_ENABLED')

    @PageService()
    def validate_as_per_replication_group(self, source, replication_group):
        """
        Validate as Per Replication Group setting
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu("AsPerScheduleValidation")

    @PageService()
    def pit_fail_over(self, source, replication_group):
        """
        Point in Time Failover
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_toolbar_menu("VSAFailover")
        self.__table.access_toolbar_menu("PITFailover")
        self.__modal_panel.submit()

    @PageService()
    def enable_reverse_replication(self, source, replication_group):
        """
        Reverse repliaction action
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_menu_from_dropdown(menu_id=self.__label['action.reverseReplication'],
                                               label=self.__label['label.replication'])
        self.__dialog.click_yes_button()

    @PageService()
    def reverse_replication_schedule(self, source, replication_group):
        """
        Open the Reverse repliaction schedule modal
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.access_menu_from_dropdown(menu_id=self.__label['action.reverseReplication'],
                                               label=self.__label['label.replication'])
        edit_schedule = EditSchedule(self.__admin_console)
        return edit_schedule

    @PageService()
    def test_failover(self, source, replication_group=None):
        """
        Test Failover
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.context_menu_sequential_select(source, ['Failover', 'Test failover'])
        self.__admin_console.click_button(value="Yes")
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def view_test_failover_vms(self, source: str, replication_group=None):
        """
        Test Failover
        Args:
            source(str): Source name
            replication_group(str): replication group name
        """
        self.__filter_row_select(source, replication_group)
        self.__table.context_menu_sequential_select(source, ['Failover', 'View test failover VMs'])
        return TestFailoverVMs(self.__admin_console).get_all_vms_info()


class ContinuousReplicationMonitor:
    """
    This class is used to perform monitoring operations on the Continuous tab of the Replication monitor
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__table = CVTable(admin_console)
        self.__dialog = ModalDialog(admin_console)
        self.__modal_panel = ModalPanel(admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @WebAction()
    def __get_report(self):
        """Gets the values for each entity in the dash pane component"""
        values = [int(element.text) for element in
                  self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'entities')]"
                                                        "//span[contains(@class, 'entity-value')]")]
        labels = [element.get_attribute('title') for element in
                  self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'entities')]"
                                                        "//a[contains(@class, 'entity-container')]")]
        return dict(zip(labels, values))

    @WebAction()
    def __open_grid_menu(self):
        """Opens the filter menu present in the table for views and column selection"""
        self.__driver.find_element(By.XPATH, "//*[@class='ui-grid-icon-container']").click()

    @WebAction()
    def __select_menu_option_column(self, action_name):
        """
        Selects the action in the grid menu
        Args:
            action_name (str): Name of the action to be selected
        """
        self.__driver.find_element(By.XPATH, "(//*[@class='ui-grid-menu-inner']//button[contains(text(), '{}')])[2]"
                                   .format(action_name)).click()

    @WebAction()
    def __select_menu_option(self, action_name):
        """
        Selects the action in the grid menu
        Args:
            action_name (str): Name of the action to be selected
        """
        self.__driver.find_element(By.XPATH, "//*[@class='ui-grid-menu-inner']//button[contains(text(), '{}')]"
                                   .format(action_name)).click()

    @WebAction()
    def __click_view_dropdown(self):
        """Clicks on the filters dropdown"""
        self.__driver.find_element(By.XPATH, "//*[contains(@class, 'view-selection')]").click()

    @WebAction()
    def __click_view(self, name='All'):
        """Clicks on the view name available on the view dropdown"""
        self.__driver.find_element(By.XPATH, "//*[contains(@class, 'view-selection')]//*[contains(text(), '{}')]"
                                   .format(name)).click()

    @WebAction()
    def __fill_rule_form(self, rule_id, value):
        """
        Fills the rules inputs using the class name
            index: index# of the rule
            value: Value to be entered
        """
        element = self.__driver.find_element(By.XPATH, "//*[@id='{}']//input".format(rule_id))
        element.clear()
        element.send_keys(value)

    @property
    @PageService()
    def report(self):
        """Gets the report from the web action
        eg: {
            'Total pairs': 0,
            'Point in time recovery pairs': 0,
            'Latest recovery pairs': 0,
            'Application consistent pairs': 0,
            'Pairs with lag': 0
            }
        """
        return self.__get_report()

    @PageService()
    def create_view(self, view_name, rules, set_default=False):
        """
        Creates a new view in the replication pairs for sorting and filtering
        Args:
            view_name: Name of the view to be created
            rules: A dictionary of rules in the form of {<column-name>: <value>}
                    eg: {'Source': 'client1'}
            set_default: Sets the view as default when opening the replication monitor
        """
        self.__open_grid_menu()
        self.__select_menu_option(self.__label['label.createView'])
        self.__admin_console.wait_for_completion()

        self.__admin_console.fill_form_by_id("viewName", view_name)
        if set_default:
            self.__admin_console.checkbox_select("chkSetAsDefault")
        num_rules = len(rules)
        for rule_idx, rule_key in enumerate(rules):
            self.__admin_console.select_value_from_dropdown(f'rule-{rule_idx}', rule_key)
            self.__fill_rule_form(f'ruleFilter-{rule_idx}', rules[rule_key])
            if rule_idx < num_rules - 1:
                # Click add rule only if rule is not the last
                self.__admin_console.click_button(self.__label['label.addRule'])
        self.__modal_panel.submit()
        self.__admin_console.check_error_message()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_grid_option(self, action_name):
        """Checks whether a given view exists or not"""
        self.__open_grid_menu()
        self.__select_menu_option_column(action_name)
        self.__open_grid_menu()

    @PageService()
    def check_view(self, name):
        """Checks whether a given view exists or not"""
        return self.__admin_console.check_if_entity_exists("xpath", "//*[contains(@class, 'view-selection')]"
                                                                    "//*[contains(text(), '{}')]".format(name))

    @PageService()
    def select_view(self, view_name):
        """Selects a view based on the name provided"""
        if not self.check_view(view_name):
            raise CVWebAutomationException('The view {} does not exist'.format(view_name))
        self.__click_view_dropdown()
        self.__click_view(view_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def delete_view(self, view_name):
        """Removes the view from the command center"""
        if not self.check_view(view_name):
            raise CVWebAutomationException('Cannot delete the view {} because it does not exist'.format(view_name))
        self.__open_grid_menu()
        self.__select_menu_option(self.__label['label.deleteView'])
        self.__admin_console.wait_for_completion()

        self.__admin_console.select_value_from_dropdown("deleteViewName", view_name)
        self.__modal_panel.submit()
        self.__admin_console.check_error_message()

    @PageService()
    def access_action(self, action_name, source_client=None, destination_client=None):
        """Access the actions options present in the action button for the first row"""
        row_index = 0
        if source_client and destination_client:
            row_indices, _ = self.get_replication_group_details(source_client, destination_client)
            if not row_indices:
                raise CVWebAutomationException(f"Pair {source_client} -> {destination_client} not found")
            row_index = row_indices[0]
        self.__table.access_action_item(action_item=action_name, row_index=row_index)

    @PageService()
    def has_replication_group(self, source_client, destination_client):
        """
        Returns the boolean on whether the pair exists or not
        Args:
            source_client       (str): Name of the source client
            destination_client  (str): Name of the destination client
        Returns: true, if row exists, false otherwise
        """
        row_indices, details = self.__table.filter_values_from_table({
            self.__label['label.source']: source_client,
            self.__label['label.destination']: destination_client,
        })
        return len(details) > 0

    @PageService(log=False)
    def get_replication_group_details(self, source_client, destination_client):
        """
        Gets the row data for the selected replication pair
        Args:
            source_client       (str): Name of the source client
            destination_client  (str): Name of the destination client
        Returns: list of row indices, list of table content
        """
        if not self.has_replication_group(source_client, destination_client):
            raise CVWebAutomationException("No pair {}, {} found".format(source_client, destination_client))
        group_details, row_indices = self.__table.filter_values_from_table({
            self.__label['label.source']: source_client,
            self.__label['label.destination']: destination_client,
        })
        return row_indices, group_details

    @PageService()
    def search_vm(self, source_vm_name):
        """
        Search a VM on page
        Args:
            source_vm_name       (str): Name of the source client
        """
        self.__table.search_for(source_vm_name)

    @PageService()
    def get_column_data(self, column_name, get_data=False):
        """
        Gets the column data for the selected replication pair
        Args:
            column_name       (str): Name of column of the table eg. "Source","Destination"
            get_data          (bool): Specify True if want to get all the column data else False
        Returns: list
        """
        details = self.__table.get_column_data(column_name, get_data)
        return details

    @PageService(log=False)
    def sync_status(self, source_client, destination_client):
        """
        Returns the synchronisation status of the FIRST replication pair of the source client
        """
        _, pair_details = self.get_replication_group_details(source_client, destination_client)
        if not pair_details:
            raise CVWebAutomationException(f"No pair found {source_client} -> {destination_client}")
        return pair_details[0].get(self.__label['label.syncStatus'])

    @PageService()
    def access_pair_details(self, source_client, destination_client=None):
        """
        Clicks on the FIRST replication pair for the source client name
        To make sure you select the right pair, ensure to pass destination_client
        """
        pair_details = PairDetailsOperations(self.__admin_console)
        if destination_client is None:
            self.__table.access_link(source_client)
        else:
            row_indices, _ = self.get_replication_group_details(source_client, destination_client)
            if not row_indices:
                raise CVWebAutomationException(f"Pair {source_client} -> {destination_client} not found")
            self.__table.access_link(row_index=row_indices[0])
        return pair_details

    @PageService()
    def resync(self, source_client=None, destination_client=None):
        """
        Performs the resync operation on the FIRST replication pair for the source client
        To make sure you select the right pair, ensure to use pass source_client and destination_client
        """
        self.access_action(self.__label['action.resync'], source_client, destination_client)

    @PageService()
    def stop(self, source_client=None, destination_client=None):
        """
        Performs the stop operation on the FIRST replication pair for the source client
        To make sure you select the right pair, ensure to use pass source_client and destination_client
        """
        self.access_action(self.__label['action.stop'], source_client, destination_client)

    @PageService()
    def suspend(self, source_client=None, destination_client=None):
        """
        Performs the suspend operation on the FIRST replication pair for the source client
        To make sure you select the right pair, ensure to use pass source_client and destination_client
        """
        self.access_action(self.__label['action.suspend'], source_client, destination_client)

    @PageService()
    def Undo_failover(self, source_client=None, destination_client=None):
        """
        Performs the resume operation on the FIRST replication pair for the source client
        To make sure you select the right pair, ensure to use pass source_client and destination_client
        """
        self.access_action(self.__label['label.undoFailover'], source_client, destination_client)

    @PageService()
    def start(self, source_client=None, destination_client=None):
        """
        Performs the start operation on the FIRST replication pair for the source client
        To make sure you select the right pair, ensure to use pass source_client and destination_client
        """
        self.access_action(self.__label['action.start'], source_client, destination_client)

    @PageService()
    def delete_pair(self, source_client=None, destination_client=None):
        """
        Performs the suspend operation on the FIRST replication pair for the source client
        To make sure you select the right pair, ensure to use pass source_client and destination_client
        """
        self.access_action(self.__label['action.deletePair'], source_client, destination_client)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def edit_recovery_options(self, source_client=None, destination_client=None):
        """
        Accesses the Edit recovery options and then returns the RecoveryPointStore used to configure the recovery
        options on the page
        """
        rpstore = RecoveryPointStore(self.__admin_console)
        self.access_action(self.__label['action.editRecoveryOptions'], source_client, destination_client)
        return rpstore

    @PageService()
    def edit_replication_volumes(self, source_client=None, destination_client=None):
        """
        Accesses the Edit replication volumes and then returns the ConfigureBLR object used to configure the volumes
        on the page
        """
        blr = ConfigureBLR(self.__admin_console)
        self.access_action(self.__label['label.editReplicationVolume'], source_client, destination_client)
        return blr

    @PageService()
    def create_replica_copy(self, source_client=None, destination_client=None):
        """
        Accesses the replica copy pair action for a replication pair, and return the ReplicaCopy object which
        can be used to configure a replica copy
        """
        replica_copy = ReplicaCopy(self.__admin_console)
        self.access_action(self.__label['action.createNewPermMount'], source_client, destination_client)
        self.__admin_console.wait_for_completion()
        return replica_copy

    @PageService()
    def continuous_test_bootvm(self, test_boot_options, source_client=None, destination_client=None):
        """
        This method test the boot for VM for contnuous pair
        Args:
            test_boot_options (dict)      : Specify Test VM options {"key":"value"}
                                          Eg:{
                                                "test_vm_name":"vm name",
                                                "expiration_time":"1:2",
                                                "recoveryType":"Oldest point in time or Latest recovery point",
                                                "recovery_point":"Jun17, 2021 2:37:13 PM"-->can get the rp details using
                                                get_all_rp_stats
                                            }
        Raises:
            Exception:
                Test boot VM action item is not present
                Wrong job text is displayed
        """
        days, hours = test_boot_options['expiration_time'].split(":")
        self.access_action(self.__label['action.createNewTestBootFailoverEnabled'], source_client, destination_client)
        self.__admin_console.fill_form_by_id("newVMName", test_boot_options['test_vm_name'])
        self.__admin_console.fill_form_by_id("days", days)
        self.__admin_console.fill_form_by_id("hours", hours)
        self.__admin_console.select_value_from_dropdown('recoveryType', test_boot_options['recovery_type'])
        if test_boot_options['recovery_type'] == "Recovery point time":
            self.__admin_console.select_value_from_dropdown('crashConsistentRPTDetailDate',
                                                            test_boot_options['recovery_point'])
        if test_boot_options['recovery_type'] == "Application consistent recovery point time":
            self.__admin_console.select_value_from_dropdown('appConsistentRPTDetailDate',
                                                            test_boot_options['recovery_point'])
        self.__modal_panel.submit(wait_for_load=False)
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def clone_vm(self, clone_vm_options, source_client=None, destination_client=None):
        """
        This method performs the clone vm operation for continuous pair
        Args:
            clone_vm_options (dict)      : Specify Clone VM options {"key":"value"}
                              Eg:{
                                    "clone_vm_name":"vm name",
                                    "recoveryType":"Oldest point in time or Latest recovery point",
                                    "recovery_point":"Jun17, 2021 2:37:13 PM"-->can get the rp details using
                                    get_all_rp_stats
                                }
            source_client                   : Specify source client name
            destination_client              : Specify destination client name
        Raises:
            Exception:
                Clone VM action item is not present
                Wrong job text is displayed
        """
        self.access_action(self.__label['action.createNewPermBootFailoverEnabled'], source_client, destination_client)
        self.__admin_console.fill_form_by_id("newVMName", clone_vm_options['clone_vm_name'])
        self.__admin_console.select_value_from_dropdown('recoveryType', clone_vm_options['recovery_type'])
        if clone_vm_options['recovery_type'] == "Recovery point time":
            self.__admin_console.select_value_from_dropdown('crashConsistentRPTDetailDate',
                                                            clone_vm_options['recovery_point'])
        if clone_vm_options['recovery_type'] == "Application consistent recovery point time":
            self.__admin_console.select_value_from_dropdown('appConsistentRPTDetailDate',
                                                            clone_vm_options['recovery_point'])
        self.__modal_panel.submit(wait_for_load=False)
        return self.__admin_console.get_jobid_from_popup()
