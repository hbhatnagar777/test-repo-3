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
    create_subclient()                           -- Creates a subclient
    run_backup_job()                             -- Runs a backup job
    init_tc()                                    -- Initial configuration for the testcase
    run_data_curation()                          -- Runs the data curation job on the client
    cleanup()                                    -- Runs cleanup
    run()                                        -- Run function for this testcase
"""
import time
import os

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import (
    ThreatScan, UnusualFileActivity)
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

from Web.AdminConsole.Helper.GDPRHelper import GDPR
from cvpysdk.job import Job

NUM_FILES = 100


class TestCase(CVTestCase):
    """Class for executing data curation job on unusual file activity"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to validate data curation job with no suspicious files"
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

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        partial_path = partial_path.removeprefix("\\")
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=NUM_FILES)
        
    def create_subclient(self):
        """
        Runs backup 
        """
        self.log.info("Get a subclient object.")
        self.log.info("Creating subclient.")
        self.subclient_obj = self.activateutils.create_commcell_entities(
            self.commcell, self.tcinputs['MediaAgentName'], self.client, self.local_path,
            id=self.id)    
        
    def run_backup_job(self, level=cs.FULL):
        """
        Runs a backup job
        """
        # Run a backup job
        self.log.info("Running backup on the subclient")
        job_object = self.subclient_obj.backup(backup_level=level)
        self.log.info(f"Job with id {job_object.job_id} is submitted")
        job = Job(self.commcell, job_object.job_id)
        self.log.info("Waiting for the job to finish.")
        job.wait_for_completion() 

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

        client_name = self.tcinputs['ClientName']
        index_server_name = self.tcinputs['IndexServerName']
        file_activity = UnusualFileActivity(self.admin_console)
        navigator = self.admin_console.navigator

        # Note down the details of the last run job
        job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION)

        #Navigate to Unusual file activity, Delete the existing anomaly
        navigator.navigate_to_unusual_file_activity()
        file_activity.clear_anomaly(self.client_name)
        self.admin_console.refresh_page()
        time.sleep(cs.ONE_MINUTE)
        
        #Add Server and start a threat scan job
        file_activity.start_threat_scan(
            client_name, index_server_name, [cs.FDA_ANOMALY])
        
        #Fetch the threat scan job id and check the status
        running_job_details = self.gdpr_obj.get_latest_job_by_operation(cs.RESTORE_JOB)
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_status = job.wait_for_completion()
        self.log.info(f"Job finished status {job_status}")
        if (job_details and running_job_details[cs.ID] == job_details[cs.ID]) or not job_status:
            raise CVTestStepFailure("Job wasn't successful.")
        
        self.admin_console.refresh_page()
        client_file_count = file_activity.get_file_count(client_name)
        if client_file_count != 0:
            raise CVTestStepFailure("Suspected file count is not zero.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.source_machine.clear_folder_content(self.local_path)
        storage_policy_name = f"{self.id}_storagepolicy"
        library_name = f"{self.id}_library"
        backupset_name = f"{self.id}_backupset"
        self.activateutils.activate_cleanup(
            commcell_obj=self.commcell,
            client_name=self.tcinputs['ClientName'],
            backupset_name=backupset_name,
            storage_policy_name=storage_policy_name,
            library_name=library_name
        )

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.create_subclient()
            self.run_backup_job()
            self.run_data_curation()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)