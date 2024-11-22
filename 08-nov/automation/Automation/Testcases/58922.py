# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class
    setup()                     --  setup method for test case
    run()                       --  run function of this test case
    create_instance()           --  create an informix instance
    create_subclient()          --  create a new subclient
    run_backup()                --  Submit backup for the new subclient
    kill_active_jobs()          --  Kills all active jobs for the client
    delete_subclient_instance() --  Delete the subclient and instance created by test case

Input Example:
    "testCases":
        {
            "58922":
                    {
                        "ClientName":"meeratrad",
                        "InstanceName":"ol_informix1210",
                        "Plan": "dbplan1",
                        "UserName":"informix",
                        "password": "#####",
                        "InformixDir":"/opt/IBM/informix",
                        "ONCONFIG":"onconfig.ol_informix1210",
                        "SQLHOSTS":"/opt/IBM/informix/etc/sqlhosts.ol_informix1210",
                        "incr_Level": "2"
                    }
        }
Put password value as empty for linux clients.
Provide DomainName also in UserName for windows clients.

"""

from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup

class TestCase(CVTestCase):
    """ Class for executing the testcase """
    test_step = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "Creation,deletion of instance and subclient from command center for Informix"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None,
            'UserName': None,
            'password': None,
            'InformixDir': None,
            'ONCONFIG': None,
            'SQLHOSTS': None,
            'incr_Level': None
            }
        self.db_instance = None
        self.subclient_page = None
        self.db_instance_details = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)

    @test_step
    def create_instance(self):
        """Create informix instance"""
        navigator = self.admin_console.navigator
        navigator.navigate_to_db_instances()
        is_windows_os = "windows" in self.client.os_info.lower()
        self.log.info("Check if instance exists")
        if self.db_instance.is_instance_exists(DBInstances.Types.INFORMIX,
                                               self.tcinputs['InstanceName'],
                                               self.tcinputs['ClientName']):
            self.log.info("Deleting the instance")
            self.db_instance.select_instance(DBInstances.Types.INFORMIX,
                                             self.tcinputs['InstanceName'],
                                             self.tcinputs['ClientName'])
            self.kill_active_jobs()
            self.db_instance_details.delete_instance()
            self.log.info("Deleted it and creating new instance")
        self.db_instance.add_informix_instance(
            self.tcinputs['ClientName'],
            self.tcinputs['InstanceName'],
            self.tcinputs['Plan'],
            self.tcinputs['UserName'],
            self.tcinputs['InformixDir'],
            self.tcinputs['ONCONFIG'],
            self.tcinputs['SQLHOSTS'],
            is_windows_os,
            self.tcinputs['password']
        )
        self.log.info("Instance created successfully")

    @test_step
    def create_subclient(self):
        """Create a new subclient with whole system as content"""
        self.subclient_page = SubClient(self.admin_console)
        subclient_object = self.db_instance_details.click_add_subclient(DBInstances.Types.INFORMIX)
        subclient_object.add_subclient(
            'Sub_58922',
            self.tcinputs['Plan'],
            'WholeSystem',
            self.tcinputs['incr_Level']
        )
        self.log.info("Subclient created successfully")

    @test_step
    def run_backup(self):
        """Submit backup job for the new subclient"""
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        job_obj = self.commcell.job_controller.get(job_id)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (job_id, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", job_id)
        if job_obj.status.lower() != 'completed':
            raise CVTestStepFailure(
                "Job status of %s is not completed" % (job_id)
            )
        self.log.info("Backup completed successfully")

    @test_step
    def kill_active_jobs(self):
        """Kill all active jobs for the client"""
        active_jobs = self.commcell.job_controller.active_jobs(
            client_name=self.tcinputs['ClientName'])
        if active_jobs:
            for jobid in active_jobs.keys():
                job_object = Job(self.commcell, jobid)
                job_object.kill(True)
            self.log.info("Killed all running jobs for the client")

    @test_step
    def delete_subclient_instance(self):
        """Delete the instance and subclient"""
        self.kill_active_jobs()
        self.subclient_page.delete_subclient()
        self.log.info("Subclient deleted successfully")
        self.db_instance_details.delete_instance()
        self.log.info("Instance deleted successfully")

    def run(self):
        """ Main function for test case execution """
        try:
            self.create_instance()
            self.create_subclient()
            self.run_backup()
            self.delete_subclient_instance()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
