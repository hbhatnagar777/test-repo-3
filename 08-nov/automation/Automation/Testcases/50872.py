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

    navigate_to_instance()      --  navigates to specified instance

    navigate_to_entity_action() --  navigates to database group tab performs action on the provided entity

    restore_validation()        --  method to perform restore and validation of data restored

    backup_and_restore()        -- method to perform backup and restore

    set_subclient_content()     -- method to set subclient content to test databases

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "50872": {
                    "ClientName": "mysql",
                    "InstanceName": "mysql_1_3306",
                    "Port": "3306",
                    "AgentName": "MySQL",
                    "SubclientName":"default"
                }
            }
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RModalDialog, RBackup
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing  testcase to verify restore from de-configured MySQL Instance on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'verify restore from de-configured MySQL Instance'
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.database_group = None
        self.db_group_content = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "Port": None,
            "SubclientName": None
        }
        self.page_container = None
        self.db_list = None
        self.helper_object = None
        self.dbhelper = None
        self.dialog = None
        self.restore_panel = None
        self.deconfigure = False

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
        self.database_group = MySQLSubclient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.dbhelper = DbHelper(self.commcell)
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

    @test_step
    def restore_validation(self, db_info):
        """
        method to perform restore and validation of data restored
        Args:
            db_info  (dict): Dictionary of database content before restore for validation
        """
        self.log.info("Data + Log Restore")
        job_id = self.restore_panel.in_place_restore(data_restore=True,
                                                     log_restore=True)
        self.dbhelper.wait_for_job_completion(job_id)
        db_info_after_restore = self.helper_object.get_database_information()
        self.helper_object.validate_db_info(db_info, db_info_after_restore)

    @test_step
    def backup_and_restore(self):
        """ method to perform backup and restore """
        self.log.info("Full Backup")
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.FULL)
        self.dbhelper.wait_for_job_completion(job_id)

        self.helper_object.populate_database(subclient_content=self.db_list)
        self.log.info("Incremental Backup")
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.INCR)
        self.dbhelper.wait_for_job_completion(job_id)

        self.subclient.refresh()
        content_to_restore = \
            [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]
             if db not in ['mysql', 'sys', 'information_schema', 'performance_schema', 'sakila', 'world']]

        db_info_after_bkp = self.helper_object.get_database_information()
        self.helper_object.cleanup_test_data('auto')

        self.log.info("De-configuring MySQL Instance")
        self.admin_console.select_breadcrumb_link_using_text(self.instance.instance_name)
        self.page_container.access_page_action('Deconfigure')
        self.dialog.click_yes_button()
        self.deconfigure = True

        self.admin_console.refresh_page()
        self.log.info("Checking if the Backup button is disabled after Deconfiguration")
        if self.page_container.check_if_page_action_item_exists('Backup'):
            raise CVTestStepFailure("### Backup button still exists. Validation Failed ###")
        else:
            self.log.info("### Backup button is disabled. Validation Successful ###")

        self.navigate_to_entity_action(self.subclient.subclient_name, "Restore")

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, items_to_restore=content_to_restore)
        self.restore_validation(db_info=db_info_after_bkp)

        self.navigate_to_instance()
        self.log.info("Re-configuring MySQL Instance")
        self.page_container.access_page_action('Reconfigure')
        self.dialog.click_yes_button()
        self.deconfigure = False

        self.admin_console.refresh_page()
        self.log.info("Checking if the Backup button is enabled after Reconfiguration")
        if self.page_container.check_if_page_action_item_exists('Backup'):
            self.log.info("### Backup button is enabled. Validation Successful ###")
        else:
            raise CVTestStepFailure("### Backup button is not enabled. Validation Failed ###")

    @test_step
    def set_subclient_content(self, db_list):
        """Sets subclient content to test databases
        Args:
            db_list  (list):  List of databases to be in subclient content
        """
        self.admin_console.refresh_page()
        self.database_group.edit_content(db_list)

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            self.navigate_to_instance()
            if self.deconfigure is True:
                self.log.info("Re-configuring MySQL Instance")
                self.page_container.access_page_action('Reconfigure')
                self.dialog.click_yes_button()
            self.db_instance_details.click_on_entity(self.subclient.subclient_name)
            self.set_subclient_content(self.db_group_content)
        except Exception as e:
            self.log.info(e)
            pass

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.subclient.subclient_name)
            self.db_group_content = \
                [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]]
            self.db_list = self.helper_object.generate_test_data(f"auto_{int(time.time())}")
            self.backup_and_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
