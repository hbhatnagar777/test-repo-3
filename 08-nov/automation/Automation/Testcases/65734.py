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

    tear_down()                 --  tear down method for testcase

    add_sap_maxdb_server()     -- add new sap maxdb server

    add_instance()              --  add new sap maxdb instance

    delete_instance_if_exists() --  delete the sap maxdb instance if already exist

    wait_for_job_completion()   --  waits for completion of job

    clear_credentials()         --  clear the credential

    navigate_to_job_details()   --  navigate to the job details page

    run()                       --  run function of this test case

Input Example:
    "testCases":
        {
            "65734": {
                  "OsType": "windows"
                  "ServerName": "maxdb",
                  "ClientUsername": "maxdb\\administrator",
                  "ClientPassword": "dbPassword",
                  "NewClientName": "maxdb",
                  "NewInstanceName": "max_ins",
                  "Plan": "CS_PLAN"

                 }
        }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from cvpysdk.instance import Instances
from cvpysdk.credential_manager import Credentials
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs


class TestCase(CVTestCase):
    """ Class for executing Instance creation testcase for SAP MaxDB """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Instance  creation testcase for SAP MaxDB"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'OsType': None,
            'ServerName': None,
            'ClientUsername': None,
            'ClientPassword': None,
            'NewClientName': None,
            'NewInstanceName': None,
            'Plan': None}
        self.database_instances = None
        self.database_instances_details = None
        self.credential_manager = None
        self.instances = None
        self.job = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.database_instances = DBInstances(self.admin_console)
        self.database_instances_details = DBInstanceDetails(self.admin_console)
        self.credential_manager = Credentials(self.commcell)
        self.job = Jobs(self.admin_console)

    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        self.log.info("waiting for job to complete")
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    def delete_instance_if_exists(self):
        """deletes the instance if it already exists"""
        self.navigator.navigate_to_db_instances()
        if self.database_instances.is_instance_exists(DBInstances.Types.SAP_MAXDB, self.tcinputs['NewInstanceName'],self.tcinputs['NewClientName']):
            self.database_instances.select_instance(
                DBInstances.Types.SAP_MAXDB, self.tcinputs['NewInstanceName'], self.tcinputs['NewClientName'])
            self.database_instances_details.delete_instance()

    def navigate_to_job_details(self,job_id):
        """navigate to job details page for a particular job"""
        self.navigator.navigate_to_jobs()
        self.job.view_job_details(job_id=job_id, details=False)

    @test_step
    def add_instance(self):
        """add new sapmaxdb instance"""
        self.delete_instance_if_exists()
        self.database_instances.add_sapmaxdb_instance(
            server_name=self.tcinputs['NewClientName'],
            instance_name=self.tcinputs['NewInstanceName'],
            plan=self.tcinputs['Plan']
        )

    @test_step
    def add_sap_maxdb_server(self):
        """add new server for sapmaxdb"""
        self.clear_credentials(self.tcinputs["ClientUsername"])
        job_id=self.database_instances.add_server(
            database_type=DBInstances.Types.SAP_MAXDB,
            plan=self.tcinputs["Plan"],
            server_name=self.tcinputs["ServerName"],
            username=self.tcinputs["ClientUsername"],
            password=self.tcinputs["ClientPassword"],
            os_type=self.tcinputs["OsType"])
        self.navigate_to_job_details(job_id)
        self.wait_for_job_completion(job_id)

    def clear_credentials(self, credential_name):
        """delete the credential
         Args:
            credential_name   (str): Name of the credential
        """
        if credential_name in self.credential_manager.all_credentials:
            self.credential_manager.delete(credential_name)

    def tear_down(self):
        """tear down method for testcase"""
        self.log.info("Deleting automatically created instance")
        client = self.commcell.clients.get(self.tcinputs["ServerName"])
        agent = client.agents.get("sap for max db")
        self.instances = Instances(agent)
        self.instances.delete(self.tcinputs["NewInstanceName"])
        self.log.info("Clearing automatically added credential")
        self.clear_credentials(self.tcinputs["ClientUsername"])
        self.log.info("Deleting automatically created client")
        job_obj = client.retire()
        self.wait_for_job_completion(job_obj.job_id)
        self.commcell.refresh()
        client_exists = self.commcell.clients.has_client(self.tcinputs["ServerName"])
        if client_exists:
            self.commcell.clients.delete(self.tcinputs["ServerName"])

    def run(self):
        """ Main function for test case execution """
        try:
            self.add_sap_maxdb_server()
            self.add_instance()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

