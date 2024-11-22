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

Inputs:

    UpdatePath      -- path of the update

"""
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.maintenance import Maintenance
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for Copying software when there is no media in cache"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Copying software when there is no media in cache"
        self.config_json = None
        self.download_obj = None
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.maintenance = None
        self.admin_console = None
        self.deployment_helper = None
        self.maintenance = None
        self.machine_obj = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.machine_obj = Machine(self.commcell.commserv_client)
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)
        self.maintenance = Maintenance(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                self.log.info("Deleting cache")
                self.commcell.commserv_cache.delete_cache()

                self.log.info("Commiting cache")
                self.commcell.commserv_cache.commit_cache()
            except Exception as exp:
                self.log.warning("Unable to delete CS cache")

            self.maintenance.admin_page.navigate_to_maintenance()
            self.admin_console.wait_for_completion()

            self.log.info("Copying Windows Media to CS Cache")
            # Creating a dummy folder to use
            path = "/opt/dummy" if 'UNIX' in self.machine_obj.os_info else "C:\\dummy"
            media_path = self.machine_obj.create_directory(path, force_create=True)
            job_id = self.maintenance.run_copy_software(media_path=path)
            self.log.info("Job Id Obtained is %s", job_id)
            job_obj = self.commcell.job_controller.get(job_id)
            if not job_obj.wait_for_completion():
                raise Exception("Copy software job failed. Please check logs - %s", job_obj.pending_reason)
            if job_obj.status == 'Completed w/ one or more warnings':
                self.log.info("Copy software job completed with one or more warnings - %s", job_obj.pending_reason)
            else:
                raise Exception("Negative Scenario testcase failed. Please check logs")

            self.log.info("Downloading media")
            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value])
            if not job.wait_for_completion():
                raise Exception("download job failed. Check logs - %s", job.delay_reason)
            self.log.info("Download software completed successfully")

            self.log.info("Running copy software job after populating cache")
            self.deployment_helper.run_copy_software(
                media_path=self.config_json.Install.update_path,
                auth=True,
                username=self.config_json.Install.dvd_username,
                password=self.config_json.Install.dvd_password)
            # Deleting the created dummy folder
            delete_dir = self.machine_obj.remove_directory(path)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        job = self.commcell.download_software(
            options=DownloadOptions.LATEST_HOTFIXES.value,
            os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value])
        if not job.wait_for_completion():
            pass
        self.admin_console.logout()
