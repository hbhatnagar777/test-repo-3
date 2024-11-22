# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing cloudlaptop operations on Commcell

cloudlaptopHelper is the only class defined in this file

cloudlaptopHelper:
    __init__()                  --  initialize instance of the cloudlaptopHelper class

    __repr__()                  --  Representation string for the instance
                                    of the cloudlaptopHelper class.

    run_backup()                --  Check for backup to be triggered and completed successfully

    get_osc_min_interval()      --  Get automatic schedule's minimum backupinterval minutes

    backup_logfile()            --  Removes and renames old logfile

    incr_backup_and_restore()   --  Validates incremental backup and restore works fine from osc schedule

    wait_for_full_backup()      --  Validates first full backup ran for the cloud laptop

    osc_backup_and_restore()    --  Automatic backup and restore validation for cloud laptops

    is_macore_installed()       --  Check if storage accelerator package is installed or not.

    validate_restore()          --  Method to validate restore jobs with meta data and checksum

    validate_backup_log()       --  Method to validate backup log with required log line

    rename_backup_logfile()     -- rename the backup logfile before trigger the current backup

    check_if_any_job_running()    -- Method to verify currently any backup job running on the client machine

    validate_job_from_backuplog()    -- Method to validate backup status from both logs and registry
    
    validate_immediate_backup()  -- Validates incr backup ran for the cloud laptop when Worktoken for immediate backup received

