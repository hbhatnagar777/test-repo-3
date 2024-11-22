# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
CommonUtils:   Provides test common commcell related operations.

CommonUtils:

    __init__()                  -- initialize instance of CommonUtils class

    __repr__()                  --  Representation string for the instance of the
                                    CommonUtils class for specific test case

    get_backup_copy_job_id()    -- Method to fetch backup copy job ID given the snap job ID for
                                   snap subclient

    backup_validation()         -- Method to validate backup jobs with application size
                                   and data size

    check_client_readiness()    -- performs check readiness on the list of clients

    get_subclient()             -- Gets default subclient object for a given commcell
                                    client, agent, backupset.

    get_backupset()             -- Gets default backupset object for a given commcell
                                    client, agent.

    restart_services()          -- restarts services on the list of clients

    subclient_backup()          -- Executes backup on any subclient object and waits for job
                                    completion.

    subclient_restore_in_place()
                                -- Restores the files/folders specified in the input paths list
                                    to the same location.

    subclient_restore_out_of_place()
                                -- Restores the files/folders specified in the input paths list
                                    to the input client, at the specified destination location.

    subclient_backup_and_restore()
                                -- Executes backup on a subclient, and restores data out of place

    subclient_restore_from_job()
                                -- Initiates restore for data backed up in a given job
                                    and performs the applicable verifications.

    osc_backup_and_restore()    -- Validates backup works fine from osc schedule for incremental
                                     backup for devices and out of place restore works.

    aux_copy()                  -- Executes aux copy on a specific storage policy copy and waits
                                    for job completion.

    data_aging()                -- Executes data aging for a specific storage policy copy and
                                    waits for job completion.

    compare_file_metadata()     -- Compares the meta data of source path with destination path
                                    and checks if they are same.

    cleanup_jobs()              -- Kills all the jobs in the job list self.job_list,
                                    if the jobs are not completed already.

    cleanup_dir()               -- Removes directories in the temp directories list

    cleanup()                   -- ida cleanup tasks

    modify_additional_settings()-- Updates Additional settings key/value for a given client

    get_synthetic_full_job()    -- Method to fetch synthetic full  job ID given the subclient object
                                        and backup type

    delete_additional_settings()-- Deletes Additional settings key/value for a given client

    download_software()         -- Executes Download software job and waits for job completion

    data_verification()         -- Runs a Data verification job and waits for job completion

    kill_active_jobs()          -- Method to kill the active jobs running for the client

