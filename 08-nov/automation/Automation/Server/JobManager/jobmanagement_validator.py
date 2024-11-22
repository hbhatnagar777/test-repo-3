# -*- coding: utf-8 -*-
# pylint: disable=W1202

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing job management settings validations.

JobManagementValidator is the only class defined in this file

JobManagementValidator:
    __init__(test_object)                                --          initialize instance of the JobManagementValidator
                                                                     class.

    _entities_setup()                                    --          creates disklibrary and storage policy
                                                                     entities.

    _create_pre_scan_script()                            --          creates pre scan script on the client

    create_subclient()                                   --          creates required number of subclients

    validate_job_preemption()                            --          validates job preemption feature.

    _job_via_schedule()                                  --          triggers a job via schedule.

    _job_via_schedule_policy()                           --          triggers a job via schedule policy.

    validate()                                           --          entry point for validations

    validate_job_max_restarts()                          --          validates job max restarts feature.

    validate_job_total_running_time_pending_scenario()   --          validates total running time scenario 1
                                                                     (pending -> failed)

    validate_job_total_running_time_killed_scenario()    --          validates total running time scenario 2
                                                                    (kill job after total time expires)

    validate_high_watermark_level()                      --          validates high water mark level feature

    validate_queue_jobs_if_conflicting_job_active()      --          validates queue jobs if conflicting job
                                                                     active feature.

    validate_queue_job_if_activity_is_disable()          --          validates queue job if activity is disable

    validate_queue_schedule_jobs()                       --          validates queue schedule jobs feature

    validate_job_max_restarts_change_prop                --          validates if job max-restartability is changed while job is still running

    disable_restartability_test                          --          validates if job restarts after restartability is disabled
    
    validate_disabled_client_jobs                        --          validates if job runs while client is disabled
    
    client_Job_throttle                                  --          validates client/client_group job throttling property
    
    job_suspend_interval                                 --          validates if auto resume option of the job runs when suspended
    
    job_priority                                         --          validates the priority of job at client and agent level
    
    set_job_priority                                     --          to set the priority of job at client/agent 
    
    validate_missing_files_failed_job                    --          to validate if some file is deleted after scan phase
    
    validate_blackout_window_jobs                        --          validates if running job should get completed during blackout window.

