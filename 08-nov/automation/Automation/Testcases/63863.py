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

    generate_sensitive_data()                    -- Generates sensitive files with PII entities

    init_tc()                                    -- Initial configuration for the testcase

    run_data_curation()                          -- Runs the data curation job on the client

    verify_mark_safe_action()                    -- Marks the file safe and verifies
    
    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import datetime
import os

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import (
    ThreatScan, UnusualFileActivity)
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception

from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing threat scan remediation action"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to validate the threat scan mark safe remediation action"
        self.tcinputs = {
            "IndexServerName": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None,
            "ClientName": None,
            "MediaAgentName": None
        }
        # Testcase constants
        self.browser = None
        self.admin_console = None
        self.test_case_error = None
        self.subclient_obj = None
        self.backup_start_time_obj = None
        self.client_name = None
        self.index_server_name = None
        self.navigator = None
        self.threat_scan = None
        self.file_activity = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        partial_path = partial_path.removeprefix("\\")
        unc_path = self.source_machine.get_unc_path(partial_path)
        self.activateutils.sensitive_data_generation(
            unc_path, number_files=100)

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.client_name = self.tcinputs['ClientName']
            self.index_server_name = self.tcinputs['IndexServerName']
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']

            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            self.activateutils = ActivateUtils()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
            self.threat_scan = ThreatScan(self.admin_console)
            self.file_activity = UnusualFileActivity(self.admin_console)
            self.navigator = self.admin_console.navigator      
            self.gdpr_obj = GDPR(self.admin_console, self.commcell)    
            self.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def run_data_curation(self):
        """Runs the data curation job on the client"""

        # Note down the details of the last run job
        job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION)
        self.log.info(job_details)

        self.log.info("Creating subclient.")
        self.subclient_obj = self.activateutils.create_commcell_entities(
            self.commcell, self.tcinputs['MediaAgentName'], self.client, self.local_path,
            id=self.id)
        self.run_backup_job()

        # Corrupt the folder
        self.log.info(f"Local file path is {self.local_path}")
        self.activateutils.encrypt_data(self.local_path)

        self.run_backup_job(level=cs.INCREMENTAL)

        # Navigate to unusual file activity
        self.navigator.navigate_to_unusual_file_activity()

        # Sample time obtained from the job 2023-03-16 00:38:22.392282
        self.run_threat_scan(
            self.client_name, self.index_server_name, [cs.FDA_ANOMALY])

        running_job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION,active_job=True)
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_finished = job.wait_for_completion()

        if running_job_details[cs.ID] == job_details[cs.ID] or not job_finished:
            raise CVTestStepFailure("Job wasn't successful.")
        self.file_activity.refresh_grid()

    def run_backup_job(self, level=cs.FULL):
        """
        Runs an incremental job
        """
        # Run an incremental backup job
        job_object = self.subclient_obj.backup(backup_level=level)
        self.log.info(f"Job with id {job_object.job_id} is submitted")
        job = Job(self.commcell, job_object.job_id)
        self.log.info("Waiting for the job to finish.")
        job.wait_for_completion()
        end_time_obj = datetime.datetime.now()
        return end_time_obj

    def run_threat_scan(self, client_name, index_server_name, anomaly):
        """
        Runs threat analysis job

        """
        self.file_activity.start_threat_scan(
            client_name, index_server_name, anomaly)

    @test_step
    def verify_mark_safe_action(self):
        """Marks the file safe and verifies"""

        suspicious_files_count = self.threat_scan.get_suspicious_files_count()
        self.log.info(
            f"Number of suspicious files present {suspicious_files_count}")
        file = self.activateutils.get_random_file_from_path(
            self.source_machine, self.local_path)
        self.log.info("Marking a file safe")
        self.log.info(f"File chosen is {file}")
        #keyword_arr = file.split()
        #search_keyword = ' '.join((keyword_arr[0], keyword_arr[1]))
        search_keyword = f"*{file}*"
        self.log.info(f"Search keyword is {search_keyword}")
        self.threat_scan.mark_safe(search_keyword, file)
        new_count = self.threat_scan.get_suspicious_files_count()
        self.log.info(f"Number of suspicious files present now: {new_count}")
        self.threat_scan.search_for_keyword(search_keyword)
        num = self.threat_scan.get_row_count()
        if num != 0 and new_count != suspicious_files_count-1:
            raise CVTestStepFailure(
                "Marked safe file is present in the report")
        self.log.info("Mark safe action completed.")

    def navigate_to_client_threat_scan(self, client):
        """
        Navigates to the file data report of the client

        """
        self.file_activity.click_client_action(self.client_name, cs.DETAILS)

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.navigator.navigate_to_unusual_file_activity()
        try:
            self.file_activity.delete_anomaly(self.client_name)
        except CVWebAutomationException:
            self.log.info("Coudln't delete anomalies")
        self.file_activity.refresh_grid()
        storage_policy_name = f"{self.id}_storagepolicy"
        library_name = f"{self.id}_library"
        backupset_name = f"{self.id}_backupset"
        self.activateutils.activate_cleanup(
            commcell_obj=self.commcell,
            client_name=self.client_name,
            backupset_name=backupset_name,
            storage_policy_name=storage_policy_name,
            library_name=library_name
        )

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.run_data_curation()
            self.navigate_to_client_threat_scan(self.client_name)
            self.verify_mark_safe_action()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
