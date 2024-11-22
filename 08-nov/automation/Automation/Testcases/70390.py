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

    navigate_to_instance()      --  navigates to specified instance

    validate_preview()          --  Validate the Preview Script for backup and restore

    backup_preview()            --  Method to access backup

    restore_preview()           --  Method to access restore

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "70390":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance"
                        }
            }

"""

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import TestStep, handle_testcase_exception
from datetime import datetime, timedelta
from pytz import timezone
import time


class TestCase(CVTestCase):
    """ Class for executing Test for Oracle script preview for backup and restore """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle script preview for backup and restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None}
        self.database_instances = None
        self.db_instance_details = None
        self.machine_object = None
        self.page_container = None
        self.dialog = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.page_container = PageContainer(self.admin_console)
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.machine_object = Machine(self.client, self.commcell)
        self.dialog = RModalDialog(self.admin_console)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def validate_preview(self, action_type, search_term):
        """Validate the Preview Script for backup and restore"""
        cur_time = datetime.now(timezone('US/Eastern'))
        self.dialog.click_preview_button()
        self.log.info("The program is sleeping for 60 seconds as we wait for script to be loaded")
        time.sleep(60)

        self.log.info(f"#######Checking if the {action_type} preview script is generated in ClOraAgent.log#######")
        attempts = 3
        val = 1
        upd_time = cur_time.strftime("%m/%d %H:%M")
        while attempts > 0:
            search_term1 = f"{upd_time}.*{search_term}.*"
            output = self.machine_object.get_logs_for_job_from_file(log_file_name="ClOraAgent.log",
                                                                    search_term=search_term1)
            if len(output) > 0:
                self.log.info(f"###The {action_type} preview script is generated in ClOraAgent.log successfully..!!###")
                break
            upd_time = cur_time + timedelta(minutes=val)
            upd_time = upd_time.strftime("%m/%d %H:%M")
            attempts -= 1
            val += 1
        if attempts == 0:
            raise Exception(f"The {action_type} preview script is failed to generate in ClOraAgent.log !!")

        self.log.info(f"#######Checking if the {action_type} preview script appears in the dialog#######")
        preview_modal = RModalDialog(self.admin_console, title=f'{action_type} preview')
        preview_modal.access_tab('Database script')
        details = self.dialog.get_preview_details()
        if len(details) > 10:
            self.log.info(f"###{action_type} preview has script!!###")
        else:
            raise Exception(f"{action_type} preview is empty!!")

        preview_modal.click_cancel()
        self.dialog.click_cancel()

    @test_step
    def backup_preview(self):
        """Method to access backup"""
        self.db_instance_details.access_subclients_tab()
        self.db_instance_details.click_on_entity('default')
        self.log.info("Waiting to load Subclient properties")
        self.page_container.access_page_action('Backup')
        search_term = "DATA/CONTROL FILE/SPFILE BACKUP SCRIPT"
        self.validate_preview("Backup", search_term)

    @test_step
    def restore_preview(self):
        """Method to access restore"""
        self.page_container.click_breadcrumb(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        self.db_instance_details.restore_folders(database_type=DBInstances.Types.ORACLE, all_files=True)
        self.dialog.select_radio_by_id("inPlaceRestore")
        search_term = "DATA RESTORE SCRIPT"
        self.validate_preview("Restore", search_term)

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                          self.tcinputs["InstanceName"],
                                                          self.tcinputs["ClientName"]):
                self.log.info("Instance found")
            else:
                raise Exception('Instance not found')

            self.navigate_to_instance()

            self.backup_preview()

            self.restore_preview()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
