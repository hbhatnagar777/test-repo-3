"""

Main file for performing schedule policy related operations


SchedulePolicyHelper: schedule policy helper class to perform schedule policy related operations

SchedulePolicyHelper:
    __init__(class_object)                              --  initialise object of the
                                                            SchedulePolicyHelper class

    _validate_entities                                  -- validates the associations and appgroups being modified
                                                           based on the operation type

    schedule_policy_obj                                 -- setter and getter for the schedule policy object

    create_schedule_policy()                            -- creates a schedule policy and returns the object

    modify_associations()                               -- modifies the associations of the schedule policy

    modify_app_group()                                  -- modifies the app groups of the schedule policy

    add_schedule_to_policy()                            -- adds a schedule to a schedule policy

    _verify_pattern()                                   -- verifies the pattern set for the schedule of a schedule
                                                           policy

    _verify_option()                                    -- verifies the various options set for the schedule

    modify_schedule_of_policy()                         -- modify a schedule associated to the schedule policy

    delete_schedule_of_policy()                         -- delete a schedule from a schedule policy

    delete_schedule_policy()                            -- deletes the schedule policy



"""
from cvpysdk.policies.schedule_options import ScheduleOptions
from cvpysdk.policies.schedule_policies import SchedulePolicies, OperationType
from cvpysdk.schedules import Schedules
from AutomationUtils import logger


