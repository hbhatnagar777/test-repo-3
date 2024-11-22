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
    """Class for executing threat scan with encrypt files and threats"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to validate the threat scan with encrypt files and threats"
        self.tcinputs = {
            "IndexServerName": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None,
            "ClientName": None,
            "MediaAgentName": None,
            "ControllerHostname": None
        }
        # Testcase constants
        self.browser = None
        self.admin_console = None
        self.test_case_error = None
        self.subclient_obj = None
        self.client_name = None
        self.index_server_name = None
        self.navigator = None
        self.threat_scan = None
        self.file_activity = None
        self.jobs = None
        self.expected_files_ts = None

    def get_unc_path(self, local_path):
        """
        Gets a unc path
        """
        partial_path = os.path.splitdrive(
            local_path)[1]
        partial_path = partial_path.removeprefix("\\")
        path = self.source_machine.get_unc_path(partial_path)
        return path

    def generate_sensitive_data(self, num_files=100, encrypt=False, corrupt=False):
        """
            Generate sensitive files with PII entities
        """
        path = self.get_unc_path(self.local_path)
        self.activateutils.sensitive_data_generation(
            path, number_files=num_files)
        self.expected_files_ts = num_files

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
            self.gdpr_obj = GDPR(self.admin_console, self.commcell)
            self.threat_scan = ThreatScan(self.admin_console)
            self.file_activity = UnusualFileActivity(self.admin_console)
            self.jobs = Jobs(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def run_data_curation(self):
        """Runs the data curation job on the client"""
        index_server_name = self.tcinputs['IndexServerName']
        threat_scan = ThreatScan(self.admin_console)
        navigator = self.admin_console.navigator
        controller_machine = Machine(
            machine_name=self.tcinputs['ControllerHostname'],
            commcell_object=self.commcell)

       # Note down the details of the last run job
        job_details = self.gdpr_obj.get_latest_job_by_operation(
            cs.DATA_CURATION)

        self.log.info("Creating subclient.")
        self.subclient_obj = self.activateutils.create_commcell_entities(
            self.commcell, self.tcinputs['MediaAgentName'], self.client, self.local_path,
            id=self.id)
        self.run_backup_job()

        # Encrypt the folder
        unc_path = self.get_unc_path(self.local_path)
        self.log.info(
            f"Local file path is {self.local_path} at client {self.client_name}")
        self.log.info(f"UNC path is {unc_path}")
        self.activateutils.encrypt_data(unc_path)

        self.activateutils.eicar_data_generation(unc_path, machine=controller_machine,
                                                 remote_machine=self.source_machine, number_files=10)

        self.expected_files_ts = self.expected_files_ts + 10

        # Run an incremental backup job
        self.run_backup_job(level="Incremental")

        # Navigate to unusual file activity
        navigator.navigate_to_unusual_file_activity()
        self.file_activity.start_threat_scan(
            self.client_name, index_server_name, anomaly_types=[cs.TA_ANOMALY, cs.FDA_ANOMALY])
        
        
        running_job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION)
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_finished = job.wait_for_completion()

        self.log.info(f"Job finished status {job_finished}")
        if (job_details and running_job_details[cs.ID] == job_details[cs.ID]) or not job_finished:
            raise CVTestStepFailure("Job wasn't successful.")
        
        self.admin_console.refresh_page()
        self.navigate_to_client_threat_scan()
        count = threat_scan.get_row_count()
        if count != self.expected_files_ts:
            self.log.info(
                f"Files expected {self.expected_files_ts}, files present {count}")
            raise CVTestStepFailure("Threats scan file count doesn't match.")

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

    def navigate_to_client_threat_scan(self):
        """
        Navigates to the file data report of the client

        """
        self.navigator.navigate_to_unusual_file_activity()
        self.file_activity.refresh_grid()
        self.file_activity.open_client_details(self.client_name)

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.navigator.navigate_to_unusual_file_activity()
        self.file_activity.refresh_grid()
        try:
            self.file_activity.delete_anomaly(self.client_name)
        except CVWebAutomationException:
            self.log.info("Coudln't delete anomalies")
        self.file_activity.refresh_grid()
        self.source_machine.remove_directory(self.local_path + os.sep + cs.THREAT_SCAN_FOLDER)
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
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
