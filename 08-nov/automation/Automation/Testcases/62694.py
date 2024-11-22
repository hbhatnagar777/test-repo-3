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
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    tear_down()                             --  tear down function of this test case
    
    selection_test()                        --  performs multi-job control on selected jobs
    
    all_jobs_test()                         --  performs multi-job control on all jobs
    
    client_jobs_test()                      --  performs multi-job control on client jobs
    
    agent_jobs_test()                       --  performs multi-job control on agent jobs
    
    particular_jobs_test()                  --  performs multi-job control on particular job types 
                                                    'Download Software' job in this testcase
    run_all_jobs()                          --  triggers full backup jobs for fs,vsa,sql agent and download job
                                                    and keeps them in suspended state 
    kill_all_jobs()                         --  kills all active jobs

Pre-requisites for executing:
    - Subclients for FS agents, VSA agent and MySQL agent must already exist and be provided
    - Subclient contents must exceed 1 GB for proper test (for long job duration)
    - Enough storage space for 15 of those full backup jobs in case they are committed

"""
from random import sample
from time import sleep

from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages
from cvpysdk.subclients.mysqlsubclient import MYSQLSubclient
from cvpysdk.subclients.vssubclient import VirtualServerSubclient

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import MultiJobPanel
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.end_status = {
            'kill': ["Killed", "Committed", "Completed"],
            'resume': ["Running", "Completed"],
            'suspend': ["Suspended", "Committed", "Completed"]
        }
        self.mysql_subclients = None
        self.mysql_backupset = None
        self.vsa_backupset = None
        self.vsa_subclients = None
        self.fs_subclients = None
        self.jd_wait = None
        self.jobs_page = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "Functional test cases for Active jobs page - Multi-job control"
        self.tcinputs = {
            "load_time_limit": None,
            "ClientName": None,
            "VSAClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "VSABackupsetName": None,
            "FsSubclientNames": None,
            "VSASubclientNames": None,
            "MySQLSubclientNames": None,
        }

    def setup(self):
        """Initial configuration for the test case"""
        self.jd_wait = int(self.tcinputs["load_time_limit"])

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.jobs_page = Jobs(self.admin_console)
        self.fs_subclients = [
            self.backupset.subclients.get(subclient_name)
            for subclient_name in self.tcinputs["FsSubclientNames"]
        ]
        self.vsa_backupset = self.commcell.clients.get(self.tcinputs["VSAClientName"]) \
            .agents.get("Virtual Server") \
            .backupsets.get(self.tcinputs["VSABackupsetName"])
        self.vsa_subclients = [
            VirtualServerSubclient(self.vsa_backupset, subclient_name)
            for subclient_name in self.tcinputs["VSASubclientNames"]
        ]
        self.mysql_backupset = self.client.agents.get("MySQL").backupsets.get('defaultdummybackupset')
        self.mysql_subclients = [
            MYSQLSubclient(self.mysql_backupset, subclient_name)
            for subclient_name in self.tcinputs["MySQLSubclientNames"]
        ]

    def run(self):
        """Run function of this test case"""
        self.navigator.navigate_to_jobs()
        self.selection_test()
        self.all_jobs_test()
        self.client_jobs_test()
        self.agent_jobs_test()
        self.particular_jobs_test()

    def tear_down(self):
        """Tear down function of this test case"""
        self.admin_console.logout()
        self.browser.close()

    @test_step
    def selection_test(self):
        """Performs selected jobs test"""
        ids = self.run_all_jobs()
        all_jobs = set(ids[0] + ids[1] + ids[2] + [ids[-1]])
        random_ids = set(sample(all_jobs, 3))
        for operation in ["resume", "suspend", "kill"]:
            self.jobs_page.multi_job_control(
                operation=operation,
                selection=MultiJobPanel.SelectionType.SELECTED,
                selected_jobs=random_ids
            )
            self.jobs_page.wait_jobs_status(random_ids, self.end_status[operation], self.jd_wait)
            self.jobs_page.wait_jobs_status(all_jobs-random_ids, self.end_status["suspend"], 2)
            self.log.info(f"{operation} test passed for selected jobs")
        self.kill_all_jobs()

    @test_step
    def all_jobs_test(self):
        """Performs all jobs test"""
        ids = self.run_all_jobs()
        all_ids = ids[0] + ids[1] + ids[2] + [ids[-1]]
        for operation in ["resume", "suspend", "kill"]:
            self.jobs_page.multi_job_control(
                operation=operation,
                selection=MultiJobPanel.SelectionType.ALL
            )
            self.jobs_page.wait_jobs_status(all_ids, self.end_status[operation], self.jd_wait)
            self.log.info(f"{operation} test passed for all jobs")
        self.kill_all_jobs()

    @test_step
    def client_jobs_test(self):
        """Performs test for client jobs"""
        ids = self.run_all_jobs()
        client_jobs = ids[0] + ids[1]
        for operation in ["resume", "suspend", "kill"]:
            self.jobs_page.multi_job_control(
                operation=operation,
                selection=MultiJobPanel.SelectionType.CLIENT,
                entity_name=self.client.name
            )
            self.jobs_page.wait_jobs_status(client_jobs, self.end_status[operation], self.jd_wait)
            self.jobs_page.wait_jobs_status(ids[2]+[ids[-1]], self.end_status["suspend"], 2)
            self.log.info(f"{operation} test passed for all client jobs")
        self.kill_all_jobs()

    @test_step
    def agent_jobs_test(self):
        """Performs tests for only agent"""
        ids = self.run_all_jobs()
        agent_jobs = ids[0]
        for operation in ["resume", "suspend", "kill"]:
            self.jobs_page.multi_job_control(
                operation=operation,
                selection=MultiJobPanel.SelectionType.AGENT_ONLY,
                entity_name=self.client.name,
                agent_name=self.agent.name
            )
            self.jobs_page.wait_jobs_status(agent_jobs, self.end_status[operation], self.jd_wait)
            self.jobs_page.wait_jobs_status(ids[1] + ids[2] + [ids[-1]], self.end_status["suspend"], 2)
            self.log.info(f"{operation} test passed for all agent jobs")
        self.kill_all_jobs()

    @test_step
    def particular_jobs_test(self):
        """Performs test on Software Download jobs"""
        ids = self.run_all_jobs()
        download_jobs = ids[-1]
        for operation in ["resume", "suspend", "kill"]:
            self.jobs_page.multi_job_control(
                operation=operation,
                selection=MultiJobPanel.SelectionType.JOB_TYPE,
                entity_name="Download Software"
            )
            self.jobs_page.wait_jobs_status(download_jobs, self.end_status[operation], self.jd_wait)
            self.jobs_page.wait_jobs_status(ids[2] + ids[1] + ids[0], self.end_status["suspend"], 2)
            self.log.info(f"{operation} test passed for all download jobs")
        self.kill_all_jobs()

    @test_step
    def run_all_jobs(self):
        """Triggers FS, VSA, MySQL and Download Jobs"""
        self.log.info("Running All Jobs")
        ids = [[], [], []]
        agent = 0
        for subclient_set in [self.fs_subclients, self.mysql_subclients, self.vsa_subclients]:
            for subclient in subclient_set:
                self.log.info("Starting job for subclient %s", subclient.name)
                job = subclient.backup("Full")
                ids[agent].append(job.job_id)
                job.pause()
                self.log.info("Backup Job started")
            agent += 1
        download_job = self.commcell.download_software(
            options=DownloadOptions.LATEST_HOTFIXES.value,
            os_list=[DownloadPackages.WINDOWS_64.value]
        )
        download_job.pause()
        ids.append(download_job.job_id)
        return ids

    @test_step
    def kill_all_jobs(self):
        """Kills all jobs using API"""
        self.commcell.job_controller.kill_all_jobs()
        self.log.info("Kill request submitted successfully")
        sleep(40)

