# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    run()                       --  run function of this test case

    database_setup()            --  connects to the database and creates sample data

    backup_and_validate()       --  Connects to the database and creates sample data

    alter_data()                --  Adds tables prior to incremental job

    restore_and_validate()      --  Runs command line restore and performs validation

    delete_data()               --  Deletes data before the restore job

Input Example:

    "testCases":
            {
                "5024":
                        {
                          "ClientName":"client",
                          "AgentName":"oracle",
                          "InstanceName":"instance",
                          "RMAN_Script": ["Path to Full backup rman script", "Path to incremental backup
                                            rman script","Path to rman script to shutdown and startup
                                            database in mount mode", "Path to restore rman script"],
                           "Oracle_user":"oracle_user",
                           "Oracle_password":"oracle_password",
                           "Client_hostname":"client_hostname"
                        }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.OracleUtils.oraclehelper import OracleHelper
from AutomationUtils.machine import Machine
from AutomationUtils import constants



class TestCase(CVTestCase):
    """ Class for executing Command Line acceptance Test for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle Command Line Backups ACCT"
        self.tablespace_name = 'CV_5024'
        self.tcinputs = {
            'RMAN_Script': None,
            'Oracle_user': None,
            'Oracle_password': None,
            'Client_hostname':None
        }
        self.oracle_helper_object = None
        self.machine = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.machine = Machine( self.tcinputs['Client_hostname'],username=self.tcinputs['Oracle_user'],
                               password=self.tcinputs['Oracle_password'])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)

    @test_step
    def database_setup(self):
        """
            Connects to the database and creates sample data
        """
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)

        self.oracle_helper_object.create_sample_data(
            self.tablespace_name, 1, 1)
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.log.info("Test Data Generated successfully")

    @test_step
    def backup_and_validate(self, backup_type, script_index):
        """
            Run Command Line Backups & validate the backup
            Arguments:
                backup_type:    Type of backup_type to be run
                    accepted: FULL, INCREMENTAL
                script_index:   The list index of rman_script to pick rman script path for commandline backup job
        """
        self.log.info("Starting {0} Backup".format(backup_type))
        oracle_home = self.oracle_helper_object.oracle_home
        oracle_instance = self.instance.instance_name
        data = {
            'oracle_home': oracle_home,
            'oracle_sid': oracle_instance,
            'remote_file': self.tcinputs['RMAN_Script'][script_index]
        }
        self.machine.execute_script(constants.UNIX_ORACLE_RMAN_RECOVER,
                                    data)

        jobs = self.commcell.job_controller.finished_jobs(client_name=self.client.client_name,
                                                          entity={"instanceName": self.instance.instance_name,
                                                                  "subclientName": "(command line)"})

        val = jobs[list(jobs.keys())[0]]
        if val['operation'] == 'Application Command Line Backup' and val['status'] == 'Completed' and val[
            'backup_level'] == backup_type:
            self.log.info("Oracle {0} Backup is validated".format(backup_type))
        else:
            raise Exception("Command Line Backup Failed")

    @test_step
    def alter_data(self):
        """
            Adds tables prior to incremental job
        """
        user = "{0}_user".format(self.tablespace_name.lower())
        self.oracle_helper_object.db_create_table(
            self.tablespace_name, "CV_TABLE_INCR_", user, 1)

    @test_step
    def delete_data(self):
        """
            Deletes data before the restore job
        """
        oracle_home = self.oracle_helper_object.oracle_home
        oracle_instance = self.instance.instance_name
        data = {
            'oracle_home': oracle_home,
            'oracle_sid': oracle_instance,
            'remote_file': self.tcinputs['RMAN_Script'][2]
        }
        location = self.oracle_helper_object.db_fetch_dbf_location()
        self.machine.execute_script(constants.UNIX_ORACLE_RMAN_RECOVER,
                                    data)
        self.machine.delete_file(self.machine.join_path(location, '{0}.dbf'.format(self.tablespace_name)))
        self.machine.delete_file(self.machine.join_path(location, '{0}1.dbf'.format(self.tablespace_name)))

    @test_step
    def restore_and_validate(self):
        """
            Runs command line restore and performs validation
        """
        oracle_home = self.oracle_helper_object.oracle_home
        oracle_instance = self.instance.instance_name
        self.log.info("Starting Oracle Restore")
        data = {
            'oracle_home': oracle_home,
            'oracle_sid': oracle_instance,
            'remote_file': self.tcinputs['RMAN_Script'][3]
        }

        self.machine.execute_script(constants.UNIX_ORACLE_RMAN_RECOVER,
                                    data)
        self.log.info("Validating content")
        self.oracle_helper_object.validation(self.tablespace_name, 1,
                                             "CV_TABLE_01", 10)
        self.oracle_helper_object.validation(self.tablespace_name, 1,
                                             "CV_TABLE_INCR_01", 10)
        self.log.info("Validation Successfull.")

    def run(self):
        """ Main function for test case execution """
        try:
            self.database_setup()
            self.backup_and_validate('Full', 0)
            self.alter_data()
            self.backup_and_validate('Incremental', 1)
            self.delete_data()
            self.restore_and_validate()

        except Exception as exp:
            handle_testcase_exception(self, exp)