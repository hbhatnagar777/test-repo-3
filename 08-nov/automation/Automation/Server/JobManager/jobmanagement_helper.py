# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing Commcell -> Control Panel -> Job Management related operations.

JobManagementHelper: Class for performing Job Management operations

JobManagementHelper
==============

    __init__(commcell_object)                                       --  initialise object of the JobManagement class

     refresh()                                                      --  refreshes the settings.

     modify_general_settings(settings)                              --  sets the general settings of job management

     modify_priority_settings(settings)                             --  sets the priority settings of job management

     modify_restart_settings(settings)                              --  sets the restart settings of job management

     modify_update_settings(settings)                               --  sets the update settings of job management

     job_priority_precedence                                        --  gets the job priority precedence

     job_priority_precedence(priority_type)                         --  sets the job priority precedence property

     start_phase_retry_interval                                     --  gets the start phase retry interval in
                                                                        (minutes)

     start_phase_retry_interval(minutes)                            --  sets the start phase retry interval property

     state_update_interval_for_continuous_data_replicator           --  gets the start phase retry interval in
                                                                        (minutes)

     state_update_interval_for_continuous_data_replicator           --  sets the state update interval for continuous
                                                                        data replicator

     allow_running_jobs_to_complete_past_operation_window           --  gets the allow running jobs to complete past
                                                                        operation window(True/False)

     allow_running_jobs_to_complete_past_operation_window(flag)     --  sets the allow running jobs to complete past
                                                                        operation window

     job_alive_check_interval_in_minutes                            --  gets the job alive check interval in (minutes)

     job_alive_check_interval_in_minutes(minutes)                   --  sets the job alive check interval in minutes

     queue_scheduled_jobs                                           --  gets the queue scheduled jobs

     queue_scheduled_jobs(flags)                                    --  sets the queue scheduled jobs

     enable_job_throttle_at_client_level                            --  gets the enable job throttle at client level

     enable_job_throttle_at_client_level(flag)                      --  sets the enable job throttle at client level

     enable_multiplexing_for_db_agents                              --  gets the enable multiplexing for db agents

     enable_multiplexing_for_db_agents(flag)                        --  sets the enable multiplexing for db agents

     queue_jobs_if_conflicting_jobs_active                          --  gets the queue jobs if conflicting jobs active

     queue_jobs_if_conflicting_jobs_active(flag)                    --  sets the queue jobs if conflicting jobs active

     queue_jobs_if_activity_disabled                                --  gets the queue jobs if activity disabled

     queue_jobs_if_activity_disabled(flag)                          --  sets the queue jobs if activity disabled

     backups_preempts_auxilary_copy                                 --  gets the backups preempts auxilary copy

     backups_preempts_auxilary_copy(flag)                           --  sets the backups preempts auxilary copy

     restore_preempts_other_jobs                                    --  gets the restore preempts other jobs

     restore_preempts_other_jobs(flag)                              --  sets the restore preempts other jobs

     enable_multiplexing_for_oracle                                 --  gets the enable multiplexing for oracle

     enable_multiplexing_for_oracle(flag)                           --  sets the enable multiplexing for oracle

     job_stream_high_water_mark_level                               --  gets the job stream high water mark level

     job_stream_high_water_mark_level(level)                        --  sets the job stream high water mark level

     backups_preempts_other_backups                                 --  gets the backups preempts other backups

     backups_preempts_other_backups(flag)                           --  sets the backups preempts other backups

     do_not_start_backups_on_disabled_client                        --  gets the do not start backups on disabled
                                                                        client

     do_not_start_backups_on_disabled_client(flag)                  --  sets the do not start backups on disabled
                                                                        client

     get_restart_setting(jobtype)                                   --  gets the restart settings of a specific
                                                                        jobtype

     get_priority_setting(jobtype)                                  --  gets the priority setting of a specific
                                                                        jobtype

     get_update_setting(jobtype)                                    --   gets the update settings of a specfic
                                                                        jobtype

