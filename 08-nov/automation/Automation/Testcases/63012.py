# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Dynamics 365: Basic Test case for Backup and Restore

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
import random
import time
from typing import Set, Any, List

from Application.Dynamics365.constants import D365JobPhases
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception
from Application.Dynamics365 import CVDynamics365


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365 CRM: Backup Advanced Cases.

    Example for test case inputs:
        "63012":
        {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "ServerPlan": "<Server-Plan>>",
          "IndexServer": <Index-Server>>,
          "AccessNode": <access-node>>,
          "office_app_type": "Dynamics365",
          "TokenAdminUser": <global-admin-userid>>,
          "TokenAdminPassword": <global-admin-password>>,
          "application_id":<azure-app-application-id>,
          "azure_directory_id":<azure-tenet-id>,
          "application_key_value":<azure-app-key-value>,
          "D365_Plan": "<name-of-D365-Plan>>",
          "D365_Instance":[<D365-Instance-to-backup>]

        }
    """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type

                        Ex: {

                             "MY_INPUT_NAME": None

                        }

                browser                 (object)    --  Browser object

                navigator               (object)    --  Navigator Object for Admin Console
                admin_console           (object)    --  Admin Console object

                client_name             (str)       --   Name of Dynamics 365 Client
                d365_obj                (object)    --   Object of CVDynamics 365 class
                machine                 (object)    --  Object of Machine Class
        """
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365 CRM: Backup Advanced Cases. "
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name = None
        self.d365_helper: Dynamics365Helper = None
        self.cv_dynamics365: CVDynamics365 = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname, enable_ssl=True)

            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'],
                stay_logged_in=True)
            self.log.info("Logged in to Admin Console")

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_dynamics365()
            self.log.info("Navigated to D365 Page")

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Helper(admin_console=self.admin_console, tc_object=self,is_react=True)
            self.cv_dynamics365 = CVDynamics365(self)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_tables_for_removal(self, remove_tables: str) -> list[Any]:
        """
            Get 5 tables at random for manually associating
        """
        _tables_manual_association = list()
        for _table in remove_tables.split(','):
            _tables_manual_association.append((_table, self.tcinputs.get('D365_Instance')))
        self.log.info("Setting Tables: {} to association type Manual".format(_tables_manual_association))
        return _tables_manual_association

    def verify_all_phases_for_backup_job(self, job_id: int):
        """
            Method to verify that all phases ran successfully for the backup job
        """
        _phases = self.cv_dynamics365.csdb_operations.get_phases_for_job(job_id=job_id)

        for _d365_job_phase in D365JobPhases:
            if _d365_job_phase.value not in _phases:
                self.log.info("Phase: {} with ID:{} not found for Job: {}".format(_d365_job_phase.name,
                                                                                  _d365_job_phase.value, job_id))
                raise Exception("All phases were not run for the backup job")

    def kill_job_after_interval(self, job, interval: int = 200):
        """
            Kill the job after some interval.
        """
        self.log.info("Killing Job: {} after interval: {}".format(job.job_id, interval))
        time.sleep(interval)
        job.kill()
        time.sleep(10)
        job.wait_for_completion()  # for archive index and finalize to complete

    def verify_last_backup_for_tables(self, job, processed_tables: list = list(), excluded_tables: list = None):
        """
            Verify that the last backup time is correctly populated for the tables/
        """
        _start_time = job.details
        _end_time = job.details

        _job_start_time = int(job.start_timestamp)
        _job_end_time = int(job.end_timestamp)

        _content_tables = self.subclient.get_associated_tables(refresh=True)
        for _table in _content_tables:
            if _table.get("name").lower() in processed_tables or (excluded_tables is not None
                                                                  and _table.get(
                        "name").lower() not in excluded_tables):
                _table_processed_time = _table.get("userAccountInfo", {}).get('lastBackupJobRanTime', {}).get("time",
                                                                                                              -1)

                if not (_job_end_time >= _table_processed_time >= _job_start_time):
                    self.log.info("Table Processed Time is not correct: {}".format(_table_processed_time))
                    self.log.info("Job Processed Time is: {} to {}".format(_job_start_time, _job_end_time))
                    raise CVTestStepFailure(
                        " Exception in verifying the last backup time for table: {} ".format(_table))

                # run check

    def run(self):
        """Run function for the test case"""
        try:
            self.log.info("Creating Dynamics 365 CRM Client")
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.cv_dynamics365.client_name = self.client_name

            self.log.info("Initializing SDK objects")
            self.d365_helper.initialize_sdk_objects_for_client()

            self.cv_dynamics365.d365_operations.associate_environment()
            self.log.info("Associated Dynamics 365 Instance")

            self.log.info("Populating Accounts")
            self.cv_dynamics365.d365api_helper.create_accounts(instance_name=self.d365_helper.d365instances[0],
                                                               number_of_records=3000)
            self.log.info("Populating Contacts")
            self.cv_dynamics365.d365api_helper.create_contacts(instance_name=self.d365_helper.d365instances[0],
                                                               number_of_records=3000)

            self.log.info("Running a backup for the Dynamics 365 CRM client.")
            _bkp_job = self.subclient.backup()
            self.log.info("Backup Started for client: {} with Job: {}".format(self.client_name, _bkp_job))

            # kill job in 3 minutes. all phases should be run after that
            self.kill_job_after_interval(_bkp_job)
            self.log.info("Killed Job: {}".format(_bkp_job.job_id))

            self.log.info("Verifying if all Phases were run correctly for Job with ID: {}".format(_bkp_job.job_id))
            self.verify_all_phases_for_backup_job(job_id=_bkp_job.job_id)
            self.log.info("Verified that Archive Index and Finalize were run for a killed job")

            self.log.info("Marking some tables as manually associated")
            _associated_tables = self.subclient.get_associated_tables(refresh=True)
            _tables_for_manual_association = self.get_tables_for_removal(self.tcinputs.get('Remove_Tables'))

            self.cv_dynamics365.d365_operations.associate_tables(tables_list=_tables_for_manual_association)
            self.log.info("Marked tables: {} as Manually Associated".format(_tables_for_manual_association))

            self.log.info("Verifying Environment Level backup is not picking up manually associated tables")
            self.log.info("Populating Accounts")
            self.cv_dynamics365.d365api_helper.create_accounts(instance_name=self.d365_helper.d365instances[0],
                                                               number_of_records=100)
            _env_bkp_job = self.cv_dynamics365.d365_operations.run_d365_environment_backup()

            _tables_removed = [_table for _env, _table in _tables_for_manual_association]
            self.verify_last_backup_for_tables(job=_env_bkp_job, excluded_tables=_tables_removed)
            self.log.info("Verified that Environment Level backup is not picking up manually associated tables")

            self.log.info("Verifying backup for manually associated tables")
            self.log.info("Populating Data")
            for tables in _tables_for_manual_association:
                self.cv_dynamics365.d365api_helper.create_table_records(tables[0], tables[1])
            self.log.info("Tables data Populated")
            _selected_table_bkp_job = self.cv_dynamics365.d365_operations.run_d365_tables_backup(
                tables_list=_tables_for_manual_association)
            self.verify_last_backup_for_tables(job=_selected_table_bkp_job, processed_tables=_tables_removed)
            self.log.info("Verified backup for manually associated tables")

            _all_tables = [_table.get("name") for _table in _associated_tables]
            self.log.info("Verifying backup for Dynamics 365 CRM client")
            self.log.info("Populating Accounts")
            self.cv_dynamics365.d365api_helper.create_accounts(instance_name=self.d365_helper.d365instances[0],
                                                               number_of_records=100)
            _all_table_bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup()
            self.verify_last_backup_for_tables(job=_all_table_bkp_job, processed_tables=_all_tables)
            self.log.info("Verified backup for Dynamics 365 CRM client")
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function for the test case"""
        try:
            if self.status == constants.PASSED:
                self.cv_dynamics365.d365_operations.delete_d365_client()
                self.cv_dynamics365.d365api_helper.delete_accounts(
                    instance_name=self.cv_dynamics365.d365instances[0])
                self.cv_dynamics365.d365api_helper.delete_contacts(
                    instance_name=self.cv_dynamics365.d365instances[0])

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
