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

import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.network_store_helper import NetworkStoreHelper
from Reports.utils import TestCaseUtils
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from AutomationUtils.options_selector import OptionsSelector

"""
1. Use a fresh VM. (Client and MA packages installed on that) 
2. Add the diskcache path (While adding HFS from CC).
3. wait for install job to complete
4. wait for share to go in ready state.
*************Till here we made sure that our HFS will work on new machine************
*************NOW we will delete the entries to make sure it will behave as fresh VM********
5. Delete index server.
6. delete index pool.
7. Delete HAC.
8. Then uninstall index store, index Gateway and HAC packages.
9. delete from IdxAccessPath where ClientId = client_id
10. delete from IdxCache where Description like '%{indexcache_name}%'
11. delete from IdxPool where Description like '%{name_of_Index_serverpool}%'
12. Uninstall dokany.
13. Reboot the system.
14. sleep and then make a machine class so we can make sure that VM is up now.
"""


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Install HFS in new MA"
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.network_store_helper = None
        self.tcinputs = {
            "nfs_server": None,
            "plan": None,
            "clientHostname": None,
            "clientUsername": None,
            "clientPassword": None,
            "cache_path": None,
            "idx_path": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.network_store_helper = NetworkStoreHelper(self.admin_console)
        self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                    self.tcinputs['clientUsername'],
                                    self.tcinputs['clientPassword'],
                                    self.id,
                                    self.commcell)
        self.client = self.commcell.clients.get(self.tcinputs['nfs_server'])
        self.utils = TestCaseUtils(self)
        self.utility = OptionsSelector(self._commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.network_store_helper.network_store_name = "Test_HFS_" + \
                time.strftime("%H_%M_%S", time.localtime())
            self.network_store_helper.nfs_server = self.tcinputs['nfs_server']
            self.network_store_helper.plan = self.tcinputs['plan']
            self.network_store_helper.create_network_store(
                self.commcell, self.tcinputs['cache_path'], self.tcinputs['idx_path'])
            self.nfsutil_obj.check_objectstore_install_job(
                self.tcinputs['nfs_server'])
            self.nfsutil_obj.check_hfs_components(
                hfs_client_name=self.tcinputs["nfs_server"])
            time.sleep(60)
            self.network_store_helper.validate_network_store_creation()
            self.network_store_helper.remove_network_store()
            self.network_store_helper.validate_delete()
            self.log.info("*"*20 + "Now removing HFS componets" + "*"*20)
            self.nfsutil_obj.delete_hfs_components(
                hfs_client_name=self.tcinputs["nfs_server"])
            self.log.info(
                "*"*20 + "Deleting HFS componets entry from DB" + "*"*20)
            self.nfsutil_obj.delete_db_entries(self.utility,self.tcinputs['nfs_server'])
            self.nfsutil_obj.uninstall_hfs_softwares(
                hfs_client_name=self.tcinputs["nfs_server"])
            time.sleep(60*5)
            self.nfsutil_obj.remove_hfs_additional_software()
            time.sleep(60*5)  # 5 mins for the restart of the VM.

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info(
            "Trying to connect to hostmachine to make sure that it is up.")
        # add check readiness for this method
        self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                    self.tcinputs['clientUsername'],
                                    self.tcinputs['clientPassword'],
                                    self.id,
                                    self.commcell)  # if the vm is restarted successfully then the object creation will be successful.
