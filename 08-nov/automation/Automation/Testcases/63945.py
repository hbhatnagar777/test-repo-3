# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies negative testcase for backup networks in command center

between a client and a media agent from command center.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

Testcase Inputs

    SourceClient : A client computer

    MediaAgent : Media agent of the client

"""

import socket
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.NetworkPage import NetworkPage, BackupNetworks
import os


class TestCase(CVTestCase):
    """Command Center - Backup Networks - Negative test cases for react DIPs screen"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Backup Networks - Negative test cases for react DIPs screen"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "SourceClient": "",
            "MediaAgent": "",
        }
        self.testcase_fail = False

    def hostname_to_ip(self, hostname: str) -> str:
        """Convert a hostname to its IP address.

        Args:
            hostname (str): The hostname to be converted.

        Returns:
            str: The IP address of the hostname.
        """
        try:
            return socket.gethostbyname(hostname)
        except socket.error as err:
            raise CVTestCaseInitFailure(f"Unable to resolve hostname {hostname}: {err}")

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            self.clientname = self.tcinputs.get("SourceClient")
            self.mediaagent = self.tcinputs.get("MediaAgent")

            # Get client and media agent objects
            self.client_object = self.commcell.clients.get(self.clientname)
            self.ma_object = self.commcell.clients.get(self.mediaagent)

            # Retrieve IP addresses using the hostname from the objects and convert to IP
            self.client_ip = self.hostname_to_ip(self.client_object.client_hostname)
            self.mediaagent_ip = self.hostname_to_ip(self.ma_object.client_hostname)

            self.client_summary = ""
            self.ma_summary = ""
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def validate_summary(self):
        """Validate the network summary of client and media agent"""
        import time
        time.sleep(10)
        self.client_summary = self.client_object.get_network_summary()
        self.ma_summary = self.ma_object.get_network_summary()
        self.validate_dips(self.client_ip, self.mediaagent_ip, self.client_summary)
        self.validate_dips(self.client_ip, self.mediaagent_ip, self.ma_summary)

    @test_step
    def navigate_to_dips(self):
        """Open browser and navigate to the network page"""
        try:
            self.browser = BrowserFactory().create_browser_object(browser_type=Browser.Types.EDGE)
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
        """This function adds DIPs between client and Media Agent"""
        try:
            self.log.info("Add DIPs between client and client")
            self.backupnetworks.add_backupnetworks(entity1=self.clientname,
                                                   entity2=self.clientname,
                                                   interface1=self.client_ip,
                                                   interface2=self.client_ip)
            self.log.info("DIPs getting added between the same client")
            self.testcase_fail = True
        except Exception:
            self.log.info(
                "Verified Backup Networks cannot be added between two same entities")

        # Verify the DIPs cannot be added without the network interfaces
        self.log.info("Try adding DIPs without selecting any interfaces")
        try:
            self.backupnetworks.add_backupnetworks(entity1=self.clientname,
                                                   entity2=self.mediaagent)
            self.log.info(
                "DIPs getting added b/w clients without any interfaces")
            self.testcase_fail = True
        except Exception:
            self.log.info(
                "Verified the backup networks cannot be added without interfaces")

        if self.testcase_fail:
            raise Exception("Failure in negative testcase for backup networks")

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_dips()
            self.add_interface_validate()
        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._network.cleanup_network()
            self._network.entities.cleanup()
