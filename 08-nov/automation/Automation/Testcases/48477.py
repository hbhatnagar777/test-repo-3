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

    navigate_to_client_page() -- navigates to the input client page

    add_subclient() -- creates new subclient with given name and path

    define_content() -- defines the subclient content

    refresh() -- refreshes the current page

    verify_restore() -- verifies restore for the given subclient

    Input Example FOR TESTCASE:

    "testCases": {
    "48477": {
        "ClientName": "**",
        "AgentName": "File System",
        "StoragePolicyName": "**",
        "No_of_dirs": 1,
        "No_of_files": 10,
        "File_length": 10240,
        "TestPath": "/testpath",
        "OSType": "Unix"
        }
    }

"""
import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient


class TestCase(CVTestCase):
    """ Class for executing this test case

            File system kill jobs in the middle of backups and check the next backup
            We will check the following cases:

            1. run first full-> in the middle of the job, kill the job-> verify next job is running as full

            2. run first full-> add new data 1-> run incremental 1-> in the middle of the incremental job
                -> kill the incremental job->add new data again -> next incremental should back up all
                data after last Full

            3. run first full->add new data 1 -> run incremental 1->add new data 2 -> run incremental 2->
                in the middle of the incremental job -> kill the incremental 2 job-> add new data again ->
                next incremental should back up all data after incr1
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "File system kill jobs in the middle of backups and check the next backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.machine = None
        self.helper = None
        self.file_server = None
        self.table = None
        self.RETAIN_DAYS = None
        self.fs_sub_client = None
        self.incPath = None
        self.fullPath = None
        self.test_path = None
        self.cleanup_run = None
        self.backupset_name = None
        self.runid = None
        self.num_dirs = 1
        self.num_files = None
        self.file_size_kb = None
        self.tcinputs = {
            "StoragePolicyName": None,
            "TestPath": None,
            "OSType": None
        }

    @test_step
    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator.navigate_to_file_servers()
        self.table.access_link(self.client.display_name)  # navigates to selected client page

    @test_step
    def add_subclient(self, sc_name, subclient_content):
        """ Creates new subclient
            args
                    sc_name (str) -- sub-client name
                    subclient_content (list) -- list of paths to add
            Raises:
                    Exception:
                        -- if fails to add entity
        """
        self.fs_sub_client.add_fs_subclient(backup_set=self.backupset_name,
                                            subclient_name=sc_name,
                                            plan=self.tcinputs["StoragePolicyName"],
                                            define_own_content=True,
                                            backup_data=subclient_content,
                                            file_system=self.tcinputs["OSType"],
                                            remove_plan_content=True)
        self.backupset.subclients.refresh()

    @test_step
    def define_content(self, full_con_path):
        """ Define the subclient content
            full_con_path (str) -- path to generate data
        """
        self.machine.generate_test_data(full_con_path,
                                        self.num_dirs,
                                        self.num_files,
                                        self.file_size_kb,
                                        hlinks=False,
                                        slinks=False,
                                        sparse=False)

    @test_step
    def refresh(self):
        """ Refreshes the current page """
        self.admin_console.refresh_page()

    @test_step
    def verify_restore(self, sc_name, des_path, source_path):
        """
            Verifies restore for the given subclient
            args
                sc_name (str) -- sub-client name
                des_path (str) -- path for out of place restore
                source_path (str) -- source data path for comparison
        """
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name=self.backupset_name,
            subclient_name=sc_name,
            dest_client=self.client.display_name,
            restore_path=des_path)
        self.log.info(f"Ran restore with job-id = {restore_job}")
        self.commcell.job_controller.get(restore_job).wait_for_completion()
        self.log.info("Restore completed")
        des_path = self.machine.join_path(des_path, source_path)
        result, diff = self.machine.compare_meta_data(
            des_path,
            source_path,
            dirtime=True, skiplink=True)
        if result:
            self.log.info("Metadata comparison was successful.")
        else:
            raise Exception(f"Metadata comparison failed, diff = {diff}")

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.helper = FSHelper(self)
        self.file_server = FileServers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.machine = Machine(self.client)
        self.table = Table(self.admin_console)
        self.fs_sub_client = FsSubclient(self.admin_console)
        self.test_path = self.tcinputs['TestPath']
        self.helper.populate_tc_inputs(self)
        self.num_files = int(self.tcinputs.get('No_of_files', 10))
        self.file_size_kb = int(self.tcinputs.get('File_length', 10240))

    def run(self):
        """ Main function for test case execution """
        try:
            os_sep = self.machine.os_sep
            if self.test_path.endswith(os_sep):
                self.test_path = self.test_path.rstrip(os_sep)
            self.log.info("Create a backupset for the scenarios if not already present.")
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            # ***************
            # CASE 1 BEGINS
            # ***************
            self.log.info("Case 1 begins")
            scenario_num = "1"
            sc_name = '_'.join(('subclient', str(self.id), scenario_num))
            subclient_content = [self.machine.join_path(self.test_path,
                                                        sc_name)]
            run_path = self.machine.join_path(subclient_content[0],
                                              str(self.runid))
            full_con_path = self.machine.join_path(run_path, f"full{scenario_num}")
            self.define_content(full_con_path)
            self.navigate_to_client_page()
            self.add_subclient(sc_name, subclient_content)
            self.log.info("Run first FULL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.FULL)
            backup_job = self.commcell.job_controller.get(job_id)
            self.log.info("KILL first FULL")
            while not backup_job.phase.upper() == 'BACKUP':
                time.sleep(3)
            # wait until backup state is running
            while not backup_job.status.upper() == "RUNNING":
                time.sleep(2)
            backup_job.kill(wait_for_job_to_kill=True)
            self.log.info("Run next as INCREMENTAL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.INCR)
            backup_job = self.commcell.job_controller.get(job_id)
            backup_job.wait_for_completion()
            self.log.info("Verifies whether INC is converted to FULL")
            if backup_job.backup_level.upper() == "FULL":
                self.log.info("Verified next job is running full")
            else:
                raise Exception("Could not verify")
            self.log.info("Case 1 ENDS")

            # ***************
            # CASE 2 BEGINS
            # ***************
            self.log.info("Case 2 begins")
            scenario_num = "2"
            sc_name = '_'.join(('subclient', str(self.id), scenario_num))
            subclient_content = [self.machine.join_path(self.test_path,
                                                        sc_name)]
            tmp_path = self.machine.join_path(self.test_path,
                                              'cvauto_tmp',
                                              str(self.runid))
            run_path = self.machine.join_path(subclient_content[0],
                                              str(self.runid))
            full_con_path = self.machine.join_path(run_path, f"full{scenario_num}")
            inc_con_path = self.machine.join_path(run_path, f"inc{scenario_num}")
            inc_con_path1 = self.machine.join_path(run_path, f"inc{scenario_num}1")
            self.define_content(full_con_path)
            self.navigate_to_client_page()
            self.add_subclient(sc_name, subclient_content)
            self.log.info("Run first FULL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.FULL)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.define_content(inc_con_path)
            self.log.info("Run first INCREMENTAL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.INCR)
            backup_job = self.commcell.job_controller.get(job_id)
            self.log.info("KILL first INCREMENTAL")
            while not backup_job.phase.upper() == 'BACKUP':
                time.sleep(3)
            # wait until backup state is running
            while not backup_job.status.upper() == "RUNNING":
                time.sleep(2)
            backup_job.kill(wait_for_job_to_kill=True)
            self.define_content(inc_con_path1)
            self.log.info("Run next as INC")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.INCR)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.machine.create_directory(tmp_path)
            self.log.info("Verifies if INC job backed up all data after FULL")
            self.verify_restore(sc_name, tmp_path, run_path)
            self.log.info("Case 2 ENDS")

            # ***************
            # CASE 3 BEGINS
            # ***************
            self.log.info("Case 3 begins")
            scenario_num = "3"
            sc_name = '_'.join(('subclient', str(self.id), scenario_num))
            subclient_content = [self.machine.join_path(self.test_path,
                                                        sc_name)]
            self.machine.remove_directory(tmp_path)
            run_path = self.machine.join_path(subclient_content[0],
                                              str(self.runid))
            full_con_path = self.machine.join_path(run_path, f"full{scenario_num}")
            inc_con_path = self.machine.join_path(run_path, f"inc{scenario_num}")
            inc_con_path1 = self.machine.join_path(run_path, f"inc{scenario_num}1")
            inc_con_path2 = self.machine.join_path(run_path, f"inc{scenario_num}2")
            self.define_content(full_con_path)
            self.navigate_to_client_page()
            self.add_subclient(sc_name, subclient_content)
            self.log.info("Run first FULL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.FULL)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.define_content(inc_con_path)
            self.log.info("Run first INCREMENTAL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.INCR)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.define_content(inc_con_path1)
            self.log.info("Run second INCREMENTAL")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.INCR)
            backup_job = self.commcell.job_controller.get(job_id)
            self.log.info("KILL second INCREMENTAL")
            while not backup_job.phase.upper() == 'BACKUP':
                time.sleep(3)
            # wait until backup state is running
            while not backup_job.status.upper() == "RUNNING":
                time.sleep(2)
            backup_job.kill(wait_for_job_to_kill=True)
            self.define_content(inc_con_path2)
            self.log.info("Run next as INC")
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name, sc_name, Backup.BackupType.INCR)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.machine.create_directory(tmp_path)
            self.log.info("Verifies if INC job backed up all data after FULL")
            self.verify_restore(sc_name, tmp_path, run_path)
            self.log.info("Case 3 ENDS")

            # DELETING TEST DATASET & DELETING BACKUPSET
            if self.cleanup_run:
                self.machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.backupset_name)
            else:
                self.machine.remove_directory(self.test_path, self.RETAIN_DAYS)

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)