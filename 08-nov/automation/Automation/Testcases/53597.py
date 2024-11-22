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

    """Class for executing Validation of cvping tool

        Setup requirements to run this test case:
        2 clients for source and destination

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Validate CVPing tool [IPv4 & IPv6]"
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

            self._network.do_cvping(self.tcinputs['SourceClient'],
                                    self.tcinputs['DestinationClient'],
                                    8400, validate=True)

            self._network.do_cvping(self.tcinputs['SourceClient'],
                                    self.tcinputs['DestinationClient'],
                                    8400, "UseIPv4", True)

            self._network.do_cvping(self.tcinputs['SourceClient'],
                                    self.tcinputs['DestinationClient'],
                                    8400, "UseIPAny", True)

            self._network.do_cvping(self.tcinputs['SourceClient'],
                                    self.tcinputs['DestinationClient'],
                                    8400, "UseIPv6", True)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
