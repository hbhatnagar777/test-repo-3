# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that act as wrapper for testcase and SDK

ActivityControl:  - Helper Class for all Activity Control operations for SDK activity apis

    __init__()                          --  Initializes the instance of ActivityControl
                                                    class.

    backup_with_activity_disabled()     --  Runs backup when backup activity is disabled

    set_all_activity()                  --  Sets all the activity control options
                                                (default: enable)

    modify_activity                     --  Modify Backup, Restore and data Aging activity control

    enable_activity                     --  Enable all activity disabled as part of test case

    complete_job_with_activity_enable() -- Enable activity, UnCheck JobsCompleteIfActivityDisabled
                                                and wait for job completion

    cleanup()                           --  Enables all activity back to defaults.

"""

import re
import inspect
from cvpysdk import activitycontrol
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import options_selector
from Server.JobManager.jobmanager_helper import JobManager
from Server.ActivityControl import activitycontrol_constants


class ActivityControlHelper(object):
    """ Class for all Activity Control operations"""

    def __init__(self, testcase):
        """ Initialize the ActivityControl helper class

        Args:
            testcase  (obj)    -- Testcase object
        """
        self._activity_map = activitycontrol_constants.ACTIVITY_MAP
        self.log = testcase.log
        self._subclient = testcase.subclient
        self._activity_control = activitycontrol.ActivityControl(testcase.commcell)
        self._server_base = CommonUtils(testcase)
        self.job_manager = JobManager(commcell=testcase.commcell)
        self.ida_utils = CommonUtils(testcase.commcell)
        self._utility = options_selector.OptionsSelector(testcase.commcell)
        self._client = testcase.client
        self._object_map = {}

    def backup_with_activity_disabled(self, backup_type):
        """ Runs backup when backup activity is disabled

        Args:
                backup_type        (str)   -  level of backup the user wish to run
                                                Full / Incremental / Differential / Synthetic_full
                                                default: Incremental

        Return:
                job   (obj)                - instance of the Job class for this backup job

                True   (Bool)              - True if job triggered but failed only if
                                                Data Management activity disabled

        Raises:
            Exception:

                - if job failed for any other reason
        """

        try:
            job = self._server_base.subclient_backup(self._subclient, backup_type, False)

            return job
        except Exception as excp:
            if re.search("Data Management activity on CommServe is disabled.",
                         str(excp), re.IGNORECASE):
                self.log.info(str(excp))
                return True
            else:
                raise Exception(str(excp))

    def set_all_activity(self, action="Enable"):
        """ Sets all the activity control options

        Args:
                action        (str)   --  Enable or Disable all the activities
                                            Enable/Disable
                                            default: Enable
        Returns:
            None
        """

        for activity_type in self._activity_control._activity_type_dict:
            self.log.info('Setting Activity Type: "{0}" to "{1}"'.format(activity_type, action))
            self._activity_control.set(activity_type, action)

    def modify_activity(self, activity_type, entity_object, action='Enable'):
        """ Modify Backup, Restore and data Aging activity control options

            Args:
            activity_type(str)      --   Activity type to be enable/Disable
                                            Ex: backup/restore/data_aging

            entity_object(object)   --  object name on which activity need be perform

            action(str)             --   Enable or disable activity default: Enable

            Returns:
                None

            Raises:
                Exception:
                    if unable to modify activity

        """
        try:

            if activity_type.lower() not in self._activity_map:
                raise Exception("Unsupported operation type passed to modify_activity")
            if action.lower() not in self._activity_map[activity_type]:
                raise Exception("Unsupported activity type passed to modify_activity")
            activiy_method = getattr(entity_object,
                                     self._activity_map[activity_type.lower()][action.lower()])
            activiy_method()
            if action == 'disable':
                self._object_map.setdefault(entity_object, []).append(activity_type)

            self.log.info("Successfully! {0} {1} activity on {2}".
                          format(action, activity_type, entity_object))

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def enable_activity(self):
        ''' Enable all entities in the self._object_map dictionary '''

        try:
            self.log.info("Enabling activity for test case")
            enable_failed = False
            for entity_object, activity_values in self._object_map.items():
                for each_activity in activity_values:
                    try:
                        activiy_method = getattr(entity_object,
                                                 self._activity_map[each_activity]['enable'])
                        activiy_method()
                    except Exception as exp:
                        self.log.error("Exception: {0}".format(str(exp)))
                        enable_failed = True
                if enable_failed:
                    raise Exception("Failed to enable activity")

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    def complete_job_with_activity_enable(self, job_list, _wait_secs):
        """Enable activity, UnCheck JobsCompleteIfActivityDisabled and wait for job completion"""

        self.enable_activity()
        self.ida_utils.modify_additional_settings('JobsCompleteIfActivityDisabled', '0')
        for _job in job_list:
            self.job_manager.job = _job
            self.job_manager.wait_for_state('completed')
        self._utility.sleep_time(_wait_secs)

    def cleanup(self):
        """ Enables all activity and set back to defaults on Commcell """
        self.log.info("Enabling all activity back.")
        self.set_all_activity("Enable")
