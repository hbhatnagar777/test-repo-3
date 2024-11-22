# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on Operation Window page.

Utility Functions:

    seconds_to_time     -   convert seconds to human readable string

    time_to_seconds     -   convert human readable time string to seconds

    random_timerange    -   generate list of random timeranges

    random_window       -   generate random op window config

    random_dates        -   generate pair of random to and from date

    weekrange           -   util to get week day index range

    in_range            -   util to check if timerange lies within list of ranges

    validate_daytimes   -   compares UI returned format daytimes with API returned format

Classes:

    OperationWindowHelper()

Methods:

    api_blackout_windows    -   gets data from API

    ui_blackout_windows     -   gets data from UI (table)

    setup_bw_page           -   util to setup blackout window page

    validate_bw_table       -   teststep to validate bw table

    validate_bw_creation    -   teststep to validate bw creation

    validate_bw_edit        -   teststep to validate bw edit

    validate_bw_delete      -   teststep to validate bw deletion

    clean_up                -   method to clean up any unintended entities

"""
import re
from datetime import datetime, timedelta
import random
import numpy as np
from dateutil.tz import tz
from deepdiff import DeepDiff
from dateutil.parser import parse
import time
import calendar
from cvpysdk.commcell import Commcell

from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.AdminConsolePages.OperationWindow import OperationWindow
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


def seconds_to_time(seconds: int) -> str:
    """
    Converts number of seconds to HH:MM time format str

    Args:
        seconds (int)   -   time in seconds
    
    Returns:
        time_str    (str)   -   the HH:MM format time
    """
    time_str = time.strftime('%I%p', time.gmtime(seconds))
    return time_str.lstrip('0').lower()


def time_to_seconds(timestr: str) -> int:
    """
    Converts HH:MM am/pm time string to number of seconds

    Args:
        timestr (str)   -   time string in HHMMam/pm format

    Returns:
        seconds (int)   -   total seconds passed since 00:00
    """
    time, merid = timestr[:-2], timestr[-2:]
    if merid.lower() == 'pm':
        return int(time) + 12
    else:
        return int(time)


def _list_of_diffs(obj_diff) -> list[str]:
    """
    Util to get list of error messages indicating what properties did not merge among the entities

    Args:
        obj_diff    -   a deepdiff object with comparison results

    Returns:
        errors  (list)  -   list of error strings indicating what did not match
    """
    errors = []
    for diff_type in obj_diff:
        errors.append(f'---------{diff_type}---------')
        if isinstance(obj_diff[diff_type], dict):
            for k, v in obj_diff[diff_type].items():
                errors.append(f'{k} = {v}')
        elif isinstance(obj_diff[diff_type], list):
            for diff_elem in obj_diff[diff_type]:
                errors.append(diff_elem)
        else:
            errors.append(obj_diff[diff_type])
    return errors


def random_timerange(n: int = 2, _lower: int = 0) -> list:
    """
    Generates a random list of timerange strings

    Args:
        n   (int)   -   number of timeranges needed
        _lower (int)-   lower bound for generating timeranges
    
    Returns:
        timeranges  (list)  -   list of timeranges
                                example: ['1am-2pm', '2pm-3pm']
    """
    if n == 0:
        return []

    a = np.array_split(range(_lower, 25), n)
    min_chunk_len = min(len(k) for k in a)
    if min_chunk_len <= 3:
        start, end = _lower, _lower + 1
    else:
        start, end = sorted(random.sample(list(a[0]), 2))

    range_str = [f'{seconds_to_time(start * 60 * 60)}-{seconds_to_time(end * 60 * 60)}']
    if end < 22:
        range_str += random_timerange(n - 1, end + 2)
    return range_str


def random_window(n: int = 3, k: int = 2) -> dict:
    """
    Generates random op window config dict

    Args:
        n   (int)   -   number of random days
        k   (int)   -   timeranges size per week day

    Returns:
        operating_window    (dict)  -   random window config
        example:    {
            'MONDAY': ['12am-4am','5am-9am'],
            'FRIDAY': ['2pm-3pm', '7pm-8pm']
        }
    """
    return {
        week_day.upper(): random_timerange(k)
        for week_day in random.sample(sorted(calendar.day_name), n)
    }


def random_dates() -> list:
    """
    Generates a pair of random dates in mm-dd-yyyy format

    Returns:
        random_dates    (list)  -   random to and from date
        example: ['10-27-2099','11-30-3001']
    """
    from_date = datetime.now() + timedelta(days=random.randint(5, 10))
    to_date = from_date + timedelta(days=random.randint(5, 10))
    return [from_date.strftime("%m-%d-%Y"), to_date.strftime("%m-%d-%Y")]


def weekrange(a: int, b: int) -> list:
    """
    util to get week range list

    Args:
        a   (int)   -   weekday index start
        b   (int)   -   weekday index end
    
    Returns:
        weekindexlist   (list)  -   list of weekday indices a to b
        example: when a=4, b=1 returns [4, 5, 6, 0]
    """
    rets = [a]
    c = a
    while c != b:
        c = (c + 1) % 7
        rets.append(c)
    return rets


def in_range(timerange: str, ranges: list) -> bool:
    """
    Checks if given timerange str lies within timeranges list given

    Args:
        timerange   (str)   -   timerange str like '4am-3pm'
        ranges  (list)      -   list of timeranges as above
    
    Returns:
        in_range    (bool)  -   if given timerange is covered by ranges list
    """
    from_t, to_t = [time_to_seconds(tim) for tim in timerange.split('-')]
    for tims in ranges:
        from_b, to_b = [time_to_seconds(tim) for tim in tims.split('-')]
        if from_t >= from_b and to_t <= to_b:
            return True
    return False


def validate_daytimes(ui: dict, api: dict) -> bool:
    """
    Checks if daytimes in UI match API returned format

    Args:
        ui  (dict)  -   window config dict as visible in webpage
        api (dict)  -   window config as returned by API

    Returns:
        valid   (bool)  -   if both configs match
    """
    day_names = list(calendar.day_name)
    for day_str, time_list in ui.items():
        days_list = []
        split_days = re.split(r" and |, ", day_str)
        for day_token in split_days:
            if 'through' not in day_token:
                days_list.append(day_token.upper())
            else:
                start_num, end_num = [
                    day_names.index(day_name.lower().title())
                    for day_name in day_token.split(' through ')
                ]
                for day_num in weekrange(start_num, end_num):
                    days_list.append(day_names[day_num].upper())
        for day in days_list:
            for timerange in time_list:
                if not in_range(timerange, api[day]):
                    return False
    return True


class OperationWindowHelper:
    """Helper file to provide arguments and handle function call to main file"""
    test_step = TestStep()

    def __init__(self, admin_console: AdminConsole = None, commcell: Commcell = None, options: dict = None) -> None:
        """
        Initialize method for OperationWindowHelper
        
        Args:
            admin_console   -   the AdminConsole object
            commcell        -   commcell sdk object
            options         -   dict of test related options
                creation_params: input dict to pass to create test
                edit_params: input dict to pass to edit test
                rule_to_delete: name to bw to test delete
                all above options are randomized if not given
        """
        self.edit_bw_config = {}
        self.bw_config = {}
        if options is None:
            options = {}
        self.__commcell = commcell
        self.__admin_console = admin_console
        if admin_console:
            self.__navigator = admin_console.navigator
            self.__operation_window = OperationWindow(self.__admin_console)
        self.log = logger.get_log()
        self.options = options
        self.to_be_cleaned = []

    def api_blackout_windows(self, simplified: bool = False) -> dict:
        """
        Util to get the operation windows in comparable format
        
        Args:
            simplified  (bool)  -   if True, returns simplified API data

        Returns:
            api_data    (dict)  -   dict with API data of blackout windows

        """
        operations_convert = {
            "FULL_DATA_MANAGEMENT": 'label.allowedOpsFDM',
            "NON_FULL_DATA_MANAGEMENT": 'label.allowedOpsNFDM',
            "SYNTHETIC_FULL": 'label.allowedOpsSF',
            "SRM": 'label.transactionOps'
        }
        admin_ops_convert = {
            "BACKUP_COPY": 'label.backupCopy',
            "AUX_COPY": 'label.auxCopy',
            "UPDATE_SOFTWARE": 'label.upgradeSoftware'
        }
        weeks_convert = {
            "all": 'label.allWeeks',
            "first": 'label.firstWeek',
            "second": 'label.secondWeek',
            "third": 'label.thirdWeek',
            "fourth": 'label.fourthWeek',
            "last": 'label.lastWeek'
        }

        api_data = self.__commcell.operation_window.list_operation_window()
        if not api_data:
            return {}
        processed_data = {}
        for window in api_data:
            if window.get('entity', {}).get('clientId') != 2:
                # CCM migrated windows show up under commcell level but different client ID
                continue

            name = window.get('name')

            level = int(window.get('level', 0))
            if int(level) != 0:
                continue  # windows from plans and policies arent listed in UI

            start_date = window.get('startDate', 0)
            end_date = window.get('endDate', 0)
            between_dates = [start_date, end_date]
            if start_date == 0 and end_date == 0:
                between_dates = None

            off_daytimes = {}
            for daytime in window.get('dayTime', []):
                days = [
                    calendar.day_name[int(day_num) - 1].upper()
                    for day_num in daytime.get('dayOfWeek', [])
                ]
                start_time = seconds_to_time(int(daytime.get('startTime', 0)))
                end_time = seconds_to_time(int(daytime.get('endTime', 0)))
                timerange = f'{start_time}-{end_time}'
                for day in days:
                    off_daytimes[day] = off_daytimes.get(day, set()) | {timerange}

            if "ALL" in window.get("operations", []):
                operations = 'All'
                admin_operations = None
            else:
                operations = [
                    self.__admin_console.props[operations_convert[api_op]]
                    for api_op in window.get('operations', [])
                    if api_op in operations_convert
                ]
                admin_operations = [
                    self.__admin_console.props[admin_ops_convert[api_op]]
                    for api_op in window.get('operations', [])
                    if api_op in admin_ops_convert
                ]

            off_weeks = [
                self.__admin_console.props[weeks_convert[api_week]]
                for api_week in window.get('dayTime', [{}])[0].get('weekOfTheMonth', [])
            ]

            processed_data[name] = {
                'between_dates': between_dates,
                'off_daytimes': off_daytimes,
            }
            if not simplified:
                processed_data[name].update({
                    'backup_operations': operations,
                    'admin_operations': admin_operations,
                    'off_weeks': off_weeks,
                    'no_submit_schedule': window.get('doNotSubmitJob', False)
                })
        return processed_data

    def ui_blackout_windows(self) -> dict:
        """
        Util to get operation windows from UI and process to comparable format
        
        Returns:
            ui_data (dict)  -   dict with blackout window table data
        """
        ui_data = self.__operation_window.read_all_operation_rules()
        for window in ui_data:
            dates = ui_data[window]['between_dates']
            if dates is not None:
                dates = [
                    parse(each_date, dayfirst=False).replace(tzinfo=tz.gettz('GMT')).timestamp()
                    for each_date in dates
                ]
            ui_data[window]['between_dates'] = dates
        return ui_data

    def setup_bw_page(self) -> None:
        """Util to setup blackout window page"""
        if '/operationWindow' not in self.__admin_console.current_url():
            self.__navigator.navigate_to_operation_window()

    @test_step
    def validate_bw_table(self) -> None:
        """Validates the first page in blackout window table"""
        self.__commcell.refresh()
        ui_data = self.ui_blackout_windows()
        api_data = self.api_blackout_windows(True)
        diffs = DeepDiff(ui_data, api_data,
                         ignore_numeric_type_changes=True)
        self.log.info(f"UI Blackout Windows: {ui_data}")
        self.log.info(f"API Blackout Windows: {api_data}")
        errors = _list_of_diffs(diffs)
        if errors:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure('Blackout Windows table failed to match API')
        self.log.info("Blackout Windows table verified!")

    @test_step
    def validate_bw_creation(self) -> None:
        """Validates creation and read of blackout window"""
        self.bw_config = {
            'operation_rule_name': OptionsSelector.get_custom_str('bw'),
            'backup_operations': random.choice((
                list(random.sample(self.__operation_window.operations, 2)),
                'All'
            )),
            'admin_operations': list(random.sample(self.__operation_window.admin_operations, 2)),
            'off_daytimes': random_window(),
            'off_weeks': random.choice((
                list(random.sample(self.__operation_window.weeks, 2)),
                self.__operation_window.all_weeks
            )),
            'between_dates': random.choice((random_dates(), None)),
            'no_submit_schedule': random.choice((True, False))
        }
        if self.bw_config['backup_operations'] == 'All':
            self.bw_config['admin_operations'] = None
        # override with user tcinputs
        self.bw_config.update(self.options.get('creation_params', {}))

        self.log.info("Attempting to create blackout window with rules:")
        self.log.info(self.bw_config)
        self.__operation_window.add_operation_rule(**self.bw_config)
        self.to_be_cleaned.append(self.bw_config['operation_rule_name'])
        self.log.info("Blackout window added successfully from UI!")
        self.log.info("Validating creation")

        api_data = self.api_blackout_windows()[self.bw_config['operation_rule_name']]
        api_data['operation_rule_name'] = self.bw_config['operation_rule_name']

        between_dates = self.bw_config['between_dates']
        if between_dates:
            self.bw_config['between_dates'] = [
                parse(date, dayfirst=False).replace(tzinfo=tz.gettz('GMT')).timestamp()
                for date in between_dates
            ]
        # dates are set to timestamps as returned from API

        diffs = DeepDiff(self.bw_config, api_data,
                         ignore_type_in_groups=[(list, set)],
                         ignore_order=True)
        errors = _list_of_diffs(diffs)
        if errors:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure('Blackout Window UI input failed to match API')
        self.log.info("Blackout Window UI input validated to API output!")
        self.log.info("Validating UI output now")

        ui_data = self.__operation_window.fetch_all_operation_rule_details(
            self.bw_config['operation_rule_name']
        )
        between_dates = ui_data['between_dates']
        if between_dates:
            ui_data['between_dates'] = [
                parse(date, dayfirst=False).replace(tzinfo=tz.gettz('GMT')).timestamp()
                for date in between_dates
            ]

        diffs = DeepDiff(ui_data, api_data,
                         # validate daytimes seperately as this UI output format is different
                         exclude_paths=["root['off_daytimes']"],
                         ignore_type_in_groups=[(list, set)],
                         ignore_order=True)
        errors = _list_of_diffs(diffs)
        if errors:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure('Blackout Window UI output failed to match API')
        if not validate_daytimes(ui_data['off_daytimes'], api_data['off_daytimes']):
            self.log.error("daytimes do not match!")
            self.log.error(f"UI: {ui_data['off_daytimes']}")
            self.log.error(f"API: {api_data['off_daytimes']}")
        self.log.info("Blackout Window UI output validated to API output!")
        self.log.info("BW CREATION AND READ VALIDATED!")

    @test_step
    def validate_bw_edit(self) -> None:
        """Validates edit of blackout window"""
        self.edit_bw_config = {
            'operation_rule_name': self.bw_config['operation_rule_name'],
            'new_operation_rule_name': OptionsSelector.get_custom_str('bw_renamed'),
            'backup_operations': [
                list(random.sample(self.__operation_window.operations, 2)),
                'All'
            ][int(self.bw_config['backup_operations'] != 'All')],
            'admin_operations': [
                list(random.sample(self.__operation_window.admin_operations, 2)),
                None
            ][int(self.bw_config['backup_operations'] != 'All')],
            'off_daytimes': random_window(),
            'off_weeks': [
                list(random.sample(self.__operation_window.weeks, 2)),
                self.__operation_window.all_weeks
            ][int(self.bw_config['off_weeks'] != self.__operation_window.all_weeks)],
            'between_dates': [random_dates(), None][int(self.bw_config['between_dates'] is not None)],
            'no_submit_schedule': [True, False][int(self.bw_config['no_submit_schedule'])]
        }
        if self.edit_bw_config['backup_operations'] == 'All':
            self.edit_bw_config['admin_operations'] = None
        # override with user tcinputs
        self.edit_bw_config.update(self.options.get('edit_params', {}))

        self.log.info("Attempting to edit blackout window with rules:")
        self.log.info(self.edit_bw_config)
        self.__operation_window.edit_operation_rule(**self.edit_bw_config)
        self.log.info("Blackout window edited successfully from UI!")
        self.log.info("Validating if API returns edited data")

        # Update the edit configs for comparison with API
        new_name = self.edit_bw_config['new_operation_rule_name']
        old_name = self.edit_bw_config['operation_rule_name']
        del self.edit_bw_config['new_operation_rule_name']
        self.edit_bw_config['operation_rule_name'] = new_name
        # name params are set
        self.to_be_cleaned.append(new_name)
        if old_name in self.to_be_cleaned:
            self.to_be_cleaned.remove(old_name)

        between_dates = self.edit_bw_config['between_dates']
        if between_dates:
            self.edit_bw_config['between_dates'] = [
                parse(date, dayfirst=False).replace(tzinfo=tz.gettz('GMT')).timestamp()
                for date in between_dates
            ]
        # dates are set to timestamps as returned from API

        api_data = self.api_blackout_windows()[new_name]
        api_data['operation_rule_name'] = new_name
        diffs = DeepDiff(self.edit_bw_config, api_data,
                         ignore_numeric_type_changes=True,
                         ignore_type_in_groups=[(list, set)],
                         ignore_order=True)
        errors = _list_of_diffs(diffs)
        if errors:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure('Blackout Window EDIT UI input failed to match API')
        self.log.info("Blackout Window EDIT UI input validated to API output!")
        self.log.info("Validating UI output now")

        ui_data = self.__operation_window.fetch_all_operation_rule_details(
            self.edit_bw_config['operation_rule_name']
        )
        # name params are set
        between_dates = ui_data['between_dates']
        if between_dates:
            ui_data['between_dates'] = [
                parse(date, dayfirst=False).replace(tzinfo=tz.gettz('GMT')).timestamp()
                for date in between_dates
            ]

        diffs = DeepDiff(ui_data, api_data,
                         # validate daytimes seperately as this UI output format is different
                         exclude_paths=["root['off_daytimes']"],
                         ignore_numeric_type_changes=True,
                         ignore_order=True)
        errors = _list_of_diffs(diffs)
        if errors:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure('Blackout Window (post EDIT) UI output failed to match API')
        if not validate_daytimes(ui_data['off_daytimes'], api_data['off_daytimes']):
            self.log.error("daytimes do not match!")
            self.log.error(f"UI: {ui_data['off_daytimes']}")
            self.log.error(f"API: {api_data['off_daytimes']}")
        self.log.info("Blackout Window (post EDIT) UI output validated to API output!")
        self.log.info("BW UPDATION AND READ VALIDATED!")

    @test_step
    def validate_bw_delete(self) -> None:
        """Validates delete of blackout window"""
        bw_name = self.options.get('rule_to_delete', self.edit_bw_config['operation_rule_name'])
        self.log.info(f"Deleting blackout window {bw_name}")
        self.__operation_window.delete_operation_rule(bw_name)
        self.log.info("Deletion is successfull from UI!")
        api_data = self.api_blackout_windows()
        if bw_name in api_data:
            self.log.error("API still returns the deleted window!")
            raise CVTestStepFailure("API says blackout window still not deleted!")
        else:
            self.log.info("API confirms deletion!")
            if bw_name in self.to_be_cleaned:
                self.to_be_cleaned.remove(bw_name)
        self.log.info("Validating if UI confirms deletion")
        ui_data = self.ui_blackout_windows()
        if bw_name in ui_data:
            self.log.error("UI still returns the deleted window!")
            raise CVTestStepFailure("UI says blackout window still not deleted!")
        else:
            self.log.info("UI confirms deletion!")
        self.log.info("BW DELETION AND READ VALIDATED!")

    def clean_up(self) -> None:
        """Clean up function for this helper"""
        if not self.to_be_cleaned:
            self.log.info("No need clean up, all blackout windows deleted")
        else:
            bwlist = self.api_blackout_windows()
            for bw in self.to_be_cleaned:
                if bw in bwlist:
                    self.log.info(f"Cleaning BW: {bw}")
                    self.__commcell.operation_window.delete_operation_window(name=bw)
                else:
                    self.log.info(f"BW {bw} not in commcell, not deleting")