"""
import inspect
from datetime import datetime
import ntpath
import time

from cvpysdk.client import Client
from cvpysdk.commcell import Commcell
from cvpysdk.subclient import Subclient
from cvpysdk.backupset import Backupset
from cvpysdk.policies.storage_policies import StoragePolicy
from cvpysdk.job import JobController, Job

from AutomationUtils import constants
from AutomationUtils import logger
from AutomationUtils import database_helper
from AutomationUtils.options_selector import OptionsSelector

from Server.JobManager.jobmanager_helper import JobManager


class CommonUtils(object):
    """Class to perform common commcell operations."""

    def __init__(self, init_object):
        ''' Initialize instance of CommonUtils class

        Args:
        init_object : Should be either the commcell or the testcase object'''

        # Pre-initialized attributes applicable for all instances of the class
        self._init_object = init_object
        if isinstance(init_object, Commcell):
            self._testcase = None
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        self.log = logger.get_log()
        self.job_list = []
        self._utility = OptionsSelector(self._commcell)
        self.job_manager = JobManager(commcell=self._commcell)
        self.job_controller = JobController(self._commcell)
        self.temp_directory_list = []

    def __repr__(self):
        """Representation string for the instance of the CommonUtils class."""
        return "CommonUtils class instance"

    def get_backup_copy_job_id(self, snap_job_id):
        """Method to fetch inline backup copy job ID given the snap job ID for s nsap subclient

            Args:
                snap_job_id         (str)       --  snap backup job ID

            Returns:
                str                         -   returns string of backup copy job ID
        """

        log_message = "Snap Job ID : {0}".format(snap_job_id)
        self.log.info(log_message)
        backup_copy_job_id = None
        query = """SELECT childJobId FROM JMJobWF WHERE processedJobId = {0}""".format(
            int(snap_job_id))
        csdb = database_helper.get_csdb()
        csdb.execute(query)
        job_list = csdb.fetch_one_row()
        backup_copy_job_id = job_list[0]
        return backup_copy_job_id

    def get_synthetic_full_job(self, subclient, backup_type):
        """
        This gets the synthetic full job if after incr or before incr
        Args:

            subclient           (object) - subclient object of SDK
            backup_type         (string) - type of synthetic full job
                                                AFTER_SYNTH - if synthetic full is
                                                                triggereged after Incremental
                                                BEFORE_SYNTH - if synthetic full is
                                                                triggereged Before Incremental


        Returns:
            job - job object of synthetic full/incremental that triggered after synthetic full

        Raises:
            Exception:
                if  failed to fetch synthetic full job id

        """

        if backup_type == "AFTER_SYNTH":
            backup_type_latest_running = "Incremental"
            backup_type_latest_finished = "Synthetic Full"

        else:
            backup_type_latest_running = "Synthetic Full"
            backup_type_latest_finished = "Incremental"

        latest_running_job = subclient.find_latest_job(include_finished=False)
        latest_completed_job = subclient.find_latest_job(include_active=False)

        if ((latest_running_job.backup_level == backup_type_latest_running) and
                (latest_completed_job.backup_level == backup_type_latest_finished)):
            return latest_running_job

        else:
            raise Exception(
                "Synthfull job did not start : {0} .".format(
                    latest_running_job.job_id))

    def backup_validation(self, jobid, backup_type):
        """
        Method to validate backup jobs with application size and data size

           Args:

                jobid           (str)    --     jobid which needs to be
                                                validated on backup completion

                backup_type     (str)    --     expected backup type from calling method

            Returns:
                (bool)     -     Returns true if the validation
                                 of backup type and size check suceeds

            Raises:
                Exception:

                    if backup validation fails

                    if response was not success

                    if response received is empty

                    if failed to get response
        """

        type_status = False
        size_status = False

        # Validating the backup type sent by user
        base_backup_level = constants.backup_level
        if base_backup_level(backup_type) not in base_backup_level:
            raise Exception(
                "Backup Type sent does not fall under available"
                "backup levels.check the spelling and case")
        jobobj = self._commcell.job_controller.get(job_id=jobid)
        gui_backup_type = jobobj.backup_level
        self.log.info("Backup Type from GUI :%s", gui_backup_type)

        # Comparing the given backup type with actually ran backup type
        if str(gui_backup_type) != str(backup_type):
            if str(backup_type) == "Differential" and str(gui_backup_type) == "Delta":
                self.log.info("Expected Backup Type is [%s] \nRan Backup Type:[%s] for JobId:[%s]",
                              backup_type,
                              backup_type,
                              jobid
                              )
                type_status = True
            else:
                self.log.error("Expected Backup Type is [%s] \nRan Backup Type:[%s] for JobId:[%s]",
                               backup_type,
                               gui_backup_type,
                               jobid
                               )
        else:
            self.log.info("Expected Backup Type is [%s] \nRan Backup Type:[%s] for JobId:[%s]",
                          backup_type,
                          gui_backup_type,
                          jobid
                          )
            type_status = True
        jobobj = self._commcell.job_controller.get(job_id=jobid)
        full_job_details = jobobj.details
        sub_dict = full_job_details['jobDetail']['detailInfo']
        data_size = int(sub_dict.get('compressedBytes'))
        application_size = int(sub_dict.get('sizeOfApplication'))

        # Checking Application and Data size for data size validation during backup
        if application_size > 0:
            if data_size <= 0:
                self.log.error(
                    "Even though job was completed"
                    "the transferred data_size is %s", str(data_size))
            else:
                self.log.info(
                    "Application Data size is: [%s]. \nData Written Size is: [%s] for Job Id: [%s]",
                    application_size,
                    data_size,
                    jobid)
                size_status = True
        if type_status and size_status:
            return True
        else:
            log_error = "Backup Validation for Job Id : {0} failed.".format(jobobj.job_id)
            raise Exception(log_error)

    def check_client_readiness(self, clients, hardcheck=True):
        """Performs check readiness on the list of clients


            Args:
                clients    (list)  -- list of clients on which check readiness needs to be performed

                hardcheck  (bool)  -- if set to True, exception shall be raised if client is not ready
                                        else will return False.

            Returns:
                True - If client is ready [ hardchek set to false ]

                False - If client is not ready [ hardcheck set to false ]

            Raises
                Exception
                    - if client is not ready [ hardcheck set to True ]
            Example:

                ["auto", "v11-restapi"]

        """
        try:
            self.log.info("Performing check readiness on clients [{0}]".format(clients))

            _flag = True
            for client in clients:
                _client_obj = self._commcell.clients.get(client)

                if _client_obj.is_ready:
                    self.log.info("Client {0} is ready".format(client))
                else:
                    if hardcheck:
                        raise Exception("Check readiness failed for client {0}".format(client))
                    _flag = False

            if not hardcheck:
                return _flag

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_subclient(self, client=None, agent='File System', backupset='defaultBackupset', subclient_name='default'):
        """" Gets subclient object for a given commcell client, agent, backupset

            Args:
                client_name    (str)    -- Client name
                                            default: Testcase initialized client

                agent          (str)    -- Client data agent name

                backupset      (str)    -- Agents backupset name

                subclient_name (str)    -- Subclient name

            Returns:
                (object)    -    Subclient object for the given client

            Raises:
                Exception
                    -    if failed to get the default subclient
        """
        try:
            if client is None and self._testcase is not None:
                client = self._testcase.client.client_name
            elif not isinstance(client, (Client, str)):
                raise Exception("Client name expected as argument")

            self.log.info("Getting subclient object for client [{0}], agent [{1}], backupset"
                          " [{2}]".format(client, agent, backupset))

            self._commcell.clients.refresh()
            client = self._commcell.clients.get(client)
            backupset = client.agents.get(agent).backupsets.get(backupset)
            subclient = backupset.subclients.get(subclient_name)

            self.log.info("Subclient object: [{0}]".format(subclient))

            return subclient

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_backupset(self, client=None, agent='File System', backupset='defaultBackupset'):
        """" Gets backupset object for a given commcell client, agent

            Args:
                client_name    (str)    -- Client name
                                            default: Testcase initialized client

                agent          (str)    -- Client data agent name

                backupset      (str)    -- Agents backupset name

            Returns:
                (object)    -    Backupset object for the given client

            Raises:
                Exception
                    -    if failed to get the default backupset
        """
        try:
            if client is None and self._testcase is not None:
                client = self._testcase.client.client_name
            elif not isinstance(client, (Client, str)):
                raise Exception("Subclient object expected as argument")

            self.log.info("Getting backupset object for client [{0}], agent [{1}], backupset"
                          " [{2}]".format(client, agent, backupset))

            self._commcell.clients.refresh()
            client = self._commcell.clients.get(client)
            backupset = client.agents.get(agent).backupsets.get(backupset)

            self.log.info("Backupset object: [{0}]".format(backupset))

            return backupset

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def restart_services(self, clients):
        """Restarts services on the list of clients

        Args:
                clients(list)  -- list of clients on which services needs to be
                                    restarted

            Example:

                ["testproxy", "v11-restapi"]

        """
        try:
            for client in clients:
                _client_obj = self._commcell.clients.get(client)

                self.log.info("Restarting services on client {0}".format(client))

                _client_obj.restart_services()

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def subclient_backup(self,
                         subclient,
                         backup_type="Incremental",
                         wait=True,
                         target_subclient=None,
                         retry_interval=10,
                         time_limit=75,
                         **kwargs):
        """Executes backup on any subclient object and waits for job completion.

            Args:
                subclient          (obj)   -- Instance of SDK Subclient class

                backup_type        (str)   -- Backup type:
                                                Full / Incremental / Differential / Synthetic_full
                                                default: Incremental

                wait               (bool)  -- If True, will wait for backup job to complete.
                                              If False, will return job object for the backup job
                                                  without waiting for job to finish.

                target_subclient   (str)   -- subclient target string where backup shall be
                                                executed.
                        e.g:
                        client1->file system->defaultinstancename->backupset_199->subclient_199
                        OR could be any custom string from user.

                retry_interval    (int)    -- Interval (in seconds) after which job state
                                                    will be checked in a loop. Default = 10

                time_limit        (int)    -- Time limit after which job status check shall be
                                                aborted if the job does not reach the desired
                                                 state. Default (in minutes) = 30

                **kwargs           (dict)  -- Key value pair for the various subclients type
                                                inputs, depending on the subclient iDA.
                                                scheduling options to be included for the task
                                                Please refer schedules.schedulePattern.
                                                createSchedule() doc for the types of Jsons

            Returns:
                (object)    - Job class instance for the backup job in case of immediate Job.
                              Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception if:

                    - is subclient object is not passed as an argument.

                    - failed during execution of module

            Example:
                - Executes full backup for subclient and **does not wait for job completion

                    job = subclient_backup(subclient_object, "full", False)

                - Executes incremental backup for subclient and waits for job completion

                    job = subclient_backup(subclient_object, "incremental")

                - Runs incremental backup for subclient
                    job = subclient_backup(subclient_object)
        """
        try:
            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("Subclient object expected as argument")

            if target_subclient is None:
                target_subclient = subclient.subclient_name

            if 'schedule_pattern' not in kwargs:
                self.log.info("Starting [{0}] backup for subclient [{1}]".format(backup_type.upper(), target_subclient))
            else:
                self.log.info("Creating {0} Backup Schedule for subclient {1} with "
                              "pattern {2}".format(backup_type, subclient, kwargs['schedule_pattern']))

            if not bool(kwargs):
                _obj = subclient.backup(backup_type)
            else:
                _obj = subclient.backup(backup_type, **kwargs)

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)
                job_type = _obj.job_type if _obj.backup_level is None else _obj.backup_level

                self.log.info("Executed [{0}] backup job id [{1}]".format(job_type.upper(), str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed', retry_interval=retry_interval, time_limit=time_limit)
                    self.job_list.remove(_obj.job_id)

            else:
                self.log.info("Successfully created Backup Schedule with Id {0}".format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def subclient_restore_in_place(self, paths, subclient=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the same location.

            Args:
                paths                 (list)       --  list of full paths
                                                        of files/folders to restore

                subclient             (obj)        --  subclient object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various subclients type
                                                inputs for underlying restore_in_place module,
                                                depending on the subclient iDA. Schedule Pattern
                                                if schedule is needed
                                                Please refer schedules.schedulePattern.
                                                createSchedule() doc for the types of Jsons
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore
                            or restore didn't complete successfully.
        """

        try:

            # Use the current test case client as default
            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object expected as argument")

            if 'schedule_pattern' not in kwargs:
                self.log.info("Execute in place restore for subclient [{0}]".format(subclient.subclient_name))
            else:
                self.log.info(
                    "Creating Restore In Place Schedule for subclient '{0}' with paths {1} "
                    "using schedule pattern {2}".format(subclient.subclient_name, paths, kwargs['schedule_pattern']))

            _obj = subclient.restore_in_place(paths=paths, **kwargs)

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)

                self.log.info("Executed in place restore with job id [{0}]".format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)
            else:
                self.log.info("Successfully created In Place Restore Schedule with Id {0}".format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def subclient_restore_out_of_place(self, destination_path, paths, client=None, subclient=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the input client,
            at the specified destination location.

            Args:
                client                (str/object) --  either the name or the instance of Client

                destination_path      (str)        --  full path of the restore location on client

                paths                 (list)       --  list of full paths of files/folders
                                                        to restore

                subclient             (obj)        --  subclient object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various subclients type
                                                inputs for underlying restore_out_of_place module,
                                                depending on the subclient iDA.
                                                Schedule Pattern if schedule is needed
                                                Please refer schedules.schedulePattern.
                                                createSchedule() doc for the types of Jsons
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore or restore didn't
                                complete successfully.
        """
        try:

            # Use the current test case client as default
            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object expected as argument")

            # Use the current test case subclient as default
            if client is None and self._testcase is not None:
                client = self._testcase.client

            if 'schedule_pattern' not in kwargs:
                self.log.info("Executing out of place restore for subclient [{0}]".format(subclient.subclient_name))

            else:
                self.log.info(
                    "Creating Restore Out of Place Schedule for subclient '{0}' with paths "
                    "{1} to client '{2}' using schedule pattern {3}"
                        .format(subclient.subclient_name, paths, client.client_name, kwargs['schedule_pattern']))

            _obj = subclient.restore_out_of_place(
                client=client, destination_path=destination_path, paths=paths, **kwargs
            )

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)

                self.log.info("Executed out of place restore with job id [{0}]".format(str(_obj.job_id)))

                if wait:
                    # Sleep for 4 seconds for job to start. If running the API to get job details immediately after
                    # triggering via out of place restore API call, it fails randomly at times
                    self._utility.sleep_time(4)
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)
            else:
                self.log.info("Successfully created Out Of Place Restore Schedule with Id {0}".format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def subclient_backup_and_restore(self, client_name, subclient, backup_type='full', validate=True):
        """Executes backup on a subclient, and restores data out of place.
            Main purpose of this module is to test if backup and restore works on a client
            for given subclient.

            Args:
                client_name          (str)/(Machine object)
                                                 -- Client name

                subclient            (object)    -- subclient object
                                                        Default: default subclient

                backup_type          (str)       -- Backup type. Various types supported by
                                                        underlying SDK backup module.

                validate             (bool)      -- Validate source content and resotred content
                                                        metadata/contents/acl/xattr

            Raises:
                Exception if:

                    - failed during execution of module
        """
        try:
            machine_obj = self._utility.get_machine_object(client_name)
            source_dir = self._utility.create_directory(machine_obj)

            self.log.info("Adding directory to subclient content: {0}".format(source_dir))

            subclient.content += [self._utility.create_test_data(machine_obj, source_dir)]
            backup_job = self.subclient_backup(subclient, backup_type)

            # Execute out of place restore and validate data post restore.
            self.subclient_restore_from_job(source_dir,
                                            job=backup_job,
                                            subclient=subclient,
                                            client=machine_obj,
                                            validate=validate)

            self._utility.remove_directory(machine_obj, source_dir)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def subclient_restore_from_job(self,
                                   data_path,
                                   tmp_path=None,
                                   job=None,
                                   cleanup=True,
                                   subclient=None,
                                   client=None,
                                   validate=True,
                                   **kwargs):
        """ Initiates restore for data backed up in the given job
            and performs the applicable verifications

            Args:
                data_path (str)          -- Source data path

                tmp_path (str)           -- temporary path for restoring the data
                                                default: None
                                                If not provided, directory to restore will be created on client.

                job (obj)/(id)           -- instance of the job class whose data needs to be restored. Or the job id.
                                                default : None

                cleanup (bool)           -- to indicate if restored data should be cleaned up
                    default : True

                subclient (object)       -- Subclient object

                client (str)/(Machine object)
                                         -- Client name or corresponding machine object

                validate (bool)          -- If True will validate metadata for restored content
                                                default: True

                **kwargs (dict)          -- Key value pairs:
                                                supported :
                                                    dirtime (bool) - Whether to validate directory time stamps or not

                                                    applicable_os (str) - UNIX/WINDOWS

                                                    acls (bool) - Validate acls for files or not

                                                    xattr (bool) - Validate attributed for the file or not

            Returns:
                job object for the restore job.

            Raises:
                Exception
                - if any error occurred while running restore or during verification.
                - Meta data comparison failed
                - Checksum comparison failed
                - ACL comparison failed
                - XATTR comparison failed
        """
        try:

            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object expected as argument")

            # Use the current test case client as default
            if subclient is None and client is None and self._testcase is not None:
                subclient = self._testcase.subclient
                client = self._testcase.client
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object needs to be passed as argument.")

            machine_obj = self._utility.get_machine_object(client)
            client_name = kwargs.get('client_name', machine_obj.machine_name)

            log = self.log
            paths = [data_path]
            if tmp_path is None:
                tmp_path = self._utility.create_directory(machine_obj)
            data_path_leaf = ntpath.basename(data_path)
            dest_path = machine_obj.os_sep.join([tmp_path, data_path_leaf + "_restore"])

            restore_from_time = None
            restore_to_time = None
            if job is not None:
                if isinstance(job, (str, int)):
                    job = self._commcell.job_controller.get(job)
                restore_from_time = str(datetime.utcfromtimestamp(job.summary['jobStartTime']))
                restore_to_time = str(datetime.utcfromtimestamp(job.summary['jobEndTime']))

            log.info(
                """
                Starting restore with source:{1},
                destination:[{0}],
                from_time:[{2}],
                to_time:[{3}]
                """.format(
                    dest_path, str(paths), restore_from_time, restore_to_time
                )
            )

            # Clean up destination directory before starting restore
            self._utility.remove_directory(machine_obj, dest_path)
            _job = self.subclient_restore_out_of_place(dest_path,
                                                       paths,
                                                       client_name,
                                                       subclient,
                                                       from_time=restore_from_time,
                                                       to_time=restore_to_time)
            if not validate:
                return _job

            # Validation for restored content
            compare_source = data_path
            compare_destination = machine_obj.os_sep.join([dest_path, data_path_leaf])
            log.info("""Executing backed up content validation:
                        Source: [{0}], and
                        Destination [{1}]""".format(compare_source, compare_destination))

            result, diff_output = machine_obj.compare_meta_data(
                compare_source, compare_destination, dirtime=kwargs.get('dirtime', False)
            )

            log.info("Performing meta data comparison on source and destination")
            if not result:
                log.error("Meta data comparison failed")
                log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Meta data comparison failed")
            log.info("Meta data comparison successful")

            log.info("Performing checksum comparison on source and destination")
            result, diff_output = machine_obj.compare_checksum(compare_source, compare_destination)
            if not result:
                log.error("Checksum comparison failed")
                log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Checksum comparison failed")
            log.info("Checksum comparison successful")

            if kwargs.get('applicable_os') == 'UNIX':
                if kwargs.get('acls'):
                    log.info("Performing ACL comparison on source and destination")
                    result, diff_output = machine_obj.compare_acl(
                        compare_source, compare_destination
                    )
                    if not result:
                        log.error("ACL comparison failed")
                        log.error("Diff output: \n{0}".format(diff_output))
                        raise Exception("ACL comparison failed")
                    log.info("ACL comparison successful")

                if kwargs.get('xattr'):
                    log.info("Performing XATTR comparison on source and destination")
                    result, diff_output = machine_obj.compare_xattr(
                        compare_source, compare_destination
                    )
                    if not result:
                        log.error("XATTR comparison failed")
                        log.error("Diff output: \n{0}".format(diff_output))
                        raise Exception("XATTR comparison failed")
                    log.info("XATTR comparison successful")

            return _job
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            if cleanup:
                self._utility.remove_directory(machine_obj, dest_path)

    def backupset_restore_in_place(
            self, paths, backupset=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the input client,
            to the same location.

            Args:
                paths                 (list)       --  list of full paths of files/folders to restore

                backupset             (obj)        --  backupset object of relevant SDK subclient class.

                wait                  (bool)       -- If True, will wait for backup job to complete.
                                                      If False, will return job object for the backup job without
                                                          waiting for job to finish.

                **kwargs              (dict)       -- Key value pair for the various backupset type
                                                        inputs for underlying restore_out_of_place module
            Returns:
                object - instance of the Job class for this restore job Schedule Object will be returned to perform
                            tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore or restore didn't
                                complete successfully.
        """
        try:

            # Use the current test case client as default
            if backupset is None and self._testcase is not None:
                backupset = self._testcase.backupset
            elif not isinstance(backupset, Backupset):
                raise Exception("Backupset object expected as argument")

            if 'schedule_pattern' not in kwargs:
                self.log.info("Executing out of place restore for backupset [{0}]".format(backupset.backupset_name))
            else:
                self.log.info(
                    "Creating Restore In Place Schedule for subclient '{0}' with paths {1}"
                    "using schedule pattern {2}"
                        .format(backupset.backupset_name, paths, kwargs['schedule_pattern']))

            _obj = backupset.restore_in_place(paths=paths, **kwargs)

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)

                self.log.info("Executed in place restore with job id [{0}]".format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)

            else:
                self.log.info("Successfully created In Place Restore Schedule with Id {0}".format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def backupset_restore_out_of_place(
            self, destination_path, paths, client=None, backupset=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the input client,
            at the specified destination location.

            Args:
                client                (str/object) --  either the name or the instance of Client

                destination_path      (str)        --  full path of the restore location on client

                paths                 (list)       --  list of full paths of files/folders
                                                        to restore

                backupset             (obj)        --  backupset object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various backupset type
                                                inputs for underlying restore_out_of_place module
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore or restore didn't
                                complete successfully.
        """
        try:

            # Use the current test case client as default
            if backupset is None and self._testcase is not None:
                backupset = self._testcase.backupset
            elif not isinstance(backupset, Backupset):
                raise Exception("Backupset object expected as argument")

            # Use the current test case subclient as default
            if client is None and self._testcase is not None:
                client = self._testcase.client

            if 'schedule_pattern' not in kwargs:
                self.log.info("Executing out of place restore for backupset [{0}]".format(backupset.backupset_name))

            else:
                self.log.info(
                    """Creating Restore Out of Place Schedule for subclient '{0}' with paths
                        {1} to client '{2}' using schedule pattern {3}"""
                        .format(backupset.backupset_name, paths, client.client_name, kwargs['schedule_pattern']))

            _obj = backupset.restore_out_of_place(
                client=client, destination_path=destination_path, paths=paths, **kwargs
            )

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)

                self.log.info("Executed out of place restore with job id [{0}]".format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)
            else:
                self.log.info("Successfully created Out Of Place Restore Schedule with Id {0}".format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def osc_backup_and_restore(self, client, validate=False, postbackup=True, skip_osc=False, **kwargs):
        """ Validates backup works fine from osc schedule for incremental backup for devices

            Args:
                client        (str)/(Machine object)  -- Client name or Machine object

                postbackup    (bool)                  -- If true:
                                                            Execute post backup and restore on the subclient by
                                                            modifying the subclient content.

                skip_osc      (bool)                  -- If true:
                                                            Will not wait for the filtered automatic jobs to trigger
                                                            Reinstall cases for laptop, where the owner does not change

                validate      (bool)                  -- Validate cksum/metadata for the restored subclient content.

                kwargs (dict)                    -- dictionary of optional arguments

                    Available kwargs Options:

                        options             (str)   --  to specify any other additional parameters
                            default: ""

                        client_name         (str)   --  Client name
                                                        e.g For user centric case the client name would be pseudo
                                                                client.

                        current_state      (str/list)
                                                    --  Expected job state. Could be a list or string from following
                                                        job state options
                                                        'completed'
                                                        'failed'
                                                        'suspended'
                                                        'waiting'
                                                        'pending'

                                                        This is originally added to handle the jobs for pseudo clients
                                                        which are executed in parellel when User centric client is
                                                        activated.

                        incr_current_state (str/list)
                                                    --  Expected job state for incremental job.
                                                        Could be a list or string from following job state options
                                                        'completed'
                                                        'failed'
                                                        'suspended'
                                                        'waiting'
                                                        'pending'

                                                        This is originally added to handle the jobs for pseudo clients
                                                        which are executed in parellel when User centric client is
                                                        activated.

                        backup_level        (str)    -- The level of backup.
                                                        Valid values are Full, Incremental, Differential, Synthetic Full
                                                        Default: Full

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:
            machine_obj = self._utility.get_machine_object(client)
            client_name = kwargs.get('client_name', machine_obj.machine_name)
            backup_level = kwargs.get('backup_level', 'Full')
            if kwargs.get('validate_user'):
                backup_level = 'Incremental'
                job_state = ['completed', 'running', 'waiting', 'pending']
                _, filtered_jobs = self.job_manager.get_filtered_jobs(client_name, current_state=job_state)
                filtered_jobs.sort()
                latest_job = filtered_jobs[1]
                self.log.info("latest incremental job is {0}".format(latest_job))
                latest_job = JobManager(latest_job, self._commcell).job

                if not latest_job.username == kwargs['registering_user']:
                    raise Exception("Job not triggered with the activated username {0}".format(latest_job.username))

                self.log.info("Job triggered with activated username {0}".format(latest_job.username))

            # Wait for auto triggered backups
            job_state = kwargs.get('current_state')

            if not skip_osc:
                self.job_manager.get_filtered_jobs(
                    client_name,
                    time_limit=6,
                    retry_interval=5,
                    backup_level=backup_level,
                    current_state=job_state
                )

            if not postbackup:
                self.log.info("Skipping post osc backup subclient modification.")
                return True

            # Add new content to default subclient of this client and check auto triggered
            # incremental backup
            subclient = self.get_subclient(client_name)
            source_dir = self._utility.create_directory(machine_obj)
            self.temp_directory_list.append({'client': machine_obj, 'directory': source_dir})
            options = kwargs.get('options', "")
            subclient_content_dir = self._utility.create_test_data(machine_obj, source_dir, options=options)
            # Let windows flush the directory and file changes, ELSE due to timing issues the metadata
            # may not match for the time stamp of folders,  after restoring the backed up content
            self._utility.sleep_time(60)
            self.log.info("Adding directory [{0}] to subclient content".format(subclient_content_dir))
            subclient.content += [subclient_content_dir]
            job_state = kwargs.get('incr_current_state')
            if not job_state:
                job_state = kwargs.get('current_state')
            jobs = self.job_manager.get_filtered_jobs(
                client_name,
                time_limit=5,
                retry_interval=5,
                backup_level='Incremental',
                current_state=job_state
            )

            # Execute out of place restore and validate data post restore.
            self.subclient_restore_from_job(
                source_dir,
                job=jobs[1][0],
                subclient=subclient,
                client=client,
                validate=validate
            )

            self.log.info("Successfully executed auto backup jobs and validated "
                          "out of place restore on client [{0}]".format(client_name))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def aux_copy(self, storage_policy, sp_copy, media_agent, wait=True, **kwargs):
        """Executes aux copy on a specific storage policy copy and waits for job completion.

            Args:
                storage_policy    (obj/str)   -- storage policy name OR corresponding storage
                                                    policy SDK instance of class StoragePolicy

                sp_copy           (str)       -- name of the storage policy copy

                media_agent       (str)       -- name of the media agent

                wait              (bool)      -- If True, will wait for backup job to complete.

                                                  If False, will return job object for the job
                                                      without waiting for job to finish.

            Returns:
                job object        (object)    -- Job class instance for the aux copy job

            Raises:
                Exception if :

                    - storage_policy is neither the policy name nor SDK object

                    - failed during execution of module

            Example:
                - Executes aux copy for the storage policy sp01 and copy sp01_copy on media agent
                    ma01 and waits for job completion.

                job = aux_copy('sp01', 'sp01_copy', 'ma01')
        """
        try:

            # If storage policy name is passed as argument get it's object
            if isinstance(storage_policy, str):
                storage_policies = self._commcell.storage_policies
                storage_policy = storage_policies.get(storage_policy)
            elif not isinstance(storage_policy, StoragePolicy):
                raise Exception("storage_policy should either be policy name or SDK object")

            if 'schedule_pattern' not in kwargs:
                self.log.info("Starting aux copy for storage policy [{0}] copy [{1}]"
                              "".format(storage_policy.storage_policy_name, sp_copy))
            else:
                self.log.info("Creating Aux copy Schedule on commcell with pattern {0}".
                              format(kwargs['schedule_pattern']))

            if not bool(kwargs):
                _job = storage_policy.run_aux_copy(sp_copy, media_agent)
            else:
                _job = storage_policy.run_aux_copy(sp_copy, media_agent, **kwargs)

            if 'schedule_pattern' not in kwargs:
                _jobid = str(_job.job_id)
                self.job_list.append(_jobid)

                self.log.info("Executed [{0}] aux copy job id [{1}]".format(_job.job_type, _jobid))

                if wait:
                    self.job_manager.job = _job
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_jobid)

            else:
                self.log.info("Successfully created Aux copy job Schedule with Id {0}".format(_job.schedule_id))

            return _job

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def data_aging(self, storage_policy=None, sp_copy=None, wait=True, **kwargs):
        """Executes data aging for a specific storage policy copy and waits for job completion.

            Args:
                storage_policy    (obj/str)   -- storage policy name OR corresponding storage
                                                    policy SDK instance of class StoragePolicy

                sp_copy           (str)       -- name of the storage policy copy

                wait              (bool)      -- If True, will wait for backup job to complete.

                                                  If False, will return job object for the job
                                                      without waiting for job to finish.

                **kwargs           (dict)     -- Key value pair for the various subclients type
                                                 inputs, depending on the subclient iDA.
                                                 scheduling options to be included for the task
                                                 Please refer schedules.schedulePattern.
                                                 createSchedule() doc for the types of Jsons


            Returns:
                job object        (object)    -- Job class instance for the data aging job.

            Raises:
                Exception if :

                    - failed during execution of module

            Example:
                - Executes data aging for the storage policy sp01 and copy sp01_copy and waits
                    for job completion

                job = aux_copy('sp01', 'sp01_copy')
        """
        try:

            # If storage policy object is passed as argument get policy name from object
            if isinstance(storage_policy, StoragePolicy):
                storage_policy = storage_policy.storage_policy_name

            if 'schedule_pattern' not in kwargs:
                self.log.info("Starting Data aging job on commcell")
            else:
                self.log.info("Creating Data Aging Schedule on commcell with pattern {0}".
                              format(kwargs['schedule_pattern']))

            # Either Run Data Aging on commcell or on a specific storage policy and sp_copy
            if storage_policy is None and sp_copy is None:
                if not bool(kwargs):
                    _job = self._commcell.run_data_aging()
                else:
                    _job = self._commcell.run_data_aging(**kwargs)
            else:
                _job = self._commcell.run_data_aging(sp_copy, storage_policy)

            if 'schedule_pattern' not in kwargs:
                _jobid = str(_job.job_id)
                self.job_list.append(_jobid)

                self.log.info("Executed [{0}] data aging job id [{1}]".format(_job.job_type, _jobid))

                if wait:
                    self.job_manager.job = _job
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_jobid)

            else:
                self.log.info("Successfully created Data Aging Schedule with Id {0}".format(_job.schedule_id))

            return _job

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def compare_file_metadata(self, client, source_path, destination_path, dirtime=True):
        """Compares the meta data of source path with destination path and checks if they are same

             Args:

                client              (str)/(Machine object)
                                            -- Client name on which source and destination paths
                                                exist. Or corresponding machine object for client.

                source_path         (str)   --  source path of the folder to compare

                destination_path    (str)   --  destination path of the folder to compare

                dirtime             (bool)  --  whether to get time stamp of all directories
                    default: False

            Returns:
                bool   -   Returns True if lists are same or returns False

            Raises:
                Exception:
                    if any error occurred while comparing the source and destination paths.
        """

        try:
            machine_obj = self._utility.get_machine_object(client)
            client = machine_obj.machine_name

            self.log.info("Client: [{0}], Source path [{1}]".format(client, source_path))
            self.log.info("Client: [{0}], Destination path [{1}]".format(client, destination_path))
            self.log.info("Comparing meta data for source and destination paths")

            response = machine_obj.compare_meta_data(source_path, destination_path, dirtime)
            if not response[0]:
                self.log.error("Differences found between source and destination")
                self.log.error("Diff list: [{0}]".format(response[1]))
                raise Exception("Metadata comparison failed")

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def cleanup_jobs(self):
        """ Kills all the jobs in the job list self.job_list, if the jobs are not completed
                already.

            self.job_list is populated with every call to the function in this module which
                executes a job.

                For example : aux_copy, data_aging, subclient_backup

            This module can be called as part of the testcase cleanup code in case the testcase
            ends abruptly in between leaving behind these running jobs which might interfere with
            other test cases execution.

            Args:
                None:

            Returns:
                None

            Raises:
                Exception if :

                    - failed during execution of module
        """
        try:
            for _job in self.job_list:
                if isinstance(_job, str):
                    _job = self._commcell.job_controller.get(_job)

                self.log.info("Job [{0}] status = [{1}]".format(str(_job.job_id), _job.status))

                if not _job.is_finished:
                    self.job_manager.job = _job
                    self.job_manager.modify_job('kill')

                del _job

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def cleanup_dir(self):
        """ Removes directories in the temp directories list """
        try:
            for dir_map in self.temp_directory_list:
                self._utility.remove_directory(dir_map['client'], dir_map['directory'])

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def cleanup(self):
        """Generic cleanup for jobs/directories etc ."""
        self.log.info("***Cleaning up ida specific environmental changes***")
        self.cleanup_jobs()
        self.cleanup_dir()

    def modify_additional_settings(
            self, key_name, value, category="CommServDB.GxGlobalParam", data_type="STRING", client=None
    ):
        """ Updates additional settings for a client based on name and value, for a specific category and data type

            Args:
                key_name  (str)   --  Name to update
                                        Ex:"JobsCompleteIfActivityDisabled",
                                            "isMSPCommcell"

                value (str/int)  --   Value to update
                                        Ex: "0 or 1",
                                            "500"

                category (str)   --  Key category
                                        Default : CommServDB.GxGlobalParam

                data_type (str)  --  Key data type
                                        Default : STRING

                client   (str/clientobj)
                                 --  Client name OR client object for which to delete the key.
                                        Default: Commserver
            Returns:
                None

            Exception:
                failed to update parameters

        """
        try:
            self.log.info(
                "Setting %(key_name)s to %(value)s for category=%(category)s, data_type=%(data_type)s",
                {
                    'key_name': key_name,
                    'value': value,
                    'category': category,
                    'data_type': data_type,
                }
            )

            clientobj = self._commcell.commserv_client if client is None else self._utility.get_machine_object(client)
            clientobj.add_additional_setting(category, key_name, data_type, value)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete_additional_settings(self, key_name, category='CommServDB.GxGlobalParam', client=None):
        """ Updates additional settings on commserve client based on name and value,
                for a specific category and data type

            Args:
                key_name  (str)   --  Name to delete
                                        Ex:"JobsCompleteIfActivityDisabled",
                                            "isMSPCommcell"

                category (str)   --  Key category
                                        Default : CommServDB.GxGlobalParam

                client   (str/clientobj)
                                 --  Client name OR client object for which to delete the key.
                                        Default: Commserver
            Returns:
                None

            Exception:
                failed to delete key

        """
        try:
            self.log.info(
                "Deleting additional settings: category=%(category)s, %(key_name)s",
                {
                    'category': category,
                    'key_name': key_name
                }
            )

            clientobj = self._commcell.commserv_client if client is None else self._utility.get_machine_object(client)
            clientobj.delete_additional_setting(category, key_name)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def download_software(self, wait=True, **kwargs):
        """Executes Download software job and waits for job completion.

            Args:
                wait              (bool)      -- If True, will wait for backup job to complete.

                                                  If False, will return job object for the job
                                                      without waiting for job to finish.

                **kwargs           (dict)     -- Key value pair for the various options for Download software job
                                                 Please refer download_software() doc for the types of supported
                                                 Jsons


            Returns:
                job object        (object)    -- Job class instance for Download Software job.

            Raises:
                Exception if :

                    - failed during execution of module

        """
        try:

            if 'schedule_pattern' not in kwargs:
                self.log.info("Starting Download Software job on commcell")
            else:
                self.log.info("Creating Download Software Schedule on commcell with pattern {0}".
                              format(kwargs['schedule_pattern']))

            # Either Run Data Aging on commcell or on a specific storage policy and sp_copy
            if not bool(kwargs):
                _job = self._commcell.download_software()
            else:
                _job = self._commcell.download_software(**kwargs)

            if 'schedule_pattern' not in kwargs:
                _jobid = str(_job.job_id)
                self.job_list.append(_jobid)

                self.log.info("Executed [{0}] Download Software job id [{1}]".format(_job.job_type, _jobid))

                if wait:
                    self.job_manager.job = _job
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_jobid)

            else:
                self.log.info("Successfully created Download Software Schedule with Id {0}".format(_job.schedule_id))

            return _job

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def data_verification(self,
                          storage_policy,
                          media_agent_name='',
                          copy_name='',
                          jobs_to_verify='NEW',
                          wait=True,
                          **kwargs):
        """Runs Data verification job and waits for job completion.

            Args:
                storage_policy    (obj/str)       -- storage policy name OR corresponding storage
                                                    policy SDK instance of class StoragePolicy

                media_agent_name  (str)       -- name of the mediaAgent to use for data reading

                copy_name         (str)       -- name of Copy
                                                (default - verifies jobs on all copies)

                jobs_to_verify    (str)       -- jobs to be Verified
                                                 (NEW/ VERF_EXPIRED/ ALL)

                wait              (bool)      -- If True, will wait for backup job to complete.

                                                  If False, will return job object for the job
                                                      without waiting for job to finish.

                **kwargs           (dict)     -- optional arguments


            Returns:
                job object        (object)    -- Job class instance for the data aging job.

            Raises:
                Exception if :

                    - failed during execution of module
        """
        try:

            # If storage policy object is passed as argument get policy name from object
            if isinstance(storage_policy, str):
                storage_policies = self._commcell.storage_policies
                storage_policy = storage_policies.get(storage_policy)
            elif not isinstance(storage_policy, StoragePolicy):
                raise Exception("storage_policy should either be policy name or SDK object")

            if 'schedule_pattern' not in kwargs:
                self.log.info("Starting Data verification job for storage policy [{0}] copy [{1}]"
                              .format(storage_policy.storage_policy_name, copy_name))
            else:
                self.log.info("Creating Data verification Schedule on commcell with pattern {0}".
                              format(kwargs['schedule_pattern']))

            if not bool(kwargs):
                _job = storage_policy.run_data_verification(media_agent_name=media_agent_name,
                                                            copy_name=copy_name,
                                                            jobs_to_verify=jobs_to_verify)
            else:
                _job = storage_policy.run_data_verification(media_agent_name=media_agent_name,
                                                            copy_name=copy_name,
                                                            jobs_to_verify=jobs_to_verify,
                                                            **kwargs)

            if 'schedule_pattern' not in kwargs:
                _jobid = str(_job.job_id)
                self.job_list.append(_jobid)

                self.log.info("Executed [{0}] data verification job id [{1}]".format(_job.job_type, _jobid))

                if wait:
                    self.job_manager.job = _job
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_jobid)

            else:
                self.log.info("Successfully created Data Verification Schedule with Id {0}".format(_job.schedule_id))

            return _job

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def kill_active_jobs(self, client_name):
        """ Method to kill the active jobs running for the client """
        active_jobs = self._commcell.job_controller.active_jobs(client_name)
        if active_jobs:
            for job in active_jobs:
                Job(self._commcell, job).kill(True)
        else:
            self.log.info("No Active Jobs found for the client.")
