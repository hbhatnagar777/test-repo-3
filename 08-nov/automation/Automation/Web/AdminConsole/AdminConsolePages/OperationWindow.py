# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
Main file for performing Operation window (Admin Console) related operations

Classes:

    OperationWindow()

Functions:

    add_operation_rule           :    Method to create Backup rule

    edit_operation_rule          :    Method to modify the operation rule

    delete_operation_rule        :    Method to Delete operation rule

    fetch_operation_rule_details :  Method to extract operation rule details from UI
"""

import re
import time

from dateutil.parser import parse

from Web.AdminConsole.Components.core import BlackoutWindow, CalendarView
from Web.AdminConsole.Components.dialog import Form, RModalDialog
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import PageService


class OperationWindow:
    """ Class for the Backup Window page """

    def __init__(self, admin_page):
        """
        Method to initiate Operation Window class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__admin_console.load_properties(self)

        self.operations = [
            'label.allowedOpsFDM', 'label.allowedOpsNFDM',
            'label.allowedOpsSF', 'label.transactionOps'
        ]
        self.admin_operations = [
            'label.auxCopy', 'label.backupCopy', 'label.upgradeSoftware'
        ]
        self.weeks = [
            'label.firstWeek', 'label.secondWeek', 'label.thirdWeek',
            'label.fourthWeek', 'label.lastWeek'
        ]
        self.all_weeks = ['label.allWeeks']
        # replace label names with the actual labels in page
        for label_list in [self.operations, self.admin_operations, self.weeks, self.all_weeks]:
            for i in range(len(label_list)):
                label_list[i] = self.__admin_console.props[label_list[i]]

        self.__driver = admin_page.driver
        self.__rtable = Rtable(admin_page)
        self.__blackout_window = Form(admin_page)
        self.__edit_dialog = RModalDialog(
            admin_page, title=self.__admin_console.props['label.operationWindow']
        )
        self.__window = BlackoutWindow(admin_page)
        self.__calendar = CalendarView(admin_page, date_only=True)
        self.__dropdown = RDropDown(admin_page)

    @PageService()
    def add_operation_rule(
            self,
            operation_rule_name,
            backup_operations='All',
            admin_operations=None,
            off_daytimes=None,
            off_weeks=None,
            between_dates=None,
            no_submit_schedule=False):

        """
        Method to create a new Backup Rule

        Args:
            operation_rule_name (str)       -   Name for operation rule to be created

            backup_operations (list/str)    -   Backup operations for blackout window
                                                Must be from below strings
                                                ['Full',
                                                'Incremental and Differential',
                                                'Synthetic Full', 'Transaction Log']
                                                Can be 'All' for all operations

            admin_operations (str/list)     -   Admin operations for blackout window
                                                Must be from below strings
                                                ['Auxiliary copy', 'Backup copy',
                                                'Upgrade software']
                                                Can be None to leave default

            off_daytimes    (dict)          -   Dict with each day of week key and timeranges list value
                                                each timerange can be like 'X-Y' or 'All day'
                                                [Note X,Y are integer hour times
                                                 X<Y, X>=12am,Y<12am]
                                                Example: {
                                                    'Monday': ['5am-6pm', '9pm-11pm'],
                                                    'Tuesday': ['All day'],
                                                    'Wednesday': ['12am-12pm']
                                                }

            off_weeks   (str/list)          -   The weeks to apply this blackout window on
                                                ['Every', 'First', 'Second', 'Third', 'Fourth', 'Last']
                                                Can be None to keep the default window setting

            between_dates   (list)          -   list with from and to date strings in any human format
                                                example: ['07/24/23', '1st of August 2023']

            no_submit_schedule  (bool)      -   Toggle whether schedules jobs must not be submitted
                                                during the window

        Returns:
            None

        Raises:
            Exception:
                if failed to create operation rule
        """

        self.__admin_console.click_button_using_text('Add')
        self.__blackout_window.fill_text_in_field("name", operation_rule_name)

        if backup_operations == 'All':
            self.__blackout_window.enable_toggle("operationAll")
        else:
            self.__blackout_window.disable_toggle("operationAll")
            self.__blackout_window.select_dropdown_values(drop_down_id="operations", values=backup_operations)
            if admin_operations is not None:
                self.__blackout_window.select_dropdown_values(drop_down_id="adminOperations", values=admin_operations)

        if off_daytimes is not None:
            self.__window.edit_blackout_window(off_daytimes)
        if off_weeks is not None:
            self.__blackout_window.select_dropdown_values(drop_down_id="weekOfTheMonth", values=off_weeks)
        if between_dates is not None:
            self.__blackout_window.enable_toggle("betweenDays")
            # set start date
            self.__calendar.open_calendar('Start date')
            start_date = parse(between_dates[0], dayfirst=False)
            self.__calendar.select_date({
                'day': start_date.day,
                'month': start_date.strftime("%B"),
                'year': start_date.year
            })
            # set end date
            self.__calendar.open_calendar('End date')
            end_date = parse(between_dates[1], dayfirst=False)
            self.__calendar.select_date({
                'day': end_date.day,
                'month': end_date.strftime("%B"),
                'year': end_date.year
            })
        else:
            self.__blackout_window.disable_toggle("betweenDays")
        if no_submit_schedule:
            self.__blackout_window.enable_toggle("doNotSubmitJob")
        else:
            self.__blackout_window.disable_toggle("doNotSubmitJob")
        self.__blackout_window.click_button_on_dialog('Save')
        self.__admin_console.check_error_message()

    @PageService()
    def edit_operation_rule(
            self,
            operation_rule_name,
            new_operation_rule_name=None,
            backup_operations=None,
            admin_operations=None,
            off_daytimes=None,
            off_weeks=None,
            between_dates=None,
            no_submit_schedule=None):
        """
        Method to modify an existing Backup Rule

        Args:

            operation_rule_name (str)    : Name of the existing operation rule

            new_operation_rule_name (str): New name for operation rule

            backup_operations (list/str)    -   Backup operations for blackout window
                                                Must be from below strings
                                                ['Full',
                                                'Incremental and Differential',
                                                'Synthetic Full', 'Transaction Log']
                                                Can be 'All' for all operations

            admin_operations (str/list)     -   Admin operations for blackout window
                                                Must be from below strings
                                                ['Auxiliary copy', 'Backup copy',
                                                'Upgrade software']
                                                Can be None to leave default

            off_daytimes    (dict)          -   Dict with each day of week key and timeranges list value
                                                each timerange can be like 'X-Y' or 'All day'
                                                [Note X,Y are integer hour times
                                                 X<Y, X>=12am,Y<12am]
                                                Example: {
                                                    'Monday': ['5am-6pm', '9pm-11pm'],
                                                    'Tuesday': ['All day'],
                                                    'Wednesday': ['12am-12pm']
                                                }

            off_weeks   (str/list)          -   The weeks to apply this blackout window on
                                                ['Every', 'First', 'Second', 'Third', 'Fourth', 'Last']
                                                Can be None to keep the default window setting

            between_dates   (list)          -   list with from and to date strings in any human format
                                                example: ['07/24/23', '1st of August 2023']

            no_submit_schedule  (bool)      -   Toggle whether schedules jobs must not be submitted
                                                during the window

        Returns:
            None

        Raises:
            Exception:
                if failed to modify a operation rule

        """
        if not self.__blackout_window.is_dialog_present():
            self.__rtable.access_action_item(
                operation_rule_name, self.__admin_console.props['action.edit'])
            time.sleep(12)
        if new_operation_rule_name:
            self.__blackout_window.fill_text_in_field(element_id="name", text=new_operation_rule_name)
        if backup_operations == 'All':
            self.__blackout_window.enable_toggle("operationAll")
        elif backup_operations is not None:
            self.__blackout_window.disable_toggle("operationAll")
            self.__blackout_window.select_dropdown_values(drop_down_id="operations", values=backup_operations)
        if admin_operations is not None:
            self.__blackout_window.select_dropdown_values(drop_down_id="adminOperations", values=admin_operations)
        if off_daytimes is not None:
            self.__window.edit_blackout_window(off_daytimes)
        if off_weeks is not None:
            self.__blackout_window.select_dropdown_values(drop_down_id="weekOfTheMonth", values=off_weeks)
        if between_dates is not None:
            self.__blackout_window.enable_toggle("betweenDays")
            # set start date
            self.__calendar.open_calendar('Start date')
            start_date = parse(between_dates[0], dayfirst=False)
            self.__calendar.select_date({
                'day': start_date.day,
                'month': start_date.strftime("%B"),
                'year': start_date.year
            })
            # set end date
            self.__calendar.open_calendar('End date')
            end_date = parse(between_dates[1], dayfirst=False)
            self.__calendar.select_date({
                'day': end_date.day,
                'month': end_date.strftime("%B"),
                'year': end_date.year
            })
        else:
            self.__blackout_window.disable_toggle("betweenDays")
        if no_submit_schedule is not None:
            if no_submit_schedule:
                self.__blackout_window.enable_toggle("doNotSubmitJob")
            else:
                self.__blackout_window.disable_toggle("doNotSubmitJob")
        self.__edit_dialog.click_submit()

    @PageService()
    def delete_operation_rule(self, operation_rule_name):
        """
        Method to delete a Operation Rule

        Args:
            operation_rule_name (str)   :   name of the Backup rule to be deleted

        Raises:
            Exception:
                if failed to delete a operation rule
        """
        self.__rtable.access_action_item(
            operation_rule_name, self.__admin_console.props['action.delete'])
        self.__admin_console.click_button('Yes')
        self.__admin_console.check_error_message()

    @PageService()
    def read_all_operation_rules(self):
        """
        Method to read all the operation windows in table

        Returns:
            dict    -   dict with operation window name as key and its details value
        """
        count, rows_data = self.__rtable.get_rows_data(id_column='Name')
        all_details = {}
        for op_name in rows_data:
            between_dates = rows_data[op_name]['Dates']
            between_dates = None if between_dates == 'Not set' else between_dates.split(' to ')

            off_daytimes = rows_data[op_name]['Do not run between the following time intervals']
            off_daytimes = off_daytimes.replace(':00', '')
            off_daytimes = re.split(r', (?=[A-Z])', off_daytimes)
            off_daytimes = {
                day.strip(): {"".join(window.split()) for window in timerange.strip().split(', ')}
                for daytime in off_daytimes
                for day, timerange in [daytime.split(' : ', 1)]
            }

            all_details[op_name] = {
                'between_dates': between_dates,
                'off_daytimes': off_daytimes
            }
        return all_details

    @PageService()
    def fetch_operation_rule_details(self, operation_rule_name):
        """
        Method to extract operation rule details from UI (table)

        Args:
            operation_rule_name (str) : name of the operation rule, details to be fetched for

        Returns:
            operation_rule_details (dict) : dictionary containing operation rule values displayed in UI
                                            (in same format as required for input)
                Eg. - operation_rule_details = {
                            'between_dates': ['12 Jun, 2023', '30 Jun 2023'],
                            'off_daytimes': {'MONDAY': ['12am-3pm', '5pm-7pm'], ...}
                        }
        """
        count, rows_data = self.__rtable.get_rows_data(search=operation_rule_name, id_column='Name')
        between_dates = rows_data[operation_rule_name]['Dates']
        between_dates = None if between_dates == 'Not set' else between_dates.split(' to ')

        off_daytimes = rows_data[operation_rule_name]['Do not run between the following time intervals']
        off_daytimes = re.split(r', (?=[A-Z])', off_daytimes)
        off_daytimes = {
            day.strip(): ["".join(window.split()) for window in time.strip().split(', ')]
            for daytime in off_daytimes
            for day, time in [daytime.split(' : ', 1)]
        }

        return {
            'between_dates': between_dates,
            'off_daytimes': off_daytimes
        }

    @PageService()
    def fetch_all_operation_rule_details(self, operation_rule_name):
        """
        Method to extract all operation rule details from Edit dialog

        Args:
            operation_rule_name (str)   -   name of the operation rule

        Returns:
            operation_rule_dict (dict)  -   dictionary with all details about this operation rule
        """
        details = {
            'between_dates': None,
            'admin_operations': None
        }
        if not self.__blackout_window.is_dialog_present():
            self.__rtable.access_action_item(operation_rule_name, 'Edit')
            time.sleep(12)
        details['operation_rule_name'] = self.__blackout_window.get_text_in_field("name")
        if self.__blackout_window.toggle.is_enabled(id="operationAll"):
            details['backup_operations'] = 'All'
        else:
            details['backup_operations'] = \
                self.__dropdown.get_selected_values("operations")
            details['admin_operations'] = \
                self.__dropdown.get_selected_values("adminOperations")
        details['off_daytimes'] = self.__window.get_blackout_window_config()
        details['off_weeks'] = \
            self.__dropdown.get_selected_values("weekOfTheMonth")
        if self.__blackout_window.toggle.is_enabled(id="betweenDays"):
            details['between_dates'] = [
                self.__calendar.read_date("Start date"),
                self.__calendar.read_date("End date")
            ]
        details["no_submit_schedule"] = self.__blackout_window.toggle.is_enabled(id="doNotSubmitJob")
        self.__edit_dialog.click_cancel()
        return details
