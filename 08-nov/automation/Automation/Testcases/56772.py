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
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.page_object import handle_testcase_exception
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from cvpysdk.commcell import Commcell

from Web.VcloudPlugin.VcloudPluginHelper import VcloudPluginHelper


class TestCase(CVTestCase):
    """Class for executing basic testcase for Backup and restore for Vcloud through Vcloud Plugin as Admin User"""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "Basic testcase for Backup and restore for Vcloud through Vcloud Plugin as Admin User"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.vcloud_helper = None
        self.tcinputs = {
            "VcloudVdc": None
        }


    def setup(self):
        decorative_log("Initialising Browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        decorative_log("Creating login object")
        vcloud_setup = self.tcinputs['vcloud_setup']
        commcell_setup = self.inputJSONnode['commcell']

        self.vcloud_helper = VcloudPluginHelper(self.browser, commcell_setup, vcloud_setup, self.commcell)

    def run(self):
        """"Main function for testcase execution"""

        try:
            self.vcloud_helper.setup()
            self.vcloud_helper.backup_and_restore()
        except Exception as ex:
            handle_testcase_exception(self, ex)

    def tear_down(self):
        self.browser.close()

