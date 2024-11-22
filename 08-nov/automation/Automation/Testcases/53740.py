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

    setup()         -- sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  cleans up the element created during test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware CI test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware Content Indexing Search and Download in AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.ADMINCONSOLE
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.vsa_obj = None

    def setup(self):
        """
        Sets up the variables required for running the test case
        """
        self.utils.reset_temp_dir()
        download_directory = self.utils.get_temp_dir()
        self.log.info("Download directory is %s", download_directory)

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.set_downloads_dir(download_directory)
        self.browser.open()

        self.log.info("Creating the login object")
        login_obj = LoginMain(self.browser.driver, self.csdb)
        login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                        self.inputJSONnode['commcell']['commcellPassword']
                        )
        self.log.info("Login completed successfully. Creating object for VSA")

        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser.driver,
                                                 self.commcell, self.csdb)
        self.vsa_obj.download_directory = download_directory

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.ci_enabled = True
            self.vsa_obj.backup()

            self.vsa_obj.search_and_download()

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.browser.close()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
