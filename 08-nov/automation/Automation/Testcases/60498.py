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

    __init__()                 --  initializes test case class object
    setup()                    --  setup function of this test case
    tear_down()                -- tear down method for test case
    run()                      --  run function of this test case
    create_ifx_helper_object() -- Creates informix helper class object
    add_data_get_metadata()    -- Adds data for incremental backup & collect backup metadata
    wait_for_job_completion()  -- Wait for completion of job and check job status
    run_backup()               -- Submit backup, interrupt and resume it
    restore_and_validate()     -- Submit restore and validate data restored

    Input Example:
    "testCases":
        {
            "60498":
                    {
                        "ClientName":"client_name",
                        "AgentName": "Informix",
                        "InstanceName":"instance_name",
                        "BackupsetName": "default",
                        "SubclientName": "default",
                        "InformixDatabasePassword": "password",
                        "InformixServiceName": "port_number"
                        "TestDataSize": [2, 10, 100]
                    }
        }
"""
import time
from AutomationUtils import logger, constants, interruption, database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper

class TestCase(CVTestCase):
    """Class for executing invalidate data archfile with restart for Informix iDA"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Invalidate data archfile with restart for Informix iDA"
        self.show_to_user = True
        self.tcinputs = {
            'InformixDatabasePassword': None,
            'InformixServiceName': None,
            'TestDataSize': None
        }
        self.informix_helper_object = None

    def setup(self):
        """Setup function of this test case"""
        self.log = logger.get_log()
        self.log.info("Started executing %s testcase", self.id)

    def run_backup(self, backup_type="FULL", job_phase="data"):
        """Submit backup, interrupt and resume to complete.
        Validate isvalid status in archfile table after job completes.
        Args:
            backup_type (str) -- Type of backup to run
                Accepted values: full, incremental. Default is Full
            job_phase (str)   -- Phase in which job has to be interrupted
                Accepted values: data, log, config_files. Default is data.
        Raises Exception if:
                Backup restarted during config file phase restart job from beginning
                IsValid for afile is not -1 for full job restarted during data backup
                IsValid for afile is not 1 for all other cases
        """
        job = self.subclient.backup(backup_type)
        self.log.info("Started %s backup with JobID: %s", backup_type, job.job_id)
        while job.phase != 'Database Backup':
            time.sleep(3)
        csdb = database_helper.get_csdb()
        interrupt_object = interruption.Interruption(job.job_id, self.commcell)
        if job_phase == "config_files":
            while job.phase != "Configuration Files Backup":
                time.sleep(1)
            interrupt_object.suspend_resume_job()
            query = "select id from archfile where jobid={0} and " \
                    "name like '%rootdbs%'".format(job.job_id)
            self.log.info("Executing query %s", query)
            csdb.execute(query)
            cur = csdb.fetch_all_rows()
            if len(cur) > 1:
                self.log.info("Query output is %s", cur)
                raise Exception("Rootdbs was not expected to have more than one entry")
        else:
            if job_phase == "data":
                query = "select id from archfile where jobid={0} and " \
                        "name like '%rootdbs%'".format(job.job_id)
            elif job_phase == "log":
                query = "select id from archfile where jobid={0} and filetype=4".format(job.job_id)
                time.sleep(3)
            while True:
                self.log.info("Executing query %s", query)
                csdb.execute(query)
                cur = csdb.fetch_all_rows()
                if len(cur[0][0]) > 0:
                    break
                time.sleep(2)
            interrupt_object.kill_process(process_name="onbar_d", client_object=self.client)
            interrupt_object.wait_and_resume()
        self.wait_for_job_completion(job.job_id)
        query2 = "select IsValid from archfile where jobid={0} " \
                 "and id={1}".format(job.job_id, cur[0][0])
        self.log.info("Executing query %s", query)
        csdb.execute(query2)
        cur2 = csdb.fetch_all_rows()
        self.log.info("Query output is %s", cur2)
        if cur2[0][0] == "-1" and job_phase == "data" and job.backup_level.lower() == "full":
            self.log.info("Afile is invalid for full restarted in data backup phase. Verified fine")
        elif cur2[0][0] == "1" and job_phase == "data" and job.backup_level.lower() == "incremental":
            self.log.info("Afile is valid for incremental restarted during data backup. "
                          "Verified fine")
        elif cur2[0][0] == "1" and job_phase in ["log", "config_files"]:
            self.log.info("Afile is valid for restart in %s backup phase. Verified fine", job_phase)
        else:
            raise Exception("Afile isvalid status is incorrect. "
                            "Check details for job {0}".format(job.job_id))

    def create_ifx_helper_object(self, refresh=False):
        """Creates object of informix helper class
        Args:
            refresh (bool) -- Skips informix test data population and
                              creates informix helper object only if True
                              Default is false
        """
        self.informix_helper_object = InformixHelper(
            self.commcell,
            self.instance,
            self.subclient,
            self.client.client_hostname,
            self.instance.instance_name,
            self.instance.informix_user,
            self.tcinputs['InformixDatabasePassword'],
            self.tcinputs['InformixServiceName']
        )
        if not refresh:
            self.log.info("Populate the informix server with "
                          "test data size=%s", self.tcinputs['TestDataSize'])
            self.informix_helper_object.populate_data(scale=self.tcinputs['TestDataSize'])

    def add_data_get_metadata(self):
        """Adds more rows to tab1 and returns metadata"""
        self.informix_helper_object.insert_rows(
            "tab1",
            database="auto1",
            scale=2)
        self.log.info("Collect metadata from server")
        metadata_backup = self.informix_helper_object.collect_meta_data()
        return metadata_backup

    def wait_for_job_completion(self, jobid):
        """Wait for completion of job and check job status
        Raises:
            Exception: If job doesnt complete fine
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    def restore_and_validate(self, metadata_backup):
        """ Submit restore and validate data restored
        Args:
            metadata_backup (str)--  metadata collected during backup
        Raises:
            Exception: If metadata validation fails.
        """
        db_space_list = sorted(self.informix_helper_object.list_dbspace())
        self.log.info("List of DBspaces in the informix server: %s", db_space_list)
        self.log.info("Stop informix server to perform restore")
        self.informix_helper_object.stop_informix_server()
        job = self.instance.restore_in_place(db_space_list)
        self.log.info("started the restore Job %d", job.job_id)
        self.wait_for_job_completion(job.job_id)
        self.log.info("Making server online and validating data")
        self.informix_helper_object.bring_server_online()
        self.log.info("Metadata collected during backup=%s", metadata_backup)
        self.create_ifx_helper_object(refresh=True)
        metadata_restore = self.informix_helper_object.collect_meta_data()
        self.log.info("Metadata collected after restore=%s", metadata_restore)
        if metadata_backup == metadata_restore:
            self.log.info("Restored data is validated")
        else:
            raise Exception("Data validation failed")

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created databases")
        if self.informix_helper_object:
            self.informix_helper_object.delete_test_data()

    def run(self):
        """Run function of this test case"""
        try:
            self.create_ifx_helper_object()
            self.log.info("Setting the backup mode of subclient to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"
            self.run_backup()
            metadata_backup = self.add_data_get_metadata()
            self.run_backup(backup_type="INCREMENTAL")
            self.restore_and_validate(metadata_backup)
            self.run_backup(job_phase="log")
            metadata_backup = self.add_data_get_metadata()
            self.run_backup(backup_type="INCREMENTAL", job_phase="config_files")
            self.restore_and_validate(metadata_backup)

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