"""
import copy
from cvpysdk.job import JobManagement

from AutomationUtils import logger

from Server.serverhandlers import argtypes


class JobManagementHelper(object):
    """Class for performing job management operations. """

    def __init__(self, commcell_object):
        """
        Initialize instance of JobManagement class for performing operations on jon management settings.

            Args:
                commcell_object         (object)        --  instance of Commcell class.

            Returns:
                None

        """
        self.log = logger.get_log()
        self.management = JobManagement(commcell_object)
        self._cell = commcell_object

    def refresh(self):
        """
        refreshs the settings

            Returns:
                None
        """
        self.management.refresh()
        self.log.info("Settings have been refreshed successfully.")

    def modify_general_settings(self, settings, validation=True):
        """
        sets general settings of job management and verifies whether the settings have been applied successfully
        or not.

        NOTE : Dedicated setters and getters have been provided for modifying general settings.
            Args:
                settings (dict)  --       Following key/value pairs can be set.
                                            {
                                                "allowRunningJobsToCompletePastOperationWindow": False,
                                                "jobAliveCheckIntervalInMinutes": 5,
                                                "queueScheduledJobs": False,
                                                "enableJobThrottleAtClientLevel": False,
                                                "enableMultiplexingForDBAgents": False,
                                                "queueJobsIfConflictingJobsActive": False,
                                                "queueJobsIfActivityDisabled": False,
                                                "backupsPreemptsAuxilaryCopy": False,
                                                "restorePreemptsOtherJobs": False,
                                                "enableMultiplexingForOracle": False,
                                                "jobStreamHighWaterMarkLevel": 500,
                                                "backupsPreemptsOtherBackups": False,
                                                "doNotStartBackupsOnDisabledClient": False

                                            }

                validation  (bool)  --    whether the validation of settings to be done or not after modifications.
        """

        if isinstance(settings, dict):
            self.log.info("Modifying the general settings {0}".format(settings))
            self.management.set_general_settings(settings)
            if validation:
                config = self.management.general_settings.get('generalSettings')
                for key in settings:
                    if config.get(key) != settings.get(key):
                        raise Exception('{0} settings not applied successfully'.format(key))
                self.log.info("Successfully modified the settings {0}".format(settings))
        else:
            raise Exception('Data type of input(s) is not valid')

    def modify_priority_settings(self, settings, validation=True):
        """
        sets priority settings for jobs and agents type and verifies whether the settings have been applied
        successfully or not.

        NOTE : Use getter to get the settings of particular type and then you can use modify functionality with ease.
            Args:
                settings  (list)    --  list of dictionaries with following format.
                                         [
                                            {
                                                "type_of_operation": 1,
                                                "combinedPriority": 10,
                                                "jobTypeName": "Information Management"
                                            },
                                            {
                                                "type_of_operation": 2,
                                                "combinedPriority": 10,
                                                "appTypeName": "Windows File System"
                                            },
                                            {
                                            "type_of_operation": 1,
                                            "combinedPriority": 10,
                                            "jobTypeName": "Auxiliary Copy"
                                             }
                                        ]

                validation  (bool)  --    whether the validation of settings to be done or not after modifications.

            NOTE : for setting, priority for jobtype the 'type_of_operation' must be set to 1 and name of the job type
                   must be specified as below format.

                        "jobTypeName": "Information Management"

            NOTE : for setting, priority for agent type the 'type_of_operation' must be set to 2 and name of the
             job type must be specified as below format

                        "appTypeName": "Windows File System"

            Returns:
                None

        """
        if isinstance(settings, list):
            self.log.info("Modifying the priority settings {0}".format(settings))
            copy_settings = copy.deepcopy(settings)
            self.management.set_priority_settings(copy_settings)
            if validation:
                for element in settings:
                    jobtype = None
                    if element.get('type_of_operation') == 1:
                        jobtype = element.get('jobTypeName')
                    elif element.get('type_of_operation') == 2:
                        jobtype = element.get('appTypeName')
                    config = self.management.get_priority_setting(jobtype)
                    if config.get('combinedPriority') != element.get('combinedPriority'):
                        raise Exception('{0} settings not applied successfully'.format(element.get('jobTypeName')))
                self.log.info("Successfully modified the settings {0}".format(settings))
        else:
            raise Exception('Data type of input(s) is not valid')

    def modify_restart_settings(self, settings, validation=True):
        """
        sets restart settings for jobs.

        NOTE : Use getter to get the settings of particular type and then you can use modify functionality with ease.
            Args:
                settings    (list)      --  list of dictionaries with following format
                                            [
                                                {
                                                    "killRunningJobWhenTotalRunningTimeExpires": False,
                                                    "maxRestarts": 10,
                                                    "enableTotalRunningTime": False,
                                                    "restartable": False,
                                                    "jobTypeName": "File System and Indexing Based (Data Protection)",
                                                    "restartIntervalInMinutes": 20,
                                                    "preemptable": True,
                                                    "totalRunningTime": 21600,
                                                    "jobType": 6
                                                },
                                                {
                                                    "killRunningJobWhenTotalRunningTimeExpires": False,
                                                    "maxRestarts": 144,
                                                    "enableTotalRunningTime": False,
                                                    "restartable": False,
                                                    "jobTypeName": "File System and Indexing Based (Data Recovery)",
                                                    "restartIntervalInMinutes": 20,
                                                    "preemptable": False,
                                                    "totalRunningTime": 21600,
                                                    "jobType": 7
                                                }
                                            ]

             validation  (bool)  --    whether the validation of settings to be done or not after modifications
                                        validation is true by default

            Returns:
                None

        """
        if isinstance(settings, list):
            self.log.info("Modifying the restart settings {0}".format(settings))
            self.management.set_restart_settings(settings)
            if validation:
                for element in settings:
                    config = self.management.get_restart_setting(element.get('jobTypeName'))
                    for key in element:
                        if config.get(key) != element.get(key):
                            raise Exception('{0} settings not applied successfully'.format(element.get('jobTypeName')))
                self.log.info("Successfully modified and validated the settings {0}".format(settings))
        else:
            raise Exception('Data type of input(s) is not valid')

    def modify_update_settings(self, settings, validation=True):
        """
        sets update settings for jobs

        NOTE : Use getter to get the settings of particular type and then you can use modify functionality with ease.
            Args:
                settings    (list)      --      list of dictionaries with following format
                                                [
                                                    {
                                                        "appTypeName": "Windows File System",
                                                        "recoveryTimeInMinutes": 20,
                                                        "protectionTimeInMinutes": 20
                                                    },
                                                    {
                                                        "appTypeName": "Windows XP 64-bit File System",
                                                        "recoveryTimeInMinutes": 20,
                                                        "protectionTimeInMinutes": 20,
                                                    }
                                                ]

                validation  (bool)  --    whether the validation of settings to be done or not after modifications,
                                          validation is true by default

            Returns:
                None

        """
        if isinstance(settings, list):
            copy_settings = copy.deepcopy(settings)
            self.log.info("Modifying the update settings {0}".format(settings))
            self.management.set_update_settings(copy_settings)
            if validation:
                for element in settings:
                    config = self.management.get_update_setting(element.get('appTypeName'))
                    for key in element:
                        if config.get(key) != element.get(key):
                            raise Exception('{0} settings not applied successfully'.format(element.get('appTypeName')))
                self.log.info("Successfully modified and validated the settings {0}".format(settings))
        else:
            raise Exception('Data type of input(s) is not valid')

    @property
    def job_priority_precedence(self):
        """
        gets the job priority precedence
            Returns:
                 (str)  --   type of job priority precedence is set.
        """

        return self.management.job_priority_precedence

    @job_priority_precedence.setter
    @argtypes(str)
    def job_priority_precedence(self, priority_type):
        """
        sets job priority precedence

                Args:
                    priority_type   (str)   --      type of priority to be set

                    Values:
                        "client"
                        "agentType"

         available_priorities = {
            "client": 1,
            "agentType": 2
        }

        """

        self.management.job_priority_precedence = priority_type
        if self.management.job_priority_precedence != priority_type:
            raise Exception('job priority precedence setting is not applied successfully')
        self.log.info("Successfully modified the setting job_priority_precedence")

    @property
    def start_phase_retry_interval(self):
        """
        gets the start phase retry interval in (minutes)
            Returns:
                 (int)      --      interval in minutes.
        """
        return self.management.start_phase_retry_interval

    @start_phase_retry_interval.setter
    @argtypes(int)
    def start_phase_retry_interval(self, minutes):
        """
        sets start phase retry interval for jobs

            Args:
                minutes     (int)       --      minutes to be set.

            Raises:
                SDKException:
                    if input is not valid type.
        """

        self.management.start_phase_retry_interval = minutes
        if self.management.start_phase_retry_interval != minutes:
            raise Exception('start phase retry interval is not set successfully')
        self.log.info("Successfully modified the setting start_phase_retry_interval")


    @property
    def state_update_interval_for_continuous_data_replicator(self):
        """
        gets the state update interval for continuous data replicator in (minutes)
            Returns:
                 (int)      --      interval in minutes
        """
        return self.management.state_update_interval_for_continuous_data_replicator

    @state_update_interval_for_continuous_data_replicator.setter
    @argtypes(int)
    def state_update_interval_for_continuous_data_replicator(self, minutes):
        """
        sets state update interval for continuous data replicator

            Args:
                 minutes       (int)        --      minutes to be set.

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.state_update_interval_for_continuous_data_replicator = minutes
        if self.management.state_update_interval_for_continuous_data_replicator != minutes:
            raise Exception('state update interval for continuous data replicator setting is not set successfully')
        self.log.info("Successfully modified the setting state_update_interval_for_continuous_data_replicator")

    @property
    def allow_running_jobs_to_complete_past_operation_window(self):
        """
        Returns True if option is enabled
        else returns false
        """
        return self.management.allow_running_jobs_to_complete_past_operation_window

    @allow_running_jobs_to_complete_past_operation_window.setter
    @argtypes(bool)
    def allow_running_jobs_to_complete_past_operation_window(self, flag):
        """
        enable/disable, allow running jobs to complete past operation window.
            Args:
                flag    (bool)    --        (True/False) to be set.

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.allow_running_jobs_to_complete_past_operation_window = flag
        if self.management.allow_running_jobs_to_complete_past_operation_window != flag:
            raise Exception('allow running jobs to complete past operation window setting is not set successfully')
        self.log.info("Successfully modified the setting allow_running_jobs_to_complete_past_operation_window")

    @property
    def job_alive_check_interval_in_minutes(self):
        """
        gets the job alive check interval in (minutes)
            Returns:
                (int)       --      interval in minutes
        """
        return self.job_alive_check_interval_in_minutes

    @job_alive_check_interval_in_minutes.setter
    @argtypes(int)
    def job_alive_check_interval_in_minutes(self, minutes):
        """
        sets the job alive check interval in (minutes)
            Args:
                  minutes       --      minutes to be set.

            Raises:
                  SDKException:
                        if input is not valid type
        """
        self.management.job_alive_check_interval_in_minutes = minutes
        if self.management.job_alive_check_interval_in_minutes != minutes:
            raise Exception('job alive check interval in minutes setting is not applied successfully')
        self.log.info("Successfully modified the setting job_alive_check_interval_in_minutes")

    @property
    def queue_scheduled_jobs(self):
        """
        Returns True if option is enabled
        else returns false
        """
        return self.management.queue_scheduled_jobs

    @queue_scheduled_jobs.setter
    @argtypes(bool)
    def queue_scheduled_jobs(self, flag):
        """
        enable/disable, queue scheduled jobs

            Args:
                flag   (bool)      --       (True/False to be set)

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.queue_scheduled_jobs = flag
        if self.management.queue_scheduled_jobs != flag:
            raise Exception('queue scheduled jobs setting is not applied successfully')
        self.log.info("Successfully modified the setting queue_scheduled_jobs")

    @property
    def enable_job_throttle_at_client_level(self):
        """
        Returns True if option is enabled
        else returns false
        """
        return self.management.enable_job_throttle_at_client_level

    @enable_job_throttle_at_client_level.setter
    @argtypes(bool)
    def enable_job_throttle_at_client_level(self, flag):
        """
        enable/disable, job throttle at client level
            Args:
                flag    (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.enable_job_throttle_at_client_level = flag
        if self.management.enable_job_throttle_at_client_level != flag:
            raise Exception('enable job throttle at client level setting is not applied successfully')
        self.log.info("Successfully modified the setting enable_job_throttle_at_client_level")

    @property
    def enable_multiplexing_for_db_agents(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.enable_multiplexing_for_db_agents

    @enable_multiplexing_for_db_agents.setter
    @argtypes(bool)
    def enable_multiplexing_for_db_agents(self, flag):
        """
        enable/disable, multiplexing for db agents
            Args:
                flag    (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.enable_multiplexing_for_db_agents = flag
        if self.management.enable_multiplexing_for_db_agents != flag:
            raise Exception('enable multiplexing for db agents setting is not applied successfully')
        self.log.info("Successfully modified the setting enable_multiplexing_for_db_agents")

    @property
    def queue_jobs_if_conflicting_jobs_active(self):
        """
        Returns True if option is enabled
        else returns false
        """
        return self.management.queue_jobs_if_conflicting_jobs_active

    @queue_jobs_if_conflicting_jobs_active.setter
    @argtypes(bool)
    def queue_jobs_if_conflicting_jobs_active(self, flag):
        """
        enable/disable, queue jobs if conflicting jobs active
            Args;
                flag    (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """

        self.management.queue_jobs_if_conflicting_jobs_active = flag
        if self.management.queue_jobs_if_conflicting_jobs_active != flag:
            raise Exception('queue jobs if conflicting jobs active ' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting queue_jobs_if_conflicting_jobs_active")

    @property
    def queue_jobs_if_activity_disabled(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.queue_jobs_if_activity_disabled

    @queue_jobs_if_activity_disabled.setter
    @argtypes(bool)
    def queue_jobs_if_activity_disabled(self, flag):
        """
        enable/disable, queue jobs if activity disabled
            Args;
                flag    (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.queue_jobs_if_activity_disabled = flag
        if self.management.queue_jobs_if_activity_disabled != flag:
            raise Exception('queue jobs if activity disabled' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting queue_jobs_if_activity_disabled")

    @property
    def backups_preempts_auxilary_copy(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.backups_preempts_auxilary_copy

    @backups_preempts_auxilary_copy.setter
    @argtypes(bool)
    def backups_preempts_auxilary_copy(self, flag):
        """
        enable/disable, backups preempts auxiliary copy
            Args:
                flag    (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.backups_preempts_auxilary_copy = flag
        if self.management.backups_preempts_auxilary_copy != flag:
            raise Exception('backups preempts auxilary copy' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting backups_preempts_auxilary_copy")

    @property
    def restore_preempts_other_jobs(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.restore_preempts_other_jobs

    @restore_preempts_other_jobs.setter
    @argtypes(bool)
    def restore_preempts_other_jobs(self, flag):
        """
        enable/disable, restore preempts other jobs
            Args:
                flag    (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.restore_preempts_other_jobs = flag
        if self.management.restore_preempts_other_jobs != flag:
            raise Exception('restore preempts other jobs' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting restore_preempts_other_jobs")

    @property
    def enable_multiplexing_for_oracle(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.enable_multiplexing_for_oracle

    @enable_multiplexing_for_oracle.setter
    @argtypes(bool)
    def enable_multiplexing_for_oracle(self, flag):
        """
        enable/disable, enable multiplexing for oracle
            Args:
                 flag   (bool)  --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.enable_multiplexing_for_oracle = flag
        if self.management.enable_multiplexing_for_oracle != flag:
            raise Exception('enable multiplexing for oracle' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting enable_multiplexing_for_oracle")

    @property
    def job_stream_high_water_mark_level(self):
        """
        gets the job stream high water mark level
        """
        return self.management.job_stream_high_water_mark_level

    @job_stream_high_water_mark_level.setter
    @argtypes(int)
    def job_stream_high_water_mark_level(self, level):
        """
        sets, job stream high water mak level
            Args:
                level   (int)       --      number of jobs to be performed at a time

            Raises:
                SDKException:
                    if input is not valid type
        """
        self.management.job_stream_high_water_mark_level = level
        if self.management.job_stream_high_water_mark_level != level:
            raise Exception('job stream high watermark level' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting job_stream_high_water_mark_level")

    @property
    def backups_preempts_other_backups(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.backups_preempts_other_backups

    @backups_preempts_other_backups.setter
    @argtypes(bool)
    def backups_preempts_other_backups(self, flag):
        """
        enable/disable, backups preempts other backups
            Args:
                 flag   (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not a valid type
        """
        self.management.backups_preempts_other_backups = flag
        if self.management.backups_preempts_other_backups != flag:
            raise Exception('backups preempts other backups' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting backups_preempts_other_backups")

    @property
    def do_not_start_backups_on_disabled_client(self):
        """
        Returns True if option is enabled
        else returns False
        """
        return self.management.do_not_start_backups_on_disabled_client

    @do_not_start_backups_on_disabled_client.setter
    @argtypes(bool)
    def do_not_start_backups_on_disabled_client(self, flag):
        """
         enable/disable, do not start backups on disabled client
            Args:
                 flag   (bool)      --      (True/False) to be set

            Raises:
                SDKException:
                    if input is not a valid type
        """
        self.management.do_not_start_backups_on_disabled_client = flag
        if self.management.do_not_start_backups_on_disabled_client != flag:
            raise Exception('do not start backups on disabled client' + 'setting is not applied successfully')
        self.log.info("Successfully modified the setting do_not_start_backups_on_disabled_client")

    @argtypes(str)
    def get_restart_setting(self, jobtype):
        """
        restart settings associated to particular jobtype can be obtained
            Args:
                jobtype     (str)       --      settings of the jobtype to get

                Available jobtypes:

                        "Disaster Recovery backup"
                        "Auxiliary Copy"
                        "Data Aging"
                        "Download/Copy Updates"
                        "Offline Content Indexing"
                        "Information Management"
                        "File System and Indexing Based (Data Protection)"
                        "File System and Indexing Based (Data Recovery)"
                        "Exchange DB (Data Protection)"
                        "Exchange DB (Data Recovery)"
                        "Informix DB (Data Protection)"
                        "Informix DB (Data Recovery)"
                        "Lotus Notes DB (Data Protection)"
                        "Lotus Notes DB (Data Recovery)"
                        "Oracle DB (Data Protection)"
                        "Oracle DB (Data Recovery)"
                        "SQL DB (Data Protection)"
                        "SQL DB (Data Recovery)"
                        "MYSQL (Data Protection)"
        `               "MYSQL (Data Recovery)"
                        "Sybase DB (Data Protection)"
                        "Sybase DB (Data Recovery)"
                        "DB2 (Data Protection)"
                        "DB2 (Data Recovery)"
                        "CDR (Data Management)"
                        "Media Refresh"
                        "Documentum (Data Protection)"
                        "Documentum (Data Recovery)"
                        "SAP for Oracle (Data Protection)"
                        "SAP for Oracle (Data Recovery)"
                        "PostgreSQL (Data Protection)"
                        "PostgreSQL (Data Recovery)"
                        "Other (Data Protection)"
                        "Other (Data Recovery)"
                        "Workflow"
                        "DeDup DB Reconstruction"
                        "CommCell Migration Export"
                        "CommCell Migration Import"
                        "Install Software"
                        "Uninstall Software"
                        "Data Verification"
                        "Big Data Apps (Data Protection)"
                        "Big Data Apps (Data Recovery)"
                        "Cloud Apps (Data Protection)"
                        "Cloud Apps (Data Recovery)"
                        "Virtual Server (Data Protection)"
                        "Virtual Server (Data Recovery)"
                        "SAP for Hana (Data Protection)"
                        "SAP for Hana (Data Recovery)"



            Returns:
                dict          --        settings of the specific job type as follows
                                        {
                                            "jobTypeName": "File System and Indexing Based (Data Protection)",
                                            "restartable": true,
                                            "maxRestarts": 10,
                                            "restartIntervalInMinutes": 20,
                                            "enableTotalRunningTime": false,
                                            "totalRunningTime": 25200,
                                            "killRunningJobWhenTotalRunningTimeExpires": false,
                                            "preemptable": true,

                                        }
                None        --          if not found.

            Raises:
                SDKException:
                    if input is not valid type
        """
        return self.management.get_restart_setting(jobtype)

    @argtypes(str)
    def get_priority_setting(self, jobtype):
        """
        priority settings associated to particular jobtype can be obtained
            Args:
                jobtype     (str)       --      settings of jobtype to get

                Available jobtype

                    "Information Management"
                    "Auxiliary Copy"
                    "Media Refresh"
                    "Data Verification"
                    "Persistent Recovery"
                    "Synth Full"

                    "Windows File System"
                    "Windows XP 64-bit File System"
                    "Windows 2003 32-bit File System"
                    "Windows 2003 64-bit File System"
                    "Active Directory"
                    "Windows File Archiver"
                    "File Share Archiver"
                    "Image Level"
                    "Exchange Mailbox (Classic)"
                    "Exchange Mailbox Archiver"
                    "Exchange Compliance Archiver"
                    "Exchange Public Folder"
                    "Exchange Database"
                    "SharePoint Database"
                    "SharePoint Server Database"
                    "SharePoint Document"
                    "SharePoint Server"
                    "Novell Directory Services"
                    "GroupWise DB"
                    "NDMP"
                    "Notes Document"
                    "Unix Notes Database"
                    "MAC FileSystem"
                    "Big Data Apps"
                    "Solaris File System"
                    "Solaris 64bit File System"
                    "FreeBSD"
                    "HP-UX File System"
                    "HP-UX 64bit File System"
                    "AIX File System"
                    "Unix Tru64 64-bit File System"
                    "Linux File System"
                    "Sybase Database"
                    "Oracle Database"
                    "Oracle RAC"
                    "Informix Database"
                    "DB2"
                    "DB2 on Unix"
                    "SAP for Oracle"
                    "SAP for MAX DB"
                    "ProxyHost on Unix"
                    "ProxyHost"
                    "Image Level On Unix"
                    "OSSV Plug-in on Windows"
                    "OSSV Plug-in on Unix"
                    "Unix File Archiver"
                    "SQL Server"
                    "Data Classification"
                    "OES File System on Linux"
                    "Centera"
                    "Exchange PF Archiver"
                    "Domino Mailbox Archiver"
                    "MS SharePoint Archiver"
                    "Content Indexing Agent"
                    "SRM Agent For Windows File Systems"
                    "SRM Agent For UNIX File Systems"
                    "DB2 MultiNode"
                    "MySQL"
                    "Virtual Server"
                    "SharePoint Search Connector"
                    "Object Link"
                    "PostgreSQL"
                    "Sybase IQ"
                    "External Data Connector"
                    "Documentum"
                    "Object Store"
                    "SAP HANA"
                    "Cloud Apps"
                    "Exchange Mailbox"

            Returns:
                dict        --          settings of a specific jobtype
                                        {
                                            "jobTypeName": "Information Management",
                                            "combinedPriority": 0,
                                            "type_of_operation": 1
                                        }

                                        or

                                        {
                                            "appTypeName": "Windows File System",
                                            "combinedPriority": 6,
                                            "type_of_operation": 2
                                        }

                None        --          if not found.
            Raises:
                SDKException:
                    if input is not valid type

        """
        return self.management.get_priority_setting(jobtype)

    @argtypes(str)
    def get_update_setting(self, jobtype):
        """
        update settings associated to particular jobtype can be obtained
            Args:
                jobtype     (str)       --      settings of jobtype to get

                Available jobtype

                    Check get_priority_setting(self, jobtype) method documentation.

            Returns:
                dict        -           settings of a jobtype
                                        {
                                            "appTypeName": "Windows File System",
                                            "recoveryTimeInMinutes": 20,
                                            "protectionTimeInMinutes": 20
                                        }

                None        --          if not found.
            Raises:
                SDKException:
                    if input is not valid type

        """
        return self.management.get_update_setting(jobtype)
