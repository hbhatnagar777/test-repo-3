# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""File for performing common operations required to verify RPO driven backup

RpoHelper and RPOBasedSubclient are 2 classes defined in this file.

RpoHelper: Class for providing common functions to validate RPO driven backup

RPOBasedSubclient: Class for maintaining common Job attributes and methods for RPO driven
                   subclients

RpoHelper:
    __init__()                    --  Initialize instance of the RpoHelper class by
            creating necessary entities for subclient creation

    create_pre_scan_script()      --  creates pre scan script required by subclient
            pre/post processing

    stop_ma_services()            --  stops media agent service on current media agent client

    start_ma_services()           --  starts media agent service on current media agent client

    collect_job_rpo_details()     --  collect Job details like strike count and Estimated run time

    validate_rpo_schedule()       --  validates the resource priority order

    validate_rsc_alloc_order()    -- creates necessary setup and validates RPO based Job priority

RPOBasedSubclient:
    __init__()                    --  Initialize instance of the RPOBasedSubclient class by
            creating subclient

    force_strike_count()          --  achieves the desired strike count for subclient by
            forcing the Job to fail

    force_estimated_runtime()     --  achieves the desired forecast for the subclient by running
            backup jobs

    cleanup()                     --  perform the necessary cleanup operations for
            RPOBasedSubclient
