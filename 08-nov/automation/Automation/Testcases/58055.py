# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Basic acceptance test case for NFS Objectstore in Command Center

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.network_store_helper import NetworkStoreHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "58055":
                {
                "nfs_server": "vmnfsserver",
                "plan": "Server plan"
                }

        """

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for NFS Objectstore in Command Center"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.network_store_helper = None
        self.tcinputs = {
            "nfs_server": None,
            "plan": None
            }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.click_button("OK")
        self.network_store_helper = NetworkStoreHelper(self.admin_console)

    def run(self):

        try:

            self.network_store_helper.network_store_name = "Test_HFS_"+time.strftime("%H_%M_%S",time.localtime())
            self.network_store_helper.nfs_server = self.tcinputs['nfs_server']
            self.network_store_helper.plan = self.tcinputs['plan']

            self.log.info("*********Adding a network store*********")
            self.network_store_helper.create_network_store(commcell=self._commcell)

            self.log.info("*********Verifying if network store added*********")
            time.sleep(60)
            self.network_store_helper.validate_network_store_creation()

            self.log.info("*********Deleting a network store*********")
            self.network_store_helper.remove_network_store()

            self.log.info("*********Verifying if network store is deleted*********")
            self.network_store_helper.validate_delete()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
