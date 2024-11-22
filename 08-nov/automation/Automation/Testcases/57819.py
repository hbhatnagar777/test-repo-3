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

    add_instance()              --  add new postgreSQL instance

    create_test_data()          --  creates test databases for automation

    create_database_group()     --  creates database group in backupset

    delete_operations()         --  deletes test created subclients and instances

    check_unix_user_name()      --  checks if unix user name edit/display working as expected

    delete_instance_if_exists() --  deletes the instance if already exists

    tear_down()                 --  tear down method for testcase

    run()                       --  run function of this test case

Input Example:
    "testCases":
        {
            "57819":
                    {
                        "ClientName":"pgtestunix",
                        "DatabaseUser":"postgres",
                        "DatabasePassword":"postgres",
                        "DatabasePort":"5532",
                        "BinaryDirectory":"/usr/pgsql-10/bin",
                        "LibraryDirectory":"/usr/pgsql-10/lib",
                        "ArchiveLogDirectory":"/var/lib/pgsql/10/wal",
                        "Plan": "db2plan"
                    }
        }

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset


class TestCase(CVTestCase):
    """ Class for executing Instance and subclient creation/Deletion testcase for PostgreSQL """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Instance and subclient creation/Deletion testcase for PostgreSQL"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'DatabaseUser': None,
            'DatabasePassword': None,
            'DatabasePort': None,
            'BinaryDirectory': None,
            'LibraryDirectory': None,
            'ArchiveLogDirectory': None,
            'Plan': None}
        self.postgres_database_object = None
        self.database_instances = None
        self.instance_name = None
        self.db_instance_details = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.client = self.commcell.clients.get(self.tcinputs['ClientName'])
        self.postgres_database_object = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.tcinputs['DatabasePort'],
            self.tcinputs['DatabaseUser'],
            self.tcinputs['DatabasePassword'],
            "postgres")
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.instance_name = self.tcinputs['ClientName'] + "_" + self.tcinputs['DatabasePort']

    @test_step
    def add_instance(self):
        """add new postgreSQl instance"""
        self.database_instances.add_postgresql_instance(
            self.tcinputs['ClientName'],
            self.instance_name,
            self.tcinputs['Plan'],
            self.tcinputs['DatabaseUser'],
            self.tcinputs['DatabasePassword'],
            self.tcinputs['DatabasePort'],
            self.tcinputs['BinaryDirectory'],
            self.tcinputs['LibraryDirectory'],
            self.tcinputs['ArchiveLogDirectory'],
            maintenance_db="postgres")

    @test_step
    def create_test_data(self):
        """creates test databases for automation"""
        self.postgres_database_object.create_db("dummy_database_1")
        self.postgres_database_object.create_db("dummy_database_2")

    @test_step
    def create_database_group(self):
        """creates database group/subclient in dumpbased backupset"""
        self.db_instance_details.click_on_entity('DumpBasedBackupSet')
        postgres_backupset = PostgreSQLBackupset(self.admin_console)
        postgres_backupset.add_subclient(
            "dummy_subclient", 4, True,
            self.tcinputs['Plan'], ['dummy_database_1', 'dummy_database_2'])
        return postgres_backupset

    @test_step
    def delete_operations(self, postgres_backupset):
        """deletes test created subclient/database group and instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES, self.instance_name, self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('DumpBasedBackupSet')
        postgres_backupset.delete_subclient(subclient_name="dummy_subclient")
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES, self.instance_name, self.tcinputs['ClientName'])
        self.db_instance_details.delete_instance()

    @test_step
    def check_unix_user_name(self):
        """method to check if unix user edit and display in instance is working"""
        self.db_instance_details.unix_user = 'check'
        if not self.db_instance_details.unix_user == "check":
            raise CVTestStepFailure("Unix user displayed is not correct")
        self.log.info("Unix user validation success")

    @test_step
    def delete_instance_if_exists(self):
        """deletes the instance if it already exists"""
        self.navigator.navigate_to_db_instances()
        if self.database_instances.is_instance_exists(DBInstances.Types.POSTGRES, self.instance_name, self.tcinputs['ClientName']):
            self.database_instances.select_instance(
                DBInstances.Types.POSTGRES, self.instance_name, self.tcinputs['ClientName'])
            PostgreSQLInstanceDetails(self.admin_console).delete_instance()

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting automation generated databases")
        self.postgres_database_object.drop_db("dummy_database_1")
        self.postgres_database_object.drop_db("dummy_database_2")


    def run(self):
        """ Main function for test case execution """
        try:
            self.delete_instance_if_exists()
            self.add_instance()
            self.log.info("Waiting for 5 mins for automatic backup to finish")
            time.sleep(300)
            if "unix" in self.client.os_info.lower():
                self.check_unix_user_name()
            self.create_test_data()
            postgres_backupset = self.create_database_group()
            self.delete_operations(postgres_backupset)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