class SchedulePolicyHelper:
    """Class for Schedule Policy Operations"""

    def __init__(self, commcell_obj, schedule_policy_obj=None):
        """
        initialise object of the SchedulePolicyHelper class with the commcell obj and schedule policy obj if available
        """
        self.log = logger.get_log()
        self._commcell_obj = commcell_obj
        self._schedule_policy_obj = schedule_policy_obj

    @staticmethod
    def _validate_entities(input_entities, output_entities, operation_type):
        """
        validates the associations and appgroups being modified based on the operation type
        Args:
            input_entities (list) -- list of dictionaries containing the input entities (associations/app groups)
            output_entities (list) -- list of dictionaries containing the entities set at the schedule policy
            operation_type: Operation type is according to OperationType enum (include/exclude/delete)

        Raises: Exception if there is a failure in validating the entities according to the Operation Type

        """
        set_input_entities = [set(entity.items()) for entity in [{k: v for k, v in d.items() if k != 'flags'}
                                                                 for d in input_entities]]
        set_output_entities = [set(entity.items()) for entity in [{k: v for k, v in d.items() if k != 'flags'}
                                                                  for d in output_entities]]

        success_list = [
            'entity present' for input_entity in set_input_entities for output_entity in set_output_entities if not (
                input_entity - output_entity)]
        if operation_type == OperationType.INCLUDE:
            if not success_list:
                raise Exception("Provided input associations is not present in the output associations on an include "
                                "operation")
        else:
            if success_list:
                raise Exception("Provided input associations is present in the output associations on a delete req")

    @property
    def schedule_policy_obj(self):
        """
        Getter for the schedule policy object
        Returns: An instance of the schedule policy class

        """
        return self._schedule_policy_obj

    @schedule_policy_obj.setter
    def schedule_policy_obj(self, sp_obj):
        """
        Setter for the schedule policy object
        Args:
            sp_obj: Instance of the schedule policy class

        Returns:

        """
        self._schedule_policy_obj = sp_obj

    def create_schedule_policy(self, name, policy_type, associations, schedules, agent_type=None):
        """
        Creates a schedule policy and returns the object
        Args:
            name (string) -- Name of the schedule policy
            policy_type (string) -- Type of the policy
            associations (list) -- list of dictionaries with associations to be set
                                    Example:
                                    [
                                    {
                                        "clientName": "scheduleclient1"
                                    },
                                    {
                                        "clientGroupName": "scheduleclient2"
                                    }
                                    ]
            schedules (list) -- list of dictionaries with pattern and corresponding options
                                Example:
                                {
                                    pattern : {}, -- Please refer SchedulePattern.create_schedule in schedules.py
                                    for the types of pattern to be sent

                                     eg: {
                                            "freq_type": 'daily',
                                            "active_start_time": time_in_%H/%S (str),
                                            "repeat_days": days_to_repeat (int)
                                         }

                                    options: {} -- Please refer ScheduleOptions.py classes for respective schedule
                                                   options

                                                    eg:  {
                                                        "maxNumberOfStreams": 0,
                                                        "useMaximumStreams": True,
                                                        "useScallableResourceManagement": True,
                                                        "totalJobsToProcess": 1000,
                                                        "allCopies": True,
                                                        "mediaAgent": {
                                                            "mediaAgentName": "<ANY MEDIAAGENT>"
                                        }
                                    }
            agent_type (list) -- gent Types to be associated to the schedule policy

                          eg:    [
                                    {
                                        "appGroupName": "Protected Files"
                                    },
                                    {
                                        "appGroupName": "Archived Files"
                                    }
                                ]

        Returns:

        """
        self.log.info("Creating Schedule Policy with name %s", name)
        schedule_policy_obj = SchedulePolicies(self._commcell_obj).add(name, policy_type, associations,
                                                                       schedules, agent_type)
        self.log.info("Successfully created Schedule Policy")
        return schedule_policy_obj

    def modify_associations(self, associations, operation_type, validate=True):
        """
        Modifies the associations of the schedule policy
        Args:
            associations (list) -- list of associations to modify
            operation_type (string) -- OperationType (include, exclude, delete)
            validate (bool) -- boolean to validate the modification

        Raises:
            Exception if association updation fails according to the OperationType

        """
        self.log.info("Performing %s operation on the following associations %s for the schedule policy %s",
                      operation_type, associations, self.schedule_policy_obj.schedule_policy_id)
        self.schedule_policy_obj.update_associations(associations, operation_type)
        if validate:
            existing_associations = self.schedule_policy_obj._associations
            self._validate_entities(associations, existing_associations, operation_type)
        self.log.info("Successfully updated and validated Schedule Policy")

    def modify_app_group(self, app_groups, operation_type, validate=True):
        """
                Modifies the app_groups of the schedule policy
                Args:
                    app_groups (list) -- list of app groups to modify
                    operation_type (string) -- OperationType (include, exclude, delete)
                    validate (bool) -- boolean to validate the modification

                Raises:
                    Exception if app group updation fails according to the OperationType

                """
        self.log.info("Performing %s operation on the following appgroups %s for the schedule policy %s",
                      operation_type, app_groups, self.schedule_policy_obj.schedule_policy_id)
        self.schedule_policy_obj.update_app_groups(app_groups, operation_type)
        if validate:
            existing_app_groups = self.schedule_policy_obj._app_groups
            self._validate_entities(app_groups, existing_app_groups, operation_type)
        self.log.info("Successfully updated Schedule Policy")

    def add_schedule_to_policy(self, schedule_dict, validate=True):
        """
        Adds a schedule to a schedule policy
        Args:
            schedule_dict (dict) -- {
                    pattern : {}, -- Please refer SchedulePattern.create_schedule in schedules.py for the types of
                                     pattern to be sent

                                     eg: {
                                            "freq_type": 'daily',
                                            "active_start_time": time_in_%H/%S (str),
                                            "repeat_days": days_to_repeat (int)
                                         }

                    options: {} -- Please refer ScheduleOptions.py classes for respective schedule options

                                    eg:  {
                                        "maxNumberOfStreams": 0,
                                        "useMaximumStreams": True,
                                        "useScallableResourceManagement": True,
                                        "totalJobsToProcess": 1000,
                                        "allCopies": True,
                                        "mediaAgent": {
                                            "mediaAgentName": "<ANY MEDIAAGENT>"
                                        }
                                    }
            validate (bool) -- boolean to validate the modification

        Raises:
                    Exception if schedule not added to schedule policy

        """
        self.log.info("Creating a schedule with the following configuration %s for the schedule policy %s",
                      schedule_dict, self.schedule_policy_obj.schedule_policy_id)
        self.schedule_policy_obj.add_schedule(schedule_dict)
        if validate:
            if not self.schedule_policy_obj.get_schedule(schedule_name=schedule_dict.get('pattern').
                                                         get('schedule_name')):
                raise Exception("Schedule not created for the schedule policy")

        self.log.info("Successfully created and added the schedule to the schedule policy")

    @staticmethod
    def _verify_pattern(input_pattern, schedule_obj):
        """
        verifies the pattern set for the schedule of a schedule policy
        Args:
            input_pattern (dict) -- input pattern to verify
            schedule_obj (obj) -- schedule object to check the pattern.

        Raises: Exception if schedule pattern verification failed

        """
        set_pattern = getattr(schedule_obj, schedule_obj.schedule_freq_type.lower())
        set_pattern['freq_type'] = schedule_obj.schedule_freq_type.lower()
        if set(input_pattern.items()) - set(set_pattern.items()):
            raise Exception("Schedule pattern verification failed")

    def _verify_option(self, input_option, schedule_id, schedule_name):
        """
        Verifies the various options set for the schedule
        Args:
            input_option (dict) -- input option to verify
            schedule_id (int) -- schedule id to check the option
            schedule_name (name) -- schedule name to check the option

        Raises: Exception if schedule pattern verification failed

        """
        sub_task = self.schedule_policy_obj.get_schedule(schedule_id, schedule_name)
        option_allowed = ScheduleOptions.policy_to_options_map[self.schedule_policy_obj.policy_type]
        existing_options = self.schedule_policy_obj.get_option(sub_task['options'], option_allowed)
        if set(input_option.items()) - set(existing_options.items()):
            raise Exception("Schedule options verification failed")

    def modify_schedule_of_policy(self, schedule_dict, schedule_id=None, schedule_name=None, validate=True):
        """
                Modifies a schedule to a schedule policy
                Args:
                    schedule_dict (dict) -- {
                            pattern : {}, -- Please refer SchedulePattern.create_schedule in schedules.py for the types
                            of pattern to be sent

                                             eg: {
                                                    "freq_type": 'daily',
                                                    "active_start_time": time_in_%H/%S (str),
                                                    "repeat_days": days_to_repeat (int)
                                                 }

                            options: {} -- Please refer ScheduleOptions.py classes for respective schedule options

                                            eg:  {
                                                "maxNumberOfStreams": 0,
                                                "useMaximumStreams": True,
                                                "useScallableResourceManagement": True,
                                                "totalJobsToProcess": 1000,
                                                "allCopies": True,
                                                "mediaAgent": {
                                                    "mediaAgentName": "<ANY MEDIAAGENT>"
                                                }
                                            }
                    schedule_id (int) -- schedule id to modify schedule
                    schedule_name (name) -- schedule name to modify schedule
                    validate (bool) -- boolean to validate the modification

                Raises:
                            Exception if schedule not modified to schedule policy

                """
        self.log.info("modifying the schedule %s with the following configuration %s for the schedule policy %s"
                      , schedule_name if schedule_name else schedule_id, schedule_dict,
                      self.schedule_policy_obj.schedule_policy_id)
        self.schedule_policy_obj.modify_schedule(schedule_dict, schedule_id, schedule_name)
        if validate:
            if schedule_dict.get('pattern'):
                self._verify_pattern(schedule_dict.get('pattern'), Schedules(self._commcell_obj).
                                     get(schedule_id=schedule_id, schedule_name=schedule_name))
            if schedule_dict.get('options'):
                self._verify_option(schedule_dict.get('options'), schedule_id, schedule_name)
        self.log.info("Successfully modified the schedule of the schedule policy")

    def delete_schedule_from_policy(self, schedule_id=None, schedule_name=None, validate=True):
        """
                        Deletes a schedule to a schedule policy
                        Args:
                            schedule_id (int) -- schedule id to modify schedule
                            schedule_name (name) -- schedule name to modify schedule
                            validate (bool) -- boolean to validate the modification

                        Raises:
                                    Exception if schedule in not deleted from schedule policy

        """
        self.log.info(
            "deleting the schedule %s from the schedule policy %s",
            schedule_name if schedule_name else schedule_id,
            self.schedule_policy_obj.schedule_policy_id)
        self.schedule_policy_obj.delete_schedule(schedule_id, schedule_name)
        if validate:
            if validate:
                if self.schedule_policy_obj.get_schedule(schedule_id, schedule_name):
                    raise Exception("Schedule not deleted for the schedule policy")
        self.log.info("Successfully deleted the schedule from the schedule policy")

    def delete_schedule_policy(self):
        """
        Deletes the schedule policy

        Raises:
                Exception if schedule policy is not deleted

        """
        self.log.info("Deleting Schedule Policy with name %s", self.schedule_policy_obj.schedule_policy_name)
        schedule_policies = SchedulePolicies(self._commcell_obj)
        schedule_policies.delete(self.schedule_policy_obj.schedule_policy_name)
        if schedule_policies.has_policy(self.schedule_policy_obj.schedule_policy_name):
            raise Exception("Schedule policy not deleted successfully")
        self.log.info("Successfully deleted Schedule Policy")
        self.schedule_policy_obj = None
