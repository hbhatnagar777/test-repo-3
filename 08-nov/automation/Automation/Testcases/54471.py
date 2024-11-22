# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function for the test case

    restore_validation()--  Method to validate oracle database after replication is complete

    run()           --  run function of this test case

    tear_down()     -- Tear down function for this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """Class for executing Oracle live sync test case"""

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle live sync automation test case"
        self.oracle_helper_source = None
        self.oracle_helper_destination = None
        self.machine_object = None
        self.result_string = "Run of test case 54471 is incomplete"
        self.tcinputs = {
            "dest_client": None,
            "dest_instance": None
        }
        self.destination_client = None
        self.destination_agent = None
        self.destination_instance = None
        self.destination_machine_object = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log.info(
            "%(boundary)s %(message)s %(boundary)s",
            {
                'boundary': "*" * 10,
                'message': "Initialize helper and SDK objects"
            }
        )
        self.machine_object = machine.Machine(self.client)
        self.destination_client = self.commcell.clients.get(self.tcinputs["dest_client"])
        self.destination_agent = self.destination_client.agents.get('Oracle')
        self.destination_instance = self.destination_agent.instances.get(self.tcinputs['dest_instance'])
        self.oracle_helper_source = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_destination = OracleHelper(self.commcell, self.destination_client,
                                                      self.destination_instance)
        self.log.info('creation of oracle helper object for source and destination succeeded.')
        self.log.info('CS set to %s', self.commcell)
        self.destination_machine_object = machine.Machine(self.destination_client)

    def restore_validation(self, expected_row_count, backup_jobid,
                           replication_jobid, isbaselinerestore):
        """Method to run validation on oracle database after replication job is complete

                Args:
                    expected_row_count  (int) -- The row count expected on table after replication

                    backup_jobid    (int)-- The jobid of the backup job on source

                    replication_jobid   (int)-- The jobid of replication job triggered by backup

                    isbaselinerestore   (boolean)-- True if the replication job is baseline
                                                        replication, False for sync restores

                Returns:
                        None

                Raises:
                        Exceptions:

                        1. If database was opened in any other state other than RAED ONLY
                        2. If we dont get the expected row count on table after replication
                        3. If we dont find the next SCN of backup job being used for recovery
                        4. If we dont find the expected RMAN commands in the restore script
                        """

        # Step:1 Connect to destination database and check if it was opened in READ ONLY mode
        self.log.info("Performing validation on destination database")
        self.oracle_helper_destination.db_connect(OracleHelper.CONN_SYSDBA)
        self.log.info("Connected to destination database")

        destination_database_status = self.oracle_helper_destination.get_db_status()
        self.log.info('DB Status: %s', destination_database_status)

        if destination_database_status != 'READ ONLY':
            self.log.exception('Database status after restore is invalid: %s',
                               destination_database_status)
            raise ValueError('Invalid status for destination database: {0}'.format
                             (destination_database_status))
        else:
            self.log.info("Step:1 successful- Database is opened in READ ONLY mode")

        # Step:2 On the destination, switch to created user and fetch number of columns
        number_of_rows_created = self.oracle_helper_destination.\
            db_table_validate("c##cv_user_54471", "cv_5447101")
        if number_of_rows_created != expected_row_count:
            self.log.info(" table validation after replication failed ")
            raise Exception("Table validation failed after replication job")
        else:
            self.log.info("Step:2 successful- Table validation passed")

        # Step:3 Get the RMAN script and compare if the latest SCN was used for recovery
        next_scn = str(self.oracle_helper_source.get_next_scn(backup_jobid))
        rman_restore_log = str(self.oracle_helper_destination.fetch_rman_log(
            replication_jobid, self.destination_client, 'restore')).lower()
        if rman_restore_log.find(next_scn) > 0:
            self.log.info("Step:3 successful- Found the expected SCN in RMAN restore log")
        else:
            raise Exception("Did not find the expected SCN")

        # Step:4 Get RMAN script and check the following:
        # if job was a baseline restore, check if RMAN script had the following statements:
        # 1. restore controlfile  2. restore database
        # if job was a sync restore, check if RMAN script had the following statements:
        # 1. configure channel 2. catalog device type

        if isbaselinerestore is True:

            if (rman_restore_log.find("restore controlfile") > 0 and rman_restore_log.find
                    ("restore database") > 0) and rman_restore_log.find(backup_jobid) > 0:
                self.log.info("Step:4 successful- Found the expected "
                              "statements in RMAN script after baseline restore")
            else:
                raise Exception("RMAN log validation after baseline restore failed")

        else:
            if (rman_restore_log.find("configure channel") > 0 and rman_restore_log.find
                    ("catalog device type") > 0) and rman_restore_log.find(backup_jobid) > 0:
                self.log.info("Step:4 successful- Found the expected "
                              "statements in RMAN script after sync restore")
            else:
                raise Exception("RMAN log validation after sync restore failed")

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Creating oracle user, table and populating data before backup")
            # Connect to source Oracle database and check if database is UP/OPEN
            self.oracle_helper_source.db_connect(OracleHelper.CONN_SYSDBA)
            self.log.info("connected to source database")
            source_database_status = self.oracle_helper_source.get_db_status()
            self.log.info('DB DBID: %s', self.instance.dbid)
            self.log.info('DB Status: %s', source_database_status)
            self.log.info('DB Version: %s', self.oracle_helper_source.ora_version)

            if source_database_status != 'READ WRITE':
                self.log.exception('Database status is invalid: %s', source_database_status)
                raise ValueError('Invalid status for source database: {0}'.format
                                 (source_database_status))

            # create user and table and populate with 10 records
            self.log.info("Creaing users on source")
            self.oracle_helper_source.db_create_user('cv_user_54471', 'USERS')
            self.oracle_helper_source.db_create_table('USERS', 'cv_54471', 'c##cv_user_54471', 1)
            self.log.info('Successfully Created table and populated data')

            # create live sync schedule, full backup will be run before creation
            self.log.info("Running baseline backup and then creating live sync schedule")
            full_bkp_obj = self.instance.create_live_sync_schedule(self.tcinputs['dest_client'],
                                                    self.tcinputs['dest_instance'], 'CV_schedule_54471')
            self.log.info("Created live sync configuration successfully")
            self.log.info("Trying to get the baseline replication Job ID")
            baseline_restore = self.oracle_helper_source.get_replication_job(full_bkp_obj)

            if not baseline_restore.wait_for_completion():
                raise Exception(
                    "Failed to run baseline replication job with error: {0}".format(
                        baseline_restore.delay_reason
                    )
                )
            self.log.info("Baseline replication job: %s completed", baseline_restore.job_id)
            self.log.info("Running validation after baseline restore/replication")
            self.restore_validation(10, full_bkp_obj.job_id, baseline_restore.job_id, True)

            # Insert more data and run incremental backup
            self.log.info("Inserting more data before running incremental backup")
            self.oracle_helper_source.db_populate_table('cv_54471', 'c##cv_user_54471')
            incr_bkp_obj = self.subclient.backup(backup_level='incremental')
            if not incr_bkp_obj.wait_for_completion():
                self.log.info(
                    "Backup JOB ID: %s", incr_bkp_obj.job_id)
                raise Exception(
                    "Failed to run incremental backup job with error: {0}".format
                    (incr_bkp_obj.delay_reason))

            number_of_rows_created = (
                self.oracle_helper_source.db_table_validate("c##cv_user_54471", "cv_5447101"))
            if number_of_rows_created != 20:
                self.log.info("Expected number of rows not inserted into table")
                raise Exception("Expected number of rows not inserted into table")
            self.log.info("Trying to get the sync restore/replication Job ID")
            sync_restore = self.oracle_helper_source.get_replication_job(incr_bkp_obj)
            if not sync_restore.wait_for_completion():
                raise Exception(
                    "Failed to run sync restore job with error: {0}".format(
                        sync_restore.delay_reason
                    )
                )

            # Run validataion after sync restore
            self.restore_validation(20, incr_bkp_obj.job_id,
                                    sync_restore.job_id, False)
            self.log.info("validations passed , test case completed successfully")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = exp
            self.status = constants.FAILED

    def tear_down(self):
        self.log.info("Tear Down Function")
        self.log.info("Cleanup the tables created during test case run")
        # Drop the tables created during TC run
        try:
            self.oracle_helper_source.db_drop_table("c##cv_user_54471", "cv_5447101")
        except Exception as exp:
            self.log.error("Clean up failed")