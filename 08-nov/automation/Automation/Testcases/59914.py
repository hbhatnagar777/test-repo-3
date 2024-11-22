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

    check_if_instance_exists()  --  checks if instance iexists

    navigate_to_instance()      --  navigates to specified instance

    create_helper_object()      --  creates object of OracleHelper class

    create_test_data()          --  creates test data

    new_subclient()             --  method to create new subclient

    run_backup()                --  method to run backup

    validate_backup()           --  method to validate backup

    backup_and_validate()       --  method to run run_backup() and validate_backup()

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59914":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"XXXX"
                        }
            }

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import OracleSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
import time

class TestCase(CVTestCase):
    """ Class for executing Oracle Backup arguments Test for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Test for Oracle iDA Backup arguments from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59914'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None}
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.add_subclient = None
        self.automation_subclient = None

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
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = OracleSubclient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE

    def tear_down(self):
        """ tear down method for testcase """
        if self.status == constants.PASSED:
            if self.automation_subclient:
                self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.automation_subclient)

            self.subclient_page.delete_subclient()
            self.log.info("Deleting Automation Created tablespaces and tables")
            if self.oracle_helper_object:
                self.oracle_helper_object.oracle_data_cleanup(
                    tables=["CV_TABLE_01"], tablespace=self.tablespace_name,
                    user="{0}_user".format(self.tablespace_name.lower()))
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

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
    def check_if_instance_exists(self):
        """Checking if instance exists"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.log.info("Instance found")
        else:
            raise CVTestStepFailure("Instance not found")

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def create_test_data(self):
        """ Generating Sample Data for test"""
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        self.create_helper_object()
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name, table_limit, num_of_files, row_limit)
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.log.info("Test Data Generated successfully")

    @test_step
    def new_subclient(self):
        """Adding new subclient"""
        self.db_instance_details.access_subclients_tab()
        if self.admin_console.check_if_entity_exists('link', self.tablespace_name):
            self.db_instance_details.click_on_entity(self.tablespace_name)
            time.sleep(60)
            self.subclient_page.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        self.add_subclient.add_subclient(
            subclient_name=self.tablespace_name, plan=self.tcinputs["Plan"])
        self.log.info("Waiting for subclient creation completion")
        time.sleep(60)
        self.automation_subclient = self.tablespace_name

    @test_step
    def run_backup(self):
        """ Method to run backup"""
        display_name = self.tcinputs["ClientName"]
        for client in self.commcell.clients.all_clients:
            if client.startswith(self.tcinputs["ClientName"]):
                display_name = client
                break
        active_jobs = self.commcell.job_controller.active_jobs(
            client_name=display_name, job_filter="Backup")
        active_job = None
        for job in active_jobs:
            job_obj = self.commcell.job_controller.get(job)
            if job_obj.subclient_name == self.tablespace_name \
                    and job_obj.instance_name == self.instance.instance_name:
                active_job = job_obj
                job_id = active_job.job_id
                break
        if active_job:
            self.wait_for_job_completion(job_id)
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle Full Backup is completed")
        return job_id

    @test_step
    def validate_backup(self, job_id, backup_args):
        """ Method to validate backup"""
        backup_file = self.oracle_helper_object.fetch_rman_log(job_id, self.client, "backup")
        script = backup_file.split("Rman Log:[")
        data_script = script[0]
        log_script = script[1].split("Recovery Manager complete.")[-1]
        streams = backup_args.get('Number of data streams')
        if streams:
            if not(data_script.count("setlimit channel") == int(streams)):
                raise CVTestStepFailure("Number of data streams validation failed")
            self.log.info("Number of streams validation successful")
        data_files = backup_args.get('Data files (BFS)')
        if data_files:
            if data_script.find(f"filesperset = {data_files} ") == -1:
                raise CVTestStepFailure("data files per BFS validation failed")
            self.log.info("Data files per BFS validation successful")
        archive_files = backup_args.get('Archive files (BFS)')
        if archive_files:
            if log_script.find(f"filesperset = {archive_files} ") == -1:
                raise CVTestStepFailure("archive files per BFS validation failed")
            self.log.info("Archive files per BFS validation successful")
        max_open_files = backup_args.get('Maximum number of open files')
        if max_open_files:
            if not(data_script.count("maxopenfiles") == data_script.count(f"maxopenfiles {max_open_files}") and
                   log_script.count("maxopenfiles") == log_script.count(f"maxopenfiles {max_open_files}")):
                raise CVTestStepFailure("Max open files validation failed")
            self.log.info("Max number of open files validation successful")
        backup_piece_size = backup_args.get('RMAN Backup piece size')
        if backup_piece_size:
            size_type, size, value, mode = backup_piece_size.split()
            if mode.lower() == "mb":
                value = int(value)*1024
            elif mode.lower() == "gb":
                value = int(value)*1048576
            if size_type.lower() == "maximum":
                if not(data_script.count("kbytes") == data_script.count(f"kbytes {value}") and
                       log_script.count("kbytes") == log_script.count(f"kbytes {value}")):
                    raise CVTestStepFailure("Maximum Rman backup piece size validation failed")
                self.log.info("Maximum Rman backup piece size validation successful")
            else:
                if data_script.find(f"SECTION SIZE = {value}K") == -1:
                    raise CVTestStepFailure("Rman Backup piece section size validation failed")
                self.log.info("Rman Backup piece section size validation successful")

    @test_step
    def backup_and_validate(self, backup_args):
        """ Method to run backup and validate backup args"""
        self.subclient_page.edit_backup_arguments(
            backup_args=backup_args)
        job_id = self.run_backup()
        self.validate_backup(job_id, backup_args)

    def run(self):
        """ Main function for test case execution """
        try:
            self.check_if_instance_exists()
            self.navigate_to_instance()
            self.create_test_data()

            self.new_subclient()

            self.log.info("Preparing for Backup.")

            backup_args =[{'Number of data streams': '3',
                            'Maximum number of open files': '7',
                            'Data files (BFS)': '7',
                            'Archive files (BFS)': '39',
                            'RMAN Backup piece size': 'Maximum size 10 MB'},
                           {'Number of data streams': '5',
                            'Maximum number of open files': '9',
                            'Data files (BFS)': '7',
                            'Archive files (BFS)': '32',
                            'RMAN Backup piece size': 'Section size 20 MB'}]

            for backup_arg in backup_args:
                self.backup_and_validate(backup_arg)

        except Exception as exp:
            handle_testcase_exception(self, exp)
