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
    prepare_subclient()           -- Prepares default subclient to check job linking
    wait_for_job_completion()     -- Wait for completion of job and check job status
    run_backup()                  -- Submit backup and return backup job id
    run_sweep_job()               -- Runs sweep job and returns sweep job id

Input Example:
    "testCases":
        {
            "60483":
                    {
                        "ClientName": "meeratrad_3",
                        "AgentName": "informix",
                        "InstanceName": "ol_informix1210",
                        "BackupsetName": "default",
                        "UserName":"informix",
                        "password": "informix",
                        "InformixServiceName": "9088"
                    }
        }
Put password value as empty for linux clients.
Provide DomainName also in UserName for windows clients.
Provide port to which informix server listens using ipv4 address in InformixServiceName
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import InformixSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Database.dbhelper import DbHelper
from Database.InformixUtils.informixhelper import InformixHelper

class TestCase(CVTestCase):
    """Class for executing job linking for informix with log backup to disk cache"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Job linking for Informix log backup to disk cache"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'UserName': None,
            'password': None,
            'InformixServiceName': None
            }
        self.subclient_page = None
        self.informix_helper_object = None
        self.db_instance = None
        self.db_instance_details = None

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
        self.subclient_page = InformixSubclient(self.admin_console)
        self.informix_helper_object = InformixHelper(
            self.commcell,
            self.instance,
            'default',
            self.client.client_hostname,
            self.instance.instance_name,
            self.tcinputs['UserName'],
            self.tcinputs['password'],
            self.tcinputs['InformixServiceName']
        )
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)

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
        plan_details = PlanDetails(self.admin_console)
        if enable:
            plan_details.edit_database_options(use_disk_cache=True)
            if not self.informix_helper_object.is_log_backup_to_disk_enabled():
                raise CVTestStepFailure("Log backup to disk cache is not enabled")
        else:
            plan_details.edit_database_options(use_disk_cache=False)
            if self.informix_helper_object.is_log_backup_to_disk_enabled():
                raise CVTestStepFailure("Log backup to disk cache is not disabled")

    @test_step
    def prepare_subclient(self):
        """Prepares the subclient to verify test case"""
        self.log.info("Enable log backup to disk cache if not enabled")
        if not self.informix_helper_object.is_log_backup_to_disk_enabled():
            self.set_backup_to_disk_cache()
        self.log.info("Switch log to prepare for log only backup")
        self.informix_helper_object.cl_switch_log(
            self.client.client_name,
            self.client.instance,
            self.informix_helper_object.base_directory)
        self.log.info("Run log only backup to ensure pending sweep job complete")
        self.informix_helper_object.cl_log_only_backup(
            self.client.client_name,
            self.client.instance,
            self.informix_helper_object.base_directory)
        self.log.info("Ensure default subclient content is Entire Instance")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance.select_instance(DBInstances.Types.INFORMIX,
                                    self.instance.instance_name,
                                    self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('default')
        self.subclient_page.edit_content('EntireInstance')

    @test_step
    def wait_for_job_completion(self, jobid):
        """Wait for completion of job and check job status
                Args:
                    jobid (int) -- job id of the operation
                Returns:
                    CVTestStepFailure exception: If job fails
                """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def run_backup(self):
        """Submits full backup, wait for completion and returns the backup jobid
            Returns:
                jobid (int) -- job id of the backup job
        """
        full_jobid = self.subclient_page.backup(RBackup.BackupType.FULL)
        self.wait_for_job_completion(full_jobid)
        return full_jobid

    @test_step
    def run_sweep_job(self, full_jobid):
        """ Method to run sweep job and get the sweep job id
        Args:
            full_jobid(str) -- job id of the full backup
        Returns:
            last_job(int)   -- job id of the sweep job
        """
        machine_object = machine.Machine(self.client)
        output = machine_object.get_logs_for_job_from_file(
            job_id=full_jobid, log_file_name="IFXXBSA.log",
            search_term="DataServer context initialized successfully")
        media_agent = output.split()[-1].split("*")[1]
        self.informix_helper_object.run_sweep_job_using_regkey(media_agent)
        cli_subclient = self.backupset.subclients.get('(command line)')
        dbhelper_object = DbHelper(self.commcell)
        last_job = dbhelper_object._get_last_job_of_subclient(cli_subclient)
        self.log.info("Disable log backup to disk cache option")
        self.set_backup_to_disk_cache(enable=False)
        return last_job

    def run(self):
        """ Main function for test case execution """
        try:
            if 'planEntity' not in self.instance.properties:
                raise CVTestStepFailure('Ensure instance is associated with a plan')
            self.prepare_subclient()
            full_jobid1 = self.run_backup()
            full_jobid2 = self.run_backup()
            sweep_jobid = self.run_sweep_job(full_jobid1)
            child_list1 = self.informix_helper_object.get_child_jobs(full_jobid1)
            if sweep_jobid in child_list1:
                self.log.info("Job linking for full backup 1 is verified fine")
            else:
                raise CVTestStepFailure('Job linking is missing for full backup 1')
            child_list2 = self.informix_helper_object.get_child_jobs(full_jobid2)
            if sweep_jobid in child_list2:
                self.log.info("Job linking for full backup 2 is verified fine")
            else:
                raise CVTestStepFailure('Job linking is missing for full backup 2')

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
