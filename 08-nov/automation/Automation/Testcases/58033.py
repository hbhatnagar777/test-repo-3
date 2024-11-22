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
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.maintenance import Maintenance
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from AutomationUtils.windows_machine import WindowsMachine


class TestCase(CVTestCase):
    """Class for validating copy software when user does not have access to cache"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Scenario - Copy software when user does not have access to cache"
        self.config_json = None
        self.machine_obj = None
        self.download_obj = None
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.maintenance = None
        self.windows_machine_obj = None
        self.admin_console = None
        self.navigator = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.machine_obj = Machine(self.commcell.commserv_client)
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.windows_machine_obj = WindowsMachine(self.admin_console)
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)
        self.navigator = self.admin_console.navigator
        self.maintenance = Maintenance(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Removing access for Software Cache")
            self.windows_machine_obj.modify_ace(
                user="Administrators",
                path=self.commcell.commserv_cache.get_cs_cache_path(),
                action="Deny",
                permission="FullControl",
                folder=True)
            self.log.info("Copying Windows Media to CS Cache")
            self.navigator.navigate_to_maintenance()
            self.admin_console.wait_for_completion()
            job_id = self.maintenance.run_copy_software(
                media_path=self.config_json.Install.update_path,
                auth=True,
                username=self.config_json.Install.dvd_username,
                password=self.config_json.Install.dvd_password)
            self.log.info('Job Id obtained is %s', job_id)
            job_obj = self.commcell.job_controller.get(job_id)
            if not job_obj.wait_for_completion():
                self.log.info("Failed to run copy software job with error: %s", job_obj.delay_reason)
            else:
                raise Exception("Testcase Failed. Copy software job passed. Check cache folder permissions")
            self.log.info("Resetting permission for the user")
            self.windows_machine_obj.modify_ace(
                user="Administrators",
                path=self.commcell.commserv_cache.get_cs_cache_path(),
                action="Deny",
                permission="FullControl",
                folder=True,
                remove=True)
            self.log.info("Starting copy software job with Full Control access to CS cache")
            self.deployment_helper.run_copy_software(
                media_path=self.tcinputs.get('UpdatePath'),
                auth=True,
                username=self.config_json.Install.dvd_username,
                password=self.config_json.Install.dvd_password)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.windows_machine_obj.modify_ace(
                user="Administrators",
                path=self.commcell.commserv_cache.get_cs_cache_path(),
                action="Deny",
                permission="FullControl",
                folder=True,
                remove=True)
