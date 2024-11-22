# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    clear_existing_zip_from_temp()      --  Clear the existing zip files from the temp directory

    restore()                           --  Runs out of place restore of a Windows file system client

    validate_data()                     --  Validates data after restore

    run()                               --  run function of this test case

"""

import os
import re
from glob import glob
import time
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Application.CloudStorage.azure_helper import AzureFileShareHelper
from AutomationUtils import constants, machine
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Restore validation of Windows FS client to Azure File Share Object Storage from command center
        Example inputs:
        "70507": {
                  "fs_client_name": "WINDOWS FS CLIENT NAME",
                  "fs_subclient_name: "FS SUBCLIENT NAME", # Optional, default is 'default'
                  "dest_cloud": "CROSS CLOUD - FILE SHARE DESTINATION CLIENT ON CS",
                  "dest_cloud_path": "PATH ON THE CLOUD DESTINATION CLIENT",
                  "account_name": "AZURE ACCOUNT NAME",
                  "access_key": "AZURE ACCESS KEY",
            }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.fs_client_name = None
        self.dest_cloud = None
        self.dest_cloud_path = None
        self.fs_client = None
        self.azure_helper = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.original_data_path = None
        self.restored_data_path = None
        self.controller_object = None
        self.common_dir_path = None
        self.file_server = None
        self.file_server_subclient = None
        self.fs_subclient_name = None
        self.bucket_name = None
        self.AUTOMATION_DIRECTORY = None
        self.TEMP_DIR = None
        self.zip_file = None
        self.db_helper = None
        self.tcinputs = {
            "fs_client_name": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "account_name": None,
            "access_key": None,
        }

    def setup(self):
        """ Setup function of this test case """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                 self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.admin_console.navigator

        # Helper objects
        self.file_server = FileServers(self.admin_console)
        self.file_server_subclient = Subclient(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

        # Cloud Helper
        self.azure_helper = AzureFileShareHelper(account_name=self.tcinputs.get('account_name'),
                                                 access_key=self.tcinputs.get("access_key"))

        # Helper variables initialization
        self.controller_object = machine.Machine()
        self.common_dir_path = self.azure_helper.common_dir_path
        self.fs_client_name = self.tcinputs.get("fs_client_name")
        self.fs_subclient_name = self.tcinputs.get("fs_subclient_name", "default")
        self.dest_cloud = self.tcinputs.get("dest_cloud")
        self.dest_cloud_path = self.tcinputs.get("dest_cloud_path")
        self.bucket_name = self.tcinputs.get("dest_cloud_path")[1:]

        # Define the path to the temp directory of the automation
        self.AUTOMATION_DIRECTORY = os.path.dirname(os.path.dirname(__file__))
        self.TEMP_DIR = os.path.join(self.AUTOMATION_DIRECTORY, 'temp')

    @test_step
    def unzip_downloaded_file(self):
        """ Unzips the downloaded data onto the original_data_path """

        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.db_helper.unzip_downloaded_file(self.TEMP_DIR, self.original_data_path)
        self.log.info("Unzipping downloaded file done!")

    @test_step
    def clear_existing_zip_from_temp(self):
        """ Clear the existing zip files from the temp directory """
        try:
            zip_files = glob(os.path.join(self.TEMP_DIR, 'Download_*.zip'))
            if not zip_files:
                self.log.info("No existing zip files found in the temp directory")
                return
            for file in zip_files:
                os.remove(file)
            self.log.info(f"Cleared {len(zip_files)} existing zip files from the temp directory")
        except Exception as exp:
            self.log.error(f"Failed to clear existing zip files from the temp directory with error: {exp}")

    @test_step
    def navigate_to_subclient_listing_page(self):
        """ Navigates to the FS client's sub-client's listing page """

        # Navigate to file servers
        self.navigator.navigate_to_file_servers()
        self.admin_console.wait_for_completion()

        # Access the file server client
        self.file_server.access_server(self.fs_client_name)
        self.admin_console.access_tab(self.admin_console.props['label.subclients'])
        self.admin_console.wait_for_completion()

    @test_step
    def cleanup(self):
        """ Cleaning up the temp files created during the test case execution """

        if self.azure_helper is not None:
            self.azure_helper.azure_file_share_cleanup()

    @test_step
    def validate_data(self):
        """ Validates data after restore"""

        self.log.info("original path : %s", self.original_data_path)
        self.log.info("restored path : %s", self.restored_data_path)

        restore_status = self.controller_object.compare_folders(self.controller_object,
                                                                self.original_data_path,
                                                                self.restored_data_path)
        if len(restore_status) > 0:
            raise CVTestStepFailure("Restore to Given destination Failed During Validation")
        self.log.info("Restore Validation Succeeded")

    @test_step
    def restore(self):
        """ Runs out of place restore of a Windows file system client """

        # Download data for the given subclient from the file server
        self.navigate_to_subclient_listing_page()
        self.log.info("Downloading container from FS")
        notification = self.file_server_subclient.download_selected_items(subclient_name=self.fs_subclient_name,
                                                                          select_all=True)
        # Get the job id from the notification
        jobid = None
        match = re.search(r'\(job (\d+)\)', notification)
        jobid = match.group(1)
        self.log.info("Download job started with jobid: %s", jobid)

        if jobid:
            self.db_helper.wait_for_job_completion(jobid)
            self.log.info("Download job completed successfully. Waiting for 5 minutes before unzipping files")
            time.sleep(300)

            # Unzip the downloaded data onto the original_data_path
            self.unzip_downloaded_file()

            # Start restore job for the given subclient
            self.navigate_to_subclient_listing_page()
            self.log.info("Starting restore job")
            jobid = self.file_server_subclient.restore_subclient(subclient_name=self.fs_subclient_name,
                                                                 dest_client=self.dest_cloud,
                                                                 destination_path=self.dest_cloud_path,
                                                                 cloud_client=True)
            self.db_helper.wait_for_job_completion(jobid)
            self.log.info("Restore job completed successfully")

            # Download data for the given subclient from the cloud
            self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
            self.log.info("Downloading container from cloud")
            self.azure_helper.download_file_share(self.bucket_name, "restored_contents")
            self.log.info("Downloading bucket done!")

            # Validate
            self.validate_data()
        else:
            raise CVTestStepFailure("Failed to download data from the file server")

    def run(self):
        """Run function of this test case"""
        try:
            self.clear_existing_zip_from_temp()
            self.restore()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
