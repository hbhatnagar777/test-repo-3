# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Operation window operations
OpHelper:
        __init__()                  -- Initialises OpHelper object

        add()                       -- Adds an operation window

        delete()                    -- Deletes Operation window

        edit()                      -- Edits Operation window

        get()                       --Returns an operation rule for modifying/such operations

        list_rules()                --Lists the operation rules for the associated commcell entity.

        delete_all_rules()          --Deletes all the operation window rules for the associated commcell entity

        testcase_rule()             --Returns an operation based on the current date
"""
import calendar
from time import mktime, strptime
from datetime import datetime, timedelta
from cvpysdk.operation_window import OperationWindow
from cvpysdk.commcell import Commcell
from cvpysdk.clientgroup import ClientGroup
from cvpysdk.client import Client
from cvpysdk.agent import Agent
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient
from AutomationUtils import logger


from Server.Scheduler.schedulerhelper import ScheduleCreationHelper


class OpHelper:
    """Helper class to perform operation window operations"""

    def __init__(self, testcase, entity_level, **kwargs):
        """
        Initialize instance of the OpHelper class.
        Args:
            testcase     (obj)     --- Testcase object

            entity_level (obj)     --- Commcell entity object
                    Expected value : commcell/Client/Agent/BackupSet/Subclient/Clientgroup Instance
        """
        self.additional_options = dict(kwargs.items())
        self.testcase = testcase
        self.entity_level = entity_level
        self.log = logger.get_log()
        self.operation_window = OperationWindow(entity_level)
        if 'initialize_sch_helper' in self.additional_options and \
                self.additional_options.get("initialize_sch_helper") == False:
            self.sch = None
        else:
            self.sch = ScheduleCreationHelper(self.testcase)
        # List of all available operations for a operation window
        self._operation_list = {"FULL_DATA_MANAGEMENT",
                                "NON_FULL_DATA_MANAGEMENT",
                                "SYNTHETIC_FULL",
                                "DATA_RECOVERY",
                                "AUX_COPY",
                                "DR_BACKUP",
                                "DATA_VERIFICATION",
                                "ERASE_SPARE_MEDIA",
                                "SHELF_MANAGEMENT",
                                "DELETE_DATA_BY_BROWSING",
                                "DELETE_ARCHIVED_DATA",
                                "OFFLINE_CONTENT_INDEXING",
                                "ONLINE_CONTENT_INDEXING",
                                "SRM",
                                "INFORMATION_MANAGEMENT",
                                "MEDIA_REFRESHING",
                                "DATA_ANALYTICS",
                                "DATA_PRUNING",
                                "BACKUP_COPY",
                                "CLEANUP_OPERATION"}
        if isinstance(entity_level, Commcell):
            # List of operations not supported by Commcell
            self._operation_set = {"SRM",
                                   "DATA_PRUNING"}
        elif isinstance(entity_level, ClientGroup):
            # List of operations not supported by Client group
            self._operation_set = {"SYNTHETIC_FULL",
                                   "DR_BACKUP",
                                   "SRM",
                                   "DATA_VERIFICATION",
                                   "ERASE_SPARE_MEDIA",
                                   "MEDIA_REFRESHING"}
        elif isinstance(entity_level, Client):
            # List of operations not supported by Client
            self._operation_set = {"SYNTHETIC_FULL",
                                   "AUX_COPY",
                                   "SRM",
                                   "DATA_PRUNING",
                                   "DR_BACKUP",
                                   "DATA_VERIFICATION",
                                   "ERASE_SPARE_MEDIA",
                                   "MEDIA_REFRESHING"}
        elif isinstance(entity_level, Agent):
            # List of operations not supported by Agent
            self._operation_set = {"SYNTHETIC_FULL",
                                   "AUX_COPY",
                                   "SRM",
                                   "DATA_PRUNING",
                                   "DR_BACKUP",
                                   "DATA_VERIFICATION",
                                   "ERASE_SPARE_MEDIA",
                                   "MEDIA_REFRESHING"}
        elif isinstance(entity_level, Backupset):
            # List of operations not supported by Backupset
            self._operation_set = {"SYNTHETIC_FULL",
                                   "AUX_COPY",
                                   "DATA_RECOVERY",
                                   "DATA_ANALYTICS",
                                   "SRM",
                                   "DATA_PRUNING",
                                   "DELETE_DATA_BY_BROWSING",
                                   "DR_BACKUP",
                                   "DATA_VERIFICATION",
                                   "OFFLINE_CONTENT_INDEXING",
                                   "ONLINE_CONTENT_INDEXING",
                                   "ERASE_SPARE_MEDIA",
                                   "MEDIA_REFRESHING"}
        elif isinstance(entity_level, Subclient):
            # List of operations not supported by Subclient
            self._operation_set = {"SYNTHETIC_FULL",
                                   "AUX_COPY",
                                   "DATA_RECOVERY",
                                   "DATA_ANALYTICS",
                                   "SRM",
                                   "DATA_PRUNING",
                                   "OFFLINE_CONTENT_INDEXING",
                                   "ONLINE_CONTENT_INDEXING",
                                   "DELETE_DATA_BY_BROWSING",
                                   "DR_BACKUP",
                                   "DATA_VERIFICATION",
                                   "ERASE_SPARE_MEDIA",
                                   "MEDIA_REFRESHING"}
        else:
            raise Exception("Invalid instance passed")
        # Getting list of operations supported based on given entity level
        self._operation_set = self._operation_list - self._operation_set

    def add(
            self,
            name,
            start_date,
            end_date,
            operations,
            day_of_week,
            start_time,
            end_time,
            week_of_the_month=None,
            validate=False,
            do_not_submit_job=False):
        """
        Adds an operation window with given parameters

            Args:
                name                (str)   -- Name of the operation window

                start_date          (str)   -- start date(dd/mm/yyyy) of the operation window

                end_date            (str)   -- end date(dd/mm/yyyy) of the operation window

                operations          (list)  -- List of operations of the operation window

                day_of_week         (list)  -- List of days for the operation window

                start_time          (str)   -- start time(HH:MM) of the operation in a day

                start_time          (list)  -- list of start time(HH:MM) of the operation for each day

                end_time            (str)   -- end time(HH:MM) of the operation in a day

                end_time            (list)  -- list of end time(HH:MM) of the operation for each day

                week_of_the_month   (list)  --  List of weeks for the operation window

                validate            (bool)  -- validates whether the rule properties are as given
                                       Default-True

                do_not_submit_job   (bool)  -- doNotSubmitJob of the operation window

            Returns:
                OperationWindowDetails object for the created/added rule

            Raises:
                Exception if the arguments are not valid
        """
        try:
            self.log.info("Adding an operation window with attributes")
            start_date = int(
                calendar.timegm(
                    datetime.strptime(
                        start_date,
                        "%d/%m/%Y").timetuple()))
            end_date = int(
                calendar.timegm(
                    datetime.strptime(
                        end_date,
                        "%d/%m/%Y").timetuple()))
            if isinstance(start_time, str) and isinstance(end_time, str):
                temp_time = strptime(start_time, "%H:%M")
                start_time = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)
                temp_time = strptime(end_time, "%H:%M")
                end_time = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)
                if start_time > end_time:
                    raise Exception("Failed to add operation window because end_date_time is "
                                    "smaller than start_date_time")
            elif (isinstance(start_time, list) and isinstance(end_time, list)) and (len(start_time)==len(end_time)):
                for time in range(len(start_time)):
                    temp_time = strptime(start_time[time], "%H:%M")
                    start_time[time] = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)
                    temp_time = strptime(end_time[time], "%H:%M")
                    end_time[time] = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)
                    if start_time[time] >= end_time[time]:
                        raise Exception("start time of {0} week day is greater than or equal to end time".format(time+1))
            else:
                raise Exception("Both start_time and end_time should be of same type.")

            for operation in operations:
                if operation not in self._operation_set:
                    raise Exception("Agent {0} does not support " "{1} operation".format(
                        str(self.entity_level), str(operation)))

            operations = [item.upper() for item in operations]
            self.log.info(
                "Name:{0},Start Date:{1},End Date:{2},Operations:{3},Days Of Week:{4},Start Time:{5},"
                "End Time:{6}, Week of the Month:{7},Do Not Submit Job:{8}" .format(
                    name,
                    start_date,
                    end_date,
                    operations,
                    day_of_week,
                    start_time,
                    end_time,
                    week_of_the_month,
                    do_not_submit_job))
            op_rule = self.operation_window.create_operation_window(
                name,
                start_date,
                end_date,
                operations,
                day_of_week,
                start_time,
                end_time,
                week_of_the_month,
                do_not_submit_job)
            if validate:
                self._validate(
                    op_rule,
                    name,
                    start_date,
                    end_date,
                    operations,
                    day_of_week,
                    start_time,
                    end_time,
                    week_of_the_month,
                    do_not_submit_job)
            self.log.info(
                "Successfully created operation window named:%s", name)
            return op_rule
        except Exception as excp:
            self.log.error(
                'Error occurred while adding operation window %s',
                str(excp))
            raise Exception(
                'Adding operation window Failed with error: {0}'.format(
                    str(excp)))

    def delete(
            self,
            name=None,
            rule_id=None):
        """
        Deletes the operation window with specified name
            Args:
                name    (str)    -- Name of the operation window to be deleted

                rule_id (int)    -- Rule id of the operation window to be deleted

            Returns: None
        """
        if name:
            self.log.info("Deleting operation window named %s", name)
            self.operation_window.delete_operation_window(name=name)
            self.log.info(
                "Successfully deleted operation window named %s", name)
        if rule_id:
            self.log.info(
                "Deleting operation window with rule id: %s",
                rule_id)
            self.operation_window.delete_operation_window(rule_id=rule_id)
            self.log.info(
                "Successfully deleted operation window with rule_id: %s",
                rule_id)

    def edit(
            self,
            rule_id=None,
            name=None,
            new_name=None,
            start_date=None,
            end_date=None,
            operations=None,
            day_of_week=None,
            start_time=None,
            end_time=None,
            week_of_the_month=None,
            validate=False,
            do_not_submit_job=False):
        """
        Edits an operation window based on name  and modifies it's properties

            Args:
                rule_id     (int)   -- Rule_id of the operation window to be edited

                new_name    (str)   -- New name of the operation window

                name        (str)   -- Name of the operation window

                start_date  (str)   -- start date(dd/mm/yyyy) of the operation window

                end_date    (str)   -- end date(dd/mm/yyyy) of the operation window

                operations  (list)  -- List of operations of the operation window

                day_of_week (list)  -- List of days for the operation window

                start_time  (str)   -- start time(HH:MM) of the operation in a day

                start_time  (list)  -- list of start time(HH:MM) of the operation for each day

                end_time    (str)   -- end time(HH:MM) of the operation in a day

                end_time    (list)  -- list of end time(HH:MM) of the operation for each day

                week_of_the_month   (list)  --  List of weeks for the operation window

                validate    (bool)  -- validates whether the rule properties are as given
                                       Default-True

                do_not_submit_job  (bool)  -- doNotSubmitJob of the operation window

            Returns:
                OperationWindowDetails object for the Modified rule

            Raises:
                Exception if the arguments are not valid
        """
        try:
            op_rule = self.operation_window.get(rule_id=rule_id, name=name)
            if start_date:
                start_date = int(
                    calendar.timegm(
                        datetime.strptime(
                            start_date,
                            "%d/%m/%Y").timetuple()))
            if end_date:
                end_date = int(
                    calendar.timegm(
                        datetime.strptime(
                            end_date,
                            "%d/%m/%Y").timetuple()))
            if start_time and isinstance(start_time, int):
                temp_time = strptime(start_time, "%H:%M")
                start_time = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)

            elif start_time and isinstance(start_time, list):
                for time in len(start_time):
                    temp_time = strptime(start_time[time], "%H:%M")
                    start_time[time] = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)

            if end_time and isinstance(end_time, int):
                temp_time = strptime(end_time, "%H:%M")
                end_time = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)

            elif end_time and isinstance(end_time, list):
                for time in len(end_time):
                    temp_time = strptime(end_time[time], "%H:%M")
                    end_time[time] = int(temp_time.tm_hour * 3600 + temp_time.tm_min * 60)

            if start_date is not None and end_date is not None:
                if start_date > end_date:
                    raise Exception("Failed to add operation window because "
                                    "end date is smaller than start date")
            elif start_date is not None:
                if start_date > op_rule.end_date:
                    raise Exception("Failed to add operation window because "
                                    "end date is smaller than start date")
            elif end_date is not None:
                if op_rule.start_date > end_date:
                    raise Exception("Failed to add operation window because "
                                    "end date is smaller than start date")

            if start_time is not None and end_time is not None:
                self.check_valid_start_time_end_time(start_time, end_time)
            elif start_time is not None:
                self.check_valid_start_time_end_time(start_time, op_rule.end_time)
            elif end_time is not None:
                self.check_valid_start_time_end_time(op_rule.start_time, end_time)

            if operations is not None:
                for operation in operations:
                    if operation not in self._operation_set:
                        raise Exception(
                            "Agent {0} does not support {1} operation" .format(
                                self.entity_level, operation))
            if new_name is not None:
                name = new_name

            if name:
                self.log.info(
                    "Modifying the given operation window named : %s", name)
                op_rule.modify_operation_window(
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    operations=operations,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    week_of_the_month=week_of_the_month,
                    do_not_submit_job=do_not_submit_job)
                self.log.info(
                    "Successfully modified an operation window named : %s", name)
            if rule_id:
                self.log.info(
                    "Modifying the given operation window with rule id: %s",
                    rule_id)
                op_rule.modify_operation_window(
                    name,
                    start_date,
                    end_date,
                    operations,
                    day_of_week,
                    start_time,
                    end_time,
                    week_of_the_month,
                    do_not_submit_job)
                self.log.info(
                    "Successfully modified an operation window with rule id: %s",
                    rule_id)

            if validate:
                self._validate(
                    op_rule,
                    name,
                    start_date,
                    end_date,
                    operations,
                    day_of_week,
                    start_time,
                    end_time,
                    week_of_the_month,
                    do_not_submit_job)
            return op_rule
        except Exception as excp:
            self.log.error(
                'Error occurred while editing operation window %s',
                str(excp))
            raise Exception(
                'Editing operation window Failed with error: {0}'.format(
                    str(excp)))

    def get(self, name=None, rule_id=None):
        """Returns the operation rule object for a given rule

         Args:
            rule_id               (int)   --  Rule Id of an operation Window

            name                  (str)   --  Name of the operation window

         Returns:
                object - instance of the OperationWindowDetails class
                            for the given operation window name/rule
         Raises:
                SDKException:
                    if type of the operation window name argument is not string

                    if no operation window exists with such name
        """
        return self.operation_window.get(rule_id=rule_id, name=name)

    def list_rules(self):
        """
        Lists the operation rules for the associated commcell entity.

            Returns:
                Returns the List of operation rules (dictionary) associated with given commcell entity

                Example --

                    [{'ruleEnabled': True,
                      'doNotSubmitJob': False,
                      'endDate': 0,
                      'level': 0,
                      'name': 'Rule1',
                      'ruleId': 1,
                      'startDate': 0,
                      'operations': ['FULL_DATA_MANAGEMENT', 'NON_FULL_DATA_MANAGEMENT'],
                      'company': {'_type_': 61,
                                  'providerId': 0,
                                  'providerDomainName': ''},
                      'dayTime': [{'startTime': 28800,
                                   'endTime': 64800,
                                   'weekOfTheMonth': ['first','third'],
                                   'dayOfWeek': ['sunday','monday']}]}
                    ]
        """
        return self.operation_window.list_operation_window()

    def delete_all_rules(self):
        """Deletes all the operation window rules associated with given commcell entity"""
        self.log.info(
            "Deleting all the the rules related to %s", str(
                self.entity_level))
        for operation_rule in self.list_rules():
            self.operation_window.delete_operation_window(
                operation_rule.get("ruleId"))

    def _validate(self,
                  op_rule,
                  name,
                  start_date,
                  end_date,
                  operations,
                  day_of_week,
                  start_time,
                  end_time,
                  week_of_the_month,
                  do_not_submit_job):
        """
        Validates the operation rule after making a rest api call
            Args:
                op_rule: the OperationWindowDetails object
            Raises:
                Exception if changes are not reflected
        """
        self.log.info("Validating if the changes made are reflected or not")
        if name is None:
            name = op_rule.name
        if end_time is None:
            end_time = op_rule.end_time
        if start_time is None:
            start_time = op_rule.start_time
        if start_date is None:
            start_date = op_rule.start_date
        if end_date is None:
            end_date = op_rule.end_date
        if operations is None:
            operations = op_rule.operations
        if week_of_the_month is None:
            week_of_the_month = op_rule.week_of_the_month
        if day_of_week is None:
            day_of_week = op_rule.day_of_week
        if do_not_submit_job is None:
            do_not_submit_job = op_rule.do_not_submit_job
        if (op_rule.name != name or op_rule.end_time != end_time or op_rule.start_time != start_time
                or op_rule.start_date != start_date or op_rule.end_date != end_date
                or op_rule.operations.sort() != operations.sort() or op_rule.day_of_week.sort() != day_of_week.sort()
                or op_rule.week_of_the_month.sort() != week_of_the_month.sort()
                or op_rule.do_not_submit_job != do_not_submit_job):
            self.log.error(
                "Operation rule doesn't have the values passed: Validation Failed")
            raise Exception(
                "Operation rule doesn't have the values passed: Validation Failed")
        self.log.info("Success:The changes made are reflected")

    def testcase_rule(self, operations, start_time=None, end_time=None, start_date=None, end_date=None):
        """
        An operation window(rule) created based on current date
            Args:
                operations  (list)  -- List of operations of the operation window
                start_time  (string) -- start time in HH:MM in 24 Hrs format of blackout window
                end_time    (string) -- end time in HH:MM in 24 Hrs format of blackout window
                start_date  (date object) -- start date in %d/%m/%Y format of blackout window
                end_date    (date object) -- end date in %d/%m/%Y format of blackout window
            Returns:
                Object of the created operation rule
        """
        days_list = ["sunday",
                     "monday",
                     "tuesday",
                     "wednesday",
                     "thursday",
                     "friday",
                     "saturday"]
        if start_time is None:
            start_time = "00:00"
        if end_time is None:
            end_time = "23:59"
        if start_date is None:
            start_date = (datetime.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        if end_date is None:
            end_date = (datetime.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        return self.add(
            self.testcase.name,
            start_date,
            end_date,
            operations,
            days_list,
            start_time,
            end_time)

    def weekly_rule(self, operations, machine_obj, do_not_submit_job=False):
        """
        An operation window(rule) created based on current week date
            Args:
                operations          (list)   -- List of operations of the operation window
                do_not_submit_job   (bool)   -- doNotSubmitJob of the operation window
                machine_obj         (object) -- machine object which can be used to perform operation on blackout window
            Returns:
                Object of the created operation rule
        """
        timezone = self.sch.get_client_tzone(self.testcase.client)[1]
        current_time = machine_obj.current_time(timezone)
        self.log.info("Test client current time is {0}".format(current_time))
        start_time = current_time
        end_time = current_time + timedelta(minutes=60)
        start_date = start_time.strftime("%d/%m/%Y")
        end_date = end_time.strftime("%d/%m/%Y")
        week_day = [start_time.strftime('%A')]
        month_week = []
        if start_time.date() != end_time.date():
            start_time = [start_time.strftime("%H:%M"), "00:00"]
            end_time = ["23:59", end_time.strftime("%H:%M")]
            week_day.append(end_time.strftime('%A'))
        else:
            start_time = start_time.strftime("%H:%M")
            end_time = end_time.strftime("%H:%M")

        return self.add(
            self.testcase.name,
            start_date,
            end_date,
            operations,
            week_day,
            start_time,
            end_time,
            month_week,
            do_not_submit_job=do_not_submit_job)

    def monthly_rule(self, operations, machine_obj, do_not_submit_job=False):
        """
        An operation window(rule) created based on current month week
            Args:
                operations          (list)   -- List of operations of the operation window
                do_not_submit_job   (bool)   -- doNotSubmitJob of the operation window
                machine_obj         (object) -- machine object which can be used to perform operation on blackout window
            Returns:
                Object of the created operation rule
        """
        week_of_the_month_mapping = {
            1: "first",
            2: "second",
            3: "third",
            4: "fourth",
            5: "last"}
        timezone = self.sch.get_client_tzone(self.testcase.client)[1]
        current_time = machine_obj.current_time(timezone)
        self.log.info("Test client current time is {0}".format(current_time))
        start_time = current_time
        end_time = current_time + timedelta(minutes=60)
        start_date = start_time.strftime("%d/%m/%Y")
        end_date = end_time.strftime("%d/%m/%Y")
        week_day = [start_time.strftime('%A')]
        cal = calendar.monthcalendar(current_time.year, current_time.month)
        wd = current_time.weekday()
        days = [week[wd % 7] for week in cal]
        days = list(filter(lambda x: x != 0, days))
        week_number = days.index(current_time.day) + 1
        self.log.info("week number is {0}".format(week_number))
        month_week = [week_of_the_month_mapping[week_number]]
        if start_time.date() != end_time.date():
            week_day.append(end_time.strftime('%A'))
            month_week.append(week_of_the_month_mapping[week_number + 1])
            start_time = [start_time.strftime("%H:%M"), "00:00"]
            end_time = ["23:59", end_time.strftime("%H:%M")]
        else:
            start_time = start_time.strftime("%H:%M")
            end_time = end_time.strftime("%H:%M")
        return self.add(
            self.testcase.name,
            start_date,
            end_date,
            operations,
            week_day,
            start_time,
            end_time,
            month_week,
            do_not_submit_job=do_not_submit_job)

    def check_valid_start_time_end_time(self, start_time, end_time):
        if (isinstance(start_time, int) and isinstance(end_time, int)) and (start_time >= end_time):
            raise Exception("Failed to add operation window because "
                            "end time is smaller than start time")
        elif (isinstance(start_time, list) and isinstance(end_time, list)) and (len(start_time) == len(end_time)):
            for time in range(len(start_time)):
                if start_time[time] > end_time[time]:
                    raise Exception("Failed to add operation window because "
                                    "end time is smaller than start time")
        else:
            raise Exception("Both start_time and end_time should be of same type.")
