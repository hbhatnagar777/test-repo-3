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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing download of files and folders when Collect file details is enabled for v1
    clients test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = " Download of files and folders is successful when Collect file details is enabled for v1 clients."
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.files_to_download = []

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
        self.files_to_download = self.tcinputs['Files']

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            if not backup_options.collect_metadata:
                raise Exception("Metadata collection is not enabled")

            self.vsa_obj.backup_type = "FULL"

            self.vsa_obj.vsa_discovery()
            self.vsa_obj.create_testdata_for_guest_file_download()
            self.vsa_obj.backup()

            self.log.info("Download and validation of single file started")
            self.vsa_obj.guest_file_download(files=["test1.txt"],
                                             browse_folder="TESTFOLDER/TestData/TestFolder")
            self.log.info("Download and validation of single file completed")

            self.log.info("Download and validation of multiple file started")
            self.vsa_obj.guest_file_download(files=["test1.txt", "test2.txt"],
                                             browse_folder="TESTFOLDER/TestData/TestFolder")
            self.log.info("Download and validation of multiple file completed")

            self.log.info("Modifying files and again testing downloads")
            self.vsa_obj.modify_testdata_for_guest_file_download(file_name="test1.txt")
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            self.log.info("Download and validation of single file started")
            self.vsa_obj.guest_file_download(files=["test1.txt"],
                                             browse_folder="TESTFOLDER/TestData/TestFolder")
            self.log.info("Download and validation of single file completed")

            self.log.info("Download and validation of multiple file started")
            self.vsa_obj.guest_file_download(files=["test1.txt", "test2.txt"],
                                             browse_folder="TESTFOLDER/TestData/TestFolder")
            self.log.info("Download and validation of multiple file completed")


        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()