# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                   -- Initializes TestCase class

    generate_sensitive_data()                    -- Generate an EICAR file

    init_tc()                                    -- Initial configuration for the testcase

    run_backup()                                 -- Runs backup

    run_data_curation()                          -- Runs the data curation job on the client

    verify_event()                               -- Verifies threat scan event

    run()                                        -- Run function for this testcase
"""
import datetime

from cvpysdk.eventviewer import Event, Events
from cvpysdk.job import Job

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import (
    ThreatScan, UnusualFileActivity)
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing threat analysis job from unusual file activity page"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance test for threat scan job and event verification"
        self.tcinputs = {
            "IndexServerName": None,
            "FileServerLocalDirectoryPath": None,
            "ClientName": None,
            "Subclient": None
        }
        # Testcase constants
        self.browser = None
        self.admin_console = None
        self.test_case_error = None
        self.backup_info = None
        self.local_path = None
        self.eicar_files = None

    def generate_sensitive_data(self):
        """
            Generate an EICAR file
        """
        self.log.info(f"Number of files present in the path {self.local_path}")
        self.log.info(f"Local file path is {self.local_path}")
        # Note the number of files generated
        self.eicar_files = self.activateutils.eicar_data_generation(
            self.local_path)

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']

            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.activateutils = ActivateUtils()

            self.generate_sensitive_data()
            self.run_backup()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
            self.gdpr_obj = GDPR(self.admin_console, self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def run_backup(self):
        """
        Runs backup 
        """
        instance_name = "defaultinstancename"
        backupset_name = "defaultBackupSet"
        timezone = self.commcell.commserv_timezone
        timezone_name = self.commcell.commserv_timezone_name

        self.log.info(f"Commserver's timezone is {timezone}")
        self.log.info(f"Commserver's timezone name is {timezone_name}")
        self.log.info("Get a subclient object.")
        client_obj = self.commcell.clients.get(self.tcinputs['ClientName'])
        agent_obj = client_obj.agents.get(cs.FILE_SYSTEM)
        instance = agent_obj.instances.get(instance_name)
        backupset = instance.backupsets.get(backupset_name)
        subclient_obj = backupset.subclients.get(self.tcinputs['Subclient'])

        start_time_obj = datetime.datetime.now()
        self.log.info("Running backup on the subclient")
        job_object = subclient_obj.backup()
        job = Job(self.commcell, job_object.job_id)
        self.log.info(f"Job with id {job_object.job_id} is submitted")
        self.log.info(f"Job started at {start_time_obj}")
        self.log.info("Waiting for the backup job to finish.")
        job.wait_for_completion()
        end_time_obj = datetime.datetime.now()

        # Sample time obtained from the job 2023-03-16 00:38:22.392282

        start_date_time = self.activateutils.get_date_time_dict_calendarview(
            start_time_obj)
        start_date = start_date_time.get("date")
        start_time = start_date_time.get("time")

        end_date_time = self.activateutils.get_date_time_dict_calendarview(
            end_time_obj)
        end_date = end_date_time.get("date")
        end_time = end_date_time.get("time")

        self.log.info(f"start date {start_date} start time {start_time}")
        self.log.info(f"end date {end_date} end time {end_time}")
        self.backup_info = {}
        self.backup_info["start_date"] = start_date
        self.backup_info["start_time"] = start_time
        self.backup_info["end_date"] = end_date
        self.backup_info["end_time"] = end_time

    @test_step
    def verify_event(self):
        """
        Verifies the event generated in Commcell
        """
        events_obj = Events(self.commcell)
        event_dict = events_obj.events(
            {"jobId": str(self.jobID)}, details=True)
        event_id = None
        self.log.info(event_dict)
        for id in event_dict.keys():
            if event_dict.get(id).get('eventCodeString') == cs.THREAT_SCAN_EVENT_CODE:
                self.log.info(f"Event id is {id}")
                event_id = id
        if event_id:
            event = Event(self.commcell, event_id)
            self.log.info(event.event_code)
            self.log.info(event)
        else:
            self.test_case_error = "Threat scan event didn't get generated"

    @test_step
    def run_data_curation(self):
        """Runs the data curation job on the client"""

        client_name = self.tcinputs['ClientName']
        index_server_name = self.tcinputs['IndexServerName']
        file_activity = UnusualFileActivity(self.admin_console)
        threat_scan = ThreatScan(self.admin_console)
        navigator = self.admin_console.navigator

        start_date = self.backup_info.get("start_date")
        start_time = self.backup_info.get("start_time")
        end_date = self.backup_info.get("end_date")
        end_time = self.backup_info.get("end_time")

        # Note down the details of the last run job
        job_details = self.gdpr_obj.get_latest_job_by_operation(
            cs.DATA_CURATION, client_name=client_name)

        navigator.navigate_to_unusual_file_activity()
        file_activity.open_client_details(client_name)
        old_count = threat_scan.get_row_count()
        self.log.info(f"Number of threat scan files in the report {old_count}")

        # Navigate to unusual file activity
        navigator.navigate_to_unusual_file_activity()
        file_activity.start_threat_scan(
            client_name, index_server_name, anomaly_types=[
                cs.TA_ANOMALY], start_date=start_date,
            start_time=start_time, end_date=end_date, end_time=end_time)

        running_job_details = self.gdpr_obj.get_latest_job_by_operation(
            cs.DATA_CURATION)
        self.jobID = running_job_details.get("Id")
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_finished = job.wait_for_completion()

        self.log.info(f"Job finished status {job_finished}")
        if (job_details and running_job_details[cs.ID] == job_details[cs.ID]) or not job_finished:
            raise CVTestStepFailure("Job wasn't successful.")

        navigator.navigate_to_unusual_file_activity()
        file_activity.open_client_details(client_name)

        count = threat_scan.get_row_count()
        num_eicar_files = len(self.eicar_files)
        if count != (num_eicar_files + old_count):
            self.log.info(
                f"Files expected {num_eicar_files + old_count}, files present {count}")
            self.test_case_error = "Threats detected file count doesn't match."
        else:
            self.log.info("Test step passed")

    def run(self):
        try:
            self.init_tc()
            self.run_data_curation()
            self.verify_event()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
