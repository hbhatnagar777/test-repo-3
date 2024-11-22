# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper


class TestCase(CVTestCase):

    """Class for executing working of CVIPInfo tool

        Setup requirements to run this test case:
        2 clients for source and destination

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Validate CVIPInfo tool [IPv4 & IPv6]"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "SourceClient": None,
            "DestinationClient": None
        }

    def setup(self):
        """Setup function of this test case"""

        self._network = NetworkHelper(self)

    def run(self):
        """Run function """

        try:
            self.log.info("Started executing testcase")

            self._network.cv_ip_info(self.tcinputs['SourceClient'],
                                     self.tcinputs['DestinationClient'])

            self._network.cv_ip_info(self.tcinputs['SourceClient'])

            self._network.cv_ip_info(self.tcinputs['SourceClient'],
                                     self.tcinputs['DestinationClient'], "IPv6")

            self._network.cv_ip_info(self.tcinputs['SourceClient'], family="IPv6")

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
