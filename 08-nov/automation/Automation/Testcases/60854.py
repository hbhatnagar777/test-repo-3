# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test case to validate the User permissions on Hybrid file store via commandcenter
steps:
1.Create 2 shares with user1 and user2 and create PIT for share with user1
2.Change the password for both the users
3.Login as User 1 and check if all entites are there
4.Login as User 2 and check if all user 2 entites are there
5.Tear down the Entities
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
from Web.Common.page_object import TestStep
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "60854":
                {
                "nfs_server": "edgelinuxma",
                "plan": "Server plan"
                }

        """

        super(TestCase, self).__init__()
        self.name = "HFS share user is able to see only appropriate data"
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
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.network_store_helper = NetworkStoreHelper(self.admin_console)
        self.network_store_helper.nfs_server = self.tcinputs['nfs_server']
        self.network_store_helper.plan = self.tcinputs['plan']
        self.user_1 = "Test_User_1_"+self._id + \
            time.strftime("_%H_%M_%S", time.localtime())
        self.user_2 = "Test_User_2_"+self._id + \
            time.strftime("_%H_%M_%S", time.localtime())
        self.pit_name = "PIT_view_"
        self.NFS_server_obj = NFSHelper(self.tcinputs['nfs_server'],
                                        self.commcell,
                                        self.inputJSONnode['commcell']['commcellUsername'],
                                        self.inputJSONnode['commcell']['commcellPassword'],
                                        self.tcinputs.get('storagePolicy'))

    @test_step
    def test_step_1(self):
        """Create 2 shares with user1 and user2 and create PIT for share with user1"""
        self.network_store_helper.network_store_name = self.user_1
        self.log.info("*********Adding a network store*********")
        self.network_store_helper.create_network_store(commcell=self._commcell)

        self.log.info("*********Verifying if network store added*********")
        time.sleep(60)
        self.network_store_helper.validate_network_store_creation()
        timestamp = time.time()
        self.log.info("Creating PIT view for HFS " +
                      self.network_store_helper.network_store_name+" for timestamp "+str(timestamp))
        self.network_store_helper.add_pit_view(timestamp, self.pit_name+"1")

        timestamp = time.time()
        self.log.info("Creating PIT view for HFS " +
                      self.network_store_helper.network_store_name+" for timestamp "+str(timestamp))
        self.network_store_helper.add_pit_view(timestamp, self.pit_name+"2")

        self.network_store_helper.network_store_name = self.user_2
        self.log.info("*********Adding a network store*********")
        self.network_store_helper.create_network_store(commcell=self._commcell)

        self.log.info("*********Verifying if network store added*********")
        time.sleep(60)
        self.network_store_helper.validate_network_store_creation()
        AdminConsole.logout_silently(self.admin_console)

    @test_step
    def test_step_2(self):
        """Change the password for both the users"""
        user_obj = self._commcell.users.get(self.user_1)
        user_obj.update_user_password(
            self.inputJSONnode['commcell']['commcellPassword'], self.inputJSONnode['commcell']['commcellPassword'])
        user_obj = self._commcell.users.get(self.user_2)
        user_obj.update_user_password(
            self.inputJSONnode['commcell']['commcellPassword'], self.inputJSONnode['commcell']['commcellPassword'])

    @test_step
    def test_step_3(self):
        """Login as User 1 and check if all entites are there"""
        self.network_store_helper.network_store_name = self.user_1
        self.admin_console.login(
            self.user_1, self.inputJSONnode['commcell']['commcellPassword'])
        time.sleep(60)
        self.network_store_helper.validate_network_store_creation()
        #TO:DO:validate PIT function
        self.network_store_helper.network_store_name = self.user_2
        # to confirm that user 1 can't see user2 HFS share.
        self.network_store_helper.validate_delete()
        AdminConsole.logout_silently(self.admin_console)

    @test_step
    def test_step_4(self):
        """Login as User 2 and check if all user 2 entites are there"""
        self.network_store_helper.network_store_name = self.user_2
        self.admin_console.login(
            self.user_2, self.inputJSONnode['commcell']['commcellPassword'])
        time.sleep(60)
        self.network_store_helper.validate_network_store_creation()
        #TO:DO:validate PIT function
        self.network_store_helper.network_store_name = self.user_1
        # to confirm that user2 can't see user1 HFS share.
        self.network_store_helper.validate_delete()
        AdminConsole.logout_silently(self.admin_console)

    def run(self):

        try:
            self.test_step_1()
            self.test_step_2()
            self.test_step_3()
            self.test_step_4()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        self.NFS_server_obj.delete_nfs_objectstore(self.user_1,
                                                   delete_user=True)
        self.NFS_server_obj.delete_nfs_objectstore(self.user_2,
                                                   delete_user=True)
