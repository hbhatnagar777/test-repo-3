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

    setup()         --  setup function of this test case

    tear_down()     --  tear down function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for validation OCI Replication"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Virtual Server - OCI - Validate Replication"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None

    def setup(self):
        """Setup function for test case execution"""
        decorative_log("Initializing browser Objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login Object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance,
                                                 self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.replication_group = self.tcinputs['ReplicationGroup']

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Performing Full backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            decorative_log(str(exp))

        try:
            self.log.info("Performing Live Sync Validation")
            self.vsa_obj.validate_live_sync(replication_group_name=self.replication_group)
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            self.log.info(exp)

        finally:
            self.vsa_obj.logout_command_center()
            self.browser.close()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        """Teardown function for this test case execution"""
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()