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

    delete_instance_if_exists() --  deletes the instance if already exists

    check_if_instance_added()   --  checks if instance is added

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    active_jobs_action()        --  method to kill the active jobs of client

    cleanup()                   --  method to cleanup all testcase created instance

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "13949":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"XXXX",
                          "OracleHome":"oracle/home/directory",
                          "ConnectString":"username/password@servicename"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ Class for executing Instance creation testcase for Oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Instance configuration for Oracle"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None,
            'ConnectString': None,
            'OracleHome': None}
        self.table = None
        self.database_instances = None
        self.db_instance_details = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.table = Rtable(self.admin_console)
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        if self.status == constants.PASSED:
            self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def delete_instance_if_exists(self):
        """deletes the instance if it already exists"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.cleanup()

    @test_step
    def check_if_instance_added(self):
        """Checks if instance is added or not"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.table.reload_data()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.log.info("Instance found")
        else:
            raise CVTestStepFailure("Instance not found")

    @test_step
    def add_instance(self):
        """Adds new instance"""
        self.database_instances.add_oracle_instance(server_name=self.tcinputs["ClientName"],
                                                    oracle_sid=self.tcinputs["InstanceName"],
                                                    plan=self.tcinputs["Plan"],
                                                    oracle_home=self.tcinputs["OracleHome"],
                                                    connect_string=self.tcinputs["ConnectString"])

    @test_step
    def active_jobs_action(self):
        """Method to kill the active jobs running for the client"""
        self.commcell.refresh()
        active_jobs = self.commcell.job_controller.active_jobs(self.tcinputs["ClientName"])
        self.log.info("Active jobs for the client:%s", active_jobs)
        if active_jobs:
            for job in active_jobs:
                self.log.info("Killing Job:%s", job)
                self.commcell.job_controller.get(job).kill(wait_for_job_to_kill=True)
            self.active_jobs_action()
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def cleanup(self):
        """Cleans up testcase created instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])
        self.active_jobs_action()
        self.log.info("Deleting instance")
        self.db_instance_details.delete_instance()

    def run(self):
        """ Main function for test case execution """
        try:
            self.delete_instance_if_exists()

            self.add_instance()

            self.check_if_instance_added()

        except Exception as exp:
            handle_testcase_exception(self, exp)
