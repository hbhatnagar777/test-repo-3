# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Basic acceptance test case for Point in time view from command center.
Steps:
1.Create a HFS share.
2.Add some data into it.
3.Wait for the data to get backup
4.Modify the testdata.
5.Wait for backup and create the PIT.
6.Compare the snapshot of the share and PIT.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import time
import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.network_store_helper import NetworkStoreHelper
from Reports.utils import TestCaseUtils
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper

class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "60848": {
                "clientHostname": "edgelinuxma",
                "clientUsername": "root",
                "clientPassword": "###########",
                "nfs_server":"edgelinuxma",
                "plan":"Server plan",
                "version_interval": 0
            }

        """

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for HFS PIT in Command Center"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.network_store_helper = None
        self.tcinputs = {
            "nfs_server": None,
            "plan": None,
            "clientHostname":None,
            "clientUsername":None,
            "clientPassword":None,
            "version_interval":None
            }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.network_store_helper = NetworkStoreHelper(self.admin_console)

        self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                        self.tcinputs['clientUsername'],
                                        self.tcinputs['clientPassword'],
                                        self.id,
                                        self.commcell)
        self.NFS_server_obj = NFSHelper(self.tcinputs['nfs_server'],
                                            self.commcell,
                                            self.inputJSONnode['commcell']['commcellUsername'],
                                            self.inputJSONnode['commcell']['commcellPassword'],
                                            self.tcinputs.get('storagePolicy'))
        self.mounted_dirs = []
        self.test_dir_name = "AutoMation"
        self.objstore_test_path = self.nfsutil_obj.machine_obj.join_path(
                                                                        self.nfsutil_obj.mount_dir,
                                                                        self.test_dir_name)
        self.version_interval = self.tcinputs['version_interval']

    def run(self):

        try:

            self.network_store_helper.network_store_name = "Test_HFS_"+time.strftime("%H_%M_%S",time.localtime())
            self.pit_name = "PIT_HFS_"+self.id+'_'+time.strftime("%H_%M_%S",time.localtime())
            self.network_store_helper.nfs_server = self.tcinputs['nfs_server']
            self.network_store_helper.plan = self.tcinputs['plan']

            self.log.info("*********Adding a network store*********")
            self.network_store_helper.create_network_store(commcell=self._commcell)

            self.log.info("*********Verifying if network store added*********")
            time.sleep(60)
            self.network_store_helper.validate_network_store_creation()

            self.log.info("*"*10+"Adding data in Share"+"*"*10)

            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                         self.tcinputs['nfs_server'],
                                                         self.network_store_helper.network_store_name)
            self.mounted_dirs.append(self.nfsutil_obj.mount_dir)

            self.nfsutil_obj.create_test_data_objecstore(2,self.nfsutil_obj.machine_obj,self.objstore_test_path,self.network_store_helper.network_store_name)

            time.sleep(60*self.version_interval) # sleep for version interval time.

            self.nfsutil_obj.machine_obj.modify_test_data(self.objstore_test_path,rename=True,modify=True)

            time.sleep(60) #additional 1 min after backup completes

            timestamp = time.time()
            self.log.info("Timestamp for the PIT view "+str(timestamp))

            self.network_store_helper.add_pit_view(timestamp,self.pit_name)

            time.sleep(2*60) # additional 2 mins for the share to get exported

            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.snap_mount_dir,
                                                         self.tcinputs['nfs_server'],
                                                         '/'+self.network_store_helper.network_store_name+'-'+self.pit_name)
            self.mounted_dirs.append(self.nfsutil_obj.snap_mount_dir)

            self.nfsutil_obj.compare_snapshot(self.nfsutil_obj.snap_mount_dir,self.nfsutil_obj.mount_dir)
            
            self.network_store_helper.delete_pit_view(self.pit_name)

            self.nfsutil_obj.check_objectstore_backup_job(self.network_store_helper.network_store_name)



        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.NFS_server_obj.delete_nfs_objectstore(self.network_store_helper.network_store_name,
                                                   delete_user=True)
