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
    __init__()                              --  Initialize TestCase class

    setup()                                 --  Setup method for test case

    wait_for_job_completion()               --  Waits for job completion

    wait_for_active_jobs()                  --  Waits for any active jobs to finish for the client

    configure_db_from_hub()                 --  Configures SQL from Metallic Hub

    redirect_to_admin_console_from_hub()    --  Redirects to admin console from Metallic Hub

    navigate_to_instance_page()             --  Navigates to instance details page

    impersonate_user_for_sql()              --  Impersonates user for SQL Instance

    create_sqlhelper_object()               --  Creates and sets up sqlhelper object

    create_subclient()                      --  Creates subclient from Admin Console

    delete_dbs_before_restore()             --  Deletes db before running in-place restore

    dump_db_to_file()                       --  Dumps database to file for comparison

    backup()                                --  Runs full backup

    restore()                               --  Runs restore-in-place

    validate_restore()                      --  Validates restored dbs

    run()                                   --  Run function of this test case

"""

import os
from datetime import datetime
from cvpysdk.commcell import Commcell
from cvpysdk.job import Job
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.vmoperations import HyperVOperations
from Application.SQL.sqlhelper import SQLHelper
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.constants import DatabaseTypes
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances, SQLInstance
from Web.AdminConsole.Databases.db_instance_details import MSSQLInstanceDetails
from Web.AdminConsole.Hub.Databases.databases import DatabasesMetallic


class TestCase(CVTestCase):
    """Class for executing basic acceptance test for SQL Metallic onboarding, backup and restore"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_Databases_MSSQL_Acceptance"

        self.tenant_mgmt = None
        self.company_name = None
        self.company_email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.jobs = None

        self.sqlhelper = None
        self.sql_metallic = None
        self.sql_instance = None
        self.db_instance = None
        self.db_instance_details = None

        self.clientname = None
        self.instancename = None
        self.sqluser = None
        self.sqlpass = None

        self.planname = None

        self.hyperv = None

        self.tcinputs = {
            'DBServerName': None,
            'MachineUsername': None,
            'MachinePassword': None,

            'StorageAccount': None,
            'CloudProvider': None,
            'Region': None,

            'SQLInstanceName': None,
            'SQLImpersonateUser': None,
            'SQLImpersonatePassword': None,
            'SQLServerUser': None,
            'SQLServerPassword': None,

            'HyperVServer': None,
            'HyperVUserName': None,
            'HyperVPassword': None,
            'HyperVVMName': None,
            'HyperVSnapName': None
        }

    def setup(self):
        """Setup function for the testcase"""
        self.instancename = self.tcinputs["SQLInstanceName"]
        self.sqluser = self.tcinputs["SQLServerUser"]
        self.sqlpass = self.tcinputs["SQLServerPassword"]
        self.hyperv = HyperVOperations(self.tcinputs["HyperVServer"],
                                       self.tcinputs["HyperVUserName"],
                                       self.tcinputs["HyperVPassword"]
                                       )
        self.tenant_mgmt = HubManagement(self, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.company_name = datetime.now().strftime("MSSQL-Automation-%d-%B-%H-%M")
        self.company_email = datetime.now().strftime(f"mssql%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.company_email)
        self.tenant_pswrd = get_config().Metallic.tenant_password

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd)
        self.commcell = Commcell(self.commcell.webconsole_hostname,
                                 self.tenant_username,
                                 self.tenant_pswrd)

        self.sql_metallic = DatabasesMetallic(self.admin_console, DatabaseTypes.sql)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for job completion
        Args:
            jobid       (str)   :       Job ID
        """
        job_details = self.jobs.job_completion(jobid)
        if not job_details['Status'] == 'Completed':
            raise Exception(f"Job {jobid} did not complete successfully")
        self.log.info("Job {0} completed successfully!!".format(jobid))

    @test_step
    def wait_for_active_jobs(self):
        """Waits for any active job to complete for this client"""
        active_jobs = self.commcell.job_controller.active_jobs(self.clientname)
        self.log.info("Active jobs for the client:%s", active_jobs)
        if active_jobs:
            for job in active_jobs:
                if active_jobs[job]['status'] == 'Pending':
                    Job(self.commcell, job).resume()
                Job(self.commcell, job).wait_for_completion()
        else:
            self.log.info("No Active Jobs found")

    @test_step
    def configure_db_from_hub(self):
        """Completes the configuration of SQL from Metallic Hub"""
        install_inputs = {
            "remote_clientname": self.tcinputs["DBServerName"],
            "remote_username": self.tcinputs["MachineUsername"],
            "remote_userpassword": self.tcinputs["MachinePassword"],
            "os_type": "windows",
            "username": self.tenant_username,
            "password": self.tenant_pswrd,
        }
        cloud_storage_inputs = {
            "StorageAccount": self.tcinputs["StorageAccount"],
            "CloudProvider": self.tcinputs["CloudProvider"],
            "Region": self.tcinputs["Region"]

        }
        plan_inputs = {
            "RetentionPeriod": "1 month"
        }
        self.log.info("*" * 10 + " Started configuring the SQL Database Server from Metallic Hub " + "*" * 10)

        self.planname = self.sql_metallic.configure_database(
            commcell=self.commcell,
            install_inputs=install_inputs,
            cloud_storage_inputs=cloud_storage_inputs,
            use_existing_plan=False,
            plan_inputs=plan_inputs
            )
        self.planname = self.company_name + '-' + self.planname

    @test_step
    def redirect_to_admin_console_fom_hub(self):
        """Redirects to Admin Console from Metallic Hub"""
        self.log.info("*" * 10 + "Redirecting to Admin Console " + "*" * 10)
        self.sql_metallic.redirect_to_admin_console()
        self.admin_console.wait_for_completion()

    @test_step
    def navigate_to_instance_page(self):
        """Navigates to db instance details page"""
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.tcinputs["DBServerName"])
        self.clientname = self.client.client_name
        agent = self.client.agents.get("SQL Server")
        self.instance = agent.instances.get(self.instancename)

        self.navigator = self.admin_console.navigator
        self.jobs = Jobs(self.admin_console)
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(DBInstances.Types.MSSQL,
                                         self.instancename,
                                         self.tcinputs["DBServerName"])
        self.db_instance_details = MSSQLInstanceDetails(self.admin_console)

    @test_step
    def impersonate_user_for_sql(self):
        """Impersonates SQL user from Instance Details Page"""
        self.log.info("*" * 10 + " Impersonating user for SQL using credential manager" + "*" * 10)

        if not self.db_instance_details.impersonate_user_with_cred_manager(
                self.tcinputs["SQLImpersonateUser"],
                self.tcinputs["SQLImpersonatePassword"],
                self.id):
            raise CVTestStepFailure("Impersonation failed")

        self.log.info("*" * 10 + " Impersonation Successful " + "*" * 10)

    @test_step
    def create_sqlhelper_object(self):
        """Creates sqlhelper object"""
        self.sqlhelper = SQLHelper(self,
                                   self.clientname,
                                   self.instancename,
                                   self.sqluser,
                                   self.sqlpass,
                                   _command_centre=True)
        self.sqlhelper.sql_setup(noof_dbs=2)

    @test_step
    def create_subclient(self):
        """Creates new subclient and assigns it to TC object"""
        self.log.info("*" * 10 + " Creating new subclient " + "*" * 10)
        self.db_instance_details.click_add_subclient(DBInstances.Types.MSSQL).add_subclient(
            self.sqlhelper,
            self.planname)
        self.subclient = self.sqlhelper.subclient
        self.log.info("*" * 10 + "Subclient created successfully " + "*" * 10)

    @test_step
    def delete_dbs_before_restore(self):
        """Deletes dbs from SQL Instance before running restore job"""
        self.log.info("*" * 10 + " Deleting dbs before running restore in place " + "*" * 10)
        if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
            self.log.error("Unable to drop the database")

    @test_step
    def get_random_dbnames_and_filegroups(self):
        """Returns the values required to dump the db"""
        # get table shuffled list
        returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
            100,
            self.sqlhelper.noof_dbs,
            self.sqlhelper.noof_ffg_db,
            self.sqlhelper.noof_tables_ffg
        )
        if not returnstring:
            raise CVTestStepFailure("Error in while generating the random number.")
        return list1, list2, list3

    @test_step
    def dump_db_to_file(self, file_name, list1, list2, list3):
        """Dumps db to file for comparison"""
        if not self.sqlhelper.dbvalidate.dump_db_to_file(
                os.path.join(self.sqlhelper.tcdir, file_name),
                self.sqlhelper.dbname,
                list1,
                list2,
                list3,
                'FULL'
        ):
            raise CVTestStepFailure("Failed to write database to file.")

    @test_step
    def backup(self):
        """Performs the backup operation"""
        self.wait_for_active_jobs()
        self.log.info("*" * 10 + " Starting full backup job " + "*" * 10)
        bkp_jobid = self.sql_instance.sql_backup(self.instancename, self.subclient.name, "Full")
        self.wait_for_job_completion(bkp_jobid)
        self.log.info("*" * 10 + " Full backup finished successfully " + "*" * 10)

    @test_step
    def restore(self):
        """Performs the restore in place operation"""
        self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        self.admin_console.refresh_page()
        self.log.info("*" * 10 + " Page Refreshed " + "*" * 10)
        rst_jobid = self.sql_instance.sql_restore(self.instancename,
                                                  self.sqlhelper.subcontent,
                                                  "In Place")
        self.wait_for_job_completion(rst_jobid)
        self.log.info("*" * 10 + " Restore finished successfully " + "*" * 10)

    @test_step
    def validate_restore(self, dump_file1, dump_file2):
        """Validates the restore job by comparing source and restored dumped db files
        Args:
            dump_file1      (str)       :       Dump file of source db
            dump_file2      (str)       :       Dump file of restored db
        """
        self.log.info("*" * 10 + " Validating content " + "*" * 10)
        if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, dump_file1),
                                                    os.path.join(self.sqlhelper.tcdir, dump_file2)):
            raise CVTestStepFailure("Failed to compare both files.")
        self.log.info("*" * 10 + " Validation successful " + "*" * 10)

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            self.hyperv.revert_snapshot(self.tcinputs["HyperVVMName"], self.tcinputs["HyperVSnapName"])
            self.hyperv.power_on_vm(self.tcinputs["HyperVVMName"])

            self.configure_db_from_hub()
            self.redirect_to_admin_console_fom_hub()

            self.navigate_to_instance_page()
            self.impersonate_user_for_sql()

            self.create_sqlhelper_object()
            self.create_subclient()

            # write the original database to file for comparison
            list1, list2, list3 = self.get_random_dbnames_and_filegroups()
            self.dump_db_to_file(sqldump_file1, list1, list2, list3)

            self.sql_instance = SQLInstance(self.admin_console)
            self.backup()
            self.delete_dbs_before_restore()
            self.restore()

            # write the restored database to file for comparison
            self.dump_db_to_file(sqldump_file2, list1, list2, list3)

            # compare original and restored databases
            self.validate_restore(sqldump_file1, sqldump_file2)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.tenant_mgmt.deactivate_tenant(self.tenant_username)
            self.tenant_mgmt.delete_tenant(self.tenant_username)
            self.sqlhelper.sql_teardown()
            self.hyperv.power_off_vm(self.tcinputs["HyperVVMName"])
