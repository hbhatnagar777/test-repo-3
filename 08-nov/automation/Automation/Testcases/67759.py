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

    run_data_curation()                          -- Runs the data curation job on the client

    core_cleanup_validation()                    -- Verifies that the delete anomaly option deletes the core

    cleanup()                                    -- Clean up the commcell entities

    run()                                        -- Run function for this testcase
"""
import os

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import \
    UnusualFileActivity
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import TestStep, handle_testcase_exception

from cvpysdk.client import Client
from cvpysdk.index_server import IndexServer
from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing delete anomaly option"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete anomaly testcase"
        self.tcinputs = {
            "IndexServerName": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None,
            "ClientName": None,
            "ControllerHostname":None,
            "MediaAgentName": None
        }
        # Testcase constants
        self.browser = None
        self.admin_console = None
        self.test_case_error = None
    
    def generate_sensitive_data(self):
        """
            Generate an EICAR file
        """
        # Note the number of files generated
        controller_machine = Machine(
                machine_name=self.tcinputs['ControllerHostname'])
        self.eicar_files = self.activateutils.eicar_data_generation(self.local_path, machine=controller_machine,
                                                                    remote_machine=self.source_machine)

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']

            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            self.activateutils = ActivateUtils()           
            self.client_name = self.tcinputs['ClientName']
            self.index_server_name = self.tcinputs['IndexServerName']  
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
            self.navigator = self.admin_console.navigator
            self.file_activity = UnusualFileActivity(self.admin_console)
            self.gdpr_obj = GDPR(self.admin_console, self.commcell)
            self.cleanup()
            
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def run_backup(self):
        """
        Runs backup 
        """
        self.log.info("Get a subclient object.")
        self.log.info("Creating subclient.")
        subclient_obj = self.activateutils.create_commcell_entities(
            self.commcell, self.tcinputs['MediaAgentName'], self.client, self.local_path,
            id=self.id)
        self.log.info("Running backup on the subclient")
        job_object = subclient_obj.backup()
        job = Job(self.commcell, job_object.job_id)
        self.log.info(f"Job with id {job_object.job_id} is submitted")
        self.log.info("Waiting for the backup job to finish.")
        job.wait_for_completion()

    @test_step
    def run_data_curation(self):
        """Runs the data curation job on the client"""

        client_name = self.tcinputs['ClientName']
        index_server_name = self.tcinputs['IndexServerName']
        # Note down the details of the last run job
        job_details = self.gdpr_obj.get_latest_job_by_operation(
            cs.DATA_CURATION)

        # Navigate to unusual file activity
        self.navigator.navigate_to_unusual_file_activity()
        self.file_activity.start_threat_scan(
            client_name, index_server_name, anomaly_types=[cs.TA_ANOMALY])

        running_job_details = self.gdpr_obj.get_latest_job_by_operation(
            cs.DATA_CURATION)
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_finished = job.wait_for_completion()

        self.log.info(f"Job finished status {job_finished}")
        if (job_details and running_job_details[cs.ID] == job_details[cs.ID]) or not job_finished:
            raise CVTestStepFailure("Job wasn't successful.")
        self.log.info("Test step passed")

    @test_step
    def core_cleanup_validation(self):
        """
        Verifies that the delete anomaly option deletes the core
        """
        self.client_obj = Client(self.commcell, self.client_name)
        index_server_obj = IndexServer(self.commcell, self.index_server_name)
        all_cores = index_server_obj.get_all_cores()[0]
        core_status = self.is_core_present(all_cores)
        if not core_status[1]:
            raise CVTestStepFailure("Threat scan core is not present")
        self.navigator.navigate_to_unusual_file_activity()
        self.file_activity.refresh_grid()
        self.file_activity.delete_anomaly(self.client_name)
        all_cores = index_server_obj.get_all_cores()[0]
        deleted_core_status = self.is_core_present(
            all_cores, core_status[0])
        if deleted_core_status[1]:
            raise CVTestStepFailure(
                "Threat scan core is present after anomaly deletion")
        self.log.info("Test step passed")

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
            self.log.info("Couldn't delete anomalies")
        self.file_activity.refresh_grid()
        storage_policy_name = f"{self.id}_storagepolicy"
        library_name = f"{self.id}_library"
        backupset_name = f"{self.id}_backupset"
        self.source_machine.remove_directory(self.local_path + os.sep + cs.THREAT_SCAN_FOLDER)
        self.file_activity.refresh_grid()
        self.activateutils.activate_cleanup(
            commcell_obj=self.commcell,
            client_name=self.client_name,
            backupset_name=backupset_name,
            storage_policy_name=storage_policy_name,
            library_name=library_name
        )
    
    def is_core_present(self, all_cores, core_name=None):
        """
        Returns true if the index server core is present
        """
        self.log.info(all_cores)
        index_server_core = ''
        core_present = False
        for core in all_cores:
            if self.client_obj.client_id in core:
                index_server_core = core
                core_present = True
        return [index_server_core, core_present]

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.run_backup()
            self.run_data_curation()
            self.core_cleanup_validation()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
