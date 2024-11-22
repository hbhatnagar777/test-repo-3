# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from Server.CVFailover.cvfailover import CSLiveSync
from cvpysdk.commcell import Commcell
import cvpysdk


class TestCase(CVTestCase):
    """ Production Failover cycle
    """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Commerve Live Sync]: Test Failover cycle"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "active_node": None,
            "target_node": None,
            "client": None,
            "media_agent": None
        }
        self.network_helper = None
        self.active_node = None
        self.target_node = None
        self.client = None
        self.media_agent = None

    def setup(self):
        # Initialising variables
        self.active_node = self.tcinputs["active_node"]
        self.target_node = self.tcinputs["target_node"]
        self.client = self.tcinputs["client"]
        self.media_agent = self.tcinputs["media_agent"]

    def run(self):
        # run function
        self.perform_failover(self.target_node, CSLiveSync.TEST)
        self.network_helper = NetworkHelper(self)
        self.network_helper.serverbase.check_client_readiness([self.client, self.media_agent])

        self.perform_failover(self.active_node, CSLiveSync.TEST_FAILBACK)
        self.network_helper = NetworkHelper(self)
        self.network_helper.serverbase.check_client_readiness([self.client, self.media_agent])

        self.log.info(">>> SUCCESS <<<")

    def perform_failover(self, target_node, failover_type):
        """
        This function perform failover and login to the target Commserve

        Args:
            target_node (str):  Target node name
        """
        target_livesync = CSLiveSync(self.commcell, target_node)
        target_livesync.failover(failover_type, CSLiveSync.PLANNED, target_node)
        while True:
            time.sleep(60)
            self.log.info(f"Trying to login: {target_livesync.failover_client_obj.client_hostname}")
            try:
                self.commcell = Commcell(target_livesync.failover_client_obj.client_hostname,
                                         self.inputJSONnode["commcell"]["commcellUsername"],
                                         self.inputJSONnode["commcell"]["commcellPassword"])
                self.log.info(f"Logged in Successfully !!! ")
                return
            except cvpysdk.exception.SDKException as e:
                pass

            except Exception as e:
                self.log.info("Error: "+str(e))
