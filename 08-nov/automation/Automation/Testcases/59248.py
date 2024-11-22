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

    run()                       --  run function of this test case

"""

import os
from AutomationUtils.cvtestcase import CVTestCase
from Application.SQL.sqlhelper import SQLHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import SQLInstance
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for SQL Command Center backup and restore """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL Command Center - Instance list backup and restore"
        self.browser = None
        self.admin_console = None
        self.sql_instance = None
        self.jobs = None

        self.sqlhelper = None
        self.sqlmachine = None

        self.clientname = None
        self.instancename = None
        self.sqluser = None
        self.sqlpass = None

        self.tcinputs = {
            'SQLServerUser': None,
            'SQLServerPassword': None
        }

    def setup(self):
        """ Method to setup test variables """

        self.clientname = self.client.client_name
        self.instancename = self.instance.instance_name
        self.sqluser = self.tcinputs["SQLServerUser"]
        self.sqlpass = self.tcinputs["SQLServerPassword"]

        self.log.info("*" * 10 + " Initialize SQLHelper objects " + "*" * 10)
        self.sqlhelper = SQLHelper(self, self.clientname, self.instancename, self.sqluser, self.sqlpass)
        self.sqlhelper.sql_setup(noof_dbs=2)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.sql_instance = SQLInstance(self.admin_console)
        self.jobs = Jobs(self.admin_console)

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100,
                self.sqlhelper.noof_dbs,
                self.sqlhelper.noof_ffg_db,
                self.sqlhelper.noof_tables_ffg
            )
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            self.subclient = self.sqlhelper.subclient

            # run full backup
            bkp_jobid = self.sql_instance.sql_backup(self.instancename, self.subclient.name, "Full")

            bkp_jdetails = self.jobs.job_completion(bkp_jobid)
            if not bkp_jdetails['Status'] == 'Completed':
                raise Exception("Backup job {0} did not complete successfully".format(bkp_jobid))

            if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3):
                self.log.info("Failed to modify database before taking log backups")

            # run log backup
            bkp_jobid = self.sql_instance.sql_backup(self.instancename, self.subclient.name, "Transaction_Log")

            bkp_jdetails = self.jobs.job_completion(bkp_jobid)
            if not bkp_jdetails['Status'] == 'Completed':
                raise Exception("Backup job {0} did not complete successfully".format(bkp_jobid))

            # write the original database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # delete all databases
            if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
                self.log.error("Unable to drop the database")

            # run restore in place job
            self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            rst_jobid = self.sql_instance.sql_restore(self.instancename, self.sqlhelper.subcontent, "In Place")

            rst_jdetails = self.jobs.job_completion(rst_jobid)
            if not rst_jdetails['Status'] == 'Completed':
                raise Exception("Restore job {0} did not complete successfully".format(bkp_jobid))

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'INCREMENTAL'):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            self.log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                        os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.sqlhelper.sql_teardown()
