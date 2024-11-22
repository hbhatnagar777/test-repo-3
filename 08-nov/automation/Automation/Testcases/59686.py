# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of User-Level Backup of OneDrive v2 client

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import time

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "OneDrive v2: Verification of User-Level Backup"
        self.browser = None
        self.users = None
        self.plan = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.single_user = None
        self.jobs = None
        self.modal_panel = None
        self.file_server = None
        self.dest_path = None
        self.mssql = None
        self.csdb_helper = None
        self.solr_helper_obj = None
        self.cvcloud_object = None

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

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.tcinputs['Name'] += "_OD_59686"
            self.users = self.tcinputs['Users'].split(",")
            self.single_user = self.users[0]
            self.users.remove(self.single_user)

            self.csdb_helper = CSDBHelper(self)
            self.jobs = Jobs(self.admin_console)
            self.modal_panel = ModalPanel(self.admin_console)

            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business
            self.onedrive = OneDrive(self.tcinputs, self.admin_console)

            self.mssql = MSSQL(
                self.tcinputs['SQLServerName'],
                self.tcinputs['SQLUserName'],
                self.tcinputs['SQLPassword'],
                'CommServ',
                as_dict=False)

            self.onedrive.create_office365_app()
            self._initialize_sdk_objects()

            # Data generation
            self.cvcloud_object.one_drive.delete_folder(user_id=self.single_user)
            self.cvcloud_object.one_drive.create_files(
                user=self.single_user,
                no_of_docs=o365_constants.OneDrive.DOC_COUNT_FULL_BKP_JOB.value)
            for user in self.users:
                self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.one_drive.create_files(
                    user=user,
                    no_of_docs=o365_constants.OneDrive.DOC_COUNT_FULL_BKP_JOB.value)

            time.sleep(60)  # Give time for OneDrive sync

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
    def verify_job_completion(self, job_id):
        """Verify that backup jobs complete successfully"""
        try:
            self.jobs.access_job_by_id(job_id)
            job_details = self.jobs.job_details()
            if (job_details['Status'] not in
                    ["Committed", "Completed", "Completed w/ one or more errors",
                     "Completed w/ one or more warnings"]):
                raise Exception(f'Job {job_id} did not complete successfully'
                                f' - Job Status: {job_details["Status"]}')
            else:
                self.log.info(f'No. of items backed up: {job_details["No of objects backed up"]}')
                self.log.info(f'Job {job_id} completed successfully')
        except Exception:
            raise CVTestStepFailure(f'Job {job_id} did not complete successfully')

    @test_step
    def verify_restore_docs_count(self, job_details):
        """
        Verify count of documents restored against count of documents in index
        """
        try:
            query_url = self.csdb_helper.get_index_server_url(
                self.mssql, client_name=self.tcinputs['Name'])
            query_url += '/select?'
            self.solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
            solr_results = self.solr_helper_obj.create_url_and_get_response({'keyword': '*'})
            index_count = int(self.solr_helper_obj.get_count_from_json(solr_results.content))
            # 3 users are restored, root folder count would be 3 * FILTERS_RESTORE_FOLDER_COUNT
            doc_count = index_count - 3 * o365_constants.OneDrive.FILTERS_RESTORE_FOLDER_COUNT.value
            self.log.info(f'Document Count obtained from Index: {doc_count}')
            restore_count = int(job_details['No of files restored']) - - 2*3 # removing folders count
            self.log.info(f'Documents in index: {doc_count};'
                          f' Documents restored: {restore_count}')
            if doc_count != restore_count:
                raise Exception('Count Mismatch for Restore of all documents in client')
        except Exception:
            raise CVTestStepFailure(f'Verification of count FAILED')

    def run(self):
        try:
            self.onedrive.add_user()
            single_user_bkp = self.onedrive.initiate_backup([self.single_user])
            multiple_user_bkp = self.onedrive.initiate_backup(self.users)

            time.sleep(10)
            self.onedrive.view_jobs()
            retry = 0
            while retry <= 10:
                time.sleep(90)
                if self.onedrive.get_jobs_count() >= 2:
                    self.verify_job_completion(job_id=single_user_bkp)
                    self.verify_job_completion(job_id=multiple_user_bkp)
                    break
                self.browser.driver.refresh()
                retry += 1

            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])
            restore_job = self.onedrive.run_restore(
                destination=o365_constants.RestoreType.TO_DISK,
                file_server=self.tcinputs['FileServer'],
                dest_path=self.tcinputs['DestPath'])

            self.verify_restore_docs_count(restore_job)

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.log.info("Testcase Passed")
                for user in self.users:
                    self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.one_drive.delete_folder(user_id=self.single_user)
                self.cvcloud_object.cvoperations.cleanup()
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
