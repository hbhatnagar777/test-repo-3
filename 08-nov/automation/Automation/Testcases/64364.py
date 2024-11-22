# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"64364": {
            "ClientName": None,
            "AgentName": None,
            "instance_name": None,
            "db2_username": None,
            "database": None,
            "db2_user_password": None,
            "db2_home_path": None,
            "media_agent": None,
            "backup_location": None,
            "credential_name": None
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    prerequisite_setup_test_case()          -- Prerequisites needed to run the testcase

    delete_existing_instance()              --  Deletes Existing instance on Command Center

    add_db2_instance()                      -- Adds DB2 instance on Command Center

    delete_database()                       -- Deletes database if it exists on Command Center

    add_database()                          -- Adds database to Command Center

    initialize_db2_helper()                 -- Initializing db2 helper object

    validate_default_instance_schedule()    -- Validating the default instance schedule

    calculate_difference()                  -- calculating the difference between two jobs

    validate_jobs()                         -- validating if all the jobs has triggered within specified schedule time

    wait_for_jobs()                         -- waits for next job to trigger

    change_plan_details()                   -- changing the plan details such as full, incremental or delta

    create_storage()                        -- creates storage group

    delete_storage()                        -- deletes storage group

    create_plan()                           -- creates plan

    delete_plan()                           -- deletes plan

    cleanup()                               -- Cleans up the setup

    tear_down()                             --  tear down function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.DB2Utils.db2helper import DB2
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.Plans import RPO
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
import datetime


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()

        self.plan_detail = None
        self.plans_page = None
        self.storage_helper = None
        self.plan_name = None
        self.storage_name = None
        self.plan_helper = None
        self.name = "Command Center - DB2 Out of place Restore to a different database on same instance on same machine"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.dbtype = None
        self.port = None
        self.home_path = None
        self.db2_helper = None
        self.redirect_path = None
        self.table_data = None
        self.table_name = None
        self.sto_grp = None
        self.tablespace_name = None
        self.page_container = None
        self.rpo = None
        self.instance = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "instance_name": None,
            "db2_username": None,
            "database": None,
            "db2_user_password": None,
            "db2_home_path": None,
            "media_agent": None,
            "backup_location": None,
            "credential_name": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])

            self.navigator = self.admin_console.navigator
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.dbtype = DBInstances.Types.DB2
            self.page_container = PageContainer(self.admin_console)
            self.storage_helper = StorageMain(self.admin_console)
            self.plan_helper = PlanMain(self.admin_console)
            self.plans_page = Plans(self.admin_console)
            self.plan_detail = PlanDetails(self.admin_console)
            self.storage_name = f"Disk{self.id}"
            self.plan_name = f"Plan{self.id}"
            self.plan_helper.plan_name = {"server_plan": self.plan_name}
            self.plan_helper.storage = {'pri_storage': self.storage_name,
                                        'pri_ret_period': '30',
                                        'ret_unit': 'Day(s)'}
            self.plan_helper.backup_data = None
            self.plan_helper.backup_day = None
            self.plan_helper.backup_duration = None
            self.plan_helper.rpo_hours = None
            self.plan_helper.allow_override = None
            self.plan_helper.database_options = None
            self.rpo = RPO(self.admin_console)
            self.prerequisite_setup_test_case()
            self.instance = self.agent.instances.get(self.tcinputs['instance_name'])

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function of this test case"""
        try:
            self.validate_default_instance_schedule()
            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(self.dbtype, self.tcinputs["instance_name"], self.client.display_name)

            self.change_plan_details("Full")
            self.wait_for_jobs(backuplevel="Full")

            self.change_plan_details("Incremental")
            self.wait_for_jobs(backuplevel="Incremental")

            self.change_plan_details("Differential")
            self.wait_for_jobs(backuplevel="Delta")

            self.log.info("Testcase passed")
            self.log.info("Sleeping for 30 seconds")
            time.sleep(30)
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.cleanup()

    @test_step
    def validate_default_instance_schedule(self):
        """Validating default schedule"""
        self.intialize_db2_helper(self.tcinputs["instance_name"], self.tcinputs['database'])

        csdb = self.db2_helper.csdb_object_to_execute()

        query = """select refTime from APP_InstanceName where id = {0}""".format(self.instance.instance_id)
        output = csdb.execute(query)
        self.log.info(output)

        instance_creation_time = output.rows[0][0]
        current_time = time.time()

        self.log.info("Instance creation time is:")
        self.log.info(instance_creation_time)

        if (current_time - instance_creation_time) < 86400:
            self.log.info("The default instance created within 24hours")
        else:
            jobs = self.commcell.job_controller.all_jobs(self.tcinputs['ClientName'])
            flag = False
            for j in jobs:
                job = self.commcell.job_controller.get(j)
                if job.instance_name == self.tcinputs['instance_name']:
                    flag = True
                    break

            if flag:
                self.log.info("Backup found. Default plan is being honoured")
            else:
                raise CVTestStepFailure("Instance is old enough to backup but no schedules were honoured")

        self.log.info("Sleeping for 30 sec")
        time.sleep(30)

    @test_step
    def wait_for_job_to_trigger(self, backuplevel):
        """Waiting for the job to trigger"""
        count = 60
        while count > 0:
            jobs = self.commcell.job_controller.active_jobs(self.tcinputs['ClientName'])

            for job in jobs:
                j = self.commcell.job_controller.get(job)
                if j.backup_level == backuplevel and j.instance_name == self.tcinputs['instance_name']:
                    self.log.info("Found job with job id " + j.job_id)
                    return j

            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")
            count -= 1

        return -1

    @test_step
    def calculate_difference(self, firstTime, secondtime):
        """Calculating difference"""
        date1 = datetime.datetime.strptime(firstTime, "%Y-%m-%d %H:%M:%S")
        date2 = datetime.datetime.strptime(secondtime, "%Y-%m-%d %H:%M:%S")

        difference = date1 - date2

        return difference.seconds / 60

    @test_step
    def validate_jobs(self, jobs):
        """validating the jobs"""
        prev_job_time = 0
        for job in jobs:
            if prev_job_time == 0:
                prev_job_time = job.start_time
            else:
                self.log.info(job.start_time + " " + prev_job_time)
                diff = self.calculate_difference(job.start_time, prev_job_time)
                prev_job_time = job.start_time
                if diff <= 7:
                    continue
                else:
                    return False

        return True

    @test_step
    def wait_for_jobs(self, backuplevel):
        """waiting for jobs to trigger"""

        firstjob = self.wait_for_job_to_trigger(backuplevel)  # wait for around 10 minutes to trigger first job

        if firstjob == -1:
            raise CVTestStepFailure("No job triggered")

        job_list = []
        job_list.append(firstjob)
        self.log.info("First job got triggered")

        # wait for 2 more jobs
        for i in range(0, 2):
            self.log.info("waiting 5 minutes for next job to trigger")
            time.sleep(300)  # sleep for 5 minutes
            job = self.wait_for_job_to_trigger(backuplevel)

            if job == -1:
                raise CVTestStepFailure("No job triggered")

            job_list.append(job)

        if self.validate_jobs(job_list):
            self.log.info("Jobs validated successfully")
        else:
            raise CVTestStepFailure("Jobs did not trigger within 5 minutes interval")

    @test_step
    def change_plan_details(self, backupType):
        """Changing plan details"""
        self.navigator.navigate_to_plan()
        self.plans_page.select_plan(self.plan_name)
        try:
            self.rpo.edit_schedule(1, new_values={
                'BackupType': backupType, 'Frequency': 5, 'FrequencyUnit': 'Minute(s)'
            })
        except Exception as exception:
            self.log.info(f"Deletion of plan failed as plan {self.plan_name} doesn't exist")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def prerequisite_setup_test_case(self):
        """
        Runs prerequisite steps to create client side setups and details
        """
        self.navigator.navigate_to_db_instances()
        self.delete_existing_instance()
        self.db_instance.react_instances_table.reload_data()
        self.delete_plan()
        self.delete_storage()
        self.create_storage()
        self.create_plan()
        self.navigator.navigate_to_db_instances()
        self.add_db2_instance()
        self.add_database(self.tcinputs["database"])
        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)

    @test_step
    def create_storage(self):
        """ Creates a storage disk """
        try:
            self.log.info("Creating a storage disk")
            self.storage_helper.add_disk_storage(disk_storage_name=self.storage_name,
                                                 media_agent=self.tcinputs["media_agent"],
                                                 backup_location=self.tcinputs["backup_location"])
            self.log.info("Successfully created a storage disk")
        except Exception as exception:
            self.log.info("Failed to create storage disk")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def refresh_commcell(self):
        """ Refreshes the commcell """
        self.commcell.refresh()

    @test_step
    def create_plan(self):
        """ Creates a plan with disk cache option enabled """
        try:
            self.log.info(f"Creating a plan {self.plan_name}")
            self.plan_helper.add_plan()
            self.refresh_commcell()
            self.log.info(f"Successfully created the plan")
        except Exception as exception:
            self.log.info("Failed to create the plan")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def delete_plan(self):
        """ Deletes Plan """
        self.navigator.navigate_to_plan()
        try:
            if self.plan_name in self.plans_page.list_plans():
                self.plans_page.delete_plan(self.plan_name)
            else:
                self.log.info("Plan Doesn't exist to delete")
        except Exception as exception:
            self.log.info(f"Deletion of plan failed as plan {self.plan_name} doesn't exist")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def delete_storage(self):
        """ Deletes Storge Disk """
        self.navigator.navigate_to_disk_storage()
        self.admin_console.refresh_page()
        try:
            if self.storage_name in self.storage_helper.list_disk_storage():
                self.storage_helper.delete_disk_storage(self.storage_name)
            else:
                self.log.info(f"Deletion of disk storage failed as {self.storage_name} doesn't exist")
        except Exception as exception:
            self.log.info("Deletion of disk failed as disk doesn't exist")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def delete_existing_instance(self):
        """
        Deletes if instance exists on Command Center
        """
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client.display_name):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client.display_name)
            self.db_instance_details.delete_instance()

    @test_step
    def add_db2_instance(self):
        """
        Adds DB2 instance on Command Center
        """
        self.db_instance.add_db2_instance(server_name=self.client.display_name,
                                          plan=self.plan_name,
                                          instance_name=self.tcinputs["instance_name"],
                                          db2_home=self.tcinputs['db2_home_path'],
                                          db2_username=self.tcinputs["db2_username"],
                                          db2_user_password=self.tcinputs["db2_user_password"],
                                          credential_name=self.tcinputs["credential_name"])
        self.commcell.refresh()
        self.admin_console.refresh_page()

    @test_step
    def add_database(self, database_name):
        """
        Adding database to Command Center
        Args:
            database_name (str) -- Database name to be added
        """
        self.commcell.refresh()
        self.admin_console.refresh_page()
        if database_name in self.db_instance_details.get_instance_entities():
            self.delete_database(database_name=database_name)
            self.admin_console.access_tab("Databases")
        self.db_instance_details.add_db2_database(database_name=database_name,
                                                  plan=self.plan_name)

    @test_step
    def delete_database(self, database_name):
        """
        Deletes database if it exists on Command Center
        Args:
            database_name (str) -- Database name to be deleted
        """
        if database_name in self.db_instance_details.get_instance_entities():
            self.db_instance_details.delete_entity(database_name)
        self.admin_console.refresh_page()
        self.commcell.refresh()

    @test_step
    def intialize_db2_helper(self, instance_name, dbname):
        """Initializing db2 helper object"""

        instance = self.agent.instances.get(instance_name)
        backupset = instance.backupsets.get(dbname)

        self.db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=instance,
                              backupset=backupset)

    @test_step
    def cleanup(self):
        """Cleanup"""
        self.navigator.navigate_to_db_instances()
        self.delete_existing_instance()
        self.delete_plan()
        self.delete_storage()

    def tear_down(self):
        """Tear down function of this test case"""
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
