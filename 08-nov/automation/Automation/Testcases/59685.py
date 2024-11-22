# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of Server Plan Scheduled Backups for OneDrive v2 client

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import time

from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "OneDrive v2: Verification of Server Plan Scheduled Backups"
        self.epoch_time = str(int(time.time()))
        self.browser = None
        self.user = None
        self.plan = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.plans_page = None
        self.bkp_start_time = None
        self.jobs = None
        self.modal_panel = None
        self.users = None
        self.cvcloud_object = None
        self.server_plan = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])

            self.jobs = Jobs(self.admin_console)
            self.modal_panel = ModalPanel(self.admin_console)

            self.bkp_start_time = str(int(self.epoch_time) + 1800)  # 30 minutes
            server_plan_time = time.strftime(
                '%I:%M %p', time.gmtime(int(self.bkp_start_time)))
            rpo_dict = o365_constants.OneDrive.RPO_DICT.value
            rpo_dict['StartTime'] = server_plan_time
            rpo_dict['AdvanceOptions'] = True
            rpo_dict['TimeZone'] = 'UTC'
            storage = o365_constants.OneDrive.STORAGE_DICT.value
            storage['pri_storage'] = self.tcinputs['Storage']
            self.server_plan = o365_constants.OneDrive.SERVER_PLAN_NAME.value + self.epoch_time

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_plan()
            self.plans_page = Plans(self.admin_console)
            self.plans_page.create_server_plan(
                self.server_plan, storage, [rpo_dict])

            self.navigator.navigate_to_office365()
            self.tcinputs['Name'] += "_OD_59685"
            self.tcinputs['ServerPlan'] = self.server_plan
            self.users = self.tcinputs['Users'].split(",")
            self.plan = self.tcinputs['Office365Plan']

            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business
            self.onedrive = OneDrive(self.tcinputs, self.admin_console)

            self.onedrive.create_office365_app()
            self._initialize_sdk_objects()

            # Data generation
            for user in self.users:
                self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.one_drive.create_files(
                    user=user,
                    no_of_docs=o365_constants.OneDrive.DOC_COUNT_FULL_BKP_JOB.value)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after app creation"""
        self.commcell.refresh()
        self.log.info("Create client object for: %s", self.tcinputs['Name'])
        self._client = self.commcell.clients.get(self.tcinputs['Name'])
        self.log.info("Create agent object for: %s", self.tcinputs['AgentName'])
        self._agent = self._client.agents.get(self.tcinputs['AgentName'])
        if self._agent is not None:
            # Create object of Instance, if instance name is provided in the JSON
            if 'InstanceName' in self.tcinputs:
                self.log.info("Create instance object for: %s", self.tcinputs['InstanceName'])
                self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
            # Create object of the Backupset class
            if 'BackupsetName' in self.tcinputs:
                self.log.info("Creating backupset object for: %s",
                              self.tcinputs['BackupsetName'])
                # If instance object is not initialized, then instantiate backupset object
                # from agent
                # Otherwise, instantiate the backupset object from instance
                if self._instance is None:
                    self._backupset = self._agent.backupsets.get(
                        self.tcinputs['BackupsetName']
                    )
                else:
                    self._backupset = self._instance.backupsets.get(
                        self.tcinputs['BackupsetName']
                    )
            # Create object of the Subclient class
            if 'SubclientName' in self.tcinputs:
                self.log.info("Creating subclient object for: %s",
                              self.tcinputs['SubclientName'])
                # If backupset object is not initialized, then try to instantiate subclient
                # object from instance
                # Otherwise, instantiate the subclient object from backupset
                if self._backupset is None:
                    if self._instance is None:
                        pass
                    else:
                        self._subclient = self._instance.subclients.get(
                            self.tcinputs['SubclientName']
                        )
                else:
                    self._subclient = self._backupset.subclients.get(
                        self.tcinputs['SubclientName']
                    )
        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    @test_step
    def verify_bkp_job_initiation(self):
        """Verify that backup jobs complete successfully"""
        try:

            self.onedrive.view_jobs()
            retry = 0
            while retry <= 10:
                time.sleep(90)
                if self.onedrive.get_jobs_count() >= 1:
                    job_id = self.jobs.get_job_ids()[0]
                    self.jobs.access_job_by_id(job_id)
                    job_details = self.jobs.job_details()
                    if (job_details['Status'] not in
                            ["Committed", "Completed", "Completed w/ one or more errors",
                             "Completed w/ one or more warnings"]):
                        raise Exception(f'Job {job_id} did not complete successfully')
                    else:
                        self.log.info(f'Job {job_id} completed successfully')
                    break
                self.browser.driver.refresh()
                retry += 1
            if retry > 10:
                raise Exception('Backup Job did not get initiated according to server plan')
        except Exception:
            raise CVTestStepFailure(f'Exception while verifying backup job initiation')

    def run(self):
        try:
            self.onedrive.add_user()

            sleep_time = int(self.bkp_start_time) - int(time.time())
            if sleep_time > 0:
                time.sleep(sleep_time)

            self.verify_bkp_job_initiation()

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.log.info("Testcase Passed")
                for user in self.users:
                    self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.cvoperations.cleanup()

                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])

                self.navigator.navigate_to_plan()
                self.plans_page.delete_plan(self.server_plan)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
