# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

"""
Answer File :
"57801": {
  "ClientName": "",
  "AgentName": "",
  "BackupsetName": "",
  "PlanName": "",
  "StoragePolicyName": "",
  "TestPath": "",
  "RestorePath": "",
  "IsNetworkShareClient": false,
}
"""

import time
from AutomationUtils.config import get_config
from Web.AdminConsole.Hub.constants import FileObjectTypes, HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import SubclientOverview
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for executing this test case

            Verifying Add/Delete exclusions and exceptions at subclient level from command center
            We will check the following cases:

            1. Set Exclusion and Exceptions -> FULL -> Restore -> Validation
            2. Edit Exclusion and Exceptions -> INCR -> Restore -> Validation

            #TODO : Add support for NAS
    """
    SUBCLIENT_NAME = 'Test_57801'
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.slash_format = None
        self.name = "Verifying Add/Delete exclusions and exceptions at subclient level from command center"
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.subclient = None
        self.fs_sub_client = None
        self.sub_client_details = None
        self.file_server = None
        self.fs_helper = None
        self.config = get_config()
        self.restore_path = None
        self.proxy_client = None
        self.machine = None
        self.client_machine = None
        self.delimiter = None
        self.os_name = None
        self.is_client_network_share = None
        self.hostname = None
        self.username = None
        self.password = None
        self.test_path = None
        self.exclusions = []
        self.exceptions = []
        self.step = ""
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "PlanName": None,
            "TestPath": None,
            "RestorePath": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """
        self.utils = TestCaseUtils(self)

        try:
            self.fs_helper = FSHelper(self)
            self.fs_helper.populate_tc_inputs(self, mandatory=False)
            if "cv_fs_automation_{0}".format(self.id) not in self.test_path:
                self.test_path = "{0}{1}{2}".format(
                    self.test_path.rstrip(self.slash_format), self.slash_format, self.id)
            self.is_client_network_share = self.tcinputs.get('IsNetworkShareClient', False)

        except Exception as exp:
            raise CVTestCaseInitFailure(exp)

    def run(self):
        """Run function for test case execution"""
        try:
            self.log_stage_details("executing testcase", str(self.id))
            self.define_content_and_filters()
            self.login()
            self.add_subclient()
            self.backup_job(Backup.BackupType.FULL)
            self.refresh()
            self.restore()
            self.edit_paths_and_verify()

        except Exception as excp:
            handle_testcase_exception(self, excp)

    def tear_down(self):
        if self.cleanup_run:
            self.delete_sub_client()
            self.logout()

    def log_stage_details(self, stage, scenario="", beginning=True):
        """Prints scenario details

        Args:
            stage:(str)    --   What step of testcase is the process currently in
            scenario:(str) --  Prints testcase id.
            beginning:(bool)  -- Determines if we're printing details during the beginning or end of a scenario.

        Returns: None

        Raises: None
        """

        if beginning:
            self.log.info("********************************")
            self.log.info("STARTED : %s : %s", stage, scenario)
            self.log.info("********************************")
        else:
            self.log.info("********************************")
            self.log.info("END OF %s", stage)
            self.log.info("********************************")

    def define_content_and_filters(self):
        """ Define the subclient content, exclusions and exceptions """
        self.step = "Step1. Generating data, defining exclusion and exceptions client machine"
        self.log_stage_details(self.step)
        self.fs_helper.generate_testdata(['.html', '.css'], self.test_path, 4)
        if self.is_client_network_share:
            if self.client_machine.os_info.lower() == 'windows':
                share_name = self.test_path.split('\\')[1]
                try:
                    self.client_machine.unshare_directory(share_name)
                except Exception:
                    pass
                self.client_machine.share_directory(share_name, self.test_path)
            else:
                pass
                # TODO: Add a way to share folder to NFS server
        files_list = self.client_machine.get_files_in_path(self.test_path)
        self.exclusions = [file for file in files_list if file.endswith(".html")]
        for i in range(0, len(self.exclusions)):
            if i % 3 == 0:
                self.exceptions.append(self.exclusions[i])
        self.log_stage_details(self.step, beginning=False)

    def login(self):
        """Log-in to the admin console after starting a browser object"""
        self.step = "Step2. Log-in to the admin console"
        self.log_stage_details(self.step)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)

        # Updated login method to use paramters from config.json
        # Added this so that cases can be handled from autocenter
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

        self.hub_dashboard = Dashboard(
            self.admin_console,
            HubServices.file_system,
            app_type=FileObjectTypes.file_server
        )

        try:
            self.admin_console.click_button("OK, got it")
        except BaseException:
            self.log.info("No Popup seen")

        self.file_server = FileServers(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        self.sub_client_details = SubclientOverview(self.admin_console)
        self.log_stage_details(self.step, beginning=False)

    def logout(self):
        """Logs out from the admin console and closes the browser object"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.log.info("\nLOGOUT SUCCESSFUL")

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')

    def refresh(self):
        """ Refreshes the current page """
        time.sleep(60)
        self.admin_console.refresh_page()

    def navigate_to_subclient(self):
        """Navigates to the subclient page for both NAS and FS clients"""
        self.admin_console.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.file_server.access_server(self.client.display_name)
        if self.is_client_network_share:
            if self.client_machine.os_info.lower() == 'windows':
                self.fs_sub_client.access_cifs()
            else:
                self.fs_sub_client.access_nfs()
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    @test_step
    def delete_sub_client(self):
        """ Verifies whether subclient exists or not and then deletes the subclient """
        if self.fs_sub_client.is_subclient_exists(subclient_name=self.SUBCLIENT_NAME,
                                                  backupset_name=self.tcinputs['BackupsetName']):
            self.log.info("DELETING PRE-EXISTING SUBCLIENT : %s", self.SUBCLIENT_NAME)
            self.fs_sub_client.delete_subclient(subclient_name=self.SUBCLIENT_NAME,
                                                backupset_name=self.tcinputs['BackupsetName'])
            self.log.info("\nDELETED SUBCLIENT : %s", self.SUBCLIENT_NAME)

    @test_step
    def add_subclient(self):
        """ Creates new subclient
                Raises:
                    Exception:
                        -- if fails to add entity
        """
        self.step = "Step3. Creating new subclient"
        self.log_stage_details(self.step)
        self.navigate_to_subclient()
        self.delete_sub_client()
        backup_data = self.test_path
        self.log.info("\n\nCREATING SUBCLIENT : %s", self.SUBCLIENT_NAME)
        if self.client_machine.os_info.lower() == 'windows':
            path = self.test_path.split('\\')
            if self.is_client_network_share:
                backup_data = f"\\\\{self.client_machine.machine_name}\\" + '\\'.join(path[1:])
                replace_drive_letter = lambda x: f"\\\\{self.client_machine.machine_name}" + x.replace(path[0], '')
                self.exclusions = [replace_drive_letter(exclusion) for exclusion in self.exclusions]
                self.exceptions = [replace_drive_letter(exception) for exception in self.exceptions]
        else:
            path = self.test_path.split('//')[1:]
        if self.is_client_network_share:
            self.fs_sub_client.add_subclient(subclient_name=self.SUBCLIENT_NAME, 
                                             contentpaths=[backup_data], 
                                             plan_name=self.tcinputs['PlanName'],
                                             contentfilters=self.exclusions, 
                                             contentexceptions=self.exceptions,
                                             impersonate_user={'username': self.username,
                                                               'password': self.password})
        else:
            self.fs_sub_client.add_subclient(subclient_name=self.SUBCLIENT_NAME,
                                             backupset_name=self.tcinputs['BackupsetName'],
                                             plan_name=self.tcinputs['PlanName'],
                                             contentpaths=[backup_data],
                                             contentfilters=self.exclusions,
                                             contentexceptions=self.exceptions,
                                             define_own_content=True,
                                             remove_plan_content=True)

        self.backupset.subclients.refresh()
        self.subclient = self.backupset.subclients.get(self.SUBCLIENT_NAME)
        self.log_stage_details(self.step, beginning=False)

    @test_step
    def backup_job(self, backup_type):
        """ Function to run a backup job
            Args:
                backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
            Raises:
                Exception :
                 -- if fails to run the backup
        """
        self.log.info("\nSTARTING %s BACKUP FOR SUBCLIENT : %s", backup_type.value, self.SUBCLIENT_NAME)

        job = self.fs_sub_client.backup_subclient(subclient_name=self.SUBCLIENT_NAME,
                                                  backupset_name=self.tcinputs['BackupsetName'],                                      
                                                  backup_type=backup_type)
        self.wait_for_job_completion(job)
        self.log.info("\n\nBACKUP SUCCESSFULL FOR SUBCLIENT : %s", self.SUBCLIENT_NAME)

    @test_step
    def restore(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("\nSTARTING RESTORE FOR SUBCLIENT : %s PATH : %s", self.SUBCLIENT_NAME, self.restore_path)
        
        if self.client_machine.check_directory_exists(self.restore_path):
            self.client_machine.remove_directory(self.restore_path)
        self.client_machine.create_directory(self.restore_path, False)

        if self.is_client_network_share:
            dest_client = self.tcinputs["DestinationClientName"]
            impersonate_user = {'username': self.username, 'password': self.password}
        else:
            dest_client = self.client.display_name
            impersonate_user = None

        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.SUBCLIENT_NAME,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=dest_client,
            destination_path=self.restore_path,
            impersonate_user=impersonate_user)
        
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()
        self.log.info("\n\n RESTORE SUCCESSFUL FOR SUBCLIENT : %s", self.SUBCLIENT_NAME)

    def get_restore_path(self):
        """Gets the restored data path"""
        if self.is_client_network_share:
            if self.client_machine.os_info.lower() == 'windows':
                return self.client_machine.join_path(self.restore_path, f"UNC-NT_{self.hostname}")
            else:
                # TODO: Determine path for unix
                return self.restore_path
        else:
            return self.restore_path

    @test_step
    def verify_restore(self):
        """Verifies that the restore was successfully done"""
        self.log.info("\nVALIDATING RESTORED DATA")
        restore_path = self.get_restore_path()
        self.fs_helper.validate_backup(dest_client=self.tcinputs.get('DestinationClientName'),
                                       content_paths=[self.test_path],
                                       restore_path=restore_path,
                                       add_exclusions=self.exclusions,
                                       exceptions_list=self.exceptions)
        self.log.info("\n\nVALIDATION OF RESTORED DATA SUCCESSFUL")

    def edit_filters(self, add_exclusion=None, rem_exclusion=None,
                     add_exception=None, rem_exception=None):
        """ To add/remove exclusions or exceptions
                Args:
                     add_exclusion (lst)      : Exclusions to be added
                     rem_exclusion(lst)      : Exclusions to be removed
                     add_exception (lst)   : Exceptions to be added
                     rem_exception (lst)   : Exceptions to be removed
                Raises:
                    Exception:
                        There is no option to edit the content of the collection
        """
        self.log.info("\n ADD/REMOVE FILTERS FROM SUBCLIENT ")
        self.fs_sub_client.access_subclient(subclient_name=self.SUBCLIENT_NAME,
                                            backupset_name=self.tcinputs['BackupsetName'])
        
        self.sub_client_details.edit_content(del_exceptions=rem_exception,
                                             del_exclusions=rem_exclusion,
                                             add_exceptions=add_exception,
                                             add_exclusions=add_exclusion)
        
        self.browser.driver.back()
        self.admin_console.wait_for_completion()
        self.log.info("\n\n ADD/REMOVE FILTERS FROM SUBCLIENT SUCCESSFUL")

    def get_filter_path(self, fltr):
        """  Get the Content path from subclient
                Args:
                    fltr  : Entity to get it's path
                            'includePath'  for Exceptions
                            'excludePath'  for Exclusions
                            'path'         for Content
                Returns :
                     filter_paths : path of the entity
        """
        self.log.info("%s Gets the path of a selected filter of a subclient %s", "*" * 8, "*" * 8)
        self.subclient.refresh()
        sub_cont_obj = self.subclient._content
        keys_list = []
        for dic in sub_cont_obj:
            dic_keys = list(dic.keys())
            keys_list.append(dic_keys)
        keys_list = [key for lst in keys_list for key in lst]
        filter_paths = []
        for idx, key in enumerate(keys_list):
            if keys_list[idx] == fltr:
                filter_paths.append(sub_cont_obj[idx][key])
        return filter_paths

    @test_step
    def edit_paths_and_verify(self):
        """  Edit subclient backup paths and verifies the new content is backed up or not
                Raises:
                    Exception:
                        -- -- There is no option to edit the filters of the collection
                        -- if fails to create file
                        -- if fails to run the backup
                        -- if fails to run the restore operation
        """
        self.backupset.subclients.refresh()
        self.subclient = self.backupset.subclients.get(self.SUBCLIENT_NAME)
        self.log.info("%s Adds new files to content %s", "*" * 8, "*" * 8)
        path1 = self.client_machine.join_path(self.test_path, 'newfile1.html')
        self.client_machine.create_file(path1, 'New file is added after full backup')
        path2 = self.client_machine.join_path(self.test_path, 'newfile2.html')
        self.client_machine.create_file(path2, 'New file is added after incremental backup')

        if self.is_client_network_share:
            path = self.test_path.split('\\')
            replace_drive_letter = lambda x: f"\\\\{self.client_machine.machine_name}" + x.replace(path[0], '')
            path1 = replace_drive_letter(path1)
            path2 = replace_drive_letter(path2)

        exclusions = self.get_filter_path('excludePath')
        self.edit_filters([path1], exclusions, [path2], self.exceptions)
        self.backup_job(Backup.BackupType.INCR)
        self.restore()
        exceptions = self.get_filter_path('includePath')
        restore_path = self.get_restore_path()
        self.fs_helper.validate_backup(dest_client=self.tcinputs.get('DestinationClientName'),
                                       content_paths=[self.test_path],
                                       restore_path=restore_path,
                                       add_exclusions=[path1],
                                       rem_exclusions=exclusions,
                                       exceptions_list=exceptions)
