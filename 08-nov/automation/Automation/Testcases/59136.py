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
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsAgent
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """ Admin console : System state backup and Virtualize Me
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Admin console : System state backup and Virtualize Me"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.fs_sub_client = None
        self.backupset_name = '1-touch_AC'
        self.subclient_name = 'default'
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "PlanName": None,
            "RecoveryTarget": None,
            "Volumes": None
        }

    @test_step
    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.tcinputs['ClientName'])

    @test_step
    def create_backupset(self):
        """ Creates a new backupset """
        self.delete_backupset()
        self.fs_agent_obj.add_backupset(backup_set=self.backupset_name, plan=self.tcinputs['PlanName'],
                                        define_own_content=True, backup_data=['\\'], backup_system_state=True,
                                        remove_plan_content=True)

    def refresh(self):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(60)
        self.admin_console.refresh_page()

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = Job(self.commcell, job_id=job_id)
        return job_obj.wait_for_completion()

    @test_step
    def run_backup(self):
        """Backup is initiated if there are active job on subclient"""
        self.log.info("%s Runs a Full Backup %s", "*" * 8, "*" * 8)
        self.fs_sub_client.backup_history_subclient(backupset_name=self.backupset_name,
                                                    subclient_name=self.subclient_name)
        self.admin_console.access_tab('Active jobs')
        jobid = self.table.get_column_data('Job Id')
        self.browser.driver.back()
        self.browser.driver.back()
        self.admin_console.wait_for_completion()
        if not jobid:
            job_id = self.fs_sub_client.backup_subclient(self.backupset_name,
                                                         self.subclient_name, Backup.BackupType.FULL, False)
        else:
            job_id = jobid[0]

        if self.wait_for_job_completion(job_id):
            self.log.info("System state backup ran successfully")
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigate_to_client_page()

        else:
            raise Exception("The job did not get completed successfully")

    @test_step
    def run_vme(self):
        """ Runs a virtualize Me job """
        volumes = (self.tcinputs['Volumes']).split(',')
        job_id = self.fs_agent_obj.virtualize_me(backupset_name=self.backupset_name, recovery_target=self.tcinputs['RecoveryTarget'],
                                                 deselect_volumes=volumes)
        if self.wait_for_job_completion(job_id):
            self.log.info("The job completed successfully")
        else:
            raise Exception("The job did not get completed succesfully")

    @test_step
    def delete_backupset(self):
        """ Verifies whether backupset exists or not and then deletes the backupset """
        backupsets_object = self.instance.backupsets
        if backupsets_object.has_backupset(self.backupset_name):
            self.log.info("%s Deletes backupset %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_backup_set(backup_set_name=self.backupset_name)
            self.admin_console.wait_for_completion()
            self.refresh()

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.table = Table(self.admin_console)
        self.fs_agent_obj = FsAgent(self.admin_console)
        self.file_servers = FileServers(self.admin_console)
        self.backup_type = Backup(self.admin_console)
        self.fs_sub_client = FsSubclient(self.admin_console)
        self.jobs = Jobs(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigate_to_client_page()
            self.create_backupset()
            self.run_backup()
            self.run_vme()
            self.delete_backupset()
        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
