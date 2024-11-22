# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for OneDrive v2 functionality testing of Full and Incremental backup and PIT restore

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import time

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.one_drive import OneDrive
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
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
        self.testcaseutils = CVTestCase
        self.name = "Onedrive v2: Verification of Full and Incremental backup and PIT restore"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.users = None
        self.cvcloud_object = None
        self.csdb_helper = None
        self.solr_helper_obj = None
        self.mssql = None
        self.jobs = None
        self.file_server = None
        self.dest_path = None
        self.full_solr_count = 0
        self.incr_solr_count = 0
        self.full_bkp_items_counts=0
        self.incr_bkp_items_count=0
        self.full_restore_count = 0
        self.incr_restore_count = 0

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

            self.csdb_helper = CSDBHelper(self)
            self.jobs = Jobs(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.tcinputs['Name'] += "_OD_59442"
            self.users = self.tcinputs['Users'].split(",")
            self.file_server = self.tcinputs['FileServer']
            self.dest_path = self.tcinputs['DestPath']

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

            # self.onedrive.access_office365_app("OneDrive_v2_1653425006")
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
    def get_document_count_in_index(self, job_id, full=False):
        """
        Query Index Server wrt Job Id to get Document count

        Args:
            job_id: Job Id of backup job
            full:   Whether backup job is full or incremental

        """
        try:
            query_url = self.csdb_helper.get_index_server_url(self.mssql, job_id)
            query_url += '/select?'
            self.solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                {'JobId': job_id, 'DocumentType': '1'})
            if full:
                self.full_solr_count = int(self.solr_helper_obj.get_count_from_json(solr_results.content))
                self.log.info(f'Document Count obtained from Index: {self.full_solr_count}')
                return self.full_solr_count
            else:
                self.incr_solr_count = int(self.solr_helper_obj.get_count_from_json(solr_results.content))
                self.log.info(f'Document Count obtained from Index: {self.incr_solr_count}')
                return self.incr_solr_count
        except Exception:
            raise CVTestStepFailure(f'Error while querying index')

    @test_step
    def verify_full_bkp_and_incr_bkp(self,full_bkp_items_count,incr_bkp_items_count):
        """
        Verify Incremental backup is not backing up same items again

        """
        try:
            self.log.info(f'Full backup items count in solr is: {full_bkp_items_count}')
            self.log.info(f'Incremental backup items count in solr is: {incr_bkp_items_count}')
            if full_bkp_items_count>=15 and incr_bkp_items_count<=8:
                self.log.info(f'Full and Incremental backup jobs are working as expected')
            elif full_bkp_items_count<15 and incr_bkp_items_count<=8+15-full_bkp_items_count:
                self.log.info(f'Full and Incremental backup jobs are working as expected')
            else:
                raise Exception('Incremental backup is not working correctly')
        except Exception:
            raise CVTestStepFailure(f'Verification of Incremental backup FAILED')

    @test_step
    def verify_restore_docs_count_full(self):
        """
        Verify count of documents restored against count of documents in index
        """
        try:
            self.log.info(f'Documents in index: {self.full_solr_count};'
                          f' Documents restored: {self.full_restore_count}')
            if self.full_solr_count != self.full_restore_count+4:
                raise Exception('Count Mismatch for PIT Restore of Full backup job')
        except Exception:
            raise CVTestStepFailure(f'Verification of count FAILED')

    @test_step
    def verify_restore_docs_count_incr(self):
        """
        Verify count of documents restored against count of documents in index
        """
        try:
            self.log.info(f'Documents in index: {self.incr_solr_count};'
                          f' Documents restored: {self.incr_restore_count}')
            if self.incr_restore_count != self.incr_solr_count:
                raise Exception('Count Mismatch for PIT Restore of Incremental Job')
        except Exception:
            raise CVTestStepFailure(f'Verification of count FAILED')

    def run(self):
        try:
            # Addition of users to Office 365 App and initiation of backup
            self.onedrive.add_user()
            job_details = self.onedrive.run_backup()
            full_bkp_job = job_details['Job Id']
            full_bkp_time = job_details['Start time']
            self.full_bkp_items_count=self.get_document_count_in_index(full_bkp_job, full=True)
            self.log.info(f'Full bkp items count = {self.full_bkp_items_count}')
            # Data generation for incremental job
            for user in self.users:
                self.cvcloud_object.one_drive.create_files(
                    user=user,
                    no_of_docs=o365_constants.OneDrive.DOC_COUNT_INCR_BKP_JOB.value,
                    new_folder=False)

            # Initiate incremental backup job
            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])
            job_details = self.onedrive.run_backup()
            incr_bkp_job = job_details['Job Id']
            incr_bkp_time = job_details['Start time']
            self.incr_bkp_items_count=self.get_document_count_in_index(incr_bkp_job)
            self.log.info(f'Incr bkp items count = {self.incr_bkp_items_count}')

            #Verification of Incremental backup
            self.verify_full_bkp_and_incr_bkp(self.full_bkp_items_count,self.incr_bkp_items_count)

            # Point-In-Time Restore
            for user in self.users:
                self.navigator.navigate_to_office365()
                self.onedrive.access_office365_app(self.tcinputs['Name'])
                job_details = self.onedrive.point_in_time_restore(
                    user_name=user,
                    time=full_bkp_time,
                    file_server=self.file_server,
                    dest_path=self.dest_path)
                restore_count = (int(job_details['No of files restored']) -
                                 o365_constants.OneDrive.PIT_RESTORE_FOLDER_COUNT.value)
                self.log.info(f'Full Bkp Job Restore file count for user {user}: {restore_count}')
                self.full_restore_count += restore_count

                self.navigator.navigate_to_office365()
                self.onedrive.access_office365_app(self.tcinputs['Name'])
                job_details = self.onedrive.point_in_time_restore(
                    user_name=user,
                    time=incr_bkp_time,
                    file_server=self.file_server,
                    dest_path=self.dest_path)
                count = (int(job_details['No of files restored']) -
                         o365_constants.OneDrive.PIT_RESTORE_FOLDER_COUNT.value
                         - restore_count)
                self.log.info(f'Incr Bkp Job Restore file count for user {user}: {count}')
                self.incr_restore_count += count

            # Validation of PIT Restore
            self.verify_restore_docs_count_full()
            self.verify_restore_docs_count_incr()

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                for user in self.users:
                    self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.cvoperations.cleanup()
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
