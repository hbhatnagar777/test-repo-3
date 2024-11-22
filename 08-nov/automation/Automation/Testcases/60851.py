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
from Web.Common.page_object import TestStep
from Reports.utils import TestCaseUtils
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "60851":
                {
                "nfs_server":"edgelinuxma",
                "plan":"Server plan"
                }

        """

        super(TestCase, self).__init__()
        self.name = "Edit and validate the HFS in Command Center"
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
        self.network_store_helper = NetworkStoreHelper(self.admin_console)
        self.hfs_helper = NFSHelper(self.tcinputs['nfs_server'],
                                    self.commcell,
                                    self.inputJSONnode['commcell']['commcellUsername'],
                                    self.inputJSONnode['commcell']['commcellPassword'],
                                    self.tcinputs.get('storagePolicy'))

    @test_step
    def test_step1(self):
        """In this teststep we are going to edit and validate general tile option in HFS"""
        general_settings = {"file_server":"edgelinuxma","allowed_network":"172.168.271.191",      # for multiple allowed clients
                                    "access_type":"Read Only","squash_type":"No Root Squash"}
        self.network_store_helper.edit_general_tile(general_settings)
        self.network_store_helper.validate_general_tile(self.hfs_helper)
        

    @test_step
    def test_step2(self):
        """In this teststep we are going to edit and validate retention tile option in HFS"""
        retention_settings = {'retention_deleted':{'val':10,'period':"Weeks"},
                'version':"ON","retention_versions":{'val':10,'period':"Weeks"},
                "no_of_version":31,"version_interval":42}
        self.network_store_helper.edit_retention_settings(retention_settings)
        self.network_store_helper.validate_retention_tile(self.hfs_helper)

    def run(self):

        try:

            self.network_store_helper.network_store_name = "Test_HFS_"+self.id+time.strftime("_%H_%M_%S",time.localtime())
            self.network_store_helper.nfs_server = self.tcinputs['nfs_server']
            self.network_store_helper.plan = self.tcinputs['plan']

            self.log.info("*********Adding a network store*********")
            self.network_store_helper.create_network_store(commcell=self._commcell)

            self.log.info("*********Verifying if network store added*********")
            time.sleep(60)
            self.network_store_helper.validate_network_store_creation()

            self.log.info("*********Verifying General settings*********")
            self.test_step1()

            self.log.info("*********Verifying Retention settings*********")
            self.test_step2()

            self.log.info("*********Deleting a network store*********")
            self.network_store_helper.remove_network_store()

            self.log.info("*********Verifying if network store is deleted*********")
            self.network_store_helper.validate_delete()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
