# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Backup job Suspend and Resume

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogs
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
        self.name = "OneDrive v2: Backup job Suspend and Resume"
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
        self.job = None
        self.job_details = None
        self.view_logs = None
        self.backup_job_id = None
        self.accessnode = None
        self.accessnode_machine = None
        self.job_res_dir = None
        self.rst_job_details = None
        self.input_doc_count = None
        self.backup_doc_count = None
        self.solr_doc_count = None
        self.restore_doc_count = None
        self.first_processed_user = None


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
            self.tcinputs['Name'] = "OD_63733"
            self.users = self.tcinputs['Users'].split(",")
            self.plan = self.tcinputs['Office365Plan']
            self.accessnode = self.tcinputs['AccessNode']
            self.input_doc_count = 200

            self.csdb_helper = CSDBHelper(self)
            self.jobs = Jobs(self.admin_console)
            self.job_details = JobDetails(self.admin_console)
            self.view_logs = ViewLogs(self.admin_console)
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

            self.job_res_dir=self.cvcloud_object.cvoperations.get_job_results_dir()

            # #Data generation
            # self.cvcloud_object.one_drive.delete_folder(user_id=self.users[0])
            # self.cvcloud_object.one_drive.create_files(user=self.users[0],no_of_docs=120,pdf=True)
            #
            # self.cvcloud_object.one_drive.delete_folder(user_id=self.users[1])
            # self.cvcloud_object.one_drive.create_files(user=self.users[1], no_of_docs=120,pdf=True)
            #
            # time.sleep(60)  # Give time for OneDrive sync

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
        self.accessnode_machine = Machine(
            self.accessnode, self.commcell
        )
        self.log.info('Initialized Proxy Machine Object')
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
    def add_users(self, users, plan):
        """
        adding users
        Args:
                users (list)       --   list of users
                plan (str)         --   Office365 plan
        """
        try:
            self.onedrive.refresh_cache()
            time.sleep(30)  # time to refresh
            self.onedrive.add_user(users, plan)
        except Exception:
            raise CVTestStepFailure(f'Adding users failed')

    @test_step
    def edit_streams(self,stream_count):
        """
        editing number of streams

        Args:
            stream_count(int)  :  Number of streams to be set
        """
        try:
            self.admin_console.access_tab("Configuration")
            self.onedrive._edit_stream_count(stream_count)
            self.admin_console.access_tab("Users")
        except Exception:
            raise CVTestStepFailure(f'Editing streams failed')

    @test_step
    def backup_users(self):
        """Backup newly associated users of the client"""
        self.log.info('Starting backup Job..')
        self.job = self.subclient.backup()
        self.backup_job_id = self.job.job_id
        self.log.info('Job Id: %d', int(self.backup_job_id))
        self.log.info('Job start time(Unix): %s', str(self.job.start_timestamp))

    @test_step
    def wait_until_user_backup(self):
        """wait until one user backup"""
        initial_folders = len(self.accessnode_machine.get_folders_in_path(self.job_res_dir))
        self.log.info('Initial number of folders in job results dir: %d', initial_folders)

        if initial_folders == 1:
            self.first_processed_user = (self.accessnode_machine.get_folders_in_path(self.job_res_dir)[0].split("\\"))[-1]

        for _ in range(60):
            time.sleep(10)

            current_folders = len(self.accessnode_machine.get_folders_in_path(self.job_res_dir))
            self.log.info("Current number of folders in Job results dir: %d", current_folders)

            if self.first_processed_user == None and current_folders == 1:
                self.first_processed_user=(self.accessnode_machine.get_folders_in_path(self.job_res_dir)[0].split("\\"))[-1]

            if initial_folders==0:
                if current_folders - initial_folders >= 2:
                    break
            else:
                if current_folders - initial_folders >= 1:
                    break

    @test_step
    def suspend_job(self):
        """Suspend the job"""
        self.log.info('Trying to suspend the job..')

        self.job.pause(wait_for_job_to_pause=True)
        if self.job.status.lower() != 'suspended':
            raise CVTestStepFailure('Failed to Suspend the Job')

        self.log.info('Job Successfully Suspended')
        time.sleep(10)

    @test_step
    def resume_job(self):
        """Resume the job"""
        self.log.info('Trying to resume the job..')

        self.job.resume(wait_for_job_to_resume=True)
        if self.job.status.lower() != 'running':
            raise CVTestStepFailure('Failed to resume the Job')

        self.log.info('Job Successfully Resumed')
        time.sleep(5)

    @test_step
    def kill_job(self, wait_for_job_to_kill=True):
        """Kills the job"""
        try:
            self.log.info("Killing active job [{0}]".format(self.job.job_id))
            self.job.kill(wait_for_job_to_kill)
            if self.job.status.lower() == 'killed':
                self.log.info('Job is killed successfully')
            elif self.job.status.lower() == 'committed':
                self.log.info('Job is committed successfully')
            else:
                raise Exception('Job is not killed with Job status : {0}'.format(self.job.status.lower()))
        except Exception as exception:
            self.log.exception("Failed to kill job [{0}] with error : {1}".format(self.job.job_id, exception))

    @test_step
    def verify_backed_up_user_logs(self):
        """verify logs"""
        try:
            self.jobs.access_job_by_id(self.backup_job_id)
            self.job_details.view_logs()
            time.sleep(45)
            indexed_list=self.view_logs.get_log_lines_by_search(job_view_logs=True,search_string="Already indexed")
            first_user_stats =[i.split(" - ")[1] for i in indexed_list if self.first_processed_user in i]
            self.log.info(first_user_stats[1])
            if (int((first_user_stats[1].split(" ")[2])[1:-1]))>=(self.input_doc_count//2):
                self.log.info("first processed user is not picked up again")
            else:
                raise Exception("first processed user is picked up again")
            self.admin_console.driver.back()
            self.admin_console.driver.back()  #navigate back to Users tab
        except Exception:
            raise CVTestStepFailure(f'verifying logs failed')


    @test_step
    def verify_backup(self):
        """verify backup"""
        try:
            self.admin_console.refresh_page()
            items=self.onedrive.get_browse_table_content(columns=["Email address","Number of items"])
            user_list=[]
            self.backup_doc_count=0
            for each in items:
                self.backup_doc_count=self.backup_doc_count+int(each["Number of items"])
                if each["Number of items"]=='0':
                    user_list.append(each["Email address"])
            self.log.info(f'Documents given as input: {self.input_doc_count};'
                          f'Documents backed up: {self.backup_doc_count}')
            if self.input_doc_count!=self.backup_doc_count:
                raise  Exception("Count mismatch in backup")
            if len(user_list)==0:
                raise Exception("Job not killed immediately")
            elif len(user_list)>1:
                for each in user_list:
                    self.log.info(f'No data backed up for user: {each}')
                raise Exception("More than one user is not backed up")
            else:
                self.log.info(f'No data backed up for user: {user_list[0]}')
                self.log.info(f'Single user not backed up successfully')
        except Exception:
            raise CVTestStepFailure(f'verify backup failed')

    @test_step
    def verify_browse_and_restore(self):
        """verify browse and restore"""
        try:
            query_url = self.csdb_helper.get_index_server_url(
                self.mssql, client_name=self.tcinputs['Name'])
            query_url += '/select?'
            self.solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
            solr_results = self.solr_helper_obj.create_url_and_get_response({'DocumentType': '1'})
            self.solr_doc_count = int(self.solr_helper_obj.get_count_from_json(solr_results.content))
            self.onedrive._select_all_users()
            self.onedrive._click_restore(account=False)
            self.rst_job_details = self.onedrive.run_restore(destination=o365_constants.RestoreType.IN_PLACE,restore_option=o365_constants.RestoreOptions.OVERWRITE)
            self.restore_doc_count = int(self.rst_job_details['No of files restored'])-2  # Automation folder is restored for both users that are backed up
            self.log.info(f'Documents present in solr index: {self.solr_doc_count};'
                          f' Documents backed up: {self.backup_doc_count};'
                          f' Documents restored: {self.restore_doc_count}')
            if self.solr_doc_count!=self.restore_doc_count or self.restore_doc_count!=self.backup_doc_count :
                raise Exception('Count Mismatch in Restore')
            self.log.info('Browse and Restore verified successfully')
        except Exception:
            raise CVTestStepFailure(f'verify restore failed')


    def run(self):
        """Run function of this test case"""
        try:
            self.add_users(self.users, self.plan)
            self.edit_streams(1)
            self.backup_users()
            time.sleep(30)   #waiting some time for job results directory creation
            self.wait_until_user_backup()
            self.suspend_job()
            time.sleep(30)   #waiting some time after suspending job
            self.resume_job()
            self.wait_until_user_backup()
            self.kill_job()
            time.sleep(30)  #waiting some time after killing job
            self.verify_backed_up_user_logs()
            self.verify_backup()
            self.verify_browse_and_restore()

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == constants.PASSED:
                self.cvcloud_object.cvoperations.cleanup()
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

