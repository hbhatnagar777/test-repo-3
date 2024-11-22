# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies basic backup networks creation, update and deletion 

between a client and a media agent from command center.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

Testcase Inputs

    SourceClient : A client computer

    ClientInterface : Source Client Interface / IP

    ClientInterface2 : Source Client's second Interface /IP

    MediaAgent : Media agent of the client

    MediaAgentInterface : Media Agent's Interface/IP address

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.NetworkPage import NetworkPage, BackupNetworks
import os
import re

class TestCase(CVTestCase):
    """Command Center - Backup Networks - Validate Create & Delete Backup Networks (Between Clients)"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Backup Networks - Validate Create & Delete Backup Networks (Between Clients)"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "SourceClient": "",
            "ClientInterface":"",
            "MediaAgent": "",
            "MediaAgentInterface": "",
            "ClientInterface2": ""
        }


    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            self.clientname = self.tcinputs.get("SourceClient")
            self.mediaagent = self.tcinputs.get("MediaAgent")
            self.client_ip = self.tcinputs.get("ClientInterface")
            self.client_ip2 = self.tcinputs.get("ClientInterface2")
            self.mediaagent_ip = self.tcinputs.get("MediaAgentInterface")
            self.client_object = self.commcell.clients.get(self.clientname)
            self.ma_object = self.commcell.clients.get(self.mediaagent)
            self.client_summary = ""
            self.ma_summary = ""
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def validate_dips(self, client_ip, ma_ip, summary):
        """Validate the DIPs in outgoing routes
            Args:
                client_ip = IP of the client selected in DIP

                ma_ip = IP of the media agent machine selected in DIP

                summary - Network Summary of the client or media agent
        """
        time.sleep(10)
        self.log.info("Validate the Summary")
        fwconfiglines =  summary
        self.log.info(summary)
        for i in fwconfiglines.split("\n"):
            if self.clientname in i and self.mediaagent in i:
                self.log.info(f"Fwconfig has the entry : {i}")
                entty_type = re.search(r"type=(\w+)", i)
                match entty_type[1]:
                    case "dip":
                        if client_ip in i and \
                           ma_ip in i:
                            self.log.info("DIPs validated successfully")
                            return
                        break
                    case "persistent":
                        if client_ip in i and \
                           ma_ip in i:
                            self.log.info("DIPs validated successfully")
                            return
                        break
                    case "passive":
                        self.log.info("Passive route so ignore this")
                        return
        raise Exception("The network summary is invalid {0}".format(summary))
            
    def validate_summary(self, client_ip):
        """Validate the network summary of client and media agent"""
        import time
        time.sleep(10)
        self.client_summary = self.client_object.get_network_summary()
        self.ma_summary = self.ma_object.get_network_summary()
        self.validate_dips(client_ip, self.mediaagent_ip, self.client_summary)
        self.validate_dips(self.mediaagent_ip, client_ip, self.ma_summary)


    @test_step
    def navigate_to_dips(self):
        """Open browser and navigate to the network page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(os.getcwd())
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_network()

            # Click tile topologies in adminpage
            self.networkpage = NetworkPage(self.admin_console)
            self.backupnetworks = BackupNetworks(self.admin_console)
            self.networkpage.click_dips()

        except Exception as exception:
            raise CVTestStepFailure(exception)

    @test_step
    def add_interface_validate(self) -> None:
        """This functions adds DIPs between client and Media Agent"""
        self.backupnetworks.add_backupnetworks(entity1=self.clientname ,
                                               entity2=self.mediaagent,
                                               interface1=self.client_ip,
                                               interface2=self.mediaagent_ip)
        # Verify the entry present in the table
        table_rows = self.backupnetworks.get_all_backupnetworks()["Server and server groups"]
        valid_entry = True if f"{self.clientname} and {self.mediaagent}" in table_rows else False
        if not valid_entry: raise Exception("DIPs entry is not present in the table after creation")
        self.validate_summary(self.client_ip)
        self._network.validate([self.clientname], self.mediaagent)
    
    @test_step
    def edit_interface_validate(self) -> None:
        """Edit the interface of one of the client to a different IP"""
        self.backupnetworks.edit_backupnetworks(entity1=self.clientname ,
                                               entity2=self.mediaagent,
                                               interface1=self.client_ip2,
                                               interface2=self.mediaagent_ip)
        # Verify the entry present in the table
        self.validate_summary(self.client_ip2)
        self._network.validate([self.clientname], self.mediaagent)

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_dips()
            self.add_interface_validate()
            self.edit_interface_validate()
            self.backupnetworks.delete_backupnetworks(entity1=self.clientname, entity2=self.mediaagent)
        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._network.cleanup_network()
            self._network.entities.cleanup()
