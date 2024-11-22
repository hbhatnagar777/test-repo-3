# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup method for testcase

    tear_down()             --  tear down method for the testcase

    populate_run_backup()   --  method to populate data and run backup

    run_sweep_job()         --  method to ensure sweep job run

    run_restore_validate()  --  method to run restore and validate data after restore

    run()                   --  run function of this test case

    kill_active_jobs()      --  method to kill all active job for the client

"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing index reconstruction case of Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Index reconstruction case of Informix iDA"
        self.tcinputs = {
            'InformixDatabasePassword': None,
            'InformixServiceName': None,
            'TestDataSize': None
        }
        self.dbhelper_object = None
        self.informix_helper_object = None
        self.base_directory = None

    def setup(self):
        """ setup method for the testcase """
        self.dbhelper_object = DbHelper(self.commcell)
        self.informix_helper_object = InformixHelper(
            self.commcell,
            self.instance,
            self.subclient,
            self.client.client_hostname,
            self.instance.instance_name,
            self.instance.informix_user,
            self.tcinputs['InformixDatabasePassword'],
            self.tcinputs['InformixServiceName'],
            run_log_only_backup=True)
        self.base_directory = self.informix_helper_object.base_directory
        if self.commcell.schedule_policies.has_policy('ifx_idx_automation_sweep'):
            self.log.info("Deleting the existing sweep schedule policy")
            self.commcell.schedule_policies.delete('ifx_idx_automation_sweep')
        self.log.info("Creating the sweep schedule policy")
        self.informix_helper_object.create_sweep_schedule_policy(
            'ifx_idx_automation_sweep', sweep_time=1)

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created databases")
        if self.informix_helper_object:
            self.informix_helper_object.delete_test_data()
        if self.commcell.schedule_policies.has_policy('ifx_idx_automation_sweep'):
            self.log.info("Deleting the automation created sweep schedule policy")
            self.commcell.schedule_policies.delete('ifx_idx_automation_sweep')

    def populate_run_backup(self, backup_type="incr"):
        """ method to populate data and run backup

        Args:
            backup_type(str)    --  Type of backup to run
                Accepted values: full/incr

        """
        if "full" in backup_type:
            self.log.info("Populating the informix server")
            self.informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            self.log.info("Setting the backup mode of subclient to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"
            full_job = self.dbhelper_object.run_backup(self.subclient, "FULL")
            return (full_job, None)
        self.informix_helper_object.insert_rows(
            "tab1",
            database="auto1",
            scale=2)
        meta_data_before_backup = self.informix_helper_object.collect_meta_data()
        self.log.info("Starting log backup")
        self.informix_helper_object.cl_switch_log(
            self.client.client_name,
            self.client.instance,
            self.base_directory)
        self.informix_helper_object.cl_log_only_backup(
            self.client.client_name,
            self.client.instance,
            self.base_directory)
        self.log.info("Finished log backup")
        return (None, meta_data_before_backup)

    def run_sweep_job(self, full_job, force_sweep=False):
        """ method to ensure sweep job run

        Args:
            full_job    (obj)    --  Full job object

            force_sweep (bool)  --  Flag to force sweep job using regkey

        """
        self.log.info("Sleeping for 2 mins")
        time.sleep(120)
        if force_sweep:
            return self.informix_helper_object.run_sweep_job_using_regkey()
        cli_subclient = self.instance.backupsets.get('default').subclients.get('(command line)')
        last_job = self.dbhelper_object._get_last_job_of_subclient(cli_subclient)
        if not last_job:
            self.informix_helper_object.run_sweep_job_using_regkey()
        else:
            job_obj = self.commcell.job_controller.get(last_job)
            if not ("(command line)" in job_obj.subclient_name.lower() and job_obj.job_type.lower() in "backup" and job_obj.start_timestamp > full_job.start_timestamp):
                self.informix_helper_object.run_sweep_job_using_regkey()

    def run_restore_validate(self, meta_data, copy_precedence=None):
        """ method to run restore and validate data after restore

        Args:
            meta_data(dict)         --  meta data after full backup

            copy_precedence(int)    --  Copy precedence of aux copy

                default: None

        """
        self.log.info("Stopping informix server to perform restore")
        self.informix_helper_object.stop_informix_server()
        self.log.info("***************Starting restore Job*****************")
        if not copy_precedence:
            self.informix_helper_object.cl_restore_entire_instance(
                self.client.client_name,
                self.client.instance,
                self.base_directory)
        else:
            self.informix_helper_object.cl_aux_copy_restore(
                self.client.client_name,
                self.client.instance,
                self.base_directory,
                copy_precedence)
            self.informix_helper_object.cl_aux_log_only_restore(
                self.client.client_name,
                self.client.instance,
                self.base_directory,
                copy_precedence)
        self.log.info("Finished commandline restore of Entire Instance")
        self.informix_helper_object.bring_server_online()
        self.informix_helper_object.reconnect()
        meta_data_after_restore = self.informix_helper_object.collect_meta_data()
        if meta_data == meta_data_after_restore:
            self.log.info("Data is validated Successfully.")
        else:
            raise Exception(
                "Database information validation failed.")

    def kill_active_jobs(self):
        """ Method to kill the active jobs running for the client """
        self.commcell.refresh()
        active_jobs = self.commcell.job_controller.active_jobs(self.client.client_name)
        self.log.info("Active jobs for the client:%s", active_jobs)
        if active_jobs:
            for job in active_jobs:
                self.log.info("Killing Job:%s", job)
                self.commcell.job_controller.get(job).kill(True)
            active_jobs = self.commcell.job_controller.active_jobs(self.system_name)
            if active_jobs:
                self.kill_active_jobs()
            self.log.info("All active jobs are killed")
        else:
            self.log.info("No Active Jobs found for the client.")

    def run(self):
        """Main function for test case execution"""

        try:
            self.kill_active_jobs()
            self.log.info("Started executing %s testcase", self.id)
            self.log.info(
                "Requested data population size=%s",
                self.tcinputs['TestDataSize'])
            if not self.informix_helper_object.is_log_backup_to_disk_enabled():
                raise Exception("Log backup to disk feature needs to be enabled for this Testcase")
            full_job = self.populate_run_backup(backup_type="full")[0]
            force_sweep = False
            for i in range(0, 2):
                meta_data_before_backup = self.populate_run_backup()[1]
                if i == 1:
                    force_sweep = True
                    self.log.info("Running 2nd Sweep job after index reconstruction")
                self.run_sweep_job(full_job, force_sweep)
                self.log.info("Deleting V2 index and restart index service")
                self.dbhelper_object.delete_v2_index_restart_service(self.backupset)
            self.run_restore_validate(meta_data_before_backup)

            ###################### creating aux copy ########################
            dbhelper_object = DbHelper(self.commcell)
            self.dbhelper_object.delete_v2_index_restart_service(self.backupset)
            copy_precedence = dbhelper_object.prepare_aux_copy_restore(self.subclient.storage_policy)
            self.log.info("Proceeding to restore with copy precendence value = %s", copy_precedence)
            self.run_restore_validate(meta_data_before_backup, copy_precedence)

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
