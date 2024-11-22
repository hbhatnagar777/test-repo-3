# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Application.SQL import sqlconstants
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL - Restore - To same paths"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATARECOVERY
        self.show_to_user = True

        self.sqlhelper = None
        self.sqlmachine = None

        self.tcinputs = {
            "SQLServerUser": None,
            "SQLServerPassword": None
        }

    def run(self):
        """Main function for test case execution"""

        log = self.log

        clientname = self.client.client_name
        instancename = self.instance.instance_name
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]
        self.sqlmachine = Machine(self.client)
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)

        try:

            log.info("Started executing {0} testcase".format(self.id))

            self.sqlhelper.sql_setup()
            self.subclient = self.sqlhelper.subclient

            # run a FULL backup
            job_id = self.sqlhelper.sql_backup('Full')
            
            # check backup level for Full
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of Full from CS db
            fullend = self.sqlhelper.get_sql_backup_end_time(job_id, timeformat="datestringformat")
            log.info("Job End time - " + fullend)

            # kill open db connections
            if not self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True):
                raise Exception("Unable to kill database connections")

            # run restore in place job - based on Full time.  Should fail with proper JPR
            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, timeout=1,
                                              job_delay_reason=sqlconstants.ERROR_OVERWRITE, to_time=fullend,
                                              overwrite=False):
                raise Exception("Restore was not successful!")

            # run restore in place job - based on Full time.  Should succeed and overwrite
            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=fullend):
                raise Exception("Restore was not successful!")

            # Checking if databases are online
            if not self.sqlhelper.dbvalidate.is_db_online(self.sqlhelper.dbname, self.sqlhelper.noof_dbs):
                raise Exception("Databases are not online.")

            log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        self.sqlhelper.sql_teardown()
