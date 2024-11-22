# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Validate below NFS Objectstore REST APIs
    /NFSObjectStores/Cache?mediaAgentId={mediaAgentId}
    /NFSObjectStores/Shares?mediaAgentId={mediaAgentId}
    /NFSObjectStores/NFSIndexServers
    /NFSObjectStores/Users
    /NFSObjectStores/NFSServers
    /NFSObjectStores/NFSSharesInfo

"""
import time
import datetime
import random
import string

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing validation of NFS ObjectStore REST APIs"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "validate NFS ObjectStore REST APIs"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.RESTAPI
        self.applicable_os = self.os_list.WINDOWS
        self.show_to_user = False
        self.tcinputs = {
            'NFSServerHostName': None,
            'ClientHostName': None,
            'IndexServerMA': None
        }
        self.NFS_server_obj = None
        self.Obj_store_name = None
        self.snap_name = "AutoSnapforRESTAPI"
        self.subclient_id = None
        self.nfs_server_id = None
        self._restapi = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")
        self.Obj_store_name = "Auto" + '-' + self.id + '-' + \
                              ''.join(random.choice(string.ascii_lowercase) for _ in range(6))
        self.NFS_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                        self.commcell,
                                        self.inputJSONnode['commcell']['commcellUsername'],
                                        self.inputJSONnode['commcell']['commcellPassword'],
                                        self.tcinputs.get('storagePolicy'))

        self.log.info("Creating Object Store : {0}".format(self.Obj_store_name))
        share_path = self.NFS_server_obj.create_nfs_objectstore(
                                                    self.Obj_store_name,
                                                    self.NFS_server_obj.storage_policy,
                                                    self.tcinputs['IndexServerMA'],
                                                    self.tcinputs['NFSServerHostName'],
                                                    self.tcinputs['ClientHostName'],
                                                    squashing_type="NO_ROOT_SQUASH",
                                                    delete_if_exists=True)

        time.sleep(10)

        # Expected time stamp format : "MM-DD-YYYY HH:MM:SS"
        timestamp1 = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y %H:%M:%S')

        self.log.info("creating PIT view for timestamp {0}".format(timestamp1))
        self.snap_mount_path = self.NFS_server_obj.create_objectstore_snap(
                                                                self.Obj_store_name,
                                                                timestamp= timestamp1,
                                                                allowed_nfs_clients= self.tcinputs['ClientHostName'],
                                                                snap_name=self.snap_name)
        self.commcell.refresh()
        objstore_client = self.commcell.clients.get(self.Obj_store_name)
        agent = objstore_client.agents.get("File System")
        bkpset = agent.backupsets.get(self.Obj_store_name)
        subclient = bkpset.subclients.get(self.Obj_store_name)
        self.subclient_id = subclient.subclient_id

        nfs_server_client = self.commcell.clients.get(self.tcinputs['NFSServerHostName'])
        self.nfs_server_id = nfs_server_client.client_id

        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "NFSServerName": self.tcinputs['NFSServerHostName'],
                       "NFSServerMAId": self.nfs_server_id,
                       "NFSSubclientId": self.subclient_id,
                       "NFSIndexServer": self.tcinputs['IndexServerMA'],
                       "PITName": self.snap_name,
                       "NFSShareName": self.Obj_store_name,
                       "CurrentTime": timestamp1,
                       "POSTReqPITName": int(time.time())
                       }
        self.log.info("env inputs:%s" % self.tcinputs)

    def run(self):
        """Main function for test case execution"""
        try:
            collection_json = 'NFSObjectStore.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)
        except Exception as excp:
            self.server.fail(excp)

    def tear_down(self):
        """Tear down function"""
        self.NFS_server_obj.delete_nfs_objectstore(self.Obj_store_name,
                                                   delete_user=True)
