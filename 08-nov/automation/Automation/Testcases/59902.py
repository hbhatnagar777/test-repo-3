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
    __init__()                    -- initialize TestCase class
    setup()                       -- setup method for test case
    tear_down()                   -- tear down method for test case
    run()                         -- run function of this test case
    set_backup_to_disk_cache()    -- Sets log backup to disk cache option for the plan
    navigate_to_instance()        -- Navigates to details page for instance
    create_helper_object()        -- Creates oracle helper class object
    wait_for_job_completion()     -- Wait for completion of job and check job status
    run_backup()                  -- Submit backup and return backup job id
    run_restore()                 -- Submit restore and return job id
    get_log()                     -- Get log from one of the nodes
    feature_validation()          -- Confirm the restore used right source
    run_sweep_job()               -- Runs sweep job and returns sweep job id

Input Example:

    "testCases":
        {
            "59902":
                {
                    "RacInstanceName": "name of the instance",
                    "RacClusterName": "name of the cluster",
                    "MediaAgent": "name of MA"
                }
        }



"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import OracleSubclient
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Components.panel import Backup, PanelInfo
from Database.dbhelper import DbHelper
from Database.OracleUtils.oraclehelper import OracleRACHelper

class TestCase(CVTestCase):
    """Class for executing oracle log backup to disk cache"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle RAC log backup to disk cache"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59902'
        self.tcinputs = {
            'RacClusterName': None,
            'RacInstanceName': None,
            'MediaAgent': None
        }
        self.subclient_page = None
        self.oracle_helper_object = None
        self.dbhelper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.database_type = None
        self.cli_subclient = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.subclient_page = OracleSubclient(self.admin_console)
        self.dbhelper_object = DbHelper(self.commcell)
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE_RAC
        self.cli_subclient = self.instance.subclients.get('(command line)')

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)

    @test_step
    def set_backup_to_disk_cache(self, enable=True):
        """Sets log backup to disk cache option for the plan
        Args:
            enable (bool) -- True to enable log backup to disk cache option
                             for the plan. Default is true
        Raises:
            CVTestStepFailure exception:
            If log backup to disk cache option is not set as intended
        """
        self.navigator.navigate_to_plan()
        self.admin_console.wait_for_completion()
        plans = Plans(self.admin_console)
        plans.select_plan(self.instance.properties["planEntity"]["planName"])
        self.admin_console.wait_for_completion()
        db_panel = PanelInfo(self.admin_console, "Database options")
        if enable:
            db_panel.enable_toggle('Use disk cache for log backups')
            if not self.oracle_helper_object.is_log_backup_to_disk_enabled():
                raise CVTestStepFailure("Log backup to disk cache is not enabled")
        else:
            db_panel.disable_toggle('Use disk cache for log backups')
            if self.oracle_helper_object.is_log_backup_to_disk_enabled():
                raise CVTestStepFailure("Log backup to disk cache is not disabled")

    @test_step
    def navigate_to_instance(self):
        """Opens details page for default subclient"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                self.tcinputs["RacInstanceName"],
                                                self.tcinputs["RacClusterName"])

    @test_step
    def create_helper_object(self):
        """Creates oracle RAC helper object"""
        self.client = self.commcell.clients.get(self.tcinputs["RacClusterName"])
        self.instance = self.client.agents.get("oracle rac").instances.get(
            self.tcinputs["RacInstanceName"])
        self.oracle_helper_object = OracleRACHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleRACHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def wait_for_job_completion(self, jobid):
        """Wait for completion of job and check job status"""
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def run_backup(self):
        """Submits full backup, wait for completion and returns the backup jobid"""
        full_jobid = self.subclient_page.backup(Backup.BackupType.FULL)
        self.wait_for_job_completion(full_jobid)
        return full_jobid

    @test_step
    def run_restore(self):
        """ method to run restore"""
        num_of_files = 1
        row_limit = 10
        self.oracle_helper_object.oracle_data_cleanup(
            tables=["CV_TABLE_01"], tablespace=self.tablespace_name)
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["RacInstanceName"])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore(recover_to="most recent backup")
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle RAC Restore completed")
        self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                             "CV_TABLE_01", row_limit)

    @test_step
    def get_log(self, job_id, keyword, log_file):
        """ method to get log start and end sequence to restore"""
        nodes = self.oracle_helper_object.get_nodes()
        output = None
        for node in nodes:
            machine_object = Machine(node, self.commcell)
            try:
                output = machine_object.get_logs_for_job_from_file(
                    job_id=job_id, log_file_name=log_file, search_term=keyword)
            except Exception as str_err:
                self.log.info("Unable to fetch log from node: %s, %s", node, str_err)
        if not output:
            raise CVTestStepFailure("Failed to retrieve log from both nodes")
        return output

    @test_step
    def feature_validation(self, restore_jobid, sweep_jobid=None):
        """ Method to ensure restore is actually using right source
        Args:
            restore_jobid(int) --  Job id of the restore job
            sweep_jobid(int)   --  Job id of the sweep job
        Raises:
            CVTestStepFailure exception:
            If restore is not from expected media
        """
        if sweep_jobid:
            output = self.get_log(
                job_id=restore_jobid, log_file_name="ORASBT.log", search_term="GetBackupInfo")
            afileid = self.oracle_helper_object.get_afileid(sweep_jobid, "4")
            if str(afileid) in output:
                self.log.info("Logs were restored from swept job.Feature validation completed")
            else:
                raise CVTestStepFailure("Restore is not from swept job."
                                        "Output is {0}".format(output))
        else:
            output = self.get_log(
                job_id=restore_jobid, log_file_name="ORASBT.log", search_term="GetBackupInfo")
            if "Successful DataServer API search" in output:
                self.log.info("Logs were restored from disk cache.Feature validation completed")
            else:
                raise CVTestStepFailure("No log is restored from disk cache."
                                        "Output is {0}".format(output))

    def run_sweep_job(self):
        """ Method to run sweep job and get the sweep job id
        Returns:
            last_job(int)   -- job id of the sweep job
        """
        self.oracle_helper_object.run_sweep_job_using_regkey(self.tcinputs.get("MediaAgent"))
        last_job = self.dbhelper_object._get_last_job_of_subclient(self.cli_subclient)
        return last_job

    def run(self):
        """ Main function for test case execution """
        try:
            if 'planEntity' not in self.instance.properties:
                raise CVTestStepFailure('Ensure instance is associated with a plan')
            self.log.info(
                "#" * (10) + "  Oracle RAC Backup/Restore Operations  " + "#" * (10))

            self.log.info("Navigating to DB Instances page")
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()

            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE_RAC,
                                                          self.tcinputs["RacInstanceName"],
                                                          self.tcinputs["RacClusterName"]):
                self.log.info("Instance found")
                self.navigate_to_instance()
            else:
                raise CVTestStepFailure("Instance not found")

            self.log.info("Generating Sample Data for test")
            table_limit = 1
            num_of_files = 1
            self.create_helper_object()

            self.oracle_helper_object.db_execute('alter system switch logfile')

            self.set_backup_to_disk_cache()
            self.log.info("Run log only backup to ensure pending sweep job complete")
            self.admin_console.select_hyperlink('ArchiveLog')
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle RAC Log Backup is completed")
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files)
            self.log.info("Test Data Generated successfully")
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["RacInstanceName"])
            self.admin_console.select_hyperlink('default')
            full_jobid = self.run_backup()
            restore_jobid = self.run_restore()
            self.feature_validation(restore_jobid)
            sweep_jobid = self.run_sweep_job()
            restore_jobid = self.run_restore()
            self.feature_validation(restore_jobid, sweep_jobid)
            self.set_backup_to_disk_cache(enable=False)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
