# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies basic backup networks creation, update and deletion 

between a client and a media agent.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

Testcase Inputs

    SourceClient1 : A client computer

    SourceClient2 : Another client computer

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
import re
import time


class TestCase(CVTestCase):
    """Command Center - Backup Networks - Validate Create & Update Backup Networks (Between Client && client group)"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Backup Networks - Validate Create & Update Backup Networks (Between Client && client group)"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "SourceClient": "",
            "SourceClient2": "",
            "MediaAgent": ""
        }
        self.client_group_name = "CG_63944"

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            self.clientname = self.tcinputs.get("SourceClient")
            self.clientname2 = self.tcinputs.get("SourceClient2")
            self.mediaagent = self.tcinputs.get("MediaAgent")
            self.client_object = self.commcell.clients.get(self.clientname)
            self.client_object2 = self.commcell.clients.get(self.clientname2)
            self.client1_ip = self.convert_hostname_to_ip(self.client_object.client_hostname)
            self.client2_ip = self.convert_hostname_to_ip(self.client_object2.client_hostname)
            self.ma_object = self.commcell.clients.get(self.mediaagent)
            self.mediaagent_ip = self.convert_hostname_to_ip(self.ma_object.client_hostname)
            self.client_summary = ""
            self.ma_summary = ""
            self.clientgrps = self._network.entities.create_client_groups([self.client_group_name])
            self.clientgroupobject = self.clientgrps[self.client_group_name]["object"]
            self.clientgroupobject.add_clients([self.clientname, self.clientname2])

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def convert_hostname_to_ip(self, hostname):
        """Converts a hostname to its corresponding IP address.

        Args:
            hostname (str): The hostname to convert to an IP address.

        Returns:
            str: The IP address corresponding to the given hostname.
        """
        try:
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except socket.error as e:
            raise Exception(f"Unable to resolve hostname {hostname}: {e}")

    def validate_dips(self, client_name, client_ip, ma_ip, summary):
        """Validate the DIPs in outgoing routes
            Args:
                client_name = Client name of the whose summary is passed

                client_ip = IP of the client selected in DIP

                ma_ip = IP of the media agent machine selected in DIP

                summary - Network Summary of the client or media agent
        """
        self.log.info(summary)
        if summary.strip() == "":
            raise Exception("The network summary is empty for {0}".format(client_name))
        fwconfiglines = summary
        for i in fwconfiglines.split("\n"):
            if client_name in i and self.mediaagent in i:
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

    def validate_summary(self, is_wildcard_filter=False):
        """Validate the network summary of client and media agent"""
        time.sleep(10)
        self.client_summary = self.client_object.get_network_summary()
        self.client2_summary = self.client_object2.get_network_summary()
        self.ma_summary = self.ma_object.get_network_summary()
        client1_interface = self.client_object.client_hostname if is_wildcard_filter else self.client1_ip
        client2_interface = self.client_object2.client_hostname if is_wildcard_filter else self.client2_ip
        self.validate_dips(self.clientname, client1_interface, self.mediaagent_ip, self.client_summary)

        self.validate_dips(self.clientname2, client2_interface, self.mediaagent_ip, self.client2_summary)
        self.validate_dips(self.clientname, self.mediaagent_ip, client1_interface, self.ma_summary)
        self.validate_dips(self.clientname2, self.mediaagent_ip, client2_interface, self.ma_summary)

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
        """This functions adds DIPs between client group and Media Agent"""
        self.backupnetworks.add_backupnetworks(entity1=self.client_group_name,
                                               entity2=self.mediaagent,
                                               interface2=self.mediaagent_ip)
        # Verify the entry present in the table
        # table_rows = self.backupnetworks.get_all_backupnetworks()["Server and server groups"]
        # valid_entry = True if f"{self.client_group_name} and {self.mediaagent}" in table_rows else False
        # if not valid_entry: raise Exception("DIPs entry is not present in the table after creation")
        self._network.push_config_client([self.clientname, self.mediaagent])
        self.validate_summary(is_wildcard_filter=True)

    @test_step
    def edit_interface_validate(self) -> None:
        """Edit the interface of one of the client group to a wildcard interface"""
        self.backupnetworks.edit_backupnetworks(entity1=self.client_group_name,
                                                entity2=self.mediaagent,
                                                interface1="172.16.*",
                                                interface2=self.mediaagent_ip)
        # Verify the entry present in the table
        self.validate_summary()
        self._network.validate([self.clientname], self.mediaagent)

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_dips()
            self.add_interface_validate()
            self.edit_interface_validate()
            self.backupnetworks.delete_backupnetworks(entity1=self.client_group_name, entity2=self.mediaagent)
        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.networkpage.remove_fwconfig_files()
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._network.cleanup_network()
            self._network.entities.cleanup()
