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

    setup()         --  setup function for this test case

    run()           --  run function of this test case
"""

import os
from AutomationUtils import constants
from Application.CloudApps.Spanner.spannerhelper import SpannerHelper
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instances import SpannerInstance
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Google Cloud Spanner: configuration,
    backup and restore test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Google Cloud Spanner - Instance list backup and restore"

        self.browser = None
        self.admin_console = None
        self.database_instances = None
        self.cc_spanner_instance = None
        self.jobs = None

        self.spanner_helper = None
        self.instance_name = None
        self.cloud_account = None
        self.spanner_account_id = None
        self.spanner_key = None
        self.plan_name = None

        self.tcinputs = {
            "PlanName",
            "CloudAccount",
            "SpannerInstanceName",
            "SpannerKeyJSON"
        }

    def setup(self):
        """ Method to setup test variables """

        self.cloud_account = self.tcinputs["CloudAccount"]
        instance_name = self.tcinputs["SpannerInstanceName"]
        self.spanner_account_id = self.tcinputs["SpannerAccountID"]
        self.spanner_key = self.tcinputs["SpannerKeyJSON"]

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.database_instances = DBInstances(self.admin_console)
        self.cc_spanner_instance = SpannerInstance(self.admin_console)
        self.jobs = Jobs(self.admin_console)

        self.log.info("*" * 10 + " Initialize SpannerHelper objects " + "*" * 10)
        self.spanner_helper = SpannerHelper(
            self,
            instance_name,
            self.spanner_account_id,
            self.spanner_key,
            self.cloud_account
        )

    def run(self):
        """Main function for test case execution"""

        try:
            self.spanner_helper.spanner_setup(add_instance=True, add_subclient=True)
            spanner_dump_file1 = "before_backup_full.txt"
            spanner_dump_file2 = "after_restore.txt"

            self.spanner_helper.dump_database_to_file(spanner_dump_file1, self.spanner_helper.dbname + "1")
            self.subclient = self.spanner_helper.subclient

            self.log.info("*" * 10 + " Run Backup " + "*" * 10)
            self.admin_console.navigator.navigate_to_db_instances()

            bkp_jobid = self.database_instances.backup(
                self.instance.name.lower(),
                DBInstances.Types.SPANNER.value,
                self.subclient.name,
                RBackup.BackupType.FULL,
                client=self.cloud_account
            )

            self.admin_console.navigator.navigate_to_jobs()
            bkp_jdetails = self.jobs.job_completion(bkp_jobid)
            if not bkp_jdetails['Status'] == 'Completed':
                raise Exception("Backup job {0} did not complete successfully".format(bkp_jobid))

            # delete all databases
            if not self.spanner_helper.drop_databases(self.spanner_helper.dbname):
                self.log.error("Unable to drop the database")

            # run restore in place job
            self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            self.admin_console.navigator.navigate_to_db_instances()
            rst_jobid = self.cc_spanner_instance.spanner_restore(
                self.instance.name,
                self.spanner_helper.content_list,
                "In Place",
                client=self.cloud_account
            )

            rst_jdetails = self.jobs.job_completion(rst_jobid)
            if not rst_jdetails['Status'] == 'Completed':
                raise Exception("Restore job {0} did not complete successfully".format(bkp_jobid))

            # write the restored database to file for comparison
            self.spanner_helper.dump_database_to_file(spanner_dump_file2, self.spanner_helper.dbname + "1")

            # compare original and restored databases
            self.log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.spanner_helper.database_compare(
                    os.path.join(self.spanner_helper.tcdir, spanner_dump_file1),
                    os.path.join(self.spanner_helper.tcdir, spanner_dump_file2)
            ):
                raise Exception("Failed to compare both files.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.spanner_helper.spanner_teardown()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
