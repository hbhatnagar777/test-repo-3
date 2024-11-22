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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    setup()         --  setup method for this test case

    create_instance()   --  method to perform SQL instance creation

    write_validation_data()     --  method to write data for validation

    tear_down()     --  tear down method for this test case

Input Example :

    "testCases": {
        "63094": {
            "Region": "AZURE_REGION",
            "BackupGateway": "BACKUP_GATEWAY_NAME",
            "CloudStorageAccount": "CLOUD_STORAGE_ACCOUNT",
            "CloudAccount": "CLOUD_ACCOUNT",
            "InstanceName": "AZURE_SQL_INSTANCE_NAME",
            "PlanName": "PLAN_NAME",
            "SQLServerUser": "AZURE_SQL_SERVER_ADMIN",
            "SQLServerPassword": "PASSWORD_FOR_ABOVE",
            "CredentialName": "CREDENTIAL_NAME",
            "StorageConnectionString": "AZURE_STORAGE_ACCOUNT_CONNECTION_STRING"
        }
    }

"""

import os
from AutomationUtils import constants
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Databases.db_instances import SQLInstance
from Web.AdminConsole.Databases.db_instance_details import MSSQLInstanceDetails
from Web.AdminConsole.Hub.constants import DatabaseTypes, HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.Databases.databases import RAzureSQLServerInstance
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL - Data Protection - Full Backup and Restore"

        self.browser = None
        self.admin_console = None
        self.hub_dashboard = None
        self.page_container = None
        self.wizard = None
        self.sql_instance = None
        self.sql_instance_details = None
        self.jobs = None

        self.sqlhelper = None
        self.sqlmachine = None
        self.list1 = None
        self.list2 = None
        self.list3 = None

        self.clientname = None
        self.instancename = None
        self.sqluser = None
        self.sqlpass = None
        self.planname = None
        self.region = None
        self.backup_gateway = None
        self.cloud_storage_account = None
        self.credential_name = None
        self.storage_connection_string = None

        self.tcinputs = {
            'Region': None,
            'BackupGateway': None,
            "CloudStorageAccount": None,
            'CloudAccount': None,
            'InstanceName': None,
            'SQLServerUser': None,
            'SQLServerPassword': None,
            'PlanName': None,
            'CredentialName': None,
            'StorageConnectionString': None
        }

    @test_step
    def setup(self):
        """ Method to setup test variables """

        self.region = self.tcinputs['Region']
        self.backup_gateway = self.tcinputs['BackupGateway']
        self.cloud_storage_account = self.tcinputs['CloudStorageAccount']
        self.planname = self.tcinputs["PlanName"]
        self.clientname = self.tcinputs["CloudAccount"]
        self.instancename = self.tcinputs["InstanceName"]
        self.sqluser = self.tcinputs["SQLServerUser"]
        self.sqlpass = self.tcinputs["SQLServerPassword"]
        self.credential_name = self.tcinputs["CredentialName"]
        self.storage_connection_string = self.tcinputs["StorageConnectionString"]

        self.log.info("*" * 10 + " Initialize SQLHelper objects " + "*" * 10)
        self.sqlhelper = SQLHelper(
            self,
            self.clientname,
            self.instancename,
            self.sqluser,
            self.sqlpass,
            _command_centre=True,
            _instance_exists=False
        )

        self.sqlhelper.sql_setup(noof_dbs=1)

        # get table shuffled list
        returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
            100,
            self.sqlhelper.noof_dbs,
            self.sqlhelper.noof_ffg_db,
            self.sqlhelper.noof_tables_ffg
        )
        self.list1, self.list2, self.list3 = list1, list2, list3

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.hub_dashboard = Dashboard(self.admin_console, HubServices.database, DatabaseTypes.azure)
        self.hub_dashboard.go_to_admin_console()
        self.admin_console.wait_for_completion()

        self.sql_instance = SQLInstance(self.admin_console)
        self.sql_instance_details = MSSQLInstanceDetails(self.admin_console)
        self.jobs = Jobs(self.admin_console)

    @test_step
    def create_instance(self):
        """Method for performing necessary actions to create an Azure SQL instance"""

        # navigate to DB Instances page
        self.admin_console.navigator.navigate_to_db_instances()

        # click on add new cloud instance
        self.page_container = PageContainer(self.admin_console)
        self.page_container.access_page_action(self.admin_console.props['pageHeader.addInstance'])
        self.page_container.access_page_action(self.admin_console.props['label.cloudDbService'])
        self.admin_console.wait_for_completion()

        self.wizard = Wizard(self.admin_console)
        self.wizard.select_radio_button(self.admin_console.props['label.vendor.azure_v2'])
        self.wizard.click_next()

        azure_sql_instance = RAzureSQLServerInstance(self.admin_console)
        azure_sql_instance.configure(
            self.region,
            self.backup_gateway,
            self.cloud_storage_account,
            self.planname,
            self.clientname,
            self.instancename,
            self.storage_connection_string,
            credentials=self.credential_name
        )

        self.admin_console.driver.refresh()
        self.sql_instance_details.add_subclient(self.sqlhelper, self.planname)

    @test_step
    def write_validation_data(self, filename, database_name, backup_type):
        """
        Method for writing database tables to file for validation purposes

        Args:
            filename (str):     Name of the file to write to

            database_name (str):    Name of the database to write

            backup_type (str):      Type of backup to be validated

        """
        # write the original database to file for comparison
        self.sqlhelper.dbvalidate.dump_db_to_file(
            os.path.join(self.sqlhelper.tcdir, filename),
            database_name,
            self.list1,
            self.list2,
            self.list3,
            backup_type
        )

    def run(self):
        """Main function for test case execution"""

        try:
            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            self.log.info("Started executing {0} testcase".format(self.id))
            self.create_instance()
            self.write_validation_data(sqldump_file1, self.sqlhelper.dbname, 'Full')

            self.sql_instance = SQLInstance(self.admin_console)
            self.sql_instance_details = MSSQLInstanceDetails(self.admin_console)
            self.jobs = Jobs(self.admin_console)

            # run full backup
            bkp_jobid = self.sql_instance.sql_backup(
                self.instancename,
                self.sqlhelper.subclient.name,
                'Full',
                client=self.clientname
            )
            bkp_jdetails = self.jobs.job_completion(bkp_jobid)
            if not bkp_jdetails['Status'] == 'Completed':
                raise Exception("Backup job {0} did not complete successfully".format(bkp_jobid))

            # delete all databases on destination
            if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
                self.log.error("Unable to drop the database")

            # run restore in place job
            self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            rst_jobid = self.sql_instance.sql_restore(
                self.instancename,
                self.sqlhelper.subcontent,
                'In Place',
                destination_instance=self.instancename,
                access_node=self.backup_gateway,
                staging_path=self.sqlhelper.tcdir
            )

            rst_jdetails = self.jobs.job_completion(rst_jobid)
            if not rst_jdetails['Status'] == 'Completed':
                raise Exception("Restore job {0} did not complete successfully".format(bkp_jobid))

            # write the restored database to file for comparison
            self.write_validation_data(sqldump_file2, self.sqlhelper.dbname, 'Full')

            # compare original and restored databases
            self.log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                        os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.sqlhelper.sql_teardown(delete_instance=True)