"""

import time
from datetime import datetime,timedelta

from cvpysdk.client import Client
from cvpysdk.agent import Agent
from cvpysdk.subclient import Subclient, Subclients
from cvpysdk.commcell import Commcell
from cvpysdk.policies import schedule_policies
from cvpysdk import schedules
from cvpysdk import activitycontrol
from cvpysdk.clientgroup import ClientGroups, ClientGroup
from AutomationUtils.constants import FAILED
from AutomationUtils.constants import WINDOWS_TMP_DIR
from AutomationUtils.constants import UNIX_TMP_DIR
from .rpo_constants import MM_SERVICE_NAME
from AutomationUtils import logger, options_selector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Server.ActivityControl import activitycontrolhelper
from Server.Scheduler import schedulerhelper
from Server.JobManager.jobmanagement_helper import JobManagementHelper
from Server.OperationWindow.ophelper import OpHelper

class JobManagementValidator(object):
    """JobManagementValidator helper class to perform job management validations"""

    def __init__(self, test_object):
        """Initialize instance of the JobManagementValidator class."""
        self.log = logger.get_log()
        self.test_object = test_object
        self.common_utils = CommonUtils(test_object.commcell)
        self.commcell = test_object.commcell
        self.job_manager = self.common_utils.job_manager
        self.client_machine_obj = Machine(test_object.client.client_name, self.commcell)
        self.schedule_policies = schedule_policies.SchedulePolicies(self.commcell)
        self._utility = options_selector.OptionsSelector(self.commcell)
        self.pre_scan_script = None
        self._cs_db = test_object.csdb
        self.management = JobManagementHelper(self.commcell)
        self.schedule_creation_helper = schedulerhelper.ScheduleCreationHelper(test_object)
        self.client_groups = ClientGroups(self.commcell)

    def _entities_setup(self, streams=None):
        """
        Creates disklibrary and storage policy entities for automation.

        Returns:
            (obj)              --       subclient object(s) with the required entities

        """
        if not self.test_object.client:
            raise Exception('Client name must be passed in the input json')
        self._entities = options_selector.CVEntities(self.commcell)
        ready_ma = self._utility.get_ma("any")
        self.current_time = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        entity_inputs = {
            'target':
                {
                    'client': self.test_object.client.client_name,
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'backupset': "defaultBackupSet",
                    'mediaagent': ready_ma
                },
            'disklibrary': {
                'name': "disklibrary_" + self.current_time,
                'mount_path': self._entities.get_mount_path(ready_ma),
                'cleanup_mount_path': True,
                'force': False,
                },
            'storagepolicy':
                {
                    'name': "storagepolicy_" + self.current_time,
                    'dedup_path': None,
                    'incremental_sp': None,
                    'retention_period': 3,
                    'force': False,
                    'number_of_streams': streams
                }
        }
        self._entities.create(entity_inputs)

    def _create_pre_scan_script(self, content=''):
        """creates pre scan script required by subclient pre/post processing
           with content passed.

        Args:
            content           (str)   --  content that is to be written to file

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create file

        """
        if self.client_machine_obj.os_info.lower() == 'windows':
            self.pre_scan_script = self.client_machine_obj.join_path(
                WINDOWS_TMP_DIR,
                'temp' + self.current_time + ".bat")
        else:
            self.pre_scan_script = self.client_machine_obj.join_path(
                UNIX_TMP_DIR,
                'temp' + self.current_time + ".sh")
        if self.client_machine_obj.check_file_exists(self.pre_scan_script):
            self.log.info("deleting existing pre scan script {0}".format(self.pre_scan_script))
            self.client_machine_obj.delete_file(self.pre_scan_script)
        self.log.info("creating pre scan command file {0}".format(self.pre_scan_script))
        self.client_machine_obj.create_file(self.pre_scan_script, content)
        if self.client_machine_obj.os_info.lower() == "unix":
            self.client_machine_obj.change_file_permissions(self.pre_scan_script, '777')

    def create_subclient(self, no_subclients=1,level = 3,size = 100):
        """
        Creates number of subclients based on the parameter no_subclients

            Args:
                 no_subclients  (int)           --          number of subclients to be created

            Returns:
                (list)                          --          properties of a created subclients
        """
        subclient_pattern = {
            'subclient':
                {
                    'name': "",
                    'client': self.test_object.client.client_name,
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': "storagepolicy_" + self.current_time,
                    'backupset': 'defaultBackupSet',
                    'level': level,
                    'size': size,
                    'pre_scan_cmd': self.pre_scan_script,
                    'force': False,
                }
        }

        subclient_objects = []
        for value in range(no_subclients):
            current_time = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
            subclient_pattern['subclient']['name'] = str(self.test_object.id) + 'subclient' + current_time
            subclient_objects.append(self._entities.create(subclient_pattern))
        return subclient_objects

    def validate(self, features):
        """
        Entry point for feature validations

            Args:
                features        (list)      --      list of features to be validated.

        Returns :
            None
        """
        try:
            subclient_properties = None
            self.log.info('Creating DiskLibrary and Storage policy')
            self._entities_setup()
            self.log.info('Successfully created DiskLibrary and Storage policy')
            for feature in features:
                method_name = feature.lower()
                if method_name == 'queue_job_if_activity_is_disable':
                    subclient_properties = self.create_subclient()
                    entity_objects = [self.test_object.commcell, self.test_object.client,
                                      subclient_properties[0]['subclient']['agent'],
                                      subclient_properties[0]['subclient']['object']]
                    for entity in entity_objects:
                        self.validate_queue_job_if_activity_is_disable(entity, subclient_properties)
                elif method_name == 'job_total_running_time_commcell':
                    trigger = ['schedule_policy', 'schedule', 'ondemand']
                    self._create_pre_scan_script(content='exit 1')
                    subclient_properties = self.create_subclient()
                    for way in trigger:
                        self.validate_job_total_running_time_killed_scenario(subclient_properties, 'commcell', way)
                        self.validate_job_total_running_time_pending_scenario(subclient_properties, 'commcell', way)
                elif method_name == 'job_total_running_time_subclient':
                    trigger = ['schedule', 'ondemand']
                    self._create_pre_scan_script(content='exit 1')
                    subclient_properties = self.create_subclient()
                    for way in trigger:
                        self.validate_job_total_running_time_killed_scenario(subclient_properties, 'subclient', way)
                        self.validate_job_total_running_time_pending_scenario(subclient_properties, 'subclient', way)
                elif method_name == 'job_max_restarts_subclient':
                    self._create_pre_scan_script(content='exit 1')
                    subclient_properties = self.create_subclient()
                    trigger = ['ondemand', 'schedule']
                    for way in trigger:
                        self.validate_job_max_restarts(subclient_properties, 'subclient', way)
                elif method_name == 'job_max_restarts_commcell':
                    self._create_pre_scan_script(content='exit 1')
                    subclient_properties = self.create_subclient()
                    trigger = ['ondemand', 'schedule_policy', 'schedule']
                    for way in trigger:
                        self.validate_job_max_restarts(subclient_properties, 'commcell', way)
                elif method_name == 'high_water_mark_level':
                    subclient_properties = self.create_subclient(no_subclients=3)
                    self.validate_high_watermark_level(subclient_properties)
                elif method_name == 'job_preemption' or method_name == 'queue_jobs_if_conflicting_job_active' or \
                        method_name == 'queue_schedule_jobs':
                    if not subclient_properties:
                        subclient_properties = self.create_subclient()
                    getattr(self, 'validate_' + method_name)(subclient_properties, True)
                    getattr(self, 'validate_' + method_name)(subclient_properties, False)
                elif method_name == 'job_zero_restarts_commcell':
                    self._create_pre_scan_script(content='exit 1')
                    subclient_properties = self.create_subclient()
                    # trigger = ['ondemand', 'schedule_policy', 'schedule']
                    trigger = ['ondemand', 'schedule']
                    for job_type in trigger:
                        self.validate_job_max_restarts(
                            subclient_properties, 'commcell', job_type, max_restarts=0)
                        self.validate_job_max_restarts(
                            subclient_properties, 'subclient', job_type, max_restarts=0)
                elif method_name == 'queue_job_client_group':
                    clientgroup_name = 'ClientGroup_' + datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S')
                    client_gp = self.client_groups.add(
                        clientgroup_name, [self.test_object.client.client_name])
                    self.client_group = client_gp
                    self.client_group.update_properties(
                        {"queueConflictingJobsEnabledForCG": True})
                    ###################################Case 1#####################################
                    subclient_properties = self.create_subclient()
                    self.log.info("Running full backup of subclient ")
                    self.validate_queue_jobs_if_conflicting_job_active(
                        subclient_properties, True, Commcell_level=False)
                    self.validate_queue_jobs_if_conflicting_job_active(
                        subclient_properties, False, Commcell_level=False)
                    self.client_groups.delete(clientgroup_name)
                    time.sleep(20)
                elif method_name == 'queue_job_clientgroup_resume_after_failed':
                    ##################################CASE 2######################################
                    self.validate_queue_job_clientgroup_resume_after_failed()
                elif method_name == 'disabled_client_run_no_job':
                    subclient_properties = self.create_subclient()
                    self.validate_disabled_client_jobs(subclient_properties)
                elif method_name == 'job_throttle_client':
                    self.client_Job_throttle()
                elif method_name == 'job_throttle_client_group':
                    self.client_Job_throttle(clientgroup=True)
                elif method_name == 'job_suspended_delay':
                    self.job_suspend_interval()
                elif method_name == 'job_priority':
                    self.job_priority()
                elif method_name == 'missing_files_failed':
                    self.validate_missing_files_failed_job()
                elif method_name == 'blackout_window_validation':
                    self.validate_blackout_window_jobs()
                else:
                    raise Exception('pass the valid feature name {0}'.format(method_name))

        finally:
            time.sleep(30)
            # sometimes entity cleanup fails saying that jobs are still running,
            # JM marks job as completed but sometimes it will get stuck in index update.
            self._entities.cleanup()

    def validate_job_preemption(self, subclient_properties, action):
        """
        Validates job preemption feature at commcell level

            Args:
                subclient_properties    (dict)      --      dict obtained from CVEntities.create()

                action                  (bool)      --       enable/disable of feature to be validated

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails.

        Validates below cases:
            Disable preemption : Job should not be suspended.
            Enable preemption : Job should get suspended

        """
        self.log.info('Validating the job preemption feature at commcell level')
        subclient_object = subclient_properties[0]['subclient']['object']
        jobtype = "File System and Indexing Based (Data Protection)"
        self.log.info('obtaining the restart settings of jobtype {0}'.format(jobtype))
        initial_setting = self.management.get_restart_setting(jobtype)
        copy_settings = initial_setting.copy()
        self.log.info('initial settings are as follows {0}'.format(initial_setting))
        try:
            initial_setting['preemptable'] = action
            self.log.info('Preemptable property of jobtype is set to {0}= {1}'.format(jobtype, action))
            self.management.modify_restart_settings([initial_setting])
            self.log.info('modified settings are as follows {0}'.format(self.management.get_restart_setting(jobtype)))
            self.job_manager.job = self.common_utils.subclient_backup(subclient_object, "full", False)
            self.log.info('Full backup is triggered on subclient {0} with job id : {1}'.
                          format(subclient_object, self.job_manager.job.job_id))
            self.job_manager.wait_for_state('running', time_limit=2)
            self.job_manager.modify_job('suspend', hardcheck=False, wait_for_state=False)
            self.log.info('suspend command issued')

            if action:
                self.job_manager.wait_for_state(expected_state='suspended')
                if self.job_manager.job.status != 'Suspended':
                    raise Exception("Job is not suspended, it should be as preemptable is enabled")
                self.job_manager.modify_job('kill')
                self.log.info('job preemption enable feature validated successfully')
            else:
                self.job_manager.wait_for_state('completed', time_limit=30)
                self.log.info('job preemption disable feature validated successfully')
        except Exception as exp:
            if self.job_manager.job and self.job_manager.job not in ('Completed', 'Failed', 'Killed', 'Commited'):
                self.job_manager.modify_job('kill')
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            self.management.modify_restart_settings([copy_settings])

    def _job_via_schedule(self, subclient_object, options=None):
        """
        Triggers job via schedule

            Args:
                subclient_object        (obj)   --      instance of the subclient

                options                 (dict)  --      advanced options to be included

            Returns:
                job object

        """
        timezone = self.schedule_creation_helper.get_client_tzone(client=self.test_object.client)[1]
        current_time = self.client_machine_obj.current_time(timezone)
        date, rtime = schedulerhelper.ScheduleCreationHelper.add_minutes_to_datetime(time=current_time, minutes=3)
        pattern = {"freq_type": 'one_time',
                   "active_start_date": str(date),
                   "active_start_time": str(rtime)
                   }
        schedule_object = self.common_utils.subclient_backup(subclient_object, "full", wait=False,
                                                             common_backup_options=options,
                                                             schedule_pattern=pattern)
        job_list = schedulerhelper.SchedulerHelper(schedule_object,
                                                   self.commcell).check_job_for_taskid(retry_count=8,
                                                                                       retry_interval=30)
        job_object = job_list[0]
        return job_object

    def _job_via_schedule_policy(self, subclient_object):
        """
        Triggers job via schedule Policy

            Args:
                subclient_object        (obj)   --      instance of the subclient

            Returns:
                job object

        """
        assocs = [{
            "clientName": self.test_object.client.client_name,
            "backupsetName": 'defaultBackupSet',
            "subclientName": subclient_object.name,
            "instanceName": "DefaultInstanceName",
            "appName": "File System"
        }]

        timezone = self.schedule_creation_helper.get_client_tzone(client=self.test_object.client)[1]	
        current_time = self.client_machine_obj.current_time(timezone)
        date, rtime = schedulerhelper.ScheduleCreationHelper.add_minutes_to_datetime(time=current_time, minutes=3)
        current_time = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        pattern = [{'name': 'Auto' + current_time,
                    'pattern': {"freq_type":
                                'one_time',
                                "active_start_date": str(date),
                                "active_start_time": str(rtime)
                                }}]
        types = [{"appGroupName": "Protected Files"}]
        schedule_policy = self.schedule_policies.add(name='auto' + current_time,
                                                     policy_type='Data Protection', associations=assocs,
                                                     schedules=pattern, agent_type=types)
        schedules_list = schedule_policy.all_schedules
        schedule_object = schedules.Schedule(self.test_object.commcell,
                                             schedule_id=schedules_list[0]['schedule_id'])
        job_list = schedulerhelper.SchedulerHelper(schedule_object,
                                                   self.commcell).check_job_for_taskid(retry_count=8,
                                                                                       retry_interval=30)
        job_object = job_list[0]
        return job_object

    def validate_job_max_restarts(self, subclient_properties, entitiy_level, trigger, max_restarts=2):
        """
        Validates job max restarts feature

            Description of the feature:
            say max restarts = 2
            job should be resumed or restarted as per max restarts
            after exhaustive attempts or max restarts job should be failed

            Args:
                subclient_properties    (dict)  --      dict obtained from CVEntities.create()

                entitiy_level           (str)   --      at which level feature need to be validated

                    Values:

                        "commcell"
                        "subclient"

                trigger                 (str)   --      in what way job must should be triggered

                    Values:

                        "ondemand"
                        "schedule"
                        "schedule_policy"

                max_restarts            (int)  --       no. of restarts that job can have at max.        

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails
        """
        job_object = None
        restart_interval = 1
        jobtype = "File System and Indexing Based (Data Protection)"
        self.log.info('Validating job max restarts at {0} level, job is triggered through = {1}'.format(
            entitiy_level, trigger))
        subclient_object = subclient_properties[0]['subclient']['object']
        self.log.info('obtaining the restart settings of jobtype {0}'.format(jobtype))
        initial_setting = self.management.get_restart_setting(jobtype)
        default_settings = initial_setting.copy()
        try:
            if entitiy_level.lower() == 'commcell':
                self.log.info('initial settings are as follows {0}'.format(initial_setting))

                initial_setting['restartable'] = True
                initial_setting['maxRestarts'] = max_restarts

                initial_setting['restartIntervalInMinutes'] = restart_interval
                initial_setting['enableTotalRunningTime'] = False
                self.management.modify_restart_settings([initial_setting])
                self.log.info('modified settings are as follows {0}'.format(
                    self.management.get_restart_setting(jobtype)))
                if trigger == 'schedule':
                    job_object = self._job_via_schedule(subclient_object)
                elif trigger == 'schedule_policy':
                    job_object = self._job_via_schedule_policy(subclient_object)
                elif trigger == 'ondemand':
                    job_object = self.common_utils.subclient_backup(subclient_object, "full", wait=False)
                else:
                    raise Exception('Unexpected value passed for parameter trigger')
            elif entitiy_level.lower() == 'subclient':
                options = {
                    'enable_number_of_retries': True,
                    'number_of_retries': max_restarts
                }
                initial_setting['restartIntervalInMinutes'] = restart_interval
                initial_setting['enableTotalRunningTime'] = False

                self.management.modify_restart_settings([initial_setting])
                self.log.info('modified settings are as follows {0}'.format(
                    self.management.get_restart_setting(jobtype)))
                if trigger == 'schedule':
                    job_object = self._job_via_schedule(subclient_object, options)
                elif trigger == 'ondemand':
                    job_object = self.common_utils.subclient_backup(subclient_object, 'full', wait=False,
                                                                    common_backup_options=options)
                elif trigger == 'schedule_policy':
                    pass    # Changes need to be done in schedule policy creation(sdk) to change JM settings
                else:
                    raise Exception('Unexpected value passed for parameter trigger')
            self.job_manager.job = job_object
            self.log.info('Full backup is triggered on subclient {0} with job id : {1}'.
                          format(subclient_object, self.job_manager.job.job_id))

            self.job_manager.wait_for_state(expected_state='failed', time_limit=30)
            # if 'Number of restarts has exceeded the maximum number allowed' not in self.job_manager.job.delay_reason:
            #    raise Exception("delay reason didn't match, obtained = {0}".format(self.job_manager.job.delay_reason))
            # self.log.info('Validated job delay reason')
            self.log.info('Delay reason of the job {0} is {1}'.format(self.job_manager.job.job_id,
                                                                      self.job_manager.job.delay_reason))
            _, rows = self._utility.exec_commserv_query("select count(phase) from JMBkpAtmptStats where "
                                              "jobid = {0} and phase = {1} group by "
                                              "phase".format(self.job_manager.job.job_id, 3))
            if int(rows[0][0]) != max_restarts + 1:
                raise Exception('given number of attempts are not performed,'
                                ' failed at {0} {1}'.format(entitiy_level, trigger))
            else:
                self.log.info('level = {0}, job triggered via {1} successfully validated'
                              ' max restarts'.format(entitiy_level, trigger))
        except Exception as exp:
            if job_object and job_object.status not in ('Completed', 'Failed', 'Killed'):
                self.job_manager.modify_job('kill')
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            self.log.info('Applying default settings as follows {0}'.format(default_settings))
            self.management.modify_restart_settings([default_settings])

    def validate_job_total_running_time_pending_scenario(self, subclient_properties, entitiy_level, trigger):
        """
        Validates job total running time feature(scenario 1)

            Description of the scenario 1:

            say total running time = 5 minutes
            scenario 1: after 5 minutes if the job is in pending or waiting state then the job should be failed

            Args:
                subclient_properties    (dict)  --      dict obtained from CVEntities.create()

                entitiy_level           (str)   --      at which level feature need to be validated

                    Values:

                        "commcell"
                        "subclient"

                trigger                 (str)   --      in what way job must be triggered

                    Values:

                        "ondemand"
                        "schedule"
                        "schedule_policy"

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails
        """
        job_object = None
        total_run_rime = 120  # secs
        restart_interval = 30  # mins
        jobtype = "File System and Indexing Based (Data Protection)"
        self.log.info('entity level = {0} job triggered via = {1} ,'
                      'Validating, pending -> failed, when job is'
                      ' in pending state after reaches time interval.'.format(entitiy_level, trigger))
        subclient_object = subclient_properties[0]['subclient']['object']
        self.log.info('obtaining the restart settings of jobtype {0}'.format(jobtype))
        initial_setting = self.management.get_restart_setting(jobtype)
        default_settings = initial_setting.copy()
        try:
            # ---------------------------- scenario #1 start----------------------------------------------------- #
            if entitiy_level == 'commcell':
                self.log.info('initial settings are as follows {0}'.format(initial_setting))
                initial_setting['enableTotalRunningTime'] = True
                initial_setting['restartIntervalInMinutes'] = restart_interval
                initial_setting['totalRunningTime'] = total_run_rime
                initial_setting['killRunningJobWhenTotalRunningTimeExpires'] = False
                self.log.info('enabling the total running time property with {0} minutes for jobtype'
                              ' {1}'.format(3, jobtype))
                self.management.modify_restart_settings([initial_setting], validation=False)
                self.log.info('modified settings are as follows {0}'.format(
                    self.management.get_restart_setting(jobtype)))
                if trigger == 'ondemand':
                    job_object = self.common_utils.subclient_backup(subclient_object, "full", False)
                elif trigger == 'schedule':
                    job_object = self._job_via_schedule(subclient_object)
                elif trigger == 'schedule_policy':
                    job_object = self._job_via_schedule_policy(subclient_object)
                else:
                    raise Exception('Unexpected value passed for parameter trigger')
            elif entitiy_level == 'subclient':
                options = {
                    'enable_total_running_time': True,
                    'total_running_time': total_run_rime
                }
                if trigger == 'ondemand':
                    job_object = self.common_utils.subclient_backup(subclient_object, 'full', wait=False,
                                                                    common_backup_options=options)
                elif trigger == 'schedule':
                    job_object = self._job_via_schedule(subclient_object, options)
                elif trigger == 'schedule_policy':
                    pass    # Changes need to be done in schedule policy creation(sdk) to change JM settings
                else:
                    raise Exception('Unexpected value passed for parameter trigger')
            self.job_manager.job = job_object
            self.log.info('Full backup is triggered on subclient {0} with job id : {1}'.
                          format(subclient_object, self.job_manager.job.job_id))
            self.job_manager.wait_for_state(expected_state='pending', time_limit=2)
            fail_status = self.job_manager.wait_for_state(expected_state=['failed', 'killed'],
                                                          hardcheck=False, time_limit=30)
            if 'The job has exceeded the total running time' not in self.job_manager.job.delay_reason:
                raise Exception("delay reason didn't match, obtained = {0}".format(self.job_manager.job.delay_reason))
            self.log.info('Validated job delay reason')
            self.log.info('Delay reason of the job {0} is {1}'.format(self.job_manager.job.job_id,
                                                                      self.job_manager.job.delay_reason))
            if fail_status:
                self.log.info('job is in failed state')
                self.log.info('Successfully Validated at level {0} job'
                              ' triggered via = {1} ,pending -> failed,'
                              ' when job is in pending state'
                              ' after reaches time interval'.format(entitiy_level, trigger))
            else:
                raise Exception('job is not in failed state')
        except Exception as exp:
            if job_object and job_object.status not in ('Completed', 'Failed', 'Killed'):
                self.job_manager.modify_job('kill')
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            self.log.info('Applying default settings as follows {0}'.format(default_settings))
            default_settings['enableTotalRunningTime'] = True
            self.management.modify_restart_settings([default_settings], validation=False)
            default_settings['enableTotalRunningTime'] = False
            self.management.modify_restart_settings([default_settings], validation=False)

    def validate_job_total_running_time_killed_scenario(self, subclient_properties, entitiy_level, trigger):
        """
        Validates job total running time feature(scenario 2)

             Description of the scenario 2:

            say total running time = 5 minutes
            if killRunningJobWhenTotalRunningTimeExpires is enabled : running job should be killed after time expires.

            Args:
                subclient_properties    (dict)  --      dict obtained from CVEntities.create()

                entitiy_level           (str)   --      at which level feature need to be validated

                    Values:

                        "commcell"
                        "subclient"

                trigger                 (str)   --      in what way job must should be triggered

                    Values:

                        "ondemand"
                        "schedule"
                        "schedule_policy"

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails
        """
        job_object = None
        total_runtime = 60  # secs
        acceptable_delay = 900  # secs
        restart_interval = 30  # mins
        jobtype = "File System and Indexing Based (Data Protection)"
        self.log.info('entity level = {0}, job triggered via = {1},'
                      ' Validating, killRunningJobWhenTotalRunningTimeExpires'.format(entitiy_level, trigger))
        backupset_object = subclient_properties[0]['subclient']['backupset']
        # Picking default subclient from DefaultBackupSet for this testcase, Because backup must run for certain time
        # to validate this case, so instead of generating dummy data on client, i am using default subclient.
        subclient_object = Subclients(backupset_object).get("default")
        # Here we are modifying the storage policy of default subclient as the space consumed will be later pruned.
        # after all the validatioon we restore it to the previous policy
        hasPlan = False
        if subclient_object.plan is not None:
            hasPlan  = True
            previous_storage_policy = subclient_object.plan
            subclient_object.plan = None
        else:
            previous_storage_policy = subclient_object.properties.get(
                    'commonProperties').get('storageDevice').get('dataBackupStoragePolicy').get('storagePolicyName', {})

        if not previous_storage_policy:
            raise Exception('Please attach a storage policy/plan to default subclient of DefaultBackupSet')

        subclient_object.update_properties(
            {'commonProperties':
                 {'storageDevice':
                      {'dataBackupStoragePolicy':
                           {'storagePolicyName' : subclient_properties[0]['subclient']['storagepolicy_name']
                            }
                       }
                  }
             })
        self.log.info('obtaining the restart settings of jobtype {0}'.format(jobtype))
        initial_setting = self.management.get_restart_setting(jobtype)
        default_settings = initial_setting.copy()
        self.job_manager.modify_all_jobs(operation_type='kill')
        time.sleep(20)
        try:
            if entitiy_level == 'commcell':
                initial_setting['enableTotalRunningTime'] = True
                initial_setting['restartIntervalInMinutes'] = restart_interval
                initial_setting['totalRunningTime'] = total_runtime
                initial_setting['killRunningJobWhenTotalRunningTimeExpires'] = True
                self.log.info('enabling killRunningJobWhenTotalRunningTimeExpires property for jobtype '
                              '{0}'.format(jobtype))
                self.management.modify_restart_settings([initial_setting], validation=False)
                self.log.info('modified settings are as follows {0}'.format(
                    self.management.get_restart_setting(jobtype)))
                if trigger == 'ondemand':
                    job_object = self.common_utils.subclient_backup(subclient_object, "full", False)
                elif trigger == 'schedule':
                    job_object = self._job_via_schedule(subclient_object)
                elif trigger == 'schedule_policy':
                    job_object = self._job_via_schedule_policy(subclient_object)
                else:
                    raise Exception('Unexpected value passed for parameter trigger')
            elif entitiy_level == 'subclient':
                options = {
                    'enable_total_running_time': True,
                    'total_running_time': total_runtime,
                    'kill_running_job_when_total_running_time_expires': True
                }
                if trigger == 'ondemand':
                    job_object = self.common_utils.subclient_backup(subclient_object, 'full', wait=False,
                                                                    common_backup_options=options)
                elif trigger == 'schedule':
                    job_object = self._job_via_schedule(subclient_object, options)
                elif trigger == 'schedule_policy':
                    pass    # Changes need to be done in schedule policy creation(sdk) to change JM settingss
                else:
                    raise Exception('Unexpected value passed for parameter trigger')
            self.job_manager.job = job_object
            self.log.info('Full backup is triggered on subclient')
            self.job_manager.wait_for_state(expected_state='running')
            kill_status = self.job_manager.wait_for_state(expected_state=['failed', 'killed', 'committed'],
                                                          hardcheck=False,
                                                          time_limit=((total_runtime + acceptable_delay)//total_runtime))
            if 'The job has exceeded the total running time' not in self.job_manager.job.delay_reason:
                raise Exception("delay reason didn't match, obtained = {0}".format(self.job_manager.job.delay_reason))
            self.log.info('Validated job delay reason')
            self.log.info('Delay reason of the job {0} is {1}'.format(self.job_manager.job.job_id,
                                                                      self.job_manager.job.delay_reason))
            if kill_status:
                self.log.info('Successfully Validated at level = {0}, job triggered via = {1}'
                              ' killRunningJobWhenTotalRunningTimeExpires'.format(entitiy_level, trigger))
            else:
                raise Exception('job with id: {0} not killed successfully'.format(self.job_manager.job.job_id))
        except Exception as exp:
            if job_object and job_object.status not in ('Completed', 'Failed', 'Killed'):
                self.job_manager.modify_job('kill')
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            if hasPlan:
                subclient_object.plan = previous_storage_policy
            subclient_object.update_properties(
                {'commonProperties':
                     {'storageDevice':
                          {'dataBackupStoragePolicy':
                               {'storagePolicyName': previous_storage_policy}
                           }
                      }
                 })
            self.log.info('Applying default settings as follows {0}'.format(default_settings))
            default_settings['enableTotalRunningTime'] = True
            self.management.modify_restart_settings([default_settings], validation=False)
            default_settings['enableTotalRunningTime'] = False
            self.management.modify_restart_settings([default_settings], validation=False)

    def validate_high_watermark_level(self, subclient_properties):
        """
        Validates high water mark level feature

            Args:
                subclient_properties        (dict)      --      dict obtained from CVEntities.create()

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails

        Description of the faeture:

            say high watermark level = 6
            maximum 5 jobs should be running, 6th job should in waiting state
        """
        job_objects = []
        count = 0
        self.log.info('Validating High water mark level feature at commcell level')
        high_water_mark_level = 2
        default_value = self.management.job_stream_high_water_mark_level
        try:
            self.management.job_stream_high_water_mark_level = high_water_mark_level
            self.log.info('high water mark level is set to {0}'.format(
                self.management.job_stream_high_water_mark_level))

            for element in subclient_properties:
                subclient_object = element['subclient']['object']
                job_object = self.common_utils.subclient_backup(subclient_object, "full", False)
                job_objects.append(job_object)
            jobs_status = list()
            time_limit = 30  # mins
            total_time = time.time() + time_limit * 60
            while jobs_status.count('Completed') != 3:
                jobs_status.clear()
                jobs_status.append(job_objects[0].status)
                jobs_status.append(job_objects[1].status)
                jobs_status.append(job_objects[2].status)
                self.log.info('Status of the jobs: {0}, {1}, {2} = {3}'.format(
                    job_objects[0].job_id, job_objects[1].job_id, job_objects[2].job_id, jobs_status))
                if jobs_status.count('Running') > high_water_mark_level:
                    count += 1
                    if count > 4:
                        raise Exception('High Water mark level failed, Three jobs are running instead of two.')
                if 'Pending' in jobs_status or 'Failed' in jobs_status:
                    raise Exception('One of the job went into unexpected state,'
                                    ' status of three jobs as follows {0}, {1}, {2}= {3}'.format(
                                        job_objects[0].job_id, job_objects[1].job_id, job_objects[2].job_id, jobs_status))
                if time.time() >= total_time:
                    raise Exception('Total time of {0} mins elapsed, check logs for more info'.format(time_limit))
                time.sleep(10)
            self.log.info('High water mark level validated succesfully')
        except Exception as exp:
            if job_objects:
                self.job_manager.modify_all_jobs('kill')
                time.sleep(60)
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            self.management.job_stream_high_water_mark_level = default_value

    def validate_queue_jobs_if_conflicting_job_active(self, subclient_properties, action, Commcell_level=True):
        """
        Validates Queue jobs if conflicting job active feature at commcell level

            Args:

                subclient_properties        (dict)      --      dict obtained from CVEntities.create()

                action                  (bool)      --       enable/disable of feature to be validated

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails

         Description of the feature:

            run two backup jobs on same subclient, second backup job should be in queued state
        """
        self.log.info('Validating queue job if conflicting job active feature at commcell levels')
        job_object2 = None
        default_state = self.management.queue_jobs_if_conflicting_jobs_active
        try:
            if Commcell_level:
                self.management.queue_jobs_if_conflicting_jobs_active = action
                self.log.info('enabling the property "queue jobs if conflicting job active" '
                              '{0}'.format(self.management.queue_jobs_if_conflicting_jobs_active))

            subclient_object = subclient_properties[0]['subclient']['object']
            job_object1 = self.common_utils.subclient_backup(subclient_object, "full", False)
            self.log.info('Full backup is triggered on subclient with job id %s', job_object1.job_id)
            try:
                job_object2 = self.common_utils.subclient_backup(subclient_object, "full", False)
            except Exception as exp:
                if 'Another backup is running for client' in str(exp):
                    self.job_manager.job = job_object1
                    self.job_manager.wait_for_state(hardcheck=False, time_limit=30)
                    self.log.info('queue jobs if conflicting job active feature = {0} is'
                                  ' Validated successfully'.format(action))
            if action:
                time.sleep(20)
                self.log.info("status = {0}, Delay Reason = {1}".format(job_object2.status, job_object2.delay_reason))
                if job_object2.status == "Queued":
                    self.log.info('Delay reason of the second job {0} is {1}'.format(job_object2.job_id,
                                                                                     job_object2.delay_reason))
                    self.log.info('second backup job is in queue, Validated')
                    self.job_manager.job = job_object1
                    complete_status = self.job_manager.wait_for_state(hardcheck=False, time_limit=30)
                    if complete_status:
                        self.log.info('first backup job is successfully completed')
                        self.job_manager.job = job_object2
                        self.job_manager.modify_job('resume', hardcheck=False)
                        status2 = self.job_manager.wait_for_state(hardcheck=False, time_limit=30)
                        if status2:
                            self.log.info('second backup job is successfully completed')
                            self.log.info('queue jobs if conflicting job active feature is Validated successfully')
                        else:
                            raise Exception('Second backup job with id : {0} not completed'
                                            'successfully'.format(self.job_manager.job.job_id))
                    else:
                        raise Exception('First backup job with id : {0} not completed'
                                        'successfully'.format(self.job_manager.job.job_id))
                else:
                    raise Exception('Second backup job with id : {0} not queued'
                                    'successfully'.format(self.job_manager.job.job_id))
        finally:
            self.management.queue_jobs_if_conflicting_jobs_active = default_state

    def _backup_activity_switch(self, entity_object, switch):
        """
        Enables/disables backup activity at various levels

            Args:
                  entity_object     (obj)       --      Instance of the any level

                    values:
                        Commcell
                        Client
                        Agent
                        Subclient

                    switch          (bool)      --      True/False

            Returns:
                None
        """
        if isinstance(entity_object, (Client, Agent, Subclient)):
            activity_helper = activitycontrolhelper.ActivityControlHelper(self.test_object)
            self.log.info('{0} the backup activity on {1} level '.format(switch, entity_object))
            activity_helper.modify_activity(activity_type='backup',
                                            entity_object=entity_object,
                                            action=switch)
        elif isinstance(entity_object, Commcell):
            activity_controller = activitycontrol.ActivityControl(entity_object)
            self.log.info('{0} the data management activity on {1} level '.format(switch, entity_object))
            activity_controller.set(activity_type='DATA MANAGEMENT', action=switch)

    def _restore_activity_switch(self, entity_object, switch):
        """
        Enables/disables restore activity at various levels

            Args:
                  entity_object     (obj)       --      Instance of the any level

                    values:
                        Commcell
                        Client
                        Agent
                        Subclient

                    switch          (bool)      --      True/False

            Returns:
                None
        """
        if isinstance(entity_object, (Client, Agent)):
            activity_helper = activitycontrolhelper.ActivityControlHelper(self.test_object)
            self.log.info('{0} the restore activity on {1} level '.format(switch, entity_object))
            activity_helper.modify_activity(activity_type='restore',
                                            entity_object=entity_object,
                                            action=switch)
        elif isinstance(entity_object, Commcell):
            activity_controller = activitycontrol.ActivityControl(entity_object)
            self.log.info('{0} the restore activity on {1} level '.format(switch, entity_object))
            activity_controller.set(activity_type='DATA RECOVERY', action=switch)

    def validate_queue_job_if_activity_is_disable(self, entity_object, subclient_properties):
        """
        Validates queue job if activity is disable at various levels

            Args:

                entity_object       (obj)       --      Instance of the any level

                    values:
                        Commcell
                        Client
                        Agent
                        Subclient

                subclient_properties        (dict)      --      dict obtained from CVEntities.create()

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails
        Description of the feature:

            entity_object : commcell, client, agent, subclient
            Based on the entity object, backup and restore will be disabled correspondingly and
            feature will be validated.
        """
        self.log.info('Validating queue job if activity disabled feature at level {0}'.format(entity_object))
        default_setting = self.management.queue_jobs_if_activity_disabled
        try:
            self.management.queue_jobs_if_activity_disabled = True
            self.log.info('queue jobs if activity is disable {0}'.format(
                self.management.queue_jobs_if_activity_disabled))
            subclient_object = subclient_properties[0]['subclient']['object']
            self.test_object.subclient = subclient_object
            self._backup_activity_switch(entity_object, switch='Disable')
            backup_job_obj = self.common_utils.subclient_backup(subclient_object, "full", False)
            if backup_job_obj.status == 'Queued':
                self._backup_activity_switch(entity_object, switch='Enable')
                self.job_manager.job = backup_job_obj
                self.log.info('Delay reason of the job {0} is {1}'.format(self.job_manager.job.job_id,
                                                                          self.job_manager.job.delay_reason))
                backup_job_status = self.job_manager.wait_for_state(hardcheck=False, time_limit=30)
                if backup_job_status:
                    self.log.info('backup job with id : {0} is completed successfuly'.format(backup_job_obj.job_id))
                    if not isinstance(entity_object, Subclient):
                        self._restore_activity_switch(entity_object, switch='Disable')
                        restore_job_obj = self.common_utils.subclient_restore_in_place(
                            subclient_properties[0]['subclient']['content'],
                            subclient=subclient_object,
                            wait=False)
                        if restore_job_obj.status == 'Queued':
                            # -------------------------------- Add delay ------------------------------------------
                            self._restore_activity_switch(entity_object, switch='Enable')
                            self.job_manager.job = restore_job_obj
                            self.log.info('Delay reason of the job '
                                          '{0} is {1}'.format(self.job_manager.job.job_id,
                                                              self.job_manager.job.delay_reason))
                            restore_job_status = self.job_manager.wait_for_state(hardcheck=False, time_limit=10)
                            if restore_job_status:
                                self.log.info('restore job with id : {0} is completed successfuly'.format(
                                    restore_job_obj.job_id))
                            else:
                                raise Exception('Restore job with job id: {0} not completed successfully'.
                                                format(restore_job_obj.job_id))
                        else:
                            raise Exception(
                                'Restore job with job id: {0} not queued successfully'.format(restore_job_obj.job_id))
                else:

                    raise Exception('Backup job with id: {0} not completed successfully'
                                    .format(self.job_manager.job.job_id))
            else:
                raise Exception('backup job with id: {0} not queued successfully'.format(backup_job_obj.job_id))
            self.log.info('queue jobs if activity disabled is Validated at {0} level'.format(entity_object))
        except Exception as exp:
            if self.job_manager.job and self.job_manager.job.status not in ('Completed', 'Failed', 'Killed'):
                self.job_manager.modify_job('kill')
                self.log.info('Enabling the activities at level {0}'.format(entity_object))
            self._backup_activity_switch(entity_object, switch='Enable')
            self._restore_activity_switch(entity_object, switch='Enable')
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            self.management.queue_jobs_if_activity_disabled = default_setting

    def validate_queue_schedule_jobs(self, subclient_properties, action):
        """
        Validates queue schedule jobs

            Args:

                subclient_properties        (dict)     --       dict obtained from CVEntities.create()

                action                  (bool)      --       enable/disable of feature to be validated

            Returns:
                None

            Raises:
                Exception:
                    when validation of the feature fails.

        Description of the feature:
            validates whether the scheduled job is getting queued or not.
        """
        job_obj = None
        reason = 'The scheduled job is queued because the Queue Scheduled Jobs option is on'
        self.log.info('Validating queue schedule jobs feature at commcell level')
        default_state = self.management.queue_scheduled_jobs
        try:
            self.management.queue_scheduled_jobs = action
            self.log.info('queue schedule jobs is enabled {0}'.format(self.management.queue_scheduled_jobs))
            subclient_object = subclient_properties[0]['subclient']['object']
            job_obj = self._job_via_schedule(subclient_object=subclient_object)
            self.log.info('Backup with id : {0}'.format(job_obj.job_id))
            self.log.info('status of the job {0}'.format(job_obj.status))
            self.job_manager.job = job_obj
            if action:
                queue_status = self.job_manager.wait_for_state(expected_state='queued', hardcheck=False, time_limit=30)
                if queue_status:
                    self.log.info('scheduled job is successfully Queued')
                    self.job_manager.job = job_obj
                    if reason not in self.job_manager.job.delay_reason:
                        raise Exception("delay reason didn't match, obtained = {0}".format(
                            self.job_manager.job.delay_reason))
                    self.log.info('Validated job delay reason')
                    self.log.info('Delay reason of the job {0} is {1}'.format(self.job_manager.job.job_id,
                                                                              self.job_manager.job.delay_reason))
                    self.job_manager.modify_job('resume', hardcheck=False)
                    backup_status = self.job_manager.wait_for_state(hardcheck=False, time_limit=30)
                    if backup_status:
                        self.log.info('queue schedule jobs(Enable) is successfully Validated')
                    else:
                        raise Exception('Backup job with id: {0} not completed successfully'
                                        .format(self.job_manager.job.job_id))
                else:
                    raise Exception('backup job with id: {0} not queued successfully'.format(job_obj.job_id))
            else:
                complete_status = self.job_manager.wait_for_state(hardcheck=False, time_limit=30)
                if complete_status:
                    self.log.info('queue schedule jobs(Disable) is successfully Validated')
                else:
                    raise Exception('Backup job with id: {0} not completed successfully'
                                    .format(self.job_manager.job.job_id))
        except Exception as exp:
            if job_obj and job_obj.status not in ('Completed', 'Failed', 'Killed'):
                self.job_manager.modify_job('kill')
            self.log.error(exp)
            self.test_object.result_string = str(exp)
            self.test_object.status = FAILED
        finally:
            self.management.queue_scheduled_jobs = default_state

    def validate_job_max_restarts_change_prop(self):
        """
        To validate -->  when the restart setting of job gets changed for maxRestarts.
        eg . Keep restart attempts to say 10, and let 5 attempts fail. 
             Change restart attempt value to 3. 
             Job should fail after sixth attempt. 
        """
        try:
            self._entities_setup()
            self.log.info("Max restartability change when the job failed for couple of times.")
            initial_setting = self.management.get_restart_setting("File System and Indexing Based (Data Protection)")
            modified_setting = initial_setting.copy()
            modified_setting['restartable'] = True
            modified_setting['maxRestarts'] = 10
            modified_setting['restartIntervalInMinutes'] = 2
            modified_setting['killRunningJobWhenTotalRunningTimeExpires'] = False
            self.log.info("Modifying Job Manager Settings")
            self.management.modify_restart_settings([modified_setting])
            self._create_pre_scan_script(content='exit 1')
            self.log.info("Creating Subclient")
            subclient_properties = self.create_subclient()
            subclient_object = subclient_properties[0]['subclient']['object']
            self.log.info("Running full backup of subclient ")
            job = subclient_object.backup('full')
            self.log.info("Lets sleep for 5 mins and let the backup fail")
            time.sleep(300)
            self.log.info("Job {0} is getting paused".format(job.job_id))
            job.pause()
            _, rows = self._utility.exec_commserv_query("select count(*) from JMBkpAttemptInfo where "
                                              "jobid = {0} ".format(job.job_id))

            restarted = int(rows[0][0])
            if restarted:
                max_restart = restarted - 1
            else:
                raise Exception("Job not restarting")
            modified_setting['maxRestarts'] = max_restart
            self.management.modify_restart_settings([modified_setting])
            job.resume()

            time.sleep(60)
            _, rows = self._utility.exec_commserv_query("select count(*) from JMBkpAttemptInfo where "
                                              "jobid = {0} ".format(job.job_id))
            if int(rows[0][0]):
                raise Exception("Testcase failed Job restarted more than required no. of times")

            _, rows = self._utility.exec_commserv_query("select count(phase) from JMBkpAtmptStats where "
                                              "jobid = {0} and phase = {1} group by "
                                              "phase".format(job.job_id, 3))
            if int(rows[0][0]) > restarted + 1:
                raise Exception("Testcase failed Job restarted more than required no. of times")
            else:
                self.log.info("Passed")
        except Exception as excp:
            raise Exception(str(excp))

        finally:
            self.management.modify_restart_settings([initial_setting])
            self._entities.cleanup()

    def disable_restartability_test(self):
        """This function is to check whether the job can restart after the restartability is disabled.

        Args:
            subclient_properties  (dict)     --       dict obtained from CVEntities.create()
        Returns:
                None

        Raises:
             Exception:
                    when validation of the feature fails.
        """
        try:
            self._entities_setup()
            self.log.info("Max restartability change when the job failed for couple of times.")
            initial_setting = self.management.get_restart_setting("File System and Indexing Based (Data Protection)")
            modified_setting = initial_setting.copy()
            modified_setting['restartable'] = False # setting restartability to False
            self.log.info("Modifying Job Manager Settings")
            self.management.modify_restart_settings([modified_setting])
            self._create_pre_scan_script(content='exit 1')
            self.log.info("Creating Subclient")
            subclient_properties = self.create_subclient()
            subclient_object = subclient_properties[0]['subclient']['object']
            self.log.info("Running full backup of subclient ")
            job = subclient_object.backup('full')
            self.log.info("Lets sleep for some mins and let the backup fail")
            self.job_manager.job = job
            self.job_manager.wait_for_state(expected_state="failed")
            _, rows = self._utility.exec_commserv_query("select count(phase) from JMBkpAtmptStats where "
                                              "jobid = {0} and phase = {1} group by "
                                              "phase".format(job.job_id, 3))
            if int(rows[0][0]) > 1:
                raise Exception("Testcase failed Job restarted more than required no. of times")
            else:
                self.log.info("Passed")
        except Exception as excp:
            raise Exception(str(excp))
        finally:
            self.management.modify_restart_settings([initial_setting])
            self._entities.cleanup()

    def validate_disabled_client_jobs(self, subclient_properties):
        """Function to validate if job runs while client is disabled(Release-license).

        Args:
            subclient_properties (list): props of subclient that we had created.

        Raises:
            Exception: when job runs while client disabled.
        """
        subclient_obj = subclient_properties[0]['subclient']['object']
        self.client_machine_obj.client_object.release_license()
        self.log.info(f"Released license of client {self.client_machine_obj.client_object.client_name} successfully")
        job_successful = True
        exp = ""
        try:
            job = subclient_obj.backup('full')
        except Exception as excp:
            job_successful = False
            exp = str(excp)
        finally:
            self.client_machine_obj.client_object.reconfigure_client()
        if job_successful:
            job.kill(wait_for_job_to_kill=True)
            raise Exception("Job should not be running state while client is disabled!")
        self.log.info(str(exp))
        self.log.info("Job not running while client is disabled. As its expected behaviour")

    def client_Job_throttle(self, clientgroup=False):
        """function is used check the job throttling at client and client group level

        Args:
            clientgroup (bool, optional): True if we are using function for client group. Defaults to False.

        Raises:
            Exception: If job throttling is not followed
        """
        # self.management.enable_job_throttle_at_client_level = True
        # from SP36 Onwards, job throttle at client level is enabled by default at Commserv level.
        if not clientgroup:
            self.log.info("*"*50)
            self.client_machine_obj.client_object.update_properties({
                "clientProps": {
                    "jobThrottleSettings": {
                        "isJobThrottleEnabledAtCS": 1,
                        "isJobThrottleEnabled": 1,
                        "dataThreshold": 1,
                        "excludeImmidiateJobs": 0,
                        "logThreshold": 1
                    }
                }
            })
            self.log.info("Client level job throttling applied successfully")
        else:
            clientgroup_name = 'ClientGroup_' + datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S')
            client_gp = self.client_groups.add(
                clientgroup_name, [self.test_object.client.client_name])
            self.client_group = client_gp
            self.client_group.update_properties(
                {
                    "jobThrottleSettings":
                        {
                            "isJobThrottleEnabled": 1,
                            "dataThreshold": 1,
                            "excludeImmidiateJobs": 0,
                            "logThreshold": 1
                         }
                })
            self.log.info("Client group level job throttling applied successfully")
        self.log.info("#"*50)
        subclient_properties = self.create_subclient(no_subclients=3)
        subclient_objects = []
        for subclient_prop in subclient_properties:
            subclient_objects.append(subclient_prop['subclient']['object'])
        is_job_running = False
        jobs_not_queued = []
        for subclient_count in range(len(subclient_objects)):
            job = subclient_objects[subclient_count].backup('full')
            self.log.info("Job ID{0} is in {1} state".format(
                job.job_id, job.state))
            time.sleep(5)
            if subclient_count and (job.state != 'Queued' or "Maximum number of data jobs allowed to run has been reached for" not in job.delay_reason):
                self.log.info(
                    "Job id {0} is not in Queued state".format(job.job_id))
                is_job_running = True
                jobs_not_queued.append(job.job_id)
        if is_job_running:
            self.log.error('following jobs are in running state',jobs_not_queued)
            raise Exception("Job Throttling not followed.")

        self.job_manager.job = job
        self.job_manager.wait_for_state(expected_state="completed")
        if not clientgroup:
            self.client_machine_obj.client_object.update_properties({  # disable job throttling at client level
                "clientProps": {
                    "jobThrottleSettings": {
                        "isJobThrottleEnabledAtCS": 1,
                        "isJobThrottleEnabled": 0,
                        "dataThreshold": 1,
                        "excludeImmidiateJobs": 0,
                        "logThreshold": 1
                    }
                }
            })
        else:
            self.client_groups.delete(clientgroup_name)

    def job_suspend_interval(self):
        """To check the auto resume functionality of Job

        Raises:
            Exception: If job doesn't go into suspended state
            Exception: If job doesn't resume
        """
        subclient_properties = self.create_subclient()
        subclient_obj = subclient_properties[0]['subclient']['object']
        job = subclient_obj.backup('full')
        self.log.info(
            "Executing qcommand ---> qoperation jobcontrol -j {0} -o suspend -autoResumeInt 1".format(job.job_id))
        self.commcell.execute_qcommand(
            "qoperation jobcontrol -j {0} -o suspend -autoResumeInt 2".format(job.job_id))
        self.job_manager.job = job
        self.job_manager.wait_for_state(expected_state="suspended")
        if job.state != 'Suspended':
            self.log.error("job not suspended for given period of time")
            raise Exception("job not suspended for given period of time")
        time.sleep(120)
        time.sleep(20) # added 20 secs buffer time
        if job.state != 'Running':
            self.log.error(
                "Job should start running after given intervel of time")
            raise Exception(
                "Job should start running after given intervel of time")
        self.job_manager.wait_for_state(expected_state="completed")
        self.log.info("Job Finished!!")

    def job_priority(self):
        """
            This function checks the job_priority at client level
        """
        try:
            self.log.info( "Setting up all the required entities with storage policy with no. of stream = 1")
            self._entities_setup(streams=1)
            client_machine_obj2 = self.client_machine_obj
            self.log.info("Setting up Windows subclient")
            win_client = self.create_subclient()
            self.log.info(self.test_object._tcinputs['ClientName2'])
            client2 = self.commcell.clients.get(self.test_object._tcinputs['ClientName2'])
            self.client_machine_obj = Machine(client2.client_name, self.commcell)
            self.test_object.client = client2
            self.log.info("Setting up Linux subclient")
            linux_client = self.create_subclient()
            self.log.info("Setting up job priority of clients")
            # to set job priority
            self.set_job_priority(client_machine_obj2, self.client_machine_obj)
            ma_client_obj = self.commcell.clients.get(self._utility.get_ma())
            self.ma_service_name = "{0}({1})".format(MM_SERVICE_NAME,
                                                     ma_client_obj.instance)

            linux_job = linux_client[0]['subclient']['object'].backup()
            win_job = win_client[0]['subclient']['object'].backup()

            ma_client_obj.stop_service(self.ma_service_name)

            self.job_manager.job = linux_job
            self.job_manager.wait_for_state('waiting')
            self.job_manager.job = win_job
            self.job_manager.wait_for_state('waiting')

            ma_client_obj.start_service(self.ma_service_name)

            self.job_manager.wait_for_state('running')
            if linux_job.state in ['Waiting', 'Pending']:
                self.log.info("Windows client got Priority")
            else:
                self.log.error("Linux client got priority")
                raise Exception(
                    "Windows client's job should be given priority")
            self.job_manager.job = linux_job
            self.job_manager.wait_for_state(expected_state="completed")
        except Exception as exce:
            self.log.error(exce)
            raise Exception(exce)
        finally:
            self._entities.cleanup()

    def set_job_priority(self, win_client_obj, linux_client_obj, level='client'):
        """This function is used to set the job Priority at client level

        Args:
            win_client_obj (object): windows client object
            linux_client_obj (object): linux client object
        """
        self.management.job_priority_precedence = level
        win_client_obj.client_object.update_properties(
            {"clientProps": {"JobPriority": 1}})
        linux_client_obj.client_object.update_properties(
            {"clientProps": {"JobPriority": 2}})

    def validate_missing_files_failed_job(self):
        """
          This function checks if one file is missing after scan phase then backup job should fail. 
        """
        self.log.info('*'*50)
        # XML data for enabling the job status on error.
        xml_data_for_error_rules = self.get_xml_data_for_error_rules(commcell_id=self.commcell.commcell_id,
                                                        commserv_name=self.commcell.commserv_name)
        self.commcell._qoperation_execute(
            "{0}".format(xml_data_for_error_rules))
        # self.log.info(st)
        # self.log.info('*'*50)
        self.log.info("Starting a backup job for client {0}".format(
            self.client_machine_obj.machine_name))
        subclient_properties = self.create_subclient()
        job = subclient_properties[0]['subclient']['object'].backup()
        self.job_manager.job = job
        self.job_manager.wait_for_phase('backup')
        job.pause()
        self.client_machine_obj.remove_directory(
            subclient_properties[0]['subclient']['content'][0]+'\\dir3')
        job.resume()
        time.sleep(60)
        self.job_manager.wait_for_state(['failed', 'running'])
        if job.state == 'Failed':
            self.log.info(
                "Job {0} failed after deleting the file/folder after scan phase.".format(job.job_id))
        else:
            self.log.error(
                "Job {0} was running after the directory been deleted.".format(job.job_id))
            raise Exception(
                "Job {0} was running after the directory been deleted.".format(job.job_id))

        xml_data_for_error_rules = self.get_xml_data_for_error_rules(commcell_id=self.commcell.commcell_id,
                                                        commserv_name=self.commcell.commserv_name,enable_flag_ida=0)
        self.commcell._qoperation_execute(
            "{0}".format(xml_data_for_error_rules))

    def validate_blackout_window_jobs(self):
        """
            To validate the running job should be allowed to get completed and the new jobs should be kept at queued state. 
        """
        self.log.info("Allowing running jobs to complete at commcell level")
        op_helper = OpHelper(self.test_object,self.client_machine_obj.client_object) # for blackoutout
        self.management.modify_general_settings({"allowRunningJobsToCompletePastOperationWindow": True})
        subclient_properties = self.create_subclient(no_subclients=1,size=1000,level=4)
        subclient_properties2 = self.create_subclient(size=300,level=3)
        self.log.info("*"*50)
        self.log.info("First job was triggered from ")
        job1 = subclient_properties[0]['subclient']['object'].backup()
        time.sleep(30)
        blackout_window_obj = op_helper.add(
                                                name = "blackout"+ datetime.strftime(
                                                        datetime.now(), '%Y-%m-%d_%H-%M-%S'),
                                                start_date = datetime.strftime(
                                                               datetime.now(), '%d/%m/%Y'),
                                                end_date =  datetime.strftime(
                                                               datetime.now(), '%d/%m/%Y'),
                                                operations =  [
                                                            #    'NON_FULL_DATA_MANAGEMENT', 
                                                            #    'INFORMATION_MANAGEMENT',
                                                            #    'CLEANUP_OPERATION', 
                                                            #    'ONLINE_CONTENT_INDEXING', 
                                                               'FULL_DATA_MANAGEMENT'
                                                            #    'DELETE_ARCHIVED_DATA', 
                                                            #    'SHELF_MANAGEMENT', 
                                                            #    'DELETE_DATA_BY_BROWSING', 
                                                            #    'DATA_ANALYTICS', 
                                                            #    'BACKUP_COPY', 
                                                            #    'OFFLINE_CONTENT_INDEXING', 
                                                            #    'DATA_RECOVERY'
                                                               ],
                                                day_of_week = [
                                                                "MONDAY",
                                                                "TUESDAY",
                                                                "WEDNESDAY",
                                                                "THURSDAY",
                                                                "FRIDAY",
                                                                "SATURDAY",
                                                                "SUNDAY"
                                                               ],
                                                start_time =  datetime.strftime(
                                                               datetime.now(), '%H:%M'),
                                                end_time = datetime.strftime(
                                                               datetime.now()+timedelta(minutes = 10), '%H:%M')
                                                )
        time.sleep(60) # delay for blackout window to get registered
        job2 = subclient_properties2[0]['subclient']['object'].backup()
        time.sleep(60)
        try:
            if job1.state != 'Queued':
                self.log.info("*"*50)
                self.log.info("Job 1({0}) is in {1} state".format(job1.job_id,job1.state))
                self.log.info('Job {0} is in running state as it started before the blackout window'.format(job1.job_id))
            else:
                self.log.info("*"*50)
                self.log.info("Job 1({0}) is in {1} state".format(job1.job_id,job1.state))
                self.log.error("Job {0} should not be in Queued state.".format(job1.job_id))
                raise Exception("Job {0} should not be in Queued state.".format(job1.job_id))
            self.job_manager.job = job2
            self.job_manager.wait_for_state(['running','queued','completed'])
            if job2.state == 'Queued':
                self.log.info('Job {0} is in Queued state as it started during the blackout window'.format(job2.job_id))
            else:
                self.log.info("*"*50)
                self.log.info("Job 2({0}) is in {1} state".format(job2.job_id,job2.state))
                self.log.error("Job {0} should be in Queued state.".format(job2.job_id))
                raise Exception("Job {0} should be in Queued state.".format(job2.job_id))
            time.sleep(5*60)
        except Exception as excep:
            self.log.error(excep)
            raise Exception(excep)
        finally:
            self.job_manager.job = job2
            self.job_manager.wait_for_state(['failed','complete'])
            op_helper.delete(name=blackout_window_obj.name)
            self.management.modify_general_settings({"allowRunningJobsToCompletePastOperationWindow": False})

    def validate_queue_job_clientgroup_resume_after_failed(self):
        """Validates if job is resumed after first job is failed when queue job is enabled at client group"""
        clientgroup_name = 'ClientGroup_' + datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        client_gp = self.client_groups.add(clientgroup_name, [self.test_object.client.client_name])
        self.client_group = client_gp
        self.client_group.update_properties({"queueConflictingJobsEnabledForCG": True})
        self._create_pre_scan_script(content='exit 1')
        subclient_properties = self.create_subclient()
        subclient_obj = subclient_properties[0]['subclient']['object']
        self.log.info("Running Full backup Job 1")
        job_object1 = self.common_utils.subclient_backup(subclient_obj, "full", False)
        self.job_manager.job = job_object1
        self.log.info("Job should be in pending state pre-scan_script has exit 1")
        self.job_manager.wait_for_state(expected_state='pending', time_limit=2)
        self.log.info("Running Full backup Job 2 on same subclient")
        job_object2 = self.common_utils.subclient_backup(subclient_obj, "full", False)
        self.job_manager.job = job_object2
        self.job_manager.wait_for_state(expected_state='queued', time_limit=2)
        if job_object2.status != "Queued":
            self.log.error("Job not in queued state")
            job_object2.kill(wait_for_job_to_kill=True)
            raise Exception("Job 2 not queued")
        self.client_machine_obj.delete_file(self.pre_scan_script)
        self.log.info("creating pre scan command file {0} with exit 0".format(self.pre_scan_script))
        self.client_machine_obj.create_file(self.pre_scan_script, "exit 0")
        if self.client_machine_obj.os_info.lower() == "unix":
            self.client_machine_obj.change_file_permissions(self.pre_scan_script, '777')
        self.job_manager.job = job_object1
        self.job_manager.wait_for_state(expected_state=['completed'])
        self.job_manager.job = job_object2
        self.job_manager.wait_for_state(expected_state="running", time_limit=2)
        if job_object2.status == "Running":
            self.job_manager.job = job_object2
            self.job_manager.wait_for_state(expected_state="completed")
        else:
            raise Exception("Job 2 not running")
        self.client_groups.delete(clientgroup_name)
    def get_xml_data_for_error_rules(self,commcell_id,commserv_name,
                        enable_flag_ida=1,app_group_name="APPGRP_WindowsFileSystemIDA"):
        
        xml_data_rules = """
        <?xml version="1.0" encoding="UTF-8"?>
        <App_SetJobErrorDecision>
            <entity _type_="1" commCellId="{commcell_id}" commCellName="{commserv_name}" />
            <jobErrorRuleList>
            <idaRuleList isEnabled="{enable_flag_ida}">
            <ida _type_="78" appGroupId="57" appGroupName="{app_group_name}" />
            <ruleList>
                <ruleList blockedFileTypes="0" isEnabled="1" jobDecision="2" pattern="*" skipTLbackups="0" skipofflineDBs="0" skippedFiles="0">
                <errorCode allErrorCodes="1" fromValue="1" skipReportingError="0" toValue="1" />
                <srcEntity _type_="1" commCellId="2" />
                </ruleList>
                <thresholdList applyRuleOn="0" count="1" isCountEnabled="1" isEnabled="1" isPercentageEnabled="1" jobDecision="2" percentage="1">
                <srcEntity _type_="1" clientSidePackage="1" commCellId="2" consumeLicense="1" srmReportSet="0" srmReportType="0" type="0" />
                </thresholdList>
            </ruleList>
            <osEntity _type_="161" />
            </idaRuleList>
            </jobErrorRuleList>
        </App_SetJobErrorDecision>"""

        xml_data_rules = xml_data_rules.format(
                        commcell_id=commcell_id,
                        commserv_name=commserv_name,
                        enable_flag_ida=enable_flag_ida,
                        app_group_name=app_group_name
                        )
        
        xml_data_for_error_rules = ''.join(
                    i.lstrip().rstrip() for i in xml_data_rules.split("\n"))
        
        return xml_data_for_error_rules
