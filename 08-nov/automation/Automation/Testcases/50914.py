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
                                    end time once job completes

    navigate_to_instance()      --  navigates to specified instance

    navigate_to_entity_action() --  navigates to database group tab performs action on the provided entity

    create_database_group()     --  creates database group/subclient in MySQL Client

    create_test_data()          -- method to generate test data

    delete_subclient()          -- deletes the testcase created subclient

    check_if_subclient_exists() -- to check subclient existence after delete operation

    restore_validate()          --  method to perform restore and validation of data restored

    backup_and_restore()        -- method to perform backup and restore

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "50914": {
                    "ClientName": "mysql",
                    "InstanceName":"mysql_1_3306",
                    "Port": "3306",
                    "Plan": "CS_PLAN",
                    "AgentName":"MySQL",
                    "Subclientname":"dummy_subclient"
                }
            }
"""

import ast
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.Instances.add_subclient import AddMySQLSubClient


class TestCase(CVTestCase):
    """ Class for executing restore data from deleted subclient testcase for MySQL IDA on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Restore data from deleted subclient"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.helper_object = None
        self.restore_panel = None
        self.db_subclient = None
        self.db_group_content = None
        self.instance_name = None
        self.subclient = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "Port": None,
            "Plan": None,
            "Subclientname": None
        }
        self.page_container = None
        self.table = None
        self.db_list = None

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
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.db_subclient = MySQLSubclient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.table = Rtable(self.admin_console)
        connection_info = {
            'client_name': self.client.client_name,
            'instance_name': self.instance.instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        self.helper_object = MYSQLHelper(commcell=self.commcell, hostname=self.client.client_hostname,
                                         user=self.instance.mysql_username,
                                         port=self.tcinputs["Port"], connection_info=connection_info
                                         )

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

        Returns:

            end_time    (str) -- Job end time

        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)
        end_time = time.strftime('%d-%B-%Y-%H-%M', time.localtime(time.mktime(time.strptime(
            time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(job_obj.summary['lastUpdateTime'])),
            '%d-%B-%Y-%I-%M-%p')) + 60))
        return end_time

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.tcinputs['InstanceName'],
                                                self.tcinputs['ClientName'])

    @test_step
    def navigate_to_entity_action(self, entity_name, action_item):
        """Navigates to MySQL Instance details page, clicks on 'Database groups' tab and
        performs action on the provided entity
        Args:
            entity_name (str)   :   Name of entity
            action_item (str)   :   Name of action item
        """
        self.log.info("Navigate to instance details page")
        self.navigate_to_instance()
        self.db_instance_details.access_actions_item_of_entity(
            entity_name=entity_name, action_item=action_item)
        self.admin_console.wait_for_completion()

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
    def delete_subclient(self):
        """Deletes the testcase created subclient"""
        self.navigate_to_instance()
        self.db_instance_details.click_on_entity(self.tcinputs["Subclientname"])
        self.db_subclient.delete_subclient()
        self.log.info("Subclient successfully deleted.")

    @test_step
    def check_if_subclient_exists(self):
        """To Check Subclient Existence After Deletion Operation"""
        self.navigate_to_instance()
        self.page_container.select_entities_tab()
        res = self.table.is_entity_present_in_column(column_name='Name', entity_name=self.tcinputs["Subclientname"])
        if res is True:
            raise Exception(f"### The subclient {self.tcinputs["Subclientname"]} still exists ### ")
        else:
            self.log.info("Subclient successfully deleted. The subclient no longer exists")

    @test_step
    def restore_validate(self, db_info):
        """Executes restore according to restore type input and validates restore
            db_info         (dict): Dictionary of database content before restore for validation
        """
        self.log.info("Data + Log Restore from Deleted SubClient")
        job_id = self.restore_panel.in_place_restore(data_restore=True, log_restore=True)
        self.wait_for_job_completion(job_id)
        db_info_after_restore = self.helper_object.get_database_information()
        self.helper_object.validate_db_info(db_info, db_info_after_restore)

    @test_step
    def backup_and_restore(self):
        """
        Executes backup and restore of the subclient
        """
        self.instance.refresh()
        self.subclient = self.instance.subclients.get(self.tcinputs['Subclientname'])
        self.log.info("Full Backup")
        job_id = self.db_subclient.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)

        self.helper_object.populate_database(subclient_content=self.db_list)
        self.log.info("Incremental Backup")
        job_id = self.db_subclient.backup(backup_type=RBackup.BackupType.INCR)
        end_time = self.wait_for_job_completion(job_id)

        db_info = self.helper_object.get_database_information()

        self.log.info("Deleting the subclient after full and incremental backups")
        self.delete_subclient()

        self.check_if_subclient_exists()
        self.helper_object.cleanup_test_data("auto")

        self.log.info("### Data + Log restore of deleted subclient content from recovery points ###")
        self.navigate_to_instance()
        self.db_instance_details.access_restore()
        self.restore_panel = self.db_subclient.restore_folders(
            DBInstances.Types.MYSQL, all_files=True, to_time=end_time)
        self.restore_validate(db_info=db_info)

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            self.log.info("Deleting the test created ")
            self.navigate_to_instance()
            self.page_container.select_entities_tab()
            subclient = self.table.is_entity_present_in_column(column_name='Name',
                                                               entity_name=self.tcinputs["Subclientname"])
            if subclient is True:
                self.delete_subclient()
        except Exception as e:
            self.log.info(e)
            pass

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_instance()
            self.admin_console.wait_for_completion()
            self.db_list = self.create_test_data('auto')
            self.create_database_group(self.db_list)
            self.backup_and_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
