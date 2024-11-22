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

import time
from Server.Network.networkhelper import NetworkHelper
from Server.Network import networkconstants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """This test verifies all positive and negative test cases for TPPM
    ( [tppm-whitelist] and [tppm-blacklist] )
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : TPPM validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "WCClient": None,
            "WSClient": None
        }

        self.webserver = None
        self.wc_obj = None
        self.ws_obj = None
        self.webconsole = None
        self._network = None
        self.browser = None
        self.driver = None
        self.fwconfiglocal = None
        self.cs_machine = None
        self.option_selector = None

    def setup(self):
        """Setup function of this test case"""
        self.webserver = self.tcinputs['WSClient']
        self.wc_obj = self._commcell.clients.get(self.tcinputs['WCClient'])
        self.ws_obj = self.commcell.clients.get(self.webserver)
        self.webconsole = self.wc_obj.client_hostname
        self.client_list.extend([self.webserver, self.tcinputs['WCClient']])
        self._network = NetworkHelper(self)
        self.option_selector = OptionsSelector(self.commcell)

        self.log.info("[+] Checking if TPPM exist")
        self.csdb.execute(f"select status from APP_FirewallTPPM WHERE fromEntityId = {self.wc_obj.client_id} and toEntityId = {self.ws_obj.client_id};")
        status = self.csdb.fetch_one_row()[0]
        if status != '0':
            self.log.info(f"[+] TPPM exist with id {id} [+]")
            self.delete_tppm()

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

            self.csdb.execute(f"select status from APP_FirewallTPPM WHERE fromEntityId = {self.wc_obj.client_id} and toEntityId = {self.ws_obj.client_id};")
            status = self.csdb.fetch_one_row()[0]
            if status != '0':
                raise Exception(f"[+] Not able to delete TPPM and please try again [+]")

            # Negative scenario of whitelist TPPM
            self.log.info("[+] Validaion of negative scenario of whitelist TPPM [+]")
            self._network.set_one_way(
                {'clientName': self.client_list[0]},
                {'clientName': self.client_list[1]}
            )
            self._network.push_config_client([self.client_list[1],
                                              self.client_list[0]])
            self._network.enable_firewall([self.tcinputs['WCClient'], self.webserver],
                                          [8403, 8403])
            time.sleep(300)
            self._network.serverbase.check_client_readiness(self.client_list)
            try:
                self.login_webconsolepage()
                self.status = constants.FAILED
            except Exception as e:
                self.log.info("[+] Login failed as expected [+]")
                self.status = constants.PASSED

            if self.status == constants.FAILED:
                raise Exception("We are able to login")

            # Validating blacklist TPPM
            self.log.info("[+] Validaion of blacklist TPPM [+]")
            self._network.set_wswc_tppm({'webserver': self.webserver},
                                        {'webconsole': self.tcinputs['WCClient'],
                                         'portNumber': 8989})
            self.create_fwconfiglocal()
            self._network.push_config_client([self.client_list[1],
                                              self.client_list[0]])
            self._network.serverbase.restart_services([self.tcinputs['WCClient']])
            time.sleep(300)
            self._network.exclude_machine(self.client_list)
            self._network.serverbase.check_client_readiness(self.client_list)
            self._network.enable_firewall([self.tcinputs['WCClient'],
                                           self.tcinputs['WCClient'],
                                           self.tcinputs['WSClient']], 
                                           [8403, 80, 8403])
            self.log.info("Performing check readiness after enabling windows firewall")
            time.sleep(300)
            self._network.serverbase.check_client_readiness(self.client_list)
            try:
                self.login_webconsolepage()
                self.status = constants.FAILED
            except Exception as e:
                self.log.info("[+] Login failed as expected [+]")
                self.status = constants.PASSED

            if self.status == constants.FAILED:
                raise Exception("We are able to login")
        except Exception as excp:
            self._network.server.fail(excp)
        finally:
            self.log.info("[+] Test case completed successfully [+]")
            self.cs_machine.create_file(f"{self.ws_obj.install_directory}\\Base\\FwConfigLocal.txt",
                                        self.fwconfiglocal)
            self._network.cleanup_network()
            self.delete_tppm()

    def login_webconsolepage(self):
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

    def create_fwconfiglocal(self):
        self.log.info("Getting the GUID of webserver")
        self.csdb.execute(f"SELECT GUID FROM APP_Client WHERE name = '{self.tcinputs['WCClient']}'")
        guid = self.csdb.fetch_one_row()[0]
        content = f"""
[tppm-whitelist]
acl clnt=* dst=@self@ ports=81
[tppm-blacklist]
acl clnt={guid} dst=@self@ ports=81
        """

        self.cs_machine = Machine(self.ws_obj)
        self.fwconfiglocal = self.cs_machine.read_file(f"{self.ws_obj.install_directory}\\Base\\FwConfigLocal.txt")
        if '[tppm-blacklist]' in self.fwconfiglocal:
            content = self.fwconfiglocal + f'''\nacl clnt={guid} dst=@self@ ports=81'''
        else:
            content = self.fwconfiglocal + content
        self.cs_machine.create_file(f"{self.ws_obj.install_directory}\\Base\\FwConfigLocal.txt", content)

    def delete_tppm(self):
        """Delete TPPM from DB and push network configuration"""
        query = f"UPDATE APP_FirewallTPPM SET status = 0 "\
                f"WHERE fromEntityId = {self.wc_obj.client_id} and toEntityId = {self.ws_obj.client_id} "\
                "and toPortNumber = 81 and fromPortNumber = 8989;"
        self.log.info(f"[+] Deleting the TPPM with below query.\n{query}[+]")
        self.option_selector.update_commserve_db_via_cre(query)
        self._network.push_config_client([self.client_list[1],
                                          self.client_list[0]])
