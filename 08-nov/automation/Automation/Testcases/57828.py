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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """ Command center: Override plan content and verify backup """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Testcase for file system to associate/remove plan of subclient and verify backup from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.machine = None
        self.subclient = None
        self.fs_sub_client = None
        self.sub_client_details = None
        self.fs_helper = None
        self.delimiter = None
        self.os_name = None
        self.restore_file_path = ''
        self.sub_client_name = 'Test_57828'
        self.content = []
        self.plan = None
        self.plan_content = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "NewPlanName": None,
            "PlanPath": None,
            "PrimaryStorageForPlan": None,
            "RestorePath": None
        }

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion()

    def define_plan_content(self):
        """Populate the plan content path"""
        self.os_name = self.client._properties['client']['osInfo']['Type']
        self.restore_file_path = self.tcinputs['RestorePath']
        if self.os_name == "Windows":
            self.delimiter = "\\"
        else:
            self.delimiter = "/"
        self.plan_content = self.tcinputs['PlanPath']
        self.fs_helper.populate_tc_inputs(self, mandatory=False)
        self.fs_helper.generate_testdata(['.html', '.css'], self.plan_content, 6)

    @test_step
    def add_plan(self):
        """ adds new plan """
        self.define_plan_content()
        self.navigator = self.admin_console.navigator
        self.navigate_to_client_page()
        self.delete_sub_client()
        self.navigator.navigate_to_plan()
        plan_names = self.table.get_column_data('Plan name')
        plan_name = self.tcinputs['NewPlanName']
        if plan_name in plan_names:
            self.plan.delete_plan(plan_name)
            self.admin_console.wait_for_completion()
        backup_data = {'file_system': [self.os_name],
                       'content_backup': None,
                       'content_library': None,
                       'custom_content': self.plan_content,
                       'exclude_folder': None,
                       'exclude_folder_library': None,
                       'exclude_folder_custom_content': None}
        storage = {'pri_storage': self.tcinputs['PrimaryStorageForPlan'],
                   'pri_ret_period': '30',
                   'sec_storage': None,
                   'sec_ret_period': '45',
                   'ret_unit': 'Day(s)'}
        self.plan.create_server_plan(plan_name=plan_name,
                                     storage=storage,
                                     backup_data=backup_data)

    @test_step
    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator.navigate_to_file_servers()
        self.table.access_link(self.client.display_name)  # navigates to selected client page

    @test_step
    def refresh(self):
        """ Refreshes the current page """
        time.sleep(60)
        self.admin_console.refresh_page()

    @test_step
    def add_subclient(self):
        """ Creates new subclient
                Raises:
                    Exception:
                        -- if fails to add entity
        """
        self.fs_sub_client.add_fs_subclient(backup_set=self.tcinputs['BackupsetName'],
                                            subclient_name=self.sub_client_name,
                                            plan=self.tcinputs['NewPlanName'],
                                            file_system=self.os_name)
        self.backupset.subclients.refresh()
        self.subclient = self.backupset.subclients.get(self.sub_client_name)

    @test_step
    def backup_job(self, backup_type):
        """ Function to run a backup job
            Args:
                backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
            Raises:
                Exception :
                 -- if fails to run the backup
        """
        job = self.fs_sub_client.backup_subclient(self.tcinputs['BackupsetName'],
                                                  self.sub_client_name, backup_type, False)
        self.wait_for_job_completion(job)

    @test_step
    def restore(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        if self.machine.check_directory_exists(self.restore_file_path):
            self.machine.remove_directory(self.restore_file_path)
        self.machine.create_directory(self.restore_file_path, False)
        if self.os_name == "Windows":
            des_path = self.restore_file_path.replace("\\", "/")
        else:
            des_path = self.restore_file_path[1:]
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
            dest_client=self.client.display_name,
            restore_path=des_path)
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def define_content(self):
        """ Populate subclient content path """
        self.log.info("%s Populates subclient content %s", "*" * 8, "*" * 8)
        path = self.client.job_results_directory + self.delimiter + '57828'
        self.fs_helper.generate_testdata(['.py', '.c'], path, 4)
        self.content.append(path)

    def edit_sub_content(self, backup_content):
        """ Overrides the plan content
                Args:
                    backup_content list(paths) : backup content to be backed up

                Raises:
                    Exception:
                        -- if fails to edit the content
        """
        self.log.info("%s Edits subclient content %s", "*" * 8, "*" * 8)
        self.table.access_link(self.sub_client_name)
        self.sub_client_details.edit_content(browse_and_select_data=False,
                                             backup_data=backup_content,
                                             file_system=self.os_name)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    @test_step
    def override_plan_content_and_verify(self):
        """ Override the plan content and verifies new content is backedup or not
                Raises:
                    Exception:
                        -- if fails to edit the content
                        -- if fails to run the backup
                        -- if fails to run the restore operation
                        -- if fails to validate backup files
        """
        self.define_content()
        path1 = self.plan_content + self.delimiter + 'newfile1.html'
        self.machine.create_file(path1, 'New file is added in {} folder'.format(self.plan_content))
        path2 = self.plan_content + self.delimiter + 'newfile2.html'
        self.machine.create_file(path2, 'New file is added {} folder'.format(self.plan_content))
        files = self.content[:]
        files.append(path1)
        files.append(path2)
        self.edit_sub_content(self.content)
        self.backup_job(Backup.BackupType.INCR)
        self.fs_helper.validate_collect_files(subclient_id=self.subclient.subclient_id,
                                              collect_file_level='incr', new_path=files)

    def remove_plan_content(self, del_backup_data):
        """ Removes Plan content and associated plan of subclient
                Args:
                    del_backup_data   list(paths) : paths to be edited for back up

                 Raises:
                    Exception:
                        -- There is no option to edit the content of the collection
        """
        self.log.info("%s Removes plan content %s", "*" * 8, "*" * 8)
        self.table.access_link(self.sub_client_name)
        self.sub_client_details.edit_content(browse_and_select_data=False,
                                             backup_data=[],
                                             del_content=del_backup_data,
                                             file_system=self.os_name)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    @test_step
    def remove_plan_content_and_verify(self):
        """ Remove Plan and Plan content and verify that plan content is not backedup
                Raises:
                    Exception:
                        -- if fails to run the backup
                        -- if fails to validate backup files
        """
        path1 = self.content[0] + self.delimiter + 'newfile1.html'
        self.machine.create_file(path1, 'New file is added in Backup_Content folder')
        path2 = self.content[0] + self.delimiter + 'newfile2.html'
        self.machine.create_file(path2, 'New file is added Backup_Content folder')
        self.remove_plan_content([self.plan_content])
        self.backup_job(Backup.BackupType.INCR)
        self.fs_helper.validate_collect_files(subclient_id=self.subclient.subclient_id,
                                              collect_file_level='incr',
                                              new_path=[path1, path2],
                                              deleted_path=self.plan_content)

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
        self.log.info("%s Gets the path of a selected filter of a subclient %s",
                      "*" * 8, "*" * 8)
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
    def delete_sub_client(self):
        """ Verifies whether subclient exists or not and then deletes the subclient """
        subclient_names = self.table.get_column_data('Name')
        subclient_name = self.sub_client_name
        if subclient_name in subclient_names:
            self.log.info("%s Deletes subclient %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_subclient(backupset_name=self.tcinputs['BackupsetName'],
                                                subclient_name=self.sub_client_name)
            self.admin_console.wait_for_completion()

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.table = Table(self.admin_console)
        self.plan = Plans(self.admin_console)
        self.fs_sub_client = FsSubclient(self.admin_console)
        self.sub_client_details = FsSubclientDetails(self.admin_console)
        self.fs_helper = FSHelper(self)
        self.machine = Machine(self.client)

    def run(self):
        """ Main function for test case execution """
        try:
            self.add_plan()
            self.navigate_to_client_page()
            self.add_subclient()
            self.backup_job(Backup.BackupType.FULL)
            self.refresh()
            self.restore()
            self.fs_helper.validate_backup(content_paths=[self.plan_content],
                                           restore_path=self.tcinputs['RestorePath'])
            self.override_plan_content_and_verify()
            self.remove_plan_content_and_verify()
            self.delete_sub_client()
            self.navigator.navigate_to_plan()
            self.plan.delete_plan(plan_name=self.tcinputs['NewPlanName'])

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
