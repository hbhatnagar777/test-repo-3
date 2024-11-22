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

    create_mysql_helper_object()--  method to create object of SDK mysqlhelper class

    delete_instance_if_exists() --  method to delete the instance if exists

    delete_subclient()          --  method to delete the subclient

    add_instance()              --  method to add new instance

    create_test_data()          --  method to generate test data

    create_database_group()     --  creates database group/subclient in MySQL Client

    validate_plan()             --  method to update and validate the storage policy of instance and subclient

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "47513": {
                    "ClientName": "mysql",
                    "Port": "3306",
                    "Plan": "CS_PLAN",
                    "DatabaseUser":"root",
                    "DatabasePassword":"Database_password",
                    "BinaryDirectory":"C:\\Program Files\\MySQL\\MySQL Server 8.4\\bin",
                    "LogDirectory":"E:\\MySQL\\Data",
                    "ConfigFile":"E:\\MySQL\\my.ini",
                    "Subclientname":"mysql_subclient",
                    "PlanNameForValidation":"MySQL_Plan",
                    "SocketFile": "/var/lib/mysql/mysql.sock",  (optional, for unix client),
                    "UnixUsername": "username",                 (optional, for unix client)
                    "NTUsername": "username",                   (optional, for windows client)
                    "NTPassword": "password",                   (optional, for windows client)
                    "XtraBackup": ""                            (optional)
                }
            }
