# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    run_backup()    --  method to populate data and run backup job

    tear_down()     --  Tear down function to delete automation generated data

    run()           --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing Synthfull in loop testcase of MySQL iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Mysql synthfull backup in a loop and verify restores from each"
        self.mysql_helper_object = None
        self.machine_object = None
        self.tcinputs = {
            'PortForClone': None
        }
        self.dbhelper_object = None

    def setup(self):
        """setup function for this testcase"""
        # Creating MYSQLHelper Object
        self.log.info("Creating MYSQLHelper class object")
        self.mysql_helper_object = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username)
        self.machine_object = machine.Machine(self.client)
        self.dbhelper_object = DbHelper(self.commcell)

    def run_backup(
            self,
            db_name_suffix=None,
            backup_level="FULL"):
        """ method to populate data and run backup job

            Args:
                db_name_suffix      (str)  --  suffix to the database
                being created

                backup_level        (str)  --  backup level

                    Accepted Values: FULL/INCREMENTAL

                    default: "FULL"

            Returns:

                job                 (obj)  --  job object

            Raises:
                Exception:

                    if unable to run backup job

        """
        self.log.info("Adding data before running %s backup", backup_level)
        self.log.info("Generating Test Data")
        database_name = "automation_inc{0}".format(db_name_suffix)
        self.mysql_helper_object.generate_test_data(database_name, 2, 3, 50)

        ### run incremental backup
        self.log.info("###Starting %s backup job###", backup_level)
        if backup_level.lower() == "full":
            job = self.dbhelper_object.run_backup(
                self.subclient,
                "FULL")
        else:
            job = self.dbhelper_object.run_backup(
                self.subclient,
                "Incremental",
                inc_with_data=True)
        ###### Wait for log backup to complete
        job_log = self.dbhelper_object.get_snap_log_backup_job(job.job_id)
        self.log.info(
            "Log backup job with ID:%s is now completed",
            job_log.job_id)
        if not job_log.wait_for_completion():
            raise Exception(
                "Failed to run log backup job with error: {0}".format(
                    job_log.delay_reason
                )
            )
        return job

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.mysql_helper_object.cleanup_test_data("automation")

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.mysql_helper_object.snap_prerequirement_check()

            self.log.info(
                "Check Basic Setting of mysql server before stating the test cases")
            self.mysql_helper_object.basic_setup_on_mysql_server()

            # populate test data
            self.mysql_helper_object.generate_test_data()
            self.log.info("Test Data generated..!!")

            ###################### Running Full Backup ########################
            self.log.info("Starting FULL backup job")
            full_job = self.dbhelper_object.run_backup(self.subclient, "FULL")

            full_job_log = self.dbhelper_object.get_snap_log_backup_job(full_job.job_id)
            self.log.info("Log backup job with ID:%s is now completed", full_job_log.job_id)

            if "native" in self.subclient.snapshot_engine_name.lower():
                self.log.info(
                    (
                        "Native Snap engine is being run. Backup "
                        "copy job will run inline to snap backup"))
                self.log.info("Getting the backup job ID of backup copy job")
                job = self.dbhelper_object.get_backup_copy_job(full_job.job_id)
                self.log.info("Job ID of backup copy Job is: %s", job.job_id)

            for iteration in range(0, 2):
                #### Running Incremental and synthfull in loop
                for incremental in range(1, 3):
                    incremental_job = self.run_backup(
                        "_{0}_{1}".format(incremental, iteration),
                        backup_level="INCREMENTAL")

                    if "native" in self.subclient.snapshot_engine_name.lower():
                        self.log.info(
                            (
                                "Native Snap engine is being run. Backup "
                                "copy job will run inline to snap backup"))
                        self.log.info("Getting the backup job ID of backup copy job")
                        job = self.dbhelper_object.get_backup_copy_job(incremental_job.job_id)
                        self.log.info("Job ID of backup copy Job is: %s", job.job_id)

                if "native" not in self.subclient.snapshot_engine_name.lower():
                    self.log.info("Snap engine is not native.")
                    ###### Run backup copy job #########
                    self.log.info(
                        "Running backup copy job for storage policy: %s",
                        self.subclient.storage_policy)
                    copy_precedence = self.dbhelper_object.run_backup_copy(
                        self.subclient.storage_policy)
                    self.log.info(
                        "Copy precedence of 'primary snap' copy is: %s",
                        copy_precedence)

                ############ run synthfull backup jobs ######
                self.dbhelper_object.synthfull_backup_validation(
                    self.client, self.machine_object, self.subclient, is_synthfull_loop=True)

                db_size_before = self.mysql_helper_object.get_database_information()

                ########### verify clone restore #############
                storage_policy_object = self.commcell.storage_policies.get(
                    self.subclient.storage_policy)
                copy_precedence = storage_policy_object.get_copy_precedence("primary")
                self.log.info("Copy precedence of Primary copy:%s", copy_precedence)
                self.log.info("starting clone restore")
                clone_options = {"stagingLocaion": "/tmp/22222",
                                 "forceCleanup": True,
                                 "port": str(self.tcinputs['PortForClone']),
                                 "libDirectory": "",
                                 "isInstanceSelected": True,
                                 "reservationPeriodS": 3600,
                                 "user": "",
                                 "binaryDirectory": self.instance.binary_directory
                                }
                self.log.info("Clone Options: %s", clone_options)
                self.mysql_helper_object.run_restore(
                    ["/"],
                    clone_env=True, copy_precedence=copy_precedence, clone_options=clone_options)

                mysql_helper_clone = MYSQLHelper(
                    self.commcell,
                    self.subclient,
                    self.instance,
                    self.client.client_hostname,
                    self.instance.mysql_username,
                    int(self.tcinputs['PortForClone']))

                db_size_after = mysql_helper_clone.get_database_information()
                self.mysql_helper_object.validate_db_info(
                    db_size_before, db_size_after)

                self.log.info("Restoring from primary copy")
                # stopping mysql server
                self.mysql_helper_object.stop_mysql_server()
                # Restore from Primary copy
                self.mysql_helper_object.run_restore(
                    db_list=["/"], copy_precedence=copy_precedence, table_level_restore=False)

                db_size_after = self.mysql_helper_object.get_database_information()

                self.mysql_helper_object.validate_db_info(
                    db_size_before, db_size_after)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