"""
import re
import time

from cvpysdk.job import Job

from AutomationUtils import logger
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.options_selector import OptionsSelector
from Server.JobManager.jobmanagement_helper import JobManagementHelper

from AutomationUtils.constants import UNIX_TMP_DIR
from AutomationUtils.constants import WINDOWS_TMP_DIR

from .rpo_constants import JOBMANGER_PROCESS_NAME
from .rpo_constants import MM_SERVICE_NAME
from .rpo_constants import JM_SERIVICE_NAME
from .rpo_constants import ESTIMATED_TIME_THRESHOLD
from .rpo_constants import RPO_ADDITIONAL_SETTING_KEY


class RpoHelper:
    """Class for performing all common functions related to JM RPO feature"""
    def __init__(self, commcell, commcell_client,
                 media_agent, storage_policy=None):
        """Initialize instance of the RpoHelper class by creating necessary entities
           for subclient creation

            Args:
                commcell             (str)     -- Instance of commcell class

                commcell_client      (str)     -- client where subclients to be created

                media_agent          (str)     -- media agent name

                storage_policy      (object)  --  name of the storage policy to be used

            Returns:
                object - instance of the RpoHelper class
        """
        self.log = logger.get_log()
        self.utils = OptionsSelector(commcell)
        self.entities = CVEntities(commcell)
        self.job_manager = JobManager(commcell=commcell)
        self.client_machine_obj = Machine(commcell_client, commcell)
        self.commserv_machine_obj = Machine(commcell.commserv_client)
        self.serverbase = CommonUtils(commcell)
        self.ma_client_obj = commcell.clients.get(media_agent)
        self.ma_service_name = "{0}({1})".format(MM_SERVICE_NAME,
                                                 self.ma_client_obj.instance)
        self.jm_logfile = self.commserv_machine_obj.join_path(
            commcell.commserv_client.log_directory, JOBMANGER_PROCESS_NAME+'.log')

        if 'unix' in self.ma_client_obj.os_info.lower():
            # we cannot stop only ma service on linux media agent like in windows. Hence
            # we don't know yet how to force the Job to waiting state
            raise Exception("linux Media agent is currently not supported")

        if storage_policy is None:
            # if storage policy is not passed, let's auto create necessary entities to create
            # subclients
            storage_policy = "autorpostoragepolicy_" + media_agent
            disk_lib = "autorpodisklibrary_" + media_agent
            self.log.info("auto initializing entities required for subclient creation")

            if storage_policy not in commcell.storage_policies.all_storage_policies:
                # if default auto storage policy is not present. let's create
                disklibrary_inputs = {
                    'disklibrary': {
                        'name': disk_lib,
                        'mediaagent': media_agent,
                        'mount_path': self.entities.get_mount_path(media_agent),
                        'username': '',
                        'password': '',
                        'cleanup_mount_path': True,
                        'force': False,
                    }
                }
                self.log.info("auto Creating disk library {0} using media agent {1}".format(
                    disk_lib, media_agent))
                self.entities.create(disklibrary_inputs)
                self.log.info("disk library {0} created successfully".format(disk_lib))
    
                # create storage policy
                storagepolicy_inputs = {
                    'target':
                        {
                            'library': disk_lib,
                            'mediaagent': media_agent,
                            'force': False
                        },
                    'storagepolicy':
                        {
                            'name': storage_policy,
                            'dedup_path': None,
                            'incremental_sp': None,
                            'retention_period': 7,
                            'number_of_streams': 1
                        },
                }
                self.log.info("Creating storage policy {0} using library {1}".format(
                    storage_policy, disk_lib))
                self.entities.create(storagepolicy_inputs)
                self.log.info("storage policy {0} created successfully".format(storage_policy))
            else:
                # we will try to reuse storage policy if test was already run with
                # same media agent
                self.log.info("auto storage policy {0} is already present".format(storage_policy))
        else:
            # if user passed storage policy is not present. let's bail out
            if storage_policy.lower() not in commcell.storage_policies.all_storage_policies:
                raise Exception("storage policy {0} doesn't exist in commcell".format(
                    storage_policy))

        commcell.add_additional_setting('CommServe', RPO_ADDITIONAL_SETTING_KEY,
                                        'INTEGER', '1')
        self.storage_policy = storage_policy
        self.commcell_client = commcell_client
        self.commcell = commcell
        self.media_agent = media_agent

    def verify_rpo_is_enabled(self):
        """verifies if RPO feature is enabled by parsing JM log

        Args:

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to find the expected string in log message

            Sample output:
            15144 18a8  11/02 14:58:40 ### Service    bEnableDynamicPriorityForJobs reg /
            key is set to [1]
        """
        pattern = "bEnableDynamicPriorityForJobs reg key is set to \[(\d+)\]"
        self.jm_serive_name = "{0}({1})".format(JM_SERIVICE_NAME,
                                                self.commcell.commserv_client.instance)

        # enable Job Manager debug level
        self.commserv_machine_obj.set_logging_debug_level(JOBMANGER_PROCESS_NAME)

        self.log.info("trying to restart JM service {0}".format(self.jm_serive_name))
        self.commcell.commserv_client.restart_service(self.jm_serive_name)

        time.sleep(10)  # allow some time to log
        log_file_content = self.commserv_machine_obj.read_file(self.jm_logfile)

        # disable debug log for JM
        self.commserv_machine_obj.set_logging_debug_level(JOBMANGER_PROCESS_NAME, '0')

        match = re.findall(pattern, log_file_content)
        if match is not None and match != []:
            self.log.info("pattern details found {0}".format(match))
            rpo_state = match[-1]  # lets take the last match to get the latest state
        else:
            raise Exception("expected pattern {0} not found in log file {1}."
                            "Please check JM logs".format(pattern, self.jm_logfile))
        return int(rpo_state)

    def create_pre_scan_script(self, pre_scan_script, content=''):
        """creates pre scan script required by subclient pre/post processing
           with content passed.

        Args:
            pre_scan_script   (str)   --  path of file to be created

            content           (str)   --  content that is to be written to file

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create file

        """
        if self.client_machine_obj.check_file_exists(pre_scan_script):
            self.log.info("deleting existing pre scan script {0}".format(pre_scan_script))
            self.client_machine_obj.delete_file(pre_scan_script)
        self.log.info("creating pre scan command file {0}".format(pre_scan_script))
        self.client_machine_obj.create_file(pre_scan_script, content)

        if self.client_machine_obj.os_info.lower() == "unix":
            self.client_machine_obj.change_file_permissions(pre_scan_script, '777')

    def stop_ma_services(self):
        """stops media agent service on current media agent client

        Args:

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to stop media agent service

        """
        self.log.info("stopping service {0} on ma {1}".format(self.ma_service_name,
                                                              self.media_agent))
        self.ma_client_obj.stop_service(self.ma_service_name)

    def start_ma_services(self):
        """starts media agent service on current media agent client

        Args:

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to start media agent service

        """
        self.log.info("starting service {0} on ma {1}".format(self.ma_service_name,
                                                              self.media_agent))
        self.ma_client_obj.start_service(self.ma_service_name)

    def collect_job_rpo_details(self, rpo_scobj):
        """runs SQL query and get details such as strike count,
           estimated run time for given instance of RPOBasedSubclient class

        Args:
            rpo_scobj    (obj)   --  Instance of RPOBasedSubclient class

        Returns:
            None

        Raises:
            Exception:
                if SQL SP fails to run
        """
        sql_command = ("SET NOCOUNT ON exec JMGetDynamicPriorityConfig"
                       " @subClientID={0},@bkpLevel=1,@opType=4".format(
                        rpo_scobj.subclient_obj.subclient_id))
        response = self.utils.update_commserve_db(sql_command)
        if not response.rows:
            self.log.error("unable to run SP to get RPO details for given subclient")
            raise Exception("unable to run SP to get RPO details for given subclient")

        (_, _, rpo_scobj.strikecount, rpo_scobj.estimated_job_time) = map(int, response.rows[0])
        self.log.info("RPO details, subclient id:%s, strikecount:%s, ECT:%s" %
                      (rpo_scobj.subclient_obj.subclient_id,
                       rpo_scobj.strikecount,
                       rpo_scobj.estimated_job_time))

    def validate_rpo_schedule(self, sc_details):
        """validates the resource allocation order based on strikecount and estimated completion
           time.

        Args:
            sc_details    (list)   --  list of subclient details

        Returns:
            None

        Raises:
            Exception:
                if resource allocation for the Jobs are not as expected
                if strike count and estimated Job completion time are same
        """
        sc_details_sorted = sc_details[:]
        is_strikecount_same = all([True if x[2] == sc_details[0][2] else False
                                   for x in sc_details])
        is_ect_same = all([True if x[3] == sc_details[0][3] else False for x in sc_details])
        if not is_strikecount_same:
            self.log.info("Strike count is expected to be honoured")
            sc_details_sorted.sort(key=lambda x: x[2], reverse=True)
        elif not is_ect_same:
            self.log.info("estimated Job completion is expected to be honoured")
            sc_details_sorted.sort(key=lambda x: x[3], reverse=True)
        else:
            raise Exception("strike count and estimated completion time, both are equal."
                            "Static priority validation is not yet supported")

        self.log.debug("Expected resource order {0}".format(sc_details_sorted))
        result = all([True if x[0] == y[0] else False for x,y in
                      zip(sc_details, sc_details_sorted)])
        if result:
            self.log.info("RPO scheduling validated successfully")
        else:
            raise Exception("RPO scheduling verification failed"
                            "expected order {0} current order {1}".format(sc_details_sorted,
                                                                          sc_details))

    def validate_rsc_alloc_order(self, rpo_subclients):
        """ creates necessary setup and validates resource priority order
        It does following steps:
            1. stops media agent services on media agent client
            2. creates backup Job for each RPO subclient object and wait for it go
               to waiting state(reason: resource not available)
            3. set Job Manager debug log level to 5
            4. starts media agent services on media agent client
            5. for each Job, it will wait for Job to complete or running state and
               collect necessary information such as strike count and
               estimated Job completion time from JM log file
            6. It verifies the order of resource allocation for the given subclients
               based on strike count and estimated Job completion time
            7. reset Job Manager debug log level to 1

        Args:
            rpo_subclients    (list)   --  list of subclient names to be used to create subclients

        Returns:
            None

        Raises:
            Exception:
                if any error occurs in the validation

        """
        subclients_details = []

        # bring down MA service so that backup Jobs for all subclients goes to waiting state
        self.stop_ma_services()

        # let us give some time for communication to MA breaks down
        time.sleep(60)

        for rpo_subclient in rpo_subclients:

            self.create_pre_scan_script(rpo_subclient.pre_scan_script, content='exit 0')
            self.log.info("triggering backup Job for subclient {0}".format(
                rpo_subclient.subclient_name))
            rpo_subclient.backup_job_obj = self.serverbase.subclient_backup(
                                            rpo_subclient.subclient_obj,
                                            "full",
                                            wait=False)
            self.job_manager.job = rpo_subclient.backup_job_obj
            self.log.info("waiting for job {0} for subclient {1} go to waiting state".format(
                self.job_manager.job.job_id, rpo_subclient.subclient_name))
            self.job_manager.wait_for_state(expected_state='waiting',
                                            fetch_job_state_in_validate=False)
            self.log.info("backup Job ID {0} for subclient {1} is waiting for"
                          " resource as expected".format(rpo_subclient.backup_job_obj.job_id,
                                                         rpo_subclient.subclient_name))

        self.start_ma_services()

        for rpo_subclient in rpo_subclients:
            self.job_manager.job = rpo_subclient.backup_job_obj
            self.log.info("waiting for job {0} for subclient {1} go to "
                          "running/completed state".format(self.job_manager.job.job_id,
                                                           rpo_subclient.subclient_name))
            self.job_manager.wait_for_state(expected_state=['completed'],
                                            fetch_job_state_in_validate=False)
            self.log.info("backup Job ID {0} for subclient {1} went to running/completed"
                          " state as expected".format(rpo_subclient.backup_job_obj.job_id,
                                                      rpo_subclient.subclient_name))

            # now create Job instance of the current Job to get the job end time
            job_obj = Job(self.commcell, rpo_subclient.backup_job_obj.job_id)

            subclients_details.append([rpo_subclient.subclient_name,
                                       job_obj.end_time,
                                       rpo_subclient.strikecount,
                                       rpo_subclient.estimated_job_time])

        self.log.debug("all subclient details collected {0}".format(subclients_details))

        # now sort the subclient based on job end time
        subclients_details.sort(key=lambda x: x[1])
        self.log.debug("subclient details after sorting based on Job end time {0}".format(
            subclients_details))

        # now verify if resource allocation is fairly scheduled as per the expectation
        self.validate_rpo_schedule(subclients_details)


class RPOBasedSubclient:
    """Class for common RPO related operations performed on subclient"""
    def __init__(self, rpo_helper_obj, subclient_name, use_existing_subclient = False):
        """Initialize instance of the RPOBasedSubclient class by creating subclient

            Args:
                rpo_helper_obj     (obj) -- Instance of RpoHelper class

                subclient_name     (str) -- name of the subclient to be created

                use_existing_subclient
                                   (bool)-- If True subclient should exist and only
                                                subclient instance is created
                                            If False, Subclient is created in the test


            Returns:
                object - instance of the RPOBasedSubclient class
        """

        self.log = logger.get_log()
        self.subclient_name = subclient_name
        self.strikecount = None
        self.backup_job_obj = None
        self.rsc_alloca_timestamp = None
        self.rpo_helper_obj = rpo_helper_obj
        self.estimated_job_time = None

        if rpo_helper_obj.client_machine_obj.os_info.lower() == 'windows':
            self.pre_scan_script = rpo_helper_obj.client_machine_obj.join_path(
                                        WINDOWS_TMP_DIR,
                                        self.subclient_name + ".bat")
        else:
            self.pre_scan_script = rpo_helper_obj.client_machine_obj.join_path(
                                        UNIX_TMP_DIR,
                                        self.subclient_name + ".sh")

        subclient_inputs = {
            'target':
                {
                    'client': rpo_helper_obj.commcell_client,
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': rpo_helper_obj.storage_policy,
                    'backupset': "defaultBackupSet",
                    'force': True
                },
            'subclient':
                {
                    'name': self.subclient_name,
                    'client_name': rpo_helper_obj.commcell_client,
                    'data_path': None,
                    'description': "Automation - RPO driven backup",
                    'subclient_type': None,
                    'pre_scan_cmd': self.pre_scan_script
                }
        }
        # by default create pre scan script with return successful
        rpo_helper_obj.create_pre_scan_script(self.pre_scan_script, content='exit 0')

        if use_existing_subclient:
            idata_agent = rpo_helper_obj.client_machine_obj.client_object.agents.get("File System")
            self.log.debug("using File System as default idata agent")
            instance = idata_agent.instances.get("defaultinstancename")
            backup_set = instance.backupsets.get('defaultBackupSet')
            self.log.debug("using defaultBackupSet as instance")
            self.log.info("Checking if the given subclient is valid or not")
            if not subclient_name in backup_set.subclients.all_subclients:
                self.log.error("Invalid subclient {0}".format(subclient_name))
                raise Exception("The given subclient {0} is not a valid subclient.".format(subclient_name))
            self.subclient_props = backup_set.subclients.get(subclient_name)
            self.log.info("subclient {0} Instance is created".format(subclient_name))
            self.subclient_obj = self.subclient_props
        else:
            self.log.info("creating subclient {0}".format(self.subclient_name))
            self.subclient_props = rpo_helper_obj.entities.create(subclient_inputs)
            self.subclient_obj = self.subclient_props['subclient']['object']
            self.log.info("subclient {0} is created successfully".format(subclient_name))

    def force_strike_count(self, strike_count=1):
        """achieves the desired strike count for subclient by forcing the Job to fail

        Args:
            strike_count    (int)   --  strike count to be achieved

        Returns:
            None

        Raises:
            Exception:
                if any error occurs in creating pre scan script or running backup Jobs
        """
        job_type = "File System and Indexing Based (Data Protection)"

        job_management = JobManagementHelper(self.rpo_helper_obj.commcell)
        current_setting = job_management.get_restart_setting(job_type)

        default_settings = current_setting.copy()

        current_setting['restartable'] = False
        self.log.info("disabling restart flag for File system backup jobs to achieve "
                      "strike count")
        job_management.modify_restart_settings([current_setting])

        try:
            self.rpo_helper_obj.create_pre_scan_script(self.pre_scan_script, content='exit 1')
            for count in range(strike_count):
                self.log.info("Going to trigger backup job on Subclient:{0} for "
                              "strike count:{1}".format(self.subclient_name, count))
                job = self.rpo_helper_obj.serverbase.subclient_backup(
                                                        self.subclient_obj,
                                                        "full",
                                                        wait=False)
                self.rpo_helper_obj.job_manager.job = job
                self.rpo_helper_obj.job_manager.wait_for_state(expected_state='failed')
                self.log.info("backup Job ID {0} for subclient {1} failed as expected".format(
                    job.job_id, self.subclient_name))

            # let's verify if strike count is reflecting in the DB
            self.rpo_helper_obj.collect_job_rpo_details(self)
            if int(self.strikecount) != strike_count:
                raise Exception("Expected strike count not set in the DB"
                                "SC in DB:%s, expected:%s" %(self.strikecount, strike_count))
        except Exception as exp:
            self.log.error(exp)
        finally:
            self.log.info('Applying default settings as follows {0}'.format(default_settings))
            job_management.modify_restart_settings([default_settings])

    def force_estimated_runtime(self, num_backups, file_size):
        """achieves the desired estimated Job run time by backing up the data for n number of
        times

        Args:
            num_backups    (int)   --  number of backups to be run to compute estimated Job
                                       run time

            file_size      (int)   --  file size in bytes. higher file size greater the estimated
                                       Job run time

        Returns:
            None

        Raises:
            Exception:
                if any error occurs in achieving estimated Job run time
        """
        if num_backups < ESTIMATED_TIME_THRESHOLD:
            raise Exception("number of backup {0} is less than minimum threshold {1} to compute"
                            "estimated time ".format(num_backups, ESTIMATED_TIME_THRESHOLD))

        self.log.info("number of backups to be run %s" % num_backups)

        test_file_path = self.rpo_helper_obj.client_machine_obj.join_path(
                                                                    self.subclient_obj.content[0],
                                                                    "test_file")

        # subclient backups are failing because of some intermittent issue in job state verification in automation.
        # so we will retry in case of any exception during backup Job as it is time consuming operation to hit ECT
        attempt = 0
        for count in range(num_backups+1):
            self.log.info("running subclient backup count %s" % count)
            self.rpo_helper_obj.client_machine_obj.create_file(test_file_path,
                                                               content='',
                                                               file_size=file_size)
            try:
                self.rpo_helper_obj.job_manager.job = self.rpo_helper_obj.serverbase.subclient_backup(
                                                                                        self.subclient_obj,
                                                                                        "full",
                                                                                        wait=False)
                self.rpo_helper_obj.job_manager.wait_for_state(expected_state='completed',
                                                               fetch_job_state_in_validate=False)
            except Exception as e:
                self.log.error("subclient backup job failed with exception %s" % e)
                if attempt < 3:
                    self.log.info("retrying subclient backup")
                    attempt += 1
                else:
                    raise Exception(e)

        self.rpo_helper_obj.commserv_machine_obj.set_logging_debug_level("EvMgrs", "10")

        # estimated runtime is calculated lazily based on Arima Param_4_1_ComputeTime param.
        # in order to run it immediately we should run below query and then backup Job
        query = ("SELECT 1 FROM App_subclientprop WHERE componentNameId = {0} and " 
                 "attrname = 'Arima Param_4_1_ComputeTime' and modified=0".format(self.subclient_obj.subclient_id))
        response, result_set = self.rpo_helper_obj.utils.exec_commserv_query(query)
        self.log.info("response:{0}, result:{1}".format(response, result_set))
        if response[0]:
            sql_command = ("update APP_SubClientProp set attrval=dbo.GetUnixTime(getutcdate()) "
                           "where componentNameId = {0} and "
                           "attrname = 'Arima Param_4_1_ComputeTime'".format(
                            self.subclient_obj.subclient_id))
        else:
            sql_command = ("insert into App_subclientprop(componentNameId, attrname,  attrtype, "
                           "attrval, created, modified) "
                           "values({0},'Arima Param_4_1_ComputeTime',10 ,"
                           "dbo.GetUnixTime(getutcdate()),dbo.GetUnixTime(getutcdate()),0)".format(
                            self.subclient_obj.subclient_id))

        self.log.info("running SP '%s' to to set ECT compute time" % sql_command)
        self.rpo_helper_obj.utils.update_commserve_db(sql_command)

        sql_command = ("update APP_SubClientProp set created=created-(3600*24) "
                       "where attrName in ('Estimated Run Time_4_1','Anomalous Run Time_4_1') "
                       "and componentNameId={0}".format(self.subclient_obj.subclient_id))

        self.log.info("running SP '%s' to to set ECT run time" % sql_command)
        self.rpo_helper_obj.utils.update_commserve_db(sql_command)

        self.rpo_helper_obj.client_machine_obj.create_file(test_file_path,
                                                           content='',
                                                           file_size=file_size)
        job = self.rpo_helper_obj.serverbase.subclient_backup(self.subclient_obj, "full", wait=False)

        # We see that by the time forecast thread is invoked backup Job is completed and forecasting is not done.
        # So we will suspend the Job for 10 mins so that forecast thread is invoked and executed
        iteration = 0
        max_attempt = 12
        while iteration <= max_attempt:
            job.pause()
            if job.status.lower() in ["suspended"]:
                break
            else:
                self.log.info("job is not suspended even after job.pause().."
                              "retry %s in 5 seconds" % (iteration+1))
            iteration += 1
            time.sleep(5)
        if max_attempt > 12:
            raise Exception("We couldn't suspend backup Job %s" % job.job_id)

        self.log.info("waiting for 40 minutes so that forecast thread is invoked")
        time.sleep(40*60)

        job.resume()
        self.log.info("waiting for job to complete after job resume")
        job.wait_for_completion()

        self.rpo_helper_obj.client_machine_obj.create_file(test_file_path,
                                                           content='',
                                                           file_size=file_size)

        self.rpo_helper_obj.commserv_machine_obj.set_logging_debug_level("EvMgrs", "0")

        # let's verify if strike count is reflecting in the DB
        self.rpo_helper_obj.collect_job_rpo_details(self)
        if not int(self.estimated_job_time):
            raise Exception("Estimated run time value is not caluculated."
                            "ECT in DB:%s" % self.estimated_job_time)

    def cleanup(self):
        """perform the necessary cleanup operations

        Args:

        Returns:
            None

        Raises:
            Exception:
                if any cleanup operation fails

        """
        self.log.info("executing cleanup for subclient {0}".format(self.subclient_name))
        self.rpo_helper_obj.entities.delete(self.subclient_props)
        self.rpo_helper_obj.client_machine_obj.delete_file(self.pre_scan_script)