"""
import ast
import time
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Databases.Instances.add_subclient import AddMySQLSubClient
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails


class TestCase(CVTestCase):
    """ Class for executing Instance and subclient creation/deletion testcase for MySQL IDA on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Instance and subclient creation/deletion testcase for MySQL"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.tcinputs = {
            "ClientName": None,
            "Port": None,
            "Plan": None,
            "DatabaseUser": None,
            "DatabasePassword": None,
            "BinaryDirectory": None,
            "LogDirectory": None,
            "ConfigFile": None,
            "Subclientname": None,
            "PlanNameForValidation": None
        }
        self.dialog = None
        self.instance_name = None
        self.helper_object = None
        self.db_subclient = None

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.instance_name = self.tcinputs["ClientName"] + "_" + str(self.tcinputs["Port"])
        self.db_subclient = MySQLSubclient(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")

    @test_step
    def create_mysql_helper_object(self):
        """Creates object of SDK mysqlhelper class"""
        connection_info = {
            'client_name': self.client.client_name,
            'instance_name': self.instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        self.helper_object = MYSQLHelper(commcell=self.commcell,
                                         hostname=self.client.client_hostname,
                                         user=self.tcinputs['DatabaseUser'],
                                         port=self.tcinputs["Port"],
                                         connection_info=connection_info)

    @test_step
    def delete_instance_if_exists(self):
        """method to delete the instance if exists"""
        self.navigator.navigate_to_db_instances()
        if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL, self.instance_name,
                                                      self.tcinputs['ClientName']):
            self.database_instances.select_instance(
                DBInstances.Types.MYSQL, self.instance_name, self.tcinputs['ClientName'])
            MySQLInstanceDetails(self.admin_console).delete_instance()
        else:
            self.log.info(f"Instance {self.instance_name} doesnt exists")

    @test_step
    def delete_subclient(self):
        """Deletes the subclient"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.instance_name,
                                                self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity(self.tcinputs["Subclientname"])
        self.db_subclient.delete_subclient()
        self.log.info("Subclient successfully deleted.")

    @test_step
    def add_instance(self):
        """method to add new instance"""
        unix = "windows" not in self.client.os_info.lower()
        self.database_instances.add_mysql_instance(
            server_name=self.tcinputs["ClientName"],
            instance_name=self.instance_name,
            plan=self.tcinputs["Plan"],
            database_user=self.tcinputs["DatabaseUser"],
            password=self.tcinputs["DatabasePassword"],
            unix=unix,
            unix_username=self.tcinputs.get("UnixUsername"),
            nt_username=self.tcinputs.get('NTUsername'),
            nt_password=self.tcinputs.get('NTPassword'),
            xtra_backup_bin_path=self.tcinputs.get('XtraBackup'),
            socketfile_directory=self.tcinputs.get("SocketFile"),
            binary_directory=self.tcinputs["BinaryDirectory"],
            log_directory=self.tcinputs["LogDirectory"],
            config_directory=self.tcinputs["ConfigFile"],
            port=self.tcinputs["Port"])
        self.log.info("Instance successfully created")
        self.admin_console.wait_for_completion()

    @test_step
    def create_test_data(self, prefix):
        """Creates test databases according to input
            returns:    list of names of databases created
        """
        timestamp = str(int(time.time()))
        if self.tcinputs.get("TestData"):
            if isinstance(self.tcinputs["TestData"], str):
                num_of_db, num_of_tables, num_of_rows = ast.literal_eval(self.tcinputs["TestData"])
            else:
                num_of_db, num_of_tables, num_of_rows = self.tcinputs["TestData"]
            db_list = self.helper_object.generate_test_data(prefix + "_" + timestamp,
                                                            num_of_db, num_of_tables, num_of_rows)
        else:
            db_list = self.helper_object.generate_test_data(
                database_prefix=prefix + "_" + timestamp)
        return db_list

    @test_step
    def create_database_group(self, db_list):
        """creates database group/subclient in MySQL Client
        Args:
            db_list (List): List of databases to be added to the subclient
        """
        self.db_instance_details.click_add_subclient(DBInstances.Types.MYSQL)
        add_subclient = AddMySQLSubClient(self.admin_console)
        add_subclient.add_subclient(subclient_name=self.tcinputs["Subclientname"],
                                    number_backup_streams=2,
                                    database_list=db_list,
                                    plan=self.tcinputs['Plan'])
        self.admin_console.wait_for_completion()

    @test_step
    def validate_plan(self, isinstance_validation=True):
        """method to Updating and validate the STORAGE POLICY in MySQL Instance and subclient
        Args:
            isinstance_validation (bool)  : If the validation is for an instance
                default : True
        """
        if isinstance_validation:
            self.db_instance_details.click_on_edit()
            self.dialog.select_dropdown_values(values=[self.tcinputs["PlanNameForValidation"]],
                                               drop_down_id='planDropdown')
            self.dialog.click_submit()
            self.admin_console.wait_for_completion()
            instance_details = self.db_instance_details.get_instance_details()
            if instance_details['Plan'] == self.tcinputs["PlanNameForValidation"]:
                self.log.info("### Plan validation for instance is successful ###")
            else:
                raise CVTestStepFailure("Unable to modify MySQL Instance details")
        else:
            panel_info = RPanelInfo(self.admin_console, title='Protection summary')
            panel_info.edit_tile()
            self.dialog.select_dropdown_values(values=[self.tcinputs["PlanNameForValidation"]],
                                               drop_down_id='editPlan')
            self.dialog.click_submit()
            subclient_info = panel_info.get_details()
            if subclient_info['Plan'] == self.tcinputs["PlanNameForValidation"]:
                self.log.info("### Plan validation for subclient is successful ###")
            else:
                raise CVTestStepFailure("Unable to modify MySQL Subclient details")

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            self.log.info("Deleting the test created Instance")
            self.delete_instance_if_exists()

        except Exception as e:
            self.log.info(e)
            pass

    def run(self):
        """ Main function for test case execution """
        try:
            self.delete_instance_if_exists()
            self.add_instance()
            self.validate_plan()
            self.create_mysql_helper_object()
            db_list = self.create_test_data('auto')
            self.create_database_group(db_list)
            self.validate_plan(isinstance_validation=False)
            self.log.info("Deleting the test created Subclient")
            self.delete_subclient()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
