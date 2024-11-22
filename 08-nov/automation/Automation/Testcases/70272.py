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
    generate_threatscan_data()                   -- Generate an EICAR file
    init_tc()                                    -- Initial configuration for the testcase
    create_subclient()                           -- Creates a subclient
    delete_anomaly()                             -- Clears the existing anomaly
    run_backup_job()                             -- Runs a backup job
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
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import (
    ThreatScan, UnusualFileActivity)
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

from Web.AdminConsole.Helper.GDPRHelper import GDPR
from cvpysdk.job import Job

class TestCase(CVTestCase):
    """Class for executing threat analysis job from unusual file activity page"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to validate threat name is dispalyed correctly for TA files."
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
        self.backup_info = None
        self.local_path = None
        self.eicar_files = None
        self.threat_name = ['Eicar-Test-Signature']

    def generate_threatscan_data(self):
        """
            Generate an EICAR file
        """
        self.log.info(f"Local file path is {self.local_path}")
        # Note the file generated
        self.eicar_files = self.activateutils.eicar_data_generation(
            self.local_path)
        self.log.info(f"The file generated is {self.eicar_files}")
        self.eicar_file_path = os.path.join(self.local_path,self.eicar_files[0])
        self.log.info(f"The file path of the EICAR file is {self.eicar_file_path}")

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
            self.navigator = self.admin_console.navigator
            self.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def create_subclient(self):
        """
        Creates a subclient 
        """
        self.log.info("Get a subclient object.")
        self.log.info("Creating subclient.")
        self.subclient_obj = self.activateutils.create_commcell_entities(
            self.commcell, self.tcinputs['MediaAgentName'], self.client, self.local_path,
            id=self.id)    
        
    def delete_anomaly(self):
        """
        Clears the existing anomaly
        """   
        file_activity = UnusualFileActivity(self.admin_console)
        navigator = self.admin_console.navigator
        navigator.navigate_to_unusual_file_activity()
        file_activity.clear_anomaly(self.client_name)
        time.sleep(cs.ONE_MINUTE)
        file_activity.refresh_grid()

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


    @test_step
    def run_data_curation(self):
        """Runs the data curation job on the client"""

        client_name = self.tcinputs['ClientName']
        index_server_name = self.tcinputs['IndexServerName']
        file_activity = UnusualFileActivity(self.admin_console)
        threat_scan = ThreatScan(self.admin_console)
        navigator = self.admin_console.navigator

        # Note down the details of the last run job 
        job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION, client_name=client_name)

        #Delete the existing anomaly
        navigator.navigate_to_unusual_file_activity()
        file_activity.clear_anomaly(self.client_name)
        time.sleep(cs.ONE_MINUTE)
        self.admin_console.refresh_page()

        #Add Server and start a threat scan job
        file_activity.start_threat_scan(
            client_name, index_server_name, [cs.TA_ANOMALY])

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
        file_activity.open_client_details(client_name)

        fileCorrupted = threat_scan.get_suspicious_file_info(self.eicar_file_path,'Corrupt')
        self.log.info(f"Is File Marked Corrupt? {fileCorrupted}")
    
        threatDetected = threat_scan.get_suspicious_file_info(self.eicar_file_path,'Threats')
        self.log.info(f"The detected threat is {threatDetected}")
        
        if threatDetected != self.threat_name:
            raise CVTestStepFailure(
                "Threat detected doesn't match with threat expected.")
        else:
            if fileCorrupted != ['Yes']:
                raise CVTestStepFailure(
                "Threat is detected correctly, but file isn't marked as corrupt.")
            else:
                self.log.info(
                f"Threat detected is correct, and file is marked as corrupt")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.source_machine.clear_folder_content(self.local_path)
        self.delete_anomaly()
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
            self.generate_threatscan_data()
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
