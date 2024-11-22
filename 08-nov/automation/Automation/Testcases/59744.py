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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from VirtualServer.VSAUtils import VirtualServerHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.DRHelper import ReplicationMain


class TestCase(CVTestCase):
    """Class for performing unplanned failover and failback of Azure VM's"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Unplanned failover and failback operations from Command center"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.replication_helper = None

    def setup(self):
        """Setup function for test case execution"""
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.close_popup()

        decorative_log("Creating a Subclient Object")
        auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                              self.agent, self.instance)
        auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
        auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

        decorative_log("Creating a Replication Helper Object")
        self.replication_helper = ReplicationMain(auto_subclient, self.instance, self.browser, self.commcell,
                                                  self.csdb)
        self.replication_helper.hypervisor = self.tcinputs['ClientName']
        self.replication_helper.instance = self.tcinputs['InstanceName']

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Performing an unplanned failover operation")
            self.replication_helper.do_unplanned_failover(self.tcinputs['ReplicationGroup'])
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)

        try:
            decorative_log("Performing a failback operation")
            self.replication_helper.do_failback(self.tcinputs['ReplicationGroup'])
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)

    def tear_down(self):
        """Tear down function for test case execution"""
        try:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
