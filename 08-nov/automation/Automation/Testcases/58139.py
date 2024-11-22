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

    wait_for_job_completion()   --  Waits for completion of job and gets the
                                    end date once job completes

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    new_subclient()             --  creates new subclient with specified name
                                    and details

    create_mysql_helper_object()--  creates object of MYSQLHelper class

    create_test_data()          --  method to create test databases according to input

    create_instance()           --  method to delete existing instance and create new
                                    instance

    edit_instance_change_plane()--  method to edit instance to change plan set

Input Example:

    "testCases":
            {
                "58139": {
                    "ClientName": "mysql_client",
                    "Plan": "plan",
                    "NewPlan": "newplan",
                    "DBGroupPlan": "plan",
                    "DatabaseGroupName": "dbgroup",
                    "DatabaseUser": "username",
                    "DatabasePassword": "password",
                    "SocketFile": "/var/lib/mysql/mysql.sock",  (optional, for unix client)
                    "BinaryDirectory": "/usr/bin",
                    "LogDirectory": "/var/lib/mysql",
                    "ConfigFile": "/etc/my.cnf",
                    "UnixUsername": "username",                 (optional, for unix client)
                    "NTUsername": "username",                   (optional, for windows client)
                    "NTPassword": "password",                   (optional, for windows client)
                    "Port": 3306,
                    "XtraBackup": "",                           (optional)
                    "TestData": [10, 20, 100] (eg. [No. of Databases, No. of Tables, No. of Rows)
                     as list or string representation of list ie. "[10, 20, 100]"
                                                                (optional, default:[5,10,50])
                    "DeleteInstanceAfterTC": bool               (optional, default:False)
                }
            }

"""

import ast
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.panel import DropDown
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper


class TestCase(CVTestCase):
    """ Class for executing Test for MySQL Instance
     and subclient configuration from Command Center """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "MySQL Instance and subclient configuration from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.test_case = None
        self.helper_object = None
        self.database_group = None
        self.add_subclient = None
        self.browse = None
        self.panel_dropdown = None
        self.instance_name = None
        self.subclient_created = None
        self.tcinputs = {
            "ClientName": None,
            "Plan": None,
            "NewPlan": None,
            "DBGroupPlan": None,
            "DatabaseGroupName":None,
            "DatabaseUser": None,
            "DatabasePassword": None,
            "BinaryDirectory": None,
            "LogDirectory": None,
            "ConfigFile": None,
            "Port": None
        }

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open(maximize=True)
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)
        self.browse = Browse(self.admin_console)
        self.panel_dropdown = DropDown(self.admin_console)
        self.instance_name = self.tcinputs["ClientName"] + "_" + str(self.tcinputs["Port"])

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.instance_name,
                                                self.tcinputs["ClientName"])

    @test_step
    def add_instance(self):
        """Adds new instance"""
        unix = "windows" not in self.client.os_info.lower()
        self.database_instances.add_mysql_instance(server_name=self.tcinputs["ClientName"],
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
        self.admin_console.wait_for_completion()


    @test_step
    def new_subclient(self, database_list):
        """Adds new subclient"""
        self.log.info("Checking if database group already exists and delete if exists")
        self.db_instance_details.select_entities_tab()
        db_group_exists = self.admin_console.check_if_entity_exists('link',
                                                                    self.tcinputs['DatabaseGroupName'])
        if db_group_exists:
            self.db_instance_details.click_on_entity(self.tcinputs['DatabaseGroupName'])
            self.database_group.delete_subclient()
        self.log.info("Creating new database group")
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.MYSQL)
        self.add_subclient.add_subclient(subclient_name=self.tcinputs['DatabaseGroupName'],
                                         number_backup_streams=2, database_list=database_list,
                                         plan=self.tcinputs['DBGroupPlan'])
        subclient_created = True
        self.log.info("Database group created")
        if subclient_created:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.tcinputs['DatabaseGroupName'])
            self.admin_console.wait_for_completion()

    @test_step
    def create_mysql_helper_object(self):
        """Creates object of SDK mysqlhelper class"""
        connection_info = {
            'client_name': self.tcinputs["ClientName"],
            'instance_name': self.instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        self.helper_object = MYSQLHelper(commcell=self.commcell,
                                         hostname=self.tcinputs["ClientName"],
                                         user=self.tcinputs["DatabaseUser"],
                                         port=self.tcinputs["Port"],
                                         connection_info=connection_info)

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
            db_list = self.helper_object.generate_test_data(prefix+"_"+timestamp,
                                                            num_of_db,
                                                            num_of_tables,
                                                            num_of_rows)
        else:
            db_list = self.helper_object.generate_test_data(
                database_prefix=prefix + "_" + timestamp)
        return db_list

    @test_step
    def create_instance(self):
        """Checks if instance exists, if not, creates new instance"""
        self.log.info("Checking if instance exists")
        if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL,
                                                      self.instance_name,
                                                      self.tcinputs['ClientName']):
            self.log.info("Instance found, navigating to instance")
            self.admin_console.select_hyperlink(self.instance_name)
        else:
            self.log.info("Instance not found. Creating new instance")
            self.add_instance()
            self.log.info("Instance successfully created")

    @test_step
    def edit_instance_change_plan(self):
        """ Edits instance to change plan"""
        self.db_instance_details.edit_instance_change_plan(self.tcinputs["NewPlan"])
        self.log.info("Verifying plan has changed")
        instance_object = self.client.agents.get("MySQL").instances.get(self.instance_name)
        if instance_object.properties['mySqlInstance']['logStoragePolicy']['storagePolicyName']\
                == self.tcinputs["NewPlan"]:
            self.log.info("Plan successfully changed")
        else:
            raise Exception("Plan change failed")

    @test_step
    def verify_subclient_content(self, db_list):
        """ Compares subclient content with list of test databases created"""
        instance_object = self.client.agents.get("MySQL").instances.get(self.instance_name)
        subclient_content = instance_object.subclients.get(
            self.tcinputs["DatabaseGroupName"]).content.copy()
        content = []
        for database in subclient_content:
            if database.startswith('\\'):
                database = database.lstrip("\\")
            else:
                database = database.lstrip('/')
            content.append(database)
        if len(content) == len(db_list) and all(
                database in content for database in db_list):
            self.log.info("Subclient content validation successfull")
        else:
            raise Exception("Subclient content validation failed")

    def cleanup(self):
        """Cleans up testcase created changes"""
        if self.tcinputs.get("DeleteInstanceAfterTC") is not None and\
                bool(self.tcinputs.get("DeleteInstanceAfterTC")):
            self.navigate_to_instance()
            self.db_instance_details.delete_instance()
        elif self.subclient_created:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.tcinputs['DatabaseGroupName'])
            self.database_group.delete_subclient()

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.create_instance()
            self.edit_instance_change_plan()
            self.create_mysql_helper_object()
            db_list = self.create_test_data("auto")
            self.admin_console.refresh_page()

            self.new_subclient(db_list)
            self.verify_subclient_content(db_list)
            active_jobs = self.commcell.job_controller.active_jobs(
                client_name=self.tcinputs['ClientName'], job_filter="Backup")
            active_job = None
            for job in active_jobs:
                job_obj = self.commcell.job_controller.get(job)
                if job_obj.subclient_name == self.tcinputs['DatabaseGroupName']\
                        and job_obj.instance_name == self.instance_name:
                    active_job = job_obj
                    break
            if active_job:
                self.log.info("Found active job %s for subclient."
                              " Waiting for job to complete before"
                              " deleting subclient/instance", active_job.job_id)
                self.wait_for_job_completion(active_job.job_id)
            self.log.info("Test case execution completed successfully")
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
