# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class
    
    setup()         --  setup function of this test case

    access_instant_clones_tab()     -- access Instant clone tab

    run()           --  run function of this test case


Inputs:

        Source server         --      name of the client for backup

        SubclientName         --      subclient to be backed up

        InstanceName          --      name of the instance

        ClientName            --      name of the client name

        SourceDatabase        --      name of the source database

"""

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances ,SQLInstance
from Web.AdminConsole.Databases.Instances.instant_clone import MSSQLInstantClone
from Application.SQL.sqlhelper import SQLHelper
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep,handle_testcase_exception




class TestCase(CVTestCase):

    """ Class for executing SQL Instant Clone for SQL Server in Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.agentType = None
        self.name = "SQL Command Center -  SQL Instant Clone"
        self.instance = None
        self.client_name = None
        self.SQLInstance = None
        self.subclient_page = None
        self.tcinputs = {
            "InstanceName": None,
            "SourceServer": None,
            "SubclientName": None,
            "ClientName": None,
            "SourceDatabase" : None
        }

    def setup (self):
        """ Method to setup test variables """

        self.instance_name = self.tcinputs['InstanceName']
        self.subclient_name = self.tcinputs['SubclientName']
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.log.info("*" * 10 + " Initialize SQLHelper objects " + "*" * 10)
        self.dbinstance_obj = DBInstances(self.admin_console)
        self.sql_instance = SQLInstance(self.admin_console)
        self.db_instances = DBInstances(self.admin_console)
        self.jobs = Jobs(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.db_instance_details = None
        self.instant_clone_obj = MSSQLInstantClone(self.admin_console)
        self.props = self.admin_console.props
        self.source_server = self.tcinputs['SourceServer']



    @test_step
    def access_instant_clones_tab(self):

        """Clicks on 'Instant clones' tab in Databases page"""

        self.admin_console.access_tab(self.admin_console.props['pageHeader.clones'])

    @test_step
    def wait_for_job_completion(self, jobid):

        """Waits for Backup or Restore Job to complete"""

        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    def run(self, csdb=None):

        """Main function for test case execution"""

        try:

            self.log.info("Started executing {0} testcase".format(self.id))

            self.navigator.navigate_to_db_instances()
            self.dbinstance_obj.select_instance( self.sql_instance.db_type, self.instance_name, None)

            bkp_jobid = self.sql_instance.sql_backup(self.instance_name, self.subclient_name, "Full")
            bkp_jdetails = self.jobs.job_completion(bkp_jobid)
            if not bkp_jdetails['Status'] == 'Completed':
                raise Exception("Backup job {0} did not complete successfully".format(bkp_jobid))
            self.log.info("Discovering clone instance")
            self.navigator.navigate_to_db_instances()
            self.access_instant_clones_tab()
            jobid = self.instant_clone_obj.instant_clone(DBInstances.Types.MSSQL, self.source_server ,self.tcinputs['InstanceName'],
                                                 self.tcinputs['SourceDatabase'],self.tcinputs['SourceServer'], self.instance_name)

            job_status = self.wait_for_job_completion(jobid)
            if not job_status:
                exp = "{0} Clone Job ID {1} didn't succeed".format(self.instant_clone_obj.instant_clone, jobid)
                raise Exception(exp)
            
        except Exception as exp:
            raise CVTestStepFailure(f'Clone operation failed : {exp}')


        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

