# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  Creates a tablespace, user, table with records,
                        Performs Backup, Restore and Validate
                        adds more records - Performs SnapBackup and inline backupcopy ,
                        Restore from backupcopy  and Validate
"""
from time import sleep
from cvpysdk.job import Job
from AutomationUtils import constants
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle Snap Test Case - FS backup copy Restore"
        self.show_to_user = True
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 52842 is incomplete"
        self.tcinputs = {
            "SnapEngine": None,
            "browseOption": None,
            "OracleOptions": None,
            "commonOptions": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log.info('CS set to %s in test case: %s', self.commcell,
                      self.id)
        self.log.info("Initializing the pre-requisites for %s Test Case", self.id)
        self.log.info(
            "%(boundary)s %(message)s %(boundary)s",
            {
                'boundary': "*" * 10,
                'message': "Initialize helper objects"
            }
        )
        ######Establishing Client and Oracle Connection##########
        self.oracle_helper = OracleHelper(
            self.commcell, self.client, self.instance)
        self.oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)

        self.oracle_helper.check_instance_status()
        storage_policy = self.tcinputs.get("storage_policy",
                                           self.instance.subclients.get('default').storage_policy)

        ###### Create Subclient for the Snapbackup content  = Data + Log#######
        self.subclient = self.oracle_helper.create_subclient(
            "52842", storage_policy, self.tcinputs['SnapEngine'], 2, True, True, False, 0, False)

    def run(self):
        """Main function for test case execution"""

        try:

            self.log.info("Started executing %s Test Case", self.id)
            ts_name = 'CV_52842'
            table_limit = 1
            num_of_files = 1
            row_limit = 10

            self.oracle_helper.create_sample_data(ts_name, table_limit, num_of_files)

            self.oracle_helper.db_execute('alter system switch logfile')
            self.log.info(' STEP 1: Logfile switch complete...')

            self.log.info(" STEP 1: Running full backup on database: %s",
                          self.instance.instance_name)
            job = self.subclient.inline_backupcopy(r'full')
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL snap backup job with error: {0}".format(
                        job.delay_reason))
            self.log.info(" STEP 1: Full backup JOB ID: %s", job.job_id)

            # Retrieving the job id of the backup copy operation
            bc_job_id = CommonUtils(self.commcell).get_backup_copy_job_id(job.job_id)
            backupcopy_job = Job(self.commcell, bc_job_id)

            # wait for the backupcopy to finish before performing a restore
            if not backupcopy_job.wait_for_completion():
                raise Exception(
                    "Failed to run Backup copy job with error: {0}".format(
                        backupcopy_job.delay_reason))
            self.log.info("STEP 2: BACKUP COPY JOB ID: %s", backupcopy_job.job_id)

            # populating table with 10 more records
            self.oracle_helper.db_populate_table(
                "CV_TABLE_", "{0}_user".format(ts_name.lower()), table_limit)

            self.log.info("Waiting for the restore from backup copy job to start")

            self.log.info(
                "STEP 1: Running subclient level snap restore from full snap backup: %s",
                self.instance.instance_name)

            # Set Oracle Options for the Instance level Snap Restore
            # Restoring from the latest backup and recovering to the current time

            #job = self.instance.restore()
            # Performs an instance level snap full restore - All the tablespaces from
            # the latest backup are restored
 

            job = self.subclient.restore(
                destination_client=self.client.client_name,
                destination_instance=self.instance.instance_name,
                common_options=self.tcinputs['commonOptions'],
                browse_options=self.tcinputs['browseOption'],
                oracle_options=self.tcinputs['OracleOptions'], tag='SNAP')
            if not job.wait_for_completion():
                raise Exception("Failed to run restore job with error: {0}"
                                .format(job.delay_reason))

            self.log.info(" STEP 1: Full database snap restore JOB ID: %s", job.job_id)

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                "CV_TABLE_01",
                row_limit*2)
                
            

            self.status = constants.PASSED
            self.result_string = "Run of test case 52842 has completed successfully"
        except Exception as exp:
            self.log.error("""Testcase failed with exception : %s""", exp)
            self.result_string = "Run of test case 52842 failed"
            self.status = constants.FAILED
