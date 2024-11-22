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

    tear_down()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils import VirtualServerUtils
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing download of files from snap copy, backup copy and primary copy test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = " Download of files from snap copy, backup copy and primary copy."
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.files_to_download = []
        self.vsa_snap_obj = None

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword']
                                 )

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.restore_proxy_input = None

    def test_cycle(self, vsa, backup_copy=False):

        if not backup_copy:
            vsa.backup()
            if not (vsa.backup_method == "SNAP"):
                self.admin_console.logout()
                self.admin_console.login(self.tcinputs['ACUsername'], self.tcinputs['ACPassword'])

        self.log.info("Download and validation of backup folder")
        vsa.guest_file_download(files=[self.vsa_obj.backup_type.name], end_user=True,
                                vm_without_download_permission = self.tcinputs['VMWithoutDownloadPermission'])
        self.log.info("Download and validation of backup folder completed")

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Testing download from primary copy")
            self.vsa_obj.backup_type = "FULL"
            self.test_cycle(self.vsa_obj)
            self.vsa_obj.cleanup_testdata()

            self.log.info("Testing download from snap copy")
            self.admin_console.navigator.navigate_to_dashboard()
            self.admin_console.logout()
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.subclient = self.tcinputs['SnapSubclientName']
            self.tcinputs['SubclientName'] = self.tcinputs['SnapSubclientName']

            self.reinitialize_testcase_info()
            self.vsa_snap_obj = VirtualServerUtils.create_adminconsole_object(self)
            self.vsa_snap_obj.subclient_obj = self.subclient

            self.vsa_snap_obj.backup_type = "FULL"
            self.vsa_snap_obj.backup_method = "SNAP"
            self.vsa_snap_obj.snap_restore = True
            self.test_cycle(self.vsa_snap_obj)

            self.log.info("Testing download from backup copy")
            self.vsa_snap_obj.snap_restore = False
            self.test_cycle(self.vsa_snap_obj, backup_copy=True)
            self.vsa_snap_obj.cleanup_testdata()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
