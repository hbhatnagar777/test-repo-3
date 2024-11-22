# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.maintenance import Maintenance
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for copy software job when disk is full"""

    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Scenario - copy software when disk is full"
        self.config_json = None
        self.machine_obj = None
        self.no_space_drive = None
        self.download_obj = None
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.maintenance = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "drive_path": None,
            "update_path": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.machine_obj = Machine(
            machine_name=self.commcell.commserv_name,
            commcell_object=self.commcell)
        self.log.info("machine object %s", self.machine_obj)
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser,
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.navigator = self.admin_console.navigator
        self.maintenance = Maintenance(self.admin_console)
        self.no_space_drive = self.tcinputs["drive_path"]

    def run(self):
        """Main function for test case execution"""
        try:

            path = self.no_space_drive.split(":")[0]

            drive_space = self.machine_obj.get_storage_details()[path]['available']
            self.log.info("available space %s", drive_space)
            available_drive_space = drive_space - 500
            self.log.info("space %s", available_drive_space)
            extra_files_path = self.machine_obj.join_path(self.no_space_drive,"files")

            if available_drive_space > 200:
                # Filling up the drive with random files to make the drive to have less disk space
                file_size = (available_drive_space * 1000 / 50) - 1000
                flag = self.machine_obj.generate_test_data(file_path=extra_files_path,
                                                           file_size=int(file_size),
                                                           dirs=5,
                                                           files=10)
                self.log.info("returned output: %s", flag)
                if not flag:
                    raise Exception("Failed to fill up space")

            self.log.info("Copying updates to CS Cache")
            self.navigator.navigate_to_maintenance()
            self.admin_console.wait_for_completion()
            job_id = self.maintenance.run_copy_software(
                media_path=self.tcinputs["update_path"], auth=True,
                username=self.config_json.Install.dvd_username,
                password=self.config_json.Install.dvd_password)
            self.log.info('Job Id obtained is %s', job_id)
            job = self.commcell.job_controller.get(job_id)

            JobManager(job, self.commcell).wait_for_state('failed')

            # freeing up the space in drive by deleting the random files
            if self.machine_obj.check_directory_exists(extra_files_path):
                self.machine_obj.remove_directory(extra_files_path)

            job_status = job.delay_reason
            self.log.info("JobFailingReason: %s", job_status)

            self.log.info("Starting copy software job after emptying disk")
            job_id = self.maintenance.run_copy_software(
                media_path=self.tcinputs["update_path"], auth=True,
                username=self.config_json.Install.dvd_username,
                password=self.config_json.Install.dvd_password)
            self.log.info('Job Id obtained is %s', job_id)
            job = self.commcell.job_controller.get(job_id)

            JobManager(job, self.commcell).wait_for_state()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
