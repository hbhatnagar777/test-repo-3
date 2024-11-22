
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
    get_unc_path()                               -- Gets a UNC path
    generate_regular_data()                      -- Generate regular files with no threats or infections.
    generate_eicar_data()                        -- Generate an EICAR file
    init_tc()                                    -- Initial configuration for the testcase
    create_subclient()                           -- Creates a subclient
    run_backup_job()                             -- Runs a backup job
    run_data_curation()                          -- Runs the data curation job on the client
    run_restore_job()                            -- Runs a restore job on the threat scan client
    cleanup()                                    -- Runs cleanup
    run()                                        -- Run function for this testcase
"""

import datetime
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import (
    ThreatScan, UnusualFileActivity)
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Server.JobManager.jobmanager_helper import JobManager

from Web.AdminConsole.Helper.GDPRHelper import GDPR
from cvpysdk.job import Job

class TestCase(CVTestCase):
    """Class for executing threat analysis job from unusual file activity page"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to validate infected files are not restored."
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "IndexServerName": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None,
            "ClientName": None,
            "MediaAgentName": None,
            "FileDownloadPath": None
        }
        # Testcase constants
        self.browser = None
        self.admin_console = None
        self.test_case_error = None
        self.backup_info = None
        self.local_path = None
        self.eicar_file = None
        self.regular_file = None

    def get_unc_path(self, local_path):
        """
        Gets a UNC path
        """
        partial_path = os.path.splitdrive(
            local_path)[1]
        partial_path = partial_path.removeprefix("\\")
        path = self.source_machine.get_unc_path(partial_path)
        return path    

    def generate_regular_data(self, num_files=100, encrypt=False, corrupt=False):
        """
            Generate regular files with no threats or infections.
        """
        path = self.get_unc_path(self.local_path)
        self.activateutils.sensitive_data_generation(
            path, number_files=num_files)
        self.expected_files_ts = num_files

    def generate_threatscan_data(self):
        """
            Generate an EICAR file
        """
        # Note the file generated
        self.eicar_files = self.activateutils.eicar_data_generation(
            self.local_path)
        self.eicar_file = str(self.eicar_files[0])
        folder_name = os.path.splitdrive(
            self.local_path)[1]
        folder_name = folder_name.removeprefix("\\")
        self.eicar_file_path = os.path.join(folder_name,self.eicar_file)
        self.log.info(f"EICAR Path: {self.eicar_file_path}")

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.client_name = self.tcinputs['ClientName']
            self.index_server_name = self.tcinputs['IndexServerName']

            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']

            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.download_directory = self.tcinputs['FileDownloadPath']
            
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)           
            self.activateutils = ActivateUtils()
            self.job_manager = JobManager(commcell=self.commcell)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
            self.gdpr_obj = GDPR(self.admin_console, self.commcell)
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
        navigator = self.admin_console.navigator

        # Note down the details of the last run job 
        job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION, client_name=client_name)

        #Navigate to Unusual file activity, Delete the existing anomaly
        navigator.navigate_to_unusual_file_activity()
        file_activity.clear_anomaly(self.client_name)
        time.sleep(cs.ONE_MINUTE)
        self.admin_console.refresh_page()

        #Add Server and start a threat scan job
        file_activity.start_threat_scan(
            client_name, index_server_name, [cs.TA_ANOMALY])

        #Fetch the threat scan job id and check the status
        running_job_details = self.gdpr_obj.get_latest_job_by_operation(cs.DATA_CURATION)
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_status = job.wait_for_completion()
        self.log.info(f"Job finished status {job_status}")
        if (job_details and running_job_details[cs.ID] == job_details[cs.ID]) or not job_status:
            raise CVTestStepFailure("Job wasn't successful.")

    @test_step
    def run_restore_job(self):
        """Runs a restore job on the threat scan client"""

        local_machine = Machine()
        client_name = self.tcinputs['ClientName']
        file_activity = UnusualFileActivity(self.admin_console)
        threat_scan = ThreatScan(self.admin_console)
        Rbrowse = RBrowse(self.admin_console)

        # Note down the details of the last restore job 
        job_details = self.gdpr_obj.get_latest_job_by_operation(cs.RESTORE_JOB, client_name=client_name)
        
        #Navigate to the threat scan server
        self.admin_console.refresh_page()
        file_activity.open_client_details(client_name)

        total_files = int(threat_scan.get_total_files_count())
        threat_files = int(threat_scan.get_row_count())

        restore_eicar_file_path = os.path.join(self.download_directory,self.eicar_file_path)

        threat_scan.select_recover_files()
        time.sleep(cs.ONE_MINUTE)
        Rbrowse.select_files(select_all=True)
        Rbrowse.submit_for_restore()

        #start an out of place restore job
        file_activity.start_data_restore(client_name,self.download_directory)

        #Fetch the restore job id and check the status
        running_job_details = self.gdpr_obj.get_latest_job_by_operation(cs.RESTORE_JOB)
        self.log.info(f"Running job details {running_job_details}")
        job = Job(self.commcell, running_job_details[cs.ID])
        self.log.info("Waiting for the job to complete.")
        job_status = job.wait_for_completion()
        self.log.info(f"Running job {running_job_details[cs.ID]}, old job {job_details[cs.ID]}")
        self.log.info(f"Job finished status {job_status}")
        if (job_details and running_job_details[cs.ID] == job_details[cs.ID]) or not job_status:
            raise CVTestStepFailure("Job wasn't successful.")

        files = local_machine.get_files_in_path(self.download_directory)
        restored_files = len(files)
        
        if (restored_files == total_files - threat_files):
            if not local_machine.check_file_exists(restore_eicar_file_path):
                self.log.info(f"Restored file count {restored_files}, matches the expected file count, threat file doesn't exist in Browse.")
            else:
                raise CVTestStepFailure(
                f"Restored file count {restored_files} matches, but threat infected file is being returned in the Browse.")
        else:
             raise CVTestStepFailure(
                f"Restored file count {restored_files}, doesn't match the expected file count") 


    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.source_machine.clear_folder_content(self.local_path)
        self.source_machine.clear_folder_content(self.download_directory)
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
            self.generate_regular_data()
            self.generate_threatscan_data()
            self.create_subclient()
            self.run_backup_job()
            self.run_data_curation()
            self.run_restore_job()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
