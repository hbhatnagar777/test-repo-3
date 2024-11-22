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
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case

    tear_down()                 --  Tear down function for this testcase

    create_mysql_helper_object()--  Creates object of SDK mysqlhelper class

    restore_validate()          --  Executes restore according to restore type input and validates restore

    backup_and_restore()        --  Executes backup and restore of the subclient

    run()                       --  run function of this test case

"testCases":
            {
                "41778": {
                    "ClientName": "mysql",
                    "InstanceName":"mysql_1_3306",
                    "DatabaseUser": "root",
                    "Port": "3306",
                    "SubclientName": "default"
                    "AgentName": "MySQL",
                    "DestClientName":"mysql_2",
                    "DestInstanceName":"mysql_2_3306"
                }
            }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing Recurring Restore to Cross Machine"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MySql Logs - Recurring Restore to Cross Machine"
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "DatabaseUser": None,
            "Port": None,
            "SubclientName": None,
            "AgentName": None,
            "DestClientName": None,
            "DestInstanceName": None
        }
        self.source_helper_object = None
        self.dest_helper_object = None
        self.dbhelper_object = None
        self.auto_discovery = None
        self.flag = None

    def setup(self):
        """Setup function of this test case"""
        self.dbhelper_object = DbHelper(self.commcell)

    def create_mysql_helper_object(self, client_name, instance_name):
        """Creates object of SDK mysqlhelper class"""
        connection_info = {
            'client_name': client_name,
            'instance_name': instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        if client_name is self.tcinputs["ClientName"]:
            self.source_helper_object = MYSQLHelper(commcell=self.commcell, hostname=client_name,
                                                    user=self.tcinputs["DatabaseUser"],
                                                    port=self.tcinputs["Port"],
                                                    connection_info=connection_info)
        else:
            self.dest_helper_object = MYSQLHelper(commcell=self.commcell, hostname=client_name,
                                                  user=self.tcinputs["DatabaseUser"],
                                                  port=self.tcinputs["Port"],
                                                  connection_info=connection_info)

    def restore_validate(self, data_restore, log_restore, recurring_restore, db_info=None):
        """Executes restore according to restore type input and validates restore
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            recurring_restore  (Boolean): Checks recurring restore option
            db_info  (dict): Dictionary of database content before restore for validation
        """
        if db_info is None:
            raise Exception("database information needed to validate the data after restore")
        self.subclient.refresh()
        paths = self.subclient.content.copy()
        if '\\mysql' in paths:
            paths.remove('\\mysql')
        if '\\sys' in paths:
            paths.remove('\\sys')
        self.log.debug(paths)

        job = self.instance.restore_out_of_place(path=paths, dest_client_name=self.tcinputs['DestClientName'],
                                                 dest_instance_name=self.tcinputs['DestInstanceName'],
                                                 data_restore=data_restore, log_restore=log_restore,
                                                 recurringRestore=recurring_restore
                                                 )
        self.log.info("Started restore with Job ID: %s", job.job_id)
        self.dbhelper_object.wait_for_job_completion(job.job_id)
        db_info_after_restore = self.dest_helper_object.get_database_information()
        self.source_helper_object.validate_db_info(db_info, db_info_after_restore)

    def backup_and_restore(self):
        """
                Executes backup and restore of the subclient
        """
        self.log.info("Checking if MySql Binary Logging is enabled or not")
        self.source_helper_object.log_bin_on_mysql_server()
        self.log.info("MySql Binary Logging is enabled")

        self.auto_discovery = self.instance.autodiscovery_enabled
        if self.auto_discovery is False:
            self.flag = 0
            self.log.info("Auto discovery is not enabled for the subclient")
            self.instance.autodiscovery_enabled = True
            self.log.info("Auto discovery is enabled for the subclient")
        else:
            self.log.info("Auto discovery is enabled for the subclient")

        self.log.info("Creating subclient object for subclient content")

        self.source_helper_object.generate_test_data("auto")

        self.log.info("Full Backup")
        self.dbhelper_object.run_backup(self.subclient, 'FULL')

        db_info_after_full_bkp = self.source_helper_object.get_database_information()
        self.log.info("Running Out of Place Restore for Data + Log + Recurring")
        self.restore_validate(data_restore=True, log_restore=True, recurring_restore=True,
                              db_info=db_info_after_full_bkp)

        count = 1
        while count < 3:
            self.log.info("Populating Data and running Incremental Backup")
            self.source_helper_object.generate_test_data(f"auto_incr{count}")
            self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')
            db_info_after_incr_bkp = self.source_helper_object.get_database_information()
            self.log.info("Running Out of Place Restore for Log + Recurring")
            self.restore_validate(data_restore=False, log_restore=True, recurring_restore=True,
                                  db_info=db_info_after_incr_bkp)
            count += 1

    def tear_down(self):
        """ tear down method for testcase """
        if self.flag == 0:
            self.instance.autodiscovery_enabled = False
        self.source_helper_object.cleanup_test_data("auto")
        self.dest_helper_object.cleanup_test_data("auto")

    def run(self):
        """Run function for test case execution"""
        try:
            self.create_mysql_helper_object(self.tcinputs["ClientName"], self.tcinputs["InstanceName"])
            self.create_mysql_helper_object(self.tcinputs["DestClientName"], self.tcinputs["DestInstanceName"])
            self.backup_and_restore()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)

