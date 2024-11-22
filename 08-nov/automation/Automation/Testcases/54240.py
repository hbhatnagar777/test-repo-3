# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks for JobStartTime feature

Steps in this test case:

    Creates a plan

    Associates the created plan with created existing client with JobStartTime set on it

    Validates the JobStartTime feature

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from datetime import datetime
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Class for executing JobStartTime Check test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Test Case for JobStartTime Feature at client level"
        self.log = None
        self.show_to_user = False
        self.new_plan = None
        self.plan_name = None
        self.tcinputs = {
            "StoragePoolName": None
        }

    def run(self):
        """Follows the following steps
        1) Creating a plan
        2) Associating the created plan to client with 10 mins delay from the current time
        3) Checking if the client is ready or not
        4) Creating a backupset with the plan created
        5) Checking if any jobs are trigerred for the created subclient of the created backupset
        """

        try:
            self.csdb = database_helper.CommServDatabase(self.commcell)
            self.machine_obj = Machine(self.client)
            self.utility = OptionsSelector(self.commcell)

            now = datetime.now()
            self.plan_name = "plan{0}".format(now)
            self.log.info("Step 1: Creating a plan %s", self.plan_name)
            self.new_plan = self.commcell.plans.add(
                self.plan_name, 'Server', self.tcinputs["StoragePoolName"], 1440
            )
            time_on_machine = self.machine_obj.get_system_time().split(':')
            job_start_time_value = (int(time_on_machine[0])*60*60) + (int(time_on_machine[1])*60) + 600
            self.log.info("Step 2: Setting the jobstarttime to 10 mins from the current value")
            self.windows_client = self.commcell.clients.get(self.tcinputs['ClientName'])
            self.windows_client.set_job_start_time(job_start_time_value)
            self.log.info("Step 3: Checking if the client is ready or not")
            if not self.windows_client.is_ready:
                self.log.error("Check readiness for the windows client failed")
            self.log.info("Step 4: Creating a backupset")
            self.backupset_name = "backupset{0}".format(now)
            backuset_object = self.agent.backupsets.add(backupset_name=self.backupset_name, plan_name=self.plan_name)
            self.log.info("Step 5:  Checking if any jobs are trigerred for the created "
                          "subclient of the created backupset")
            self.utility.sleep_time(300)
            total_time_elapsed = 0
            while True:
                query2 = (
                    "select jobId from JMBkpJobInfo where applicationId = "
                    "(select id from APP_Application where clientId = '{0}' and subclientName = 'default' and backupSet ="
                    "(select id from APP_BackupSetName where name = '{1}'))").format(
                    self.client.client_id, self.backupset_name
                )
                self.csdb.execute(query2)
                if (self.csdb.rows[0][0]):
                    job_id = self.csdb.rows[0][0]
                    query_jst = (
                        "select jobStartTime from jmjobinfo where jobid = {0}"
                    ).format(job_id)
                    self.csdb.execute(query_jst)
                    job_started_time = self.csdb.rows[0][0]
                    self.log.info("Job Trigerred as per the Job Start Time set at company level")
                    break

                if total_time_elapsed >= 1200:
                    raise Exception("Job is not trigerred as per the job start time set at company level for plan")

                total_time_elapsed = total_time_elapsed + 60
                self.log.info("Waiting for another 60 seconds")
                self.utility.sleep_time(60)

            job_time = (datetime.fromtimestamp(int(job_started_time)).strftime('%H:%M')).split(':')
            actual_job_start_time = (int(job_time[0])*60*60) + (int(job_time[1])*60)
            if actual_job_start_time >= job_start_time_value:
                self.log.info("Validation : Job Trigerred as per the Job Start Time set at client level")
            else:
                raise Exception("Job is not trigerred because of JobStartTime set at client level")

        except Exception as exp:
            self.log.error(str(exp))
            self.log.error("Test Case FAILED")
            self.status = constants.FAILED
            self.result_string = str(exp)

        finally:
            self.commcell.plans.delete(self.plan_name)
