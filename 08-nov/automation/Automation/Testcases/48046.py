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

    run()           --  run function of this test case

    teardown()      --  teardown function of this test case
"""
import sys
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils import machine
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper

class TestCase(CVTestCase):
    """Class for executing Sybase Log Backup to Disk"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Log Backup to Disk Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.database_name = "DB48046"
        self.machine_object = None
        self.tcinputs = {
            "dump_directory": None
        }


    def setup(self):
        """Setup function of this test case"""

        self.sybase_helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.sybase_helper.csdb = self.csdb
        self.log.info(
            "creation of sybase helper succeeded."
            " and create sybase cv helper object")
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)

        # Setting Sybase Instance user password
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()

        self.machine_object = machine.Machine(self.client)

    def run(self):
        """Main function for test case execution"""
        user_table_list = ["T48046_FULL", "T48046_TL1", "T48046_TL2"]
        try:
            # this testcase is applicable only for unix clients
            if "windows" in self.client.os_info.lower():
                raise Exception("Log backup to disk testcase 48046 is"
                                "applicable only for Unix sybase clients")

            # Generate test data
            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_table_list[0])

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # subclient creation with user database
            self.subclient = self.sybase_cv_helper.create_sybase_subclient(self.database_name,
                                                                           storage_policy,
                                                                           [self.database_name])

            # setting transaction log stream to 2
            self.subclient.transaction_log_stream = 2
            self.log.info("Transaction Log streams : %s", self.subclient.transaction_log_stream)

            # set registry key at client level
            self.client.add_additional_setting("SybaseAgent",
                                               "sDiskDumpDir",
                                               "STRING",
                                               self.tcinputs["dump_directory"])

            # Commvault instance ID on client
            cv_instance = self.client.instance

            # Full backup of given user database
            self.log.info("Full Backup")
            full_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'full')
            self.log.info("First Full Backup completed: %s", full_job.job_id)
            time.sleep(120)

            # Add test table[change 1] to user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_table_list[1])

            # Launching first log backup to disk
            self.sybase_helper.log_backup_to_disk(self.database_name, cv_instance)
            time.sleep(120)

            # Add another test table[change 2] to user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_table_list[2])

            # Launching second log backup to disk
            self.sybase_helper.log_backup_to_disk(self.database_name, cv_instance)
            time.sleep(120)

            # Launch transaction log backup TL1
            self.log.info("First Transaction Log Backup : TL1")
            tl1_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental')
            self.log.info("First Transaction Log Backup completed: %s", tl1_job.job_id)
            time.sleep(120)
            status, tl1_table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("Status of getting table list "
                          "after transaction log backup 1 : %s", status)

            # Run restore to end time of transaction log backup
            self.log.info(
                "Restoring database %s to latest point in time",
                self.database_name)
            restore_status = self.sybase_cv_helper.single_database_restore(
                database_name=self.database_name,
                user_table_list=user_table_list,
                expected_table_list=tl1_table_list)
            self.log.info("Sybase Log backup to disk Test case succeeded : %s ", restore_status)
            self.log.info("Test Case Passed")
        except Exception as exp:
            self.log.error("Testcase failed with exception : %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.sybase_cv_helper.sybase_cleanup_test_data(self.database_name)
        self.instance.subclients.delete(self.database_name)
        subclient = self.instance.subclients.get("default")
        self.sybase_cv_helper.sybase_delete_database_from_subclient(subclient, self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
        self.client.delete_additional_setting("SybaseAgent", "sDiskDumpDir")
        path = self.machine_object.join_path(self.tcinputs["dump_directory"], "*")
        self.machine_object.remove_directory(path)
