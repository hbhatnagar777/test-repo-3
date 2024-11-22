# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  Initializes test case class object
    setup()             --  Setup function for this test case
    run_backup()        --  Initiates backup job for specified subclient
    freespace_check()   --  Checks free space is enough for creating logs
    is_backup_started() --  Checks if log backup is started as expected
    feature_validation()--  Ensure backup is started by osc thread from log
    run()               --  Main function for test case execution

Input Example:
    "testCases":
        {
            "60485":
                    {
                        "ClientName": "client_name",
                        "AgentName": "POSTGRESQL",
                        "InstanceName": "instance_name",
                        "BackupsetName": "fsbasedbackupset",
                        "SubclientName": "default"
                    }
        }
"""
import time
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing Automatic log backup for postgresql test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Automatic log backup for postgresql"
        self.pg_helper_obj = None
        self.postgres_db_password = None
        self.pgsql_db_obj = None
        self.machine_object = None

    def setup(self):
        """setup function for this test case"""

        self.pg_helper_obj = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.pg_helper_obj.postgres_password
        self.pgsql_db_obj = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "template1")
        self.machine_object = machine.Machine(self.client)

    def run_backup(self):
        """Initiates full backup job for the default subclient
        Returns:
            job.job_id(int) -- job id of the backup job
        Raises:
            Exception       -- If backup job fails
        """
        job = self.subclient.backup("FULL")
        self.log.info("Started backup with Job ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception("Backup failed with: %s" % (job.delay_reason))
        self.log.info("Successfully finished backup job %d", job.job_id)
        return int(job.job_id)

    def freespace_check(self, disk_threshold, log_threshold):
        """Confirm free space is sufficient to create logs during test case run
        Returns:
            space_to_fill(int) -- space to be filled to meet space threshold (MB)
        Raises:
                Exception      -- If free space is not sufficient for log generation
        """
        wal_dir = self.instance.postgres_archive_log_directory
        self.log.info("Archive log location is %s", wal_dir)
        is_windows_os = "windows" in self.client.os_info.lower()
        if is_windows_os:
            cmd = "fsutil volume diskfree \"" + wal_dir + "\""
            output = self.machine_object.execute_command(cmd)
            free_space = round(int(output.output.split()[6])/1024/1024, 2)
            total_space = round(int(output.output.split()[12])/1024/1024, 2)
        else:
            cmd = "df -m " + wal_dir + " | tail -1"
            output = self.machine_object.execute_command(cmd)
            free_space = int(output.output.split()[3])
            total_space = int(output.output.split()[1])
        self.log.info("Free space is %d MB and total space is "
                      "%d MB", free_space, total_space)
        used_space = total_space - free_space
        # Add space needed for log threshold check
        used_space2 = used_space + (log_threshold*self.pg_helper_obj.get_wal_seg_size())
        used_space_percent = round(used_space2*100/total_space, 2)
        self.log.info("Used space percentage is %d", int(used_space_percent))
        if used_space_percent > disk_threshold:
            raise Exception("Space used already exceeds space threshold")
        space_to_fill = (disk_threshold-used_space_percent)*total_space/100
        self.log.info("Space to fill to meet disk threshold is %d MB", space_to_fill)
        if space_to_fill > 5120:
            disk_threshold = int(round(1024*100/total_space, 2)) + used_space_percent + 1
            raise Exception("Space to fill exceeds 5 GB. Change disk threshold to {}"
                            " to have space to fill as 1 GB".format(disk_threshold))
        return space_to_fill

    def is_backup_started(self, full_jobid):
        """Checks if expected log only backup is started within 20 minutes
        Args:
            full_jobid(int)-- Job id of the full backup run
        Returns:
            log_jobid(int) -- Job id of the log only backup
        Raises:
            Exception      -- If no log backup is triggered
        """
        dbhelper_obj = DbHelper(self.commcell)
        attempt = 0
        log_jobid = 0
        while attempt < 10:
            self.log.info("Sleeping for 2 minutes")
            time.sleep(120)
            attempt += 1
            last_job = dbhelper_obj._get_last_job_of_subclient(self.subclient)
            job_obj = self.commcell.job_controller.get(last_job)
            if last_job > full_jobid and job_obj.backup_level == "Log Only":
                job_type = job_obj.details["jobDetail"]["generalInfo"]["jobStartedFrom"]
                if job_type == "Scheduled":
                    self.log.info("Log backup triggered successfully")
                    log_jobid = last_job
                    if job_obj.wait_for_completion():
                        break
        if log_jobid == 0:
            raise Exception("Log backup not initiated as expected")
        return log_jobid

    def feature_validation(self, jobid):
        """ Method to ensure log backup was started by osc thread
        Args:
            jobid(int) -- Job id of the log backup job
        Raises:
            Exception  -- If osc.log does not have backup information
        """
        output = self.machine_object.get_logs_for_job_from_file(
            log_file_name="osc.log", search_term=str(jobid))
        if "OscStartOscJob" in output:
            self.log.info("Feature validation completed")
        else:
            raise Exception("Expected logging is missing in client")

    def run(self):
        """Main function for test case execution"""
        try:
            disk_threshold, log_threshold \
                = self.pg_helper_obj.schedule_details(self.subclient.subclient_id)
            space_to_fill = self.freespace_check(disk_threshold, log_threshold)
            self.log.info("Checking archive delete option status")
            archive_delete = self.instance.archive_delete
            if not archive_delete:
                self.log.info("Enabling archive delete in instance property")
                self.instance.archive_delete = True
            self.log.info("Running FSBased full backup to set environment")
            full_jobid = self.run_backup()
            self.log.info("Disabling archive delete in instance property")
            self.instance.archive_delete = False
            self.log.info("Creating logs for log threshold check")
            self.pg_helper_obj.switch_log(log_threshold)
            log_jobid = self.is_backup_started(full_jobid)
            self.log.info("Log only job id is %d", log_jobid)
            self.feature_validation(log_jobid)
            self.log.info("Creating logs for space threshold check")
            log_count = int(space_to_fill/self.pg_helper_obj.get_wal_seg_size()) +1
            self.pg_helper_obj.switch_log(log_count)
            log_jobid = self.is_backup_started(log_jobid)
            self.log.info("Log only job id is %d", log_jobid)
            self.feature_validation(log_jobid)
            if archive_delete:
                self.instance.archive_delete = True

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(excp)
            self.status = constants.FAILED