"""

import inspect
import ntpath
import os
from cvpysdk.schedules import Schedules, Schedule
from AutomationUtils.options_selector import OptionsSelector
from Laptop.CloudLaptop import cloudlaptop_constants
from AutomationUtils.idautils import CommonUtils
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from AutomationUtils import logger


class CloudLaptopHelper():
    """CloudLaptopHelper class to perform Cloudlaptop related operations"""

    def __init__(self, testcase):
        ''' Initialize instance of CloudLaptopHelper class

        Args:
            testcase (object)       : Should be testcase object

        '''

        # Pre-initialized attributes applicable for all instances of the class
        self._testcase = testcase
        self._commcell = self._testcase.commcell
        self.log = logger.get_log()
        self.utils = CommonUtils(self._testcase)
        self.utility = OptionsSelector(self._commcell)
        self._source_dir = None
        self._subclient_content_dir = None

    def __repr__(self):
        """Representation string for the instance of the CloudLaptopHelper class."""
        return "CloudLaptopHelper class instance"

    @property
    def source_dir(self):
        """ Get source data directory"""
        return self._source_dir

    @source_dir.setter
    def source_dir(self, value):
        """ Set source data directory"""
        self._source_dir = value

    @property
    def subclient_content_dir(self):
        """ Get subclient content directory"""
        return self._subclient_content_dir

    @subclient_content_dir.setter
    def subclient_content_dir(self, value):
        """ Set subclient content directory"""
        self._subclient_content_dir = value

    def run_backup(self, client, clbackup_log, logstring, job_id, subclient_id):
        """ Check for backup triggered and completed successfully

        Args:

            client (obj/str)          -- Machine class object for the client Or Client Name

            clbackup_log  (str)       -- Clbackup log to be validated after backup

            logstring   (str)         --  Logstring which we want to verify in log.

            job_id (str)              -- Current running job id

            input_path(str)           -- input path for subclient content

            subclient_id (id)         -- subclient id of the client

        Raises:
            Exception:

                - if unable to find required Logstring

        """

        try:
            machine_object = self.utility.get_machine_object(client)
            client_name = machine_object.machine_name

            # Perform CLbackup log file validation
            value = self.validate_backup_log(machine_object, clbackup_log, logstring)
            if value:
                self.log.info("job {0} completed successfully on client {1}".format(job_id, client_name))
            else:
                raise Exception("job {0} failed on client: {1}, Please check the logs".format(job_id, client_name))
            full_jobid = self.utility.check_reg_key(machine_object, "LaptopCache\\" + subclient_id, "LastFullJobID")

            # Validate backup ran as incremental
            assert job_id != full_jobid, "Expected Incremental job but converted to full job"
            self.log.info("Current running backup job is incremental as expected")
            self.log.info("Backup validation completed successfully on client: {0}".format(client_name))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_osc_min_interval(self, subclient=None):
        """
        Method to get automatic schedule's minimum backupinterval minutes

        Args:
            subclient (obj):    Subclient object
                                    Default: testcase object subclient
            Raises:
                Exception:

                    if module failed to execute due to some error

            Returns:
                _min (min backup interval in seconds) (int)
        """
        try:
            if subclient is None:
                subclient = self._testcase.subclient
            schedule_obj = Schedules(subclient)
            schedule_id = list(schedule_obj.schedules.keys())[0]
            schedule_obj = Schedule(self._commcell, schedule_id=schedule_id)
            schedule_name = schedule_obj.schedule_name
            min_bkp_interval = schedule_obj.automatic['min_interval_minutes']
            _min = min_bkp_interval * 60  # Seconds
            self.log.info("Automatic schedule [%s] min back interval [%s]min", schedule_name, min_bkp_interval)
            return _min

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def rename_backup_logfile(self, client):
        """ rename the backup logfile before trigger the current backup
        Args:

            machine (object)     -- Machine object

            client_obj (object) -- client object

        """
        # verify incremental job when immediate backp triggered .
        client_obj = self._commcell.clients.get(client)
        machine_obj = self.utility.get_machine_object(client)
        logfile_to_rename = os.path.join(client_obj.log_directory, 'clBackup.log')
        if machine_obj.check_file_exists(logfile_to_rename.replace(".log", "_1.log")):
            machine_obj.remove_directory(logfile_to_rename.replace(".log", "_1.log"))
        if machine_obj.check_file_exists(logfile_to_rename):
            machine_obj.rename_file_or_folder(logfile_to_rename, logfile_to_rename.replace(".log", "_1.log"))

    def incr_backup_and_restore(self, client, subclient_object=None, validate=True, cleanup=True):
        """
            Validates incremental backup and restore works fine from osc schedule

            Args:
                client        (str)/(Machine object)  -- Client name or Machine object

                subclient_object      (object)        -- Sub client object

                validate      (bool)                  -- Validate cksum/metadata for the restored subclient content.

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:

            self.add_subclient_content(client, subclient_object)
            self.wait_for_incremental_backup(client, subclient_object)
            self.out_of_place_restore(client, subclient_object, validate, cleanup)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def wait_for_full_backup(self, client_obj, subclient_object):
        """
            Validates first full backup ran for the cloud laptop

            Args:
                client_obj        (str)/(Machine object)  -- Client name or Machine object

                subclient_object      (object)            -- Sub client object

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:
            job_regkey_path = "LaptopCache\\" + str(subclient_object.subclient_id)
            full_jobid = self.utility.check_reg_key(client_obj, job_regkey_path, "JobID")
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "PhaseStatus", 10, 30, True, 1)
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "RunStatus", 10, 5, True, 0)
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "LastFullJobID", 5, 5, True, full_jobid)
            for key in ['TotalFiles', 'LastSuccessfulBackup', 'JobStartTime']:
                _ = self.utility.check_reg_key(client_obj, job_regkey_path, key)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def osc_backup_and_restore(self, client, validate=True, postbackup=True, skip_osc=False):
        """
            Validates first full backup ran for the cloud laptop

            Validates backup works fine from osc schedule for incremental backup for devices

            Args:
                client        (str)/(Machine object)  -- Client name or Machine object

                postbackup    (bool)                  -- If true:
                                                            Execute post backup and restore on the subclient by
                                                            modifying the subclient content and validating incremental
                                                            backups

                skip_osc      (bool)                  -- If true:
                                                            Will not wait for the first full auto trigrred backup job

                validate      (bool)                  -- Validate cksum/metadata for the restored subclient content.

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:
            client_obj = self.utility.get_machine_object(client)
            client_name = client_obj.machine_name
            subclient_object = self.utils.get_subclient(client_name)

            if not skip_osc:
                # Validate Full backup started and wait for job to complete.
                _ = self.utility.is_regkey_set(client_obj, 'MediaAgent', 'EnableCloudLaptopMode', 5, 5, True, 1)
                _ = self.utility.is_regkey_set(client_obj, 'MediaAgent', 'LaptopBackupMode', 5, 5, True, 2)
                self.is_macore_installed(self._commcell.clients.get(client_name).client_id)
                self.wait_for_full_backup(client_obj, subclient_object)

            if not postbackup:
                self.log.info("Skipping post osc backup subclient modification.")
                return True

            self.incr_backup_and_restore(client_obj, subclient_object, validate)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def scaletest(self, tcinputs):
        """ Laptop installation and registration
        Args:

        """
        try:

            self.log.info("Create testdata under testpath [{0}]".format(tcinputs['testdatapath']))
            machine_object = self.utility.get_machine_object(
                tcinputs['Machine_host_name'], tcinputs['Machine_user_name'], tcinputs['Machine_password']
            )
            tcinputs['Machine_object'] = machine_object
            machine_object.generate_test_data(file_path=tcinputs["testdatapath"], dirs=tcinputs["numfolders"], files=tcinputs["numfiles"], levels=tcinputs["levels"], file_size=tcinputs["filesize"])
            skip_osc = False
            if tcinputs['OperationType'] == "DataOperations":
                skip_osc = True
            self.osc_backup_and_restore(
                    machine_object,
                    validate=True,
                    skip_osc=skip_osc
                )
            # Run Synthfull backup
            subclient_object = self.utils.get_subclient(tcinputs['Machine_client_name'])

            self.utils.subclient_backup(subclient_object, backup_type='Synthetic_full')

        except Exception as excp:
            raise Exception ("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_macore_installed(self, clientid):
        """ Check if ma core is installed or not on the client.

            Args:

                clientid (int)             -- Client id

            Returns:
                True/False        (bool)   -- In case ma core is/(is not) installed

        """
        from Install.softwarecache_helper import SoftwareCache
        software_cache = SoftwareCache(self._commcell, self._commcell.commserv_client)
        package_status = software_cache.is_package_installed(clientid, 54, 60, 30, True)
        if package_status:
            self.log.info("Storage Accelerator is installed successfully on client")
            return package_status
        raise Exception("Failed to install Storage Accelerator package on client")

    def validate_restore(self, client, compare_source, compare_destination):
        """
        Method to validate restore jobs with meta data and checksum information

           Args:
                client (obj/str)                 --   MAchine client object or client name

                compare_source          (str)    --   source path that data needs to be
                                                      validated on restore completion

                compare_destination     (str)    --   destination path from data needs to be
                                                      validated on restore completion

            Raises:
                Exception:

                    if Meta data comparison failed

                    if Checksum comparison failed

        """
        try:

            machine_obj = self.utility.get_machine_object(client)
            client_name = machine_obj.machine_name

            self.log.info("""Comparing metada on source and destination
                Client: [{0}],
                    Source path [{1}]
                    Destination path [{2}]""".format(client_name, compare_source, compare_destination))

            result, diff_output = machine_obj.compare_meta_data(compare_source, compare_destination)
            if not result:
                self.log.error("""Meta data comparison failed. Diff output: \n {0}""".format(diff_output))
                raise Exception("Meta data comparison failed")
            self.log.info("Meta data comparison successful")

            self.log.info("Performing checksum comparison on source and destination")
            result, diff_output = machine_obj.compare_checksum(compare_source, compare_destination)
            if not result:
                self.log.error("""Checksum comparison failed. Diff output: \n{0}""".format(diff_output))
                raise Exception("Checksum comparison failed")
            self.log.info("Checksum comparison successful")

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def add_subclient_content(self, client, subclient_object=None):
        """
            Validates first full backup ran for the cloud laptop

            Validates backup works fine from osc schedule for incremental backup for devices

            Args:
                client        (str)/(Machine object)  -- Client name or Machine object

                subclient_object (subclient object)   -- subclient object

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:
            client_obj = self.utility.get_machine_object(client)
            client_name = client_obj.machine_name
            subclient_object = self.utils.get_subclient(client_name)
            # Create content and modify subclient content
            machine_obj = self.utility.get_machine_object(client_name)
            source_dir = self.utility.create_directory(machine_obj)
            subclient_content_dir = self.utility.create_test_data(machine_obj, source_dir)
            self._source_dir = source_dir
            self._subclient_content_dir = subclient_content_dir
            self.utility.sleep_time(5)
            self.log.info("Adding directory [{0}] to subclient content".format(subclient_content_dir))
            subclient_object.content += [subclient_content_dir]
            self.log.info("Subclient content [{0}] added successfully".format(subclient_content_dir))
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def wait_for_incremental_backup(self, client, subclient_object=None, os_type='windows'):
        """
            Validates first full backup ran for the cloud laptop

            Validates backup works fine from osc schedule for incremental backup for devices

            Args:
                client        (str)/(Machine object)  -- Client name or Machine object

                subclient_object (subclient object)   -- subclient object

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:
            # Wait for incremental job to start based on automatic schedule setting.
            client_obj = self.utility.get_machine_object(client)
            client_name = client_obj.machine_name
            subclient_object = self.utils.get_subclient(client_name)
            subclient_id = str(subclient_object.subclient_id)
            if os_type =='Mac':
                job_regkey_path = "LaptopCache/" + subclient_id
            else:
                job_regkey_path = "LaptopCache\\" + subclient_id
            next_interval = self.get_osc_min_interval(subclient_object)
            self.utility.sleep_time(next_interval, "Wait for incremental backup to start")
            self.utility.sleep_time(10)
            jobid = self.utility.check_reg_key(client_obj, job_regkey_path, "JobID")
            fulljobid = self.utility.check_reg_key(client_obj, job_regkey_path, "LastFullJobID")
            assert jobid != fulljobid, "Expected Incremental job did not start"
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "PhaseStatus", 10, 30, True, 1)
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "RunStatus", 10, 5, True, 0)
            for key in ['LastFullJobRefTime_JM', 'LastIncrJobRefTime_JM', 'LastSuccessfulBackup', 'TotalFiles']:
                _ = self.utility.check_reg_key(client_obj, job_regkey_path, key)
            self.log.info("Backup job [{0}] completed successfully".format(jobid))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def out_of_place_restore(self, client, subclient_object, validate=True, cleanup=True):
        """
            Validates first full backup ran for the cloud laptop

            Validates backup works fine from osc schedule for incremental backup for devices

            Args:
                client        (str)/(Machine object)  -- Client name or Machine object

                subclient_object (subclient object)   -- subclient object

            Raises:
                Exception if:
                    - failed during execution of module
        """
        try:

            # Out of place restore
            self.log.info("Started Out of place restore")
            client_obj = self.utility.get_machine_object(client)
            client_name = client_obj.machine_name
            machine_obj = self.utility.get_machine_object(client_name)
            self.utility.sleep_time(300, "Wait for index play back to finish")
            data_path_leaf = ntpath.basename(str(self._source_dir))
            dest_dir = self.utility.create_directory(machine_obj)
            dest_path = machine_obj.os_sep.join([dest_dir, data_path_leaf + "_restore"])
            self.utils.subclient_restore_out_of_place(
                dest_path,
                [self._subclient_content_dir],
                client=client_name,
                subclient=subclient_object,
                wait=True
            )

            # Meta data comparison
            if validate:
                compare_destination = machine_obj.os_sep.join([dest_path, data_path_leaf])
                self.validate_restore(client_obj, self._source_dir, compare_destination)
            self.log.info("Restore validation completed successfully")
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

        finally:
            try:
                if cleanup:
                    self.utility.remove_directory(machine_obj, self._source_dir)
                    self.utility.remove_directory(machine_obj, dest_dir)
            except Exception as error:
                self.log.info("Failed to cleanup test data{0}".format(error))

    def check_if_any_job_running(self, client, subclient_object):
        """
        Method to verify currently any backup job running on the client machine

           Args:

                client_name (str)  -- Client name

                subclient_object (object) -- subclient object

            Raises:
                Exception:

                    - if Last backup job failed or failed during execution of module

        """
        try:
            subclient_id = subclient_object.subclient_id
            status_list = cloudlaptop_constants.STATUS
            i = 1
            while i <= 5:
                # ------ read the registry to check the run status of previous run ---- #
                self.log.info("***** Reading the RunStatus value from registry *****")
                status_value = self.utility.check_reg_key(
                    client,
                    "LaptopCache\\" + subclient_id,
                    "RunStatus",
                    fail=False
                    )
                # ------ check and wait for the backup status to be zero ---- #
                # -- Status: 1,2,3,4,5 - means currently backup job is running --#
                if status_value in status_list:
                    OptionsSelector(self._commcell).sleep_time(30, "Waiting for Backup job to finish")
                # -- Status: 0 - means currently no backup job is running --#
                elif status_value == '0':
                    self.log.info("No backup job running on client [{0}]".format(client))
                    return True
                elif status_value == '6':
                    raise Exception("Last backup job failed on client [{0}]".format(client))
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_job_from_backuplog(self, client):
        """
        Method to validate backup status from backup log 
           Args:

                 client        (str)/(Machine object)  -- Client name or Machine object 

            Raises:
                Exception:

                    - if Last backup job failed or failed during execution of module

        """
        try:

            client_obj = self._commcell.clients.get(client)
            machine_obj = self.utility.get_machine_object(client)
            logfile_to_check = os.path.join(client_obj.log_directory, 'clBackup.log')
            logline = cloudlaptop_constants.LOGSTRING
            self.log.info("*---------- Reading the Backup job status from the logs----------")
            retry_count = 3
            backp_flag = 0
            for _count in range(retry_count):
                if machine_obj.check_file_exists(logfile_to_check):
                    self.utility.sleep_time(60, "waiting for backup log to be completed")
                    log_content = machine_obj.read_file(logfile_to_check)
                    if logline in log_content:
                        self.log.info("Backup job Validation completed successfully")
                        backp_flag = 1
                        break
                self.utility.sleep_time(60, "Waiting for backup log to be generated")
            if not backp_flag:
                raise Exception("Backup phase not started as expected")

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_immediate_backup(self, client, subclient_object, os_type='windows', validate_logs=True):
        """
            Validates incr backup ran for the cloud laptop when Worktoken for immediate backup received

            Args:
                 client        (str)/(Machine object)  -- Client name or Machine object 

                subclient_object (subclient object)   -- subclient object
                
                os_type (str)                         -- Os type of the cloud laptop

            Raises:
                Exception if:
                    - failed during execution of module

        """
        
        try:
            # verify incremental job when immediate backp triggered .
            client_obj = self.utility.get_machine_object(client)
            client_name = client_obj.machine_name
            subclient_object = self.utils.get_subclient(client_name)
            subclient_id = str(subclient_object.subclient_id)
            
            if os_type =='Mac':
                job_regkey_path = "LaptopCache/" + subclient_id
            else:
                job_regkey_path = "LaptopCache\\" + subclient_id
            # after backup triggered in edge verifying backup log generated or not 
            if validate_logs is True:  
                self.validate_job_from_backuplog(client)
            jobid = self.utility.check_reg_key(client_obj, job_regkey_path, "JobID")
            fulljobid = self.utility.check_reg_key(client_obj, job_regkey_path, "LastFullJobID")
            assert jobid != fulljobid, "Expected Incremental job did not start"
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "PhaseStatus", 10, 30, True, 1)
            _ = self.utility.is_regkey_set(client_obj, job_regkey_path, "RunStatus", 10, 5, True, 0)
            for key in ['LastFullJobRefTime_JM', 'LastIncrJobRefTime_JM', 'LastSuccessfulBackup', 'TotalFiles']:
                _ = self.utility.check_reg_key(client_obj, job_regkey_path, key)
            self.log.info("Backup job [{0}] completed successfully".format(jobid))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        
    def run_sythfull_with_incremenatlfrom_webconsole(self, client_name, webconsole_object, machine_object=None):
        """
        Method to start the backup from webconsole before sythfull

           Args:

                client_name (str)  -- Client name

                webconsole_object(object) -- webconsole object

                machine_object(object) -- machine_object

            Raises:
                Exception:

                    - failed during execution of module

        """

        try:
            webconsole_backup_obj = ClientDetails(webconsole_object)
            subclient_object = self.utils.get_subclient(client_name)
            if machine_object is None:
                machine_object = self.utility.get_machine_object(client_name)
            # --- verify any job running currently on client before trigger new job from webconsole---#
            job_status = self.check_if_any_job_running(client_name, subclient_object)
            if not job_status:
                raise Exception("Previous job stuck and not completed")
            #---change registry value to Start new backup job id--- #
            self.utility.update_reg_key(machine_object, "LaptopCache\\" + subclient_object.subclient_id, "StartNewJob")
            # --- Trigger backup job and verify notification from webconsole ---#
            webconsole_backup_obj.click_on_backup_button(cloud_direct=True)
            # --- trigger the synthfull job --- #
            self.utils.subclient_backup(subclient_object, backup_type='Synthetic_full')

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

