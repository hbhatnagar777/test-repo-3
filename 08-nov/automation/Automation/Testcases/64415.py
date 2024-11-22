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

    create_instance() --  Method to create sybase instance

    create_helper_object() --  Method to create sybase helper object

    prepare_instance() --    Method to prepare the instance for backup and restore

    run_backup() --      Method to run backup

    run_restore()  --    Method to run restore

    run()           --  run function of this test case

    teardown()      --  teardown function of this test case
"""

import sys
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils import idautils
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper



class TestCase(CVTestCase):
    """Class for executing Sybase Cumulative Incremental Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Encrypted Database Acceptance Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB64415"
        self.instance_name=None
        self.instance=None
        self.default_subclient=None
        self.tcinputs={
            'sybase_options':
                {
                'instance_name':None,
                'sybase_ocs': None,
				'sybase_ase': None,
				'backup_server': None,
				'sybase_home': None,
				'config_file': None,
				'enable_auto_discovery': None,
				'shared_memory_directory': None,
				'storage_policy': None,
				'sa_username': None,
				'sa_password': None,
				'localadmin_username': None,
				'localadmin_password': None,
				'masterkey_password': None
                },
            'AgentName': None,
            'ClientName': None,
            'Keys': None

        }

    def setup(self):
        """Setup function of this test case"""


        self.common_utils_object = idautils.CommonUtils(self.commcell)
    def create_instance(self):
        """Creates Sybase Instance"""
        self.log.info("Started executing encrypted database acceptance testcase: %s", self.id)
        self.instance_name = self.agent.instances.add_sybase_instance(
            sybase_options=self.tcinputs["sybase_options"])
        self.log.info("Instance Creation Succeeded")

    def create_helper_object(self,instance_name):
        """Creates Sybase Helper object"""
        self.instance=self.agent.instances.get(instance_name)
        self.sybase_helper = SybaseHelper(self.commcell, self.instance, self.client)
        self.sybase_helper.csdb = self.csdb
        self.log.info("creation of sybase helper succeeded.lets create sybase cv helper object")
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)
        # Setting Sybase Instance user password
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()

    def prepare_instance(self,user_table_list):
        """Prepares instance for backup and restore operations"""
        self.log.info("Creating Database")
        self.sybase_cv_helper.sybase_populate_data(self.database_name, user_table_list[0])
        self.log.info("Enabling encryption for db")
        self.sybase_helper.enable_encryption_for_db(self.database_name, self.tcinputs["Keys"][1])
        cumulative_status = self.sybase_helper.set_cumulative(self.database_name)
        self.log.info("Cumulative Status for database %s is %s", self.database_name,cumulative_status)
        self.default_subclient = self.sybase_helper.instance.subclients.get(subclient_name="default")
    def run_backup(self,backup_type,data=None):
        """Method to Run backup
            Args:
                backup_type  (str)  : Can be full/TL/cum
                data         (str)  : Table name to populate data within an existing database

            Returns:
                  job_end_time (str) : End time of job
                  table_list   (list) : List of tables available in a given database
        """
        if backup_type == 'full':
            self.log.info("Full Backup")
            full_job = self.sybase_cv_helper.backup_and_validation(self.default_subclient, 'full', syntax_check=True,
                                                                   db=[self.database_name])
            job_end_time = self.sybase_cv_helper.get_end_time_of_job(full_job)
            status,table_list = self.sybase_helper.get_table_list(self.database_name)
            self.sybase_cv_helper.encrypted_db_backup_syntax(full_job.job_id, keys=self.tcinputs["Keys"])
            self.log.info("Full Job End time : %s", job_end_time)
            self.log.info("Status of fetching full table list:%s",status)

        elif backup_type == 'TL':
            self.log.info("Add test table before next transaction Log backup to user database")
            self.sybase_cv_helper.single_table_populate(self.database_name,data)
            self.log.info("Transaction Log Backup")
            tl_job = self.sybase_cv_helper.backup_and_validation(self.default_subclient, 'incremental',
                                                                  syntax_check=True,
                                                                  db=[self.database_name])
            job_end_time = self.sybase_cv_helper.get_end_time_of_job(tl_job)
            self.log.info("TL Job End time : %s", job_end_time)
            status,table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("Status of fetching cumulative table list : %s", status)

        else:
            self.log.info("Add test table before cumulative backup")
            self.sybase_cv_helper.single_table_populate(self.database_name,data)
            self.log.info("Cumulative Backup")
            cum_job = self.sybase_cv_helper.backup_and_validation(self.default_subclient, 'differential',
                                                                  syntax_check=True,
                                                                  db=[self.database_name])
            job_end_time = self.sybase_cv_helper.get_end_time_of_job(cum_job)
            self.log.info("Cumulative Job End time : %s", job_end_time)
            status,table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("Status of fetching transaction log table list : %s", status)
        return job_end_time,table_list

    def run_restore(self,restore_type,user_table_list,restore_time=None,expected_table_list=None):
        """Method to run Restore
           Args:
               restore_type  (str)        : Can be userdb or Full
               user_table_list  (list)    : List of user tables created
               restore_time    (str)      : for pointintime based restore
                                            format: YYYY-MM-DD HH:MM:SS
                                            default : None
               expected_table_list (list) : expected list of tables
                                            for given user database
                                            default : None
            Returns :
                status (bool)            : True if restore completes, False if it fails or goes to pending

        """
        if restore_type == "userdb":
            self.log.info(
                "Restoring database %s to end time of cumulative job : %s",self.database_name,time)

            status = self.sybase_cv_helper.single_database_restore(
                database_name=self.database_name,
                user_table_list=user_table_list,
                expected_table_list=expected_table_list,
                timevalue=restore_time)
        else:
            self.log.info("Running Full Server Restore")
            status = self.sybase_cv_helper.sybase_full_restore(self.database_name, user_table_list)
            time.sleep(120)
        return status

    def run(self):
        """Main function for test case execution"""

        try:
            user_table_list = ["T64415_FULL", "T64415_TL1", "T64415_CUM", "T64415_TL2"]
            self.create_instance()
            self.create_helper_object(self.instance_name)
            self.prepare_instance(user_table_list)
            self.run_backup(backup_type='full')
            time.sleep(120)
            self.run_backup(backup_type='TL',data=user_table_list[1])
            time.sleep(120)
            cum_job_end_time,cum_table_list = self.run_backup(backup_type='cum',data=user_table_list[2])
            time.sleep(120)
            self.run_backup(backup_type='TL',data=user_table_list[3])
            time.sleep(120)
            restore_status = self.run_restore(restore_type="userdb",user_table_list=user_table_list[:3],
                                            expected_table_list=cum_table_list,restore_time=cum_job_end_time)
            time.sleep(120)
            self.run_backup(backup_type='full')
            time.sleep(120)
            self.run_backup(backup_type='TL', data=user_table_list[3])
            restore_status_2 = self.run_restore(restore_type="Full",user_table_list=user_table_list[:4])
            time.sleep(120)
            if restore_status and restore_status_2:
                self.log.info("Sybase Encypted database Acceptance Test case succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                raise Exception("Failed to run restore job with error %s", restore_status)

        except Exception as exp:
            self.log.error("Testcase failed with exception : %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.sybase_cv_helper.sybase_cleanup_test_data(self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
        self.instance.delete()
