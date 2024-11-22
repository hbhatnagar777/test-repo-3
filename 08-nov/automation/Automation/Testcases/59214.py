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

    wait_for_job_completion()   --  Waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    navigate_to_plan()          --  navigates to specified plan

    edit_instance_change_plane()--  method to edit instance to change plan set

    change_plan_start_time()    --  method to edit plan RPO start time

    change_log_rpo_frequency()  --  method to edit log RPO frequency

    change_full_backup_frequency()--method to edit full backup frequency

    get_job_obj()               --  method to fetch active job object according to specifications

    cleanup()                   --  method to cleanup testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59214": {
                    "ClientName": "XXX",
                    "AgentName": "XXX",
                    "InstanceName": "XXX",
                    "BackupsetName": "XXX",
                    "SubclientName": "XXX",
                    "Plan": "XXX"
                }
            }

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.panel import PanelInfo
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ Class for validation of full, incremental and log RPO schedules for DB agents"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DB agents - check incremental backup " \
                    "schedule and log RPO schedules trigger backups"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.plans = None
        self.plan_details = None
        self.database_instances = None
        self.db_instance_details = None
        self.full_backup_frequency_before_tc = None
        self.start_time_before_tc = None
        self.log_rpo_before_tc = None
        self.plan_before_tc = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "SubclientName": None,
            "Plan": None
        }

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open(maximize=True)
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.plans = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        agent_mapping = {
            "mysql": DBInstances.Types.MYSQL,
            "oracle": DBInstances.Types.ORACLE,
            "postgresql": DBInstances.Types.POSTGRES,
            "cloud apps": DBInstances.Types.CLOUD_DB,
            "db2": DBInstances.Types.DB2,
            "sybase": DBInstances.Types.SYBASE,
            "informix": DBInstances.Types.INFORMIX,
            "sap hana": DBInstances.Types.SAP_HANA,
            "oracle rac": DBInstances.Types.ORACLE_RAC
        }
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(agent_mapping[self.tcinputs["AgentName"]],
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def navigate_to_plan(self):
        """Navigates to plan page"""
        self.navigator.navigate_to_plan()
        self.plans.select_plan(self.tcinputs["Plan"])

    @test_step
    def edit_instance_change_plan(self, new_plan, get_existing_plan=True):
        """
        Method to navigate to DB instance and edit plan
            Args:
                 new_plan   (str)   : Name of plan to change to
                 get_existing_plan  (bool)  : True if method should return existing plan's name
                    Default: True
        """
        plan = None
        self.navigate_to_instance()
        if get_existing_plan:
            instance_details = PanelInfo(self.admin_console, title='General').get_details()
            if 'Plan' not in instance_details.keys():
                plan = instance_details['Plan name'].split("\n")[0]
            else:
                plan = instance_details['Plan'].split("\n")[0]
        if plan != new_plan:
            self.db_instance_details.edit_instance_change_plan(new_plan)
        return plan

    @test_step
    def change_plan_start_time(self, start_time, get_existing_start_time=True):
        """Changes plan start time to start_time input
            Args:
                start_time (str)    :   Start time in the format %I:%M %p (eg. "07:00 PM")
                get_existing_start_time (bool): True if existing start time is to be returned
                    Default: True
            Returns: plan start time before change
        """
        backup_start_time = None
        if get_existing_start_time:
            backup_frequency = PanelInfo(self.admin_console,
                                         "RPO").get_details()['Backup frequency']
            backup_start_time = backup_frequency.split("at ")[-1]
        self.plan_details.edit_plan_rpo_start_time(start_time)
        return backup_start_time

    @test_step
    def change_log_rpo_frequency(self, frequency, get_existing_frequency=True):
        """Changes log RPO frequency in plans page
            Args:
                frequency   (str)   :   "x hours and x minutes"
                get_existing_frequency  (bool)  : True  if existing frequency is to be returned
                    Default: True
            Returns: log rpo frequency before change
        """
        log_rpo = None
        if get_existing_frequency:
            log_rpo = PanelInfo(self.admin_console,
                                "Database options").get_details()['Log backup RPO']
        new_log_rpo = {"hours": "0", "minutes": "0"}
        frequency = frequency.split(" and ")
        for value in frequency:
            if "hour" in value:
                new_log_rpo["hours"] = value.split()[0]
            elif "minute" in value:
                new_log_rpo["minutes"] = value.split()[0]
        self.plan_details.edit_database_options(new_log_rpo)
        return log_rpo

    @test_step
    def change_full_backup_frequency(self, frequency=None, get_existing_frequency=True):
        """Changes full backup frequency in plans page
            Args:
                frequency   (str)   :   "%A at %I:%M %p" eg. "Saturday at 12:00 AM"
                                        If None, full backups are disabled
                get_existing_frequency  (bool)  : True  if existing frequency is to be returned
                    Default: True
            Returns: log rpo frequency before change
        """
        backup_frequency = None
        if get_existing_frequency:
            details = PanelInfo(self.admin_console, "RPO").get_details()

            if 'Full backup frequency' in details.keys():
                backup_frequency = details['Full backup frequency']
            else:
                backup_frequency = False
        if frequency:
            frequency = frequency.split(" at ")
            self.plan_details.edit_plan_full_backup_rpo(start_time=frequency[1],
                                                        start_days=frequency[0].split(','))
        else:
            self.plan_details.edit_plan_full_backup_rpo(enable=False)
        return backup_frequency

    @test_step
    def get_job_obj(self, schedule=None, time_limit=5, raise_exception=True):
        """Gets the job object from active jobs of commcell
            Args:
                schedule: schedule which triggered the job
                    default: None
                time_limit: Time limit to wait for job in minutes
                    default: 5
                raise_exception: True if exception to be raised when job not found
                    default: True
            Returns: Job object
        """
        agents_with_backupset = ['postgresql', 'db2']
        active_job = None
        time_limit = time.time() + time_limit*60
        while time.time() <= time_limit and active_job is None:
            self.log.info("Waiting for 10 seconds before checking for active job")
            time.sleep(10)
            active_jobs = self.commcell.job_controller.active_jobs(
                client_name=self.tcinputs['ClientName'], job_filter="Backup")
            for job_id in active_jobs:
                job = self.commcell.job_controller.get(job_id)
                job_of_backupset = True
                if self.tcinputs['AgentName'] in agents_with_backupset:
                    job_of_backupset = job.backupset_name == self.tcinputs["BackupsetName"]
                job_of_subclient = job.subclient_name == self.tcinputs["SubclientName"]
                job_of_schedule = True
                if schedule:
                    job_of_schedule = False
                    if "logs" in schedule and self.tcinputs['AgentName'] in ["oracle"]:
                        job_of_subclient = job.subclient_name == "ArchiveLog"
                    if 'scheduleName' in job.details['jobDetail']['generalInfo']:
                        job_of_schedule = \
                            job.details['jobDetail']['generalInfo']['scheduleName'] == schedule
                if job_of_subclient and\
                        job.instance_name == self.tcinputs["InstanceName"] and job_of_backupset\
                        and job_of_schedule:
                    active_job = job
                    break
        if active_job is None and raise_exception:
            raise CVTestStepFailure(f"Search for {schedule} triggered job failed")
        if active_job:
            self.log.info("Found job %s", active_job.job_id)
        return active_job

    @test_step
    def cleanup(self, plan_before_tc=None):
        """Cleans up testcase made changes
            Args:
                plan_before_tc  (str)   : Plan to revert to
        """
        if self.full_backup_frequency_before_tc is not None:
            self.change_full_backup_frequency(get_existing_frequency=False)
            self.full_backup_frequency_before_tc = None
        if self.start_time_before_tc:
            self.change_plan_start_time(self.start_time_before_tc,
                                        get_existing_start_time=False)
            self.start_time_before_tc = None
        if self.log_rpo_before_tc:
            self.change_log_rpo_frequency(self.log_rpo_before_tc,
                                          get_existing_frequency=False)
            self.log_rpo_before_tc = None
        if plan_before_tc:
            self.edit_instance_change_plan(plan_before_tc)

    def run(self):
        """ Main function for test case execution """
        try:
            self.plan_before_tc = self.edit_instance_change_plan(self.tcinputs["Plan"])
            self.navigate_to_plan()

            self.log.info("Waiting out any active jobs before triggering schedules")
            active_job = self.get_job_obj(time_limit=2, raise_exception=False)
            while active_job:
                self.log.info("Waiting for job %s to complete", active_job.job_id)
                self.wait_for_job_completion(int(active_job.job_id))
                active_job = self.get_job_obj(time_limit=2, raise_exception=False)

            new_start_time = time.strftime('%I:%M %p', time.localtime(time.time() + 300))
            self.start_time_before_tc = self.change_plan_start_time(new_start_time)
            self.log.info("Waiting for 2 minutes before checking for scheduled backup job")
            time.sleep(120)
            incr_job = self.get_job_obj(schedule="Incremental backup schedule")
            self.cleanup()
            self.wait_for_job_completion(incr_job.job_id)

            if self.tcinputs['AgentName'] not in ['informix', 'db2', 'db2 multinode', 'cloud apps']:
                self.log_rpo_before_tc = self.change_log_rpo_frequency("2 minutes")
                self.log.info("Checking for scheduled backup job")
                log_job = self.get_job_obj(schedule="Incremental automatic schedule for logs")
                self.cleanup()
                self.wait_for_job_completion(log_job.job_id)

            new_start_time = time.strftime('%A at %I:%M %p', time.localtime(time.time() + 300))
            self.full_backup_frequency_before_tc = self.change_full_backup_frequency(new_start_time)
            self.log.info("Waiting for 2 minutes before checking for scheduled backup job")
            time.sleep(120)
            full_job = self.get_job_obj(schedule="Full backup schedule")
            self.cleanup()
            self.wait_for_job_completion(full_job.job_id)
            self.log.info("Waiting out any active jobs before changing plan back")
            active_job = self.get_job_obj(time_limit=2, raise_exception=False)
            while active_job:
                self.log.info("Waiting for job %s to complete", active_job.job_id)
                self.wait_for_job_completion(int(active_job.job_id))
                active_job = self.get_job_obj(time_limit=2, raise_exception=False)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup(self.plan_before_tc)
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
