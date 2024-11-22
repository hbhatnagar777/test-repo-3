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
from Server.Network import networkconstants
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    """Class for executing basic network case to validate webserver-webconsole TPPM

        Setup requirements to run this test case:
        2 clients -- one client with webserver and other client with webconsole
        package installed.

        webconsole client should be pointing to webserver client given in the input.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Firewall] : Webserver-Webconsole TPPM validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "WSClient": None,
            "WCClient": None,
            "TppmPort": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        wc_obj = self._commcell.clients.get(self.tcinputs['WCClient'])

        self.webconsole = wc_obj.client_hostname

        self.client_list.extend([self.tcinputs['WSClient'], self.tcinputs['WCClient']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]}])

        self._network.push_config_client(self.client_list)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Started executing {0} testcase".format(self.id))

            self._network.set_wswc_tppm({'webserver': self.tcinputs['WSClient']},
                                        {'webconsole': self.tcinputs['WCClient'],
                                        'portNumber': int(self.tcinputs['TppmPort'])})

            self._network.push_config_client([self.client_list[1],
                                              self.client_list[0]])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.exclude_machine(self.client_list)

            self._network.serverbase.restart_services([self.tcinputs['WCClient']])
            
            self._network.options.sleep_time(60)

            self._network.enable_firewall([self.tcinputs['WCClient'],
                                                   self.tcinputs['WCClient'],
                                                   self.tcinputs['WSClient']], [8403, 80, 8403])

            self.log.info("Performing check readiness after enabling windows firewall")

            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Logging into web-console to validate TPPM")

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.driver = self.browser.driver

            web_console = WebConsole(self.browser, self.webconsole)

            web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                              self.inputJSONnode['commcell']['commcellPassword'])

            self._network.options.sleep_time(networkconstants.NEWTWORK_TIMEOUT_SEC)
            self.log.info("Logging out")
            web_console.logout()
            self.browser.close()

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
