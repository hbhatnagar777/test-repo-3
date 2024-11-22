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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Automation of Live Sync Direct from command center"
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tcinputs = {}

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()
        self.admin_console.close_popup()

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)

        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient

    def run(self):
        """Run function of this test case"""
        try:
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            replication_job_id = self.vsa_obj.get_replication_job(
                replication_group_name=self.tcinputs['ReplicationGroup'])
            if not self.vsa_obj.get_job_status(replication_job_id):
                self.log.exception("Exception occurred during Replication Job")
                raise Exception
            # todo validate live sync
            # self.vsa_obj.validate_live_sync(replication_group_name=self.tcinputs['ReplicationGroup'], live_sync_direct=True)
            self.status = constants.PASSED
        except Exception as exp:
            self.log.info('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.log.info('Failed with error: ' + str(exp))

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)