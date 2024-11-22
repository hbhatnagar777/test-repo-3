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

    wait_for_job_completion()   --  waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    add_server()                --  method to add oracle server

    create_helper_object()      --  creates object of OracleHelper class

    run_restore()               --  method to run restore and validate test data

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59359":
                        {
                          "Client":"client_name",
                          "InstanceName":"instance",
                          'ClientUsername': 'XXXX',
                          'ClientPassword': 'XXXX',
                          'Plan': 'XXXX',
                          'ConnectString': 'username/password@servicename',
                          'UnixGroup': 'client_unix_group'  (optional)
                          'InstallLocation': 'InstallLocation/on/client'    (optional)
                          'Hostname': 'client_hostname'
                                        (optional, if hostname is different from "Client" input)
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
from AutomationUtils.machine import Machine
import time


class TestCase(CVTestCase):
    """ Class for executing Add Server and restore from backup job Test for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle IDA Command Center - Add Server and restore from backup job"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59359'
        self.database_type = None
        self.tcinputs = {
            'Client': None,
            'InstanceName': None,
            'ClientUsername': None,
            'ClientPassword': None,
            'Plan': None,
            'ConnectString': None
        }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.machine_obj = None
        self.clients = None
        self.client = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE


    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def add_server(self):
        """Adds server to Commvault"""
        server_name = self.tcinputs["Client"]
        if "Hostname" in self.tcinputs:
            server_name = self.tcinputs["Hostname"]
        self.machine_obj = Machine(
            server_name, username=self.tcinputs["ClientUsername"],
            password=self.tcinputs["ClientPassword"])
        unix_group = None
        if "UnixGroup" in self.tcinputs:
            unix_group = self.tcinputs["UnixGroup"]
        install_location = None
        if "InstallLocation" in self.tcinputs:
            install_location = self.tcinputs["InstallLocation"]
        job_id = self.database_instances.add_server(
            database_type=DBInstances.Types.ORACLE, server_name=server_name,
            username=self.tcinputs["ClientUsername"], password=self.tcinputs["ClientPassword"],
            plan=self.tcinputs["Plan"], unix_group=unix_group, install_location=install_location,
            os_type=self.machine_obj.os_info.lower())
        self.wait_for_job_completion(job_id)
        self.commcell.clients.refresh()
        self.log.info("waiting for client to load")
        time.sleep(60)
        self.client = self.commcell.clients.get(self.tcinputs["Client"])

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["Client"])

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.admin_console.refresh_page()
        self.admin_console.click_button_using_text('Restore')
        self.admin_console.wait_for_completion()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.clients = self.commcell.clients
            if self.clients.has_client(self.tcinputs['Client']):
                self.client = self.commcell.clients.get(self.tcinputs["Client"])
                self.client.retire()
                self.log.info("Waiting for client uninstallation to complete")
                time.sleep(60)
                self.clients.delete(self.tcinputs['Client'])
            self.add_server()
            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                          self.tcinputs["InstanceName"],
                                                          self.tcinputs["Client"]):
                self.log.info("Instance found to be auto discovered")
            else:
                raise Exception('Instance not found')
            self.navigate_to_instance()
            self.db_instance_details.edit_instance_update_credentials(
                self.tcinputs["ConnectString"], plan=self.tcinputs["Plan"])
            self.log.info("Generating Sample Data for test")
            table_limit = 1
            num_of_files = 1
            row_limit = 10
            self.create_helper_object()
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files)
            self.oracle_helper_object.db_execute('alter system switch logfile')
            self.log.info("Test Data Generated successfully")

            self.log.info("Preparing for Backup.")
            self.db_instance_details.click_on_entity('default')
            time.sleep(30)
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            current_url = self.admin_console.current_url()
            job_details_url = current_url.split("/#/")[0]+f"/#/jobs/{job_id}"
            self.admin_console.navigate(job_details_url)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle Full Backup is completed")
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')

            self.log.info("Cleaning up tablespace and data before restore")
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

            self.log.info("Preparing for Restore.")
            self.run_restore()

            self.log.info("Validating Backed up content")
            self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                                 "CV_TABLE_01", row_limit)
            self.log.info("Validation Successfull.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
