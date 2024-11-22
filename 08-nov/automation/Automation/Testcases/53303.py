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

    setup()         --  Creates all the helper objects required for the test case to run

    run()           --  PIT Restore from log only snap backup preceding snap backups
"""
import datetime
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "PIT Restore from log only snap backup preceding snap backups"
        self.oracle_helper = None
        self.subclient1 = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 53303 is incomplete"
        self.tcinputs = {
            "SnapEngine": None
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
        self.subclient = self.oracle_helper.create_subclient("53303_DataLog", storage_policy,
                                                             self.tcinputs['SnapEngine'], 2,
                                                             True, True, False, 0, False)

        ###### Create Subclient for the Snap backup content = Log #######
        self.subclient1 = self.oracle_helper.create_subclient("53303_Log", storage_policy,
                                                              self.tcinputs['SnapEngine'], 2,
                                                              False, True, False, 0, False)

    def run(self):
        """Main function for test case execution"""

        try:
            ts_name = 'CV_53303'
            user = "{0}_user".format(ts_name.lower())
            table_limit = 1
            num_of_files = 1
            row_limit = 10

            self.oracle_helper.create_sample_data(ts_name, table_limit, num_of_files)
            self.oracle_helper.db_execute('alter system switch logfile')
            self.log.info(' STEP 1: Logfile switch complete...')

            ##########################################################################
            self.log.info(
                " STEP 1: Running full backup on database : %s from data+log subclient",
                self.instance.instance_name)
            self.oracle_helper.launch_backup_wait_to_complete(self.subclient, r"full")

            # populating table with 10 more records
            self.oracle_helper.db_populate_table("CV_TABLE_", user, 1)

            ##########################################################################
            self.log.info(
                " STEP 2: Running full backup on database : %s from log only subclient",
                self.instance.instance_name)
            self.oracle_helper.launch_backup_wait_to_complete(self.subclient1, r"full")

            # populating table with 10 more records
            self.oracle_helper.db_populate_table("CV_TABLE_", user, 1)

            ##########################################################################
            self.log.info(
                " STEP 3: Running full backup on database : %s from log only subclient",
                self.instance.instance_name)
            self.oracle_helper.launch_backup_wait_to_complete(self.subclient1, r"full")

            # populating table with 10 more records
            self.oracle_helper.db_populate_table("CV_TABLE_", user, 1)

            ##########################################################################
            self.log.info(
                " STEP 4: Running full backup on database : %s from log only subclient",
                self.instance.instance_name)

            pit_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            self.oracle_helper.launch_backup_wait_to_complete(self.subclient1, r"full")

            # populating table with 10 more records
            self.oracle_helper.db_populate_table("CV_TABLE_", user, 1)

            ##########################################################################

            browse_option = {
                "timeRange": {
                    "toTimeValue": pit_time
                }
            }

            time = {"timeValue": pit_time}
            oracle_opts = {"recoverTime": time, "restoreTime": time}

            self.log.info("Waiting for the restore job to start")

            self.log.info(
                "Running instance level snap restore from full snap backup on database: %s",
                self.instance.instance_name)

            # Performs an instance level snap full restore
            job = self.instance.restore(
                destination_client=self.client.client_name,
                destination_instance=self.instance.instance_name, files=None, browse_options=browse_option,
                common_options=None,
                oracle_options=oracle_opts, tag="SNAP")
            if not job.wait_for_completion():
                raise Exception("Failed to run restore job with error: {0}"
                                .format(job.delay_reason))

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                "CV_TABLE_01",
                5 * row_limit)

            self.status = constants.PASSED
            self.result_string = "Run of test case 53303 has completed successfully"
        except Exception as exp:
            self.log.error("""Testcase failed with exception : %s""", exp)
            raise
