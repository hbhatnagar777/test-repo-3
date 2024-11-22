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

    wait_for_active_jobs()                  --  Waits for any active jobs to finish for the client

    configure_sql_db()                      --  Completes the initial configuration of SQL instance

    update_software()                       --  Updates installed client software to get latest changes

    disable_compliance_lock()               --  Disable compliance lock on storage pool to allow tenant deletion

    create_sqlhelper_object()               --  Creates and sets up sqlhelper object

    create_subclient()                      --  Creates subclient from Admin Console

    delete_dbs_before_restore()             --  Deletes db before running in-place restore

    dump_db_to_file()                       --  Dumps database to file for comparison

    backup()                                --  Runs full backup

    restore()                               --  Runs restore-in-place

    validate_restore()                      --  Validates restored dbs

    run()                                   --  Run function of this test case

Input Example :

    "testCases": {
              "64337": {
                    "DBServerName" : "SERVER_NAME",
                    "MachineUsername":"USER_NAME_OF_SERVER",
                    "MachinePassword":"PASSWORD_FOR_ABOVE_USER",

                    "CloudStorageLocation" : "CLOUD_STORAGE_LOCATION",

                    "StorageAccount":"STORAGE_ACCOUNT_IN_METALLIC",
                    "CloudProvider":"CLOUD_PROVIDER",
                    "Region":"REGION_NAME",

                    "SQLInstanceName" : "SQL_INSTANCE_NAME",
                    "SQLImpersonateUser": "SQL_USER_WITH_SYSADMIN_ACCESS_AND_LSA",
                    "SQLImpersonatePassword": "PASSWORD_FOR_ABOVE_USER",
                    "SQLServerUser" : "SA_USER_FOR_SQL",
                    "SQLServerPassword" : "PASSWORD_FOR_ABOVE_USER",

                    "HyperVServer":"HYPERV_SERVER_NAME",
                    "HyperVUserName":"HYPERV_USER",
                    "HyperVPassword":"PASSWORD_FOR_ABOVE_USER",
                    "HyperVVMName":"VM_NAME_IN_HYPERV",
                    "HyperVSnapName":"SNAPSHOT_NAME_IN_HYPERV"
                    }
            }

