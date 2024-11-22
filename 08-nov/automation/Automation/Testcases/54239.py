# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks for JobStartTime feature

Steps in this test case:
    Creates a company

    Creates a plan

    Associates the created plan with created company with JobStartTime set on it

    Validates the JobStartTime feature

    Deletes the company, plan and servers associated with the company

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
        self.name = "Basic Test Case for JobStartTime Feature"
        self.log = None
        self.show_to_user = False
        self.helper = None
        self.new_company = None
        self.new_plan = None
        self.plan_name = None
        self.company_name = None
        self.tcinputs = {
            "StoragePoolName": None
        }

    def run(self):
        """Follows the following steps
        1) Creating a company
        2) Creating a plan
        3) Associating the created plan to company with 40 mins delay from the current time
        4) Associating CS client to the company
        5) Checking if the client is ready or not
        6) Associating tenant admin as the client admin of the company
        7) Setting the sleep time for 30 mins such that server gets associated with Smart Client group
        8) Creating a backupset
        9) Checking if any jobs are trigerred for the default subclient of the created backupset
        """

        try:
            self.csdb = database_helper.CommServDatabase(self.commcell)
            self.machine_obj = Machine(self.commcell.commserv_name, self.commcell)
            self.utility = OptionsSelector(self.commcell)

            now = datetime.now()
            self.company_name = "company{0}".format(now)
            self.mail_id = "bboinapally@commvault.com"
            self.log.info("Step 1: Creating a company %s", self.company_name)
            self.new_company = self.commcell.organizations.add(
                self.company_name, self.mail_id, self.company_name, self.company_name
            )
            self.plan_name = "plan{0}".format(now)
            self.log.info("Step 2: Creating a plan %s", self.plan_name)
            self.new_plan = self.commcell.plans.add(
                self.plan_name, 'Server', self.tcinputs["StoragePoolName"], 1440
            )
            self.log.info("Step 3: Associating the created plan to company with 60 mins delay from the client time")
            time_on_machine = self.machine_obj.get_system_time().split(':')
            job_start_time_value = (int(time_on_machine[0])*60*60) + (int(time_on_machine[1])*60) + 3600
            self.new_company.plans = [{
                'plan_name': self.plan_name,
                'job_start_time': job_start_time_value
            }]
            plan_details = self.new_company.plan_details
            temp_dict = {}
            for plans in plan_details:
                temp_dict[plans['plan']['planName']] = plans
            temp_dict[self.plan_name]['jobStartTime']
            self.log.info("Step 4: Associating CS client to the company")
            self.windows_client = self.commcell.clients.get(self.commcell.commserv_name)
            self.log.info("Step 5: Checking if the client is ready or not")
            if not self.windows_client.is_ready:
                self.log.error("Check readiness for the windows client failed")
            self.log.info("Step 6: Associating tenant admin as the client admin of the company")
            dict_ = {
                "assoc1":
                    {
                        'clientName': [self.commcell.commserv_name],
                        'role': ["Client Admins"]
                        }
                }
            self.commcell.users.get(
                r"{0}\bboinapally".format(self.company_name)).update_security_associations(dict_, "UPDATE")
            self.log.info("Step 7: Setting the sleep time for 30 mins such that server gets "
                          "associated with Smart Client group")
            self.utility.sleep_time(1800)
            self.log.info("Step 8: Creating a backupset")
            self.backupset_name = "backupset{0}".format(now)
            self.agent.backupsets.add(backupset_name=self.backupset_name, plan_name=self.plan_name)
            self.utility.sleep_time(900)
            self.log.info("Step 10:  Checking if any jobs are trigerred for the default "
                          "subclient of the created backupset")
            total_time_elapsed = 0
            while True:
                query2 = (
                    "select jobId from JMBkpJobInfo where applicationId = "
                    "(select id from APP_Application where clientId = '{0}' and subclientName = 'default' and backupSet ="
                    "(select id from APP_BackupSetName where name = '{1}'))").format(self.commcell.commcell_id,
                                                                                     self.backupset_name)
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
                self.log.info("Validation : Job Trigerred as per the Job Start Time set at company level")
            else:
                raise Exception("Job is not trigerred because of JobStartTime set at company level")

        except Exception as exp:
            self.log.error(str(exp))
            self.log.error("Test Case FAILED")
            self.status = constants.FAILED
            self.result_string = str(exp)

        finally:

            self.new_company.dissociate_plans([self.plan_name])

            dict_ = {
                "assoc1":
                    {
                        'clientName': [self.commcell.commserv_name],
                        'role': ["Client Admins"]
                        }
                }
            self.commcell.users.get(
                r"{0}\bboinapally".format(self.company_name)).update_security_associations(dict_, "DELETE")

            self.commcell.organizations.delete(self.company_name)