"""

import os
from datetime import datetime
from cvpysdk.commcell import Commcell
from cvpysdk.job import Job
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.vmoperations import HyperVOperations
from Application.SQL.sqlhelper import SQLHelper
from Install.update_helper import UpdateHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import DatabaseTypes, HubServices
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances, SQLInstance
from Web.AdminConsole.Databases.db_instance_details import MSSQLInstanceDetails
from Web.AdminConsole.Hub.Databases.databases import RMSSQLMetallic
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing basic acceptance test for SQL Metallic onboarding, backup and restore on linux servers"""

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
        self.hub_dashboard = None

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

        self.db_helper = None

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
        self.tenant_mgmt.delete_companies_with_prefix("MSSQL-Automation-")
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

        self.db_helper = DbHelper(self.commcell)

        self.sql_metallic = RMSSQLMetallic(self.admin_console)

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
    def configure_sql_db(self):
        """Completes the initial configuration of SQL instance"""
        install_inputs = {
            "remote_clientname": self.tcinputs["FQDN"],
            "remote_username": self.tcinputs["MachineUsername"],
            "remote_userpassword": self.tcinputs["MachinePassword"],
            "os_type": "unix",
            "username": self.tenant_username,
            "password": self.tenant_pswrd,
        }
        cloud_storage_inputs = {
            "cloud_vendor": self.tcinputs["StorageAccount"],
            "storage_provider": self.tcinputs["CloudProvider"],
            "region": self.tcinputs["Region"]
        }
        plan_inputs = {
            "RetentionPeriod": "1 month"
        }
        impersonate_user_inputs = {
            "SQLImpersonateUser": self.tcinputs["SQLImpersonateUser"],
            "SQLImpersonatePassword": self.tcinputs["SQLImpersonatePassword"]
        }
        self.log.info("*" * 10 + " Started configuring the SQL Database Server from Metallic Hub " + "*" * 10)

        self.hub_dashboard = Dashboard(self.admin_console, HubServices.database, DatabaseTypes.sql)
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.click_new_configuration()

        self.log.info("*" * 10 + " Rest of the configuration to be done from Command Centre " + "*" * 10)

        self.sql_metallic.select_on_prem_details(infrastructure="Virtual machine", app_type=DatabaseTypes.sql)

        self.planname = self.sql_metallic.configure_sql_db(
            commcell=self.commcell,
            cloud_storage_inputs=cloud_storage_inputs,
            plan_inputs=plan_inputs,
            install_inputs=install_inputs,
            impersonate_user_inputs=impersonate_user_inputs,
            use_existing_plan=False
        )

        self.disable_compliance_lock()

        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.tcinputs["FQDN"])
        self.clientname = self.client.client_name

        self.log.info("*" * 10 + " SQL server successfully added and at Instances page now " + "*" * 10)

        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(DBInstances.Types.MSSQL,
                                         self.instancename,
                                         self.tcinputs["DBServerName"])
        self.db_instance_details = MSSQLInstanceDetails(self.admin_console)

    @test_step
    def update_software(self):
        """Updates installed client software to get latest changes"""
        self.log.info("*" * 10 + " Updating client software " + "*" * 10)
        UpdateHelper(self.commcell, self.client).push_sp_upgrade([self.clientname])
        self.log.info("*" * 10 + "Client updated successfully " + "*" * 10)

    @test_step
    def disable_compliance_lock(self):
        """Disable compliance lock on the storage pool to allow for tenant deletion"""
        self.log.info("*" * 10 + " Disabling compliance lock " + "*" * 10)
        mm_helper = MMHelper(self)
        plan = self.commcell.plans.get(self.planname)
        storage_pool_id = mm_helper.get_copy_id(plan.storage_copies['Primary']['storagePool'], "Primary")
        if mm_helper.can_disable_compliance_lock(storage_pool_id):
            mm_helper.disable_compliance_lock(storage_pool_id)
            self.log.info("Successfully disabled compliance lock.")
        else:
            self.log.error("Failed to disable compliance lock. Continuing with test case")

    @test_step
    def create_sqlhelper_object(self):
        """Creates sqlhelper object"""
        agent = self.client.agents.get("SQL Server")
        self.instance = agent.instances.get(self.instancename)
        self.sqlhelper = SQLHelper(self,
                                   self.clientname,
                                   self.tcinputs["FQDN"],
                                   self.sqluser,
                                   self.sqlpass,
                                   _command_centre=True,
                                   _unix_os=True)
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
        bkp_jobid = self.sql_instance.sql_backup(self.instancename, self.subclient.name, "Full", os_type='unix')
        self.db_helper.wait_for_job_completion(bkp_jobid)
        self.log.info("*" * 10 + " Full backup finished successfully " + "*" * 10)

    @test_step
    def restore(self):
        """Performs the restore in place operation"""
        self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        self.admin_console.refresh_page()
        self.log.info("*" * 10 + " Page Refreshed " + "*" * 10)
        rst_jobid = self.sql_instance.sql_restore(self.instancename,
                                                  self.sqlhelper.subcontent,
                                                  "In Place",
                                                  os_type='unix')
        self.db_helper.wait_for_job_completion(rst_jobid)
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

            self.configure_sql_db()
            self.update_software()

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
            self.status = constants.PASSED

            self.tenant_mgmt.deactivate_tenant(self.tenant_username)
            self.tenant_mgmt.delete_tenant(self.tenant_username)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        self.sqlhelper.sql_teardown()
        self.hyperv.power_off_vm(self.tcinputs["HyperVVMName"])
